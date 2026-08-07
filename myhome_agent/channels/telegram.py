"""Telegram bot 双工 v0.5（§50 升级路径 2）

v0.5 实现：
- python-telegram-bot 接入
- bot token Fernet 加密
- per-member chat_id 绑定（/bind 命令）
- 命令：/chat /status /rules /devices /alerts
- 普通消息 → 转给 Agent 对话
- 远程控制走 §5.3 高危确认

v0.5 不做：
- 群组（v0.5.2）
- 内联键盘（v1.0）
- 视频片段发送（v0.5.3）
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
from typing import Any

from ..vision.crypto import encrypt, decrypt

logger = logging.getLogger(__name__)


ENV_BOT_TOKEN = "TELEGRAM_BOT_TOKEN"


class TelegramBot:
    """v0.5 Telegram bot 封装

    用法：
        bot = TelegramBot(token="...", agent=my_agent, store=my_store)
        bot.start()  # 启动 polling
        bot.stop()
    """

    def __init__(
        self,
        token: str,
        agent: Any | None = None,
        store: Any | None = None,
    ):
        self.token = token
        self.agent = agent
        self.store = store
        raw_allowed = os.getenv("MYHOME_TELEGRAM_ALLOWED_CHAT_IDS", "")
        self.allowed_chat_ids = {
            int(x.strip()) for x in raw_allowed.split(",") if x.strip().lstrip("-").isdigit()
        }
        self._application = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    def _authorized(self, update) -> bool:
        chat_id = update.effective_chat.id if update.effective_chat else None
        return chat_id is not None and chat_id in self.allowed_chat_ids

    def start(self) -> None:
        """后台线程启动 bot"""
        if self._running:
            return
        try:
            from telegram.ext import Application, CommandHandler, MessageHandler, filters
        except ImportError:
            logger.error("未安装 python-telegram-bot")
            return

        self._application = Application.builder().token(self.token).build()

        # 注册命令
        self._application.add_handler(CommandHandler("start", self._cmd_start))
        self._application.add_handler(CommandHandler("bind", self._cmd_bind))
        self._application.add_handler(CommandHandler("chat", self._cmd_chat))
        self._application.add_handler(CommandHandler("status", self._cmd_status))
        self._application.add_handler(CommandHandler("rules", self._cmd_rules))
        self._application.add_handler(CommandHandler("devices", self._cmd_devices))
        self._application.add_handler(CommandHandler("alerts", self._cmd_alerts))
        self._application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message))

        # 后台线程跑 polling
        self._running = True
        self._thread = threading.Thread(target=self._run_polling, daemon=True, name="tg-bot")
        self._thread.start()
        logger.info("Telegram bot 启动")

    def stop(self) -> None:
        self._running = False
        if self._application:
            self._application.stop()

    def _run_polling(self) -> None:
        """polling 循环（独立事件循环）"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        try:
            self._application.run_polling(stop_signals=None, close_loop=False)
        except Exception as e:
            logger.error(f"TG bot 异常: {e}")
        finally:
            self._running = False

    # ============================================================
    # 命令处理
    # ============================================================

    async def _cmd_start(self, update, context):
        await update.message.reply_text(
            "👋 你好！我是 myhome-agent 家庭管家。\n\n"
            "📱 可用命令：\n"
            "/bind <家庭成员名> - 绑定你的 chat_id\n"
            "/chat <消息> - 与管家对话\n"
            "/status - 家庭状态\n"
            "/rules - 规则列表\n"
            "/devices - 设备列表\n"
            "/alerts - 当前告警\n\n"
            "请先 /bind 你的身份。"
        )

    async def _cmd_bind(self, update, context):
        """绑定 chat_id 到 member"""
        if not self._authorized(update):
            await update.message.reply_text("❌ 未授权：请在 .env 配置 MYHOME_TELEGRAM_ALLOWED_CHAT_IDS")
            return
        args = context.args
        if not args:
            await update.message.reply_text("用法：/bind <你的名字>")
            return
        member_name = " ".join(args)
        # v0.5 简化：按名字查 member_id
        if self.store is None:
            await update.message.reply_text("❌ store 未配置")
            return
        try:
            member = self._find_member_by_name(member_name)
            if member is None:
                await update.message.reply_text(
                    f"❌ 找不到成员 '{member_name}'。可用：\n" +
                    "\n".join([m['name'] for m in self._list_members()])
                )
                return
            self._save_chat_id(member['id'], update.effective_chat.id)
            await update.message.reply_text(
                f"✅ 已绑定 {member['name']}！\n现在可以 /chat 跟我对话了。"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ 绑定失败：{e}")

    async def _cmd_chat(self, update, context):
        """与 Agent 对话"""
        if not self._authorized(update):
            await update.message.reply_text("❌ 未授权：请在 .env 配置 MYHOME_TELEGRAM_ALLOWED_CHAT_IDS")
            return
        msg = " ".join(context.args) if context.args else ""
        if not msg:
            await update.message.reply_text("用法：/chat <消息>")
            return
        if self.agent is None:
            await update.message.reply_text("❌ agent 未配置")
            return
        try:
            # v0.5 简化：直接调 agent.chat()，不做 member 上下文
            reply = self.agent.chat(msg)
            await update.message.reply_text(reply[:4000])  # TG 消息上限
        except Exception as e:
            await update.message.reply_text(f"❌ 出错：{e}")

    async def _cmd_status(self, update, context):
        """家庭状态"""
        if not self._authorized(update):
            await update.message.reply_text("❌ 未授权：请在 .env 配置 MYHOME_TELEGRAM_ALLOWED_CHAT_IDS")
            return
        if self.store is None:
            await update.message.reply_text("❌ store 未配置")
            return
        try:
            devices = self.store.list_devices()
            online = sum(1 for d in devices if d.get('online'))
            members = self.store.list_members()
            alerts = self.store.list_alerts(status='open', limit=5)
            text = (
                f"🏠 家庭状态\n\n"
                f"📡 设备：{online}/{len(devices)} 在线\n"
                f"👥 成员：{len(members)} 位\n"
                f"⚠️ 告警：{len(alerts)} 条未处理\n"
            )
            if alerts:
                text += "\n最近告警：\n"
                for a in alerts[:3]:
                    text += f"  - [{a['level']}] {a['title']}\n"
            await update.message.reply_text(text)
        except Exception as e:
            await update.message.reply_text(f"❌ 出错：{e}")

    async def _cmd_rules(self, update, context):
        """规则列表"""
        if not self._authorized(update):
            await update.message.reply_text("❌ 未授权：请在 .env 配置 MYHOME_TELEGRAM_ALLOWED_CHAT_IDS")
            return
        if self.store is None:
            await update.message.reply_text("❌ store 未配置")
            return
        try:
            from myhome_agent.rules.engine import RuleStore
            rule_store = RuleStore(str(self.store.db_path))
            rules = rule_store.list_enabled_rules(household_id=1)
            if not rules:
                await update.message.reply_text("暂无启用规则")
                return
            text = f"📋 已启用规则（{len(rules)} 条）\n\n"
            for r in rules:
                text += f"[{r.severity:6}] {r.id} (base={r.confidence_base})\n"
            await update.message.reply_text(text[:4000])
        except Exception as e:
            await update.message.reply_text(f"❌ 出错：{e}")

    async def _cmd_devices(self, update, context):
        """设备列表"""
        if not self._authorized(update):
            await update.message.reply_text("❌ 未授权：请在 .env 配置 MYHOME_TELEGRAM_ALLOWED_CHAT_IDS")
            return
        if self.store is None:
            await update.message.reply_text("❌ store 未配置")
            return
        try:
            devices = self.store.list_devices()
            if not devices:
                await update.message.reply_text("暂无设备")
                return
            text = f"📡 设备（{len(devices)} 台）\n\n"
            for d in devices[:20]:
                icon = "🟢" if d.get('online') else "⚫"
                text += f"{icon} {d['name']} ({d.get('room', '未分组')})\n"
            await update.message.reply_text(text)
        except Exception as e:
            await update.message.reply_text(f"❌ 出错：{e}")

    async def _cmd_alerts(self, update, context):
        """告警列表"""
        if not self._authorized(update):
            await update.message.reply_text("❌ 未授权：请在 .env 配置 MYHOME_TELEGRAM_ALLOWED_CHAT_IDS")
            return
        if self.store is None:
            await update.message.reply_text("❌ store 未配置")
            return
        try:
            alerts = self.store.list_alerts(status='open', limit=10)
            if not alerts:
                await update.message.reply_text("✅ 暂无告警")
                return
            text = f"⚠️ 当前告警（{len(alerts)} 条）\n\n"
            for a in alerts:
                text += f"[{a['level']}] {a['title']}\n  {a.get('created_at', '')}\n\n"
            await update.message.reply_text(text[:4000])
        except Exception as e:
            await update.message.reply_text(f"❌ 出错：{e}")

    async def _on_message(self, update, context):
        """普通消息 → 对话

        v0.5.2 群组支持：群组中 @bot 触发；reply_to_message 识别提问人
        """
        if not self._authorized(update):
            await update.message.reply_text("❌ 未授权：请在 .env 配置 MYHOME_TELEGRAM_ALLOWED_CHAT_IDS")
            return
        if self.agent is None:
            await update.message.reply_text("请先 /bind 身份")
            return

        # 群组消息：只处理 @bot 或 reply_to bot 的
        chat = update.effective_chat
        if chat.type in ("group", "supergroup"):
            bot_username = (await context.bot.get_me()).username
            msg_text = update.message.text or ""
            reply_to = update.message.reply_to_message
            is_mentioned = f"@{bot_username}" in msg_text
            is_reply_to_bot = reply_to and reply_to.from_user and reply_to.from_user.is_bot
            if not (is_mentioned or is_reply_to_bot):
                return  # 群组不相关消息不处理

        msg = update.message.text
        try:
            reply = self.agent.chat(msg)
            await update.message.reply_text(reply[:4000])
        except Exception as e:
            await update.message.reply_text(f"❌ 出错：{e}")

    # ============================================================
    # 工具
    # ============================================================

    def _list_members(self) -> list[dict]:
        return self.store.list_members() if self.store else []

    def _find_member_by_name(self, name: str) -> dict | None:
        for m in self._list_members():
            if m.get('name', '').lower() == name.lower():
                return m
        # 模糊匹配
        for m in self._list_members():
            if name in m.get('name', ''):
                return m
        return None

    def _save_chat_id(self, member_id: int, chat_id: int) -> None:
        """保存 chat_id 到 members.preferences JSON 字段"""
        if self.store is None:
            return
        try:
            with self.store._conn() as c:
                row = c.execute(
                    "SELECT preferences FROM members WHERE id = ?", (member_id,)
                ).fetchone()
                if row:
                    prefs = json.loads(row['preferences'] or '{}')
                else:
                    prefs = {}
                prefs['telegram_chat_id'] = chat_id
                c.execute(
                    "UPDATE members SET preferences = ? WHERE id = ?",
                    (json.dumps(prefs, ensure_ascii=False), member_id),
                )
        except Exception as e:
            logger.error(f"保存 chat_id 失败: {e}")


# ============================================================
# 工具：bot token 加解密
# ============================================================


def get_bot_token() -> str:
    """从环境变量拿 bot token"""
    token = os.getenv(ENV_BOT_TOKEN, "")
    if not token:
        raise ValueError(f"{ENV_BOT_TOKEN} 未配置")
    return token


def encrypt_bot_token(token: str) -> str:
    return encrypt(token)


def decrypt_bot_token(encrypted: str) -> str:
    return decrypt(encrypted)
