"""通知队列：规则/告警 -> notification_queue -> Telegram / 站内推送。"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)


class Notifier:
    """写入 notification_queue 并处理发送（当前实现 Telegram，WS 走告警轮询）。"""

    def __init__(self, store: Any, telegram_token: str | None = None, max_attempts: int = 3):
        self.store = store
        self.telegram_token = telegram_token if telegram_token is not None else os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.max_attempts = max_attempts

    def enqueue(
        self,
        *,
        member_id: int | None,
        channel: str,
        title: str,
        body: str,
        alert_id: int | None = None,
    ) -> int | None:
        """写一条待发送通知，返回 queue id。"""
        payload = json.dumps({"title": title, "body": body}, ensure_ascii=False)
        now = int(time.time())
        try:
            with self.store._conn() as c:
                cur = c.execute(
                    """INSERT INTO notification_queue
                       (alert_id, recipient_id, channel, payload, attempts, next_attempt_at, created_at)
                       VALUES (?, ?, ?, ?, 0, ?, ?)""",
                    (alert_id, member_id, channel, payload, now, now),
                )
                return cur.lastrowid
        except Exception as e:
            logger.error("通知入队失败: %s", e)
            return None

    def notify_rule_fire(self, alert_id: int, rule, confidence: float) -> int:
        """规则触发后，向已绑定 Telegram 的成员投递告警。"""
        sent = 0
        title = f"[{rule.severity}] {rule.description}"
        body = f"rule={rule.id} confidence={confidence:.2f}"
        for member in self.store.list_members():
            if self._telegram_chat_id(member["id"]) is None:
                continue
            if self.enqueue(
                member_id=member["id"],
                channel="telegram",
                title=title,
                body=body,
                alert_id=alert_id,
            ) is not None:
                sent += 1
        return sent

    def notify_alert(self, alert_id: int, title: str, body: str) -> int:
        """向已绑定 Telegram 的成员投递一条告警通知。"""
        sent = 0
        for member in self.store.list_members():
            if self._telegram_chat_id(member["id"]) is None:
                continue
            if self.enqueue(
                member_id=member["id"],
                channel="telegram",
                title=title,
                body=body,
                alert_id=alert_id,
            ) is not None:
                sent += 1
        return sent

    def process_queue(self, limit: int = 50) -> dict:
        """处理到期通知，返回 {sent, failed}。"""
        sent = failed = 0
        now = int(time.time())
        try:
            with self.store._conn() as c:
                rows = c.execute(
                    """SELECT * FROM notification_queue
                       WHERE delivered_at IS NULL AND failed_at IS NULL AND next_attempt_at <= ?
                       ORDER BY id LIMIT ?""",
                    (now, limit),
                ).fetchall()
            for row in rows:
                if self._send(row):
                    sent += 1
                else:
                    failed += 1
        except Exception as e:
            logger.error("通知队列处理失败: %s", e)
        return {"sent": sent, "failed": failed}

    def _send(self, row) -> bool:
        channel = row["channel"]
        try:
            payload = json.loads(row["payload"] or "{}")
            if channel == "telegram":
                ok = self._send_telegram(row, payload)
            elif channel == "ws":
                # 站内通知走 ws/events 的开放告警轮询，入队即视为已投递
                ok = True
            else:
                ok = False
        except Exception as e:
            logger.error("通知发送异常 %s#%s: %s", channel, row["id"], e)
            ok = False

        attempts = row["attempts"] + 1
        now = int(time.time())
        with self.store._conn() as c:
            if ok:
                c.execute(
                    "UPDATE notification_queue SET attempts = ?, delivered_at = ? WHERE id = ?",
                    (attempts, now, row["id"]),
                )
            else:
                c.execute(
                    "UPDATE notification_queue SET attempts = ?, last_error = ?, next_attempt_at = ? WHERE id = ?",
                    (attempts, "send failed", now + min(300, 30 * attempts), row["id"]),
                )
                if attempts >= self.max_attempts:
                    c.execute(
                        "UPDATE notification_queue SET failed_at = ? WHERE id = ?",
                        (now, row["id"]),
                    )
        return ok

    def _send_telegram(self, row, payload: dict) -> bool:
        if not self.telegram_token:
            return False
        import requests

        chat_id = self._telegram_chat_id(row["recipient_id"])
        if chat_id is None:
            return False
        text = f"{payload.get('title', '')}\n{payload.get('body', '')}"[:4000]
        resp = requests.post(
            f"https://api.telegram.org/bot{self.telegram_token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
        return bool(resp.ok)

    def _telegram_chat_id(self, member_id) -> int | None:
        try:
            with self.store._conn() as c:
                row = c.execute(
                    "SELECT preferences FROM members WHERE id = ?", (member_id,)
                ).fetchone()
            if not row:
                return None
            prefs = json.loads(row["preferences"] or "{}")
            chat_id = prefs.get("telegram_chat_id")
            return int(chat_id) if chat_id else None
        except Exception:
            return None
