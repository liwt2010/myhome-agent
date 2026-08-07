# 迁移与升级策略

> **同步状态（2026-08-07）**：本文档已纳入整体同步；与当前实现的差异以 [ARCHITECTURE.md](../ARCHITECTURE.md) 状态表和 `tests/` 为准。


> 你家里的一切都可能变：换路由器、换米家账号、换 NAS、加新设备、米家改 API。这套机制保证你**不需要从头再来**。

## 1. 变更场景全覆盖

| 场景 | 触发条件 | 系统怎么应对 |
|------|---------|-------------|
| **单设备替换**（旧灯坏了换新的） | did 变化，name 不变 | did 别名表 + name 匹配自动迁移 |
| **路由器更换**（IP 段变化） | 设备 IP 都变了 | 重新发现机制 |
| **米家账号变更** | token 都失效 | 重新 dump 流程 |
| **NAS 更换**（系统迁移） | 整个部署迁移 | 全量备份+恢复脚本 |
| **米家 API 变化** | 某个接口挂掉 | 通道降级 |
| **代码版本升级** | 软件更新 | schema 自动迁移 |

## 2. 容量估算与性能边界（v2.4 新增）

> 开源用户硬件差异极大，必须先说清楚这个系统能扛多大规模。

**典型家庭场景估算（20 台设备，每台 5 个指标，每分钟 1 次）**：

| 指标 | 数值 |
|------|------|
| readings 日行数 | 20 × 5 × 60 × 24 = **144,000 行/天** |
| readings 月行数（30 天） | **~430 万行** |
| events 日行数 | 100-500 条（门锁、人体、按钮） |
| SQLite 单库大小 | 30 天 ~1.5GB（按行平均 350 字节估算） |
| 30 天后聚合 | readings_hourly 大约 20 × 5 × 24 × 30 = **7.2 万行** |
| 单设备轮询平均延迟（局域网） | 50-200ms |
| 单设备轮询平均延迟（云端） | 200-800ms |
| 100 设备规模 RAM 常驻 | ≤ 500MB（不含 LLM） |

**性能断言（在 N100/树莓派 4 等入门机器上验证）**：

| 查询 | 接受时间 | 实测（草案） |
|------|---------|-------------|
| 单设备 latest_readings | ≤ 50ms | < 10ms（带索引） |
| 24h 时间范围 readings（按设备+指标过滤） | ≤ 200ms | < 100ms |
| 全设备 latest_readings（20 台） | ≤ 300ms | < 200ms |
| events 当日 range 扫描 | ≤ 200ms | < 150ms |

**什么时候超过容量（升级触发）**：

- 设备数 > 50 → 调高 polling 间隔（单设备从 60s 降到 120s）
- 单库 > 5GB → 强制走 readings_hourly 聚合（立即生效，不等 30 天）
- 单库 > 8GB → 主动报警，需要归档/删除历史
- 单库 > 10GB → 拦截写入，进入只读模式（防止 SQLite 卡死）

**升级路径**（如果需要从 SQLite 升级到 DuckDB 或 Timescale）：

- data 导出脚本：`myhome-agent export --target=duckdb`
- ARCHITECTURE.md 不预定义，开放为 optional P5 路线
- 抽象 `Store` 接口，落地实现可替换

## 2b. 字段扩展规范（v2.4 新增）

> §5.0b 已经让 `devices.spec_cache` 为 JSON，但仍要明确：**什么时候开新列 vs 往 JSON 塞**。

**新增字段判断流程**：

```
需要新增字段 X
   │
   ├─ X 是查询密集型（按 X 过滤/聚合/排序）
   │   → 加成正式列，建索引
   │
   ├─ X 是展示/导出用
   │   → 放进 devices.spec_cache（JSON）
   │
   ├─ X 是行为开关（决定分支逻辑）
   │   → 加成正式列（代码分支条件需可索引）
   │
   └─ X 是元数据（不影响主流程）
       → 进 JSON
```

**经验性归类**：

| 字段类型 | 进列 | 进 JSON |
|---------|-----|--------|
| 主机身份（did / mac） | ✅ | |
| 行为开关（local_controllable / transport） | ✅ | |
| 时间戳（first_seen / last_seen） | ✅ | |
| 设备可枚举项（type / brand） | ✅ | |
| 用户偏好（room / user_label / display_name） | ✅ | |
| 米家云端原始字段 | | ✅ (spec_cache) |
| 临时调试信息 | | ✅（不上线） |

**索引策略**：所有进列的字段必须被某条生产查询使用，否则不加索引（写入放大）。

## 3. 设备身份的三重匹配

传统方式只认 `did`，换设备就丢历史。我们用三重匹配，按优先级从高到低：

```
匹配优先级：
1. 永久身份（user_label，用户起的名字）  → 用户手动起的别名，永远绑定
2. 物理身份（mac）                       → 换 did 但 mac 不变时识别  
3. 米家身份（did）                       → 最后一道
```

### 数据模型变化

在 `devices` 表加字段：

```sql
ALTER TABLE devices ADD COLUMN user_label TEXT;     -- 用户别名
ALTER TABLE devices ADD COLUMN mac TEXT;            -- 物理地址
ALTER TABLE devices ADD COLUMN replaced_by TEXT;    -- 换设备时指向新 did
CREATE INDEX idx_devices_mac ON devices(mac);
```

### 设备替换流程

1. 用户新灯绑定米家 → 出现在云端拉清单里，did=新值
2. sync 时发现：mac 已存在，但 did 不同 → 触发"设备替换"流程
3. **自动**：把旧设备的 user_label、房间、配置复制到新设备，旧设备标记 `replaced_by=新did`
4. **历史关联**：所有 readings/events 旧 did 自动改写为新 did（或加 view 联合查询）
5. **通知用户**："检测到 [客厅吸顶灯] 已更换，已自动接管"
6. 用户可在 PWA 手动确认/撤销

## 3. IP/路由器更换

局域网 IP 变了不影响 token，但可能影响 miio 本地连接。

### 拨号机制

```python
# 原有 IP 不通时：
1. 先用 token 做局域网 miio 广播发现（UDP 54321 broadcast）
2. 收到响应后从响应包取出新 IP
3. 更新 devices 表的 local_ip
4. 后续用新 IP
```

实现：每台设备的 IP 失效后自动跑 `miio discover` 试图找回。

### 触发时机

- 单设备 ping 连续 3 次失败 → 触发该设备拨号
- 全局：手动从 PWA 触发"重新发现所有设备"

## 4. 账号/Token 变更

米家改密码或换账号 → 所有 token 失效。

### 流程

```
1. 用户在 .env 改 MI_USERNAME/MI_PASSWORD
2. 启动时检测到旧 token 全部失效（云端 login 返回 401）
3. 提示用户执行：miio cloud <user> <pass> --dump > tokens.json
4. 导入新 token，但 did 不变 → 其他数据完全不受影响
5. 通知用户哪些设备换 token 成功、哪些需要重新绑定
```

### 关键设计：业务不依赖 token

token 只用来"对话"，业务数据（readings、events、routines）都用 did 和 mac 关联。token 换新不会让历史数据失效。

## 5. 整机迁移（换 NAS）

### 备份脚本（自带）

```bash
python -m myhome_agent.backup export --output myhome-backup-20260730.tar.gz
```

打包：
- `data/myhome.db`（SQLite 整库）
- `config/` 所有 yaml
- `.env`（**用户可以选择是否包含**，默认不包含，避免泄漏）
- `logs/` 最近 7 天

### 恢复脚本

```bash
python -m myhome_agent.backup restore myhome-backup-20260730.tar.gz
```

自动：
- 解压到对应目录
- 校验 db 完整性
- 跑 schema 迁移
- 提示需要重新填的 `.env` 字段

### 局域网相关问题

新 NAS 的 IP 可能和旧的不同，但**不影响**：
- agent 不持有自己的"服务器身份"
- 设备 token 跟设备绑定，跟 agent 在哪没关系
- 配置文件里的米家 username 跟设备无关

## 6. 米家 API 变化的应对

米家会悄悄改 API。我们的防线：

### 6.1 通道降级

| 主通道挂了 | 降级到 |
|-----------|--------|
| 本地 miio 不通 | 用云端 API 控制（覆盖度低，但可用） |
| 云端 sync 接口挂 | 用老的清单数据 + miio 拨号发现新设备 |
| 某个 LLM Provider 挂 | 切换到备用 provider |

### 6.2 适配层隔离

所有米家接口调用集中在 `collectors/`。米家 API 变了只需改这里，上层逻辑不动。

### 6.3 兼容性测试

docs/TESTING.md 会包含一套"米家 API 烟雾测试"，每周跑一次：

- 登录是否成功
- 设备清单字段是否完整
- 单设备状态查询是否正常

测试失败自动告警。

## 7. 代码/schema 版本升级

### 7.1 数据库 schema 版本

`schema_meta` 表存当前版本：

```sql
CREATE TABLE schema_meta (
  key TEXT PRIMARY KEY,
  value TEXT
);
INSERT INTO schema_meta VALUES ('version', '0.5.0');  -- v2.11 与 SCHEMA.md L291 对齐
```

### 7.2 自动迁移

```
myhome_agent/migrations/
├── 001_init.sql
├── 002_add_user_label_mac.sql
└── 003_xxx.sql
```

启动时：
1. 读 `schema_meta.version`
2. 顺序执行未跑过的迁移脚本
3. 更新版本号
4. 失败时回滚事务并退出

### 7.3 代码版本与 schema 的兼容

- **代码更新向后兼容一个 schema 版本**：上个版本的代码能读这个版本的库
- **跨大版本时**：自动迁移脚本必须能跑通，否则启动报错并提示手动处理

## 8. 不可逆操作的二次确认

以下操作要求用户显式确认（不是 LLM 自动触发）：

- 删除设备（包括历史数据）
- 清空记忆库
- 删除场景
- 重置数据库
- 修改米家账号

PWA 提供"危险操作"面板，需要输入 "确认" 二次验证。

## 9. 文档化变更日志

每次架构变更（不只是代码）需要追加到 `ARCHITECTURE.md` 顶部的版本注释：

```
v2.1 (2026-07-30): DeepSeek 切换、新增概念入门 §0
v2.0 (2026-07-29): 与用户对齐 11 项决策
v1.0 (2026-07-28): 初版架构
```

并要求同步更新对应的 docs/XXX.md。

## 10. 灾难恢复清单

| 目标 | 接受程度 |
|------|---------|
| RTO (恢复时间) | < 30 分钟（含备份下载恢复） |
| RPO (数据丢失) | < 24 小时（每日备份） |
| 关键功能（告警/查询）恢复 | < 5 分钟 |

## 12. Schema 详细字段表（v2.4 索引）

> §ARCHITECTURE 5.0b 是 ER 概览 + 主要字段。完整字段定义拆到独立文件避免主文档失焦：
> [docs/SCHEMA.md](SCHEMA.md)

## 13. 实现位置

```
myhome_agent/
├── backup/                # 新增
│   ├── exporter.py        # 备份打包
│   ├── restorer.py        # 恢复解包
│   └── checker.py         # 恢复前一致性检查
├── migrations/            # 新增
│   ├── runner.py          # 迁移执行器
│   └── NNN_*.sql          # 迁移脚本
├── collectors/
│   └── discovery.py       # 现有 + 增强：设备替换检测、IP 拨号
└── ...
```
