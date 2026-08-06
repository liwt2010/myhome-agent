"""动态配额 v0.5（§50 升级路径 1）

v0.5 实现：
- 按时段（白天/夜间/度假）+ per-household 动态配额
- LLM 兜底：白天 10/天 → 夜间减半 → 度假 ×1.5
- 视觉 LLM：白天 20 → 夜间 5
- 资源池隔离（不同类型配额独立计数）
- 降级链：超限 → 降级到本地 → 警告用户

v0.5 不做：
- 跨家庭配额共享（v1.0）
- 智能预测配额（v1.0）
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# 资源类型
RESOURCE_LLM_FALLBACK = "llm_fallback"
RESOURCE_LLM_VISION = "llm_vision"
RESOURCE_RULE_FIRE = "rule_fire"


# 时段
TIME_DAY = "day"          # 8:00-22:00
TIME_NIGHT = "night"      # 22:00-8:00
TIME_VACATION = "vacation"  # 度假（用户标记）


@dataclass
class QuotaConfig:
    """单个资源的配额配置"""

    resource: str
    base_limit: int  # 基础每日上限
    night_factor: float = 0.5  # 夜间系数
    vacation_factor: float = 1.5  # 度假系数
    enabled: bool = True


# v0.5 默认配额
DEFAULT_QUOTAS: dict[str, QuotaConfig] = {
    RESOURCE_LLM_FALLBACK: QuotaConfig(
        resource=RESOURCE_LLM_FALLBACK,
        base_limit=10,        # 白天 10/天
        night_factor=0.5,      # 夜间 5/天
        vacation_factor=1.5,   # 度假 15/天
    ),
    RESOURCE_LLM_VISION: QuotaConfig(
        resource=RESOURCE_LLM_VISION,
        base_limit=20,        # 白天 20/天
        night_factor=0.25,     # 夜间 5/天
        vacation_factor=1.5,   # 度假 30/天
    ),
    RESOURCE_RULE_FIRE: QuotaConfig(
        resource=RESOURCE_RULE_FIRE,
        base_limit=500,       # 白天 500/天
        night_factor=1.0,      # 夜间不限制
        vacation_factor=1.0,
    ),
}


@dataclass
class DynamicQuotas:
    """v0.5 动态配额管理器"""

    household_id: int = 1
    configs: dict[str, QuotaConfig] = field(default_factory=lambda: dict(DEFAULT_QUOTAS))
    is_vacation: bool = False

    # 内部计数
    _counts: dict[tuple[str, str], int] = field(default_factory=dict)
    # (household_id, resource, day_str) → count

    def get_current_period(self) -> str:
        """取当前时段"""
        if self.is_vacation:
            return TIME_VACATION
        hour = int(time.strftime("%H"))
        return TIME_DAY if 8 <= hour < 22 else TIME_NIGHT

    def get_effective_limit(self, resource: str) -> int:
        """取资源的当前有效上限"""
        cfg = self.configs.get(resource)
        if not cfg or not cfg.enabled:
            return 0
        period = self.get_current_period()
        limit = cfg.base_limit
        if period == TIME_NIGHT:
            limit = int(limit * cfg.night_factor)
        elif period == TIME_VACATION:
            limit = int(limit * cfg.vacation_factor)
        return max(1, limit)

    def is_over_limit(self, resource: str) -> bool:
        """检查是否超限"""
        limit = self.get_effective_limit(resource)
        count = self._get_count(resource)
        return count >= limit

    def get_remaining(self, resource: str) -> int:
        """剩余可用次数"""
        limit = self.get_effective_limit(resource)
        count = self._get_count(resource)
        return max(0, limit - count)

    def increment(self, resource: str, n: int = 1) -> None:
        """计数 +n"""
        day = time.strftime("%Y-%m-%d")
        key = (str(self.household_id), resource, day)
        self._counts[key] = self._counts.get(key, 0) + n
        logger.debug(
            f"[quota] {self.household_id} {resource} {self._counts[key]}/{self.get_effective_limit(resource)}"
        )

    def _get_count(self, resource: str) -> int:
        day = time.strftime("%Y-%m-%d")
        return self._counts.get((str(self.household_id), resource, day), 0)

    def get_stats(self) -> dict:
        """取所有资源配额状态"""
        period = self.get_current_period()
        stats = {
            "household_id": self.household_id,
            "period": period,
            "is_vacation": self.is_vacation,
            "resources": {},
        }
        for resource, cfg in self.configs.items():
            limit = self.get_effective_limit(resource)
            count = self._get_count(resource)
            stats["resources"][resource] = {
                "limit": limit,
                "used": count,
                "remaining": max(0, limit - count),
                "base_limit": cfg.base_limit,
            }
        return stats

    def enter_vacation(self) -> None:
        self.is_vacation = True
        logger.info(f"household {self.household_id} 进入度假模式")

    def exit_vacation(self) -> None:
        self.is_vacation = False
        logger.info(f"household {self.household_id} 退出度假模式")

    def check_and_increment(self, resource: str) -> tuple[bool, int]:
        """检查 + 计数（原子操作）

        Returns:
            (allowed, remaining)
        """
        if self.is_over_limit(resource):
            return False, 0
        self.increment(resource)
        return True, self.get_remaining(resource)


# ============================================================
# FallbackReasoner 集成（v0.5 修订）
# ============================================================


class QuotaManager:
    """v0.5 多家庭配额管理"""

    def __init__(self):
        self._quotas: dict[int, DynamicQuotas] = {}

    def get(self, household_id: int) -> DynamicQuotas:
        if household_id not in self._quotas:
            self._quotas[household_id] = DynamicQuotas(household_id=household_id)
        return self._quotas[household_id]

    def all_stats(self) -> list[dict]:
        return [q.get_stats() for q in self._quotas.values()]
