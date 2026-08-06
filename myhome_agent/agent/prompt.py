"""智能体系统提示词模板。

给出一个动态的家庭上下文快照，指导 Claude 扮演家庭智能体的角色。
"""

from __future__ import annotations

from datetime import datetime

from ..analytics.presence import infer_presence
from ..analytics.routines import routine_summary
from ..memory.store import Store

BASE_SYSTEM_PROMPT = """你是「小管家」，一个温暖的、住在家里的智能体。
你的职责是帮助家庭成员更好地生活：关注家中环境、设备状态、家人作息，
在需要时主动提醒，在询问时给出贴心的建议。

## 你的性格
- 温暖、体贴，像家人一样说话
- 简洁但不冰冷，回复长度视问题而定
- 遇到异常情况时要有紧迫感，但不要制造恐慌
- 不清楚的事情直接说不知道，不编造

## 家庭背景
你生活在用户家中，家里安装了全套米家智能设备。
你能看到设备的实时状态、家人的活动记录、学到的作息规律。
你可以帮助控制设备、查看状态、记住重要事项。

## 安全原则
- 涉及门锁、燃气、摄像头的操作必须向用户二次确认
- 不要在没有用户明确指令的情况下主动控制设备（告警场景除外）
- 用户偏好（空调温度、灯光亮度等）应该记住，后续主动应用

## 当前家庭状态
{home_snapshot}

## 当前时间
{current_time}
"""


def build_system_prompt(store: Store) -> str:
    """构建包含动态家庭快照的完整 system prompt。"""
    now = datetime.now()

    # 设备概况
    devices = store.list_devices()
    online = sum(1 for d in devices if d.get("online"))
    device_summary = f"家中共 {len(devices)} 台设备，{online} 台在线。"

    # 成员在场
    infer_presence(store)
    presence = store.get_presence()
    if presence:
        member_lines = []
        for p in presence:
            status = "在家" if p.get("at_home") else "离家"
            room = f"（{p['room']}）" if p.get("room") else ""
            member_lines.append(f"  - {p['name']}（{p.get('role', '成员')}）: {status}{room}")
        member_summary = "成员状态：\n" + "\n".join(member_lines)
    else:
        member_summary = "尚未设置家庭成员档案。"

    # 作息
    routines = routine_summary(store)

    # 告警
    open_alerts = store.list_alerts(status="open", limit=10)
    if open_alerts:
        alert_lines = [f"  - [{a['level']}] {a['title']}（{a['ts']}）" for a in open_alerts]
        alert_summary = "⚠️ 当前未处理告警：\n" + "\n".join(alert_lines)
    else:
        alert_summary = "当前无未处理告警。"

    snapshot = "\n\n".join([
        device_summary,
        member_summary,
        f"作息规律: {routines}",
        alert_summary,
    ])

    return BASE_SYSTEM_PROMPT.format(
        home_snapshot=snapshot,
        current_time=now.strftime("%Y年%m月%d日 %H:%M，周%a"),
    )


def quick_system_prompt(store: Store) -> str:
    """轻量版 prompt，用于快速上下文刷新。"""
    now = datetime.now()
    devices = store.list_devices()
    online = sum(1 for d in devices if d.get("online"))
    routines = routine_summary(store)
    alerts = store.list_alerts(status="open", limit=5)

    return (
        f"时间: {now.strftime('%Y-%m-%d %H:%M')} | "
        f"设备: {len(devices)}台/{online}在线 | "
        f"作息: {routines} | "
        f"告警: {len(alerts)}条"
    )