"""2FA Session Token (v0.8.1)

轻量 JWT 用于 session.twofa_verified_at 标记：
- 用户通过 TOTP/WebAuthn 验证后，发一个 30 分钟有效 JWT
- JWT 含 member_id + scope + exp
- gateway 端用装饰器 / Depends 校验
"""
from __future__ import annotations

import logging
import time
from typing import Any

import jwt

from ..security.env_secret import get_or_create_secret

logger = logging.getLogger(__name__)

# 从环境变量读取，未配置时自动生成并持久化到 .env，避免硬编码可伪造
JWT_SECRET = get_or_create_secret("MYHOME_JWT_SECRET", nbytes=32)
JWT_ALGO = "HS256"
JWT_TTL = 30 * 60  # 30 分钟


class TwoFactorSession:
    """2FA 验证会话管理"""

    @staticmethod
    def issue(member_id: int, action: str = "*") -> str:
        """颁发 token"""
        payload = {
            "member_id": member_id,
            "action": action,
            "iat": int(time.time()),
            "exp": int(time.time()) + JWT_TTL,
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

    @staticmethod
    def verify(token: str, required_action: str = "*") -> tuple[bool, dict]:
        """验证 token + 检查 scope"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        except jwt.ExpiredSignatureError:
            return False, {"error": "token expired"}
        except jwt.InvalidTokenError as e:
            return False, {"error": f"invalid: {e}"}

        if payload["action"] != "*" and required_action != "*" and payload["action"] != required_action:
            return False, {"error": f"scope mismatch: token={payload['action']} required={required_action}"}

        return True, payload

    @staticmethod
    def remaining_seconds(token: str) -> int:
        """剩余有效秒数"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
            return max(0, payload["exp"] - int(time.time()))
        except Exception:
            return 0


# ============================================================
# FastAPI 依赖项
# ============================================================

def require_2fa_dep(action: str):
    """FastAPI 依赖工厂"""
    from fastapi import Header, HTTPException

    async def dep(x_twofa_token: str | None = Header(default=None, alias="X-2FA-Token")):
        if not x_twofa_token:
            raise HTTPException(
                status_code=401,
                detail={
                    "requires_2fa": True,
                    "action": action,
                    "next": f"POST /api/auth/2fa/verify with code then retry with X-2FA-Token header"
                }
            )
        ok, payload = TwoFactorSession.verify(x_twofa_token, action)
        if not ok:
            raise HTTPException(status_code=401, detail=payload)
        return payload

    return dep
