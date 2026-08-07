"""Secrets that are generated once and persisted to the project .env."""
from __future__ import annotations

import os
import secrets
from pathlib import Path


def _env_path() -> Path:
    from ..config import ROOT  # lazy import to avoid a config/security cycle
    return ROOT / ".env"


def _append_to_env(env_name: str, value: str) -> None:
    env_path = _env_path()
    try:
        existing = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    except OSError:
        existing = ""
    if env_name not in existing:
        with open(env_path, "a", encoding="utf-8") as f:
            f.write(f"\n# auto-generated, keep private\n{env_name}={value}\n")


def get_or_create_secret(env_name: str, nbytes: int = 32) -> str:
    """Return an existing env secret or generate, persist and cache a new one."""
    value = os.getenv(env_name)
    if value:
        return value
    value = secrets.token_urlsafe(nbytes)
    _append_to_env(env_name, value)
    os.environ[env_name] = value
    return value
