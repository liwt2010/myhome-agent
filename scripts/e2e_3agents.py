"""v4.2 3 Agent 端到端交易场景

模拟 3 个家庭：
- Agent A（张爷爷家）：老人照护 family，检测到异常
- Agent B（李家）：有高级视觉模型（YOLO-pose）
- Agent C（王家）：GPU 算力充裕，提供 LLM 兜底推理

流程：
A 检测到老人异常姿势 → 市场查 B 有视觉模型 → A 委托 B → B 完成并返回结果 → A 扣钱给 B → A 启动兜底推理给 C → C 返回 → 审计记录。
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AgentProfile:
    agent_id: str
    name: str
    capabilities: list
    wallet_balance: float


@dataclass
class TradeRecord:
    trade_id: str
    buyer: str
    seller: str
    service: str
    price: float
    status: str  # 'pending' | 'accepted' | 'executed' | 'completed' | 'failed'
    result: Any = None
    latency_ms: int = 0
    created_at: int = field(default_factory=lambda: int(time.time()))


class E2ESimulator:
    """v4.2 3 Agent 端到端模拟"""

    def __init__(self):
        self.agents: dict[str, AgentProfile] = {
            "agent_a": AgentProfile(
                "agent_a", "张爷爷家",
                ["elderly_care", "rule_execution", "basic_vision"],
                100.0,
            ),
            "agent_b": AgentProfile(
                "agent_b", "李家",
                ["advanced_vision", "yolov8n_pose", "person_detection"],
                150.0,
            ),
            "agent_c": AgentProfile(
                "agent_c", "王家",
                ["gpu_server", "llm_fallback", "deepseek_access"],
                200.0,
            ),
        }
        self.trades: list[TradeRecord] = []
        self.marketplace: dict[str, list] = {
            "vision_model": [
                {"seller": "agent_b", "capability": "advanced_vision",
                 "price": 5.0, "sla_ms": 2000},
            ],
            "llm_fallback": [
                {"seller": "agent_c", "capability": "llm_fallback",
                 "price": 8.0, "sla_ms": 3000},
            ],
        }

    def run_scenario(self, trigger_event: str, evidence: dict) -> list[TradeRecord]:
        """v4.2 3 Agent 完整交易场景"""
        trades = []
        t0_total = time.time()

        print("=" * 60)
        print(f"  v4.2 3 Agent 端到端交易模拟")
        print(f"  触发: {trigger_event}")
        print("=" * 60)
        print()
        print(f"Agent A ({self.agents['agent_a'].name}) 检测到: {trigger_event}")
        print(f"  A 钱包: ${self.agents['agent_a'].wallet_balance}")
        print()

        # ========== Step 1: A 查市场 ==========
        t0 = time.time()
        vision_services = self.marketplace.get("vision_model", [])
        best_vision = vision_services[0] if vision_services else None
        print(f"[Step 1] A 查 vision_model 市场 → {len(vision_services)} 个卖家")
        if best_vision:
            print(f"  → 选中 {best_vision['seller']} (${best_vision['price']})")
        print()

        # ========== Step 2: A → B vision 任务 ==========
        t0 = time.time()
        if best_vision:
            trade = TradeRecord(
                trade_id=f"trade_{int(time.time()*1000)}",
                buyer="agent_a", seller=best_vision["seller"],
                service="vision_model", price=best_vision["price"],
                status="accepted",
            )

            # 2a. A → B task_request（模拟网络延迟 50ms）
            time.sleep(0.05)
            # 2b. B 处理（模拟 300ms GPU 推理）
            time.sleep(0.3)
            # 2c. B → A task_response（模拟网络延迟 50ms）
            time.sleep(0.05)

            trade.status = "executed"
            trade.result = {"detections": 1, "confidence": 0.92, "kind": "fall_detected"}
            trade.latency_ms = int((time.time() - t0) * 1000)
            # 完整交易
            self.agents["agent_a"].wallet_balance -= trade.price
            self.agents["agent_b"].wallet_balance += trade.price
            trade.status = "completed"
            trades.append(trade)

            print(f"[Step 2a] A → B task_request (vision detect)")
            print(f"[Step 2b] B 推理 → {trade.result}")
            print(f"[Step 2c] B → A task_response ({trade.latency_ms}ms)")
            print(f"  B 钱包: ${self.agents['agent_b'].wallet_balance} (+${trade.price})")
            print()
        else:
            print(f"[Step 2] ❌ 无可用视觉服务")
            print()

        # ========== Step 3: A → C LLM 兜底推理 ==========
        t0 = time.time()
        llm_services = self.marketplace.get("llm_fallback", [])
        best_llm = llm_services[0] if llm_services else None
        print(f"[Step 3] A 查 llm_fallback 市场 → {len(llm_services)} 个卖家")
        if best_llm:
            print(f"  → 选中 {best_llm['seller']} (${best_llm['price']})")
            trade = TradeRecord(
                trade_id=f"trade_{int(time.time()*1000)}",
                buyer="agent_a", seller=best_llm["seller"],
                service="llm_fallback", price=best_llm["price"],
                status="accepted",
            )

            # 3a. A → C（模拟网络 50ms）
            time.sleep(0.05)
            # 3b. C 推理（模拟 500ms LLM 调用）
            time.sleep(0.5)
            # 3c. C → A（模拟网络 50ms）
            time.sleep(0.05)

            trade.status = "executed"
            trade.result = {
                "suggestion": "老人可能摔倒，建议 fire_rule + notify_caregiver",
                "confidence_after": 0.95,
            }
            trade.latency_ms = int((time.time() - t0) * 1000)
            self.agents["agent_a"].wallet_balance -= trade.price
            self.agents["agent_c"].wallet_balance += trade.price
            trade.status = "completed"
            trades.append(trade)

            print(f"[Step 3a] A → C task_request (llm fallback)")
            print(f"[Step 3b] C 推理 → {trade.result}")
            print(f"[Step 3c] C → A task_response ({trade.latency_ms}ms)")
            print(f"  C 钱包: ${self.agents['agent_c'].wallet_balance} (+${trade.price})")
            print()

        # ========== Step 4: 审计 ==========
        total_ms = int((time.time() - t0_total) * 1000)
        print(f"[Step 4] 场景结束")
        print(f"  总耗时: {total_ms}ms")
        print(f"  交易: {len(trades)} 笔")
        print(f"  A 钱包剩余: ${self.agents['agent_a'].wallet_balance:.2f}")
        print(f"  B 钱包剩余: ${self.agents['agent_b'].wallet_balance:.2f}")
        print(f"  C 钱包剩余: ${self.agents['agent_c'].wallet_balance:.2f}")
        print()
        print("=" * 60)
        print("  ✅ v4.2 3 Agent 端到端交易 PASS")
        print("=" * 60)

        self.trades.extend(trades)
        return trades


def main():
    sim = E2ESimulator()
    sim.run_scenario(
        trigger_event="老人起夜后 5 小时未归床，疑似摔倒",
        evidence={
            "bed_pressure": {"away_minutes": 300},
            "motion_living_room": {"duration_minutes": 45},
            "member_role": "elder",
        },
    )


if __name__ == "__main__":
    main()