"""2FA / TOTP 验证 v0.8（§50 治理不变量）

v0.8 实现：
- TOTP（pyotp）
- 备用码（10 个一次性）
- per-member 启用开关
- 强制场景：远程 irreversible / marketplace admin / 跨家庭切换
- Fernet 加密 secret_key 存储

强制场景对照表（§50.9 不变量）：

| 场景 | 2FA 要求 |
|------|---------|
| 本地 LAN 操作 | ❌ |
| 远程可逆操作 | ❌ |
| 远程 irreversible 操作（关阀 / 解锁）| ✅ 必 |
| marketplace admin 操作 | ✅ 必 |
| 跨家庭切换（搬家）| ✅ 必 |
| 2FA 设备更换 / 关闭 | ✅ 必 |
| 登录 PWA 24h 后 | ✅ 必 |
"""
from __future__ import annotations

import json
import logging
import os
import secrets
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


# TOTP 配置
TOTP_ISSUER = "myhome-agent"
TOTP_INTERVAL = 30  # 秒
TOTP_DIGITS = 6
BACKUP_CODES_COUNT = 10


@dataclass
class TwoFactorState:
    """成员的 2FA 状态"""

    member_id: int
    enabled: bool
    secret_key_encrypted: str  # Fernet 加密
    backup_codes_encrypted: list[str]  # Fernet 加密 + bcrypt 单向
    enabled_at: int
    last_used_at: int | None
    failed_attempts: int = 0
    locked_until: int | None = None


class TwoFactorManager:
    """v0.8 2FA 管理器"""

    def __init__(self, store: Any):
        self.store = store

    # ============================================================
    # 启用流程
    # ============================================================

    def start_setup(self, member_id: int) -> dict:
        """生成 TOTP secret + 备用码（首次启用）"""
        import pyotp

        secret = pyotp.random_base32()
        backup_codes = [self._gen_backup_code() for _ in range(BACKUP_CODES_COUNT)]
        encrypted_secret = self._encrypt(secret)
        encrypted_backup = [self._bcrypt_hash(c) for c in backup_codes]

        # 不立刻启用——先让用户扫 QR 码验证
        provisioning_uri = pyotp.TOTP(secret).provisioning_uri(
            name=f"member:{member_id}",
            issuer_name=TOTP_ISSUER,
        )

        return {
            "member_id": member_id,
            "secret_plain": secret,  # 仅返回一次，让前端生成 QR
            "provisioning_uri": provisioning_uri,
            "backup_codes_plain": backup_codes,  # 仅返回一次，让用户保存
            "encrypted_secret": encrypted_secret,
            "encrypted_backup": encrypted_backup,
            "next_step": "用户扫 QR + 输入 6 位码确认 + 保存备用码"
        }

    def confirm_setup(self, member_id: int, code: str, secret_plain: str,
                       encrypted_secret: str, encrypted_backup: list[str]) -> bool:
        """用户输入 6 位码确认启用"""
        import pyotp

        if not pyotp.TOTP(secret_plain).verify(code, valid_window=1):
            logger.warning(f"member {member_id} 2FA setup 验证码错误")
            return False

        # 写入数据库
        try:
            with self.store._conn() as c:
                c.execute(
                    """INSERT OR REPLACE INTO member_2fa
                       (member_id, enabled, secret_key_encrypted, backup_codes_encrypted,
                        enabled_at, last_used_at, failed_attempts)
                       VALUES (?, 1, ?, ?, ?, NULL, 0)""",
                    (
                        member_id,
                        encrypted_secret,
                        json.dumps(encrypted_backup),
                        int(__import__("time").time()),
                    ),
                )
            return True
        except Exception as e:
            logger.error(f"启用 2FA 失败: {e}")
            return False

    # ============================================================
    # 验证流程
    # ============================================================

    def verify(self, member_id: int, code: str) -> tuple[bool, str]:
        """验证 6 位 TOTP 或备用码"""
        import pyotp
        import bcrypt

        state = self._load_state(member_id)
        if state is None or not state.enabled:
            return False, "2FA 未启用"

        # 锁定检查
        if state.locked_until and state.locked_until > int(__import__("time").time()):
            return False, "已锁定（5 分钟内失败次数过多）"

        secret = self._decrypt(state.secret_key_encrypted)
        if secret is None:
            return False, "解密失败"

        # 先尝试验证 TOTP
        if pyotp.TOTP(secret).verify(code, valid_window=1):
            self._mark_used(member_id)
            return True, "OK"

        # 验证备用码
        backup_codes = json.loads(state.backup_codes_encrypted)
        for i, hashed in enumerate(backup_codes):
            try:
                if bcrypt.checkpw(code.encode(), hashed.encode()):
                    # 一次性使用，删除该备用码
                    backup_codes.pop(i)
                    self._update_backup(member_id, backup_codes)
                    self._mark_used(member_id)
                    return True, f"OK (备用码 {i+1}/{len(backup_codes)+i+1} 已用)"
            except Exception:
                pass

        # 失败
        self._mark_failed(member_id)
        return False, "验证码错误"

    # ============================================================
    # 强制场景检查
    # ============================================================

    def is_required(self, member_id: int, action: str) -> bool:
        """该动作是否强制 2FA？"""
        REQUIRED_ACTIONS = {
            "remote_irreversible_control",  # 远程不可逆控制
            "marketplace_admin",            # 公共市场管理员操作
            "household_switch",             # 跨家庭切换
            "twofactor_disable",            # 关闭 2FA
            "fernet_key_rotation",          # 主密钥轮换
            "policy_high_risk",             # policy 高危变更
        }
        return action in REQUIRED_ACTIONS

    # ============================================================
    # 关闭 / 重置
    # ============================================================

    def disable(self, member_id: int, code: str) -> bool:
        """关闭 2FA（需验证当前码）"""
        ok, _ = self.verify(member_id, code)
        if not ok:
            return False
        try:
            with self.store._conn() as c:
                c.execute(
                    "UPDATE member_2fa SET enabled = 0 WHERE member_id = ?",
                    (member_id,),
                )
            logger.info(f"member {member_id} 关闭了 2FA")
            return True
        except Exception as e:
            logger.error(f"关闭 2FA 失败: {e}")
            return False

    # ============================================================
    # 工具
    # ============================================================

    def _gen_backup_code(self) -> str:
        """生成备用码（8 位 hex）"""
        return secrets.token_hex(4).upper()

    def _encrypt(self, plain: str) -> str:
        from ..vision.crypto import encrypt
        return encrypt(plain)

    def _decrypt(self, encrypted: str) -> str | None:
        from ..vision.crypto import decrypt
        try:
            return decrypt(encrypted)
        except Exception:
            return None

    def _bcrypt_hash(self, plain: str) -> str:
        import bcrypt
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

    def _load_state(self, member_id: int) -> TwoFactorState | None:
        try:
            with self.store._conn() as c:
                row = c.execute(
                    "SELECT * FROM member_2fa WHERE member_id = ?", (member_id,)
                ).fetchone()
            if not row:
                return None
            return TwoFactorState(
                member_id=row["member_id"],
                enabled=bool(row["enabled"]),
                secret_key_encrypted=row["secret_key_encrypted"],
                backup_codes_encrypted=row["backup_codes_encrypted"],
                enabled_at=row["enabled_at"],
                last_used_at=row["last_used_at"],
                failed_attempts=row["failed_attempts"],
                locked_until=row["locked_until"],
            )
        except Exception:
            return None

    def _mark_used(self, member_id: int) -> None:
        with self.store._conn() as c:
            c.execute(
                "UPDATE member_2fa SET last_used_at = ?, failed_attempts = 0, locked_until = NULL WHERE member_id = ?",
                (int(__import__("time").time()), member_id),
            )

    def _mark_failed(self, member_id: int) -> None:
        with self.store._conn() as c:
            c.execute(
                "UPDATE member_2fa SET failed_attempts = failed_attempts + 1 WHERE member_id = ?",
                (member_id,),
            )
            # 5 次失败锁 5 分钟
            state = self._load_state(member_id)
            if state and state.failed_attempts >= 5:
                locked_until = int(__import__("time").time()) + 300
                c.execute(
                    "UPDATE member_2fa SET locked_until = ? WHERE member_id = ?",
                    (locked_until, member_id),
                )
                logger.warning(f"member {member_id} 2FA 锁定 5 分钟")

    def _update_backup(self, member_id: int, codes: list[str]) -> None:
        with self.store._conn() as c:
            c.execute(
                "UPDATE member_2fa SET backup_codes_encrypted = ? WHERE member_id = ?",
                (json.dumps(codes), member_id),
            )


# ============================================================
# DB Schema（v0.8 新增）
# ============================================================

TWO_FACTOR_SCHEMA = """
CREATE TABLE IF NOT EXISTS member_2fa (
  member_id INTEGER PRIMARY KEY,
  enabled INTEGER NOT NULL DEFAULT 0,
  secret_key_encrypted TEXT NOT NULL,
  backup_codes_encrypted TEXT NOT NULL,
  enabled_at INTEGER NOT NULL,
  last_used_at INTEGER,
  failed_attempts INTEGER DEFAULT 0,
  locked_until INTEGER,
  FOREIGN KEY (member_id) REFERENCES members(id)
);
"""


# ============================================================
# 装饰器：保护 2FA 强制场景
# ============================================================

def require_2fa(action: str):
    """装饰器：标记该函数需 2FA 验证

    用法：
        @require_2fa("remote_irreversible_control")
        async def unlock_door(...):
            ...
    """
    def decorator(func):
        func._requires_2fa = action
        return func
    return decorator