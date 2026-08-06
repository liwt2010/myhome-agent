"""智能体工具集：Claude Agent 可调用的家庭工具函数。

每个工具返回一个统一的 dict:
  {"success": bool, "data": Any, "message": str}
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from ..analytics.anomaly import check_inactivity, check_hard_rules
from ..analytics.presence import infer_presence
from ..analytics.routines import routine_summary
from ..config import CONFIG, CONTROL_CONFIRM_TYPES
from ..memory.store import Store

# ─── 工具定义（传给 Claude 的 JSON Schema） ───

TOOLS: list[dict[str, Any]] = [
    {
        "name": "list_devices",
        "description": "列出家中所有智能设备，可按房间或类型筛选。",
        "input_schema": {
            "type": "object",
            "properties": {
                "room": {"type": "string", "description": "按房间名筛选，如 客厅/卧室/厨房"},
                "type": {"type": "string", "description": "按设备类型筛选，如 light/sensor_ht/lock/plug"},
            },
            "required": [],
        },
    },
    {
        "name": "get_device_state",
        "description": "获取某个设备当前所有指标的最新值（温度、湿度、开关状态等）。",
        "input_schema": {
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "设备 ID 或名称"},
            },
            "required": ["device_id"],
        },
    },
    {
        "name": "query_readings",
        "description": "查询某个设备某项指标的历史记录，用于了解趋势。",
        "input_schema": {
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "设备 ID 或名称"},
                "metric": {"type": "string", "description": "指标名，如 temperature/humidity/power"},
                "hours": {"type": "integer", "description": "回溯小时数，默认 24"},
                "limit": {"type": "integer", "description": "最多返回条数，默认 100"},
            },
            "required": ["device_id", "metric"],
        },
    },
    {
        "name": "query_events",
        "description": "查询近期家庭事件（开门、有人移动、回家、离家等）。",
        "input_schema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "description": "事件类型过滤: motion/door_open/arrive/leave/control/button"},
                "hours": {"type": "integer", "description": "回溯小时数，默认 24"},
                "limit": {"type": "integer", "description": "最多返回条数，默认 50"},
            },
            "required": [],
        },
    },
    {
        "name": "control_device",
        "description": "控制家中设备（开关灯、调节温度等）。涉及门锁、燃气、摄像头类设备需要二次确认。",
        "input_schema": {
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "设备 ID 或名称"},
                "action": {"type": "string", "description": "动作: on/off 或具体指令名"},
                "params": {"type": "array", "items": {"type": "string"}, "description": "指令参数（可选）"},
            },
            "required": ["device_id", "action"],
        },
    },
    {
        "name": "list_members",
        "description": "列出所有家庭成员及其档案信息。",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_member_status",
        "description": "查询所有家庭成员当前是否在家、可能在哪个房间。",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_home_summary",
        "description": "获取家庭整体概况：设备数量、在线状态、成员在场、近期告警、作息规律。",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_alerts",
        "description": "查看当前未处理的告警。",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "最多返回条数，默认 20"},
            },
            "required": [],
        },
    },
    {
        "name": "remember",
        "description": "记住一条重要信息，用于长期记忆。比如家人的偏好、重要约定等。",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "要记住的内容"},
                "tags": {"type": "string", "description": "标签，逗号分隔，便于后续检索"},
            },
            "required": ["content"],
        },
    },
    {
        "name": "recall",
        "description": "从长期记忆中检索与查询相关的内容。",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "limit": {"type": "integer", "description": "最多返回条数，默认 10"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_routines",
        "description": "查看家庭学到的作息规律（起床时间、就寝时间、活动密度等）。",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "check_anomaly",
        "description": "主动检查当前是否存在异常（无活动、设备离线等）。",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]

# ─── 工具实现 ───


def _resolve_device(store: Store, device_id: str) -> dict:
    """按 ID 或名称查找设备，找不到抛异常。"""
    dev = store.get_device(device_id) or store.find_device_by_name(device_id)
    if not dev:
        raise ValueError(f"找不到设备: {device_id}")
    return dev


def _tool_list_devices(store: Store, args: dict) -> dict:
    devices = store.list_devices(room=args.get("room"), type_=args.get("type"))
    # 精简返回，只保留关键字段
    summary = []
    for d in devices:
        summary.append({
            "id": d["id"],
            "name": d["name"],
            "type": d["type"],
            "room": d.get("room", ""),
            "online": bool(d.get("online")),
            "model": d.get("model", ""),
        })
    return {"success": True, "data": summary, "message": f"共 {len(summary)} 台设备"}


def _tool_get_device_state(store: Store, args: dict) -> dict:
    dev = _resolve_device(store, args["device_id"])
    readings = store.latest_readings(dev["id"])
    return {
        "success": True,
        "data": {
            "device": {"id": dev["id"], "name": dev["name"], "type": dev["type"],
                       "room": dev.get("room", ""), "online": bool(dev.get("online"))},
            "readings": readings,
        },
        "message": f"{dev['name']} 共 {len(readings)} 项指标",
    }


def _tool_query_readings(store: Store, args: dict) -> dict:
    dev = _resolve_device(store, args["device_id"])
    rows = store.query_readings(
        dev["id"], args["metric"],
        since_hours=args.get("hours", 24),
        limit=args.get("limit", 100),
    )
    return {"success": True, "data": rows, "message": f"{dev['name']} {args['metric']} 共 {len(rows)} 条记录"}


def _tool_query_events(store: Store, args: dict) -> dict:
    rows = store.query_events(
        kind=args.get("kind"),
        since_hours=args.get("hours", 24),
        limit=args.get("limit", 50),
    )
    return {"success": True, "data": rows, "message": f"共 {len(rows)} 条事件"}


def _tool_control_device(store: Store, registry, args: dict) -> dict:
    dev = _resolve_device(store, args["device_id"])
    action = args["action"]
    params = args.get("params")

    # 需要二次确认的设备类型
    if dev.get("type") in CONTROL_CONFIRM_TYPES:
        return {
            "success": False,
            "data": None,
            "message": f"⚠️ {dev['name']} 属于 {dev['type']} 类型，需要用户二次确认后才能执行 {action}。请先向用户确认。",
            "needs_confirm": True,
            "confirm_detail": {"device_id": dev["id"], "device_name": dev["name"], "action": action, "params": params},
        }

    result = registry.control(dev["id"], action, params)
    return {"success": True, "data": {"result": str(result)}, "message": f"已对 {dev['name']} 执行 {action}"}


def _tool_list_members(store: Store, args: dict) -> dict:
    members = store.list_members()
    return {"success": True, "data": members, "message": f"共 {len(members)} 位家庭成员"}


def _tool_get_member_status(store: Store, args: dict) -> dict:
    infer_presence(store)  # 先刷新在场推断
    presence = store.get_presence()
    return {"success": True, "data": presence, "message": f"共 {len(presence)} 位成员"}


def _tool_get_home_summary(store: Store, args: dict) -> dict:
    devices = store.list_devices()
    online = [d for d in devices if d.get("online")]
    infer_presence(store)
    presence = store.get_presence()
    alerts = store.list_alerts(status="open", limit=10)
    routines = routine_summary(store)

    summary = {
        "devices": {"total": len(devices), "online": len(online)},
        "members": presence,
        "open_alerts": len(alerts),
        "recent_alerts": [{"level": a["level"], "title": a["title"], "ts": a["ts"]} for a in alerts[:5]],
        "routines": routines,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    return {"success": True, "data": summary, "message": "家庭概况"}


def _tool_get_alerts(store: Store, args: dict) -> dict:
    alerts = store.list_alerts(status="open", limit=args.get("limit", 20))
    return {"success": True, "data": alerts, "message": f"共 {len(alerts)} 条未处理告警"}


def _tool_remember(store: Store, args: dict) -> dict:
    store.remember(args["content"], tags=args.get("tags", ""))
    return {"success": True, "data": None, "message": "已记住"}


def _tool_recall(store: Store, args: dict) -> dict:
    memories = store.recall(query=args["query"], limit=args.get("limit", 10))
    return {"success": True, "data": memories, "message": f"找到 {len(memories)} 条相关记忆"}


def _tool_get_routines(store: Store, args: dict) -> dict:
    routines = store.get_routines()
    summary = routine_summary(store)
    return {"success": True, "data": {"routines": routines, "summary": summary}, "message": summary}


def _tool_check_anomaly(store: Store, args: dict) -> dict:
    check_inactivity(store, int(CONFIG.get("analytics", {}).get("inactivity_grace_minutes", 180)))
    alerts = store.list_alerts(status="open", limit=10)
    return {"success": True, "data": alerts, "message": f"当前 {len(alerts)} 条未处理告警"}


# 工具名 → 实现函数
_TOOL_HANDLERS: dict[str, Any] = {
    "list_devices": _tool_list_devices,
    "get_device_state": _tool_get_device_state,
    "query_readings": _tool_query_readings,
    "query_events": _tool_query_events,
    "control_device": _tool_control_device,
    "list_members": _tool_list_members,
    "get_member_status": _tool_get_member_status,
    "get_home_summary": _tool_get_home_summary,
    "get_alerts": _tool_get_alerts,
    "remember": _tool_remember,
    "recall": _tool_recall,
    "get_routines": _tool_get_routines,
    "check_anomaly": _tool_check_anomaly,
}


def execute_tool(name: str, args: dict, store: Store, registry=None) -> dict:
    """执行一个工具调用，返回统一格式的结果 dict。

    registry 仅在 control_device 时需要，其他工具传 None 即可。
    """
    handler = _TOOL_HANDLERS.get(name)
    if not handler:
        return {"success": False, "data": None, "message": f"未知工具: {name}"}
    try:
        if name == "control_device":
            return handler(store, registry, args)
        return handler(store, args)
    except ValueError as e:
        return {"success": False, "data": None, "message": str(e)}
    except Exception as e:
        return {"success": False, "data": None, "message": f"工具执行出错: {e}"}


# v2.19 §53 工具调用入口（OpenAI 兼容格式 + 抽象 LLM 客户端）
# 用于上层 agent 调用 LLM 时，把 TOOLS 转成 OpenAI tools schema

def to_openai_tools() -> list[dict]:
    """把 v0.1 工具定义转成 OpenAI tools schema 格式

    v0.1 实现：本地静态映射
    v0.2 实现：从 capabilities 表动态生成
    """
    result = []
    for t in TOOLS:
        result.append(
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                },
            }
        )
    return result