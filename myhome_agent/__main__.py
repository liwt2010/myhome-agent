"""主入口：启动整个 myhome-agent 家庭私人管家。

使用方式:
    python -m myhome_agent                  # 启动服务（默认）
    python -m myhome_agent chat "你好"      # 命令行对话
    python -m myhome_agent sync             # 同步云端设备清单
    python -m myhome_agent import data.csv  # 导入历史数据
    python -m myhome_agent analyze          # 执行一次分析
    python -m myhome_agent init             # v0.1 初始化（建表 + 种子 5 条 P0 规则）
    python -m myhome_agent rules list       # v0.1 列出规则
    python -m myhome_agent rules scan       # v0.1 扫一次规则引擎
    python -m myhome_agent doctor           # 启动前诊断
"""
from __future__ import annotations

# v0.4 D.7 修复：Windows GBK 编码下 Unicode 字符报错
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import argparse
import asyncio
import logging
import os

from .config import (
    CONFIG, DB_PATH, HOST, MI_PASSWORD, MI_REGION, MI_USERNAME, PORT,
    DEEPSEEK_API_KEY,
)
from .memory.store import Store

logger = logging.getLogger(__name__)


def _make_store() -> Store:
    return Store(DB_PATH)


def cmd_init():
    """v0.1 初始化：建表 + 种子 5 条 P0 规则"""
    print("=== myhome-agent v0.1 初始化 ===")
    store = _make_store()
    print(f"  ✓ 数据库表已建: {DB_PATH}")

    from .rules.engine import RuleStore, seed_default_rules
    rule_store = RuleStore(DB_PATH)
    n = seed_default_rules(rule_store, household_id=1)
    print(f"  ✓ 种子 {n} 条 P0 规则")

    print("\n下一步: `myhome-agent serve` 启动服务，或 `myhome-agent rules list` 查看规则")


def cmd_rules_list():
    """列出已加载的规则"""
    from .rules.engine import RuleStore
    store = RuleStore(DB_PATH)
    rules = store.list_enabled_rules(household_id=1)
    print(f"=== 已启用规则（{len(rules)} 条）===")
    for r in rules:
        st = store.get_state(r.id)
        state = st.state if st else "unknown"
        print(f"  [{r.severity:6}] {r.id:30} {state:12} ({r.cooldown}s cooldown)")


def cmd_rules_scan():
    """执行一次规则扫描"""
    from .rules.engine import RuleStore, RuleScanner
    store = RuleStore(DB_PATH)
    scanner = RuleScanner(store)
    print("=== 规则扫描（v0.1 一次性）===")
    fired = scanner.scan_once(household_id=1)
    if fired:
        print(f"  触发 {len(fired)} 条规则：")
        for f in fired:
            print(f"    - {f['rule_id']}")
    else:
        print("  本次扫描无触发")
    print("  注：v0.1 mock window（无真实传感器数据），结果仅作链路验证")


def cmd_channels_start_telegram():
    """启动 TG bot（v0.5）"""
    from .channels.telegram import TelegramBot
    import os
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token or token == "your-telegram-bot-token":
        print("❌ TELEGRAM_BOT_TOKEN 未配置（在 .env 设置）")
        print("   创建 bot: Telegram 搜 @BotFather → /newbot")
        return
    store = _make_store()
    bot = TelegramBot(token=token, store=store)
    bot.start()
    print("✅ Telegram bot 启动")
    print("   在 TG 搜你的 bot，发送 /start")


def cmd_quotas_vacation(enable: bool):
    """切换度假模式（v0.5）"""
    from .governance.quotas import QuotaManager
    qm = QuotaManager()
    q = qm.get(1)  # 假设单家庭 demo
    if enable:
        q.enter_vacation()
        print("✅ 度假模式：配额提升 1.5x")
    else:
        q.exit_vacation()
        print("✅ 度假模式：已退出（恢复基础配额）")
    print(f"   状态：{q.get_stats()}")


def cmd_serve():
    """启动 FastAPI 网关服务（含后台采集）。"""
    store = _make_store()

    # 配置云端（可选，仅当启用了米家生态）
    cloud = None
    if MI_USERNAME and MI_PASSWORD:
        from .collectors.cloud_api import MiCloudCollector
        cloud = MiCloudCollector(MI_USERNAME, MI_PASSWORD, MI_REGION)

    from .collectors.registry import DeviceRegistry
    registry = DeviceRegistry(store, cloud)

    import uvicorn
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    from .gateway.server import app

    # v0.1 启动规则扫描器（后台线程）
    from .rules.engine import RuleStore, RuleScanner
    import threading
    rule_store = RuleStore(DB_PATH)
    scanner = RuleScanner(rule_store)
    scanner_thread = threading.Thread(
        target=scanner.run_forever,
        kwargs={"household_id": 1, "interval": 10.0},
        daemon=True,
    )
    scanner_thread.start()
    logger.info("v0.1 规则引擎已启动（10s 周期，5 条 P0 规则）")

    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


def cmd_chat(message: str):
    """命令行对话。"""
    api_key = DEEPSEEK_API_KEY
    if not api_key:
        print("错误: 未设置 DEEPSEEK_API_KEY 环境变量（见 .env 文件）")
        sys.exit(1)

    store = _make_store()
    cloud = None
    if MI_USERNAME and MI_PASSWORD:
        from .collectors.cloud_api import MiCloudCollector
        cloud = MiCloudCollector(MI_USERNAME, MI_PASSWORD, MI_REGION)

    from .collectors.registry import DeviceRegistry
    registry = DeviceRegistry(store, cloud)

    from .agent.core import Agent
    agent = Agent(store, api_key, registry)

    print(f"用户: {message}")
    reply = agent.chat(message)
    print(f"小管家: {reply}")


def cmd_sync():
    """从米家云端同步设备清单到本地。"""
    if not MI_USERNAME or not MI_PASSWORD:
        print("错误: 未配置米家账号，请在 .env 中设置 MI_USERNAME / MI_PASSWORD")
        sys.exit(1)

    store = _make_store()
    from .collectors.cloud_api import MiCloudCollector
    from .collectors.registry import DeviceRegistry

    cloud = MiCloudCollector(MI_USERNAME, MI_PASSWORD, MI_REGION)
    registry = DeviceRegistry(store, cloud)
    n = registry.sync_from_cloud()
    print(f"成功同步 {n} 台设备")


def cmd_import(csv_path: str):
    """导入历史数据 CSV。"""
    store = _make_store()
    from .ingestion.importer import import_auto
    n = import_auto(store, csv_path)
    print(f"导入成功: {n} 条记录")


def cmd_analyze():
    """执行一次作息学习 + 异常检测。"""
    store = _make_store()
    from .analytics.anomaly import run_all
    from .analytics.routines import learn_routines

    learn_routines(store, int(CONFIG.get("analytics", {}).get("routine_window_days", 30)))
    run_all(store, CONFIG)
    print("分析完成")

    alerts = store.list_alerts(status="open")
    if alerts:
        print(f"当前告警: {len(alerts)} 条")
        for a in alerts:
            print(f"  [{a['level']}] {a['title']}")
    else:
        print("无未处理告警。")


def cmd_doctor():
    """启动前诊断（占位，v2.4 §0a）。"""
    print("doctor 暂未实现，待 v2.5 阶段补全（schema 版本/加密 key/端口/磁盘空间/网络 5 项）")


def cli():
    """poetry/pip 安装后由 `myhome-agent` 命令调用。"""
    main()


def main():
    parser = argparse.ArgumentParser(description="myhome-agent — 家庭私人管家")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示调试日志")
    sub = parser.add_subparsers(dest="command", help="可用命令")

    # serve（默认）
    parser_serve = sub.add_parser("serve", help="启动 Web 服务")
    parser_serve.add_argument("--host", default=None, help="监听地址")
    parser_serve.add_argument("--port", type=int, default=None, help="监听端口")

    # chat
    parser_chat = sub.add_parser("chat", help="与管家对话")
    parser_chat.add_argument("message", help="消息内容")

    # sync
    sub.add_parser("sync", help="同步云端设备清单")

    # import
    parser_import = sub.add_parser("import", help="导入历史数据 CSV")
    parser_import.add_argument("csv_path", help="CSV 文件路径")

    # analyze
    sub.add_parser("analyze", help="执行一次分析（作息学习 + 异常检测）")

    # doctor
    sub.add_parser("doctor", help="启动前诊断（占位）")

    # v0.1 init
    sub.add_parser("init", help="v0.1 初始化（建表 + 种子 5 条 P0 规则）")

    # v0.1 rules 子命令
    parser_rules = sub.add_parser("rules", help="v0.1 规则引擎管理")
    rules_sub = parser_rules.add_subparsers(dest="rules_command")
    rules_sub.add_parser("list", help="列出已启用规则")
    rules_sub.add_parser("scan", help="扫一次规则引擎")

    # v0.5 channels 子命令
    parser_channels = sub.add_parser("channels", help="v0.5 多渠道管理")
    channels_sub = parser_channels.add_subparsers(dest="channels_command")
    channels_sub.add_parser("start-telegram", help="启动 Telegram bot")
    channels_sub.add_parser("vacation-on", help="进入度假模式（配额提升）")
    channels_sub.add_parser("vacation-off", help="退出度假模式")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(name)s:%(message)s")

    if args.command == "chat":
        cmd_chat(args.message)
    elif args.command == "sync":
        cmd_sync()
    elif args.command == "import":
        cmd_import(args.csv_path)
    elif args.command == "analyze":
        cmd_analyze()
    elif args.command == "doctor":
        cmd_doctor()
    elif args.command == "init":
        cmd_init()
    elif args.command == "rules":
        if args.rules_command == "list":
            cmd_rules_list()
        elif args.rules_command == "scan":
            cmd_rules_scan()
        else:
            cmd_rules_list()  # 默认 list
    elif args.command == "channels":
        if args.channels_command == "start-telegram":
            cmd_channels_start_telegram()
        elif args.channels_command == "vacation-on":
            cmd_quotas_vacation(True)
        elif args.channels_command == "vacation-off":
            cmd_quotas_vacation(False)
        else:
            print("用法: myhome-agent channels {start-telegram|vacation-on|vacation-off}")
    elif args.command == "serve":
        if args.host:
            global HOST
            HOST = args.host
        if args.port:
            global PORT
            PORT = args.port
        cmd_serve()
    else:
        # 默认启动服务
        cmd_serve()


if __name__ == "__main__":
    main()
