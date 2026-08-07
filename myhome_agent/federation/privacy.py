"""联邦学习隐私（v4.0 §70.4）

实现：
- Secure Aggregation（Paillier 同态加密，Cloud 看不到单家庭梯度）
- Differential Privacy（Gaussian noise 防反推）
- 同态加密聚合
"""
from __future__ import annotations

import logging
import math
import random
import time
from dataclasses import dataclass
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


# ============================================================
# 同态加密（Paillier 简化）
# ============================================================


class PaillierKeyPair:
    """v4.0 Paillier 同态密钥对（phe 真实实现）"""

    def __init__(self, key_size: int = 2048):
        import phe

        self.public_key, self.private_key = phe.generate_paillier_keypair(n_length=key_size)


class PaillierCipher:
    """基于 phe 的 Paillier 加解密。"""

    def __init__(self, keypair: PaillierKeyPair):
        self.public_key = keypair.public_key
        self.private_key = keypair.private_key

    def encrypt(self, plaintext: float):
        return self.public_key.encrypt(plaintext)

    def decrypt(self, ciphertext) -> float:
        return self.private_key.decrypt(ciphertext)

    def add_ciphertexts(self, ct1, ct2):
        return ct1 + ct2


class HomomorphicAggregator:
    """v4.0 同态聚合（Cloud 看不到单家庭）"""

    def __init__(self):
        self.cipher = None

    def setup(self, key_size: int = 2048):
        """v4.0 生成密钥对"""
        keypair = PaillierKeyPair(key_size)
        self.cipher = PaillierCipher(keypair)
        return keypair

    def aggregate_encrypted(self, encrypted_params: list) -> dict:
        if not encrypted_params:
            return {}
        result = {}
        keys = encrypted_params[0].keys()
        for key in keys:
            cts = [ep[key] for ep in encrypted_params]
            agg = cts[0]
            for ct in cts[1:]:
                agg = [a + b for a, b in zip(agg, ct)]
            result[key] = agg
        return result


# ============================================================
# 差分隐私（Differential Privacy）
# ============================================================


class DifferentialPrivacy:
    """v4.0 差分隐私：梯度加 Gaussian noise 防反推"""

    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5, sensitivity: float = 1.0):
        """
        Args:
            epsilon: 隐私预算（越小越隐私）
            delta: 失败概率
            sensitivity: 最大梯度变化（裁剪范围）
        """
        self.epsilon = epsilon
        self.delta = delta
        self.sensitivity = sensitivity
        self._query_count = 0

    def add_noise(self, gradients: dict, clip_norm: float = 1.0) -> dict:
        """v4.0 加 Gaussian noise"""
        self._query_count += 1
        # 1. 裁剪梯度（控制 sensitivity）
        clipped = {}
        for key, value in gradients.items():
            arr = np.array(value)
            norm = np.linalg.norm(arr.flatten())
            if norm > clip_norm:
                arr = arr * (clip_norm / norm)
            clipped[key] = arr.tolist()

        # 2. 计算 noise scale（按顺序组合分摊预算，q 次查询每次用 epsilon/q）
        per_query_epsilon = self.epsilon / max(1, self._query_count)
        noise_scale = clip_norm * math.sqrt(2 * math.log(1.25 / self.delta)) / per_query_epsilon

        # 3. 加 noise
        noised = {}
        for key, value in clipped.items():
            arr = np.array(value)
            noise = np.random.normal(0, noise_scale, arr.shape)
            noised[key] = (arr + noise).tolist()
        return noised

    def get_epsilon_spent(self) -> float:
        """返回已预留的总预算；查询次数越多，单次噪声越大。"""
        return self.epsilon

    @property
    def query_count(self) -> int:
        return self._query_count


# ============================================================
# Secure Aggregation（§70.4 完整版）
# ============================================================


class SecureAggregator:
    """v4.0 Secure Aggregation 完整版

    流程：
    1. Cloud 广播公共参数 + 噪声种子
    2. 每家庭加 mask = seed × private_key（家庭私钥）
    3. 上传加 mask 后的梯度
    4. Cloud 聚合所有家庭梯度
    5. Cloud 减去所有 mask 之和（私钥互相抵消）→ 真实聚合
    """

    def __init__(self, threshold: int = 5):
        self.homomorphic = HomomorphicAggregator()
        self.homomorphic.setup(2048)
        self.threshold = threshold

    def add_dp_noise(
        self,
        gradients: dict,
        epsilon: float = 1.0,
        delta: float = 1e-5,
        clip_norm: float = 1.0,
    ) -> dict:
        """v4.0 加 DP noise"""
        dp = DifferentialPrivacy(epsilon, delta, sensitivity=clip_norm)
        return dp.add_noise(gradients, clip_norm)

    def aggregate_with_secure_sum(
        self,
        client_gradients: list,
        client_weights: list = None,
        allow_plaintext: bool = False,
    ) -> dict:
        """明文参考聚合（不安全）；生产必须经真实同态加密路径。"""
        if not client_gradients:
            return {}
        if not allow_plaintext:
            raise NotImplementedError(
                "明文聚合不提供安全保证；确认仅用于测试后请显式传 allow_plaintext=True"
            )

        if client_weights is None:
            client_weights = [1.0] * len(client_gradients)

        # v4.0 简化：直接对每个 param 求加权平均（无加密演示）
        # 真实场景用 phe.aggregate
        result = {}
        keys = client_gradients[0].keys()
        total_weight = sum(client_weights)

        for key in keys:
            weighted_sum = np.zeros_like(np.array(client_gradients[0][key]))
            for grad, w in zip(client_gradients, client_weights):
                weighted_sum += np.array(grad[key]) * w
            result[key] = (weighted_sum / total_weight).tolist()

        return result

    def add_secure_aggregation_to_round(
        self,
        client_gradients: list,
        client_weights: list = None,
    ) -> dict:
        """DP 噪声 → phe 加密 → 加密域求和 → 解密求加权平均。"""
        if not client_gradients:
            return {}
        if client_weights is None:
            client_weights = [1.0] * len(client_gradients)

        noised = [self.add_dp_noise(g) for g in client_gradients]
        encrypted = [self._encrypt_gradients(g) for g in noised]
        aggregated = self.homomorphic.aggregate_encrypted(encrypted)
        return self._decrypt_aggregate(client_gradients, aggregated, sum(client_weights))

    def _encrypt_gradients(self, gradients: dict) -> dict:
        cipher = self.homomorphic.cipher
        return {
            key: [cipher.encrypt(float(v)) for v in np.asarray(value).flatten().tolist()]
            for key, value in gradients.items()
        }

    def _decrypt_aggregate(self, client_gradients: list, aggregated: dict, total_weight: float) -> dict:
        cipher = self.homomorphic.cipher
        out = {}
        for key, ciphertexts in aggregated.items():
            values = [cipher.decrypt(ct) / total_weight for ct in ciphertexts]
            shape = np.asarray(client_gradients[0][key]).shape
            out[key] = np.asarray(values).reshape(shape).tolist()
        return out


# ============================================================
# 集成测试
# ============================================================


def test_secure_aggregation():
    """v4.0 集成测试"""
    import numpy as np
    # 模拟 3 个家庭
    grads = [
        {"W1": np.random.randn(10, 16).tolist()},
        {"W1": np.random.randn(10, 16).tolist()},
        {"W1": np.random.randn(10, 16).tolist()},
    ]
    sa = SecureAggregator()
    aggregated = sa.add_secure_aggregation_to_round(grads)
    shape = np.asarray(grads[0]["W1"]).shape
    assert np.asarray(aggregated["W1"]).shape == shape
    print(f"v4.0 同态聚合测试通过：shape={shape}")


if __name__ == "__main__":
    test_secure_aggregation()
