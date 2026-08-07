"""myhome.market 平台核心（v3.1）

实现：
- Agent Card 注册 / 查询
- 服务目录（5 类）
- 任务市场（request / bid / complete）
- 信誉系统（v3.1 复用）
- 钱包（CARE-token 余额 + 转账）
- A2A 消息路由

v3.1 核心：去中心化 Agent 平台，本会话实现核心 stub。
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================
# Agent Card
# ============================================================


@dataclass
class AgentCard:
    """v3.1 Agent Card（§69.2）"""
    agent_id: str
    household: str
    version: str
    capabilities: list = field(default_factory=list)
    resources: dict = field(default_factory=dict)
    availability: dict = field(default_factory=dict)
    pricing: dict = field(default_factory=dict)
    rating_score: int = 500  # 初始中等
    calls_completed: int = 0
    disputes: int = 0
    last_active: int = field(default_factory=lambda: int(time.time()))
    public_key: str = ""

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "version": self.version,
            "household": self.household,
            "capabilities": self.capabilities,
            "resources": self.resources,
            "availability": self.availability,
            "pricing": self.pricing,
            "rating": {
                "score": self.rating_score,
                "calls_completed": self.calls_completed,
                "disputes": self.disputes,
            },
            "public_key": self.public_key,
        }


# ============================================================
# 服务类型 + 任务
# ============================================================


class ServiceType(str, Enum):
    RULE_TEMPLATE = "rule_template"
    VISION_MODEL = "vision_model"
    FALLBACK_LLM = "fallback_llm"
    ANOMALY_SAMPLE = "anomaly_sample"
    DEVICE_PROXY = "device_proxy"


class TaskStatus(str, Enum):
    PENDING = "pending"          # 已发布，待投标
    BIDDING = "bidding"          # 有人投标
    ASSIGNED = "assigned"        # 已分配给卖方
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DISPUTED = "disputed"


@dataclass
class ServiceListing:
    """服务目录条目"""
    listing_id: str
    seller_agent_id: str
    service_type: ServiceType
    title: str
    description: str
    price_tokens: float
    sla_seconds: int = 60
    capabilities: list = field(default_factory=list)
    rating_floor: int = 0
    enabled: bool = True
    created_at: int = field(default_factory=lambda: int(time.time()))


@dataclass
class MarketTask:
    """任务市场条目（§69.4）"""
    task_id: str
    buyer_agent_id: str
    service_type: ServiceType
    args: dict = field(default_factory=dict)
    price_tokens: float = 0.0
    escrow_tokens: float = 0.0  # 托管中
    seller_agent_id: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    bids: list = field(default_factory=list)  # [{agent_id, price, eta_ms}]
    result: Any = None
    created_at: int = field(default_factory=lambda: int(time.time()))
    deadline_at: int = 0
    completed_at: int = 0


@dataclass
class A2AMessage:
    """v3.1 A2A 协议消息（§69.5）"""
    a2a_version: str = "1.0"
    from_agent: str = ""
    to_agent: str = ""
    message_id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:16]}")
    timestamp: int = field(default_factory=lambda: int(time.time()))
    signature: str = ""
    type: str = "task_request"  # task_request | task_response | negotiation | consensus_vote
    payload: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "a2a_version": self.a2a_version,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "signature": self.signature,
            "type": self.type,
            "payload": self.payload,
        }

    def sign(self, private_key: str) -> None:
        """v3.1 简化签名：HMAC-SHA256"""
        content = json.dumps({
            "from": self.from_agent, "to": self.to_agent, "ts": self.timestamp,
            "type": self.type, "payload": self.payload,
        }, sort_keys=True)
        self.signature = "hmac-sha256:" + hashlib.hmac.new(
            private_key.encode(), content.encode(), hashlib.sha256
        ).hexdigest()[:32]


# ============================================================
# 信誉系统
# ============================================================


class ReputationEngine:
    """v3.1 信誉（§69.7）"""

    def __init__(self, store=None):
        self.store = store

    def update(
        self,
        agent_id: str,
        task_completed: bool,
        sla_met: bool,
        user_rating: int = 0,  # 1-5
    ) -> int:
        """更新 Agent 信誉评分（0-1000）"""
        try:
            with self.store._conn() as c:
                row = c.execute(
                    "SELECT rating_score, calls_completed, disputes FROM agent_cards WHERE agent_id = ?",
                    (agent_id,),
                ).fetchone()
                if not row:
                    return 500
                score = row["rating_score"]
                completed = row["calls_completed"]
                disputes = row["disputes"]

                delta = 0
                if task_completed:
                    delta += 5
                    completed += 1
                else:
                    delta -= 10
                    disputes += 1
                if sla_met and task_completed:
                    delta += 3
                if user_rating > 0:
                    delta += (user_rating - 3) * 5  # 1-5 星

                new_score = max(0, min(1000, score + delta))
                c.execute(
                    "UPDATE agent_cards SET rating_score=?, calls_completed=?, disputes=? WHERE agent_id=?",
                    (new_score, completed, disputes, agent_id),
                )
                return new_score
        except Exception as e:
            logger.error(f"update reputation 失败: {e}")
            return 500

    def should_throttle(self, agent_id: str) -> bool:
        """v3.1 限流：评分 < 500 限流"""
        score = self._get_score(agent_id)
        return 0 < score < 500

    def _get_score(self, agent_id: str) -> int:
        try:
            with self.store._conn() as c:
                row = c.execute(
                    "SELECT rating_score FROM agent_cards WHERE agent_id = ?",
                    (agent_id,),
                ).fetchone()
                return row["rating_score"] if row else 500
        except Exception:
            return 500


# ============================================================
# 钱包
# ============================================================


class Wallet:
    """v3.1 CARE-token 钱包（§69.8）"""

    def __init__(self, store=None):
        self.store = store

    def balance(self, agent_id: str) -> float:
        try:
            with self.store._conn() as c:
                row = c.execute(
                    "SELECT balance FROM wallets WHERE agent_id = ?", (agent_id,)
                ).fetchone()
                return row["balance"] if row else 0.0
        except Exception:
            return 0.0

    def credit(self, agent_id: str, amount: float, reason: str = "") -> bool:
        """加钱"""
        return self._transfer("_mint_", agent_id, amount, reason)

    def debit(self, agent_id: str, amount: float, reason: str = "") -> bool:
        """扣钱"""
        if self.balance(agent_id) < amount:
            return False
        return self._transfer(agent_id, "_burn_", amount, reason)

    def _transfer(self, from_id: str, to_id: str, amount: float, reason: str) -> bool:
        try:
            with self.store._conn() as c:
                if from_id != "_mint_":
                    cur = c.execute(
                        "UPDATE wallets SET balance = balance - ? WHERE agent_id = ? AND balance >= ?",
                        (amount, from_id, amount),
                    )
                    if cur.rowcount == 0:
                        raise ValueError(f"余额不足: {from_id}")
                if to_id != "_burn_":
                    c.execute(
                        "UPDATE wallets SET balance = balance + ? WHERE agent_id = ?",
                        (amount, to_id),
                    )
                c.execute(
                    "INSERT INTO wallet_transactions (from_agent, to_agent, amount, reason, ts) VALUES (?, ?, ?, ?, ?)",
                    (from_id, to_id, amount, reason, int(time.time())),
                )
            return True
        except Exception as e:
            logger.error(f"transfer 失败: {e}")
            return False

    def escrow(self, buyer: str, seller: str, task_id: str, amount: float) -> bool:
        """任务托管"""
        try:
            with self.store._conn() as c:
                cur = c.execute(
                    "UPDATE wallets SET balance = balance - ?, escrow_balance = escrow_balance + ? "
                    "WHERE agent_id = ? AND balance >= ?",
                    (amount, amount, buyer, amount),
                )
                if cur.rowcount == 0:
                    raise ValueError(f"buyer 余额不足: {buyer}")
                c.execute(
                    "INSERT INTO task_escrow (task_id, buyer, seller, amount, status) VALUES (?, ?, ?, ?, 'held')",
                    (task_id, buyer, seller, amount),
                )
            return True
        except Exception as e:
            logger.error(f"escrow 失败: {e}")
            return False

    def release_escrow(self, task_id: str) -> bool:
        """任务完成 → 释放托管金给卖方"""
        try:
            with self.store._conn() as c:
                row = c.execute(
                    "SELECT buyer, seller, amount FROM task_escrow WHERE task_id = ? AND status = 'held'",
                    (task_id,),
                ).fetchone()
                if not row:
                    return False
                amount = row["amount"]
                c.execute(
                    "UPDATE wallets SET escrow_balance = escrow_balance - ? WHERE agent_id = ?",
                    (amount, row["buyer"]),
                )
                c.execute(
                    "UPDATE wallets SET balance = balance + ? WHERE agent_id = ?",
                    (amount, row["seller"]),
                )
                c.execute(
                    "UPDATE task_escrow SET status = 'released' WHERE task_id = ?",
                    (task_id,),
                )
                c.execute(
                    "INSERT INTO wallet_transactions (from_agent, to_agent, amount, reason, ts) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (row["buyer"], row["seller"], amount, f"escrow_release:{task_id}", int(time.time())),
                )
            return True
        except Exception as e:
            logger.error(f"release_escrow 失败: {e}")
            return False


# ============================================================
# Marketplace 平台
# ============================================================


class Marketplace:
    """v3.1 myhome.market 平台主类（§69.1）"""

    def __init__(self, store=None):
        self.store = store
        self.reputation = ReputationEngine(store)
        self.wallet = Wallet(store)
        self._listings: dict[str, ServiceListing] = {}
        self._tasks: dict[str, MarketTask] = {}
        self._cards: dict[str, AgentCard] = {}

    # ============================================================
    # Agent Card
    # ============================================================

    def register_agent(self, card: AgentCard) -> bool:
        """注册 Agent"""
        try:
            with self.store._conn() as c:
                c.execute(
                    """INSERT OR REPLACE INTO agent_cards
                       (agent_id, household, version, capabilities, resources, availability, pricing, rating_score, public_key)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        card.agent_id, card.household, card.version,
                        json.dumps(card.capabilities, ensure_ascii=False),
                        json.dumps(card.resources, ensure_ascii=False),
                        json.dumps(card.availability, ensure_ascii=False),
                        json.dumps(card.pricing, ensure_ascii=False),
                        card.rating_score, card.public_key,
                    ),
                )
            self._cards[card.agent_id] = card
            return True
        except Exception as e:
            logger.error(f"register_agent 失败: {e}")
            return False

    def find_agents(
        self, capability: str = None, min_rating: int = 0, max_price: float = None,
    ) -> list[AgentCard]:
        """查 Agent 目录（按能力 / 评分 / 价格过滤）"""
        try:
            with self.store._conn() as c:
                rows = c.execute(
                    "SELECT * FROM agent_cards WHERE rating_score >= ? ORDER BY rating_score DESC",
                    (min_rating,),
                ).fetchall()
            result = []
            for row in rows:
                card = self._row_to_card(row)
                if capability and capability not in card.capabilities:
                    continue
                if max_price is not None and card.pricing.get("rate_per_call", 0) > max_price:
                    continue
                result.append(card)
            return result
        except Exception as e:
            logger.error(f"find_agents 失败: {e}")
            return []

    def _row_to_card(self, row) -> AgentCard:
        return AgentCard(
            agent_id=row["agent_id"],
            household=row["household"],
            version=row["version"],
            capabilities=json.loads(row["capabilities"] or "[]"),
            resources=json.loads(row["resources"] or "{}"),
            availability=json.loads(row["availability"] or "{}"),
            pricing=json.loads(row["pricing"] or "{}"),
            rating_score=row["rating_score"],
            public_key=row["public_key"] or "",
        )

    # ============================================================
    # 服务目录
    # ============================================================

    def publish_listing(self, listing: ServiceListing) -> bool:
        """发布服务"""
        try:
            with self.store._conn() as c:
                c.execute(
                    """INSERT INTO service_listings
                       (listing_id, seller_agent_id, service_type, title, description, price_tokens, sla_seconds, capabilities, enabled)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        listing.listing_id, listing.seller_agent_id, listing.service_type.value,
                        listing.title, listing.description, listing.price_tokens, listing.sla_seconds,
                        json.dumps(listing.capabilities, ensure_ascii=False),
                        1 if listing.enabled else 0,
                    ),
                )
            self._listings[listing.listing_id] = listing
            return True
        except Exception as e:
            logger.error(f"publish_listing 失败: {e}")
            return False

    def search_listings(
        self, service_type: ServiceType = None, max_price: float = None,
    ) -> list[ServiceListing]:
        """查服务目录"""
        try:
            with self.store._conn() as c:
                if service_type:
                    rows = c.execute(
                        "SELECT * FROM service_listings WHERE service_type = ? AND enabled = 1 ORDER BY price_tokens",
                        (service_type.value,),
                    ).fetchall()
                else:
                    rows = c.execute(
                        "SELECT * FROM service_listings WHERE enabled = 1 ORDER BY price_tokens"
                    ).fetchall()
            result = []
            for row in rows:
                if max_price and row["price_tokens"] > max_price:
                    continue
                result.append(self._row_to_listing(row))
            return result
        except Exception as e:
            logger.error(f"search_listings 失败: {e}")
            return []

    def _row_to_listing(self, row) -> ServiceListing:
        return ServiceListing(
            listing_id=row["listing_id"],
            seller_agent_id=row["seller_agent_id"],
            service_type=ServiceType(row["service_type"]),
            title=row["title"],
            description=row["description"],
            price_tokens=row["price_tokens"],
            sla_seconds=row["sla_seconds"],
            capabilities=json.loads(row["capabilities"] or "[]"),
            enabled=bool(row["enabled"]),
        )

    # ============================================================
    # 任务市场
    # ============================================================

    def post_task(self, task: MarketTask) -> bool:
        """发布任务"""
        try:
            with self.store._conn() as c:
                c.execute(
                    """INSERT INTO market_tasks
                       (task_id, buyer_agent_id, service_type, args, price_tokens, escrow_tokens, status, deadline_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        task.task_id, task.buyer_agent_id, task.service_type.value,
                        json.dumps(task.args, ensure_ascii=False),
                        task.price_tokens, task.escrow_tokens, task.status.value, task.deadline_at,
                    ),
                )
            # 托管
            self.wallet.escrow(task.buyer_agent_id, "_escrow_", task.task_id, task.escrow_tokens)
            self._tasks[task.task_id] = task
            return True
        except Exception as e:
            logger.error(f"post_task 失败: {e}")
            return False

    def bid(self, task_id: str, seller_agent_id: str, price: float, eta_ms: int) -> bool:
        """投标"""
        try:
            with self.store._conn() as c:
                c.execute(
                    "INSERT INTO task_bids (task_id, seller_agent_id, price, eta_ms) VALUES (?, ?, ?, ?)",
                    (task_id, seller_agent_id, price, eta_ms),
                )
                if task_id in self._tasks:
                    self._tasks[task_id].bids.append({
                        "agent_id": seller_agent_id, "price": price, "eta_ms": eta_ms,
                    })
            return True
        except Exception as e:
            logger.error(f"bid 失败: {e}")
            return False

    def assign(self, task_id: str, seller_agent_id: str) -> bool:
        """分配任务"""
        try:
            with self.store._conn() as c:
                c.execute(
                    "UPDATE market_tasks SET seller_agent_id = ?, status = ? WHERE task_id = ?",
                    (seller_agent_id, TaskStatus.ASSIGNED.value, task_id),
                )
                if task_id in self._tasks:
                    self._tasks[task_id].seller_agent_id = seller_agent_id
                    self._tasks[task_id].status = TaskStatus.ASSIGNED
            return True
        except Exception as e:
            logger.error(f"assign 失败: {e}")
            return False

    def complete_task(self, task_id: str, result: Any) -> bool:
        """完成任务"""
        try:
            with self.store._conn() as c:
                c.execute(
                    "UPDATE market_tasks SET status = ?, result = ?, completed_at = ? WHERE task_id = ?",
                    (TaskStatus.COMPLETED.value, json.dumps(result, ensure_ascii=False),
                     int(time.time()), task_id),
                )
                # 释放托管
                if task_id in self._tasks:
                    self._tasks[task_id].status = TaskStatus.COMPLETED
                    self._tasks[task_id].result = result
            return self.wallet.release_escrow(task_id)
        except Exception as e:
            logger.error(f"complete_task 失败: {e}")
            return False

    # ============================================================
    # 统计
    # ============================================================

    def get_stats(self) -> dict:
        return {
            "agents": len(self._cards),
            "listings": len(self._listings),
            "tasks": {
                "pending": sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING),
                "assigned": sum(1 for t in self._tasks.values() if t.status == TaskStatus.ASSIGNED),
                "completed": sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED),
            },
        }


# ============================================================
# A2A 处理器
# ============================================================


class A2AHandler:
    """v3.1 A2A 协议处理器（§69.5）"""

    def __init__(self, marketplace: Marketplace, private_key: str = "myhome-agent"):
        self.marketplace = marketplace
        self.private_key = private_key

    def send_task_request(
        self, from_agent: str, to_agent: str, task_type: str, args: dict, price: float,
    ) -> bool:
        """发送任务请求"""
        msg = A2AMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            type="task_request",
            payload={"task": task_type, "args": args, "price": price},
        )
        msg.sign(self.private_key)
        # v3.1 简化：直接调 marketplace API
        # 真实场景：HTTP POST 到目标 agent 的 A2A 端点
        task = MarketTask(
            task_id=msg.message_id,
            buyer_agent_id=from_agent,
            seller_agent_id=to_agent,
            service_type=ServiceType(task_type),
            args=args,
            price_tokens=price,
            escrow_tokens=price,
        )
        return self.marketplace.post_task(task)

    def send_consensus_vote(
        self, from_agent: str, to_agent: str, proposal_id: str, vote: bool,
    ) -> bool:
        """发送共识投票"""
        msg = A2AMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            type="consensus_vote",
            payload={"proposal_id": proposal_id, "vote": "yes" if vote else "no"},
        )
        msg.sign(self.private_key)
        # v3.1 stub
        return True


# ============================================================
# 数据库表
# ============================================================


MARKETPLACE_SCHEMA = """
CREATE TABLE IF NOT EXISTS agent_cards (
  agent_id TEXT PRIMARY KEY,
  household TEXT NOT NULL,
  version TEXT NOT NULL,
  capabilities TEXT,
  resources TEXT,
  availability TEXT,
  pricing TEXT,
  rating_score INTEGER DEFAULT 500,
  calls_completed INTEGER DEFAULT 0,
  disputes INTEGER DEFAULT 0,
  public_key TEXT,
  created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
  updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

CREATE TABLE IF NOT EXISTS service_listings (
  listing_id TEXT PRIMARY KEY,
  seller_agent_id TEXT NOT NULL,
  service_type TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  price_tokens REAL NOT NULL,
  sla_seconds INTEGER DEFAULT 60,
  capabilities TEXT,
  enabled INTEGER DEFAULT 1,
  created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_listings_type ON service_listings(service_type, price_tokens);

CREATE TABLE IF NOT EXISTS market_tasks (
  task_id TEXT PRIMARY KEY,
  buyer_agent_id TEXT NOT NULL,
  seller_agent_id TEXT,
  service_type TEXT NOT NULL,
  args TEXT,
  price_tokens REAL NOT NULL,
  escrow_tokens REAL DEFAULT 0,
  status TEXT DEFAULT 'pending',
  result TEXT,
  created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
  deadline_at INTEGER,
  completed_at INTEGER
);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON market_tasks(status, created_at DESC);

CREATE TABLE IF NOT EXISTS task_bids (
  bid_id INTEGER PRIMARY KEY,
  task_id TEXT NOT NULL,
  seller_agent_id TEXT NOT NULL,
  price REAL,
  eta_ms INTEGER,
  created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

CREATE TABLE IF NOT EXISTS wallets (
  agent_id TEXT PRIMARY KEY,
  balance REAL DEFAULT 0,
  escrow_balance REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS wallet_transactions (
  tx_id INTEGER PRIMARY KEY,
  from_agent TEXT NOT NULL,
  to_agent TEXT NOT NULL,
  amount REAL NOT NULL,
  reason TEXT,
  ts INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

CREATE TABLE IF NOT EXISTS task_escrow (
  task_id TEXT PRIMARY KEY,
  buyer TEXT NOT NULL,
  seller TEXT,
  amount REAL NOT NULL,
  status TEXT DEFAULT 'held'
);

CREATE INDEX IF NOT EXISTS idx_escrow_status ON task_escrow(status);
"""
