"""FastAPI 网关服务：REST API + WebSocket 实时通道。

启动方式:
    python -m myhome_agent.gateway.server
"""
from __future__ import annotations

import asyncio
import hmac
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Header, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ..agent.core import Agent, AgentSession
from ..agent.llm_router import LLMRouter, TaskType, get_llm_client
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
    CONTROL_CONFIRM_TYPES,
    SNAPSHOT_DIR,
)
from ..auth.api_auth import API_TOKEN, websocket_authorized
from ..auth.authz import (
    hash_password,
    issue_member_token,
    require_permission,
    verify_member_token,
    verify_password,
)
from ..auth.webauthn_endpoints import router as webauthn_router
from ..channels.notify import Notifier
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

app.include_router(webauthn_router)

PUBLIC_PATHS = {
    "/",
    "/api/health",
    "/api/auth/login",
    "/api/auth/members",
    "/manifest.json",
    "/sw.js",
    "/favicon.ico",
}
PUBLIC_PREFIXES = ("/static", "/api/auth/2fa/verify", "/api/auth/webauthn/login")


@app.middleware("http")
async def require_api_token_middleware(request, call_next):
    """除健康检查、2FA/WebAuthn 登录外，所有 API 都要求 Bearer token。"""
    path = request.url.path
    if path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES):
        return await call_next(request)
    auth = request.headers.get("authorization", "")
    token = auth[7:] if auth.lower().startswith("bearer ") else ""
    if not token or not hmac.compare_digest(token, API_TOKEN):
        member = verify_member_token(token)
        if member is None:
            return JSONResponse(
                {"error": "unauthorized", "hint": "set Authorization: Bearer <MYHOME_API_TOKEN or member login token>"},
                status_code=401,
            )
        request.state.member = member
    return await call_next(request)

store = Store(DB_PATH)

notifier = Notifier(store)

# 云端（可选，米家生态开启时启用）
cloud: MiCloudCollector | None = None
if MI_USERNAME and MI_PASSWORD:
    cloud = MiCloudCollector(MI_USERNAME, MI_PASSWORD, MI_REGION)

registry = DeviceRegistry(store, cloud)

# 智能体会话管理（v2.19 修订：抽象 LLMClient，缺 api_key 时降级到 mock）
api_key = DEEPSEEK_API_KEY
sessions: dict[str, AgentSession] = {}

MAX_SESSIONS = 1000
SESSION_TTL_SECONDS = 3600


def _cleanup_sessions() -> None:
    """回收过期/超量会话，避免内存无限增长。"""
    now = time.time()
    expired = [
        sid for sid, s in sessions.items()
        if now - getattr(s, "created_at", 0) > SESSION_TTL_SECONDS
    ]
    for sid in expired:
        sessions.pop(sid, None)
    while len(sessions) > MAX_SESSIONS:
        sessions.pop(next(iter(sessions)), None)


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 3)


def _pick_llm_for_chat():
    """按预算路由选择 LLM 客户端；失败时降级到默认客户端。"""
    try:
        decision = llm_router.route(TaskType.CHAT, context_size=2000)
        return get_llm_client(decision.provider), decision.provider
    except Exception as e:
        logger.warning("LLM 路由失败，使用默认客户端: %s", e)
        return default_llm, None

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

llm_router = LLMRouter()

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
vision_scheduler: Any | None = None
_poll_task: Any | None = None

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
            await asyncio.to_thread(registry.poll_all_local)
        except Exception as e:
            logger.error("轮询异常: %s", e)
        try:
            notifier.process_queue()
        except Exception as e:
            logger.error("通知队列处理异常: %s", e)

        now = asyncio.get_event_loop().time()
        if now - last_analytics > analytics_interval:
            last_analytics = now
            try:
                await asyncio.to_thread(learn_routines, store)
                await asyncio.to_thread(run_anomaly, store, CONFIG)
            except Exception as e:
                logger.error("分析异常: %s", e)

        await asyncio.sleep(poll_interval)


async def _startup():
    global _poll_task
    logger.info("myhome-agent 启动中...")
    if cloud:
        registry.sync_from_cloud()
    _start_vision_scheduler()
    _init_v09()
    _poll_task = asyncio.create_task(_poll_loop())
    logger.info("myhome-agent 已就绪，监听 %s:%s", HOST, PORT)


def _start_vision_scheduler() -> None:
    """按 MYHOME_VISION_ENABLED 开关启动视觉调度（RTSP + YOLO）。"""
    global vision_scheduler
    if os.getenv("MYHOME_VISION_ENABLED", "0") != "1":
        return
    try:
        from ..vision.scheduler import build_scheduler_from_store

        vision_scheduler = build_scheduler_from_store(
            vision_store,
            fps=5,
            max_workers=2,
            alert_store=store,
            notifier=notifier,
        )
        vision_scheduler.start()
        logger.info("视觉调度已启动: %s 路摄像头", vision_scheduler.get_stats()["camera_count"])
    except Exception as e:
        logger.warning("视觉调度启动失败: %s", e)


async def _shutdown():
    global vision_scheduler, _poll_task
    if _poll_task is not None:
        _poll_task.cancel()
        try:
            await _poll_task
        except asyncio.CancelledError:
            pass
    if vision_scheduler is not None:
        vision_scheduler.stop()


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
async def control_device(
    req: ControlRequest,
    x_twofa_token: str | None = Header(default=None, alias="X-2FA-Token"),
    _member: dict = Depends(require_permission("device.control")),
):
    dev = store.get_device(req.device_id) or store.find_device_by_name(req.device_id)
    if dev and dev.get("type") in CONTROL_CONFIRM_TYPES:
        from ..auth.session import TwoFactorSession

        if not x_twofa_token:
            return JSONResponse(
                {"error": "requires 2FA", "action": "remote_irreversible_control"},
                status_code=401,
            )
        ok, payload = TwoFactorSession.verify(x_twofa_token, "remote_irreversible_control")
        if not ok:
            return JSONResponse({"error": payload}, status_code=401)
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
async def create_memory(req: RememberRequest, _member: dict = Depends(require_permission("memories.write"))):
    store.remember(req.content, tags=req.tags)
    return {"success": True, "message": "已记住"}


# ─── 设置与场景 ───


class SceneRunRequest(BaseModel):
    name: str


class SceneCreateRequest(BaseModel):
    name: str
    actions: list[dict] = []


class PrivacyToggleRequest(BaseModel):
    enabled: bool


def _scene_key(name: str) -> str:
    return f"scene.{name}"


@app.get("/api/scenes")
async def list_scenes():
    scenes = []
    for s in store.list_settings():
        if s["key"].startswith("scene."):
            scenes.append({"name": s["key"][len("scene."):], "actions": json.loads(s["value"] or "[]")})
    return {"scenes": scenes, "total": len(scenes)}


@app.post("/api/scenes")
async def create_scene(req: SceneCreateRequest, _member: dict = Depends(require_permission("settings.write"))):
    store.set_setting(_scene_key(req.name), json.dumps(req.actions, ensure_ascii=False))
    return {"success": True, "name": req.name, "actions": req.actions}


@app.post("/api/scenes/run")
async def run_scene(req: SceneRunRequest, _member: dict = Depends(require_permission("settings.write"))):
    raw = store.get_setting(_scene_key(req.name))
    if raw is None:
        return JSONResponse({"success": False, "error": f"场景不存在: {req.name}"}, status_code=404)
    try:
        actions = json.loads(raw)
    except Exception:
        return JSONResponse({"success": False, "error": "场景配置损坏"}, status_code=500)

    results = []
    for action in actions or []:
        device_id = action.get("device_id")
        act = action.get("action")
        params = action.get("params")
        try:
            result = registry.control(device_id, act, params)
            results.append({"device_id": device_id, "action": act, "success": True, "result": str(result)})
        except Exception as e:
            results.append({"device_id": device_id, "action": act, "success": False, "error": str(e)})
    return {"success": True, "name": req.name, "results": results}


@app.get("/api/privacy")
async def get_privacy():
    def flag(key: str, default: str = "1") -> bool:
        return store.get_setting(key, default) == "1"

    return {
        "vision_enabled": flag("privacy.vision"),
        "llm_enabled": flag("privacy.llm"),
        "remote_enabled": flag("privacy.remote"),
    }


@app.post("/api/privacy/vision")
async def set_vision(req: PrivacyToggleRequest, _member: dict = Depends(require_permission("settings.write"))):
    store.set_setting("privacy.vision", "1" if req.enabled else "0")
    return {"success": True, "enabled": req.enabled}


@app.post("/api/privacy/llm")
async def set_llm(req: PrivacyToggleRequest, _member: dict = Depends(require_permission("settings.write"))):
    store.set_setting("privacy.llm", "1" if req.enabled else "0")
    return {"success": True, "enabled": req.enabled}


@app.post("/api/privacy/remote")
async def set_remote(req: PrivacyToggleRequest, _member: dict = Depends(require_permission("settings.write"))):
    store.set_setting("privacy.remote", "1" if req.enabled else "0")
    return {"success": True, "enabled": req.enabled}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """v2.19 修订：缺 api_key 时自动用 mock 客户端（v0.1 行为）"""
    _cleanup_sessions()
    provider = None
    session_id = req.session_id
    if not session_id or session_id not in sessions:
        client, provider = _pick_llm_for_chat()
        session = AgentSession(store, llm_client=client)
        session._llm_provider = provider
        sessions[session.session_id] = session
        session_id = session.session_id
    else:
        session = sessions[session_id]
        provider = getattr(session, "_llm_provider", None)

    reply = session.send(req.message)
    if provider:
        llm_router.record_usage(
            provider,
            _estimate_tokens(req.message) + 500,
            _estimate_tokens(reply),
        )
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
    cutoff = int(time.time()) - days * 86400
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


@app.get("/api/vision/snapshots/{filename}")
async def vision_snapshot(filename: str, _member: dict = Depends(require_permission("vision.read"))):
    """访问摄像头快照（带 RBAC + 路径穿越防护）。"""
    from pathlib import Path as _Path

    safe_name = _Path(filename).name
    if safe_name != filename or not safe_name.lower().endswith((".jpg", ".jpeg", ".png")):
        return JSONResponse({"error": "invalid filename"}, status_code=400)
    path = _Path(SNAPSHOT_DIR) / safe_name
    if not path.is_file():
        return JSONResponse({"error": "snapshot not found"}, status_code=404)
    return FileResponse(str(path), media_type="image/jpeg")


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


class TwoFactorSetupStartRequest(BaseModel):
    member_id: int


class TwoFactorSetupConfirmRequest(BaseModel):
    challenge_id: str
    code: str


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
async def twofa_setup_start(req: TwoFactorSetupStartRequest):
    """v0.8.1 启动 2FA 设置（生成 secret + 备用码）"""
    return _get_twofa_mgr().start_setup(req.member_id)


@app.post("/api/auth/2fa/setup/confirm")
async def twofa_setup_confirm(req: TwoFactorSetupConfirmRequest):
    """v0.8.1 确认 2FA 设置（用户输入 6 位码验证）"""
    ok, msg = _get_twofa_mgr().confirm_setup(req.challenge_id, req.code)
    if ok:
        return {"success": True, "message": "2FA 已启用"}
    return JSONResponse({"success": False, "error": msg}, status_code=400)


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


# ─── 成员登录 + RBAC ───


class MemberLoginRequest(BaseModel):
    member_id: int | None = None
    name: str | None = None
    password: str


class MemberCredentialRequest(BaseModel):
    member_id: int
    password: str


@app.get("/api/auth/members")
async def auth_members():
    """公开的最小成员列表，供登录页选择身份。"""
    with store._conn() as c:
        rows = c.execute("SELECT id, name FROM members ORDER BY name").fetchall()
    return {"members": [dict(r) for r in rows]}


@app.post("/api/auth/login")
async def member_login(req: MemberLoginRequest):
    """成员密码登录 → 24h 成员 JWT（RBAC 依据）。"""
    with store._conn() as c:
        if req.member_id is not None:
            row = c.execute("SELECT id, role FROM members WHERE id = ?", (req.member_id,)).fetchone()
        elif req.name:
            row = c.execute("SELECT id, role FROM members WHERE name = ?", (req.name,)).fetchone()
        else:
            return JSONResponse({"error": "需要 member_id 或 name"}, status_code=400)
        if not row:
            return JSONResponse({"error": "成员不存在"}, status_code=401)
        cred = c.execute(
            "SELECT password_hash FROM member_credentials WHERE member_id = ?",
            (row["id"],),
        ).fetchone()
    if not cred or not verify_password(req.password, cred["password_hash"]):
        return JSONResponse({"error": "密码错误"}, status_code=401)
    token = issue_member_token(row["id"], row["role"])
    return {
        "success": True,
        "token": token,
        "member_id": row["id"],
        "role": row["role"],
        "ttl_seconds": 86400,
    }


@app.post("/api/auth/credentials")
async def set_member_credential(req: MemberCredentialRequest):
    """设置/重置成员密码（管理员 API token）。"""
    hashed = hash_password(req.password)
    with store._conn() as c:
        c.execute(
            """INSERT INTO member_credentials (member_id, password_hash, updated_at)
               VALUES (?, ?, strftime('%s', 'now'))
               ON CONFLICT(member_id) DO UPDATE SET
                 password_hash = excluded.password_hash,
                 updated_at = excluded.updated_at""",
            (req.member_id, hashed),
        )
    return {"success": True}


# ─── v0.8.1 受 2FA 保护的远程控制端点 ───


@app.post("/api/devices/control/secure")
async def control_device_secure(
    req: ControlRequest,
    x_twofa_token: str | None = Header(default=None, alias="X-2FA-Token"),
    _member: dict = Depends(require_permission("device.control")),
):
    """远程不可逆控制（强制 2FA）。Header: X-2FA-Token: <jwt>"""
    from ..auth.session import TwoFactorSession

    if not x_twofa_token:
        return JSONResponse(
            {"error": "requires 2FA", "action": "remote_irreversible_control"},
            status_code=401,
        )
    ok, payload = TwoFactorSession.verify(x_twofa_token, "remote_irreversible_control")
    if not ok:
        return JSONResponse({"error": payload}, status_code=401)
    try:
        result = registry.control(req.device_id, req.action, req.params)
        return {"success": True, "result": str(result)}
    except ValueError as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


# ─── v0.9 跨家庭共享 ───


class HouseholdExportResponse(BaseModel):
    household_id: int
    export_format: str
    data: dict
    sha256: str


@app.get("/api/households/{household_id}/export")
async def export_household(household_id: int, _member: dict = Depends(require_permission("data.export"))):
    """v0.9 跨家庭导出（GDPR 数据可携 + 模板生成）"""
    import hashlib

    # 导出：rules + capabilities + member accessibility 偏好（不含 readings / events）
    with store._conn() as c:
        rules = [dict(r) for r in c.execute(
            "SELECT id, description, yaml_body, confidence_base, severity, category, enabled FROM rules WHERE household_id = ? AND archived_at IS NULL",
            (household_id,)
        ).fetchall()]
        members = [dict(r) for r in c.execute(
            "SELECT id, name, role, preferences, devices FROM members"
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


# ─── 统一审计 API ───


def _audit_table_exists(table: str) -> bool:
    with store._conn() as c:
        row = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
    return row is not None


@app.get("/api/audit/rules")
async def audit_rules(
    rule_id: str | None = None,
    kind: str | None = None,
    days: int = 7,
    limit: int = 100,
    _member: dict = Depends(require_permission("audit.read")),
):
    if not _audit_table_exists("rule_audit_log"):
        return {"audit": [], "total": 0}
    sql = "SELECT * FROM rule_audit_log WHERE fired_at > strftime('%s','now',?)"
    params: list[Any] = [f"-{max(days, 0)} days"]
    if rule_id:
        sql += " AND rule_id = ?"
        params.append(rule_id)
    if kind:
        sql += " AND kind = ?"
        params.append(kind)
    sql += " ORDER BY fired_at DESC LIMIT ?"
    params.append(min(max(limit, 1), 500))
    with store._conn() as c:
        rows = [dict(r) for r in c.execute(sql, params).fetchall()]
    return {"audit": rows, "total": len(rows)}


@app.get("/api/audit/decisions")
async def audit_decisions(
    member_id: int | None = None,
    days: int = 7,
    limit: int = 100,
    _member: dict = Depends(require_permission("audit.read")),
):
    if not _audit_table_exists("governance_decisions"):
        return {"audit": [], "total": 0}
    sql = "SELECT * FROM governance_decisions WHERE created_at > strftime('%s','now',?)"
    params: list[Any] = [f"-{max(days, 0)} days"]
    if member_id is not None:
        sql += " AND member_id = ?"
        params.append(member_id)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(min(max(limit, 1), 500))
    with store._conn() as c:
        rows = [dict(r) for r in c.execute(sql, params).fetchall()]
    return {"audit": rows, "total": len(rows)}


@app.get("/api/audit/notifications")
async def audit_notifications(
    status: str = "all",
    limit: int = 100,
    _member: dict = Depends(require_permission("audit.read")),
):
    if not _audit_table_exists("notification_queue"):
        return {"audit": [], "total": 0}
    sql = "SELECT * FROM notification_queue"
    params: list[Any] = []
    if status == "pending":
        sql += " WHERE delivered_at IS NULL AND failed_at IS NULL"
    elif status == "delivered":
        sql += " WHERE delivered_at IS NOT NULL"
    elif status == "failed":
        sql += " WHERE failed_at IS NOT NULL"
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(min(max(limit, 1), 500))
    with store._conn() as c:
        rows = [dict(r) for r in c.execute(sql, params).fetchall()]
    return {"audit": rows, "total": len(rows)}


@app.get("/api/audit/summary")
async def audit_summary(_member: dict = Depends(require_permission("audit.read"))):
    summary: dict[str, Any] = {}
    if _audit_table_exists("rule_audit_log"):
        with store._conn() as c:
            summary["rule_fires_30d"] = c.execute(
                "SELECT COUNT(*) FROM rule_audit_log WHERE fired_at > strftime('%s','now','-30 days')"
            ).fetchone()[0]
    if _audit_table_exists("governance_decisions"):
        with store._conn() as c:
            summary["decisions_30d"] = c.execute(
                "SELECT COUNT(*) FROM governance_decisions WHERE created_at > strftime('%s','now','-30 days')"
            ).fetchone()[0]
    if _audit_table_exists("notification_queue"):
        with store._conn() as c:
            summary["notifications_delivered"] = c.execute(
                "SELECT COUNT(*) FROM notification_queue WHERE delivered_at IS NOT NULL"
            ).fetchone()[0]
            summary["notifications_failed"] = c.execute(
                "SELECT COUNT(*) FROM notification_queue WHERE failed_at IS NOT NULL"
            ).fetchone()[0]
    with store._conn() as c:
        summary["open_alerts"] = c.execute(
            "SELECT COUNT(*) FROM alerts WHERE status = 'open'"
        ).fetchone()[0]
    return summary


@app.get("/api/audit/export")
async def audit_export(days: int = 30, _member: dict = Depends(require_permission("data.export"))):
    import hashlib

    payload = {
        "rules": (await audit_rules(days=days, limit=500))["audit"],
        "decisions": (await audit_decisions(days=days, limit=500))["audit"],
        "notifications": (await audit_notifications(limit=500))["audit"],
        "summary": await audit_summary(),
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    return {
        "export_format": "myhome-audit-v1",
        "days": days,
        "data": payload,
        "sha256": hashlib.sha256(blob).hexdigest(),
    }


# ─── 待确认动作（规则 then.control）───


@app.get("/api/actions/pending")
async def list_pending_actions(_member: dict = Depends(require_permission("device.control"))):
    actions = store.list_pending_actions("pending")
    return {"actions": actions, "total": len(actions)}


@app.post("/api/actions/{token}/confirm")
async def confirm_pending_action(
    token: str,
    x_twofa_token: str | None = Header(default=None, alias="X-2FA-Token"),
    _member: dict = Depends(require_permission("device.control")),
):
    action = store.get_pending_action(token)
    if not action:
        return JSONResponse({"error": "action not found"}, status_code=404)
    if action["status"] != "pending":
        return JSONResponse({"error": f"action already {action['status']}"}, status_code=409)
    if int(time.time()) > action["expires_at"]:
        store.set_pending_action_status(token, "expired")
        return JSONResponse({"error": "action expired"}, status_code=410)

    dev = store.get_device(action["device_id"]) or store.find_device_by_name(action["device_id"])
    if dev and dev.get("type") in CONTROL_CONFIRM_TYPES:
        from ..auth.session import TwoFactorSession

        if not x_twofa_token:
            return JSONResponse(
                {"error": "requires 2FA", "action": "remote_irreversible_control"},
                status_code=401,
            )
        ok, payload = TwoFactorSession.verify(x_twofa_token, "remote_irreversible_control")
        if not ok:
            return JSONResponse({"error": payload}, status_code=401)

    try:
        params = json.loads(action["params"] or "[]")
    except Exception:
        params = []
    try:
        result = registry.control(action["device_id"], action["action"], params)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)
    store.set_pending_action_status(token, "confirmed")
    return {"success": True, "result": str(result)}


@app.post("/api/actions/{token}/cancel")
async def cancel_pending_action(token: str, _member: dict = Depends(require_permission("device.control"))):
    action = store.get_pending_action(token)
    if not action:
        return JSONResponse({"error": "action not found"}, status_code=404)
    if action["status"] != "pending":
        return JSONResponse({"error": f"action already {action['status']}"}, status_code=409)
    store.set_pending_action_status(token, "cancelled")
    return {"success": True}


# ─── 启动时初始化（v0.9） ───


def _init_v09():
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

                -- 成员登录凭据
                CREATE TABLE IF NOT EXISTS member_credentials (
                  member_id INTEGER PRIMARY KEY,
                  password_hash TEXT NOT NULL,
                  updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
                );

                -- 治理决策审计
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
                  created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
                );

                -- 待确认控制动作
                CREATE TABLE IF NOT EXISTS pending_actions (
                  id INTEGER PRIMARY KEY,
                  token TEXT UNIQUE NOT NULL,
                  rule_id TEXT NOT NULL,
                  device_id TEXT NOT NULL,
                  action TEXT NOT NULL,
                  params TEXT,
                  status TEXT NOT NULL DEFAULT 'pending',
                  created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
                  expires_at INTEGER NOT NULL,
                  decided_at INTEGER
                );
                """
            )
    except Exception as e:
        logger.warning(f"v0.9 启动初始化失败: {e}")


@asynccontextmanager
async def lifespan(_app):
    await _startup()
    try:
        yield
    finally:
        await _shutdown()


app.router.lifespan_context = lifespan


# ─── WebSocket ───


@app.websocket("/ws/chat")
async def ws_chat(ws: WebSocket):
    if not websocket_authorized(ws):
        await ws.close(code=1008)
        return
    await ws.accept()
    session_id = None
    session: AgentSession | None = None

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)

            if msg.get("type") == "chat":
                if not session:
                    client, provider = _pick_llm_for_chat()
                    session = AgentSession(store, llm_client=client)
                    session._llm_provider = provider
                    session_id = session.session_id
                    await ws.send_json({"type": "session", "session_id": session_id})

                # v2.19 修订：mock / DeepSeek 都支持，不再 500
                reply = session.send(msg["message"])
                provider = getattr(session, "_llm_provider", None)
                if provider:
                    llm_router.record_usage(
                        provider,
                        _estimate_tokens(msg.get("message", "")) + 500,
                        _estimate_tokens(reply),
                    )
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
    if not websocket_authorized(ws):
        await ws.close(code=1008)
        return
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
