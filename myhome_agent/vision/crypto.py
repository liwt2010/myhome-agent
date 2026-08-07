"""rtsp_url 凭证加密 v0.3（§54.2.2 加密存储）

v0.3 实现：
- cryptography.fernet 对称加密
- 密钥从 .env 的 MYHOME_FERNET_KEY 派生（用户首次启动生成）
- encrypt/decrypt 工具函数
- cameras 表新增 encrypted_credentials 列（替换明文 rtsp_url）

密钥管理：
- 首次启动：自动生成 fernet key，写入 .env
- 备份：必须导出 .env 中的 key，否则新机器无法解密
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

ENV_KEY_NAME = "MYHOME_FERNET_KEY"


def _get_or_create_key() -> bytes:
    """从环境变量获取或自动生成 Fernet key

    v1.0 升级：优先用 KMS 派生（PBKDF2），.env 明文 key 仅 fallback
    """
    # v1.0 KMS 优先
    if os.getenv("MYHOME_KMS_PASSPHRASE"):
        try:
            from ..security.kms import kms_encrypt  # noqa
            # 用 KMS 派生 key
            from ..security.kms import LocalKMS
            kms = LocalKMS()
            return kms.derive_key()
        except Exception as e:
            logger.warning(f"KMS 派生失败，降级 .env: {e}")

    # v0.x fallback
    key = os.getenv(ENV_KEY_NAME)
    if key:
        return key.encode()

    # 自动生成
    try:
        from cryptography.fernet import Fernet
        new_key = Fernet.generate_key().decode()
        # 追加到 .env
        _append_to_env(f"{ENV_KEY_NAME}={new_key}")
        os.environ[ENV_KEY_NAME] = new_key
        logger.warning(f"已自动生成 {ENV_KEY_NAME} 并写入 .env；备份必带此 key")
        return new_key.encode()
    except ImportError:
        logger.error("缺少 cryptography，无法加密凭证")
        raise


def _append_to_env(line: str) -> None:
    """追加到项目 .env（如果存在）"""
    from ..config import ROOT

    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    with open(env_path, "a", encoding="utf-8") as f:
        if ENV_KEY_NAME not in env_path.read_text(encoding="utf-8"):
            f.write(f"\n# v0.3 自动生成（备份必带）\n{line}\n")


def encrypt(plaintext: str) -> str:
    """加密凭证

    Args:
        plaintext: 明文（如 rtsp_url）

    Returns:
        Fernet token (base64 url-safe)
    """
    if not plaintext:
        return ""
    from cryptography.fernet import Fernet

    f = Fernet(_get_or_create_key())
    return f.encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    """解密凭证"""
    if not token:
        return ""
    from cryptography.fernet import Fernet

    f = Fernet(_get_or_create_key())
    try:
        return f.decrypt(token.encode()).decode()
    except Exception as e:
        logger.error(f"解密失败（key 可能不匹配）: {e}")
        return ""


# ============================================================
# 数据库迁移
# ============================================================


MIGRATION_SQL = """
-- migrations/006_encrypt_rtsp_credentials.sql
ALTER TABLE cameras ADD COLUMN encrypted_rtsp_url TEXT;
ALTER TABLE cameras ADD COLUMN rtsp_url_legacy TEXT;
-- 迁移：将明文 rtsp_url 复制到 legacy，加密到新列
-- 完成后手动：DROP COLUMN rtsp_url；RENAME COLUMN rtsp_url_legacy TO rtsp_url_archived
-- v0.3 兼容期：双写（decrypt(encrypted_rtsp_url) || rtsp_url_legacy）
"""


def migrate_existing_rtsp_urls(db_path: str | Path) -> int:
    """一次性迁移：将明文 rtsp_url 加密到新列

    v0.3 兼容期保留 rtsp_url 列；新代码优先读 encrypted_rtsp_url
    """
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. 加新列（幂等）
    existing_cols = {r["name"] for r in cur.execute("PRAGMA table_info(cameras)").fetchall()}
    if "encrypted_rtsp_url" not in existing_cols:
        cur.execute("ALTER TABLE cameras ADD COLUMN encrypted_rtsp_url TEXT")

    # 2. 加密所有 rtsp_url
    rows = cur.execute("SELECT id, rtsp_url FROM cameras WHERE rtsp_url IS NOT NULL").fetchall()
    n = 0
    for row in rows:
        try:
            token = encrypt(row["rtsp_url"])
            cur.execute(
                "UPDATE cameras SET encrypted_rtsp_url = ? WHERE id = ?",
                (token, row["id"]),
            )
            n += 1
        except Exception as e:
            logger.warning(f"加密失败 {row['id']}: {e}")

    conn.commit()
    conn.close()
    logger.info(f"已加密 {n} 个摄像头凭证")
    return n


def get_rtsp_url(camera_row) -> str:
    """从 cameras 行获取解密后的 RTSP URL（v0.3 兼容期）"""
    encrypted = camera_row.get("encrypted_rtsp_url") if hasattr(camera_row, "get") else None
    if encrypted:
        try:
            return decrypt(encrypted)
        except Exception:
            pass
    # 兼容旧数据
    return camera_row["rtsp_url"] if "rtsp_url" in camera_row.keys() else ""
