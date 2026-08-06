"""成员在场推断。

务实路线（不做人脸/声纹）：
1. 成员档案里登记关联设备（手机在米家的设备 id / 手环 / 蓝牙 mac）
2. 关联设备在线状态变化 → 回家/离家事件
3. 房间人体传感器 + 时间规律 → 粗略推断"现在在哪个房间"
"""
from __future__ import annotations

import logging

from ..memory.store import Store

logger = logging.getLogger(__name__)


def infer_presence(store: Store) -> None:
    """基于成员关联设备的在线状态更新在场表。"""
    members = store.list_members()
    devices = {d["id"]: d for d in store.list_devices()}
    for m in members:
        linked = [devices[did] for did in m["devices"] if did in devices]
        if not linked:
            continue
        online = [d for d in linked if d.get("online")]
        was = _current(store, m["id"])
        now_home = bool(online)
        if was is None or was != now_home:
            evidence = ("、".join(d["name"] for d in online) + " 在线") if online \
                       else "关联设备全部离线"
            store.set_presence(m["id"], now_home, evidence=evidence)
            store.add_event(kind="arrive" if now_home else "leave",
                            member_id=m["id"], detail={"evidence": evidence})
            logger.info("成员 %s %s (%s)", m["name"], "回家" if now_home else "离家", evidence)


def _current(store: Store, member_id: int) -> bool | None:
    """读取某成员当前在场状态；presence 表无记录时返回 None。"""
    members = {m["name"]: m for m in store.list_members()}
    for p in store.get_presence():
        m = members.get(p["name"])
        if m and m["id"] == member_id:
            return None if p["at_home"] is None else bool(p["at_home"])
    return None
