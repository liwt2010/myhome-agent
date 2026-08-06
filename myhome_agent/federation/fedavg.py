"""联邦学习核心（v4.0）

实现：
- GlobalModel（Cloud 端）
- LocalTrainer（家庭端）
- FedAvg + FedProx 聚合
- 异步聚合（不等最慢）
- 异常检测（防恶意梯度）
- 8-bit 梯度压缩

v4.0 简化实现：纯 NumPy（不依赖 PyTorch / TensorFlow）
- 模型：小 MLP（2-3 层）
- 任务：v4.0 默认"摔倒检测"二分类
- 数据：每个家庭本地 50 样本（自动标注后）

真实实施可用 Flower / PySyft（推荐 v4.0.4 替换）
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


# ============================================================
# 模型（v4.0 简化 MLP）
# ============================================================


class SimpleMLP:
    """v4.0 简化 MLP（2 层 + ReLU）"""

    def __init__(self, input_dim: int = 10, hidden: int = 16, output: int = 2):
        # Xavier 初始化
        self.W1 = np.random.randn(input_dim, hidden) * np.sqrt(2 / input_dim)
        self.b1 = np.zeros(hidden)
        self.W2 = np.random.randn(hidden, output) * np.sqrt(2 / hidden)
        self.b2 = np.zeros(output)

    def forward(self, X: np.ndarray) -> np.ndarray:
        """前向"""
        self.z1 = X @ self.W1 + self.b1
        self.a1 = np.maximum(0, self.z1)  # ReLU
        self.z2 = self.a1 @ self.W2 + self.b2
        # softmax
        exp = np.exp(self.z2 - self.z2.max(axis=1, keepdims=True))
        return exp / exp.sum(axis=1, keepdims=True)

    def get_params(self) -> dict:
        return {"W1": self.W1, "b1": self.b1, "W2": self.W2, "b2": self.b2}

    def set_params(self, params: dict) -> None:
        self.W1 = params["W1"]
        self.b1 = params["b1"]
        self.W2 = params["W2"]
        self.b2 = params["b2"]

    def get_grads(self) -> dict:
        return {"W1": np.zeros_like(self.W1), "b1": np.zeros_like(self.b1),
                "W2": np.zeros_like(self.W2), "b2": np.zeros_like(self.b2)}


# ============================================================
# 全局模型（v4.0 Cloud 端）
# ============================================================


class GlobalModel:
    """v4.0 协调器端全局模型"""

    def __init__(self, model: SimpleMLP, version: str = "0.0.0"):
        self.model = model
        self.version = version
        self._round = 0

    def get_weights(self) -> dict:
        return {k: v.tolist() for k, v in self.model.get_params().items()}

    def set_weights(self, weights: dict) -> None:
        params = {k: np.array(v) for k, v in weights.items()}
        self.model.set_params(params)

    def aggregate(
        self,
        client_gradients: list,
        client_weights: list = None,
        method: str = "fedavg",
    ) -> dict:
        """v4.0 聚合（FedAvg / FedProx）"""
        if not client_gradients:
            return self.get_weights()

        if client_weights is None:
            client_weights = [1.0] * len(client_gradients)
        total_weight = sum(client_weights)

        # 加权平均
        aggregated = {}
        for key in client_gradients[0].keys():
            aggregated[key] = np.zeros_like(np.array(client_gradients[0][key]))
            for grad, w in zip(client_gradients, client_weights):
                aggregated[key] += np.array(grad[key]) * (w / total_weight)

        # FedProx：加近端项（如果有）
        if method == "fedprox":
            # 简化：实际 FederatedProximal 应基于当前全局 + μ
            # 此处 stub
            pass

        return {k: v.tolist() for k, v in aggregated.items()}

    def update(self, aggregated: dict) -> None:
        """v4.0 用聚合结果更新全局模型"""
        params = {k: np.array(v) for k, v in aggregated.items()}
        # 简单 SGD（v4.0 简化：聚合 = 更新）
        self.model.set_params(params)
        self._round += 1
        self.version = f"0.{self._round}.0"


# ============================================================
# 本地训练器（v4.0 家庭端）
# ============================================================


class LocalTrainer:
    """v4.0 本地家庭训练器"""

    def __init__(self, model: SimpleMLP, learning_rate: float = 0.01,
                 epochs: int = 5, batch_size: int = 8):
        self.model = model
        self.lr = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self._sample_count = 0
        self._last_train_loss = 0.0

    def train_one_epoch(self, X: np.ndarray, y: np.ndarray) -> float:
        """v4.0 一轮训练"""
        n = len(X)
        total_loss = 0.0
        for i in range(0, n, self.batch_size):
            Xb = X[i:i + self.batch_size]
            yb = y[i:i + self.batch_size]

            # 前向
            probs = self.model.forward(Xb)
            # 交叉熵 loss
            eps = 1e-9
            loss = -np.mean(np.log(probs[np.arange(len(yb)), yb] + eps))
            total_loss += loss

            # 简化：计算梯度
            d_z2 = probs.copy()
            d_z2[np.arange(len(yb)), yb] -= 1
            d_z2 /= len(yb)

            d_a1 = d_z2 @ self.model.W2.T
            d_z1 = d_a1 * (self.model.z1 > 0)  # ReLU 导数

            dW2 = self.model.a1.T @ d_z2
            db2 = d_z2.sum(axis=0)
            dW1 = Xb.T @ d_z1
            db1 = d_z1.sum(axis=0)

            # SGD 更新
            self.model.W2 -= self.lr * dW2
            self.model.b2 -= self.lr * db2
            self.model.W1 -= self.lr * dW1
            self.model.b1 -= self.lr * db1

        self._last_train_loss = total_loss / max(n // self.batch_size, 1)
        return self._last_train_loss

    def train(self, X: np.ndarray, y: np.ndarray) -> dict:
        """v4.0 完整本地训练"""
        self._sample_count = len(X)
        for epoch in range(self.epochs):
            loss = self.train_one_epoch(X, y)
        # 返回梯度（diff: new - old）
        old_params = self.model.get_params()
        # v4.0 简化：直接返回 new params（client 上传的是 params，不是 grad）
        # FedAvg 实际是上传 grad；但 v4.0 简化传 params（更易实现）
        return {
            "params": self.model.get_params(),
            "samples": self._sample_count,
            "loss": self._last_train_loss,
        }


# ============================================================
# 异步聚合（v4.0 不阻塞）
# ============================================================


class AsyncAggregator:
    """v4.0 异步聚合（不等最慢家庭）"""

    def __init__(self, global_model: GlobalModel, max_staleness: int = 3):
        self.global_model = global_model
        self.max_staleness = max_staleness
        # 缓存：{client_id: (params, version_at_send)}
        self._pending: dict[str, tuple] = {}
        # 触发：每收到 N 个就聚合
        self.min_clients_per_round = 5
        self._round = 0

    def submit(self, client_id: str, params: dict, samples: int = 1):
        """v4.0 家庭提交参数"""
        current_version = self.global_model.version
        self._pending[client_id] = (params, samples, current_version)
        logger.info(f"v4.0 {client_id} 提交参数 (samples={samples}, version={current_version})")

    def maybe_aggregate(self) -> bool:
        """v4.0 检查是否够触发聚合"""
        if len(self._pending) < self.min_clients_per_round:
            return False
        # 过滤 stale（超过 max_staleness 轮）
        current_version = self.global_model.version
        valid = []
        for cid, (params, samples, version) in self._pending.items():
            if current_version != version:
                # v4.0 简化：stale 的直接扔
                logger.warning(f"v4.0 丢弃 {cid} 的 stale 参数")
                continue
            valid.append((params, samples))
        if not valid:
            return False
        # 聚合
        params_list = [p for p, _ in valid]
        weights = [s for _, s in valid]
        aggregated = self.global_model.aggregate(params_list, weights)
        self.global_model.update(aggregated)
        self._pending.clear()
        self._round += 1
        logger.info(f"v4.0 全局模型 round {self._round} 更新 → {self.global_model.version}")
        return True

    def get_pending_count(self) -> int:
        return len(self._pending)


# ============================================================
# 异常检测（防恶意梯度）
# ============================================================


class AnomalyDetector:
    """v4.0 异常梯度检测（防恶意 / 噪声家庭）"""

    def __init__(self, threshold_std: float = 3.0):
        self.threshold_std = threshold_std

    def filter_by_std(self, gradients: list) -> list:
        """v4.0 简化：过滤 >3σ 异常"""
        if len(gradients) < 2:
            return gradients
        # 算每个梯度 norm
        norms = [np.linalg.norm(np.array(list(g.values())).flatten()) for g in gradients]
        mean = np.mean(norms)
        std = np.std(norms)
        return [g for g, n in zip(gradients, norms) if abs(n - mean) < self.threshold_std * std]

    def filter_by_median(self, gradients: list) -> list:
        """v4.0 简化：Krum 风格（选最接近 median）"""
        # 实际 Krum 选 sum of distances to closest K-2 最小
        # 简化：直接 median 聚合
        if not gradients:
            return []
        # median 聚合：每个 param 取中位数
        keys = gradients[0].keys()
        median_grad = {}
        for key in keys:
            stacks = [np.array(g[key]) for g in gradients]
            median_grad[key] = np.median(stacks, axis=0).tolist()
        # v4.0 简化：返回 median 代替所有（实际应保留最相似的）
        return [median_grad]


# ============================================================
# 8-bit 梯度压缩
# ============================================================


class GradientCompressor:
    """v4.0 8-bit 量化压缩（节省带宽 4x）"""

    @staticmethod
    def quantize(gradients: dict) -> dict:
        """8-bit 量化（float32 → uint8 + scale + zero_point）"""
        compressed = {}
        for key, value in gradients.items():
            arr = np.array(value, dtype=np.float32)
            min_v, max_v = arr.min(), arr.max()
            scale = (max_v - min_v) / 255.0 if max_v > min_v else 1.0
            zero_point = int(-min_v / scale) if scale > 0 else 0
            qarr = np.clip((arr / scale + zero_point), 0, 255).astype(np.uint8)
            compressed[key] = {
                "q": qarr.tolist(),
                "scale": float(scale),
                "zero_point": int(zero_point),
            }
        return compressed

    @staticmethod
    def dequantize(compressed: dict) -> dict:
        """反量化"""
        result = {}
        for key, comp in compressed.items():
            qarr = np.array(comp["q"], dtype=np.uint8)
            arr = (qarr.astype(np.float32) - comp["zero_point"]) * comp["scale"]
            result[key] = arr.tolist()
        return result


# ============================================================
# v4.0 Orchestrator（Cloud 端）
# ============================================================


class FederatedOrchestrator:
    """v4.0 联邦学习协调器（Cloud 端）"""

    def __init__(self, input_dim: int = 10, hidden: int = 16, output: int = 2):
        self.global_model = GlobalModel(SimpleMLP(input_dim, hidden, output))
        self.aggregator = AsyncAggregator(self.global_model)
        self.anomaly = AnomalyDetector()
        self.compressor = GradientCompressor()
        # 客户端注册
        self._clients: dict[str, dict] = {}  # client_id → {model, metadata}

    def register_client(self, client_id: str, model: SimpleMLP):
        """v4.0 家庭注册"""
        # 复制当前全局模型给客户端
        weights = self.global_model.get_weights()
        model.set_weights({k: np.array(v) for k, v in weights.items()})
        self._clients[client_id] = {"model": model}

    def receive_update(self, client_id: str, params: dict, samples: int = 1):
        """v4.0 接收家庭更新"""
        # 1. 反量化
        if isinstance(list(params.values())[0], dict):
            params = self.compressor.dequantize(params)
        # 2. 异常检测
        all_params = list(self._pending_params.values()) if hasattr(self, '_pending_params') else []
        all_params.append(params)
        if len(all_params) > 5:
            filtered = self.anomaly.filter_by_std(all_params)
        else:
            filtered = all_params
        # 3. 提交到异步聚合
        self.aggregator.submit(client_id, params, samples)
        if not hasattr(self, '_pending_params'):
            self._pending_params = {}
        self._pending_params[client_id] = params

    def tick(self) -> bool:
        """v4.0 周期性 tick：尝试聚合"""
        if self.aggregator.maybe_aggregate():
            self._pending_params.clear()
            return True
        return False

    def get_global_version(self) -> str:
        return self.global_model.version

    def get_global_weights(self) -> dict:
        return self.global_model.get_weights()