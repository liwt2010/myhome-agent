"""WebAuthn FastAPI 端点（真实签名验证）。

端点：
- POST /api/auth/webauthn/register/start    -> challenge + options（需 API token）
- POST /api/auth/webauthn/register/finish   -> 验签后存储 credential（需 API token）
- POST /api/auth/webauthn/login/start       -> challenge（公开）
- POST /api/auth/webauthn/login/finish      -> 验签 + 颁发 JWT（公开）
- GET  /api/auth/webauthn/credentials       -> 列出已注册设备（需 API token）
- DELETE /api/auth/webauthn/credentials/{id} -> 删除设备（需 API token）
"""
from __future__ import annotations

import base64
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth/webauthn")

_manager = None


def _b64url(data) -> str:
    if isinstance(data, str):
        return data
    if isinstance(data, (list, tuple)):
        data = bytes(data)
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _get_manager():
    global _manager
    if _manager is None:
        from ..config import DB_PATH
        from ..memory.store import Store
        from .webauthn import WebAuthnManager

        _manager = WebAuthnManager(store=Store(DB_PATH))
    return _manager


class RegisterStartRequest(BaseModel):
    member_id: int


class RegisterFinishRequest(BaseModel):
    challenge_id: str
    attestation: dict
    name: str = "Key"


class LoginStartRequest(BaseModel):
    member_id: int


class LoginFinishRequest(BaseModel):
    challenge_id: str
    assertion: dict


@router.post("/register/start")
async def register_start(req: RegisterStartRequest):
    return _get_manager().begin_registration(req.member_id)


@router.post("/register/finish")
async def register_finish(req: RegisterFinishRequest):
    from webauthn import parse_registration_credential_json

    att = req.attestation
    try:
        credential = parse_registration_credential_json({
            "id": att["id"],
            "rawId": _b64url(att.get("rawId") or att["id"]),
            "type": att.get("type", "public-key"),
            "clientDataJSON": _b64url(att["clientDataJSON"]),
            "attestationObject": _b64url(att["attestationObject"]),
            "transports": att.get("transports", []),
        })
    except Exception as e:
        raise HTTPException(400, f"attestation 格式错误: {e}")

    result = _get_manager().complete_registration(req.challenge_id, credential, nickname=req.name)
    if not result.get("success"):
        raise HTTPException(400, result.get("error", "注册失败"))
    return result


@router.post("/login/start")
async def login_start(req: LoginStartRequest):
    return _get_manager().begin_authentication(req.member_id)


@router.post("/login/finish")
async def login_finish(req: LoginFinishRequest):
    from webauthn import parse_authentication_credential_json

    asr = req.assertion
    try:
        assertion = parse_authentication_credential_json({
            "id": asr["id"],
            "rawId": _b64url(asr.get("rawId") or asr["id"]),
            "type": asr.get("type", "public-key"),
            "clientDataJSON": _b64url(asr["clientDataJSON"]),
            "authenticatorData": _b64url(asr["authenticatorData"]),
            "signature": _b64url(asr["signature"]),
            "userHandle": _b64url(asr.get("userHandle", "")),
        })
    except Exception as e:
        raise HTTPException(400, f"assertion 格式错误: {e}")

    result = _get_manager().complete_authentication(req.challenge_id, assertion)
    if not result.get("success"):
        raise HTTPException(401, result.get("error", "验证失败"))
    return result


@router.get("/credentials")
async def list_credentials(member_id: int):
    return {"credentials": _get_manager().list_credentials(member_id)}


@router.delete("/credentials/{credential_id}")
async def delete_credential(credential_id: str):
    if not _get_manager().remove_credential(credential_id):
        raise HTTPException(404, "credential 不存在")
    return {"success": True}
