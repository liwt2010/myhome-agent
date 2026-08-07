"""Regression tests for security and correctness fixes."""
from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import tempfile
import time

os.environ.setdefault("MYHOME_DB_PATH", os.path.join(tempfile.gettempdir(), "myhome_agent_test.db"))
os.environ.setdefault("MYHOME_API_TOKEN", "test-api-token")
os.environ.setdefault("MYHOME_JWT_SECRET", "test-jwt-secret-0123456789abcdef")
os.environ.setdefault("MYHOME_SNAPSHOT_DIR", os.path.join(tempfile.gettempdir(), "myhome_snapshots"))

from cryptography.fernet import Fernet

os.environ.setdefault("MYHOME_FERNET_KEY", Fernet.generate_key().decode())

import pytest

from myhome_agent.analytics.anomaly import safe_eval_condition
from myhome_agent.auth.twofa import TWO_FACTOR_SCHEMA, TwoFactorManager
from myhome_agent.channels.a2a_server import A2AMessage, A2AServer
from myhome_agent.governance.consensus import ConsensusEngine
from myhome_agent.governance.marketplace import Wallet
from myhome_agent.memory.store import Store
from myhome_agent.rules.engine import EvalContext, RuleScanner, RuleStore, evaluate_predicate, seed_default_rules
from myhome_agent.rules.feedback import submit_feedback


class TestSafeEvalCondition:
    def test_allowed_expressions(self):
        assert safe_eval_condition("value == 1", 1, 3) is True
        assert safe_eval_condition("value == 1 and 1 <= hour <= 5", 1, 3) is True
        assert safe_eval_condition("value == 1 and 1 <= hour <= 5", 1, 9) is False

    def test_injection_rejected(self):
        assert safe_eval_condition("__import__('os').system('id')", 1, 1) is False
        assert safe_eval_condition("value.__class__", 1, 1) is False


class TestTwoFactorServerSideSetup:
    def test_begin_confirm_flow(self, tmp_path):
        db = tmp_path / "twofa.db"
        store = Store(db)
        with store._conn() as c:
            c.executescript(TWO_FACTOR_SCHEMA)
        mgr = TwoFactorManager(store)
        start = mgr.start_setup(7)
        assert "challenge_id" in start
        assert "encrypted_secret" not in start  # 不再把服务端加密结果交给客户端

        import pyotp

        code = pyotp.TOTP(start["secret_plain"]).now()
        ok, _ = mgr.confirm_setup(start["challenge_id"], code)
        state = mgr._load_state(7)
        assert ok is True
        assert state is not None and state.enabled

    def test_confirm_rejects_client_supplied_secret(self, tmp_path):
        db = tmp_path / "twofa2.db"
        store = Store(db)
        with store._conn() as c:
            c.executescript(TWO_FACTOR_SCHEMA)
        mgr = TwoFactorManager(store)
        ok, _ = mgr.confirm_setup("missing-challenge", "123456")
        assert ok is False


class TestFeedbackPersistence:
    def test_feedback_commit(self, tmp_path):
        rs = RuleStore(tmp_path / "rules.db")
        seed_default_rules(rs, household_id=1)
        submit_feedback(
            rule_store=rs, rule_id="smoke_detector_v1", fire_id=1,
            member_id=1, feedback="true_positive", note="verify",
        )
        with rs._conn() as c:
            count = c.execute("SELECT COUNT(*) FROM rule_feedback").fetchone()[0]
            base = c.execute("SELECT confidence_base FROM rules WHERE id='smoke_detector_v1'").fetchone()[0]
            detail_rows = c.execute("SELECT COUNT(*) FROM rule_audit_log WHERE detail IS NOT NULL").fetchone()[0]
        assert count == 1
        assert base > 0.7
        assert detail_rows >= 1


class TestA2A:
    def test_verify_and_replay(self):
        msg = A2AMessage(from_agent="a", to_agent="b", type="task_request", payload={"x": 1})
        msg.timestamp = int(time.time())
        msg.sign("secret")
        assert msg.verify("secret") is True
        assert msg.verify("wrong") is False

        server = A2AServer(agent_id="b", private_key="secret")
        first = asyncio.run(server.handle_message(msg.to_dict()))
        replay = asyncio.run(server.handle_message(msg.to_dict()))
        assert first["status"] == "ok"
        assert replay["status"] == "auth_failed"


class TestConsensus:
    def test_no_double_vote_and_majority_quorum(self):
        engine = ConsensusEngine(agents=["a", "b", "c"])
        proposal = engine.create_proposal("t", "d", "a")
        assert engine.vote(proposal.proposal_id, "a", True) is True
        assert engine.vote(proposal.proposal_id, "a", True) is False
        assert engine.decide(proposal.proposal_id).phase.name != "DECIDED"
        assert engine.vote(proposal.proposal_id, "b", True) is True
        assert engine.decide(proposal.proposal_id).phase.name == "DECIDED"


class TestWallet:
    def test_escrow_deducts_and_releases(self, tmp_path):
        db = tmp_path / "wallet.db"
        conn = sqlite3.connect(db)
        conn.executescript(
            """
            CREATE TABLE wallets (agent_id TEXT PRIMARY KEY, balance REAL DEFAULT 0, escrow_balance REAL DEFAULT 0);
            CREATE TABLE task_escrow (task_id TEXT PRIMARY KEY, buyer TEXT, seller TEXT, amount REAL, status TEXT);
            CREATE TABLE wallet_transactions (
              id INTEGER PRIMARY KEY AUTOINCREMENT, from_agent TEXT, to_agent TEXT,
              amount REAL, reason TEXT, ts INTEGER
            );
            INSERT INTO wallets VALUES ('buyer', 100, 0), ('seller', 0, 0);
            """
        )
        conn.commit()
        conn.close()

        class FakeStore:
            def _conn(self):
                c = sqlite3.connect(db)
                c.row_factory = sqlite3.Row
                return c

        wallet = Wallet(store=FakeStore())
        assert wallet.escrow("buyer", "seller", "t1", 30) is True
        with wallet.store._conn() as c:
            buyer = c.execute("SELECT * FROM wallets WHERE agent_id='buyer'").fetchone()
        assert buyer["balance"] == 70
        assert buyer["escrow_balance"] == 30

        assert wallet.release_escrow("t1") is True
        with wallet.store._conn() as c:
            seller = c.execute("SELECT balance FROM wallets WHERE agent_id='seller'").fetchone()
            txns = c.execute("SELECT COUNT(*) FROM wallet_transactions").fetchone()[0]
        assert seller["balance"] == 30
        assert txns >= 1


class TestRuleEngine:
    def test_string_predicate(self):
        ctx = EvalContext(fields={"water_meter.flow": 1.0, "sensor.value": "on"})
        assert evaluate_predicate("water_meter.flow > 0.5", ctx) is True
        assert evaluate_predicate("sensor.value == 'on'", ctx) is True

    def test_scanner_fires_seed_rule(self, tmp_path):
        rs = RuleStore(tmp_path / "scan.db")
        seed_default_rules(rs, household_id=1)
        scanner = RuleScanner(rs)
        scanner.eval_ctx.fields = {"smoke_detector.triggered": True}
        scanner.scan_once()
        fired = scanner.scan_once()
        assert "smoke_detector_v1" in [f["rule_id"] for f in fired]

    def test_rule_fires_again_after_cooldown_expiry(self, tmp_path):
        rs = RuleStore(tmp_path / "cooldown.db")
        seed_default_rules(rs, household_id=1)
        scanner = RuleScanner(rs)
        scanner.eval_ctx.fields = {"smoke_detector.triggered": True}
        scanner.scan_once()
        assert "smoke_detector_v1" in [f["rule_id"] for f in scanner.scan_once()]
        with rs._conn() as c:
            c.execute(
                "UPDATE rule_state SET cooldown_until = 1 WHERE rule_id='smoke_detector_v1'"
            )
        assert "smoke_detector_v1" in [f["rule_id"] for f in scanner.scan_once()]


class TestVisionEncryption:
    def test_rtsp_url_not_stored_in_plaintext(self, tmp_path):
        from myhome_agent.vision.pipeline import Camera, VisionStore

        store = VisionStore(tmp_path / "vision.db")
        cam = Camera(
            id="enc_cam",
            name="加密测试",
            rtsp_url="rtsp://secret:token@10.0.0.1:554/stream1",
            location="门口",
            capabilities={"person": True},
        )
        store.upsert_camera(cam)
        with store._conn() as c:
            row = c.execute("SELECT rtsp_url, encrypted_rtsp_url FROM cameras WHERE id='enc_cam'").fetchone()
        assert not row["rtsp_url"]
        assert row["encrypted_rtsp_url"]
        assert "token" not in (row["encrypted_rtsp_url"] or "")
        loaded = store.list_cameras(household_id=1)[0]
        assert loaded.rtsp_url.startswith("rtsp://secret:")


class TestGatewayAuth:
    def test_bearer_token_enforced(self):
        from fastapi.testclient import TestClient

        from myhome_agent.auth.api_auth import API_TOKEN
        from myhome_agent.gateway.server import app

        with TestClient(app) as client:
            assert client.get("/api/health").status_code == 200
            assert client.get("/api/devices").status_code == 401
            headers = {"Authorization": f"Bearer {API_TOKEN}"}
            assert client.get("/api/devices", headers=headers).status_code == 200
            assert client.post(
                "/api/devices/control/secure",
                json={"device_id": "x", "action": "on"},
                headers=headers,
            ).status_code == 401  # 需要 X-2FA-Token


class TestSettingsScenes:
    def test_privacy_and_scene_endpoints(self):
        from fastapi.testclient import TestClient

        from myhome_agent.auth.api_auth import API_TOKEN
        from myhome_agent.gateway.server import app

        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        with TestClient(app) as client:
            assert client.post(
                "/api/privacy/vision", json={"enabled": False}, headers=headers
            ).json()["enabled"] is False
            privacy = client.get("/api/privacy", headers=headers).json()
            assert privacy["vision_enabled"] is False

            assert client.post(
                "/api/scenes",
                json={"name": "away", "actions": [{"device_id": "lr_light", "action": "off"}]},
                headers=headers,
            ).json()["success"] is True
            scenes = client.get("/api/scenes", headers=headers).json()
            assert any(s["name"] == "away" for s in scenes["scenes"])
            assert client.post(
                "/api/scenes/run", json={"name": "missing"}, headers=headers
            ).status_code == 404


class TestPrivacy:
    def test_paillier_roundtrip_and_homomorphic_add(self):
        from myhome_agent.federation.privacy import HomomorphicAggregator

        agg = HomomorphicAggregator()
        agg.setup(2048)
        cipher = agg.cipher
        ct1 = cipher.encrypt(1.5)
        ct2 = cipher.encrypt(2.5)
        assert abs(cipher.decrypt(ct1) - 1.5) < 1e-9
        assert abs(cipher.decrypt(cipher.add_ciphertexts(ct1, ct2)) - 4.0) < 1e-9

    def test_encrypted_aggregation(self):
        from myhome_agent.federation.privacy import HomomorphicAggregator

        agg = HomomorphicAggregator()
        agg.setup(2048)
        cipher = agg.cipher
        encrypted = [
            {"W1": [cipher.encrypt(1.0), cipher.encrypt(2.0)]},
            {"W1": [cipher.encrypt(3.0), cipher.encrypt(4.0)]},
        ]
        summed = agg.aggregate_encrypted(encrypted)
        assert abs(cipher.decrypt(summed["W1"][0]) - 4.0) < 1e-9
        assert abs(cipher.decrypt(summed["W1"][1]) - 6.0) < 1e-9

    def test_secure_round_shape(self):
        from myhome_agent.federation.privacy import SecureAggregator

        sa = SecureAggregator()
        result = sa.add_secure_aggregation_to_round(
            [{"W1": [1.0, 2.0]}, {"W1": [3.0, 4.0]}]
        )
        assert len(result["W1"]) == 2


class TestNotificationChain:
    def test_rule_fire_creates_alert_and_queues_telegram(self, tmp_path, monkeypatch):
        from myhome_agent.channels.notify import Notifier
        from myhome_agent.memory.store import Store
        from myhome_agent.rules.engine import RuleScanner, RuleStore, seed_default_rules

        db = tmp_path / "notify.db"
        store = Store(db)
        with store._conn() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS notification_queue (
                  id INTEGER PRIMARY KEY,
                  alert_id INTEGER NOT NULL,
                  recipient_id INTEGER NOT NULL,
                  channel TEXT NOT NULL,
                  payload TEXT,
                  attempts INTEGER DEFAULT 0,
                  last_error TEXT,
                  next_attempt_at INTEGER NOT NULL,
                  delivered_at INTEGER,
                  failed_at INTEGER,
                  created_at INTEGER NOT NULL
                );
                """
            )
        store.upsert_member("爸爸", role="adult", preferences={"telegram_chat_id": 12345})

        rs = RuleStore(db)
        seed_default_rules(rs, household_id=1)
        sent = {}

        def fake_post(url, json=None, timeout=None):
            sent["url"] = url
            sent["json"] = json

            class R:
                ok = True

            return R()

        monkeypatch.setattr("requests.post", fake_post)
        notifier = Notifier(store, telegram_token="test-token")
        scanner = RuleScanner(rs, alert_store=store, notifier=notifier)
        scanner.eval_ctx.fields = {"smoke_detector.triggered": True}
        scanner.scan_once()
        scanner.scan_once()

        with store._conn() as c:
            alerts = c.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
            queued = c.execute("SELECT COUNT(*) FROM notification_queue WHERE channel='telegram'").fetchone()[0]
        assert alerts >= 1
        assert queued >= 1

        result = notifier.process_queue()
        assert result["sent"] >= 1
        with store._conn() as c:
            delivered = c.execute(
                "SELECT COUNT(*) FROM notification_queue WHERE delivered_at IS NOT NULL"
            ).fetchone()[0]
        assert delivered >= 1
        assert sent.get("json", {}).get("chat_id") == 12345


class TestMemberAuth:
    def test_login_rbac_and_2fa(self):
        from fastapi.testclient import TestClient

        from myhome_agent.auth.api_auth import API_TOKEN
        from myhome_agent.auth.session import TwoFactorSession
        from myhome_agent.gateway.server import app, store as server_store

        adult_id = server_store.upsert_member("妈妈_rbac", role="adult")
        child_id = server_store.upsert_member("小宝_rbac", role="child")
        server_store.upsert_device(
            {
                "id": "front_door_rbac",
                "name": "大门锁",
                "type": "lock",
                "online": 0,
            }
        )

        with TestClient(app) as client:
            admin = {"Authorization": f"Bearer {API_TOKEN}"}
            assert client.post(
                "/api/auth/credentials", json={"member_id": adult_id, "password": "secret"}, headers=admin
            ).status_code == 200
            assert client.post(
                "/api/auth/credentials", json={"member_id": child_id, "password": "kid"}, headers=admin
            ).status_code == 200

            # 密码错误 / 正确登录
            assert client.post("/api/auth/login", json={"member_id": adult_id, "password": "bad"}).status_code == 401
            adult_login = client.post("/api/auth/login", json={"member_id": adult_id, "password": "secret"}).json()
            assert adult_login["role"] == "adult"
            adult = {"Authorization": f"Bearer {adult_login['token']}"}
            child_login = client.post("/api/auth/login", json={"name": "小宝_rbac", "password": "kid"}).json()
            child = {"Authorization": f"Bearer {child_login['token']}"}

            # adult 有控制权（设备不存在 → 400 而不是 401/403）
            assert client.post(
                "/api/devices/control", json={"device_id": "x", "action": "on"}, headers=adult
            ).status_code == 400
            # child 无控制权
            assert client.post(
                "/api/devices/control", json={"device_id": "x", "action": "on"}, headers=child
            ).status_code == 403

            # 高危设备（lock）未带 2FA token → 401
            resp = client.post(
                "/api/devices/control",
                json={"device_id": "front_door_rbac", "action": "unlock"},
                headers=adult,
            )
            assert resp.status_code == 401
            assert resp.json().get("error") == "requires 2FA"

            # 带上有效 2FA token → 通过鉴权，进入执行阶段（设备无 ip/token → 400）
            twofa = TwoFactorSession.issue(adult_id, action="remote_irreversible_control")
            resp = client.post(
                "/api/devices/control",
                json={"device_id": "front_door_rbac", "action": "unlock"},
                headers={**adult, "X-2FA-Token": twofa},
            )
            assert resp.status_code == 400


class TestAuditApi:
    def test_audit_endpoints_and_rbac(self):
        from fastapi.testclient import TestClient

        from myhome_agent.auth.api_auth import API_TOKEN
        from myhome_agent.gateway.server import app, store as server_store

        with server_store._conn() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS rule_audit_log (
                  id INTEGER PRIMARY KEY,
                  rule_id TEXT NOT NULL,
                  household_id INTEGER NOT NULL DEFAULT 1,
                  fired_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),
                  kind TEXT NOT NULL,
                  confidence REAL,
                  matched_predicates TEXT,
                  evidence_snapshot TEXT,
                  detail TEXT,
                  ack_at INTEGER,
                  ack_by INTEGER
                );
                CREATE TABLE IF NOT EXISTS governance_decisions (
                  id INTEGER PRIMARY KEY,
                  household_id INTEGER NOT NULL DEFAULT 1,
                  member_id INTEGER,
                  action TEXT NOT NULL,
                  level TEXT NOT NULL,
                  risk_score REAL,
                  requires_confirm INTEGER DEFAULT 0,
                  outcome TEXT,
                  user_override INTEGER DEFAULT 0,
                  created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
                );
                """
            )
            now = int(time.time())
            c.execute(
                """INSERT INTO rule_audit_log (rule_id, household_id, fired_at, kind, confidence)
                   VALUES ('smoke_detector_v1', 1, ?, 'fire', 0.95)""",
                (now,),
            )
            c.execute(
                """INSERT INTO governance_decisions
                   (household_id, member_id, action, level, risk_score, outcome, created_at)
                   VALUES (1, 1, 'control.lock', 'L1', 0.8, 'confirmed', ?)""",
                (now,),
            )

        with TestClient(app) as client:
            admin = {"Authorization": f"Bearer {API_TOKEN}"}
            rules = client.get("/api/audit/rules?days=7", headers=admin).json()
            assert rules["total"] >= 1
            decisions = client.get("/api/audit/decisions?days=7", headers=admin).json()
            assert decisions["total"] >= 1
            summary = client.get("/api/audit/summary", headers=admin).json()
            assert summary["rule_fires_30d"] >= 1
            exported = client.get("/api/audit/export?days=7", headers=admin).json()
            assert exported["sha256"]

            child_id = server_store.upsert_member("审计小宝", role="child")
            assert client.post(
                "/api/auth/credentials", json={"member_id": child_id, "password": "kid"}, headers=admin
            ).status_code == 200
            child_login = client.post(
                "/api/auth/login", json={"member_id": child_id, "password": "kid"}
            ).json()
            child = {"Authorization": f"Bearer {child_login['token']}"}
            assert client.get("/api/audit/rules", headers=child).status_code == 403


class TestVisionBridge:
    def test_person_detection_creates_alert_and_notify(self, tmp_path, monkeypatch):
        from myhome_agent.channels.notify import Notifier
        from myhome_agent.memory.store import Store
        from myhome_agent.vision.detectors import Detection, LocalDetector
        from myhome_agent.vision.pipeline import MockCameraSource, VisionPipeline, VisionStore

        db = tmp_path / "vision_bridge.db"
        mem = Store(db)
        with mem._conn() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS notification_queue (
                  id INTEGER PRIMARY KEY,
                  alert_id INTEGER NOT NULL,
                  recipient_id INTEGER NOT NULL,
                  channel TEXT NOT NULL,
                  payload TEXT,
                  attempts INTEGER DEFAULT 0,
                  last_error TEXT,
                  next_attempt_at INTEGER NOT NULL,
                  delivered_at INTEGER,
                  failed_at INTEGER,
                  created_at INTEGER NOT NULL
                );
                """
            )
        mem.upsert_member("爸爸", role="adult", preferences={"telegram_chat_id": 12345})

        class HitDetector(LocalDetector):
            @property
            def name(self):
                return "hit"

            def detect(self, frame):
                return [Detection(kind="person", confidence=0.9)]

        sent = {}

        def fake_post(url, json=None, timeout=None):
            sent["json"] = json

            class R:
                ok = True

            return R()

        monkeypatch.setattr("requests.post", fake_post)
        notifier = Notifier(mem, telegram_token="x")
        vs = VisionStore(db)
        source = MockCameraSource("cam", mock_event=True)
        pipe = VisionPipeline(
            vs, "cam", source, [HitDetector()], fps=5,
            alert_store=mem, notifier=notifier,
        )
        events = pipe.run_once()
        assert len(events) == 1
        with mem._conn() as c:
            alerts = c.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
            queued = c.execute("SELECT COUNT(*) FROM notification_queue").fetchone()[0]
        assert alerts == 1
        assert queued == 1
        assert notifier.process_queue()["sent"] == 1


class TestSnapshotAccess:
    def test_save_snapshot_file(self):
        from pathlib import Path

        import numpy as np

        from myhome_agent.config import SNAPSHOT_DIR
        from myhome_agent.vision.pipeline import VisionPipeline

        pipe = VisionPipeline.__new__(VisionPipeline)
        name = pipe._save_snapshot(
            np.zeros((64, 64, 3), dtype=np.uint8), "cam", "person", 1234567890
        )
        assert name
        assert (Path(SNAPSHOT_DIR) / name).exists()

    def test_snapshot_rbac_and_traversal(self):
        from pathlib import Path

        from fastapi.testclient import TestClient

        from myhome_agent.auth.api_auth import API_TOKEN
        from myhome_agent.config import SNAPSHOT_DIR
        from myhome_agent.gateway.server import app, store as server_store

        snap = Path(SNAPSHOT_DIR)
        snap.mkdir(parents=True, exist_ok=True)
        (snap / "test.jpg").write_bytes(b"\xff\xd8\xff\xe0")

        with TestClient(app) as client:
            admin = {"Authorization": f"Bearer {API_TOKEN}"}
            assert client.get("/api/vision/snapshots/test.jpg", headers=admin).status_code == 200
            assert client.get(
                "/api/vision/snapshots/../config.py", headers=admin
            ).status_code in (400, 404)

            child_id = server_store.upsert_member("快照小宝", role="child")
            assert client.post(
                "/api/auth/credentials", json={"member_id": child_id, "password": "kid"}, headers=admin
            ).status_code == 200
            child_login = client.post(
                "/api/auth/login", json={"member_id": child_id, "password": "kid"}
            ).json()
            assert client.get(
                "/api/vision/snapshots/test.jpg",
                headers={"Authorization": f"Bearer {child_login['token']}"},
            ).status_code == 403


class TestPendingActions:
    def test_rule_control_requires_confirm(self, tmp_path):
        from fastapi.testclient import TestClient

        from myhome_agent.auth.api_auth import API_TOKEN
        from myhome_agent.gateway.server import app, store as server_store
        from myhome_agent.rules.engine import RuleScanner, RuleStore, parse_rule_yaml

        rule = parse_rule_yaml(
            """
id: test_confirm_action_v1
description: 确认动作测试
severity: care
confidence_base: 0.9
cooldown: 0
window: 1min
when:
  smoke_detector.triggered: true
then:
  - control:
      device_id: test_light
      action: "on"
      params: []
"""
        )
        with server_store._conn() as c:
            c.execute("DELETE FROM pending_actions WHERE rule_id='test_confirm_action_v1'")
        rs = RuleStore(server_store.db_path)
        rs.upsert_rule(rule)
        scanner = RuleScanner(rs, alert_store=server_store)
        scanner.eval_ctx.fields = {"smoke_detector.triggered": True}
        scanner.scan_once()
        scanner.scan_once()

        with server_store._conn() as c:
            row = c.execute(
                "SELECT * FROM pending_actions WHERE rule_id='test_confirm_action_v1' "
                "ORDER BY id DESC LIMIT 1"
            ).fetchone()
        assert row is not None and row["status"] == "pending"
        token = row["token"]

        server_store.upsert_device({"id": "front_door_lock_confirm", "name": "确认锁", "type": "lock", "online": 0})
        lock_token = server_store.create_pending_action("r", "front_door_lock_confirm", "unlock")

        with TestClient(app) as client:
            admin = {"Authorization": f"Bearer {API_TOKEN}"}
            pending = client.get("/api/actions/pending", headers=admin).json()
            assert pending["total"] >= 1

            # 设备不存在 → 执行失败，状态保持 pending
            assert client.post(
                f"/api/actions/{token}/confirm", headers=admin
            ).status_code == 400
            assert server_store.get_pending_action(token)["status"] == "pending"

            # 高危设备（lock）未带 2FA → 401
            assert client.post(
                f"/api/actions/{lock_token}/confirm", headers=admin
            ).status_code == 401

            # 取消后不可再确认
            assert client.post(
                f"/api/actions/{token}/cancel", headers=admin
            ).status_code == 200
            assert client.post(
                f"/api/actions/{token}/confirm", headers=admin
            ).status_code == 409
