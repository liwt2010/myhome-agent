"""共识算法（v3.1 简化 PBFT）

§69.6 实现：
- 4 阶段：pre-prepare / prepare / commit / reply
- ≥2/3 同意 → 通过
- 简化版（家用场景不需要完整 BFT）

应用场景：
- 规则升级投票（多个家庭同意才能升级全局规则）
- 数据驻留策略（5/7 同意）
- 跨家庭协作决策
"""
from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ConsensusPhase(str, Enum):
    """v3.1 PBFT 4 阶段"""
    PRE_PREPARE = "pre_prepare"
    PREPARE = "prepare"
    COMMIT = "commit"
    REPLY = "reply"
    DECIDED = "decided"
    FAILED = "failed"


@dataclass
class Vote:
    """v3.1 单个投票"""
    agent_id: str
    proposal_id: str
    vote: bool  # True = yes, False = no
    timestamp: int = field(default_factory=lambda: int(time.time()))


@dataclass
class Proposal:
    """v3.1 提案"""
    proposal_id: str
    title: str
    description: str
    proposer: str
    payload: dict = field(default_factory=dict)  # 提案内容（规则更新等）
    phase: ConsensusPhase = ConsensusPhase.PRE_PREPARE
    created_at: int = field(default_factory=lambda: int(time.time()))
    deadline_at: int = 0
    required_yes_ratio: float = 2 / 3  # ≥2/3 同意
    votes: list = field(default_factory=list)  # Vote[]
    decided_at: int = 0
    passed: bool = False


class ConsensusEngine:
    """v3.1 简化 PBFT 共识引擎"""

    def __init__(self, store=None, agents: list | None = None):
        self.store = store
        # 模拟 Agent 集合（实际从 agent_cards 查）
        self.agents = agents or []
        self._proposals: dict[str, Proposal] = {}
        # 时间窗
        self.PREPARE_WINDOW = 2  # 秒
        self.COMMIT_WINDOW = 1  # 秒
        self.REPLY_WINDOW = 1  # 秒

    def create_proposal(
        self,
        title: str,
        description: str,
        proposer: str,
        payload: dict | None = None,
        required_yes_ratio: float = 2 / 3,
        deadline_seconds: int = 30,
    ) -> Proposal:
        """创建提案"""
        proposal = Proposal(
            proposal_id=f"prop_{uuid.uuid4().hex[:16]}",
            title=title,
            description=description,
            proposer=proposer,
            payload=payload or {},
            deadline_at=int(time.time()) + deadline_seconds,
            required_yes_ratio=required_yes_ratio,
        )
        self._proposals[proposal.proposal_id] = proposal
        # 持久化
        if self.store:
            try:
                with self.store._conn() as c:
                    c.execute(
                        """INSERT INTO consensus_proposals
                           (proposal_id, title, description, proposer, payload, deadline_at, required_yes_ratio)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            proposal.proposal_id, title, description, proposer,
                            json.dumps(proposal.payload, ensure_ascii=False),
                            proposal.deadline_at, proposal.required_yes_ratio,
                        ),
                    )
            except Exception as e:
                logger.error(f"create_proposal 失败: {e}")
        logger.info(f"共识提案创建: {proposal.proposal_id} {title}")
        return proposal

    def vote(self, proposal_id: str, agent_id: str, vote_yes: bool) -> bool:
        """v3.1 投票"""
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return False
        if int(time.time()) > proposal.deadline_at:
            logger.warning(f"提案 {proposal_id} 已过截止时间")
            return False
        if any(v.agent_id == agent_id for v in proposal.votes):
            logger.warning(f"agent {agent_id} 重复投票被拒绝")
            return False
        if self.agents and agent_id not in self.agents:
            logger.warning(f"agent {agent_id} 不在投票集合内")
            return False

        # 记录
        vote = Vote(agent_id=agent_id, proposal_id=proposal_id, vote=vote_yes)
        proposal.votes.append(vote)
        if self.store:
            try:
                with self.store._conn() as c:
                    c.execute(
                        "INSERT INTO consensus_votes (proposal_id, agent_id, vote, ts) VALUES (?, ?, ?, ?)",
                        (proposal_id, agent_id, 1 if vote_yes else 0, int(time.time())),
                    )
            except Exception as e:
                logger.error(f"vote 失败: {e}")
        return True

    def decide(self, proposal_id: str) -> Proposal:
        """v3.1 判定提案（PBFT 4 阶段简化）"""
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return None

        # 检查是否到达 deadline
        now = int(time.time())
        if now > proposal.deadline_at:
            proposal.phase = ConsensusPhase.FAILED
            proposal.passed = False
            self._persist_decision(proposal)
            return proposal

        # 简化 PBFT：单步判定（不真分 4 阶段）
        yes_votes = sum(1 for v in proposal.votes if v.vote)
        total_votes = len(proposal.votes)
        yes_ratio = yes_votes / max(total_votes, 1)
        if total_votes >= self._quorum_size():
            if yes_ratio >= proposal.required_yes_ratio:
                proposal.phase = ConsensusPhase.DECIDED
                proposal.passed = True
                proposal.decided_at = now
            else:
                proposal.phase = ConsensusPhase.FAILED
                proposal.passed = False
            self._persist_decision(proposal)
        return proposal

    def _quorum_size(self) -> int:
        """配置了 agent 集合时要求多数派参与，避免 1 票通过。"""
        if not self.agents:
            return 1
        return max(1, (len(self.agents) + 1) // 2)

    def _persist_decision(self, proposal: Proposal):
        if not self.store:
            return
        try:
            with self.store._conn() as c:
                c.execute(
                    "UPDATE consensus_proposals SET phase=?, passed=?, decided_at=? WHERE proposal_id=?",
                    (proposal.phase.value, 1 if proposal.passed else 0, proposal.decided_at, proposal.proposal_id),
                )
        except Exception as e:
            logger.error(f"_persist_decision 失败: {e}")

    def get_proposal(self, proposal_id: str) -> Proposal | None:
        return self._proposals.get(proposal_id)

    def list_proposals(self, status: ConsensusPhase | None = None) -> list[Proposal]:
        result = list(self._proposals.values())
        if status:
            result = [p for p in result if p.phase == status]
        return result


# ============================================================
# 跨家庭规则同步（v3.1 典型用例）
# ============================================================


class RuleConsensus:
    """v3.1 跨家庭规则升级共识"""

    def __init__(self, consensus: ConsensusEngine, marketplace: "Marketplace"):
        self.consensus = consensus
        self.marketplace = marketplace

    def propose_rule_update(
        self,
        rule_id: str,
        new_yaml: str,
        proposer: str,
        reason: str,
    ) -> Proposal:
        """提出规则升级"""
        return self.consensus.create_proposal(
            title=f"规则升级 {rule_id}",
            description=reason,
            proposer=proposer,
            payload={
                "type": "rule_update",
                "rule_id": rule_id,
                "yaml_body": new_yaml,
            },
        )

    def apply_if_passed(self, proposal_id: str, store) -> bool:
        """v3.1 通过后应用到所有家庭"""
        proposal = self.consensus.get_proposal(proposal_id)
        if not proposal or not proposal.passed:
            return False
        if proposal.payload.get("type") != "rule_update":
            return False
        rule_id = proposal.payload["rule_id"]
        yaml_body = proposal.payload["yaml_body"]
        try:
            from .engine import DSLError, parse_rule_yaml

            parsed = parse_rule_yaml(yaml_body)
            if parsed.id != rule_id:
                logger.error(f"规则升级 ID 不匹配: {parsed.id} != {rule_id}")
                return False
            with store._conn() as c:
                # 全家庭同步
                c.execute(
                    """UPDATE rules SET yaml_body = ?, cooldown = ?, window = ?, updated_at = ?
                       WHERE id = ? AND archived_at IS NULL""",
                    (yaml_body, parsed.cooldown, parsed.window, int(time.time()), rule_id),
                )
            logger.info(f"规则 {rule_id} 已跨家庭同步")
            return True
        except DSLError as e:
            logger.error(f"规则升级 YAML 校验失败: {e}")
            return False
        except Exception as e:
            logger.error(f"apply_rule 失败: {e}")
            return False


import json  # 末尾 import
