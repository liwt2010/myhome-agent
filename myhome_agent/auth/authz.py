"""成员登录 + RBAC 权限（批次 A）。"""
from __future__ import annotations

import time
from typing import Any

import bcrypt
import jwt
from fastapi import HTTPException, Request

from .session import JWT_ALGO, JWT_SECRET

MEMBER_TOKEN_TTL = 24 * 3600

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {"*"},
    "adult": {
        "chat", "device.control", "memories.write", "settings.write",
        "data.export", "audit.read", "vision.read",
    },
    "elder": {"chat", "memories.read", "data.export"},
    "child": {"chat", "memories.read"},
    "guest": {"chat"},
}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def issue_member_token(member_id: int, role: str) -> str:
    now = int(time.time())
    payload = {
        "type": "member",
        "sub": str(member_id),
        "role": role,
        "iat": now,
        "exp": now + MEMBER_TOKEN_TTL,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def verify_member_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        if payload.get("type") != "member":
            return None
        return payload
    except Exception:
        return None


def role_allows(role: str, permission: str) -> bool:
    perms = ROLE_PERMISSIONS.get(role, set())
    return "*" in perms or permission in perms


def require_permission(permission: str):
    """FastAPI 依赖：校验成员角色权限；API token 视为管理员。"""
    async def dep(request: Request):
        member = getattr(request.state, "member", None)
        if member is None:
            return {"role": "admin"}
        if not role_allows(member.get("role", "guest"), permission):
            raise HTTPException(status_code=403, detail=f"缺少权限: {permission}")
        return member

    return dep
