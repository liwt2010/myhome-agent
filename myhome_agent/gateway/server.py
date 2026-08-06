"""FastAPI 网关服务：REST API + WebSocket 实时通道。

启动方式:
    python -m myhome_agent.gateway.server
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ..agent.core import Agent, AgentSession
from ..collectors.cloud_api import MiCloudCollector
from ..collectors.registry import DeviceRegistry
from ..config import (
    CONFIG,
    DB_PATH,
    HOST,
    MI_PASSWORD,
    MI_REGION,
    MI_USERNAME,
    PORT,
    DEEPSEEK_API_KEY,
)
from ..memory.store import Store

logger = logging.getLogger(__name__)

# ─── 应用初始化 ───

app = FastAPI(title="myhome-agent — 家庭私人管家", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = Store(DB_PATH)

# 云端（可选，米家生态开启时启用）
cloud: MiCloudCollector | None = None
if MI_USERNAME and MI_PASSWORD:
    cloud = MiCloudCollector(MI_USERNAME, MI_PASSWORD, MI_REGION)

registry = DeviceRegistry(store, cloud)

# 智能体会话管理（v2.19 修订：抽象 LLMClient，缺 api_key 时降级到 mock）
api_key = DEEPSEEK_API_KEY
sessions: dict[str, AgentSession] = {}

# 选择 LLM 客户端（v0.1 默认 mock，可由环境变量启用 DeepSeek）
from ..agent.llm import MockLLMClient, DeepSeekLLMClient, get_default_client

if api_key and api_key not in ("", "sk-xxxx"):
    try:
        default_llm = DeepSeekLLMClient(api_key=api_key)
        logger.info("LLM 客户端：DeepSeek (%s)", default_llm.model)
    except Exception as e:
        logger.warning("DeepSeek 初始化失败 (%s)，降级到 mock", e)
        default_llm = MockLLMClient()
else:
    default_llm = MockLLMClient()
    logger.info("LLM 客户端：Mock（开发模式；配置 DEEPSEEK_API_KEY 切换到 DeepSeek）")

# v0.2 规则引擎 + 视觉管线
from ..rules.engine import RuleStore
from ..rules.confidence import calibrate
from ..rules.feedback import (
    submit_feedback, auto_pause_check, cascade_author_revoke,
    VALID_FEEDBACKS, FEEDBACK_TRUE_POSITIVE, FEEDBACK_FALSE_POSITIVE,
    FEEDBACK_IGNORED, FEEDBACK_DISABLE,
)
from ..rules.fallback import FallbackReasoner
from ..vision.pipeline import VisionStore, seed_demo_cameras

rule_store = RuleStore(DB_PATH)
vision_store = VisionStore(DB_PATH)
fallback_reasoner = FallbackReasoner(rule_store)

# ─── 后台任务 ───

async def _poll_loop():
    """定期轮询本地设备并写入时序库。"""
    from ..analytics.anomaly import run_all as run_anomaly
    from ..analytics.routines import learn_routines

    poll_interval = int(CONFIG.get("collect", {}).get("local_poll_interval", 60))
    analytics_interval = int(CONFIG.get("analytics", {}).get("interval", 300))
    last_analytics = 0

    while True:
        try:
            registry.poll_all_local()
        except Exception as e:
            logger.error("轮询异常: %s", e)

        now = asyncio.get_event_loop().time()
        if now - last_analytics > analytics_interval:
            last_analytics = now
            try:
                learn_routines(store)
                run_anomaly(store, CONFIG)
            except Exception as e:
                logger.error("分析异常: %s", e)

        await asyncio.sleep(poll_interval)


@app.on_event("startup")
async def startup():
    logger.info("myhome-agent 启动中...")
    if cloud:
        registry.sync_from_cloud()
    asyncio.create_task(_poll_loop())
    logger.info("myhome-agent 已就绪，监听 %s:%s", HOST, PORT)


# ─── 请求模型 ───

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str


class ControlRequest(BaseModel):
    device_id: str
    action: str
    params: list | None = None


class RememberRequest(BaseModel):
    content: str
    tags: str = ""


# ─── REST API ───


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0", "name": "myhome-agent"}


@app.get("/api/devices")
async def list_devices(room: str | None = None, type: str | None = None):
    devices = store.list_devices(room=room, type_=type)
    return {"devices": devices, "total": len(devices)}


@app.get("/api/devices/{device_id}")
async def get_device(device_id: str):
    dev = store.get_device(device_id)
    if not dev:
        return JSONResponse({"error": f"找不到设备: {device_id}"}, status_code=404)
    readings = store.latest_readings(device_id)
    return {"device": dev, "readings": readings}


@app.post("/api/devices/control")
async def control_device(req: ControlRequest):
    try:
        result = registry.control(req.device_id, req.action, req.params)
        return {"success": True, "result": str(result)}
    except ValueError as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/api/events")
async def list_events(kind: str | None = None, hours: int = 24, limit: int = 50):
    events = store.query_events(kind=kind, since_hours=hours, limit=limit)
    return {"events": events, "total": len(events)}


@app.get("/api/members")
async def list_members():
    members = store.list_members()
    return {"members": members, "total": len(members)}


@app.get("/api/presence")
async def get_presence():
    from ..analytics.presence import infer_presence
    infer_presence(store)
    presence = store.get_presence()
    return {"presence": presence}


@app.get("/api/routines")
async def get_routines():
    from ..analytics.routines import routine_summary
    routines = store.get_routines()
    summary = routine_summary(store)
    return {"routines": routines, "summary": summary}


@app.get("/api/alerts")
async def list_alerts(status: str = "open", limit: int = 50):
    alerts = store.list_alerts(status=status, limit=limit)
    return {"alerts": alerts, "total": len(alerts)}


@app.post("/api/alerts/{alert_id}/ack")
async def ack_alert(alert_id: int):
    store.ack_alert(alert_id)
    return {"success": True, "message": f"告警 {alert_id} 已确认"}


@app.get("/api/memories")
async def search_memories(query: str = "", limit: int = 20):
    memories = store.recall(query=query, limit=limit)
    return {"memories": memories, "total": len(memories)}


@app.post("/api/memories")
async def create_memory(req: RememberRequest):
    store.remember(req.content, tags=req.tags)
    return {"success": True, "message": "已记住"}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """v2.19 修订：缺 api_key 时自动用 mock 客户端（v0.1 行为）"""
    session_id = req.session_id
    if not session_id or session_id not in sessions:
        session = AgentSession(store, llm_client=default_llm)
        sessions[session.session_id] = session
        session_id = session.session_id
    else:
        session = sessions[session_id]

    reply = session.send(req.message)
    return ChatResponse(reply=reply, session_id=session_id)


@app.get("/api/summary")
async def home_summary():
    devices = store.list_devices()
    online = sum(1 for d in devices if d.get("online"))
    from ..analytics.presence import infer_presence
    from ..analytics.routines import routine_summary
    infer_presence(store)
    return {
        "devices": {"total": len(devices), "online": online},
        "presence": store.get_presence(),
        "open_alerts": store.list_alerts(status="open", limit=10),
        "routines": routine_summary(store),
    }


# ─── v0.2 规则引擎 API（§53 + §B） ───


class RuleFeedbackRequest(BaseModel):
    rule_id: str
    fire_id: int
    member_id: int = 1
    feedback: str
    note: str | None = None


@app.get("/api/rules")
async def list_rules():
    """列出已启用规则（v0.2 §53 调试面板）"""
    rules = rule_store.list_enabled_rules(household_id=1)
    out = []
    for r in rules:
        st = rule_store.get_state(r.id)
        out.append({
            "id": r.id,
            "description": r.description,
            "severity": r.severity,
            "category": r.category,
            "confidence_base": r.confidence_base,
            "cooldown": r.cooldown,
            "window": r.window,
            "state": st.state if st else "unknown",
            "true_positive_count": st.true_positive_count if st else 0,
            "false_positive_count": st.false_positive_count if st else 0,
        })
    return {"rules": out, "total": len(out)}


@app.get("/api/rules/{rule_id}")
async def get_rule(rule_id: str):
    """单条规则详情"""
    rules = [r for r in rule_store.list_enabled_rules(household_id=1) if r.id == rule_id]
    if not rules:
        return JSONResponse({"error": f"找不到规则: {rule_id}"}, status_code=404)
    r = rules[0]
    st = rule_store.get_state(rule_id)
    return {
        "rule": {
            "id": r.id, "description": r.description, "severity": r.severity,
            "category": r.category, "confidence_base": r.confidence_base,
            "cooldown": r.cooldown, "window": r.window, "yaml_body": r.yaml_body,
        },
        "state": {
            "state": st.state if st else "unknown",
            "last_fire_at": st.last_fire_at if st else None,
            "true_positive_count": st.true_positive_count if st else 0,
            "false_positive_count": st.false_positive_count if st else 0,
        },
    }


@app.get("/api/rules/{rule_id}/fires")
async def get_rule_fires(rule_id: str, limit: int = 20):
    """规则触发历史"""
    with rule_store._conn() as c:
        rows = c.execute(
            """SELECT id, fired_at, kind, confidence, matched_predicates, evidence_snapshot
               FROM rule_audit_log WHERE rule_id = ? ORDER BY fired_at DESC LIMIT ?""",
            (rule_id, limit),
        ).fetchall()
    return {"fires": [dict(r) for r in rows]}


@app.post("/api/rules/feedback")
async def rule_feedback(req: RuleFeedbackRequest):
    """提交规则反馈（v0.2 §53.5 误报闭环）"""
    try:
        result = submit_feedback(
            rule_store=rule_store,
            rule_id=req.rule_id,
            fire_id=req.fire_id,
            member_id=req.member_id,
            feedback=req.feedback,
            note=req.note,
        )
        return {
            "success": True,
            "feedback": result.feedback,
            "confidence_delta": result.confidence_delta,
            "rule_disabled": result.rule_disabled,
            "rationale": result.rationale,
        }
    except ValueError as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


@app.post("/api/rules/auto_pause_check")
async def trigger_auto_pause_check():
    """触发自动学习扫描（v0.2 §53.5.2）"""
    actions = auto_pause_check(rule_store, household_id=1)
    return {"actions": actions, "count": len(actions)}


# ─── v0.3 兜底推理 + 调试端点 ───


class FallbackRequest(BaseModel):
    rule_id: str
    evidence: dict = {}


@app.post("/api/rules/fallback")
async def manual_fallback(req: FallbackRequest):
    """手动触发兜底推理（v0.3 §53.4.3）

    通常由规则引擎自动触发；前端调试面板可手动调。
    """
    rules = [r for r in rule_store.list_enabled_rules() if r.id == req.rule_id]
    if not rules:
        return JSONResponse({"error": f"找不到规则: {req.rule_id}"}, status_code=404)
    rule = rules[0]

    result = fallback_reasoner.reason(
        rule=rule,
        evidence=req.evidence,
        household_id=1,
    )
    return {
        "triggered": result.triggered,
        "reason": result.reason,
        "suggestion": result.suggestion,
        "suggested_action": result.suggested_action,
        "confidence_after": result.confidence_after,
        "rationale": result.rationale,
        "daily_count": fallback_reasoner.get_daily_count(),
        "daily_limit": 10,
    }


@app.get("/api/rules/fallback/stats")
async def fallback_stats():
    """兜底统计"""
    return {
        "daily_count": fallback_reasoner.get_daily_count(),
        "daily_limit": 10,
        "llm_available": fallback_reasoner.llm_client is not None,
        "llm_model": fallback_reasoner.llm_client.model if fallback_reasoner.llm_client else None,
    }


@app.get("/api/rules/{rule_id}/debug")
async def rule_debug(rule_id: str, days: int = 7):
    """v0.3 规则调试面板数据

    返回：recent fires + confidence curve + fp/tp stats + state
    """
    rules = [r for r in rule_store.list_enabled_rules(household_id=1) if r.id == rule_id]
    if not rules:
        return JSONResponse({"error": f"找不到规则: {rule_id}"}, status_code=404)
    rule = rules[0]
    state = rule_store.get_state(rule_id)

    # 最近 fires
    cutoff = int(time.time()) - days * 86400 if 'time' in dir() else 0
    import time as _time
    cutoff = int(_time.time()) - days * 86400
    with rule_store._conn() as c:
        fires = c.execute(
            """SELECT id, fired_at, kind, confidence, matched_predicates
               FROM rule_audit_log
               WHERE rule_id = ? AND fired_at > ?
               ORDER BY fired_at DESC LIMIT 100""",
            (rule_id, cutoff),
        ).fetchall()
        feedbacks = c.execute(
            """SELECT feedback, COUNT(*) as cnt FROM rule_feedback
               WHERE rule_id = ? AND created_at > ?
               GROUP BY feedback""",
            (rule_id, cutoff),
        ).fetchall()

    return {
        "rule": {
            "id": rule.id,
            "description": rule.description,
            "severity": rule.severity,
            "category": rule.category,
            "confidence_base": rule.confidence_base,
            "cooldown": rule.cooldown,
            "window": rule.window,
        },
        "state": {
            "state": state.state if state else "unknown",
            "last_fire_at": state.last_fire_at if state else None,
            "true_positive_count": state.true_positive_count if state else 0,
            "false_positive_count": state.false_positive_count if state else 0,
        },
        "fires": [dict(r) for r in fires],
        "fire_count": len(fires),
        "feedback_summary": {r["feedback"]: r["cnt"] for r in feedbacks},
    }


# ─── v0.2 视觉管线 API（§54） ───


@app.get("/api/cameras")
async def list_cameras():
    """列出摄像头（v0.2 §54.2.2）"""
    cams = vision_store.list_cameras(household_id=1)
    return {"cameras": [c.__dict__ for c in cams], "total": len(cams)}


@app.post("/api/cameras/seed")
async def seed_cameras():
    """种子 3 个 mock 摄像头（v0.2 demo）"""
    n = seed_demo_cameras(vision_store, household_id=1)
    return {"seeded": n}


@app.get("/api/vision/events")
async def list_vision_events(camera_id: str | None = None, kind: str | None = None, since: int = 300):
    """最近视觉事件"""
    events = vision_store.recent_events(
        camera_id=camera_id, kind=kind, household_id=1, since_seconds=since
    )
    return {"events": events, "total": len(events)}


# ─── v0.5 治理 + 渠道 API ───


# 全局 QuotaManager（懒加载）
_quota_manager = None


def _get_quota_manager():
    global _quota_manager
    if _quota_manager is None:
        from ..governance.quotas import QuotaManager
        _quota_manager = QuotaManager()
    return _quota_manager


@app.get("/api/governance/quotas")
async def get_quotas():
    """v0.5 配额状态"""
    qm = _get_quota_manager()
    return {"households": qm.all_stats()}


@app.post("/api/governance/vacation")
async def set_vacation(req: dict):
    """v0.5 度假模式开关"""
    qm = _get_quota_manager()
    enable = req.get("enable", False)
    q = qm.get(req.get("household_id", 1))
    if enable:
        q.enter_vacation()
    else:
        q.exit_vacation()
    return {"success": True, "stats": q.get_stats()}


@app.get("/api/governance/decisions")
async def list_decisions(days: int = 7, limit: int = 50):
    """v0.5 自治决策历史"""
    try:
        with store._conn() as c:
            rows = c.execute(
                """SELECT id, member_id, action, level, risk_score, requires_confirm, outcome, created_at
                   FROM governance_decisions
                   WHERE created_at > strftime('%s', 'now', ?)
                   ORDER BY created_at DESC LIMIT ?""",
                (f"-{days} days", limit),
            ).fetchall()
        return {"decisions": [dict(r) for r in rows]}
    except Exception as e:
        return JSONResponse({"error": str(e), "hint": "请先跑 myhome-agent init"}, status_code=500)


class AutonomyTestRequest(BaseModel):
    severity: str = "care"
    irreversibility: str = "reversible"
    time_period: str = "day"
    member_role: str = "adult"
    member_home: bool = True
    is_vacation: bool = False
    action: str = "test_action"


@app.post("/api/governance/autonomy/test")
async def test_autonomy(req: AutonomyTestRequest):
    """v0.5 自治决策测试（不执行，只返回等级）"""
    from ..governance.autonomy import AutonomyEngine, RiskContext
    engine = AutonomyEngine()
    ctx = RiskContext(
        severity=req.severity,
        irreversibility=req.irreversibility,
        time_period=req.time_period,
        member_role=req.member_role,
        member_home=req.member_home,
        is_vacation=req.is_vacation,
    )
    d = engine.decide(ctx)
    return {
        "level": d.level,
        "risk_score": d.risk_score,
        "rationale": d.rationale,
        "requires_confirm": d.requires_confirm,
        "auto_execute": d.auto_execute,
        "notify": d.notify,
    }


# ─── v0.8.1 2FA 端点 ───


class TwoFactorSetupRequest(BaseModel):
    code: str | None = None  # 二次确认时的 6 位码
    secret_plain: str | None = None
    encrypted_secret: str | None = None
    encrypted_backup: list[str] | None = None


class TwoFactorVerifyRequest(BaseModel):
    member_id: int
    code: str
    action: str = "*"


class TwoFactorDisableRequest(BaseModel):
    member_id: int
    code: str


_twofa_mgr = None


def _get_twofa_mgr():
    global _twofa_mgr
    if _twofa_mgr is None:
        from ..auth.twofa import TwoFactorManager
        _twofa_mgr = TwoFactorManager(store)
    return _twofa_mgr


@app.post("/api/auth/2fa/setup/start")
async def twofa_setup_start(member_id: int):
    """v0.8.1 启动 2FA 设置（生成 secret + 备用码）"""
    result = _get_twofa_mgr().start_setup(member_id)
    # secret_plain + backup_codes_plain 仅返回一次
    return result


@app.post("/api/auth/2fa/setup/confirm")
async def twofa_setup_confirm(req: TwoFactorSetupRequest, member_id: int):
    """v0.8.1 确认 2FA 设置（用户输入 6 位码验证）"""
    if not (req.code and req.secret_plain and req.encrypted_secret and req.encrypted_backup):
        return JSONResponse({"error": "缺少必要字段"}, status_code=400)
    ok = _get_twofa_mgr().confirm_setup(
        member_id=member_id,
        code=req.code,
        secret_plain=req.secret_plain,
        encrypted_secret=req.encrypted_secret,
        encrypted_backup=req.encrypted_backup,
    )
    if ok:
        return {"success": True, "message": "2FA 已启用"}
    return JSONResponse({"success": False, "error": "验证码错误"}, status_code=400)


@app.post("/api/auth/2fa/verify")
async def twofa_verify(req: TwoFactorVerifyRequest):
    """v0.8.1 验证 2FA → 颁发 JWT token"""
    ok, msg = _get_twofa_mgr().verify(req.member_id, req.code)
    if not ok:
        return JSONResponse({"success": False, "error": msg}, status_code=401)
    from ..auth.session import TwoFactorSession
    token = TwoFactorSession.issue(req.member_id, req.action)
    return {"success": True, "token": token, "ttl_seconds": 1800}


@app.post("/api/auth/2fa/disable")
async def twofa_disable(req: TwoFactorDisableRequest):
    """v0.8.1 关闭 2FA（需 6 位码二次验证）"""
    ok = _get_twofa_mgr().disable(req.member_id, req.code)
    if ok:
        return {"success": True}
    return JSONResponse({"success": False, "error": "验证码错误"}, status_code=401)


@app.get("/api/auth/2fa/status")
async def twofa_status(member_id: int):
    """v0.8.1 2FA 状态"""
    from ..auth.twofa import TwoFactorManager
    state = TwoFactorManager(store)._load_state(member_id)
    if state is None:
        return {"enabled": False}
    return {
        "enabled": state.enabled,
        "enabled_at": state.enabled_at,
        "last_used_at": state.last_used_at,
        "failed_attempts": state.failed_attempts,
        "locked_until": state.locked_until,
    }


# ─── v0.8.1 受 2FA 保护的远程控制端点 ───


@app.post("/api/devices/control/secure")
async def control_device_secure(req: ControlRequest, payload: dict = None):
    """v0.8.1 远程控制（强制 2FA）

    Header: X-2FA-Token: <jwt>
    仅 irreversible capability 需 2FA；可逆仍走 /api/devices/control
    """
    from ..auth.session import TwoFactorSession
    from fastapi import Header, HTTPException

    # 实际 2FA 校验由依赖项完成；这里只标记示例
    # v0.9 真实接入：x_twofa_token: str | None = Header(default=None, alias="X-2FA-Token")
    return JSONResponse({
        "success": True,
        "message": "v0.8.1 占位：实际 2FA 校验已就绪（依赖项 /auth/session.py）",
        "hint": "前端需先 POST /api/auth/2fa/verify 拿 token，再带 X-2FA-Token header 调此端点",
    }, status_code=501)  # Not Implemented（占位）


# ─── v0.9 跨家庭共享 ───


class HouseholdExportResponse(BaseModel):
    household_id: int
    export_format: str
    data: dict
    sha256: str


@app.get("/api/households/{household_id}/export")
async def export_household(household_id: int):
    """v0.9 跨家庭导出（GDPR 数据可携 + 模板生成）"""
    import hashlib

    # 导出：rules + capabilities + member accessibility 偏好（不含 readings / events）
    with store._conn() as c:
        rules = [dict(r) for r in c.execute(
            "SELECT id, description, yaml_body, confidence_base, severity, category, enabled FROM rules WHERE household_id = ? AND archived_at IS NULL",
            (household_id,)
        ).fetchall()]
        members = [dict(r) for r in c.execute(
            "SELECT id, name, role, accessibility, notification_prefs FROM members WHERE household_id = ?",
            (household_id,)
        ).fetchall()]

    data = {"rules": rules, "members": members, "version": "v0.9"}
    blob = json.dumps(data, sort_keys=True, ensure_ascii=False).encode()
    digest = hashlib.sha256(blob).hexdigest()
    return HouseholdExportResponse(
        household_id=household_id,
        export_format="myhome-template-v1",
        data=data,
        sha256=digest,
    )


class HouseholdImportRequest(BaseModel):
    household_id: int
    data: dict
    dry_run: bool = True


@app.post("/api/households/import")
async def import_household(req: HouseholdImportRequest):
    """v0.9 跨家庭导入（dry_run 默认 True，admin 确认后才真导入）"""
    if not req.dry_run:
        # 真导入（v0.9.1 接入 marketplace）
        pass

    rules = req.data.get("rules", [])
    members = req.data.get("members", [])
    return {
        "dry_run": req.dry_run,
        "would_import_rules": len(rules),
        "would_import_members": len(members),
        "message": "v0.9 占位：实际 marketplace import 走 /api/marketplace/import"
    }


# ─── v0.9 治理审计端点 ───


@app.get("/api/governance/policies")
async def list_policies():
    """v0.9 列出全部 policy 决策（治理审计）"""
    try:
        with store._conn() as c:
            rows = c.execute(
                """SELECT member_id, role, capability, permission, priority, valid_until
                   FROM policies WHERE archived_at IS NULL
                   ORDER BY priority DESC LIMIT 100"""
            ).fetchall()
        return {"policies": [dict(r) for r in rows]}
    except Exception as e:
        return JSONResponse({"error": str(e), "hint": "需先跑 myhome-agent init"}, status_code=500)


# ─── 启动时初始化（v0.9） ───


@app.on_event("startup")
async def init_v09():
    """v0.9 启动时建表 + 种子"""
    try:
        with store._conn() as c:
            c.executescript(
                """
                -- 2FA 表
                CREATE TABLE IF NOT EXISTS member_2fa (
                  member_id INTEGER PRIMARY KEY,
                  enabled INTEGER NOT NULL DEFAULT 0,
                  secret_key_encrypted TEXT NOT NULL,
                  backup_codes_encrypted TEXT NOT NULL,
                  enabled_at INTEGER NOT NULL,
                  last_used_at INTEGER,
                  failed_attempts INTEGER DEFAULT 0,
                  locked_until INTEGER
                );

                -- WebAuthn credentials
                CREATE TABLE IF NOT EXISTS member_webauthn (
                  credential_id TEXT PRIMARY KEY,
                  member_id INTEGER NOT NULL,
                  public_key TEXT NOT NULL,
                  sign_count INTEGER DEFAULT 0,
                  transports TEXT,
                  nickname TEXT,
                  registered_at INTEGER NOT NULL,
                  last_used_at INTEGER
                );

                -- notification_queue
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
                CREATE INDEX IF NOT EXISTS idx_queue_pending ON notification_queue(next_attempt_at)
                  WHERE delivered_at IS NULL AND failed_at IS NULL;
                """
            )
    except Exception as e:
        logger.warning(f"v0.9 启动初始化失败: {e}")


# ─── WebSocket ───


@app.websocket("/ws/chat")
async def ws_chat(ws: WebSocket):
    await ws.accept()
    session_id = None
    session: AgentSession | None = None

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)

            if msg.get("type") == "chat":
                if not session:
                    session = AgentSession(store, llm_client=default_llm)
                    session_id = session.session_id
                    await ws.send_json({"type": "session", "session_id": session_id})

                # v2.19 修订：mock / DeepSeek 都支持，不再 500
                reply = session.send(msg["message"])
                await ws.send_json({"type": "text", "text": reply})
                await ws.send_json({"type": "done", "session_id": session_id})

            elif msg.get("type") == "ping":
                await ws.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info("WebSocket 客户端断开: %s", session_id)
    except Exception as e:
        logger.error("WebSocket 异常: %s", e)
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


@app.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    """实时事件推送：设备状态变更、告警等。"""
    await ws.accept()
    last_event_id = 0

    try:
        while True:
            events = store.query_events(since_hours=0, limit=20)
            new_events = [e for e in events if e["id"] > last_event_id]
            if new_events:
                last_event_id = max(e["id"] for e in new_events)
                await ws.send_json({"type": "events", "data": new_events})

            alerts = store.list_alerts(status="open", limit=5)
            await ws.send_json({"type": "alerts", "data": alerts})

            await asyncio.sleep(5)

    except WebSocketDisconnect:
        logger.info("WebSocket events 客户端断开")
    except Exception as e:
        logger.error("WebSocket events 异常: %s", e)


# ─── 静态文件（前端 PWA） ───

WEB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "web")
if os.path.isdir(WEB_DIR):
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index():
        index_path = os.path.join(WEB_DIR, "index.html")
        if os.path.exists(index_path):
            with open(index_path, encoding="utf-8") as f:
                return f.read()
        return "<h1>myhome-agent</h1><p>前端未部署</p>"


def main():
    import uvicorn
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
