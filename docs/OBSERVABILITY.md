# 可观测性（Observability）设计

> **同步状态（2026-08-07）**：本文档已纳入整体同步；与当前实现的差异以 [ARCHITECTURE.md](../ARCHITECTURE.md) 状态表和 `tests/` 为准。


> 系统的"神经系统"——出问题时能看清、查得到、报得出去。家庭场景下，没有这套东西出了问题你只能拆代码加 print，效率极低。

## 1. 设计目标

1. 出故障时能 30 秒内定位到模块（采集？存储？agent？渠道？）
2. 设备掉线/异常时，主人能收到通知（而不是从设备没反应才发现）
3. 资源占用可视化（CPU/内存/磁盘/网络）避免 NAS 资源耗尽
4. 不引入重型组件，一切用现有方案

## 2. 三层结构

```
┌─────────────────────────────────────────────┐
│ 通知层：异常事件 → 用户                    │  
│   企微/TG/PWA 弹窗                          │  
├─────────────────────────────────────────────┤
│ 指标层：Metrics + 定时任务                  │
│   Prometheus 兼容格式 + 关键事件表          │
├─────────────────────────────────────────────┤
│ 日志层：结构化日志                          │
│   Python logging + 文件轮换                 │
└─────────────────────────────────────────────┘
```

## 3. 日志层

### 3.1 分级

| 级别 | 用途 | 例子 |
|------|------|------|
| DEBUG | 单设备交互细节 | "收到设备 xxx 响应 ..." |
| INFO | 关键流程节点 | "设备 xxx 上线"、"场景执行：睡觉模式" |
| WARNING | 异常但不致命 | "设备 5 分钟无响应"、"云端 token 即将过期" |
| ERROR | 功能失败 | "DeepSeek API 报 401"、"数据库写入失败" |
| CRITICAL | 系统不可用 | "SQLite 文件损坏"、"配置解析失败" |

### 3.2 结构化字段

所有日志统一为 JSON 格式（用 `python-json-logger`），必备字段：

```
{
  "ts": "2026-07-30T10:30:15",
  "level": "INFO",
  "module": "collectors.registry",
  "event": "device_online",
  "device_id": "xxx",
  "device_name": "客厅空调",
  ...
}
```

### 3.3 输出

- 本地文件：`logs/myhome.log`，按天轮换，保留 30 天
- 控制台 stdout：通过 FastAPI WS 推给 PWA 调试面板
- 关键事件去重：同一事件的重复日志在 5 分钟内合并为一条计数

## 4. 指标层（Metrics）

### 4.1 用文件 + HTTP 暴露，不引入 Prometheus

只暴露一个 `/metrics` HTTP 端点，兼容 Prometheus 抓取格式。后续想接 Prometheus 直接配就行。

```
# HELP myhome_devices_total 当前已发现设备数
myhome_devices_total 23

# HELP myhome_devices_online 当前在线设备数
myhome_devices_online 21

# HELP myhome_collect_latency_seconds 单设备采集耗时（直方图）
myhome_collect_latency_seconds_bucket{le="0.5"} 18
myhome_collect_latency_seconds_bucket{le="1.0"} 22

# HELP myhome_llm_tokens_total LLM 调用 token 计数
myhome_llm_tokens_total{provider="deepseek"} 123456
myhome_llm_tokens_total{provider="local_qwen"} 45678

# HELP myhome_control_actions_total 控制指令计数
myhome_control_actions_total{action="on", result="success"} 45
myhome_control_actions_total{action="on", result="failure"} 2
```

### 4.2 关键指标清单

| 类别 | 指标名 | 用途 |
|------|--------|------|
| 设备 | devices_total / devices_online | 判断设备健康 |
| 采集 | collect_latency_seconds | 采集层健康 |
| 采集 | collect_errors_total{reason} | 区分 DNS/超时/格式错误 |
| LLM | llm_tokens_total{provider, model} | 成本控制 |
| LLM | llm_latency_seconds{provider} | 响应监控 |
| 控制 | control_actions_total{action, result} | 控制成功率 |
| 存储 | db_write_latency_seconds | 存储健康 |
| 系统 | process_cpu_percent / rss_bytes | NAS 资源占用 |

### 4.3 定时健康检查（每分钟）

```
- 拉一次 DeepSeek API 通不通 → 指标 deepseek_available
- 拉数据库通不通 → 指标 db_available
- 本地模型（如有）通不通 → 指标 local_llm_available
```

这些可用性指标接告警规则。

## 5. 告警规则

### 5.1 内置告警（不可关闭）

| 规则 | 级别 | 通知渠道 |
|------|------|---------|
| 数据库写失败 | CRITICAL | 所有已配置渠道 |
| 5 分钟内 devices_online / devices_total < 50% | WARNING | 主渠道 |
| sqlite 文件大小 > 5GB | WARNING | 主渠道 |
| LLM 5 分钟错误率 > 20% | WARNING | 主渠道 |

### 5.2 用户可配置告警

写在 `config/alerts.yaml`：

```yaml
alerts:
  - name: 卧室温度过高
    trigger: metric:temperature > 30 AND room:卧室
    duration: 5m            # 持续 5 分钟才触发
    level: WARNING
    channels: [wechat]
  - name: 客厅设备全部离线
    trigger: device_offline_count(room:客厅) >= 3
    level: CRITICAL
    channels: [wechat, telegram]
```

### 5.3 通知去重

- 同一规则 30 分钟内不重复推送
- 恢复后推送"已恢复"通知
- CRITICAL 不去重，每次都推

## 6. 事件表（业务侧"日志"）

设备/场景/控制 等业务事件不走结构化日志，走 SQLite 的 `events` 表（已存在）。

理由：
- 设备事件是业务数据，要给 agent 用，不是单纯日志
- 有 SQL 索引方便查询
- 日志文件 30 天清理，但事件表长期保留

**职责边界**：
- `logger` → 系统问题（代码、连接、API 错），开发者视角
- `events` 表 → 业务事件（设备动作、场景触发、成员在场），用户/agent 视角

## 7. 追踪（轻量）

不引入 OpenTelemetry，但做 id 串联：

1. 每次用户请求分配 `request_id`（UUID）
2. 该请求的所有日志带上这个 id
3. agent 调用工具、控制设备、写库都标同一个 id
4. PWA 调试面板可以按 id 查"这次请求全链路发生了什么"

## 8. 实施分阶段

| 阶段 | 内容 |
|------|------|
| P1（MVP） | 结构化日志 + `events` 表 + 最基础告警（硬编码） |
| P2 | `/metrics` 端点 + 配置文件驱动的告警 |
| P3 | 追踪 id 串联 + PWA 调试面板 |
| P4 | Prometheus 兼容 + 第三方接入 |

## 9. 实现位置

```
myhome_agent/
├── obs/                    # 新增
│   ├── logger.py           # 结构化日志器工厂
│   ├── metrics.py          # 指标注册表 + /metrics 端点
│   ├── alerts.py           # 告警规则引擎
│   └── trace.py            # request_id 生成和传播
└── ...
```

依赖：仅新增 `python-json-logger`（~3KB），其他零依赖。
