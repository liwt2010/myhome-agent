"""历史数据导入：把已积累的家庭数据（CSV）规范化入库。

支持两种 CSV 格式：
1. 时序: device_id,metric,value,ts        （温湿度、能耗等采样数据）
2. 事件: device_id,kind,detail,ts         （开门、人体移动等离散事件）

ts 支持 "YYYY-MM-DD HH:MM:SS" 或 ISO8601 或 unix 秒。
"""
from __future__ import annotations

import csv
import logging
from datetime import datetime
from pathlib import Path

from ..memory.store import Store

logger = logging.getLogger(__name__)


def _parse_ts(raw: str) -> str:
    raw = raw.strip()
    if raw.isdigit():
        return datetime.fromtimestamp(int(raw)).strftime("%Y-%m-%d %H:%M:%S")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(raw[:19], fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    raise ValueError(f"无法解析时间: {raw}")


def import_readings_csv(store: Store, path: str | Path) -> int:
    n = 0
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            store.add_reading(
                device_id=row["device_id"].strip(),
                metric=row["metric"].strip(),
                value=row["value"],
                ts=_parse_ts(row["ts"]),
            )
            n += 1
    logger.info("导入 %d 条时序记录: %s", n, path)
    return n


def import_events_csv(store: Store, path: str | Path) -> int:
    n = 0
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            store.add_event(
                kind=row["kind"].strip(),
                device_id=(row.get("device_id") or "").strip() or None,
                detail={"raw": row.get("detail", "")},
                ts=_parse_ts(row["ts"]),
            )
            n += 1
    logger.info("导入 %d 条事件记录: %s", n, path)
    return n


def import_auto(store: Store, path: str | Path) -> int:
    """根据表头自动识别格式。"""
    with open(path, encoding="utf-8-sig") as f:
        header = set(h.strip() for h in (f.readline() or "").split(","))
    if {"metric", "value"} <= header:
        return import_readings_csv(store, path)
    if "kind" in header:
        return import_events_csv(store, path)
    raise ValueError("无法识别 CSV 格式：表头需含 metric,value 或 kind")
