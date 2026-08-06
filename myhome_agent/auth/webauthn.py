"""WebAuthn / FIDO2 验证（v0.9 替代/补充 TOTP）

v0.9 实现：
- py_webauthn 注册（生成 challenge → 浏览器 attestation → 存 credential_id + public_key）
- py_webauthn 验证（生成 challenge → 浏览器 assertion → 验签）
- 存储 credential_id + public_key + sign_count
- 支持 YubiKey / TouchID / Windows Hello / Android Fingerprint
"""
from __future__ import annotations

import json
import logging
import secrets
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# WebAuthn 配置
RP_ID = "myhome.local"
RP_NAME = "myhome-agent"
ORIGIN = "https://myhome.local:8300"
CHALLENGE_TTL = 300  # 5 分钟


@dataclass
class WebAuthnCredential:
    """FIDO2 credential 存储"""

    credential_id: str
    member_id: int
    public_key: str
    sign_count: int = 0
    transports: list = field(default_factory=list)
    nickname: str = ""
    registered_at: int = field(default_factory=lambda: int(time.time()))
    last_used_at: int | None = None


def _to_dict_recursive(obj, depth=0):
    """递归把 pydantic model 转 dict（含嵌套 model + bytes 转 base64）"""
    if depth > 5:
        return str(obj)
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, bytes):
        return obj.hex()
    if isinstance(obj, dict):
        return {k: _to_dict_recursive(v, depth + 1) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_dict_recursive(v, depth + 1) for v in obj]
    # pydantic v1（按字段名）
    try:
        if hasattr(obj, '__fields__'):
            return {k: _to_dict_recursive(getattr(obj, k), depth + 1) for k in obj.__fields__.keys()}
    except (AttributeError, TypeError):
        pass
    # pydantic v2
    try:
        d = obj.model_dump()
        return _to_dict_recursive(d, depth + 1)
    except AttributeError:
        pass
    # 最后一搏：取所有非 _ 属性
    try:
        return {k: _to_dict_recursive(v, depth + 1) for k, v in vars(obj).items() if not k.startswith('_')}
    except TypeError:
        return str(obj)


def _options_to_dict(options):
    """pydantic v1/v2 model -> dict"""
    if isinstance(options, str):
        return json.loads(options)
    return _to_dict_recursive(options)


class WebAuthnManager:
    """v0.9 WebAuthn 管理"""

    def __init__(self, store=None, rp_id=RP_ID, origin=ORIGIN):
        self.store = store
        self.rp_id = rp_id
        self.origin = origin
        self._pending = {}

    def begin_registration(self, member_id: int) -> dict:
        """生成 challenge + options"""
        from webauthn import generate_registration_options
        from webauthn.helpers.cose import COSEAlgorithmIdentifier
        from webauthn.helpers.structs import (
            AuthenticatorSelectionCriteria,
            ResidentKeyRequirement,
            UserVerificationRequirement,
        )

        challenge = secrets.token_bytes(32)
        user_id = f"member:{member_id}".encode()

        options = generate_registration_options(
            rp_id=self.rp_id,
            rp_name=RP_NAME,
            user_id=user_id,
            user_name=f"member:{member_id}",
            user_display_name=f"Member {member_id}",
            challenge=challenge,
            supported_pub_key_algs=[
                COSEAlgorithmIdentifier.EDDSA,
                COSEAlgorithmIdentifier.ECDSA_SHA_256,
                COSEAlgorithmIdentifier.RSASSA_PSS_SHA_256,
            ],
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement.PREFERRED,
                user_verification=UserVerificationRequirement.PREFERRED,
            ),
        )

        challenge_id = secrets.token_urlsafe(16)
        self._pending[challenge_id] = {
            "type": "registration",
            "member_id": member_id,
            "challenge": challenge,
            "created_at": time.time(),
        }

        return {
            "challenge_id": challenge_id,
            "options": _options_to_dict(options),
        }

    def complete_registration(self, challenge_id, credential_response, nickname="") -> dict:
        """前端传 attestation response"""
        from webauthn import verify_registration_response

        pending = self._pending.pop(challenge_id, None)
        if not pending or pending["type"] != "registration":
            return {"success": False, "error": "challenge 失效或不存在"}
        if time.time() - pending["created_at"] > CHALLENGE_TTL:
            return {"success": False, "error": "challenge 过期"}

        try:
            verification = verify_registration_response(
                credential=credential_response,
                expected_challenge=pending["challenge"],
                expected_origin=self.origin,
                expected_rp_id=self.rp_id,
            )
        except Exception as e:
            logger.error(f"WebAuthn 注册验证失败: {e}")
            return {"success": False, "error": f"验证失败: {e}"}

        credential_id_b64 = json.dumps(
            credential_response.get("id") or credential_response.get("rawId")
        )
        public_key = (
            verification.credential_public_key.hex()
            if hasattr(verification.credential_public_key, "hex")
            else str(verification.credential_public_key)
        )
        sign_count = verification.sign_count

        try:
            with self.store._conn() as c:
                c.execute(
                    """INSERT OR REPLACE INTO member_webauthn
                       (credential_id, member_id, public_key, sign_count, transports, nickname, registered_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        credential_id_b64,
                        pending["member_id"],
                        public_key,
                        sign_count,
                        json.dumps(credential_response.get("transports", [])),
                        nickname or "Default Key",
                        int(time.time()),
                    ),
                )
            return {
                "success": True,
                "credential_id": credential_id_b64,
                "sign_count": sign_count,
            }
        except Exception as e:
            logger.error(f"存储 credential 失败: {e}")
            return {"success": False, "error": str(e)}

    def begin_authentication(self, member_id: int) -> dict:
        """生成 assertion challenge"""
        from webauthn import generate_authentication_options
        from webauthn.helpers.structs import PublicKeyCredentialDescriptor

        with self.store._conn() as c:
            creds = c.execute(
                "SELECT credential_id FROM member_webauthn WHERE member_id = ?",
                (member_id,),
            ).fetchall()
        if not creds:
            return {"success": False, "error": "该 member 未注册 WebAuthn"}

        allow_credentials = [
            PublicKeyCredentialDescriptor(id=cred["credential_id"].encode())
            for cred in creds
        ]

        challenge = secrets.token_bytes(32)
        options = generate_authentication_options(
            rp_id=self.rp_id,
            challenge=challenge,
            allow_credentials=allow_credentials,
            user_verification="preferred",
        )

        challenge_id = secrets.token_urlsafe(16)
        self._pending[challenge_id] = {
            "type": "authentication",
            "member_id": member_id,
            "challenge": challenge,
            "created_at": time.time(),
        }

        return {
            "challenge_id": challenge_id,
            "options": _options_to_dict(options),
        }

    def complete_authentication(self, challenge_id, assertion_response) -> dict:
        """前端传 assertion，验证 + 颁发 JWT"""
        from webauthn import verify_authentication_response

        pending = self._pending.pop(challenge_id, None)
        if not pending or pending["type"] != "authentication":
            return {"success": False, "error": "challenge 失效或不存在"}
        if time.time() - pending["created_at"] > CHALLENGE_TTL:
            return {"success": False, "error": "challenge 过期"}

        credential_id_b64 = assertion_response.get("id") or assertion_response.get("rawId")

        with self.store._conn() as c:
            cred = c.execute(
                "SELECT public_key, sign_count FROM member_webauthn WHERE credential_id = ?",
                (credential_id_b64,),
            ).fetchone()
        if not cred:
            return {"success": False, "error": "credential 不存在"}

        try:
            public_key_bytes = bytes.fromhex(cred["public_key"])
            verification = verify_authentication_response(
                credential=assertion_response,
                expected_challenge=pending["challenge"],
                expected_origin=self.origin,
                expected_rp_id=self.rp_id,
                credential_public_key=public_key_bytes,
                credential_current_sign_count=cred["sign_count"],
            )
        except Exception as e:
            logger.error(f"WebAuthn 验证失败: {e}")
            return {"success": False, "error": f"验证失败: {e}"}

        with self.store._conn() as c:
            c.execute(
                "UPDATE member_webauthn SET sign_count = ?, last_used_at = ? WHERE credential_id = ?",
                (verification.new_sign_count, int(time.time()), credential_id_b64),
            )

        from .session import TwoFactorSession

        token = TwoFactorSession.issue(pending["member_id"], action="*")
        return {
            "success": True,
            "token": token,
            "ttl_seconds": 1800,
            "member_id": pending["member_id"],
        }

    def list_credentials(self, member_id: int) -> list:
        with self.store._conn() as c:
            rows = c.execute(
                "SELECT credential_id, nickname, sign_count, registered_at, last_used_at FROM member_webauthn WHERE member_id = ?",
                (member_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def remove_credential(self, credential_id: str) -> bool:
        try:
            with self.store._conn() as c:
                c.execute(
                    "DELETE FROM member_webauthn WHERE credential_id = ?",
                    (credential_id,),
                )
            return True
        except Exception:
            return False

    def is_available_for(self, member_id: int) -> bool:
        return len(self.list_credentials(member_id)) > 0