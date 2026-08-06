"""GCP KMS Provider（v1.0.1 真实接入）

替换 v1.0 的 GCPStub。依赖 google-cloud-kms。

用法：
    kms = GCPKMS(
        project_id="myhome-prod",
        location="global",
        key_ring="myhome-ring",
        key_name="myhome-prod",
    )
    kms.create_key_ring()
    kms.create_key()
"""
from __future__ import annotations

import base64
import logging
import os
import time
from typing import Any

from .kms import KMSProvider

logger = logging.getLogger(__name__)


class GCPKMS(KMSProvider):
    """v1.0.1 GCP KMS 真实接入"""

    def __init__(
        self,
        project_id: str | None = None,
        location: str = "global",
        key_ring: str = "myhome-ring",
        key_name: str = "myhome-prod",
        credentials_path: str | None = None,
    ):
        """
        Args:
            project_id: GCP project ID
            location: 'global' / 'us-central1' / 'asia-east1' 等
            key_ring: KMS KeyRing 名
            key_name: KMS CryptoKey 名
            credentials_path: service account JSON 路径（生产用 workload identity）
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID", "")
        self.location = location
        self.key_ring = key_ring
        self.key_name = key_name
        self.credentials_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID 未设置")

        try:
            from google.cloud import kms  # type: ignore
        except ImportError:
            raise ImportError(
                "GCPKMS 需要 google-cloud-kms：`pip install google-cloud-kms`"
            )

        if self.credentials_path:
            self.client = kms.KeyManagementServiceClient.from_service_account_file(
                self.credentials_path
            )
        else:
            self.client = kms.KeyManagementServiceClient()

        self.key_name_full = self.client.crypto_key_path(
            self.project_id, self.location, self.key_ring, self.key_name
        )

    def get_key(self, key_id: str | None = None) -> bytes:
        """取 DEK（envelope encryption）"""
        kn = key_id or self.key_name_full
        try:
            # GCP 同样不返回 raw CMK
            response = self.client.generate_random_bytes(
                name=kn,
                location=self.location,
                length=32,
                protection_level=__import__(
                    "google.cloud.kms_v1", fromlist=["ProtectionLevel"]
                ).ProtectionLevel.SOFTWARE,
            )
            return response.data
        except Exception as e:
            logger.error(f"GCP KMS generate_random_bytes 失败: {e}")
            raise

    def encrypt(self, plaintext: str, key_id: str | None = None) -> str:
        kn = key_id or self.key_name_full
        try:
            response = self.client.encrypt(
                name=kn,
                plaintext=plaintext.encode("utf-8"),
            )
            return base64.b64encode(response.ciphertext).decode()
        except Exception as e:
            logger.error(f"GCP KMS encrypt 失败: {e}")
            raise

    def decrypt(self, ciphertext_b64: str, key_id: str | None = None) -> str:
        kn = key_id or self.key_name_full
        try:
            ciphertext = base64.b64decode(ciphertext_b64)
            response = self.client.decrypt(name=kn, ciphertext=ciphertext)
            return response.plaintext.decode("utf-8")
        except Exception as e:
            logger.error(f"GCP KMS decrypt 失败: {e}")
            raise

    def rotate_key(self, key_id: str | None = None, new_key: bytes | None = None) -> str:
        """轮换：GCP KMS CryptoKey.primary 指向新 version"""
        kn = key_id or self.key_name_full
        try:
            new_version = self.client.create_crypto_key_version(
                parent=kn,
                crypto_key_version={
                    "algorithm": __import__(
                        "google.cloud.kms_v1", fromlist=["CryptoKeyVersion"]
                    ).CryptoKeyVersion.CryptoKeyVersionAlgorithm.GOOGLE_SYMMETRIC_ENCRYPTION,
                },
            )
            # Set primary
            self.client.update_crypto_key_primary_version(
                crypto_key=kn,
                crypto_key_version_id=new_version.name.split("/")[-1],
            )
            return new_version.name
        except Exception as e:
            logger.error(f"GCP KMS 轮换失败: {e}")
            raise

    def list_versions(self, key_id: str | None = None) -> list[str]:
        kn = key_id or self.key_name_full
        try:
            versions = self.client.list_crypto_key_versions(parent=kn)
            return [v.name.split("/")[-1] for v in versions]
        except Exception as e:
            logger.error(f"GCP KMS list versions 失败: {e}")
            return []

    def create_key_ring(self) -> str:
        """创建 KeyRing（一次性）"""
        try:
            parent = f"projects/{self.project_id}/locations/{self.location}"
            ring_path = f"{parent}/keyRings/{self.key_ring}"
            self.client.create_key_ring(
                request={
                    "parent": parent,
                    "key_ring_id": self.key_ring,
                }
            )
            logger.info(f"GCP KMS KeyRing 创建: {ring_path}")
            return ring_path
        except Exception as e:
            if "ALREADY_EXISTS" in str(e):
                return ring_path
            raise

    def create_key(self) -> str:
        """创建 CryptoKey（KeyRing 必须先存在）"""
        try:
            parent = f"projects/{self.project_id}/locations/{self.location}/keyRings/{self.key_ring}"
            key_path = self.client.create_crypto_key(
                request={
                    "parent": parent,
                    "crypto_key_id": self.key_name,
                    "crypto_key": {
                        "purpose": __import__(
                            "google.cloud.kms_v1", fromlist=["CryptoKey"]
                        ).CryptoKey.CryptoKeyPurpose.ENCRYPT_DECRYPT,
                        "version_template": {
                            "algorithm": __import__(
                                "google.cloud.kms_v1", fromlist=["CryptoKeyVersion"]
                            ).CryptoKeyVersion.CryptoKeyVersionAlgorithm.GOOGLE_SYMMETRIC_ENCRYPTION,
                            "protection_level": __import__(
                                "google.cloud.kms_v1", fromlist=["ProtectionLevel"]
                            ).ProtectionLevel.SOFTWARE,
                        },
                        "rotation_period": {"seconds": 90 * 24 * 3600},  # 90 天轮换
                    },
                }
            )
            logger.info(f"GCP KMS CryptoKey 创建: {key_path.name}")
            return key_path.name
        except Exception as e:
            if "ALREADY_EXISTS" in str(e):
                return self.key_name_full
            raise


def get_kms_gcp() -> GCPKMS:
    """GCP KMS 工厂"""
    return GCPKMS()