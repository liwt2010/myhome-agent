"""自动标注 + 联邦训练（v4.0 §70.13 关键创新）

流程：
1. 本地 YOLO 检测到候选事件（如 fall_detected）
2. 询问用户确认（"刚才是真摔倒吗？" 是/否）
3. 真实样本 → 自动加入本地训练集
4. 累积 ≥10 样本 → 触发本地训练
5. 训练完 → 上传梯度（不上传样本）
6. Cloud 聚合 → 下一轮
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


# ============================================================
# 数据结构
# ============================================================


class LabelStatus(str, Enum):
    """v4.0 标注状态"""
    PENDING = "pending"          # 等待用户确认
    CONFIRMED = "confirmed"      # 用户确认是真事件
    REJECTED = "rejected"       # 用户说不是
    AUTO_SKIPPED = "auto_skipped"  # 置信度太低


@dataclass
class LocalSample:
    """v4.0 本地样本"""
    sample_id: str
    member_id: int
    features: list  # 提取的特征向量
    label: int      # 0=normal, 1=fall
    source: str     # 'yolo' | 'manual' | 'confirmed'
    confidence: float
    ts: int
    status: LabelStatus = LabelStatus.PENDING


@dataclass
class TrainingConfig:
    """v4.0 训练配置"""
    min_samples_to_train: int = 10  # 触发训练的最小样本数
    auto_label_threshold: float = 0.85  # YOLO 置信度阈值（高才询问）
    retrain_interval_days: int = 7
    epochs_per_round: int = 5
    learning_rate: float = 0.01


# ============================================================
# 自动标注
# ============================================================


class AutoLabeler:
    """v4.0 自动标注器（§70.13）"""

    def __init__(self, config: TrainingConfig | None = None):
        self.config = config or TrainingConfig()
        self._pending: list = []

    def on_yolo_detection(
        self,
        member_id: int,
        features: list,
        confidence: float,
        kind: str,
    ) -> LocalSample | None:
        """YOLO 检测到事件时调用"""
        # 高置信度才询问
        if confidence < self.config.auto_label_threshold:
            return LocalSample(
                sample_id=f"sample_{int(time.time() * 1000)}",
                member_id=member_id,
                features=features,
                label=0,  # 未知
                source="yolo",
                confidence=confidence,
                ts=int(time.time()),
                status=LabelStatus.AUTO_SKIPPED,
            )

        # 加入 pending，等用户确认
        sample = LocalSample(
            sample_id=f"sample_{int(time.time() * 1000)}",
            member_id=member_id,
            features=features,
            label=0,
            source="yolo",
            confidence=confidence,
            ts=int(time.time()),
            status=LabelStatus.PENDING,
        )
        self._pending.append(sample)
        logger.info(f"v4.0 加入待标注: {sample.sample_id} ({kind})")
        return sample

    def user_confirm(self, sample_id: str, is_real: bool) -> LocalSample | None:
        """v4.0 用户确认"""
        for i, s in enumerate(self._pending):
            if s.sample_id == sample_id:
                if is_real:
                    s.status = LabelStatus.CONFIRMED
                    s.label = 1  # 摔倒
                else:
                    s.status = LabelStatus.REJECTED
                    s.label = 0  # 正常
                confirmed = s
                self._pending.pop(i)
                logger.info(f"v4.0 用户{'确认' if is_real else '拒绝'}: {sample_id}")
                return confirmed
        return None

    def get_pending(self) -> list:
        return self._pending

    def clear_pending(self) -> None:
        self._pending.clear()


# ============================================================
# 联邦训练触发器
# ============================================================


class FederatedTrainer:
    """v4.0 联邦训练触发器（家庭端）"""

    def __init__(self, config: TrainingConfig, store=None):
        self.config = config
        self.store = store
        self._samples: list = []  # 本地累积

    def add_sample(self, sample: LocalSample) -> bool:
        """v4.0 累积样本（仅 CONFIRMED）"""
        if sample.status != LabelStatus.CONFIRMED:
            return False
        self._samples.append(sample)
        self._persist_sample(sample)
        return True

    def should_train(self) -> bool:
        """v4.0 触发条件：≥10 confirmed 样本"""
        return len(self._samples) >= self.config.min_samples_to_train

    def get_training_data(self) -> tuple[np.ndarray, np.ndarray]:
        """v4.0 取训练数据"""
        X = np.array([s.features for s in self._samples])
        y = np.array([s.label for s in self._samples])
        return X, y

    def clear_samples(self) -> None:
        """v4.0 训练后清空（避免重复训练）"""
        self._samples.clear()

    def _persist_sample(self, sample: LocalSample):
        if not self.store:
            return
        try:
            with self.store._conn() as c:
                c.execute(
                    """INSERT INTO fl_samples
                       (sample_id, member_id, features, label, source, confidence, ts, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        sample.sample_id, sample.member_id,
                        json.dumps(sample.features), sample.label,
                        sample.source, sample.confidence, sample.ts, sample.status.value,
                    ),
                )
        except Exception as e:
            logger.error(f"persist sample 失败: {e}")


# ============================================================
# 完整联邦训练流程
# ============================================================


class FullFLRound:
    """v4.0 完整一轮联邦训练"""

    def __init__(self, config: TrainingConfig, store=None):
        self.config = config
        self.store = store
        self.labeler = AutoLabeler(config)
        self.trainer = FederatedTrainer(config, store)

    def step1_yolo_detect(self, member_id: int, features: list, confidence: float, kind: str):
        """v4.0 步骤 1：YOLO 检测到事件"""
        return self.labeler.on_yolo_detection(member_id, features, confidence, kind)

    def step2_user_confirm(self, sample_id: str, is_real: bool):
        """v4.0 步骤 2：用户确认"""
        sample = self.labeler.user_confirm(sample_id, is_real)
        if sample:
            self.trainer.add_sample(sample)
        return sample

    def step3_check_trigger(self) -> bool:
        """v4.0 步骤 3：是否触发训练"""
        return self.trainer.should_train()

    def step4_get_data(self) -> tuple:
        """v4.0 步骤 4：取训练数据"""
        return self.trainer.get_training_data()

    def step5_after_train(self):
        """v4.0 步骤 5：训练后清样本"""
        self.trainer.clear_samples()


# ============================================================
# 特征提取（v4.0 占位：实际接 YOLO 输出）
# ============================================================


def extract_features_from_yolo(
    bbox: list,  # [x, y, w, h]
    confidence: float,
    pose: list | None = None,  # 17 关键点
) -> list:
    """v4.0 简化特征提取（实际应更复杂）"""
    # bbox 归一化 + 比例 + 关键点距离
    features = list(bbox) + [confidence]
    if pose:
        # 关键点 17 × 3（x, y, conf）= 51
        flat = []
        for kp in pose:
            flat.extend(kp)
        features.extend(flat)
    else:
        features.extend([0.0] * 51)
    # 填充到 64 维
    while len(features) < 64:
        features.append(0.0)
    return features[:64]


# ============================================================
# DB Schema
# ============================================================


FL_SCHEMA = """
CREATE TABLE IF NOT EXISTS consensus_proposals (
  proposal_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  proposer TEXT NOT NULL,
  payload TEXT,
  deadline_at INTEGER NOT NULL,
  required_yes_ratio REAL DEFAULT 0.67,
  phase TEXT DEFAULT 'pre_prepare',
  passed INTEGER,
  decided_at INTEGER,
  created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

CREATE TABLE IF NOT EXISTS consensus_votes (
  proposal_id TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  vote INTEGER NOT NULL,
  ts INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
  PRIMARY KEY (proposal_id, agent_id)
);

CREATE TABLE IF NOT EXISTS fl_samples (
  sample_id TEXT PRIMARY KEY,
  member_id INTEGER NOT NULL,
  features TEXT NOT NULL,
  label INTEGER NOT NULL,
  source TEXT,
  confidence REAL,
  ts INTEGER NOT NULL,
  status TEXT DEFAULT 'pending'
);
CREATE INDEX IF NOT EXISTS idx_fl_samples_member ON fl_samples(member_id, ts DESC);
"""