"""KMS / HSM 主密钥管理（v1.0）

v1.0 实现：
- PBKDF2 派生 key（从 .env 密码短语 → Fernet key）
- 主密钥轮换（rotation）
- Shamir Secret Sharing 多源备份（v1.0 占位，依赖 sssa 库）
- HSM 接口（AWS KMS / Azure Key Vault / GCP KMS 留 stub）
- 主密钥泄露应急响应

v0.x Fernet 流程：
- .env 明文存 Fernet key → 单点泄露 → 全盘失守

v1.0 KMS 流程：
- .env 存 KMS passphrase（口令）
- PBKDF2 → key 派生（10 万次迭代）
- 派生 key 用于实际加密
- 主 passphrase 由 HSM 托管（生产）或 家庭多人 Shamir 分持（开源）
"""
from __future__ import annotations

import logging
import os
import secrets
from typing import Any

logger = logging.getLogger(__name__)


def _update_env_value(name: str, value: str) -> None:
    """更新项目根 .env 中的单个键值并同步到 os.environ。"""
    from ..config import ROOT

    env_path = ROOT / ".env"
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines(keepends=True) if env_path.exists() else []
    except OSError:
        lines = []
    out = []
    updated = False
    for line in lines:
        if line.startswith(f"{name}="):
            out.append(f"{name}={value}\n")
            updated = True
        else:
            out.append(line)
    if not updated:
        out.append(f"\n# auto-generated, keep private\n{name}={value}\n")
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(out)
    os.environ[name] = value


# ============================================================
# KMS 抽象
# ============================================================


class KMSProvider:
    """v1.0 KMS 抽象基类"""

    def get_key(self, key_id: str) -> bytes:
        """取 key bytes（明文）"""
        raise NotImplementedError

    def rotate_key(self, key_id: str, new_key: bytes) -> str:
        """轮换 + 返回新版本 ID"""
        raise NotImplementedError

    def list_versions(self, key_id: str) -> list[str]:
        raise NotImplementedError


class LocalKMS(KMSProvider):
    """v1.0 本地 KMS（家庭版）

    - passphrase 存 .env（PBKDF2 派生）
    - 主 passphrase 可分 N 份 Shamir（家庭成员各持一份）
    - 派生 key 缓存 1 小时
    """

    def __init__(self, passphrase: str | None = None, salt: bytes | None = None):
        self.passphrase = passphrase or os.getenv("MYHOME_KMS_PASSPHRASE", "")
        self.salt = salt or os.getenv("MYHOME_KMS_SALT", "myhome-v1.0").encode()
        self._cache: dict[str, bytes] = {}
        self._cache_ts: dict[str, float] = {}
        self._cache_ttl = 3600  # 1h

    def derive_key(self, key_id: str = "default") -> bytes:
        """PBKDF2 → Fernet key"""
        if not self.passphrase:
            raise ValueError(
                "MYHOME_KMS_PASSPHRASE 未设置；v1.0 必须派生 key"
            )
        import time as _time
        now = _time.time()
        cached = self._cache.get(key_id)
        ts = self._cache_ts.get(key_id, 0)
        if cached and (now - ts) < self._cache_ttl:
            return cached

        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        import base64

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100_000,
        )
        derived = kdf.derive(self.passphrase.encode())
        # Fernet 格式 = base64(32 bytes)
        fernet_key = base64.urlsafe_b64encode(derived)
        self._cache[key_id] = fernet_key
        self._cache_ts[key_id] = now
        return fernet_key

    def get_key(self, key_id: str = "default") -> bytes:
        return self.derive_key(key_id)

    def rotate_key(self, key_id: str, new_key: bytes) -> str:
        """轮换派生 salt 并持久化；调用方需先用旧 key 重加密存量数据。"""
        import secrets as _secrets
        new_salt = _secrets.token_bytes(16)
        self.salt = new_salt
        self._cache.clear()
        _update_env_value("MYHOME_KMS_SALT", new_salt.hex())
        logger.warning(f"KMS key {key_id} 轮换（salt 更新）")
        return f"v{int.from_bytes(new_salt[:4], 'big')}"

    def list_versions(self, key_id: str) -> list[str]:
        return ["v1"]


class AWSCMSStub(KMSProvider):
    """v1.0 stub — 真实接入留 v1.0.1"""

    def __init__(self, region: str = "eu-central-1"):
        self.region = region

    def get_key(self, key_id: str) -> bytes:
        raise NotImplementedError("v1.0.1 接入 AWS KMS SDK")

    def rotate_key(self, key_id: str, new_key: bytes) -> str:
        raise NotImplementedError


class AzureKeyVaultStub(KMSProvider):
    """v1.0 stub"""

    def __init__(self, vault_url: str = ""):
        self.vault_url = vault_url

    def get_key(self, key_id: str) -> bytes:
        raise NotImplementedError("v1.0.1 接入 Azure SDK")


# ============================================================
# Shamir Secret Sharing（家庭多人分持）
# ============================================================


def split_secret(secret: bytes, n: int = 3, k: int = 2) -> list[bytes]:
    """Shamir 分割（v1.0 占位实现，需 sssa 库）

    Args:
        secret: 主 passphrase bytes
        n: 总份数
        k: 恢复阈值（k 份即可恢复）

    Returns:
        n 个 shares

    家庭场景：5 口人，n=5, k=3（任意 3 人合起来可恢复）
    """
    try:
        import sssa  # type: ignore
        return sssa.split(secret, n, k)
    except ImportError:
        logger.warning("sssa 未装；v1.0 占位：返回 n 份拷贝（不安全，仅 demo）")
        return [secret] * n


def recover_secret(shares: list[bytes], k: int = 2) -> bytes:
    """从 k 份恢复"""
    try:
        import sssa  # type: ignore
        return sssa.combine(shares[:k])
    except ImportError:
        logger.warning("sssa 未装；占位返回第一份")
        return shares[0] if shares else b""


# ============================================================
# Fernet 集成（替换 vision/crypto.py 直读 .env）
# ============================================================


def get_kms() -> KMSProvider:
    """工厂：按环境变量选 KMS

    v1.0.1 升级：支持 AWS / GCP / Azure（真实接入）
    """
    provider = os.getenv("MYHOME_KMS_PROVIDER", "local")
    if provider == "local":
        return LocalKMS()
    elif provider == "aws":
        try:
            from .kms_aws import AWSKMS
            return AWSKMS()
        except ImportError as e:
            logger.warning(f"AWSKMS 不可用 ({e})，降级 local")
            return LocalKMS()
    elif provider == "gcp":
        try:
            from .kms_gcp import GCPKMS
            return GCPKMS()
        except ImportError as e:
            logger.warning(f"GCPKMS 不可用 ({e})，降级 local")
            return LocalKMS()
    elif provider == "azure":
        try:
            from .kms_azure import AzureKeyVault
            return AzureKeyVault()
        except ImportError as e:
            logger.warning(f"AzureKeyVault 不可用 ({e})，降级 local")
            return LocalKMS()
    else:
        logger.warning(f"未知 KMS provider={provider}，降级 local")
        return LocalKMS()


def kms_encrypt(plaintext: str, key_id: str = "default") -> str:
    """用 KMS 派生的 Fernet key 加密"""
    from cryptography.fernet import Fernet
    kms = get_kms()
    key = kms.get_key(key_id)
    f = Fernet(key)
    return f.encrypt(plaintext.encode()).decode()


def kms_decrypt(token: str, key_id: str = "default") -> str:
    from cryptography.fernet import Fernet
    kms = get_kms()
    key = kms.get_key(key_id)
    f = Fernet(key)
    try:
        return f.decrypt(token.encode()).decode()
    except Exception as e:
        logger.error(f"KMS 解密失败: {e}")
        return ""


# ============================================================
# 主密钥泄露应急响应
# ============================================================


def emergency_rotate_all() -> dict:
    """v1.0 主密钥泄露应急流程

    1. 立即轮换 KMS passphrase（生成新随机）
    2. 重写 .env 中的 MYHOME_KMS_PASSPHRASE / MYHOME_KMS_SALT
    3. 通知所有管理员（DPA 必报）
    4. 强制所有 2FA 用户重新验证
    5. 审计最近 24h 异常访问
    6. 重新加密所有 Fernet 加密数据（轮换后旧 key 解密 + 新 key 重加密）
    """
    import secrets as _secrets

    old_passphrase = os.getenv("MYHOME_KMS_PASSPHRASE", "")
    old_salt = os.getenv("MYHOME_KMS_SALT", "myhome-v1.0")
    new_passphrase = _secrets.token_urlsafe(32)
    new_salt = _secrets.token_bytes(16).hex()

    # 写 .env
    try:
        _update_env_value("MYHOME_KMS_PASSPHRASE", new_passphrase)
        _update_env_value("MYHOME_KMS_SALT", new_salt)
    except Exception as e:
        logger.error(f"轮换 .env 失败: {e}")
        return {"success": False, "error": str(e)}

    reencrypt = reencrypt_all_fernet_data(
        old_passphrase=old_passphrase,
        old_salt=old_salt,
        new_passphrase=new_passphrase,
        new_salt=new_salt,
    )

    # 通知 DPO（v1.0 实际场景）
    logger.critical(
        f"🚨 KMS 主密钥已轮换：DPA 必报！新 passphrase={new_passphrase[:8]}..."
    )

    return {
        "success": True,
        "new_passphrase_set": True,
        "new_salt_set": True,
        "reencrypt": reencrypt,
        "actions": [
            "✅ 生成新 passphrase + salt",
            "✅ 写入 .env",
            "⚠️  DPO 通知（v1.0 必做）",
            "⚠️  强制 2FA 重验证（v1.0.1）",
            "⚠️  审计 24h 访问（v1.0.1）",
            "⚠️  重加密 Fernet 数据（v1.0.1）",
        ],
    }


# ============================================================
# Fernet 数据重加密工具（v1.0.1 占位）
# ============================================================


def _fernet_from_params(passphrase: str, salt: str):
    from cryptography.fernet import Fernet

    kms = LocalKMS(passphrase=passphrase, salt=salt.encode())
    return Fernet(kms.derive_key())


def reencrypt_all_fernet_data(
    old_passphrase: str | None = None,
    old_salt: str | None = None,
    new_passphrase: str | None = None,
    new_salt: str | None = None,
) -> dict:
    """主密钥轮换后，用旧 key 解密、新 key 重加密 Fernet 字段。"""
    old_passphrase = old_passphrase or os.getenv("MYHOME_KMS_PASSPHRASE", "")
    old_salt = old_salt or os.getenv("MYHOME_KMS_SALT", "myhome-v1.0")
    new_passphrase = new_passphrase or os.getenv("MYHOME_KMS_PASSPHRASE", "")
    new_salt = new_salt or os.getenv("MYHOME_KMS_SALT", "myhome-v1.0")
    if not old_passphrase or not new_passphrase:
        return {"success": False, "error": "KMS passphrase 未配置，无法重加密"}

    old_fernet = _fernet_from_params(old_passphrase, old_salt)
    new_fernet = _fernet_from_params(new_passphrase, new_salt)

    import sqlite3

    from ..config import DB_PATH

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rtsp = 0
    twofa = 0
    errors: list[str] = []
    try:
        tables = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "cameras" in tables:
            rows = conn.execute(
                "SELECT id, encrypted_rtsp_url FROM cameras WHERE encrypted_rtsp_url IS NOT NULL AND encrypted_rtsp_url != ''"
            ).fetchall()
            for row in rows:
                try:
                    plain = old_fernet.decrypt(row["encrypted_rtsp_url"].encode()).decode()
                    token = new_fernet.encrypt(plain.encode()).decode()
                    conn.execute("UPDATE cameras SET encrypted_rtsp_url = ? WHERE id = ?", (token, row["id"]))
                    rtsp += 1
                except Exception as e:
                    errors.append(f"camera {row['id']}: {e}")
        if "member_2fa" in tables:
            rows = conn.execute(
                "SELECT member_id, secret_key_encrypted FROM member_2fa WHERE enabled = 1 AND secret_key_encrypted != ''"
            ).fetchall()
            for row in rows:
                try:
                    plain = old_fernet.decrypt(row["secret_key_encrypted"].encode()).decode()
                    token = new_fernet.encrypt(plain.encode()).decode()
                    conn.execute("UPDATE member_2fa SET secret_key_encrypted = ? WHERE member_id = ?", (token, row["member_id"]))
                    twofa += 1
                except Exception as e:
                    errors.append(f"2fa member {row['member_id']}: {e}")
        conn.commit()
    finally:
        conn.close()

    return {
        "success": True,
        "rtsp_urls_reencrypted": rtsp,
        "member_2fa_reencrypted": twofa,
        "errors": errors[:10],
    }
