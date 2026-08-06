"""AWS KMS Provider（v1.0.1 真实接入）

替换 v1.0 的 AWSCMSStub。依赖 boto3。

用法：
    kms = AWSKMS(key_id="arn:aws:kms:eu-central-1:123456789012:key/abcd-...")
    kms.create_alias("alias/myhome-prod", key_id)
    kms_encrypt("secret data", kms=kms)
"""
from __future__ import annotations

import base64
import json
import logging
import os
import time
from typing import Any

from .kms import KMSProvider

logger = logging.getLogger(__name__)


class AWSKMS(KMSProvider):
    """v1.0.1 AWS KMS 真实接入（生产推荐）"""

    def __init__(
        self,
        key_id: str | None = None,
        region: str = "eu-central-1",
        profile: str | None = None,
    ):
        """
        Args:
            key_id: KMS Key ARN 或 alias
            region: AWS 区域（默认 eu-central-1，GDPR 合规）
            profile: AWS profile 名（本地开发）
        """
        self.key_id = key_id or os.getenv("AWS_KMS_KEY_ID", "")
        self.region = region

        try:
            import boto3  # type: ignore
            from botocore.config import Config  # type: ignore
        except ImportError:
            raise ImportError(
                "AWSKMS 需要 boto3：`pip install boto3`（清华镜像：-i https://pypi.tuna.tsinghua.edu.cn/simple/）"
            )

        session_kwargs = {"region_name": region}
        if profile:
            session_kwargs["profile_name"] = profile

        try:
            self.session = boto3.session.Session(**session_kwargs)
            self.client = self.session.client(
                "kms",
                config=Config(
                    retries={"max_attempts": 3, "mode": "standard"},
                    connect_timeout=5,
                    read_timeout=10,
                ),
            )
        except Exception as e:
            logger.error(f"AWS KMS 客户端初始化失败: {e}")
            raise

        if not self.key_id:
            logger.warning(
                "AWS_KMS_KEY_ID 未配置；调用 get_key() 会失败。"
                "请通过 init_key() 创建或 AWS 控制台手动创建。"
            )

    def get_key(self, key_id: str | None = None) -> bytes:
        """取 key bytes

        AWS KMS 不会直接返回 plaintext key（这是它的安全模型）。
        我们返回的是加密的 blob，应用层用 KMS 解密此 blob 后用结果加密数据。
        实际应用中，更常见的做法是 envelope encryption：
        - Data Encryption Key (DEK) 在本地生成
        - DEK 用 KMS CMK 加密
        - 用 DEK 加密实际数据

        本接口返回 DEK 的 plaintext（由 KMS 解密 envelope 而得）。
        """
        kid = key_id or self.key_id
        if not kid:
            raise ValueError("key_id 未指定")

        try:
            # GenerateDataKey 返回 (Plaintext, CiphertextBlob)
            response = self.client.generate_data_key(
                KeyId=kid,
                KeySpec="AES_256",
            )
            return response["Plaintext"]
        except Exception as e:
            logger.error(f"AWS KMS generate_data_key 失败: {e}")
            raise

    def encrypt(self, plaintext: str, key_id: str | None = None) -> str:
        """直接加密（< 4KB 数据）

        大数据请用 envelope encryption（get_key 拿 DEK + 本地 Fernet）。
        """
        kid = key_id or self.key_id
        try:
            response = self.client.encrypt(
                KeyId=kid,
                Plaintext=plaintext.encode("utf-8"),
            )
            return base64.b64encode(response["CiphertextBlob"]).decode()
        except Exception as e:
            logger.error(f"AWS KMS encrypt 失败: {e}")
            raise

    def decrypt(self, ciphertext_b64: str, key_id: str | None = None) -> str:
        """直接解密"""
        kid = key_id or self.key_id
        try:
            ciphertext = base64.b64decode(ciphertext_b64)
            response = self.client.decrypt(
                KeyId=kid,
                CiphertextBlob=ciphertext,
            )
            return response["Plaintext"].decode("utf-8")
        except Exception as e:
            logger.error(f"AWS KMS decrypt 失败: {e}")
            raise

    def rotate_key(self, key_id: str | None = None, new_key: bytes | None = None) -> str:
        """轮换：AWS KMS 用 enable_key_rotation 自动管

        不需要传 new_key（KMS 内部生成）
        """
        kid = key_id or self.key_id
        try:
            self.client.enable_key_rotation(KeyId=kid)
            logger.info(f"AWS KMS key {kid} 启用自动轮换")
            return f"aws-kms-{kid}-rotation-enabled"
        except Exception as e:
            logger.error(f"AWS KMS enable_key_rotation 失败: {e}")
            raise

    def list_versions(self, key_id: str | None = None) -> list[str]:
        """列出 key 轮换历史（v1.0.1 简化：返回 enabled/disabled）"""
        kid = key_id or self.key_id
        try:
            response = self.client.get_key_rotation_status(KeyId=kid)
            return ["enabled" if response["KeyRotationEnabled"] else "disabled"]
        except Exception as e:
            logger.error(f"AWS KMS get_key_rotation_status 失败: {e}")
            return []

    def create_key(
        self,
        description: str = "myhome-agent master key",
        alias: str | None = None,
    ) -> str:
        """创建新 KMS Key

        Returns:
            Key ARN
        """
        try:
            response = self.client.create_key(
                Description=description,
                KeyUsage="ENCRYPT_DECRYPT",
                Origin="AWS_KMS",
            )
            new_key_id = response["KeyMetadata"]["Arn"]
            if alias:
                self.client.create_alias(
                    AliasName=alias,
                    TargetKeyId=new_key_id,
                )
                logger.info(f"AWS KMS 创建 key + alias: {new_key_id} → {alias}")
            return new_key_id
        except Exception as e:
            logger.error(f"AWS KMS create_key 失败: {e}")
            raise

    def schedule_deletion(self, key_id: str | None = None, pending_days: int = 30) -> str:
        """计划删除（GDPR §17 数据擦除）"""
        kid = key_id or self.key_id
        try:
            response = self.client.schedule_key_deletion(
                KeyId=kid,
                PendingWindowInDays=pending_days,
            )
            logger.warning(f"AWS KMS key {kid} 计划删除（{pending_days} 天）")
            return response["DeletionDate"]
        except Exception as e:
            logger.error(f"AWS KMS schedule_deletion 失败: {e}")
            raise


# ============================================================
# KMS 工厂（更新）
# ============================================================


def get_kms_aws() -> AWSKMS:
    """AWS KMS 工厂"""
    return AWSKMS()


# ============================================================
# 安全最佳实践（v1.0.1 提示）
# ============================================================

SECURITY_BEST_PRACTICES = """
1. **永远不要 export raw key** — AWS KMS 设计上不让 export
2. **用 envelope encryption** — DEK 在本地生成 + KMS 加密 DEK
3. **enable_key_rotation** — 年度自动轮换
4. **IAM 最小权限** — 只给 decrypt/encrypt，不给 delete
5. **key policy** — 禁止 root account 直访
6. **审计日志** — CloudTrail 开启，记录每次 API 调用
7. **跨区域** — 全球家庭数据用 eu-central-1 / ap-southeast-1
8. **删除前 schedule_deletion** — 7-30 天 pending window
9. **应急恢复** — 备份 alias / ARN 到密码管理器
10. **合规** — GDPR / SOC2 / ISO 27001 一并启用
"""