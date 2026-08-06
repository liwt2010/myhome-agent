"""SQLite 家庭数据存储。

单文件数据库，线程安全（每次操作独立连接 + WAL），
承载设备目录、时序数据、事件、成员、作息、告警与长期记忆。
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Optional

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class Store:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    # ---------- 设备 ----------

    def upsert_device(self, dev: dict[str, Any]) -> None:
        with self._conn() as c:
            c.execute(
                """INSERT INTO devices (id, name, model, type, room, ip, token, source, online, extra, updated_at)
                   VALUES (:id, :name, :model, :type, :room, :ip, :token, :source, :online, :extra, datetime('now','localtime'))
                   ON CONFLICT(id) DO UPDATE SET
                     name=excluded.name, model=excluded.model,
                     type=COALESCE(excluded.type, devices.type),
                     room=COALESCE(excluded.room, devices.room),
                     ip=COALESCE(excluded.ip, devices.ip),
                     token=COALESCE(excluded.token, devices.token),
                     online=excluded.online, extra=excluded.extra,
                     updated_at=datetime('now','localtime')""",
                {
                    "id": dev["id"], "name": dev.get("name", dev["id"]),
                    "model": dev.get("model"), "type": dev.get("type"),
                    "room": dev.get("room"), "ip": dev.get("ip"),
                    "token": dev.get("token"), "source": dev.get("source", "cloud"),
                    "online": int(dev.get("online", 0)),
                    "extra": json.dumps(dev.get("extra", {}), ensure_ascii=False),
                },
            )

    def list_devices(self, room: str | None = None, type_: str | None = None) -> list[dict]:
        q = "SELECT * FROM devices WHERE 1=1"
        args: list[Any] = []
        if room:
            q += " AND room = ?"
            args.append(room)
        if type_:
            q += " AND type = ?"
            args.append(type_)
        with self._conn() as c:
            return [dict(r) for r in c.execute(q + " ORDER BY room, name", args)]

    def get_device(self, device_id: str) -> Optional[dict]:
        with self._conn() as c:
            r = c.execute("SELECT * FROM devices WHERE id = ?", (device_id,)).fetchone()
            return dict(r) if r else None

    def find_device_by_name(self, name: str) -> Optional[dict]:
        with self._conn() as c:
            r = c.execute(
                "SELECT * FROM devices WHERE name LIKE ? ORDER BY length(name) LIMIT 1",
                (f"%{name}%",),
            ).fetchone()
            return dict(r) if r else None

    # ---------- 时序 ----------

    def add_reading(self, device_id: str, metric: str, value: Any, ts: str | None = None) -> None:
        num, text = (None, str(value))
        try:
            num, text = float(value), None
        except (TypeError, ValueError):
            pass
        with self._conn() as c:
            c.execute(
                "INSERT INTO readings (device_id, metric, value, value_text, ts) "
                "VALUES (?, ?, ?, ?, COALESCE(?, datetime('now','localtime')))",
                (device_id, metric, num, text, ts),
            )

    def latest_readings(self, device_id: str) -> dict[str, Any]:
        """某设备每个指标的最新值。"""
        with self._conn() as c:
            rows = c.execute(
                """SELECT metric, value, value_text, MAX(ts) AS ts
                   FROM readings WHERE device_id = ? GROUP BY metric""",
                (device_id,),
            ).fetchall()
        return {r["metric"]: {"value": r["value"] if r["value"] is not None else r["value_text"], "ts": r["ts"]} for r in rows}

    def query_readings(self, device_id: str, metric: str, since_hours: int = 24, limit: int = 500) -> list[dict]:
        since = (datetime.now() - timedelta(hours=since_hours)).strftime("%Y-%m-%d %H:%M:%S")
        with self._conn() as c:
            return [dict(r) for r in c.execute(
                "SELECT metric, value, value_text, ts FROM readings "
                "WHERE device_id = ? AND metric = ? AND ts >= ? ORDER BY ts DESC LIMIT ?",
                (device_id, metric, since, limit),
            )]

    # ---------- 事件 ----------

    def add_event(self, kind: str, device_id: str | None = None, member_id: int | None = None,
                  detail: dict | None = None, ts: str | None = None) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO events (device_id, member_id, kind, detail, ts) "
                "VALUES (?, ?, ?, ?, COALESCE(?, datetime('now','localtime')))",
                (device_id, member_id, kind, json.dumps(detail or {}, ensure_ascii=False), ts),
            )

    def query_events(self, kind: str | None = None, since_hours: int = 24, limit: int = 200) -> list[dict]:
        since = (datetime.now() - timedelta(hours=since_hours)).strftime("%Y-%m-%d %H:%M:%S")
        q = "SELECT * FROM events WHERE ts >= ?"
        args: list[Any] = [since]
        if kind:
            q += " AND kind = ?"
            args.append(kind)
        q += " ORDER BY ts DESC LIMIT ?"
        args.append(limit)
        with self._conn() as c:
            return [dict(r) for r in c.execute(q, args)]

    # ---------- 成员 ----------

    def upsert_member(self, name: str, role: str | None = None,
                      preferences: dict | None = None, devices: list | None = None) -> int:
        with self._conn() as c:
            c.execute(
                """INSERT INTO members (name, role, preferences, devices) VALUES (?, ?, ?, ?)
                   ON CONFLICT(name) DO UPDATE SET
                     role=COALESCE(excluded.role, members.role),
                     preferences=COALESCE(excluded.preferences, members.preferences),
                     devices=COALESCE(excluded.devices, members.devices)""",
                (name, role,
                 json.dumps(preferences, ensure_ascii=False) if preferences else None,
                 json.dumps(devices, ensure_ascii=False) if devices else None),
            )
            row = c.execute("SELECT id FROM members WHERE name = ?", (name,)).fetchone()
            return row["id"]

    def list_members(self) -> list[dict]:
        with self._conn() as c:
            members = [dict(r) for r in c.execute("SELECT * FROM members")]
        for m in members:
            m["preferences"] = json.loads(m["preferences"]) if m["preferences"] else {}
            m["devices"] = json.loads(m["devices"]) if m["devices"] else []
        return members

    def set_presence(self, member_id: int, at_home: bool, room: str | None = None,
                     evidence: str | None = None) -> None:
        with self._conn() as c:
            c.execute(
                """INSERT INTO presence (member_id, at_home, room, since, evidence)
                   VALUES (?, ?, ?, datetime('now','localtime'), ?)
                   ON CONFLICT(member_id) DO UPDATE SET
                     at_home=excluded.at_home, room=excluded.room,
                     since=CASE WHEN presence.at_home != excluded.at_home
                                THEN excluded.since ELSE presence.since END,
                     evidence=excluded.evidence""",
                (member_id, int(at_home), room, evidence),
            )

    def get_presence(self) -> list[dict]:
        with self._conn() as c:
            return [dict(r) for r in c.execute(
                """SELECT m.name, m.role, p.at_home, p.room, p.since, p.evidence
                   FROM members m LEFT JOIN presence p ON p.member_id = m.id""")]

    # ---------- 作息 ----------

    def upsert_routine(self, kind: str, hour: int, value: float, confidence: float,
                       member_id: int | None = None, weekday: int | None = None) -> None:
        with self._conn() as c:
            c.execute(
                """INSERT INTO routines (member_id, weekday, hour, kind, value, confidence, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                   ON CONFLICT(member_id, weekday, hour, kind) DO UPDATE SET
                     value=excluded.value, confidence=excluded.confidence,
                     updated_at=excluded.updated_at""",
                (member_id, weekday, hour, kind, value, confidence),
            )

    def get_routines(self, kind: str | None = None) -> list[dict]:
        q, args = "SELECT * FROM routines", []
        if kind:
            q += " WHERE kind = ?"
            args.append(kind)
        with self._conn() as c:
            return [dict(r) for r in c.execute(q, args)]

    # ---------- 告警 ----------

    def add_alert(self, level: str, title: str, detail: str = "", source: str = "hard_rule") -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO alerts (level, title, detail, source) VALUES (?, ?, ?, ?)",
                (level, title, detail, source),
            )
            return cur.lastrowid

    def list_alerts(self, status: str = "open", limit: int = 50) -> list[dict]:
        with self._conn() as c:
            return [dict(r) for r in c.execute(
                "SELECT * FROM alerts WHERE status = ? ORDER BY ts DESC LIMIT ?", (status, limit))]

    def ack_alert(self, alert_id: int) -> None:
        with self._conn() as c:
            c.execute("UPDATE alerts SET status='acked' WHERE id = ?", (alert_id,))

    # ---------- 记忆 ----------

    def remember(self, content: str, tags: str = "", member_id: int | None = None) -> None:
        with self._conn() as c:
            c.execute("INSERT INTO memories (content, tags, member_id) VALUES (?, ?, ?)",
                      (content, tags, member_id))

    def recall(self, query: str = "", limit: int = 20) -> list[dict]:
        with self._conn() as c:
            if query:
                return [dict(r) for r in c.execute(
                    "SELECT * FROM memories WHERE content LIKE ? OR tags LIKE ? "
                    "ORDER BY id DESC LIMIT ?", (f"%{query}%", f"%{query}%", limit))]
            return [dict(r) for r in c.execute(
                "SELECT * FROM memories ORDER BY id DESC LIMIT ?", (limit,))]

    # ---------- 对话历史 ----------

    def append_chat(self, session_id: str, role: str, content: Any) -> None:
        with self._conn() as c:
            c.execute("INSERT INTO chat_history (session_id, role, content) VALUES (?, ?, ?)",
                      (session_id, role, json.dumps(content, ensure_ascii=False)))

    def get_chat(self, session_id: str, limit_turns: int = 30) -> list[dict]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT role, content FROM chat_history WHERE session_id = ? "
                "ORDER BY id DESC LIMIT ?", (session_id, limit_turns * 2),
            ).fetchall()
        return [{"role": r["role"], "content": json.loads(r["content"])} for r in reversed(rows)]
