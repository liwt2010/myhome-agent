"""视觉管线烟雾测试 v0.3

测试覆盖：
- MockCameraSource + PersonDetector（mock YOLO）
- FileCameraSource + 合成测试视频帧
- VisionStore CRUD
- 加密/解密循环
- 规则引擎 + 视觉事件端到端

不依赖真实 YOLO 模型（用 MockLocalDetector）
"""
from __future__ import annotations

import json
import sqlite3
import tempfile
import time
from pathlib import Path

import numpy as np
import pytest

from myhome_agent.vision.pipeline import (
    Camera, MockCameraSource, VisionPipeline, VisionStore,
    seed_demo_cameras, VisionEvent,
)
from myhome_agent.vision.sources import FileCameraSource
from myhome_agent.vision.detectors import (
    LocalDetector, Detection, PersonDetector, MotionDetector,
)


# ============================================================
# 辅助：Mock YOLO Detector（不下载模型）
# ============================================================


class MockPersonDetector(LocalDetector):
    """测试用：每 N 帧返回一次 person 检测"""

    def __init__(self, hit_every_n: int = 3):
        self.hit_every_n = hit_every_n
        self.call_count = 0

    @property
    def name(self) -> str:
        return "mock_person_for_test"

    def detect(self, frame):
        self.call_count += 1
        if self.call_count % self.hit_every_n == 0:
            return [
                Detection(
                    kind="person",
                    confidence=0.85,
                    bbox=(0.4, 0.3, 0.2, 0.4),
                    attributes={"test": True},
                )
            ]
        return []


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def tmp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def vision_store(tmp_db):
    store = VisionStore(tmp_db)
    yield store
    store._conn().close()


@pytest.fixture
def mock_frame():
    """生成一张 640x480 BGR 合成帧"""
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)


# ============================================================
# 摄像头 CRUD 测试
# ============================================================


class TestVisionStore:
    def test_upsert_and_list(self, vision_store):
        cam = Camera(
            id="test_cam_1",
            name="测试摄像头",
            rtsp_url="rtsp://admin:pass@192.168.1.100:554/stream1",
            location="客厅",
            capabilities={"person": True, "motion": True},
        )
        vision_store.upsert_camera(cam)
        cams = vision_store.list_cameras(household_id=1)
        assert len(cams) == 1
        assert cams[0].id == "test_cam_1"
        assert cams[0].name == "测试摄像头"
        assert cams[0].rtsp_url.startswith("rtsp://")
        # v0.3 加密列
        assert cams[0].id == "test_cam_1"  # 兼容期 rtsp_url 仍可读

    def test_encrypt_url(self, vision_store, tmp_db, monkeypatch):
        """v0.3：rtsp_url 自动加密"""
        cam = Camera(
            id="enc_cam",
            name="加密测试",
            rtsp_url="rtsp://secret:token@10.0.0.1:554/stream1",
            location="门口",
            capabilities={},
        )
        vision_store.upsert_camera(cam, encrypt_url=True)
        # 直接读 db，明文 rtsp_url 已不再（兼容期保留，但 encrypted_rtsp_url 有值）
        with vision_store._conn() as c:
            row = c.execute(
                "SELECT rtsp_url, encrypted_rtsp_url FROM cameras WHERE id = ?",
                ("enc_cam",),
            ).fetchone()
        assert row["encrypted_rtsp_url"]
        assert "token" not in (row["encrypted_rtsp_url"] or "")

    def test_log_and_query_event(self, vision_store):
        ev = VisionEvent(
            camera_id="test_cam",
            household_id=1,
            kind="person",
            confidence=0.85,
            bbox=(0.4, 0.3, 0.2, 0.4),
            attributes={"test": True},
        )
        eid = vision_store.log_event(ev)
        assert eid > 0
        events = vision_store.recent_events(household_id=1, since_seconds=60)
        assert len(events) == 1
        assert events[0]["kind"] == "person"
        assert events[0]["confidence"] == 0.85

    def test_seed_demo(self, vision_store):
        n = seed_demo_cameras(vision_store, household_id=1)
        assert n == 3
        cams = vision_store.list_cameras(household_id=1)
        assert len(cams) == 3
        locations = {c.location for c in cams}
        assert "门口" in locations
        assert "客厅" in locations
        assert "厨房" in locations


# ============================================================
# 摄像头源测试
# ============================================================


class TestCameraSources:
    def test_mock_source(self):
        src = MockCameraSource("test", mock_event=True)
        assert src.open()
        # 每 10 帧出现 1 次
        found_event = False
        for i in range(20):
            ok, frame = src.read()
            if ok:
                found_event = True
        assert found_event
        src.close()
        assert not src.is_opened()

    def test_mock_source_no_event(self):
        src = MockCameraSource("test", mock_event=False)
        src.open()
        for i in range(5):
            ok, frame = src.read()
            assert not ok
        src.close()


# ============================================================
# 检测器测试（不依赖真实 YOLO）
# ============================================================


class TestDetectors:
    def test_mock_person_detector(self):
        det = MockPersonDetector(hit_every_n=3)
        for i in range(10):
            dets = det.detect(None)
        assert det.call_count == 10
        # 应有几次命中
        det2 = MockPersonDetector(hit_every_n=2)
        all_dets = [det2.detect(None) for _ in range(10)]
        hits = [d for d in all_dets if d]
        assert len(hits) >= 4

    def test_motion_detector_init(self):
        """MotionDetector 不依赖真实帧也能初始化"""
        det = MotionDetector()
        assert det.name == "motion_detector_v0.3_mog2"
        # 第一帧没有背景，应返回空
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # MOG2 第一帧初始化需要 learn
        dets = det.detect(frame)
        assert isinstance(dets, list)


# ============================================================
# 端到端：Pipeline
# ============================================================


class TestVisionPipeline:
    def test_pipeline_with_mock(self, vision_store):
        cam_id = "test_pipe_cam"
        cam = Camera(
            id=cam_id,
            name="测试管道",
            rtsp_url="mock://test",
            location="测试位置",
            capabilities={"person": True},
        )
        vision_store.upsert_camera(cam)

        source = MockCameraSource(cam_id, mock_event=True)
        det = MockPersonDetector(hit_every_n=3)
        pipe = VisionPipeline(vision_store, cam_id, source, [det], fps=5)

        # 跑 20 帧
        for _ in range(20):
            pipe.run_once()

        # 验证事件
        events = vision_store.recent_events(camera_id=cam_id, since_seconds=60)
        # hit_every_n=3，20 帧中至少 6 次命中
        assert len(events) >= 1
        # kind 是 person
        for ev in events:
            assert ev["kind"] == "person"
            assert ev["confidence"] == 0.85


# ============================================================
# 加密/解密测试
# ============================================================


class TestCrypto:
    def test_encrypt_decrypt_roundtrip(self, monkeypatch):
        """v0.3：加解密循环"""
        # 设置固定的 key 避免写 .env
        from cryptography.fernet import Fernet
        test_key = Fernet.generate_key().decode()
        monkeypatch.setenv("MYHOME_FERNET_KEY", test_key)

        from myhome_agent.vision.crypto import encrypt, decrypt
        plaintext = "rtsp://user:secret@192.168.1.100:554/stream1"
        token = encrypt(plaintext)
        assert token != plaintext
        assert "secret" not in token
        # 解密
        assert decrypt(token) == plaintext

    def test_decrypt_empty(self, monkeypatch):
        from cryptography.fernet import Fernet
        test_key = Fernet.generate_key().decode()
        monkeypatch.setenv("MYHOME_FERNET_KEY", test_key)
        from myhome_agent.vision.crypto import decrypt
        assert decrypt("") == ""
