# 服务代办抽象（Services）

> ARCHITECTURE.md §23 的接口契约与安全设计。本文件给到工程级的 adapter 框架、安全闸门、订单状态机。

## 1. 抽象与目录结构

```
myhome_agent/services/
├── base.py                  # ServiceAdapter / Intent / Option / Order 类型
├── registry.py              # 注册 + 启动自检
├── router.py                # intent → 候选 service 路由
├── audit.py                 # 订单自治审计链路（autonomous_id 串联 §18）
├── guard.py                 # 四道闸门（预算/角色/渠道/审计）
├── finance_tracker.py       # 内置：家庭账本查询（无对外执行）
├── calendar_orchestrator.py # 内置：跨日历编排
├── dryrun.py                # 服务代理 dry-run 报告生成
└── adapters/                # 第三方服务
    ├── __init__.py
    ├── _example_template/   # 模板，最简 Adapter 示例
    ├── meituan/             # 外卖/生鲜
    ├── gaode/               # 地图/打车
    ├── eleme/
    └── ...
```

## 2. ServiceAdapter 接口

```python
# myhome_agent/services/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

@dataclass
class Capability:
    id: str                    # 'order_food' / 'book_ride'
    description: str
    requires_dry_run: bool = True
    allowed_roles: set[str] = field(default_factory=lambda: {"admin", "adult"})
    required_confirm_level: int = 2  # 默认 L2


@dataclass
class Query:
    intent_kind: str          # 'order_food' / 'compare_price' / 'book_taxi'
    params: dict[str, Any]    # 业务参数


@dataclass
class Option:
    id: str
    title: str
    summary: str
    estimated_cost: float     # 元；-1 表示非金额动作
    estimated_time_seconds: int
    requires_external_account: bool
    risk_level: str           # 'low' / 'medium' / 'high'


@dataclass
class OrderRequest:
    service_id: str
    option_id: str
    member_id: int
    channel: str
    idempotency_key: str      # 防重


@dataclass
class Order:
    id: str
    service_id: str
    status: str               # 'pending' / 'confirmed' / 'in_progress' / 'done' / 'failed' / 'cancelled'
    estimated_cost: float
    external_ref: str | None  # 服务方订单号
    created_at: str
    finished_at: str | None


class ServiceAdapter(ABC):
    @property
    @abstractmethod
    def service_id(self) -> str: ...

    @property
    def display_name(self) -> str:
        return self.service_id

    @property
    def category(self) -> str:
        """'delivery' / 'transit' / 'utility' / 'shopping' / 'finance'"""
        return "other"

    @abstractmethod
    async def list_capabilities(self) -> list[Capability]: ...

    @abstractmethod
    async def query(self, q: Query, ctx: dict) -> list[Option]: ...

    @abstractmethod
    async def execute(self, req: OrderRequest) -> Order: ...

    @abstractmethod
    async def track(self, order_id: str) -> Order: ...

    # 可选钩子
    def authenticate(self, ctx: dict) -> bool:
        return ctx.get("authed", False)

    def supports_dry_run(self) -> bool:
        return True
```

## 3. 注册与发现

```python
# myhome_agent/services/registry.py

class ServiceRegistry:
    def __init__(self):
        self.adapters: dict[str, ServiceAdapter] = {}

    def register(self, adapter: ServiceAdapter):
        self.adapters[adapter.service_id] = adapter

    def enabled(self, services: list[str] | None = None) -> dict[str, ServiceAdapter]:
        if services is None:
            return self.adapters
        return {sid: a for sid, a in self.adapters.items() if sid in services}

    def get(self, service_id: str) -> ServiceAdapter:
        return self.adapters[service_id]
```

**启用配置**（`config/plugins.yaml` 已有的服务字段）：

```yaml
services:
  enabled:
    - meituan              # 外卖/生鲜
    - gaode                # 打车
    # - _12306              # 默认关闭
    # - eleme

  budgets:
    per_order_default: 200            # 单笔超 200 必须二次确认
    per_day_default: 500              # 单日超 500 必须二次确认
    per_service:                      # 可 per-service 覆盖
      meituan: 100

  require_double_confirm:             # 强制二级确认的渠道
    - telegram
    - wechat
```

## 4. 四道闸门（Guard）

```python
# myhome_agent/services/guard.py

@dataclass
class GuardDecision:
    allow: bool
    need_confirm: bool
    reason: str = ""
    blocking_factors: list[str] = field(default_factory=list)


async def check(ctx: OrderContext, registry: ServiceRegistry) -> GuardDecision:
    blockers = []
    need_confirm = False

    # 闸门 1：预算
    if ctx.option.estimated_cost > ctx.budget_per_order:
        blockers.append(f"超单笔预算 {ctx.budget_per_order}元")
        need_confirm = True
    if ctx.cumulative_today_cost + ctx.option.estimated_cost > ctx.budget_per_day:
        blockers.append("将超过当日预算")
        need_confirm = True

    # 闸门 2：角色
    if ctx.member_role not in ctx.capability.allowed_roles:
        blockers.append(f"角色 {ctx.member_role} 不允许调用 {ctx.capability.id}")

    # 闸门 3：渠道分级（继承 §5.3）
    if ctx.channel in ctx.high_risk_channels:
        if ctx.option.risk_level == "high":
            blockers.append(f"远程渠道不能执行 high 风险动作")
            need_confirm = True

    # 闸门 4：审计（必须能记，无离线写盘则拒绝）
    if not ctx.audit_writable:
        blockers.append("审计层不可写，服务代办拒绝执行（保护原则）")

    allow = len([b for b in blockers if "不允许" in b]) == 0
    return GuardDecision(allow=allow, need_confirm=need_confirm,
                         blocking_factors=blockers,
                         reason=("需要二次确认" if need_confirm and allow else ""))
```

## 5. 订单状态机

```
pending → confirmed → in_progress → done
   │           │            │
   ↓           ↓            ↓
cancelled  failed        failed
```

**实现**：`myhome_agent/services/orders.py` 维护 `orders` 表：

| 列 | 类型 | 用途 |
|----|------|------|
| `id` | TEXT PK | UUID |
| `service_id` | TEXT | 服务标识 |
| `member_id` | INT | 下单人 |
| `channel` | TEXT | 来源渠道 |
| `autonomous_id` | TEXT | §18 链路 id |
| `state` | TEXT | pending/confirmed/in_progress/done/failed/cancelled |
| `estimated_cost` | REAL | 预估 |
| `actual_cost` | REAL | 实付 |
| `external_ref` | TEXT | 服务方订单号 |
| `created_at` | TEXT | UTC |
| `finished_at` | TEXT | UTC |
| `error` | TEXT | 失败原因 |
| `pre_cancel_deadline` | TEXT | 5 分钟内可撤销 |

**5 分钟可撤销窗口**：用户对下单决策后悔期。这是服务代办的伦理底线——比现实外卖 APP 取消时限更短。

## 6. Dry-run 报告

用户告知"管家执行 XX 服务"前，agent 必须先生成 dry-run 报告：

```json
{
  "intent": "订明晚 6 点 30 客厅附近 4 人餐厅",
  "options": [
    {
      "id": "opt_1",
      "title": "外婆家（建国路店）",
      "estimated_cost": 220,
      "estimated_wait_minutes": null,
      "rating": 4.6,
      "distance_km": 1.2,
      "available_time": "周二 18:30 仍有 4 人桌",
      "risk": "low"
    },
    {
      "id": "opt_2", ...
    }
  ],
  "warnings": [
    "外婆对花生过敏（来自 household_calendar 提醒）",
    "餐厅距离 2.4km，建议同时呼叫车"
  ],
  "estimated_chain_cost": 220 + 35,
  "guard": {
    "needs_confirm": false,
    "blocking_factors": []
  }
}
```

**PWA 渲染**：选项卡片 + 多选 + "我选好了，确认执行" 按钮 → 触发真实 execute。

## 7. 跨服务编排（Calendar Orchestrator）

典型场景："明晚吃饭" 涉及多个服务：

```
user: "管家订明晚 6 点吃饭，4 个人"
  │
  ▼
intent_router.query("book_dinner", {at, party_size, location})
  ├─ meituan.query() → [options]
  │
  ▼
agent 选 "外婆家餐厅" + 触发：
  ├─ gaode.book_ride(time=17:30, from=家, to=外婆家)
  ├─ family.calendar.add(event="家庭聚餐", at=..., related=外婆家)
  └─ household.notify_all(title="明晚 6 点外婆家，已叫车")
  
每个子任务都是一个独立的 Order，但通过同一个 autonomous_id 串联。
```

**编排原则**：
- 子任务可单独失败，部分成功允许（如打车失败，但餐厅预订已确认）
- 子任务并发执行（节省时间）
- 主任务以"日程编排"为名义创建，不用 user 二次确认每个子任务；**整个编排在执行前提供 dry-run 聚合视图**

## 8. 资金与认证

**管家不碰钱**：
- 用户必须在每个第三方服务自己注册账号
- 管家代用户**发起 API 调用**，但该 API 的鉴权 token 是用户提供的
- 管家从不持有支付凭证

**认证方式**：
- OAuth2 标准流程
- Cookie 复用（需用户首次扫码/确认）
- PKCE 模式（公开客户端如 PWA）

**凭据存储**：
- 加密存到 SQLite（沿用 §RELIABILITY §5.1b 的加密）
- 凭据按服务分表 `service_credentials(service_id, member_id, encrypted_blob)`
- 解密只在 service adapter 进程内使用，不写入日志

## 9. 不做的事（公开禁止列表）

**管家绝不**：
- 替用户签合同、付款超过 ¥X 不告知（X 默认 200）
- 处理处方药订单（只能提醒）
- 替孩子做经济决策
- 自动化订阅/扣款的服务（必须人为确认）
- 任何"理财/投资推荐"
- 法律咨询

这些限制在 persona.py 的系统 prompt 中明确，service_adapter 任何 ingest 也要按这个过滤。

## 10. 服务适配器模板

```python
# myhome_agent/services/adapters/_example_template/adapter.py

from myhome_agent.services.base import (
    ServiceAdapter, Capability, Query, Option,
    OrderRequest, Order
)

class TemplateAdapter(ServiceAdapter):
    @property
    def service_id(self) -> str:
        return "template"

    @property
    def category(self) -> str:
        return "other"

    async def list_capabilities(self) -> list[Capability]:
        return [
            Capability(id="do_something", description="示例能力",
                       allowed_roles={"admin", "adult"})
        ]

    async def query(self, q: Query, ctx: dict) -> list[Option]:
        return [
            Option(id="opt_1", title="示例选项", summary="",
                   estimated_cost=10.0, estimated_time_seconds=60,
                   requires_external_account=False, risk_level="low")
        ]

    async def execute(self, req: OrderRequest) -> Order:
        return Order(id=req.idempotency_key, service_id=self.service_id,
                     status="confirmed", estimated_cost=10.0,
                     external_ref=None,
                     created_at=now_iso(), finished_at=None)

    async def track(self, order_id: str) -> Order:
        return Order(id=order_id, service_id=self.service_id,
                     status="done", estimated_cost=10.0,
                     external_ref="EXT-1",
                     created_at=now_iso(), finished_at=now_iso())
```

**贡献新服务的步骤**：
1. `cp -r adapters/_example_template adapters/<your_service>`
2. 实现 4 个 abstract method
3. 在 `myhome_agent/services/adapters/<your_service>/auth.py` 实现认证
4. 配置进 `config/plugins.yaml` 的 `services.enabled`
5. 测试 `tests/services/test_<your_service>.py` mock 服务方响应
6. docs/services/<your_service>.md 描述风险和限制

## 11. 实现位置

```
myhome_agent/services/
├── base.py
├── registry.py
├── router.py
├── audit.py
├── guard.py
├── orders.py
├── dryrun.py
└── adapters/
    ├── _example_template/
    ├── meituan/
    │   ├── adapter.py
    │   ├── auth.py
    │   └── capabilities.py
    ├── gaode/
    ├── eleme/
    └── ...

tests/services/
├── test_guard.py
├── test_dryrun.py
├── test_orders_state_machine.py
├── test_router.py
└── adapters/
    └── test_meituan.py        # mock 服务方
```

## 12. 阶段性上线（服务代办）

按 §23.5 优先级：
- **E4**：家电食材比价 + 快递追踪（最小骨架）
- **E7**：缴费、打车
- 后续：餐厅预订 → 票务 → 网购
