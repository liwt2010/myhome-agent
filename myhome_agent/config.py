"""配置加载：.env + config/default.yaml"""
from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

with open(ROOT / "config" / "default.yaml", encoding="utf-8") as f:
    CONFIG: dict = yaml.safe_load(f) or {}

DB_PATH = os.getenv("MYHOME_DB_PATH", str(ROOT / "data" / "myhome.db"))
HOST = os.getenv("MYHOME_HOST", "0.0.0.0")
PORT = int(os.getenv("MYHOME_PORT", "8300"))

MI_USERNAME = os.getenv("MI_USERNAME", "")
MI_PASSWORD = os.getenv("MI_PASSWORD", "")
MI_REGION = os.getenv("MI_REGION", "cn")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

AGENT_MODEL = CONFIG.get("agent", {}).get("model", "deepseek-chat")
AGENT_MAX_TOKENS = int(CONFIG.get("agent", {}).get("max_tokens", 16000))
HISTORY_TURNS = int(CONFIG.get("agent", {}).get("history_turns", 30))
CONTROL_CONFIRM_TYPES = set(CONFIG.get("control_confirm") or [])
