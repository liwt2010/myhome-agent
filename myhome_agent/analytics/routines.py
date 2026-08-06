"""作息规律学习。

从 events 聚合"星期 × 小时"的活动直方图，学出：
- first_activity: 每天第一次活动的典型小时（起床基线）
- last_activity:  每天最后一次活动的典型小时（就寝基线）
- motion_density: 每小时活动密度（用于软异常对比）
"""
from __future__ import annotations

import json
import logging
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta

from ..memory.store import Store

logger = logging.getLogger(__name__)

ACTIVITY_KINDS = ("motion", "door_open", "control", "button")


def learn_routines(store: Store, window_days: int = 30) -> None:
    since = (datetime.now() - timedelta(days=window_days)).strftime("%Y-%m-%d %H:%M:%S")
    with store._conn() as c:
        rows = c.execute(
            f"""SELECT ts FROM events
                WHERE kind IN ({','.join('?' * len(ACTIVITY_KINDS))}) AND ts >= ?""",
            (*ACTIVITY_KINDS, since),
        ).fetchall()

    if not rows:
        logger.info("暂无活动事件，跳过作息学习")
        return

    # 按日期分组求每日首末活动小时；按 (weekday, hour) 求密度
    first_by_day: dict[str, int] = {}
    last_by_day: dict[str, int] = {}
    density: dict[tuple[int, int], int] = defaultdict(int)
    days_seen: set[str] = set()

    for r in rows:
        dt = datetime.strptime(r["ts"][:19], "%Y-%m-%d %H:%M:%S")
        day = dt.strftime("%Y-%m-%d")
        days_seen.add(day)
        first_by_day[day] = min(first_by_day.get(day, 24), dt.hour)
        last_by_day[day] = max(last_by_day.get(day, -1), dt.hour)
        density[(dt.weekday(), dt.hour)] += 1

    n_days = max(len(days_seen), 1)
    confidence = min(n_days / window_days, 1.0)

    avg_first = sum(first_by_day.values()) / len(first_by_day)
    avg_last = sum(last_by_day.values()) / len(last_by_day)
    store.upsert_routine("first_activity", hour=round(avg_first), value=avg_first, confidence=confidence)
    store.upsert_routine("last_activity", hour=round(avg_last), value=avg_last, confidence=confidence)

    n_weeks = max(n_days / 7, 1)
    for (weekday, hour), count in density.items():
        store.upsert_routine("motion_density", hour=hour, weekday=weekday,
                             value=count / n_weeks, confidence=confidence)

    logger.info("作息学习完成: 典型起床 %.1f 点 / 就寝 %.1f 点 (置信度 %.2f, %d 天数据)",
                avg_first, avg_last, confidence, n_days)


def routine_summary(store: Store) -> str:
    """给智能体 system prompt 用的作息摘要。"""
    routines = store.get_routines()
    if not routines:
        return "尚未学习到家庭作息规律。"
    parts = []
    for r in routines:
        if r["kind"] == "first_activity":
            parts.append(f"家庭典型起床时间约 {r['value']:.0f} 点（置信度 {r['confidence']:.0%}）")
        elif r["kind"] == "last_activity":
            parts.append(f"典型就寝时间约 {r['value']:.0f} 点")
    return "；".join(parts) if parts else "作息数据积累中。"
