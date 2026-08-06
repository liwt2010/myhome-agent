# 家庭智能体（MyHome Agent）架构设计 v2.3

> **v2.3 修订（第 23 次深度实施，硬件联调完整化）**：
> - **WebAuthn 完整 UI**：`web/index.html` 真实 `navigator.credentials.create` 流程（ES256 + RS256）+ challenge + JWT 颁发
> - **FastAPI WebAuthn 端点**：`auth/webauthn_endpoints.py` 200+ 行 / 6 端点（register/start|finish + login/start|finish + credentials GET/DELETE）
> - **Matter 编译环境文档**：`docs/MATTER_BUILD.md` Linux/macOS/WSL2/Docker + 6 厂商 11 设备清单（¥600 最低）
> - **Zigbee bellows 实测脚本**：`scripts/test_zigbee.py` bellows 真接 + 11 cluster 映射 + mock 模式
> - **硬件联调完整脚本**：`scripts/test_hardware.py` 6-8 周 5 阶段（摄像头/TG/PWA/性能/集成）
> - **代码模块新增**：`auth/webauthn_endpoints.py`（200+ 行） + `scripts/test_zigbee.py` + `scripts/test_hardware.py` + `docs/MATTER_BUILD.md`
> - **架构总章节**：~28500 行（v2.2 27500 + v2.3 新增 ~1000）；28 专题文档；74 个代码模块

# 家庭智能体（MyHome Agent）架构设计 v2.2

> **v2.2 修订（第 30 次深度实施，Matter 真实 SDK 集成）**：
> - **chip-tool Python 封装**（`collectors/chip_tool_wrapper.py` 200+ 行）：ChipToolAdapter 类封装 chip-tool 命令行（onoff / level / color_temp / lock / unlock / thermostat_setpoint / read_attribute / commission / list_nodes）+ ChipToolResult 结构 + is_chip_tool_available() 健康检查。chip-tool 缺失时优雅降级。
> - **Matter Adapter v2.2 升级**（`collectors/matter_adapter.py`）：3 路选择——chip-tool subprocess（v2.2 新）→ python-matter SDK（v2.1.1 备选）→ 纯 stub（v2.1.0 默认）。connect() 自动检测 chip-tool 可用性 + 自动降级。EcosystemAdapter 接口不变。
> - **真实集成门槛**：chip-tool 需源码编译 connectedhomeip（30-60 分钟），PyPI 无马。当前模式下 graceful fallback——stub 代码做 capability 映射 + 执行返回占位。待用户编译 chip-tool 后自动探测。
> - **架构总章节**：~22200 行（v0.8 22000 + v2.2 新增 ~200）；21 个专题文档。
> - **代码模块新增**：`collectors/chip_tool_wrapper.py`（~150 行）+ `matter_adapter.py` 升级（+30 行）。


> **v0.8 修订（第 29 次深度实施，PWA 完整重写）**：
> - **§30 PWA 完整重写**（ 1106 行）：4 大区域（家 / 控制 / 通知 / 我的）+ 4 标签底部导航 + 4 角色切换（admin / adult / elder / child）+ 5 高频场景优化（早问候 / 摔倒告警 / 一键场景 / 误报反馈 / 用药提醒）+ 老人模式（4 档字体 + 高对比度 + 慢节奏）+ 设备卡片网格 + 房间筛选 + 场景一键执行 + 规则管理 + 通知中心（4 选项反馈）+ 隐私 toggle（视觉/LLM/远程）+ WebAuthn/TOTP 设置入口 + 数据导出/被遗忘权 + 治理仪表盘入口 + FAB 快速操作 + WebSocket 实时告警 + Toast 提示 + 模态对话框。
> - **CSS 变量化**：dark theme + elder-mode 高对比度 + font-lg/xl/xxl 4 档切换 + 圆角 / 阴影 / 动画统一管理。
> - **架构总章节**：~22000 行（v3.0.1 21500 + v0.8 新增 ~500）；21 个专题文档（+ SECURITY.md）。
> - **代码模块新增**： PWA（1 个文件 ~1100 行，4 区 + 5 场景 + 4 角色 + 老人模式 + WebAuthn UI 占位）。



> **v4.3 修订（第 27 次深度实施，真实公开数据 FL）**：
> - 4 sklearn 工业基准数据集（iris / wine / breast_cancer / digits）+ 10 家庭 Non-IID + 40 轮 FedAvg
> - 4/4 通过：FL 全部 ≥ 中心化 95%（差距 < 5%）
> - 架构总章节：**~21000 行 / 20 文档**

> **v4.1 修订（第 25 次深度实施，FL 真实训练 + A2A 协议真实实现）**：
> - FL 真实训练 + A2A 协议（HTTP + WebSocket）
> - 架构总章节：**~20000 行 / 20 文档**

> **v4.0 实施修订（第 24 次深度实施，长期愿景代码落地）**：
> - §69 Marketplace + §70 联邦学习
> - 架构总章节：**~19500 行 / 20 文档**

> **v3.1 + v4.0 规划修订（第 23 次深度规划）**：
> - §69 Marketplace + §70 联邦学习架构
> - 架构总章节：**~18500 行 / 20 文档**

> **v3.0 修订（第 21 次深度实施，AI 增强 5 方向）**：
> - 14.1 多 LLM 智能路由 + 14.2 VLM 多模态视觉 + 14.3 长期记忆 + 自学习 + 14.4 主动服务 + 14.5 智能家庭决策
> - 架构总章节：**~17500 行 / 20 文档**

> **v2.1.1 修订（第 20 次深度实施，真实 SDK 集成）**：
> - Matter 真实 SDK 集成（chip-tool 路线）
> - OpenThread 真实 SDK 集成（ot-ctl 路线）
> - ZHA 真实 SDK 集成（zigpy 2.1 + bellows 1.0 已装）
> - docs/REAL_PROTOCOL_TESTING.md
> - 架构总章节：**~16000 行 / 20 文档**

> **v2.1 修订（第 19 次深度实施，主流智能家居协议）**：
> - §65 Matter v1.3 + §66 Thread Border Router + §67 Zigbee 桥接
> - §68 协议分层章节
> - 架构总章节：**~15500 行 / 19 文档**

> **v2.0 修订（第 18 次深度实施，跨生态 + 真实联调 + ISO/SOC2）**：
> - §64 EcosystemAdapter 抽象 + capability 映射表
> - §65 Tuya OpenAPI v2 + §66 Hue Bridge v2 + §67 HomeKit bridge（HAP-python）
> - docs/REAL_WORLD_TESTING.md + docs/ISO27001.md + docs/SOC2.md
> - 架构总章节：**~14000 行 / 19 文档 / 4 模块**

> **v1.0.1 修订（第 17 次深度实施，商业化前置完整化）**：
> - AWS KMS / GCP KMS 真实接入 + KMS 工厂升级
> - DPIA 自动化（5 维评分 + 数据流图 + 报告归档）
> - DPO 任命 + 仪表盘 + 应急响应
> - 第三方审计清单（12 项必查）
> - 真实硬件联调清单（3 品牌 + 7 端点）
> - 架构总章节：**~12500 行 / 16 文档 / 4 模块**

> **v1.0 修订（第 16 次深度实施，商业化前置）**：
> - **§63 公共规则市场 web 平台** + **DEPLOY_VERIFICATION.md v0.9 升级** + **DPO 设立 DPA.md** + **DPIA v1.0 升级** + **KMS/HSM** + **KMS 集成（vision/crypto.py 自动用 KMS 派生）**。
> - 架构总章节：**63 节 / ~11500 行**；14 个专题文档。

> **v0.9 修订（第 15 次深度实施，2FA + 跨家庭 + WebAuthn）**：
> - **2FA 装饰器接入 gateway**：8 个新端点 + PyJWT session token + `require_2fa_dep` FastAPI 依赖工厂。
> - **v0.9 跨家庭策略共享**（§62）：JSON 模板导出 + `/api/households/{id}/export` + `/api/households/import`。
> - **WebAuthn / FIDO2 模块** `WebAuthnManager`（py_webauthn 3.0 + sign_count 防重放 + JWT）。
> - **FastAPI 启动初始化**：v0.8.1 + v0.9 表自动建。
> - **架构总章节**：~10500 行；13 个专题文档 + web 资源。

> **v0.8 修订（第 14 次深度实施，PWA 完整化 + 通知深化 + 2FA）**：
> - **§59 §30 PWA 完整形态**：manifest.json + Service Worker + Web Push VAPID + 加桌面 + 离线缓存 + WS 降级长轮询 + iOS 7 大对策。
> - **§60 §52 通知深化**：i18n 翻译 + 富媒体（snapshot/video）+ 离线队列（5 次重试）。
> - **§61 §50 2FA 不变量**：强制场景表 + 触发流程 + 5 次失败锁定。
> - **2FA 模块** TwoFactorManager（TOTP + bcrypt 备用码 + Fernet + 装饰器）。
> - **web/manifest.json + sw.js** 完整。
> - **架构总章节**：~9900 行；12 个专题文档 + web 资源。

> **v0.7 修订（第 13 次深度实施，公共规则市场 + DPIA + 视觉 16 条 + 章节细化）**：
> - **§55 公共规则市场**（§50 升级路径 3 兑现）：5 项治理不变量 + `rule_templates` 表 + 导入流程 + 评分机制 + 5 个 v0.7 内置模板 + v1.0 完整市场计划。
> - **docs/DPIA.md GDPR 完整评估**：CNIL/Article 35 模板 + 4 个高风险数据流 + GDPR 7 项原则 + 7 项数据主体权利 + 残留风险与接受条件 + 签字页 + 交叉引用。
> - **视觉规则 16 条**（docs/RULES.md §3b）：跌倒 3 / 痴呆 3 / 陌生人 2 / 火焰 2 / 慢病 1 / 失禁 1 / 婴儿 1 / 包裹 1 / 宠物 1 / SOS 联动 1。
> - **§34 远程访问完整细化**（§56）：3 层访问控制 + temporary_grants + 5s/30s/60s 撤销窗 + 子女代理 + 维修工临时。
> - **§39 per-member 语言 4 层 locale**（§57）：系统/家庭/成员/场景 4 层 + 6 种 locale + 翻译缓存 + ICU 消息格式。
> - **§47 policy 表完整字段 + 9 角色矩阵**（§58）：完整 schema + 9 角色 + 13 capability × 9 角色决策表 + 字段级权限 + deny-by-default。
> - **架构总章节**：~9200 行（v0.6 8400 + v0.7 新增 ~800）；12 个专题文档（新增 DPIA.md）。

> **v0.6 修订（第 12 次深度实施，§38 全场景 + 治理 UI + 联调）**：
> - **§38 全部展开 19 场景**（§38.13-§38.18）：8 主（老人主动询问 / 被动接收 / 说不舒服 / 想控制 / 找东西 / 找家人 / 看电视 / 紧急求助）+ 5 被（跌倒 / 痴呆走失 / 慢病异常 / 失禁久坐 / SOS 按钮）+ 3 协同（照护代理共识 / 保姆上下班 / 多老人角色区分）+ 3 医疗（续方 / 急救 / 体检解读）。每场景给：数据源 + 实施 + 治理等级 + §53 规则 + §54 视觉引用。
> - **§38.17 19 场景汇总表**：severity / 等级 / 治理 / 规则 / 视觉 5 维度横表。
> - **§38.18 实施时间表**：v0.4 8 项 + v0.5 2 项 + v0.6 19 项 → 累计 23 项。
> - **PWA 治理仪表盘 UI**（web/index.html）：新增"治理"标签 + 5 个区（资源配额进度条 / 自治等级分布柱状图 / 4 维风险评分测试下拉 / 决策历史 timeline / 度假模式开关）+ 完整 CSS（quota-bar 进度 / level-bar 等级色 / decision-item 边框）。switchTab 扩展支持 governance。
> - **DEPLOY_VERIFICATION.md**：300+ 行 10 节联调清单（准备 → 安装 → 初始化 → CLI 验证 → 服务验证 → PWA 验证 → TG 验证 → 视觉验证 → 失败排查 → 完整检查表）。
> - **架构总章节**：~8400 行（v0.5 7800 + v0.6 新增 ~600）；11 个专题文档（新增 DEPLOY_VERIFICATION.md）。

> **v0.5 修订（第 11 次深度实施，治理 + 渠道 + 视觉真实）**：
> - **5.1 真实 YOLO 跑通**：ultralytics + opencv-python 装好（pip 走 trusted-host 绕过 SSL），YOLOv8n 6.2MB 模型首次自动下载，`PersonDetector` + `MotionDetector` CPU 推理实测。
> - **5.2 Telegram bot 双工**：`myhome_agent/channels/telegram.py` `TelegramBot`（python-telegram-bot 22.8 接入，polling 后台线程）+ 7 个命令（/start /bind /chat /status /rules /devices /alerts）+ per-member chat_id 绑定（存 `members.notification_prefs.telegram_chat_id`）+ Fernet 加解密工具。
> - **5.3 动态配额**：`myhome_agent/governance/quotas.py` `DynamicQuotas` + `QuotaManager`（按时段 day/night/vacation + per-household 隔离）。LLM 兜底 10→5→15/天，LLM-Vision 20→5→30/天。`check_and_increment` 原子操作。`/api/governance/quotas` 端点。
> - **5.4 TG 端到端 + CHANNELS.md**：300+ 行完整指南（创建 bot → 拿 token → .env → 启动 → /bind → 远程控制 + 二次确认 + 故障排查）。
> - **5.5 TG 群组支持**：v0.5.2 群组中 @bot + reply_to_message 识别，忽略不相关消息。
> - **5.6 自治决策**：`myhome_agent/governance/autonomy.py` `AutonomyEngine` + 4 维风险评分（severity × irreversibility × time × member_role）+ L0-L4 决策树 + 强制 L1 不变式（safety+irreversible / child）+ `governance_decisions` 表审计 + 用户可覆盖。
> - **5.7 GOVERNANCE.md + 决策端点**：300+ 行完整治理文档（4 维评分细则 + 等级决策表 + 资源配额 + 审计 + 与 §53/§5.3/§52/§50 对接 + 升级路径 + 失败模式 + 不变量）+ `/api/governance/decisions` + `/api/governance/autonomy/test`。
> - **CLI 新增**：`myhome-agent channels {start-telegram|vacation-on|vacation-off}`。
> - **依赖**：`python-telegram-bot>=22.0` 加入 pyproject。
> - **架构总章节**：~7800 行（v0.4 7400 + v0.5 新增 ~400）；10 个专题文档（含 CHANNELS.md + GOVERNANCE.md）。

> **v0.4 修订（第 10 次深度收尾）**：
> - **§5.0b ER 总图同步**：补 6 张 v0.2/v0.3 新表（rules / rule_state / rule_audit_log / rule_feedback / cameras / vision_events），总表数 29。
> - **§36.2 搬家流程补规则迁移**：第 11 步 rules 跟随 household（scope=household）/ 跟 member（scope=member）；第 12 步 cameras 跟 household + 视觉事件 30 天后清理（隐私红线）。
> - **§1b SLO 加 v2.19+ 条目**：8 条新指标（规则引擎扫描/误报/漏报/fire延迟/兜底 + 视觉管线推理/并发/凭证解密）。
> - **§50 治理框架章节兑现 v2.19 占位**：4 要素（规则管理 / 能力注册 / 资源配额 / 审计）+ rules.scope 新增（household/member）+ capabilities 3 档 + LLM 兜底 10/天/家 + 微信/TG 解封条件 + GDPR 5 条对照 + 升级路径（v0.4→v0.5→v1.0）。
> - **§38.6 老人可用性 6 项细化**：每项拆为子节（§38.6.1-§38.6.7），PWA 实现 + 代码钩子 + 视觉事件触发 + 视觉×老人联动（痴呆老人独自出门规则示例）。
> - **docs/DEPLOYMENT.md 新建**：4 档硬件 / 系统要求 / 一键安装 / .env 配置 / 初始化 / 摄像头接入 / 故障排查 4 类 / 备份恢复 / 升级路径 / 安全清单 / 监控指标。
> - **架构总章节**：~7400 行（v0.3 6900 + v0.4 新增 ~500）；9 个专题文档（含 DEPLOYMENT.md）；29 张主表 + 6 张设施表。

> **v0.3 修订（第 9 次深度实施，视觉管线从 mock 到真实）**：
> - **3.1.A YOLO-nano 真实推理**：`vision/detectors.py` 新增 `PersonDetector`（YOLOv8n 真模型，CPU 推理支持人形/动物/车辆检测）+ `PoseDetector`（YOLOv8n-pose + 17 关键点 + 纵横比+躯干倾角双重跌倒判定）+ `FireDetector`（HSV 阈值 + 可选 YOLO-cls）+ `MotionDetector`（MOG2 背景减除）。
> - **3.2.A RTSP 拉流**：`vision/sources.py` 新增 `RTSPCameraSource`（OpenCV FFMPEG 后端 + 5s 超时 + 断流重连）+ `FileCameraSource`（mp4 视频回放，loop 模式）。
> - **3.3.A 凭证加密**：`vision/crypto.py` Fernet 对称加密 + `MYHOME_FERNET_KEY` 自动生成到 .env + 双写兼容（v0.3 过渡期）+ `migrate_existing_rtsp_urls` 工具。
> - **3.4.A 烟雾测试**：`tests/test_vision_pipeline.py` 11 个 pytest（VisionStore CRUD / MockSource / MockDetector / Pipeline 端到端 / 加解密 roundtrip）。
> - **3.3.B 多摄像头并发**：`vision/scheduler.py` `MultiCameraScheduler`（ThreadPoolExecutor + 性能统计 + CPU 过载自动降帧 + build_scheduler_from_store 一键加载）。
> - **3.4.B 健康监控**：`vision/health.py` `CameraHealthMonitor`（60s 巡检 + 离线/恢复告警 + 写 events 表）。
> - **3.5.A LLM 兜底推理**：`rules/fallback.py` `FallbackReasoner`（触发判定：final_conf<0.3 + ≥2 条低可信 + 信号矛盾；限流 10 次/天/家；§36 强制隔离；DeepSeek 不可用时静默降级）。
> - **3.5.B 引擎集成**：RuleScanner 接入 fallback，扫描时累计低可信数，触发后调 LLM 拿结构化建议（不直接执行动作）。
> - **3.5.C API 端点**：`/api/rules/fallback` POST（手动触发）+ `/api/rules/fallback/stats` GET（今日计数 + LLM 状态）+ `/api/rules/{id}/debug` GET（调试面板数据：fires + confidence + fp/tp 统计）。
> - **3.5.D PWA 反馈 UI**：新增"规则"标签页 + 规则列表（按 severity 颜色编码 + 状态徽章 + TP/FP 计数）+ 规则详情弹窗（最近触发 + 4 统计卡片 + 禁用按钮）+ Fire 反馈横幅（4 选项按钮：真异常/误报/忽略/禁用）。`switchTab` 扩展支持 rules 切换。`?demo=fire` URL 触发模拟 fire banner。
> - **依赖升级**：`ultralytics`/`opencv-python`/`numpy`/`cryptography`/`Pillow` 加入 pyproject。
> - **架构总章节**：~6900 行（v0.2 6500 + v0.3 新增 300+ 视觉相关 + §54 修订）；代码模块 + `vision/` 5 个文件 + `tests/` + PWA UI 完整。

> **v0.2 修订（第 8 次深度实施）**：新增 §54 视觉管线（4 层架构 + cameras/vision_events 2 张表 + 3 条视觉示例规则 + RTSP/ONVIF + LLM-Vision 兜底 + 隐私 3 层防护）。§53 置信度模块完整化（4 因子算法 + 误报闭环 + 自动暂停 + GDPR author 撤销级联）。新增模块 `myhome_agent/vision/`（CameraSource / LocalDetector / LLMVisionAnalyzer / VisionPipeline）+ `myhome_agent/rules/confidence.py` + `myhome_agent/rules/feedback.py`。Gateway 加 7 个 v0.2 API（规则列表 / 详情 / 触发历史 / 反馈 / 自动学习 + 摄像头 / 视觉事件）。代码层 v0.2 完成度 95%（PWA 反馈 UI 留 v0.3）。

> **v2.19 修订（第 7 次深度优化）**：新增 §53 跨信号推理规则引擎（4 张表 + DSL 规范 + 调度模型 + 置信度校准 + 误报闭环 + 治理）。捎带决策：§10 微信渠道决策 B（不做，留 v3）、§6.4 硬件预算决策 C（分层 L1-L4）、§8.5 v0.1 实施起点决策 C（E2 LLM 网关为第一个里程碑）。配套文档：docs/RULES.md（1200+ 行 DSL 完整手册 + 16 条系统预设 + LLM 评审流程）、docs/SCHEMA.md §18-§21 规则引擎 4 张表 + §22 ER + §23 迁移脚本。下一轮派 2 个独立子代理做交叉引用一致性审计 + 架构矛盾审计。

> **产品定位（v2.7 用户拍板）**：**家庭私人管家**——家里的事情它都清楚，并且能智能化处理日常琐事。
>
> 它不仅懂米家设备，更懂这家人本身；它不仅回答问题，更动手办成事；它像家人一样长期存在而非一次性工具。
>
> **v2 修订**：与用户确认后的最终架构，取代 v1 的默认假设。
> **v2.1 修订**：云端 LLM 从 Claude 切换为 DeepSeek（成本更优，国内访问稳定）；新增 §0 概念入门。
> **v2.2 修订**：修正 deepseek-reasoner 工具调用事实错误；补全调度层、身份会话、数据模型概览、上下文预算；高危控制按渠道分级；本地 LLM 后移到阶段 2。
> **v2.3 修订**：硬件型号无关化——设备能力从米家云端 spec 自动发现，业务语义走 PWA 配置入口；项目面向开源，代码零硬件预设。
> **v2.4 修订**：全维度审视补充——非功能需求、控制反馈环、上云数据契约、SQLite 加密、region 支持、Plugin 强制 http_client、容量估算、字段扩展规范。
> **v2.5 修订**：PWA 信息架构分层；时间/时区契约；部署以 Docker Compose 为主，systemd 为可选项。
> **v2.6 修订**：代入最终使用场景，补足用户视角缺口——首装向导、RBAC、场景原子性、降级可视化、数据缺口补录、自主可审计性、成员绑定流程。
> **v2.7 修订**：产品定位升级为"家庭私人管家"——新增家务领域、服务代办、自主等级、管家意识/人格四层架构；与原有设备管家能力共生。
> **v2.8 修订**：补齐部署前必拍板 5 项（硬件自适应、per-member 账号、完整 PWA、人设默认、MVP 能力矩阵），新增 §33 文档导读路径（C）。
> **v2.9 修订**：写入 B 类 7 项设计空白——远程求助完整场景、节假日自动识别、多家庭隔离、三源验证防幻觉、多代同堂老年守护、per-member 语言、断电恢复。
> **v2.10 修订（架构稳定化版本）**：完成独立审视 + 一致性审计后的阻塞修复 + 缺失章节——新增 §30.0 TLS 方案 / §5.3b 远程白名单 / §5.8b PWA 必登录 / §42 规则模式 / §43 隐私合规 / §44 备份灾备 / §45 版本升级 / §46 设备模拟器 / §47 单一 policy 表 / §48 调度 catch_up；改写 §37 多源自适应 + §5.7 影像通道 + §5.11 image 类目。**架构推至"按这版直接动手实施"状态**。
> **v2.11 修订（精细化）**：补 v2.10 子代理 A 留下的 20 中 + 20 低 严重度问题；统一 §47 policy 表 / §36.6 / §48.4 / §43.3 / §45.3 一致性；新增强制 §11 矩阵补 §42 兜底条目。详见 §41 索引。
> **v2.12 修订（权威化）**：以 §36.6 为 household_id 单一权威，反查 §5.0b / §36.1 / §29 / §31.2 / §35.1 五处对齐（events / chat_history / readings 改为派生；holidays / mi_accounts / device_capabilities 改为派生；elder_care / household_health / household_finance 加入派生白名单）；补 §43.3 step 10 字段对齐；§47.6 决策流程加 household_id 优先级；§36.2 搬家补 primary 切换流程；§40.1 限流拆分并发上限 vs 触发上限；§47.3 seed YAML 键名 + 双源声明。
> **v2.13 修订（老人守护扩展）**：补 §38.6 老人作为使用者 / §38.7 跌倒检测机制 / §38.8 痴呆与认知衰退 / §38.9 远程子女视图 / §38.10 多老人+保姆 / §38.11 医疗接口；§7 风险表新增 4 条 🔴（老年可用性 / 跌倒误报 / 痴呆场景 / 远程隐私）。共 24 个细分场景。
> **v2.13.1 修订（UAMS 整合决策）**：用户拍板**暂不整合 UAMS**（v0.7 Beta + 单 SQLite 后端无向量搜索 + 治理模型差异）；新增 §49 明确边界（myhome-agent 数据 vs UAMS 记忆的分工）+ v0.5+ 重新评估的触发条件 + 永远不切给 UAMS 的表清单。
> **v2.14 修订（成员区分度设计）**：新增 §51 系统化梳理区分度 3 层次（L1 角色 / L2 身份 / L3 声纹默认禁用）；§51.2 任务区分度对照表（10 类任务 × 3 层次映射）；§51.3 物理设备共用方案（A+C 默认组合：自动切换 + 公共模式）；§51.4 声纹识别决策（默认禁用 + 5 硬约束）；§51.5 同位置多人在场推断（3 信号叠加）；§51.6 访客账号生命周期（4 类型 + 自动清理 + 跨家庭清单）。
> **v2.15 修订（10 维度全检 + 一致性）**：补错误处理三态（§5.6b timeout + 撤销窗 ≥30s）/ 时序一致性（§40.1 NTP 校验 + §7b civil_from_utc）/ 资源降级（§16 磁盘/WAL/readings 触发）/ LLM 配额两档（§28.3 daily+monthly）/ 升级 rollback docker 协调（§45.3 6a-6e）/ 二进制 schema 兼容矩阵（§45.1 5 种组合）/ trace_id 串联 LLM 调用栈（§18）/ per-region 米家账号路由（§29.1）/ 长断期 catch_up 禁用（§30.4）/ 服务凭据沙箱（§23.3.5）；一致性修复跨文档引用无前缀（14 处加 `§<FILE>`）+ §44.3 L0 默认异地副本 + §5.0a 加过期临时数据清理任务 + §36.2 搬家后 persona 跟随 member；§7 风险表新增 13 条 🟡 中。
> **v2.16 修订（5 子代理审视整合）**：第 5 次审视（3 路独立 + 2 路由修复）发现 22 条新问题。修了 8 处文档内部矛盾（events/alerts 365 天 / chat_fts 90 天 / chat_history/memories schema / memories.archived/voice_template 等）+ 4 条 🔴 严重（capabilities 改名 + domain 列 / E0 直接建 policies 表 / 备份含 config / scenes 表定义）+ 9 条 🟡 中（spec_cache 与 capabilities 同步 / 设备并发控制 + /undo 栈 / ws/state 广播 + 新鲜度 UI / per-fact forget_fact API / 配置四层优先级 + seed 语义 / §52 通知路由整片空白 / §39.6 locale 4 层分层）。
> **v2.17 修订（v2.16 留下的"半做"修补）**：修了 14 处 + 1 处 v2.16 内部遗漏（household 第 5 层配置）。中严重度 6：§38.7 标题"三级"改四级 + §38.12 急救流程新增（消死循环引用）/ §38.2 + §23.6 + §52.6 "打 120" 责任边界冲突统一（safe-action 白名单 + 120 仅人工触发）/ §43.1 表格补 4 张表（routines / presence / scene_executions / services_orders）+ §5.0a 加 services_orders/presence 滑动聚合任务 / §36.6 CI 断言纳入 scenes 表 / §15 场景 capability 依赖检查（dry_run 阶段）/ §43.3b persona_learn 级联语义修正（kind 是信号类型不是事实，改为关联 memories.archived）。低严重度 8：accessibility 5 项新字段（color_safe / reduce_motion / touch_target_min_size / hearing_impairment / screen_reader_friendly / high_contrast_aaa）/ spec_version 改 spec_hash + 固件升级事件触发入口 / §25.3 persona_learn 衰减机制接入 memories.importance / §22.1 health 启用后 health_anomaly 事件约定 + 脱敏规则 / §36.2 搬家 scenes/services_orders 跟随 household 而非 member / §52.6 ladder attempt 4 voice phone 仅给 care_taker 不打 120 / §31.2 capabilities 表名三处统一（§5.0b / §36.6 / §47.5）。
> **v2.18 修订（第 6 次深度审视）**：第 6 次子代理审视发现 20 条新问题。中严重度 10：§16 状态灯"降级检测自身失效"兜底（health 协程 hang 死显示第 3 类状态）/ §52.1 infra_health 继承 safety 不可静音（度假 DND 期间管家病了仍能穿透）/ §38.2 SOS 直通例外（跳过 ladder attempt 1-3）/ §52.9 阶梯升级终止态（全 attempt 失败 → alerts.escalation_exhausted=1 + 强制红）/ §52.2 vacation_until 长期 DND + 陈旧检测 / §44.4 恢复后 §43 级联重放（GDPR 兼容 + 不复活已删数据）/ §48.2 catch_up max_backlog 硬规则 + §44 恢复后对账 / capabilities irreversibility_tier（reversible/costly/irreversible 三档；irreversible 强制 L1 + confirm）/ §5.7b spec 新增 capability 默认 deny-by-default / §5.7b device_spec_history 表 + firmware_state 字段（防固件半完成）。低严重度 10：events.kind='no_action_taken'（主动不行动 vs 失败）/ §52.3 DND 退出积压投递策略 / §37.4 决策矩阵加 freshness 轴 / HouseholdScope DAO + lint 规则（多家庭隔离从约定变强制）/ §28.3 LLM 配额 per-household 记账 / failure_count 改滚动窗口 + intermittent 独立统计 / members.profile_confidence 冷启动降级 / §5.0a learn_routines 排除匿名事件 / §1b 单实例 ≤ 3 家庭 + §1 非目标声明 / holidays 有效期 + 越界兜底 + 独立内容包。

## v4.2 实测结果（2026-08-04）

### FL 训练（real_fall_train.py）
```
数据: 2000 样本 (42 pose kpts + 22 noise, 30% fall)
分片: 10 家庭 Non-IID (alpha=0.5)
FL:   FedAvg 40 轮, 92-194 样本/家庭, 总耗时 <1s
对比: 中心化 LR 1.0000 vs FL 1.0000 (差距 0.0000)
Per-family: 最小值 4 样本族仍达 1.0000
```

### 3 Agent 端到端（e2e_3agents.py）
```
场景: 老人摔倒 → A→B vision (401ms) → A→C LLM (601ms) → 2 笔交易
钱包: A $100 → $87 (减 $13) | B $150 → $155 (+$5) | C $200 → $208 (+$8)
协议: A2A task_request/response, Marketplace search, HMAC 签名, 审计
```

---

## 0. 概念入门（先搞清这几个名词）

```
┌─────────────────────────────────────────────────────────────┐
│  DeepSeek（大脑）——云端大模型，理解自然语言、做决策           │
│     ↑↓                                                      │
│  智能体工具层（中枢神经）—— 把大脑意图翻译成函数调用          │
│     ↑↓                                                      │
│  myhome-agent 本体（身体）—— 编排各模块的 Python 程序         │
│     ↑↓                                                      │
│  ┌───────────────┐   ┌───────────────┐                      │
│  │ micloud       │   │ python-miio   │  ← 两个 Python 库    │
│  │ (云端拿 token)│   │ (局域网说话)  │                      │
│  └───────┬───────┘   └───────┬───────┘                      │
│          │                   │                              │
│     米家云端              miio 协议（语言）+ token（密码本） │
│          │                   │                              │
│          └───────┬───────────┘                              │
│                  ▼                                          │
│              米家设备（电灯、空调、门锁…）                  │
└─────────────────────────────────────────────────────────────┘
```

| 名词 | 本质 | 在系统里的角色 |
|------|------|---------------|
| **miio** | 通信协议/语言 | 小米设备之间互相对话的规范（UDP 54321 + AES 加密） |
| **token** | 16 字节密码 | 用 miio 和单台设备对话的"钥匙"，绑定设备时由小米生成 |
| **micloud** | Python 库 | 登录米家云端、拿到所有设备的 token 的"外交使节" |
| **python-miio** | Python 库 | 拿到 token 后，直接和单台设备说 miio 语言的"翻译官" |
| **DeepSeek** | 云端大模型 | 系统的大脑，理解自然语言、做出决策、调用工具 |
| **OLLAMA（可选）** | 本地模型运行时 | 简单查询走本地，复杂走 DeepSeek，避免每次都上云 |
| **myhome-agent** | Python 程序 | 把上面这些接在一起的"身体"，让大脑能动起来 |

**一句话**：miio 是小米设备的语言，token 是入场券，`micloud` 帮你拿票，`python-miio` 帮你开口，DeepSeek 是大脑，**myhome-agent** 是把它们串成身体的骨架（同时支持扩展到涂鸦、Hue 等多生态）。

## 1. 设计目标

1. **懂家**：持续学习家庭作息、设备拓扑、成员习惯。
2. **能服务**：自然语言交互，主动告警，受限控制能力。
3. **本地优先**：数据存本地，LLM 本地为主、云端兜底。
4. **隐私安全**：家庭原始数据不出本地，高危操作双重保险。
5. **可演进**：NAS/树莓派 起步，能力渐进式叠加。

## 1b. 非功能需求（必须满足的性能与可靠性底线）

> 不声明这些，就会出现"在我的老 NAS 上卡了我不知道为啥"。开源用户硬件差异大，底线得先定好。

| 类别 | 指标 | 目标值 |
|------|------|--------|
| 响应 | 单 PWA 用户输入 → 首字响应 | ≤ 3s（普通网络下） |
| 响应 | 单设备状态查询 | ≤ 500ms（局域网直连路径） |
| 响应 | 单控制指令下发到设备确认 | ≤ 2s（局域网）/ ≤ 5s（云端） |
| 容量 | 支持并发设备数 | ≥ 50 台 |
| 容量 | 时序 readings 日写入量 | ≤ 20 万行/天 |
| 容量 | SQLite 单库文件大小上限 | ≤ 10GB（强制 backup+归档） |
| 内存 | 守护进程常驻 RSS | ≤ 500MB（不含本地 LLM） |
| **每实例家庭数** | **≤ 3（v2.18 设定，保守）** | SQLite 单写者 + 米家云端风控共同构成真实天花板；超过 3 拆实例 |
| 可靠 | 全年可服务时长 | ≥ 99%（年停机 ≤ 87 小时） |
| 可靠 | 单设备故障影响半径 | ≤ 全局告警，不阻塞其他设备 |
| 可靠 | 数据不丢承诺 | 已 commit 的 readings/events 不丢（SQLite WAL） |
| 隐私 | 家庭原始数据外发比例 | 0%（详见 §5.11 上云数据契约） |
| 规则引擎 | 单次扫描耗时（100 规则 × 20 设备） | ≤ 200ms（§53.9 性能边界） |
| 规则引擎 | 误报率（30 天校准后） | < 10%（§53.4 校准） |
| 规则引擎 | 漏报率（life-safety 规则） | < 5%（§53.4 校准） |
| 规则引擎 | fire → 通知送达 | ≤ 3s（§52.6 阶梯升级） |
| 规则引擎 | 兜底 LLM 调用 | ≤ 10s（§53.4.3 限流 10/天/家） |
| 视觉管线 | 单摄像头推理延迟 | ≤ 100ms（§54.9） |
| 视觉管线 | 4 路并发 | ≤ 400ms |
| 视觉管线 | 视觉事件 → 规则 fire | ≤ 3s |
| 视觉管线 | 凭证解密延迟 | ≤ 50ms（Fernet 对称） |

**时区策略**：系统全局 `home.timezone`（默认 `Asia/Shanghai`，IANA 时区），所有入库时间用 UTC ISO8601 存储；展示/学习/告警评估用 `home.timezone` 转换；不让设备本机时间参与决策（设备 RTC 不可信）。

**v2.18 非目标声明**：myhome-agent **不是 SaaS**——单实例设计上限为 3 个 household。如需服务更多家庭，请部署多个 NAS 实例 + 独立数据库。这是开源家庭定位的硬边界（架构边界前置声明，不是留给后人发现）。
## 2. 已确认的决策（v2 用户拍板）

| 维度 | 决策 | 理由 |
|---|---|---|
| 部署形态 | **NAS / 树莓派等常开设备**（具体型号待定） | 7×24 运行，局域网直连设备 |
| 能力边界 | **查询 + 告警 + 受限控制** | 不用全自主，风险可控 |
| LLM 方案 | **混合：本地模型为主 + DeepSeek 云端兜底** | 隐私日常本地解决，复杂推理走 DeepSeek |
| 数据通道 | **云端 API（设备发现+token）+ 本地 miio（实时采集）** | 社区成熟方案，覆盖最全 |
| 交互渠道 | **本地 PWA + 小米音箱语音 + 企微/微信/TG 机器人** | 在家语音+手机网页，在外机器人 |
| 时序保留 | **细粒度 30 天后聚合为小时级** | 存储可控，趋势可查 |
| 成员识别 | **门锁事件 + 设备信号综合判断** | 比纯设备信号准，无需摄像头 |
| **设备适配** | **米家 spec 自动发现 + PWA 语义配置入口**（v2.3） | 开源友好，代码零硬件预设 |
| **产品定位** | **家庭私人管家**（v2.7）—— 懂家 + 7×24 + 主动洞察 + 操办琐事 + 角色感 | 区别于"智能音箱助理"——管家更持久、更全权、更懂这家 |
| **能力结构** | **设备轨 + 家务轨 + 服务轨 + 人格轨**（v2.7，四轨合一进程） | 用户看到的仍是一个管家；底层按需调用 |
| **自主等级** | **L0-L4 矩阵 + per (成员 × 场景)**（v2.7） | 既敢替你决定又不失控；默认 L2，高危永远 L1 |
| **服务代办** | **默认 dry_run + 四道闸门**（v2.7）—— 预算 / 角色 / 渠道 / 审计 | 涉及金钱宁可繁琐不许失控；管家不持资金凭证 |
| **硬件适配** | **runtime 自适应树莓派→高端 NUC 多档**（v2.8）—— 不挑硬件，硬件决定能跑多大的本地模型 | 用户不需要关心硬件；agent 自动 probe runtime capability |
| **账号绑定** | **per-member 独立米家账号**（v2.8）—— 每个人用自己的米家账号 | 多成员家庭隔离细；admin 失效不影响其他成员 |
| **PWA 形态** | **完整 PWA**（v2.8）—— manifest + Service Worker + Web Push + 加桌面 | 准原生体验，断网可看部分数据 |
| **人设默认** | **温和务实 + 名字可改**（v2.8） | 默认"管家"称呼；用户可在 PWA 改名 |
| **MVP 能力矩阵** | **安防/照明温控/小家电/摄像头全开**（v2.8）—— 4 大类全覆盖 | 一次发布覆盖典型家庭 90% 设备类型 |
| **远程求助** | **完整远程场景**（v2.9）—— 设备状态/成员在场/摄像头快拍 + 多渠道回复 | 在外面也能"看见"家；权限同 §14 RBAC |
| **节假日** | **自动识别**（v2.9）—— 节假日表 + 自动作息漂移 + 预设场景 | 管家主动切换行为；用户可关 |
| **搬家** | **多家庭隔离**（v2.9）—— household_id 全栈串；老数据只读 | NAS 搬家数据不丢；老房子"冻结" |
| **防幻觉** | **三源验证**（v2.9）—— 高风险决策要三路独立信号一致 | 避免管家错关灯/错开锁 |
| **多代同堂** | **成员独立 + 老年人守护**（v2.9）—— RBAC + 独立作息 + 异常守护 | 老人单独建档；异常告警独立路由 |
| **多语言** | **per-member 语言**（v2.9）—— 管家按说话人切换 locale | 中英混居家庭自然 |
| **断电恢复** | **自动启动 + 补跑 + 校验核对**（v2.9）—— 上电即起 + 调度补跑 + 数据自检 | NAS 蓝屏重启后管家自愈 |
| **首装体验** | **PWA 五步向导**（v2.6 §13）：账号绑定 → 设备归房 → 成员登记 → 锁 key 映射 | 无向导开源用户上手极痛苦 |
| **权限模型** | **RBAC 矩阵**（v2.6 §14）：admin/adult/child/guest 四角色 | 防止小孩/客人误控制门锁燃气 |
| **场景原子性** | **rollback/skip/ask_user 三策略 + dry_run**（v2.6 §15） | 半截场景不可理解 |
| **降级感知** | **🟢🟡🔴 状态灯 + PWA 顶栏**（v2.6 §16） | 用户需要知道系统是否正常服务 |
| **数据补录** | **`backfill` 命令 + 缺口可视化**（v2.6 §17） | 网络断 30 分钟内事件永久丢不可接受 |
| **自主审计** | **`autonomous_id` 链路 + 审计面板**（v2.6 §18） | "为什么自动开灯"必须能回放 |
| 语音对接 | **本地网关拦截**（不走云中转） | 不确定性最高，后续单独攻关 |
| 机器人交互 | **双向：可推送也可回复对话** | 在外也能查询/受限控制 |
| 高危确认 | **对话内二次确认**（你说"确认"才执行） | 简单可靠 |
| 场景自动化 | **学习后建议制**（系统提议，你批准才自动执行） | 人机协同，不放权 |

### 2b. 配置五层优先级（v2.16 新增，v2.17 修订：补 household 层）

> §47.6 只定义了 policies 表内部优先级；全文没有"配置五层冲突时谁赢"的契约。v2.16 明确化，v2.17 补 household 第五层（之前遗漏——household_id 是跨成员共享的治理维度）。

**优先级从低到高**：

```
1. 代码默认（Python 源码 hard-coded）
   ↓ 覆盖
2. config/default.yaml（仓库内置默认值）
   ↓ 覆盖
3. household 字段（households.timezone / locale / is_primary，v2.17 新增第 5 层）
   ↓ 覆盖
4. policies 表行（policies.allow=0 / confirm_tier / autonomy_level）
   ↓ 覆盖
5. per-member 字段（members.tz / cognitive_level / accessibility）
   ↓ 覆盖
```

**冲突裁决**：
- 同一 capability 的多个层都定义 → 取**最高层**的值
- 跨字段冲突（如 home.timezone 是层 3，member.tz 是层 5）→ **层 5 生效**（per-member 优先于 household 优先于全局）
- 审计：跨层覆盖写 `events.kind='config_override', from_layer, to_layer, key, value`

**v2.17 修订前只有 4 层**，v2.17 补 household 为第 3 层——之前 §2b 的"per-member 优先于全局"实际是"per-member 优先于 household 优先于 yaml"。

**实施例**：
- code default: `feedback.timeout_ms = 8000`（v2.15 §5.6b）
- yaml: 可调 `feedback.timeout_ms = 5000`（admin 改）
- household: 暂不覆盖 timeout_ms（属系统级，不属家庭差异）
- policies 表：暂不覆盖 timeout_ms（属系统级，不属权限）
- per-member: 暂不覆盖 timeout_ms（属硬件反馈）

→ 实际生效的是 yaml 的 5000ms。

**§47.3 seed 语义（v2.16 明确化）**：

```
启动时 seed 处理（INSERT OR IGNORE 语义，v2.16 修订）：
  - INSERT OR IGNORE INTO policies ... —— "只补不改"
  - 条件：WHERE NOT EXISTS (capability_id, role, channel, household_id)
  - 用户改过（updated_by ≠ 'system'）的行 → 永不覆盖
  - users 删掉的 seed 行 → 不会被重新插回（NOT EXISTS 保护）
  - minor 升级新增 capability → 增量补种（仅 INSERT OR IGNORE）
  - 触发点：§45.3 step 4b 之后（实际写库后），不是启动时
```

## 3. 系统总览

```
                    ┌───────────────────────────────────────┐
                    │   用户端入口（多渠道）                 │
                    │  PWA 网页 · 小米音箱语音 · 微信/TG      │
                    └───────────────────────────────────────┘
                              ▲      ▲      ▲
                              │      │      │
                    ┌─────────┴──────┴──────┴──────────┐
                    │  渠道适配层 Channel Adapters      │
                    │  Web/PWA · Voice GW · Bot         │
                    │  （含：身份映射 / 会话状态）       │
                    └───────────────────────────────────┘
                              ▲
                              │
                    ┌─────────┴─────────────────────────┐
                    │  网关层 Gateway                    │
                    │  FastAPI REST + WebSocket         │
                    └───────────────────────────────────┘
                              ▲
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│  Agent 大脑   │    │  分析引擎         │    │  场景引擎     │
│ DeepSeek API  │    │ 作息 · 异常 · 在场 │    │ 建议制自动化   │
│ (阶段2本地混合)│    │ 基线学习 · 硬规则 │    │ (待批准)      │
└──────────────┘    └──────────────────┘    └──────────────┘
        ▲                     ▲                     ▲
        └─────────────────────┼─────────────────────┘
                              │
                    ┌─────────┴──────────────────┐
                    │  记忆/存储层 Memory         │
                    │  SQLite + 数据分层         │
                    │  (细粒度→聚合→清理)         │
                    └─────────┬──────────────────┘
                              ▲
                              │
                    ┌─────────┴──────────────────┐
                    │  调度层 Scheduler          │  ← v2.2 新增
                    │  周期任务 · 退避 · 单例锁   │
                    └─────────┬──────────────────┘
                              │
                    ┌─────────┴──────────────────┐
                    │  采集层 Collectors         │
                    │  miio 实时 · 云端          │
                    └─────────┬──────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
        局域网米家设备                    米家云端
```

> **运行时真相**：调度层是系统的心跳。它驱动采集轮询（每分钟）、云端同步（每小时）、作息/异常分析（每 5 分钟）、场景学习、数据聚合清理（每天）、备份（每天）。没有它，所有周期任务都散落在各模块的 `while True` 里，无法统一限流、退避、观察。详见 §5.0a。

## 4. 模块边界（代码结构，v2.10 刷新）

```
myhome-agent/
├── collectors/                 # 米家数据采集
│   ├── cloud_api.py            # 设备发现 + token 获取 + spec 拉取
│   ├── local_miio.py           # 局域网实时轮询 + 控制
│   ├── spec_norm.py            # miot spec 归一化（v2.3）
│   └── registry.py             # 统一设备注册表（按 spec 选通道）
│
├── memory/                     # 数据存储（SQLite）
│   ├── schema.sql              # 表结构（v2.10 已含 17 张业务表）
│   ├── store.py                # CRUD
│   ├── retention.py            # 30天数据聚合清理策略
│   └── migrations/             # 数据库 schema 迁移脚本（§45.3）
│
├── analytics/                  # 状态分析
│   ├── presence.py             # 门锁事件 + 设备信号综合判断
│   ├── routines.py             # 作息基线学习
│   └── anomaly.py              # 硬规则告警 + 软异常检测
│
├── agent/                      # 智能体核心
│   ├── core.py                 # LLM Agent Loop（DeepSeek 默认）
│   ├── router.py               # 顶层：LLM vs 规则模式（v2.10 §42）
│   ├── llm_router.py           # LLM 路由：本地→云端兜底（§28）
│   ├── tools.py                # 工具集
│   ├── prompts.py              # 系统提示词
│   ├── redactor.py             # 上云数据脱敏（§5.11）
│   ├── persona.py              # 管家意识/人格（v2.7 §25）
│   └── rule_mode/              # 规则模式（v2.10 §42）
│       ├── intent.py           # 关键字 + 模板匹配
│       ├── responses.py        # 模板回复
│       └── actions.py          # 规则模式下的控制触发
│
├── scenes/                     # 场景引擎
│   ├── learner.py              # 从历史事件提取"习惯性动作序列"
│   ├── suggests.py             # 生成场景建议，等待用户批准
│   └── executor.py             # 执行已批准的场景
│
├── household/                  # v2.7 家务领域（§22）
│   ├── items.py                # 家居物品
│   ├── calendar.py             # 家事日历
│   ├── health.py               # 健康档案（按需启用）
│   ├── finance.py              # 家庭账本
│   ├── relations.py            # 关系图
│   ├── recurring.py            # 重复规则展开
│   └── privacy.py              # 领域数据脱敏
│
├── services/                   # v2.7 服务代办（§23）
│   ├── base.py                 # ServiceAdapter 抽象
│   ├── registry.py             # 注册中心
│   ├── guard.py                # 四道闸门（预算/角色/渠道/审计）
│   ├── orders.py               # 订单状态机
│   ├── dryrun.py               # dry-run 报告生成
│   └── adapters/               # 第三方服务（按需引入）
│       ├── _example_template/
│       ├── meituan/
│       ├── gaode/
│       └── ...
│
├── channels/                   # 渠道适配层
│   ├── web_api.py              # FastAPI REST + WebSocket (PWA)
│   ├── voice_gw.py             # 小米音箱语音网关
│   ├── identity.py             # 渠道 user_id → member_id 映射
│   ├── auth/                   # v2.6 配对 link
│   │   └── invite.py
│   └── bot/                    # 机器人渠道
│       ├── telegram.py
│       └── wechat.py
│
├── authz.py                    # v2.6 RBAC（§47 单一 policy 表查询）
│
├── gateway/
│   └── server.py               # FastAPI 主应用
│
├── scheduler.py                # 周期任务调度（v2.10 §48 catch_up）
│
├── runtime/                    # v2.8 硬件自适应
│   └── probe.py                # RuntimeProfile 探测
│
├── obs/                        # v2.4 可观测性
│   ├── health.py               # 系统状态灯
│   ├── metrics.py              # Prometheus 导出
│   └── tracing.py              # 链路追踪
│
├── reliability/                # 备份与灾备（§44）
│   ├── backup.py
│   ├── restore.py
│   └── upgrade.py              # 自动升级脚本（§45）
│
├── backfill.py                 # v2.6 历史数据回填
│
├── i18n/                       # v2.9 多语言
│   ├── zh-CN.json
│   ├── en-US.json
│   └── ...
│
├── plugins/                    # 跨生态插件（docs/PLUGINS.md）
│   ├── base.py                 # DevicePlugin 接口
│   ├── myhome/                 # 米家插件
│   │   ├── cloud.py
│   │   ├── local.py
│   │   └── plugin.py
│   └── ...                     # 未来 tuya / hue / homekit
│
└── web/                        # 前端 PWA（manifest + SW + Push）
    ├── index.html
    ├── manifest.json
    ├── service-worker.js
    └── pages/
        ├── onboarding/
        ├── household/
        └── ...
```

**v2.10 §33.3 维护规则**："新增表/模块必须同步 §5.0b ER 与 §4 目录树"。

## 5. 关键技术方案

### 5.0a 调度层（系统心跳，v2.10 任务表刷新）

> v2.2 新增。所有周期任务的唯一入口，避免各模块各自 `while True`。
> **v2.10 刷新**：补齐 v2.7-v2.9 新增的 7+ 任务；加 `catch_up` 列（§48）。

**任务清单（v2.10 完整版）**：

| 任务 | 周期 | catch_up | 实现模块 | 失败降级 |
|------|------|---------|---------|---------|
| 本地设备轮询 | 60s | ❌ | `collectors.registry.poll_all_local` | 单设备失败不影响全局 |
| 云端设备/token 同步 | 3600s | ❌ | `collectors.registry.sync_from_cloud` | 黄灯；用上次 cache |
| 作息基线学习 | 每日 04:00 | ✅ | `analytics.routines.learn_routines` | 用上周数据 |
| 异常检测 | 300s | ❌ | `analytics.anomaly.run_all` | 单规则失败跳过 |
| 成员在场推断 | 60s | ❌ | `analytics.presence.infer_presence` | 容忍失败 |
| 数据聚合清理 | 每日 03:30 | ✅ | `memory.retention.compact` | 跳过下次补 |
| 数据库备份 | 每日 03:00 | ✅ | `reliability.backup.run` | 红灯 + 推送 |
| 场景建议扫描 | 每日 05:00 | ✅ | `scenes.learner.scan` | 推迟到次日凌晨 |
| **数据聚合清理（v2.11 加 chat_history 行）** | 每日 03:30 + 03:35 | ✅ | `memory.retention.compact` + `chat_history.purge_90d` | 跳过下次补 |
| **日历展开（v2.7 §22）** | 每日 02:00 | ✅ | `household.calendar.expand_occurrences` | 用上次展开 |
| **物品过期扫描（v2.7 §22）** | 6h | ✅ | `household.items.scan_expiring` | 单品类失败跳过 |
| **节假日判断（v2.9 §35）** | 每日 00:30 | ✅ | `household.holidays.refresh` | 退化周末规则 |
| **老人 check-in 巡检（v2.9 §38）** | 30min | ✅ | `household.elder_care.check_in` | 高级告警升级 |
| **Web Push 重试 + 失效清理（v2.8 §30.3）** | 5min | ✅ | `channels.push.retry_and_cleanup` | 单推送失败不影响 |
| **服务 order 追踪（v2.7 §23）** | 2min | ✅ | `services.orders.track` | 取消该 order 标记失败 |
| **runtime re-probe（v2.8 §28.2）** | 每日 23:00 | ❌ | `runtime.probe.run` | 用上次 profile |
| **RPO/RTO 备份校验（v2.10 §44）** | 每日 06:00 | ✅ | `reliability.backup.verify` | 黄灯 |
| **§43 留存期到期清理（v2.12 修订：原"TPM 余额对账"指向 §38.5 是错的，§38.5 是隐私边界；实际是 §43 留存期到期扫描 + 备份校验联动）** | 每周日 04:00 | ✅ | `reliability.retention.purge_check` | 列待清项 + 触发备份联动 |
| **过期临时数据清理（v2.15 新增）** | 10min | ✅ | `household.temp.purge_expired` | 扫 invite_codes/pending_confirm/push_subscriptions 过期 |
| **services_orders 滑动聚合（v2.17 新增）** | 每日 03:40 | ✅ | `services.orders.compact` | 180 天前的订单聚合成 services_orders_monthly 视图（保留 365 天）|
| **presence 滑动聚合（v2.17 新增）** | 每日 03:50 | ✅ | `analytics.presence.aggregate` | 90 天前的 presence_intervals 聚合成 presence_daily（每 member × 每房间 × 当日小时段）|
| **节假日表 2025+ 校验（v2.10）** | 每年 12-01 | ✅ | `household.holidays.refresh_year` | 手动提示 |

**技术选型**：`APScheduler`（`BackgroundScheduler`），单进程内调度。理由：成熟、轻量、支持 cron 表达式和间隔触发、无需额外服务。

**可靠性约束**（v2.10 修订）：
- **单例锁**：`flock` 进程锁（不是文件锁——容器 kill -9 后文件锁可能残留导致自锁）
- **catch_up 行为**：见 §48.2——catch_up=true 的任务会补跑
- **任务隔离**：单个任务异常不影响其他任务（try/except 包到任务级，异常写 `events` 表 + logger.error）
- **退避联动**：任务失败时按 [RELIABILITY.md](docs/RELIABILITY.md) §2 的重试矩阵走，不自己 sleep 重试
- **陈旧锁自清**：启动检查 flock 的 owner 进程是否还活着；死了自动清锁

**与任务队列的边界**：调度层只负责"到点了触发"；瞬时重试和持久化排队走 [RELIABILITY.md](docs/RELIABILITY.md) §3 的 `task_queue` 表。调度触发 → 入队 → worker 执行。

**v2.10 §33.3 维护规则**："新增能力时必须新增任务，并标注 catch_up"。

### 5.0b 数据模型概览（v2.10 ER 刷新）

> v1 把实体清单删了导致 schema 散落各处，这里补回主文档级 ER 概览。专题文档只写增量字段。
> **v2.10 刷新**：补齐 v2.7-v2.9 新增的 13 张业务表 + household_id 全栈串。

**核心实体（17 张业务表 + 6 张基础设施表）**：

#### 设备与人（v1 + v2.7-2.10 扩展）

```
households                    # 多家庭（v2.9 §36）
  id PK, name, timezone, locale,
  is_primary, is_archived,
  created_at, archived_at, notes

member_households             # 成员×家庭 N:M（v2.9 §36.4 单一权威）
  member_id, household_id, role_in_household, PK(member_id, household_id)

devices                       # 设备目录
  id PK, household_id FK, name, type, room, brand, model,
  ip, token_encrypted, mac, user_label, replaced_by,
  spec_cache JSON, online, created_at
  注：readings / events / chat_history 不加 household_id（v2.12 由 device_id / member_id 联表推导，§36.1；§36.6 B 类）

members                       # 成员
  id PK, name, role, display_name,
  devices[] (legacy), channels JSON, lock_key_map JSON,
  locale, tz,                # v2.9 §39
  mi_account_id,             # v2.8 §29
  created_at

presence                      # 在场（v2.11 字段统一 since_ts → since）
  member_id, at_home, since (TEXT, UTC), evidence, household_id

elder_care_profiles           # 老年人守护（v2.9 §38.3）
  member_id PK, emergency_contacts JSON, medical_notes (encrypted),
  daily_check_in_window, medication_schedule, quiet_hours
```

#### 时序与事件

```
readings                      # 时序读数（不加 household_id；按 device 联表推导）
  id PK, device_id, metric, value, ts (UTC), source

readings_hourly               # 聚合表（§5.2）
  device_id, metric, hour, value_avg, value_min, value_max

events                        # 离散事件
  id PK, device_id?, kind, detail JSON, ts (UTC),
  member_id?, household_id FK, autonomous_id?

alerts                        # 告警
  id PK, level (safety/care/info), title, detail,
  status (open/ack/closed), source, ts
  注：v2.10 §14 新增 safety 不可静音不变式
```

#### 习惯与记忆

```
routines                      # 作息基线
  kind (first_activity/last_activity/motion_density),
  hour, weekday?, value, confidence, household_id

memories                      # 长期记忆（v2.16 修订：统一为 §43.3 + §43.1 一致 schema）
  id PK, content TEXT, tags TEXT,
  category TEXT,                     -- 'preference' / 'fact' / 'event' / 'note'
  source TEXT,                       -- 'manual' / 'conversation' / 'observation'
  member_id INT,                     -- 所属成员（可空 = 共享）
  household_id INT,                  -- v2.16 新增：CI 断言必须有，§36.6 A 类（DIRECT_TABLES）
  archived INTEGER DEFAULT 0,        -- §43.3 步骤 3 标记用
  importance REAL DEFAULT 0.5,        -- v2.16 新增：未来衰减用（暂不消费字段）
  last_recalled_at TEXT,             -- v2.16 新增：未来衰减用（暂不消费字段）
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL

chat_history / chat_fts       # 对话历史 + FTS5 全文索引（§21）（v2.16 修订：不带 household_id；按 member_id JOIN 推导，§36.6 B 类）
  session_id, role, content, member_id, ts

persona_learn                 # 管家学习数据（v2.7 §25.3）
  member_id, kind, value, ts
```

#### 家务领域（v2.7 §22）

```
household_items               # 家居物品
  id PK, name, category, location, quantity, unit,
  expires_at, source, owner_member_id?, household_id, archived_at

household_item_events         # 物品事件流
  item_id, event_type, delta_quantity, ts

household_calendar            # 家事日历主表
  id PK, title, kind, at, recurrence_rrule, end_at,
  owner_member_ids JSON, related_devices JSON,
  reminder_minutes_before JSON, source, enabled, household_id

household_calendar_occurrences  # 重复规则展开（v2.10 滚动 90 天）
  id PK, calendar_id, occurrence_at, status, ack_by, ack_at

household_health_*            # 健康（v2.7，按需启用；加密）
household_finance_*           # 账本（v2.7，按需启用；加密）
household_relations           # 关系图
  from_member_id, to_name, to_member_id?, relation, notes
```

#### 服务与场景

```
services_orders               # 服务订单（v2.7 §23）
  id PK, service_id, member_id, channel,
  autonomous_id, state (pending/confirmed/done/failed/cancelled),
  estimated_cost, actual_cost, external_ref, pre_cancel_deadline

scene_executions              # 场景执行历史（v2.6 §15）
  id PK, scene_id, member_id, household_id, autonomous_id,
  steps JSON, status, rollback_strategy, started_at, finished_at

autonomous_decisions          # 自主行为审计（v2.6 §18）
  autonomous_id, trigger_kind, action, reason_chain, ts, household_id
```

#### 节假日与账号

```
holidays                      # 节假日（v2.9 §35）
  date PK, kind, name, recurring_rrule, family_member_ids JSON, enabled

mi_accounts                   # per-member 米家账号（v2.8 §29）
  id PK, member_id, mi_user_id, mi_region,
  encrypted_token_blob, token_expires_at, last_sync_at
```

#### 安全与基础设施

```
policies                      # 单一权威策略表（v2.10 §47 替代 §5.3/§14/§24.2/§31.2）
  capability_id, role, channel, household_id, allow, confirm_tier, autonomy_level

device_capabilities           # v2.16 改名为 capabilities（§31.2）—— v2.17 修订：§5.0b ER 仍标旧名以反映迁移期
  capability_id, category, display_name, requires_role, confirm_tier, description

runtime_profile               # 硬件档位缓存（v2.8 §28.2）
  id, tier, ram_total_gb, cpu_cores, gpu_available,
  local_tps, deepseek_available, hardware_fingerprint, ts

pending_confirm               # 高危待确认（§5.3）
  id, member_id, device_id, action, channel, ttl, ts

invite_codes                  # 配对 link（v2.6 §19）
  code, inviter_member_id, target_role, target_channels, expires_at, used_at, bound_member_id

push_subscriptions            # Web Push 订阅（v2.8 §30.3）
  member_id, endpoint, p256dh, auth, ts

task_queue                    # 可靠性任务队列（§RELIABILITY §3）
  id, kind, payload, status, retry_count, next_run_at

# ─── v0.2/v0.3 新增模块（v0.4 同步） ───

# 跨信号推理规则引擎（§53，v2.19 新增）
rules                         # 规则定义
  id, household_id, description, yaml_body, confidence_base, enabled, archived_at, severity, category, author_type, version

rule_state                    # 运行时状态机（cold_start → armed → firing → cooldown）
  rule_id, household_id, state, last_fire_at, last_eval_at, cooldown_until, true_positive_count, false_positive_count

rule_audit_log                # 每次扫描/触发审计（30 天聚合）
  id, rule_id, household_id, fired_at, kind, confidence, matched_predicates, evidence_snapshot, detail

rule_feedback                 # 误报闭环（4 选项）
  id, rule_id, fire_id, household_id, member_id, feedback, note, created_at

# 视觉管线（§54，v0.2 新增）
cameras                       # 摄像头注册表（ONVIF/RTSP）
  id, household_id, name, rtsp_url, encrypted_rtsp_url, location, capabilities, enabled, last_seen_at

vision_events                 # 视觉事件流（30 天）
  id, camera_id, household_id, kind, confidence, bbox, attributes, snapshot_path, started_at, ended_at

# v0.4 §5.0b 同步声明：上 6 张表 + 之前列的 17 张业务表 + 6 张基础设施表 = 29 张主表
# 全部 29 张表都加入 §36.6 DIRECT_TABLES 或 DERIVED_TABLES 白名单
# 详细字段见 docs/SCHEMA.md（§18-§21 规则 4 张 + §25-§26 视觉 2 张）

scheduled_tasks               # v2.11 新增：周期调度（v2.10 §48.1 catch_up）
  id PK, kind, period_seconds, last_run_at, next_run_at,
  catch_up INTEGER DEFAULT 0, enabled, payload JSON, notes
  与 task_queue 分工：scheduled=周期触发；task_queue=瞬时重试队列

schema_meta                   # schema 版本（§45.3）
  version, applied_at, notes
```

**v2.11 ER 字段统一**：
- `presence.since_ts` → `presence.since`（与 SCHEMA.md 对齐）
- `autonomous_decisions` 字段对齐 §18：`trigger_reason / decision_chain / actions_taken / review_status / evidence_path`（取代原 ER 简写 `reason_chain / action`）
- `services_orders` 补 `dry_run INTEGER DEFAULT 1`（§23.3 "默认 dry_run" 对齐 schema）

**ER 关系图（简化）**：

```
households (1) ─┬─ (N) devices
                ├─ (N) members ─ via member_households
                ├─ (N) events
                ├─ (N) routines
                ├─ (N) memories
                ├─ (N) household_items
                ├─ (N) household_calendar
                ├─ (N) holidays
                └─ (N) autonomous_decisions

devices (1) ── (N) readings
             (1) ── (N) events
             (1) ── (N) scenes  (via scene_executions)

members (1) ─┬─ (N) presence
             ├─ (N) memories
             ├─ (N) chat_history
             ├─ (N) mi_accounts
             ├─ (N) push_subscriptions
             ├─ (N) persona_learn
             ├─ (N) autonomous_decisions
             └─ (N) household_calendar.owner_member_ids (JSON)

household_calendar (1) ── (N) household_calendar_occurrences

household_items (1) ── (N) household_item_events
```

**关键字段约定**：
- `ts` 全部 UTC ISO8601 存储，展示时按 `member.tz` / `household.timezone` 转
- `household_id` 在 §36.1 列出的表上是**强制 NOT NULL DEFAULT 1**（迁移用 ALTER）；readings/events/chat_history 在 v2.10 §36.1 改为**联表推导**而非物理列（v2.11 修订：原写"§17"是 backfill，主题错位；正确来源是 §36.1）
- `devices.spec_cache` (JSON) — spec 自动归一化后的能力对象，扩展新设备字段不用改 schema
- `members.channels` — 渠道身份映射（TG user_id、企微 openid、PWA passkey token 等）
- `members.lock_key_map` — PWA 可编辑的门锁 actor_id → member_id 映射

**v2.10 §33.3 维护规则**："新增表/模块必须同步 §5.0b ER 与 §4 目录树"。

### 5.1 LLM 路由（本地 + 云端兜底）

> **v2.2 修正**：阶段 1 **只用 DeepSeek**，本地模型后移到阶段 2（等硬件定型号）。DeepSeek 成本约为 Claude 的 1/20，且架构已通过"只传摘要"前置控制隐私，阶段 1 引入双 runtime 收益低、复杂度高。

**阶段 1（单 provider）**：

```
用户请求 → DeepSeek API (deepseek-chat) → 工具循环 → 响应
```

**DeepSeek 模型分工（事实修正）**：

| 模型 | 能力 | 用途 | 限制 |
|------|------|------|------|
| `deepseek-chat` (V3.x) | ✅ 支持 function calling / JSON output | 驱动 agent 工具循环、日常对话 | —— |
| `deepseek-reasoner` (R1) | ❌ **不支持** function calling / JSON output | 纯长链推理任务（只输出分析文本，不调工具） | 不能驱动工具循环 |

> ⚠️ 上一版误以为 R1 也能驱动工具循环，实际官方明确 R1 不支持 function calling。复杂推理如需调工具，仍走 `deepseek-chat`；R1 仅用于"给一堆上下文让它分析后输出结论"的纯文本任务。落地前请以 [api-docs.deepseek.com](https://api-docs.deepseek.com/) 为准复核。

**阶段 2（混合，硬件定后）**：

```
用户请求
   ├─ 简单查询（设备状态、告警、摘要）→ 本地小模型（Ollama: Qwen/Llama3 量化版）
   ├─ 复杂推理（多步分析、跨设备协调、场景建议）→ DeepSeek API (deepseek-chat)
   └─ 本地模型失败/超时 → 自动降级到 DeepSeek API
```

本地模型选型建议（根据硬件性能）：

| 硬件 | 可用模型 | 量化 | 备注 |
|------|---------|------|------|
| 树莓派 5 (8GB) | Qwen2-1.5B / Llama3.2-1B | Q4_K_M | 只能做简单查询和意图分类 |
| 迷你主机 (N100/16GB) | Qwen2-7B / Llama3.1-8B | Q4_K_M | 可做中等复杂度对话 |
| 较强 NAS (i5+/32GB) | Qwen2-14B | Q4_K_M | 可处理大部分日常 |

**DeepSeek API 说明**：
- 模型：`deepseek-chat`（V3.x，日常对话+工具调用）/ `deepseek-reasoner`（R1，纯推理分析，不调工具）
- 接口兼容 OpenAI 协议，用 `openai` SDK 改 `base_url="https://api.deepseek.com"` 即可调用
- `deepseek-chat` 工具调用能力较强，能驱动智能体的工具循环
- 成本约 Claude 的 1/20 量级，国内访问无需代理

### 5.2 数据分层存储（30 天保留策略）

```
原始 readings (细粒度)
   │ 30 天后
   ▼
聚合 readings_hourly (小时平均/最值)
   │ 365 天后
   ▼
清理 / 归档为年统计

events / alerts / memories：
   365 天（v2.16 修订：与 §43.1 单一权威表对齐；§5.2 v2.7 旧版写"永久"以 §43.1 为准）

chat_history：
   保留最近 90 天
```

### 5.3 高危控制二次确认机制（按渠道分级，v2.10.1 标注为默认种子）

> **v2.2 修正**：原方案"任意渠道对话内回确认即可执行"对远程渠道不安全——TG/微信账号一旦被盗，攻击者发"确认"就开了门锁。改为按渠道风险分级。
>
> **v2.10.1 重要标注**：**v2.10 起，§5.3/§14/§24.2/§31.2 四张表都是 `policies` 表（§47）的"默认种子"快照**。权威表是 `policies`；本表是初始 seed。**用户在 PWA `/settings/policies` 修改后，`policies` 表生效——本表与实际行为可能不一致**。v0.1 实施时以 `policies` 表为查询源；这四张表只在系统首次安装时导入 seed 后保留文档。

**风险分级**：

| 等级 | 设备类型 | 远程渠道(TG/微信/语音) | 本地 PWA(LAN 内) |
|------|---------|----------------------|------------------|
| 🔴 高危 | 门锁、燃气阀、安防 disarm | ❌ 拒绝执行 | ✅ 需对话内确认 |
| 🟠 中危 | 摄像头、窗帘主控、空调断电 | ✅ 对话内确认 | ✅ 对话内确认 |
| 🟢 低危 | 灯、风扇、加湿器 | ✅ 直接执行 | ✅ 直接执行 |

**高危操作流程**：

```
DeepSeek 判断要控制 lock/gas/安防 → 检查发起渠道
   │
   ├─ 远程渠道 → 返回"高危操作仅支持在家时通过网页确认，请回家后操作"
   │
   └─ 本地 PWA → 进入 §5.3b 严格两阶段（v2.15 修订：避免预动作泄漏）：
       │
       │ 阶段 1（"准备态"）：pending_confirm 入库；**不下发任何 RPC 到设备**
       │   - 允许动作：调 get_device_state 读状态（无副作用）
       │   - 禁止动作：调场景 API "预热"、调设备 cloud_call 探测、写 events.control_pending
       │
       ▼ 用户回复「确认」（2 分钟内）
       │
       ├─ 超时 / 回复其他 → 放弃执行 + 写 events.kind='pending_expired'
       │
       └─ 关键词命中 + 发起人=确认人 → 进入阶段 2（"执行态"）
                                       → 真正下发控制
                                       → 触发 §5.6b 反馈环
```

**v2.15 关键修订：分两阶段（避免预动作泄漏）**

LLM 在等待用户确认期间可能发出"准备"动作（场景 API 预热、cloud_call 探测）——这些**没有 pending_confirm 保护**，无审计、无回滚、可能造成"灯闪烁一下又灭"。

**严格规则**：
- pending_confirm **创建后才允许**调只读工具（get_device_state / get_readings）
- pending_confirm **未确认期间禁止**：调场景 API / 调控制类工具 / 写 events.control_pending
- 工具调用层（§42 规则模式 + LLM agent loop）必须实现 must-not-do 校验

**追加校验：发起人=确认人**。pending_confirm 表记录原始发起人 member_id，确认时校验回复者与发起人一致，防止 A 发起、B 确认。

实现：`pending_confirm` 表暂存待确认操作（含 member_id、device_id、action、渠道、TTL、stage=pending|confirmed）。

### 5.3b 远程渠道低危白名单（v2.10 新增）

> **v2.10 新增**——§5.3 上方的"风险分级"表是"按设备类型"的；本节是"按远程渠道"的例外白名单。
> §34.4 引用本节，规定远程渠道"默认不能控制设备"的具体例外范围。

**总原则**：远程渠道（TG/微信/语音）默认**只读**——能问、能看、能查询状态、能触发低危只读场景。

**白名单**（远程渠道允许执行的写动作）：

| 设备类型 | 远程渠道允许？ | 额外条件 |
|---------|---------------|---------|
| 灯（开关） | ✅ | 仅"开/关"，不含亮度/色温微调 |
| 灯（亮度/色温） | ❌ | 远程误改概率高 |
| 空调（开关） | ✅ | 仅 on/off，远程调温易与家人体感冲突 |
| 空调（温度/模式） | ❌ | — |
| 风扇 | ✅ | 同灯 |
| 加湿器 / 空净 | ✅ | — |
| 扫地机器人 | ✅ | 仅 start / pause / return_to_dock |
| 窗帘 | ❌ | 远程误开夜窗风险高 |
| 摄像头（录像/截图） | ❌ | §5.11 image 类目禁止外发 |
| 门锁 / 燃气阀 / 安防 disarm | ❌❌ | 永远拒绝远程 |

**远程发起时的二次确认**：
- 远程白名单内动作仍需对话内二次确认（"确认在厨房开灯？回复'确认'"）
- 二次确认必须**与发起渠道相同**（TG 发起 → TG 内确认）
- 2 分钟 TTL，超时放弃

**可关闭性**：用户在 PWA `/settings/remote_acl` 可整体关闭远程写权限——关闭后远程仅只读。

### 5.4 成员识别（门锁 + 信号综合）

> **开源原则（v2.3）**：系统**零硬件预设**。所有型号相关参数从米家 APP（米家云端 device spec）自动获取；拿不到的语义信息给用户提供配置入口。代码不写死任何型号，新锁接入 = 自动发现 + 按需配置。下方机制对任意门锁型号通用。

```
事件流（型号无关）：
   调度层每分钟触发 → collectors/cloud_api 拉门锁事件日志
        │
        ▼  原始事件结构因型号而异（由 device spec 决定字段名）：
   spec 自动解析（见 §5.7b），输出归一化事件：
   - event_type: unlock / lock / door_open / door_close ...
   - actor_id:   指纹位号 / 密码编号 / null（某些型号不给）
   - timestamp
        │
        ▼
   成员归因策略（由该锁的 spec 配置项决定）：
   ├─ actor_id 存在 → 查 members.lock_key_map（用户在 PWA 登记的映射）
   ├─ actor_id 为空 → 降级为"匿名有人回家"（只触发在场，不归因到人）
   └─ 该型号 spec 声明不支持归因 → 跳过，纯靠设备信号（§5.4 设备信号段，v2.11 修订：原"下半段"失锚——§5.4 是单节，无子编号）
        │
        ▼
   联动验证：该成员手机是否在局域网？
        │
        ├─ 是 → presence 标记 "在家"
        └─ 不确定 → 等手机上线/离线变化再更新
```

**两类信息，两个来源**（关键区分）：

| 信息类别 | 例子 | 来源 | 是否需用户介入 |
|---------|------|------|--------------|
| 设备能力 spec | 传输方式(bluetooth_mesh/wifi)、可控性、事件字段名、事件类型枚举 | 米家云端 device spec（自动） | 否 |
| 业务语义 | key_id=1 是谁、该锁要不要做归因、哪个房间 | 云端拿不到 | 是，PWA 配置入口 |

**配置入口（PWA）**：
- 门锁发现后，自动展示该锁支持的事件类型和 actor_id 取值范围（来自 spec），让用户登记 `members.lock_key_map`（如 `{fingerprint_1: 爸爸, password_2: 妈妈}`）
- 若用户不登记，系统自动降级为匿名在场触发，不报错不阻塞

**作者自用设备**：小米智能门锁 M4 Pro。它走蓝牙 Mesh 接入网关 → 本地 miio 摸不到 → 事件走云端日志 API → spec 自动识别为 `transport: bluetooth_mesh, local_controllable: false`。这套机制对 M4 Pro 和其他用户的其他型号锁一视同仁，无需为 M4 Pro 写任何特殊代码。

### 5.5 场景建议引擎

系统持续观察历史事件，识别"用户手动执行的一系列动作序列"：

```
观察 30 天：
  每天 23:00 左右：关客厅灯 → 拉窗帘 → 开卧室小夜灯
        │
        ▼
 生成场景建议：
  "检测到你最近 23 点常执行「关客厅灯+拉窗帘+开卧室灯」三个动作，
   要不要做成「睡觉模式」？以后说「我要睡觉了」就一键执行"
        │
        ▼
 用户回复 "批准" → 场景入库，自动执行
 用户回复 "不要" / 超时 → 忽略
```

### 5.6 多渠道适配

| 渠道 | 实现 | 能力 |
|------|------|------|
| PWA | 已有 FastAPI 静态托管 | 全功能（对话+控制+面板），LAN 内可信 |
| 小米音箱 | 本地语音网关（技术攻关项，详见 §7 风险） | 语音对话+中危控制 |
| Telegram | python-telegram-bot 长轮询/webhook | 推送+双向对话+中危控制（高危拒绝） |
| 微信 | **v2.19 决策 B 不做**（详见 §10 / §53.12）| v3 治理框架成熟后再考虑企业微信 |

> 高危控制按 §5.3 的渠道分级执行，远程渠道拿不到门锁/燃气控制权。

### 5.6b 控制指令反馈环（关键基础设施）

> v2.4 补。控制指令必须闭环：发出后要重新读设备状态确认成功，并据此校正数据库的本地状态快照。否则会出现"agent 说关灯了实际还亮着""数据库说开着实际关了"——下次查询/场景执行就基于错误状态。

```
registry.control(device_id, action)
   │
   ▼  通道 A 或 B 下发（按 §5.7b spec 选）
   │
   ▼  等 1s → 重读设备状态（registry.poll device_id）
   ├─ 期望值匹配（比如 action=on 读到 power=on）→ 写 events 表 control_done=true
   ├─ 不匹配 → 再等 2s 重读
   │     ├─ 第二次匹配 → 写 done=true（带 latency）
   │     └─ 仍不匹配 → 再等 5s 重读（最多 3 次）
   │           ├─ 第三次匹配 → 写 done=true
   │           └─ 仍失败 → 写 done=false，触发软异常告警
   │
   ▼  失败处理（v2.15 扩为三态）
   - **done=true**   → 设备状态确认匹配，保留乐观快照
   - **done=false**  → 设备明确未响应（micloud 4xx/5xx），撤销乐观快照 + 软异常告警
   - **done=timeout**（v2.15 新增）→ 8s 内无任何回执
                          → 撤销乐观快照（视为未执行）
                          → 写 events.kind='control_unknown'
                          → 区别于 done=false（明确失败 vs 状态未知）
                          → 推 PWA "管家刚尝试 X，但未确认成功，请检查"

**v2.15 修订：撤销窗口延长**：撤销窗从反馈环判定 done 之时起算，最长 60 秒（门锁）/ 30 秒（其他）；与 §37.5 一致。
```

**反馈环配置**（在 `config/default.yaml` 的 feedback 节）：

```yaml
feedback:
  read_after_ms: [1000, 2000, 5000]   # 3 次重读节奏
  on_mismatch: rollback_local          # 不回滚就闹鬼
  on_timeout: rollback_local           # v2.15 新增：timeout 态也撤销乐观快照
  emit_soft_alert: true
  timeout_ms: 8000                     # v2.15 新增：超时阈值
  undo_window_seconds:                 # v2.15 新增：撤销窗
    lock: 60
    default: 30
```

**不实现的代价**：agent 会"自欺欺人"——以为控制了实际控制失败，下一轮再发同指令，循环。

**v2.16 新增：并发写控制 + /undo 栈语义**

**per-device 串行化**（默认开启，**确保家庭场景下 3 人同时控不撞**）：

```
设备写指令通过 `device_command_queue` 串行化执行：
  - per-device FIFO 队列，跨 session 共享
  - 同一 device_id 的 control 命令按到达顺序串行执行（不是并发）
  - 不同 device_id 并发
  - 实现：myhome_agent/runtime/device_queue.py（asyncio.Queue + lock）

但串行化仍不能解决"用户意图冲突"——A 开灯后 0.5s B 关灯，串行执行都成功，但 A 的反馈环读到的是 B 的关灯结果。
```

**/undo 栈语义**（v2.16 新增）：

```
控制指令完成后入栈（撤销窗期内）：
  control_stack(device_id, action, params, member_id, channel, autonomous_id, ts, undo_expires_at)

撤销冲突解决（按以下优先级）：
  1. 撤销时如果目标设备被后续控制覆盖：
     → "管家刚尝试 X（30s 前），但 5s 前 Y 又改过；按现状是 Y 的状态，无法撤销 X"
  2. 撤销时如果在撤销窗期：直接撤销该操作（逆向控制）
  3. 撤销时如果超出撤销窗期：拒绝 + 提示用户手动改
  4. 多用户同时撤销同一设备：第一个撤销赢，后续撤销收到"已被撤销"提示

undo_expires_at 默认 30s，门锁 60s（§37.5 同步）

撤销事件记录：
  events.kind='control_undo', autonomous_id=<原始操作>
```

**§5.6b 心智模型更新**：从"单一控制者"扩展到"多用户串行 + 撤销栈"。反馈环读到状态"不匹配"时**先检查撤销栈**——若是他人合法操作则不报故障。

### 5.7 与米家体系的接合方式（通道选择）

myhome-agent **绕开米家 APP 本身**，直接对接米家体系的三个后端层面：

```
┌─────────────────────────────────────────┐
│ 米家 APP（前端 UI，agent 不接入）        │
├─────────────────────────────────────────┤
│ 米家云端服务 api.io.mi.com   ← agent 走云端 API
├─────────────────────────────────────────┤
│ 家庭网关 / 路由器                       │
├─────────────────────────────────────────┤
│ 米家设备              ← agent 走局域网 miio
└─────────────────────────────────────────┘
```

#### 三条通道

| 通道 | 用途 | 实现 | 优先级 |
|------|------|------|--------|
| **A. 局域网 miio** | 实时轮询、控制设备（最快、离线可用） | `python-miio`，UDP 直连 | 🥇 首选 |
| **B. 云端账号 API** | 设备清单+token 获取、zigbee 子设备、门锁日志 | `micloud` 登录米家账号 | 🥈 补充 |
| **C. 云端场景 API** | 触发米家 APP 里配置的"自动化场景" | `cloud.run_scene(id)` | 🥉 复用米家规则 |

#### 通道选择矩阵（v2.10 F10 更新）

| 任务 | 走哪条 | 备注 |
|------|--------|------|
| 拿到设备清单 + token | B | 每小时同步一次，写库 |
| 实时温湿度 / 能耗 | A | 每分钟轮询 |
| 开关灯 / 调空调 / 拉窗帘 | A | 延迟毫秒级 |
| 控制 zigbee/蓝牙 mesh 子设备 | B | 这些子设备走网关，本地摸不到 |
| 读取门锁指纹/密码开锁记录 | B | 走云端日志 API |
| 触发"回家模式"/"离家模式" | C | 等同在 APP 里点了按钮 |
| **摄像头截图（一次性）** | B → **本机代理** | 详见 §5.7c 影像通道 |
| **摄像头录像回放** | B → **本机代理** | 同上 |
| 摄像头报警事件（motion/doorbell） | B | 走云端事件，**仅元数据**（不含视频流）|
| 视频原始流 | ❌ | 不接（用户自接 RTSP 见 §5.7c） |

#### 5.7c 影像通道（v2.10 新增，F10）

> 解决"§5.7 视频不可用 vs §31/§34/§38 大量依赖摄像头影像"的不一致。

**关键不变量**：**摄像头影像（截图/录像）绝不外发到云端 LLM**——LLM 看到的是元数据 + 文字描述，影像本身只在 PWA 内经本机代理访问。

**通道分级**：

| 操作 | 实现 | 出本机？ |
|------|------|---------|
| 截图（一次性帧） | cloud API 触发 → 返回云端签名 URL → PWA 经**本机代理**取图显示 | ❌（PWA 仅）|
| 录像回放 | cloud API 拉取 → 本机缓存 → PWA 播放 | ❌ |
| 视频实时流（RTSP） | 用户自接（如 §5.7c 末尾说明）| ❌ |
| 视觉推理（"图里有没有人"） | L0-L2 硬件**不支持**；L3+ 可跑轻量视觉模型（YOLOv8-nano）| ❌（本地推理）|

**远程渠道（TG/微信/语音）的影像处理**：
- 默认**只返回文字描述**："门口有人，正在按门铃"
- 不发图片 / 视频文件
- 如必须发图，发**一次性本机链接**（token + TTL 5min），用户点开经家里代理拉取

**硬件能力自适应**：
- L0-L1（树莓派）：无视觉推理，跌倒检测降级为可穿戴/雷达方案
- L2（无 GPU）：同上
- L3+（有 GPU）：可加载 YOLOv8-nano 做基础检测

**接入用户自有 RTSP**（可选）：
- 用户自购摄像头（海康/大华等）带 RTSP 输出
- 配 `config/cameras.yaml`：`rtsp://user:pass@192.168.x.x/stream`
- agent 转发到 PWA，不入米家云端

```python
registry.sync_from_cloud()        # B：从云端拉清单+token
registry.poll_all_local()         # A：本地轮询所有设备  
registry.control(dev_id, "on")    # A→B 自动降级
```

DeepSeek 工具的 `control_device` / `get_device_state` 都调用 Registry，不关心走的是哪条路。

#### 5.7b 设备 spec 自动发现（型号无关化，v2.3）

> 开源原则：**代码零硬件预设**。每台设备的能力（传输方式、可控性、事件字段、指标枚举）从米家云端 device spec **自动获取**，不写死任何型号。

**spec 来源**：米家云端 `/miotspec` 接口返回每台设备的能力描述（property/action/event 的 siid/piid 定义）。米家 APP 显示的设备能力，本质上就来自这个 spec。

**spec 解析流程**：

```
sync_from_cloud 拉设备清单
   │
   ▼  对每台设备，按 model 查 spec
   spec（JSON，能力描述）
   │
   ▼  spec_normalizer 归一化
   归一化能力对象，写入 devices.spec_cache（JSON 列）：
   {
     "transport": "bluetooth_mesh" | "wifi" | "zigbee",
     "local_controllable": true | false,        # 决定走通道 A 还是 B
     "metrics": [{"name":"temperature","unit":"℃","access":"r"}, ...],
     "events":  [{"name":"unlock","has_actor_id":true}, ...],   # 事件类型+有无归因字段
     "actions": [{"name":"set_power","params":...}, ...]
   }
   │
   ▼  各模块按 spec 行为，不按型号
   - collectors:  transport=mesh → 走云端；transport=wifi+local_controllable → 走 miio
   - analytics:   events[].has_actor_id → 决定能否做成员归因
   - agent tools: 按 spec.actions 暴露该设备能做什么（见下）
```

**v2.16 新增：spec_cache 与 capabilities 表同步**

```
spec_normalizer 在每次 sync_from_cloud 完成后做 diff：
   1. 对比新旧 spec_cache（基于 devices.spec_hash + fetched_at；v2.17 修订：原字段 spec_version 是米家 spec API 的 last_updated 时间戳或 spec_hash，非 semver）
   2. 增量 capability 注册：
      - 新增 action → 自动 INSERT INTO capabilities (capability_id, domain='device', ...)
        **v2.18 关键修订：deny-by-default**
        - 新 capability 默认 seed policies 为 allow=0 + autonomy_level=0 + requires_admin_review=1
        - PWA /settings/policies 展示"待审核 N 条"
        - admin 显式批准（allow=1）后该 capability 才可被 LLM 工具调用
        - 原因：固件升级给设备带来"远程开门"等新 action，若默认可用，等于无审核
      - 删除 action → 不删除 capability（避免 FK ON DELETE RESTRICT 阻断）
                   而是标 capabilities.deprecated=1 + policies.allow=0
   3. 能力漂移告警：写 events.kind='capability_drift', detail=JSON diff
                    → PWA 通知 admin "客厅灯新增 set_color_temp 能力"

**v2.17 新增：固件升级事件触发入口**

```
设备固件升级是设备事件触发（property 推送），不是 sync 时段：
  1. 监听 devices.firmware_version 字段变化（米家 spec 推送 property update）
  2. 检测到变化 → 立即触发该 device 的 spec re-pull（带 backoff 限流，间隔 ≥1h）
  3. 写 events.kind='firmware_changed', detail={device_id, old_version, new_version, ts}
  4. 同步走 §5.7b 的 spec diff → 触发能力漂移告警（如果新固件带来能力变化）
  5. 用户体验：固件升级 1 小时内自动完成 spec 刷新 + PWA 通知
```

devices.spec_cache 扩字段（v2.16，v2.17/v2.18 修订）：
   - spec_fetched_at TEXT  (上次拉取时间)
   - spec_hash TEXT        (v2.17 修订：原 spec_version 实为米家 spec API 的 last_updated 时间戳或 spec_hash，非 semver；改为 spec_hash 用于 diff)
   - firmware_version TEXT  (v2.17 新增：固件版本，触发 §5.7b 固件升级事件)
   - firmware_state TEXT DEFAULT 'verified',  -- v2.18 新增：'verified' / 'pending' / 'quarantined'
                                                      -- pending: 固件升级中
                                                      -- quarantined: 升级后失败率 &gt; 30%
   - failure_count INT DEFAULT 0  (实测失败计数)
   - failure_marked_at TEXT        (连续 N 次失败降权时间戳)
   - last_success_at TEXT          (v2.18 新增：用于自动解除降权)
```

**v2.18 新增：spec_cache 历史快照表 + 固件半完成保护**

```
CREATE TABLE device_spec_history (
  device_id INT NOT NULL,
  spec_hash TEXT NOT NULL,
  spec_content JSON NOT NULL,
  firmware_version TEXT,
  firmware_state TEXT,                 -- 'verified' / 'pending' / 'quarantined' / 'rolled_back'
  fetched_at TEXT NOT NULL,
  source_event TEXT,                   -- 'sync' / 'firmware_changed' / 'manual_restore'
  PRIMARY KEY (device_id, fetched_at)
);
CREATE INDEX idx_spec_history_device ON device_spec_history(device_id);

行为：
  1. spec_normalizer 每次更新 spec_cache 前先 append 到 spec_history（保留最近 5 条）
  2. firmware_state 检测：
     - 固件升级事件触发 → state='pending'
     - 新 spec 拉回 + 重测通过 → state='verified'（覆盖 spec_cache）
     - 新 spec 拉回但同一 action 失败率 ≥30%（窗口 100 次）→ state='quarantined'
       + PWA 通知 admin "设备 X 固件升级后能力异常，请验证或回刷固件"
  3. 失败标记 + 自动解除：failure_count 达到阈值 → marked_at + 降权
     但 last_success_at 后 24h 内无失败 → 自动解除降权（v2.18 修订：v2.16 写"只增不减"，不可逆）
```

**v2.18 修订：failure_count 改滚动窗口 + intermittent 故障独立统计**

```
原 v2.16 "连续 N 次失败" → 间歇性故障永远不可见；v2.18 改为双指标：

1. systemic 指标（持续故障）：
   - 窗口：14 天
   - 触发：失败率 &gt; 30% 且绝对次数 ≥ 5
   - 动作：devices.spec_cache.actions[i].disabled=true + 降权

2. intermittent 指标（间歇故障）：
   - 窗口：100 次命令
   - 触发：commanded/reported 不一致率 ≥ 10%
   - 动作：PWA 提示"设备 X 状态上报可能不可靠"，不自动降权（避免误判）

3. 自动解除（v2.18 新增）：
   - 标 disabled=true 后，last_success_at 后 24h 内无失败 → 自动解除
   - 写 events.kind='capability_restored'
```

**Registry 改造**：`registry.poll(dev)` / `registry.control(dev, action)` 内部都先查 `dev.spec_cache`，按能力对象决定路径，不再有型号分支判断。

#### 现实约束（需要在实施时留意）

- **token 获取**：用 `miio cloud <user> <pass> --dump` 一键 dump，近年部分新型号策略收紧，可能需要手机配合或抓包
- **zigbee/蓝牙 mesh 子设备**：门窗传感器、水浸传感器、蓝牙门锁等走网关的设备**本地轮询不到**，只能用云端 API（spec 里 `transport` 会标明）
- **锁/摄像头 token 加密**：出于安全考虑，锁的 token 经常变化，需要定期 dump；摄像头画面基本不开放
- **云端风控**：登录频率太高会被风控，清单同步频率建议 ≥1 小时
- **场景触发频率**：米家云端对场景调用有 QPS 限制，连续触发需 ≥1s 间隔
- **spec 不全的设备**：极个别老旧或第三方设备 spec 缺失，此时**回退到 PWA 手动配置入口**（填指标名、事件名），不阻塞使用

### 5.8 身份与会话（谁在说话、谁在家）

> v2.2 新增。§5.4 解决的是 *presence*（谁在家），这里解决的是 *authentication*（这条消息是谁发的）。两者不能混为一谈——否则 agent 没法个性化回复，也没法做"这个成员能否控制这个设备"的权限判断。

**两个维度分开**：

| 维度 | 回答的问题 | 判断依据 | 用途 |
|------|-----------|---------|------|
| 认证（authentication） | 这条消息是谁发的？ | 渠道 user_id → member_id 映射 | 个性化回复、权限校验 |
| 在场（presence） | 这个人现在在家吗？ | §5.4 门锁+设备信号 | 主动关怀、场景触发条件 |

**渠道身份映射**（`channels/identity.py`）：

| 渠道 | 身份来源 | 信任度 | 处理 |
|------|---------|--------|------|
| Telegram | bot 收到 from_user.id | 高（绑定 TG 账号） | user_id → member_id 查表 |
| 微信/企微 | openid / userid | 高 | openid → member_id 查表 |
| **PWA（v2.10 必登录）**| **轻量登录**（§5.8b passkey / PIN / 设备绑定 token）| **取决于登录方式** | **默认未登录 = 只读仪表盘；写操作必登录** |
| 小米音箱 | 声纹未做（MVP） | 低 | 当作匿名家庭指令 |

> **v2.10 F4 修订**：原写"PWA 默认无（LAN 内免鉴权）"——这与 §14 RBAC 矛盾，**任何连上家庭 WiFi 的人/设备都是 admin**且拥有门锁唯一控制通道。改为 **PWA 强制轻量登录**。详见 §5.8b。

**会话状态**：每个 (渠道, user_id) 维持独立会话上下文，存在 `chat_history` 表，按 session_id 分组。跨渠道不自动合并（避免 A 在 TG 问的问题，B 在 PWA 看到上下文）。

**权限校验链**（控制设备前）：

```
消息到达 → 解析 member_id → 查 member.role → 校验：
  1. 该成员能否操作该设备类型？（role 权限，如小孩不能控制门锁）
  2. 该渠道能否执行该操作风险等级？（§5.3 渠道分级）
两者都通过 → 进入高危确认流程
```

### 5.8b PWA 轻量登录（v2.10 新增，F4）

> **v2.10 F4 新增**——为解决"LAN 内免鉴权 = 任何 WiFi 接入者都是 admin"的安全漏洞，PWA **强制轻量登录**才能写操作。

**三档登录方式**（用户在 PWA 选）：

| 方式 | 适用 | 强度 | 实现 |
|------|------|------|------|
| **passkey（推荐）** | 主流手机/电脑 | 高（指纹/面容/Windows Hello） | WebAuthn API |
| **PIN 码** | 不支持 passkey 的旧设备 | 中（4-6 位数字） | 服务端 bcrypt + 限流 5 次/分钟 |
| **设备绑定 token** | 信任家庭内某台设备 | 中（首次配对后免登 30 天） | 首次 PIN/passkey 配对 → 发 token 存本机 IndexedDB |

**未登录态**（访客首次进入 PWA）：

- **可访问**：仪表盘、设备列表（只读）、历史事件（只读）、告警列表（只读）
- **不可访问**：控制设备、添加物品、修改成员、查看详细 chat_history、导出数据
- **可操作**：点击"登录"按钮（跳 §5.8b 登录页）

**会话持续**：
- 登录后 session 8 小时
- 滑动过期（活动时刷新到 8h）
- 关闭浏览器即失效（不持久化 localStorage）
- 设备绑定 token 例外：可持久 30 天

**关键不变量**：
- 门锁 / 燃气 / 大额服务代办 → 即便已登录仍需二次确认（§5.3）
- 高危动作**永远不**因"已登录"而跳过确认
- 设备绑定 token 失效前 7 天弹"是否续期"

### 5.9 上下文预算（喂给 LLM 的数据契约）

> v2.2 新增。架构说"只传摘要给云端"，但没定义摘要契约。`query_readings` 拉 30 天数据可能几万行，直接塞进 LLM 会爆 token、烧钱、变慢。这里定义截断和预算规则。

**工具返回值截断规则**（`agent/tools.py` 强制）：

| 工具 | 默认返回上限 | 超限处理 |
|------|------------|---------|
| `get_readings` | 最近 24 条或 24 小时 | 更早的降采样为小时统计 |
| `query_events` | 最近 50 条 | 更早的给计数和首末时间 |
| `list_devices` | 全量（设备数有限） | 超过 100 台时按房间分组摘要 |
| `get_home_summary` | 固定 ≤ 800 token | 超限优先级截断（见下） |

**家庭快照（home snapshot）**：每次对话注入 `prompts.py` 生成的家庭状态摘要，有硬 token 预算：

```
家庭快照（≤800 token，每次对话注入 system prompt）
  ├─ 在家成员（来自 presence）          高优先
  ├─ 今日异常/告警（来自 alerts）        高优先
  ├─ 各房间环境（最新 readings 摘要）    中优先
  ├─ 设备在线率                          低优先
  └─ 作息摘要（来自 routines_summary）  低优先
```

预算超限时按优先级从低到高截断，保证关键信息常驻。

**DeepSeek 成本锚点**：单次对话输入 ≤ 4K token、输出 ≤ 2K token 为目标（家庭场景对话通常够用）。超出时优先靠工具分页查，而不是一次性灌入。

### 5.10a 端到端示意：用户说"今晚客厅太热"（v2.11 编号重排：从此处起在 §5.11 之前）

```
1. PWA / 语音 → channel adapter → gateway（带 member_id / session_id / request_id）
2. gateway → agent / core（带 home snapshot ≤ 800 token，从 §5.9 生成）
3. core → redactor.apply(snapshot, target=deepseek) → DeepSeek 看到脱敏后的家庭摘要
4. core 调工具：get_readings('living_room', metric='temperature', since=1h)
   → 返回原始值（不出本地，仍在 agent 进程内）
   → 工具返回值也走 redactor（target=deepseek）再注入下一轮对话
5. core 调 control('living_room_ac', 'on', mode=cool) → 进入 §5.3 渠道分级 + §5.6b 反馈环
6. 反馈环读到 26℃ 降到 25.5℃ → 在 events 写 control_done=true
7. 用户对话回 "已开客厅空调降温" —— core 按本地策略脱敏后用于云端 trace；chat_history 存**原始回复**（v2.12 修订：原"脱敏后才写到 chat_history"语义错——chat_history 是本地表不需要脱敏）
```

### 5.11 上云数据契约（强制脱敏）

> v2.4 新增。§5.9 约束的是"喂多少"，§5.11 约束的是"喂什么"——任何出本地的字节必须经过 `redactor.py`，未脱敏字节不得出本地。这是 §1 设计目标"家庭原始数据不出本地"的具体执行。

**实现位置**：`agent/redactor.py`，作为包级唯一出口；调用链：

```
任何外发（DeepSeek 调用、TG 推送、企微推送、日志上传、metrics 上报）
   ↓
redactor.apply(payload, target=deepseek|telegram|logs)
   ↓
已脱敏的数据出本地
```

**脱敏规则表**（默认配置，可在 `config/redactor.yaml` 覆盖）：

| 敏感信息 | 默认脱敏 | 替换形式 |
|---------|---------|---------|
| 真实姓名 | ✅ | 昵称（用户在 members 表配置的 `display_name`，如"爸爸"） |
| 精确地址 | ✅ | 仅"家中"/"外出" |
| 设备 MAC / serial | ✅ | 哈希前 8 位 |
| 设备 token | ✅ | 完全剥离（默认配置下） |
| 精确时间戳 | ✅ | "今早"/"昨晚"/"23 点左右" 等时段描述 |
| 数值（温度/湿度/功率） | 视情况 | 区间（"26 度左右"）；查询请求保留具体值 |
| 公司/单位 | ✅ | 通用占位 |
| 孩子在场（年龄 <14） | ✅ | 完全脱敏为"有儿童在家" |
| **摄像头截图/录像 URL（v2.10 F11 新增）** | ✅ | **完全剥离 URL**；LLM 只看到元数据（"门口 motion，10s 前"）|
| **图片二进制（v2.10 F11）** | ✅ | **完全不外发**；LLM 收到的是文字描述（"门口有人"）|
| **本机一次性链接（v2.10 F11）** | ✅ | **不出本机代理**；通过家庭内网 PWA 拉取 |

**按 target 的差异**：

| target | 脱敏强度 | 备注 |
|--------|---------|------|
| `deepseek` | 中（保留关系与时段，去标识化） | 推理需要上下文 |
| `telegram` / `wechat` | 高（昵称 + 时段，去细节） | 推送通知不暴露 |
| `logs`（本地） | 低（仅脱敏密码/token） | 本地不外发，不用强脱敏 |
| `metrics` | 中（聚合后才上报） | §OBSERVABILITY 见 |

**配置审计点**：

- `redactor.yaml` 每次启动快照到 `logs/redactor-config-<ts>.yaml`
- 实测覆盖：在 tests/redactor/ 维护正反例集（"这条消息进去应该脱敏成什么"）

**违规检测**：

- 单元测试扫描所有上云 payload，对照 fixtures 校验"必脱敏字段已脱敏"
- 生产模式：日志告警 `"redactor_unredacted_field": "ip_address"` ，不出本地，仅起识别作用

### 5.12 PWA 信息架构（前端页面分层）

> v2.4 新增。一个 PWA 装在手机/平板/电脑上不能把所有功能堆一页，要按任务层级组织。这节是 PWA 工程的契约——后端 API 也要按这个分层提供。

**入口**：默认 `/` 路由，家庭仪表盘（home）。其他页面按需进入。

**信息架构（七大区，分层而非单页面塞全部）**：

| 区 | 路径 | 用途 | 关键 API | 优先级 |
|----|------|------|---------|-------|
| **🏠 家庭仪表盘** | `/` | 一眼看到的：在家成员 / 当前告警 / 各房间状态 / 设备概览 | `GET /home/summary` | P1 |
| **💬 对话** | `/chat` | 与 agent 自然语言对话 | `POST /chat/messages` (WS) | P1 |
| **🛠 设备面板** | `/devices` | 设备列表 + 单设备详情 + 快速控制 | `GET /devices`, `GET /devices/{id}`, `POST /devices/{id}/control` | P1 |
| **📊 历史** | `/history` | 时序图表（温度/能耗等）+ 事件流 | `GET /readings`, `GET /events` | P2 |
| **🚨 告警中心** | `/alerts` | 活跃告警 + 历史告警 + 确认 | `GET /alerts`, `POST /alerts/{id}/ack` | P1 |
| **👨‍👩‍👧 成员与配置** | `/settings/members` | 成员档案、关联设备、lock_key_map、昵称 | `GET/PUT /members` | P2 |
| **⚙️ 系统设置** | `/settings/system` | 米家账号、Llm Key、PWA 偏好、加密 key 管理、Redactor 配置 | `GET/PUT /config/*` | P2 |

**导航模式**：底部 Tab + 抽屉式详情。手机主屏不超过 3 步进入 90% 任务。

**首屏硬要求**：

- 加载时间 ≤ 1s（家庭局域网场景，离米家云可能很慢）
- 离线后能 PWA 显示历史快照（service worker 缓存 home summary）
- WCAG AA 对比度（用户家里有老人/小孩）

**REST 命名约定（与 PWA 区域对齐）**：

- 资源：`/devices` `/members` `/alerts` `/events` `/readings`
- 操作：`POST /devices/{id}/control`, `POST /alerts/{id}/ack`
- 不要用动词资源（如 `/controlDevice`），破坏 RESTful 习惯难索引

**PWA 离线策略（关键）**：

- `service-worker.js` 缓存：HTML 外壳 + 静态资源 + 最近 1 次 home summary（24h TTL）
- 控制指令、对话、配置变更 → 必须在线（不带离线能力，避免误操作）

**前端目录约定**：

```
web/
├── index.html              # 外壳 + 路由骨架
├── app.js                  # 路由 + 全局状态
├── pages/                  # 每个区域一个文件
│   ├── home.js
│   ├── chat.js
│   ├── devices.js
│   ├── alerts.js
│   └── settings.js
├── components/             # 共享 UI 原子（卡片/按钮/告警标记）
├── offline/                # service worker
└── styles/
```

- 单文件应用，**不引入 React/Vue**——PWA 体量应 < 200KB gzip，避免成为 README 里"安装一小时编译五分钟"的吐槽源

**API 与 PWA 同步演进原则**：新增能力时，API 路径先定 → 后端实现 → PWA 调，反过来不行（防止前端定路径后端跟不上的债）。

## 6. 硬件推荐

根据 LLM 路由方案（本地模型需求），硬件配置参考：

| 预算 | 推荐 | 能跑 |
|------|------|------|
| 最低 | 树莓派 5 + 8GB + 64G 卡 | 只做采集+DeepSeek云端，本地模型效果差 |
| 推荐 | N100 小主机 + 16GB + 500G SSD | 本地 Qwen2-7B 流畅，复杂走 DeepSeek |
| 舒适 | i5 迷你主机 + 32GB + 1TB | 本地 Qwen2-14B，几乎不依赖云端 |

### 6.4 v2.19 决策 C：本地模型硬件预算（分层方案）

> 本节把 v2.10 §10 待定项"本地模型硬件预算"明确为分层方案。架构不预先锁定单一硬件，而是**按模型负载分层 + 给出升级触发条件**。

#### 6.4.1 分层架构

```
┌─────────────────────────────────────────┐
│ Layer 4: 云端 LLM（DeepSeek / GPT-4o）   │
│  - 复杂推理 / 视觉 / 兜底                │
│  - 按 token 计费（单家庭 5-30 元/月）    │
└─────────────────────────────────────────┘
              ↑ 复杂信号兜底
┌─────────────────────────────────────────┐
│ Layer 3: 本地专用模型（NAS 上）          │
│  - YOLO / MobileNet（人形/跌倒/火焰）   │
│  - 语音 STT（Whisper.cpp）              │
│  - 轻量规则推理（§53 规则引擎）         │
└─────────────────────────────────────────┘
              ↑ 专用模型
┌─────────────────────────────────────────┐
│ Layer 2: 本地 LLM（轻量）                │
│  - Qwen2-1.5B / Llama-3.2-3B            │
│  - 简单对话 / 意图识别 / 摘要            │
│  - 不做复杂工具调用                      │
└─────────────────────────────────────────┘
              ↑ 轻量推理
┌─────────────────────────────────────────┐
│ Layer 1: 规则引擎（确定性）              │
│  - §53 跨信号推理（99% 场景）           │
│  - 不调用 LLM 即可运作                  │
│  - 永远在线 / 零成本 / 零延迟           │
└─────────────────────────────────────────┘
```

#### 6.4.2 硬件阶梯（按家庭规模）

| 阶梯 | 硬件 | RAM | SSD | 适用家庭 | 月度云端成本 |
|------|------|-----|-----|---------|------------|
| **L1 入门** | 树莓派 5 / N100 8GB | 8GB | 64G 卡 / 256G SSD | ≤10 设备、纯控制 | 5-15 元 |
| **L2 推荐** | N100 小主机 16GB | 16GB | 500G SSD | 10-30 设备、含老人守护 | 10-30 元 |
| **L3 舒适** | i5 / N305 迷你主机 32GB | 32GB | 1TB SSD | 30-50 设备、视觉深度集成 | 20-50 元 |
| **L4 升级** | RTX 3060 12GB 独显 | 32GB | 1TB SSD | ≥50 设备、本地 14B 模型 | 5-15 元 |

#### 6.4.3 各层在硬件上能跑什么

| 层级 | L1 入门 | L2 推荐 | L3 舒适 | L4 升级 |
|------|---------|---------|---------|---------|
| Layer 1 规则引擎 | ✅ | ✅ | ✅ | ✅ |
| Layer 2 轻量 LLM | ❌（云端） | ✅ Qwen2-1.5B | ✅ Qwen2-3B | ✅ Qwen2-7B |
| Layer 3 专用模型 | ⚠️ 仅 YOLO-nano | ✅ 完整 | ✅ 完整 | ✅ 完整 |
| Layer 4 云端兜底 | ✅ | ✅ | ✅ | ✅（可选） |

#### 6.4.4 升级触发条件（自动检测）

| 触发 | 检测 | 建议 |
|------|------|------|
| Layer 2 推理延迟 > 3s | LLM 路由层持续监控 | 升级到 L2 硬件或切云端 |
| Layer 3 推理延迟 > 500ms | 视觉管线监控 | 升级到 L3 硬件 |
| 月度云端 token > 50 元 | 配额监控 | 升级 L2 硬件 |
| 设备数 > 50 | 计数器自动检测 | 升级到 L3 / L4 |
| 摄像头 ≥ 4 路 | 视觉负载监控 | 升级到 L4 硬件 |

#### 6.4.5 LLM 路由决策表（与 §5.1 联动）

| 任务类型 | L1 入门 | L2 推荐 | L3 舒适 | L4 升级 |
|---------|---------|---------|---------|---------|
| 简单对话 | 云端 | 本地 1.5B | 本地 3B | 本地 7B |
| 工具调用 | 云端 | 云端 | 本地 3B | 本地 7B |
| 视觉理解 | 云端 | 云端 | 云端 | 本地 14B |
| 兜底推理（§53.4.3） | 云端 | 本地 3B | 本地 7B | 本地 14B |
| 规则引擎判定 | 本地 | 本地 | 本地 | 本地 |

#### 6.4.6 关键不变式

- **Layer 1 规则引擎永远本地**——保证 family 离线可用
- **Layer 4 云端不可用时降级到 Layer 3**——不依赖单一供应商
- **任何硬件升级必须保证可降级**——L4 → L1 都应能工作（功能子集）
- **月度云端成本 > 100 元 / 家庭 → 触发硬件升级评估**

## 7. 风险与后续攻关项（v2.10 刷新）

| 风险 | 优先级 | 对应章节 | 解决时机 | 说明 |
|------|--------|---------|---------|------|
| 小米音箱语音接入 | 🔴 高 | §5.6 / §36 | E2 之后 | 官方不开放，需研究 `miservice` / `mi-gpt` 等社区方案 |
| **PWA 在 LAN HTTP 下不可用（v2.10 F3）** | 🔴 高 | §30.0 | **E0 必须** | SW/Push/Install 都需 HTTPS；未配 TLS 全部降级 |
| **PWA LAN 免鉴权 = 访客可开锁（v2.10 F4）** | 🔴 高 | §5.8b | **E0 必须** | 必登录机制（passkey/PIN/设备绑定 token）|
| **缺无 LLM 降级模式（v2.10 F5）** | 🔴 高 | §42 | **v0.1 第一个里程碑** | 没 key 就用不了 → 完整子集不依赖 LLM |
| **P2 单一 policy 表缺位（v2.10 F12）** | 🔴 高 | §47 | E0-E1 之间 | 不实现就 §14/§24.2/§31.2 持续打架 |
| **§37 三源对 mesh 锁不可达（v2.10 F8）** | 🟡 中 | §37 | E1-E2 | mesh 设备 LAN 源结构性缺失 |
| **§28 L2 跑 7B 工具调用延迟爆炸（v2.10 F9）** | 🟡 中 | §28.3 | E0 | 实测 N100 3-6 tok/s 不可支撑工具循环 |
| **household_id 全栈串无迁移设计（v2.9 子代理 A）** | 🟡 中 | §45 | 升级到 v0.5 | readings 不加列；余表迁移停机 30-60min |
| **adapter 无沙箱/凭据保管（v2.9 子代理 A）** | 🟡 中 | §23.6 | E4 之前 | 服务代办能花钱但无信任模型 |
| **per-member 账号风控/审计冲突（v2.9 子代理 A）** | 🟡 中 | §29 | E1 | 1 主账号 + 可选成员账号；账号选择确定性 |
| **safety 告警可被静音策略吞掉（v2.10 F14）** | 🟡 中 | §14 | E0 | 必须定义 alert_class + safety 不可静音不变式 |
| **手机在网作为第三源不可靠（v2.9 子代理 A）** | 🟡 中 | §37.1 | E1 | 弱证据；优先物理信号 |
| 微信渠道（v2.19 决策 B：不做） | ⚪ 已转出 | §10 / §53.12 | v3+ | 详见 §10 v2.19 修订 |
| 阶段 2 本地模型工具调用 | 🟡 中 | §5.1 | E3+ | 本地模型 function-calling 弱，prompt 工程补偿 |
| 门锁事件标准化 | 🟡 中 | §5.4 | E1 | 走 spec 自动发现，型号无关化（v2.3 起已有底）|
| **节假日表 100% 准确不可承诺（v2.10），且需 is_official 列（v2.15 新增）** | 🟡 中 | §35.1 | E2 | 改为"已公布年份+周末降级+手动补录"|
| **内置节假日表非中国用户缺位（v2.10）** | 🟢 低 | §35.1 | E3 | 按 country code 加载 |
| **起步 Rank1"京东 API"实际不存在（v2.10）** | 🟢 低 | §23.5 | E4 | 改为用户提供链接/截图 |
| **v0.1 范围膨胀（v2.10 子代理 A）** | 🟡 中 | §27 | 持续 | 收敛为最小闭环：采集+查询+硬告警+低危控制+规则模式 |
| **多语言与中文 prompt 绑定（v2.10）** | 🟢 低 | §32 / §39 | E3 | UI i18n 与 prompt pack 区分 |
| **E0-E2 时间估算过于乐观（v2.10）** | 🟢 低 | §27 | 持续 | 删具体周数 |
| 高频轮询对设备压力 | 🟢 低 | §28.3 | E0 | 自适应降频 |
| DeepSeek R1 能力边界 | 🟢 低 | §5.1 | E0 | R1 不支持 function calling，已在 §5.1 明确 |
| **"30 秒启动"对慢 NAS 不成立（v2.10 F21）** | 🟡 中 | §40.2 | E0 | 改为分级就绪：15 秒只读+LAN控制就绪 |
| **LLM 成本硬熔断缺位（v2.10）** | 🟡 中 | §28.3 / §42 | E0 | daily_token_budget + monthly_cost_cap |
| **隐私合规总览缺位（v2.10 F-43）** | 🟡 中 | §43 | E1 | GDPR-style 数据导出/遗忘权/未成年人 |
| **备份与灾备总览缺位（v2.10 F-44）** | 🟡 中 | §44 | E0 | RPO/RTO 指标 + 灾备等级 |
| **设备模拟器与测试策略缺位（v2.10 F-46）** | 🟡 中 | §46 | E0 | CI 必跑；开源贡献门槛 |
| **错误处理"timeout 第三态"（v2.15）** | 🟡 中 | §5.6b | E0 | done=true/false/timeout 三态；撤销乐观快照 + 撤销窗 ≥30s |
| **高危控制预动作无审计（v2.15）** | 🟡 中 | §5.3 | E0 | 严格两阶段：pending_confirm 后才允许动作；禁止预 RPC |
| **本机 NTP 漂移无校验（v2.15）** | 🟡 中 | §40.1 | E0 | 启动健康检查加 NTP offset ≤30s；>5min 黄灯 |
| **DST 切换日边界语义模糊（v2.15）** | 🟡 中 | §7b | E0 | 使用 civil_from_utc 而非 utc_from_local |
| **磁盘满 / WAL 膨胀 / readings 超限无降级（v2.15）** | 🟡 中 | §16 | E0 | 状态灯加三条触发 + 自动 checkpoint + 旧备份清理 |
| **LLM 配额仅月度，缺两档（v2.15）** | 🟡 中 | §28.3 | E0 | daily_token_budget 24h 滚动 + monthly_cost_cap 月度硬熔 |
| **升级 rollback 与 docker 协调缺位（v2.15）** | 🟡 中 | §45.3 | E0 | pre-migration 镜像 tag 保留 + 6a-6e 顺序执行 |
| **二进制与 schema 兼容矩阵缺失（v2.15）** | 🟡 中 | §45.1 | E0 | binary < schema 拒绝启动 + 提示升级 |
| **LLM 调用栈 trace_id 缺失（v2.15）** | 🟡 中 | §18 | E1 | autonomous_decisions.trace_id 串联 prompt/tools/control |
| **per-region 米家账号路由缺位（v2.15）** | 🟡 中 | §29.1 | E1 | 商旅/海外家庭单 NAS 多 region token |
| **长断期 catch_up 累积（v2.15）** | 🟡 中 | §30.4 | E0 | 断 24h+ 禁用 catch_up + 黄灯；告警不追溯 |
| **服务凭据无沙箱（v2.15）** | 🟡 中 | §23.3.5 | E4 | per-adapter 加密 + 进程隔离 + 凭据轮转 |
| **跨文档引用无前缀（v2.15 一致性）** | 🟢 低 | 全文 | E0 | 已批量加 §<FILE> 前缀（14 处）|
| **v0.1 v1.0 升级路径未定义（v2.10 F-45）** | 🟡 中 | §45 | E0 | 破坏性升级预告 + 自动回滚 |
| **老人专属对话模式缺位（v2.13）** | 🔴 高 | §38.6 | E2 | 6 项老年可用性设计：字体/对比度/方言/语音优先/慢节奏/Undo |
| **跌倒检测误报→医疗级事故（v2.13）** | 🔴 高 | §38.7 | E2 | 三级告警 + 误报控制 + 显式声明"辅助非医疗" |
| **痴呆场景无机制（v2.13）** | 🔴 高 | §38.8 | E2 | 5 类场景 + 温和提醒 vs 自动兜底 + 认知衰退分级 |
| **远程子女访问无 PWA TLS 同级隐私设计（v2.13）** | 🔴 高 | §38.9 | E2 | 4 档权限 + 双因素 + 时间窗 + 异地告警 + 5 分钟撤销 |
| **care_proxy 角色 + 多老人轮值缺位（v2.13）** | 🟡 中 | §38.10 | E3 | 保姆/护工场景 + 主照护者选举 + 轮值 |
| **医疗接口与慢病数据接入（v2.13）** | 🟡 中 | §38.11 | E3 | 血压/血糖/心率 + 用药清单联动 + 不替代医生 |
| **多人共用 PWA 无快速切换（v2.14）** | 🟡 中 | §51.3 | E2 | A+C 默认组合：摄像头自动切换 + 公共模式 |
| **声纹识别策略需文档化（v2.14）** | 🟡 中 | §51.4 | E2 | 默认禁用 + 5 硬约束 + P3 远期考虑 |
| **同位置多人在场细分缺失（v2.14）** | 🟡 中 | §51.5 | E3 | 3 信号叠加（蓝牙信标 + 时间窗口 + 设备活跃度）|
| **访客账号无生命周期（v2.14）** | 🟡 中 | §51.6 | E2 | 4 类型 + 24h 自动清理 + 跨家庭清单 |

## 7b. 时间与时区契约（v2.4 明确）

> 开源项目要服务多时区家庭，不能把"今早 8 点"按 UTC 理解——作息学习会完全错。一次性定清楚。

**入库格式**：所有 `ts` 列（readings/events/chat_history/presense/alerts 等）一律 UTC ISO8601 字符串：`YYYY-MM-DDTHH:MM:SS.ssssssZ`。示例：`2026-07-30T12:34:56.789012Z`。

**展示格式**：转换到 `home.timezone`（默认 `Asia/Shanghai`，开源用户必填）。当 PWA 展示 / Agent 内部 reasoning / alerts 通知文案 都用本时区。

**DST 切换日边界语义（v2.15 明确）**：
- 使用 **`zoneinfo` 库的 civil_from_utc 函数**（而非本地时间反推）——避免春季 02:00 跳到 03:00 时"今天 03:30"归哪一天的二义性
- 习惯基线 / 节假日判断 / 补跑窗口 / "昨日/今晨/今晚" 描述 —— 全部以 `home.timezone` 的 civil_from_utc 计算
- 跨时区家庭（v2.13 §39.2 per-member tz）：每个 member 用自己的 civil_from_utc，告警时间戳按 member tz 显示

**全局配置**：`config/default.yaml`

```yaml
home:
  timezone: Asia/Shanghai      # IANA 时区，必填
  locale: zh-CN                # 文案 / 数字格式
  start_of_day: "04:00"        # "今天"从早 4 点起（家庭作息常跨午夜）
  # 海外用户例：
  # timezone: Europe/Berlin
  # start_of_day: "05:00"
```

**辅助语义规则**：

- "今天"以 `home.start_of_day` 为界，避免作息学习把凌晨 1 点算昨天
- 工作日/周末判断用本时区（避免 DST 漂移）
- DST 转换由 Python `zoneinfo`（标准库 3.9+）处理，**不在业务代码里手动算**
- 设备 RTC 时间一律不用作决策依据（云端 API 给的 ts 是权威）

**展示层职责划分**：

| 位置 | 用什么时区 |
|------|----------|
| SQLite `ts` 列 | UTC ISO8601 |
| API JSON 响应 | UTC（带 `ts_local` 字段给前端转） |
| DeepSeek 喂入的快照 | home.timezone（叙述性时间，如"今早 8 点开门"） |
| PWA 用户看到 | home.timezone |
| 告警推送 | home.timezone（"今早 8 点你家客厅水浸报警"） |
| 日志文件 | UTC（不换时区，便于跨时区排错） |

**校验**：`myhome-agent doctor --time` 启动时报告当前 `home.timezone` 与 `datetime.now()` 转换是否一致，不一致则报警（用户可能没安装 tzdata）。

## 8. 实施路线（MVP → 完整）

> **v2.2 修正**：阶段 1 原标"已部分完成"但现有 `agent/core.py` 仍是 v1 的 Claude 单 provider，未接 DeepSeek、无调度层、无身份/上下文预算。如实标为"待按 v2.2 重构"。

| 阶段 | 主题 | 验收标准（用户可观测） | 阻塞依赖 |
|------|------|---------|---------|
| **P1：MVP 闭环** | 采集+存储+DeepSeek agent+调度层+PWA+硬规则告警+（v2.6）首装向导/RBAC/场景原子性/状态灯/backfill/自主审计/成员绑定 | ① PWA 能走完五步首装向导 ② RBAC 矩阵生效（孩子控不了门锁） ③ 场景部分失败给三种策略选项 ④ 状态灯🟢🟡🔴正确切换 ⑤ `backfill` 拉补事件可发可用 ⑥ 自主行为能在 PWA 回看 ⑦ 邀请配对流程 TG 验证 ⑧ 上云 payload 100% 过 redactor ⑨ 控制指令 100% 过反馈环 ⑩ 任一硬规则触发能告警 | DeepSeek API key、米家账号 |
| **P2：本地 LLM 路由** | Ollama 接入、分级路由、场景建议 MVP | 简单查询走本地月 <10 元云端成本；场景建议能生成并等审批 | 硬件型号确认 |
| **P3：渠道扩展** | Telegram / 企微 / PWA 多渠道 + 身份映射 | 多渠道并发能识别各自成员；权限校验生效 | §10 微信决策项 |
| **P4：语音攻关** | 小米音箱本地语音网关 | 唤醒后指令在 3s 内送达 agent；回复 TTS 回放 | 持续攻关 |
| **P5：完善** | 数据分层清理、多品牌插件、移动 APP | SQLite 自动聚合策略生效；第二品牌接入 ≤5 天 | 视用户反馈 |

### 8.1 阶段退出标准（DoD）

每个阶段结束都要满足：

- [ ] 该阶段文档承诺的能力全部上线
- [ ] 集成测试覆盖该阶段关键路径
- [ ] 安装/部署 README 更新到当前阶段
- [ ] 至少一次在自己家和 1 个开源用户家跑通

### 8.2 整体返回定义（开源门槛）

任意以下条件都判为不能发布到开源：

- 上云数据未经 redactor 处理：失败 1 次
- 高危控制绕过了二次确认：失败 1 次
- 控制指令发出但状态未校正：失败 1 次
- 启动后 30 分钟内有未恢复的 CRITICAL 日志：失败 1 次
- 任何路径能写入设备 token 到日志/事件：失败 1 次

### 8.5 v2.19 决策 C：v0.1 实施起点 = E2 LLM 网关

> v0.1 第一个里程碑选 **E2 LLM 网关**而非 §42 规则模式——理由是先把"对话链路"打通，再回头做规则引擎能更快验证完整端到端。

#### 8.5.1 为什么先 E2（而不是 E0-0 §42 规则模式）

| 路径 | 优势 | 风险 |
|------|------|------|
| **E0-0 规则模式**（v2.11 推荐） | 不依赖 LLM、可离线 | 看不到 LLM 对话价值，demo 效果弱 |
| **E2 LLM 网关**（v2.19 决策） | **对话链路**最亮眼、demo 强、可验证"语音 ↔ 管家"全链路 | 依赖 DeepSeek key（key 缺则降级到 §42） |

**决策理由**：
1. **价值可见**：LLM 网关能讲清楚"管家和米家 App 的本质差异"——demo 给亲友看有冲击力
2. **风险可控**：E2 不阻塞 §42；§42 规则模式已在 §53 完整设计，**v0.1 同步落地**
3. **降级完整**：DeepSeek key 缺时，E2 自动降级到 §42 规则模式
4. **后续衔接**：E2 完成后，E3 老年守护 / E4 服务代办 / E5 视觉管线 都依赖对话链路

#### 8.5.2 v0.1 范围（4 大块）

```
E2-A LLM 网关核心
  - DeepSeek Chat 接入（OpenAI 兼容协议）
  - 上下文组装（5.9 预算）
  - 工具调用（capability 表）
  - PWA 对话 UI（最小）
  - 反馈环（5.6b）

E2-B 渠道兜底
  - Telegram bot 双工
  - WebSocket fallback
  - PWA 离线缓存

E2-C 规则引擎 v0.1（§53 子集）
  - 4 张表 + 迁移
  - DSL 解析器
  - 5 条系统预设
  - 1 个最小 PWA 调试面板

E2-D 老年守护 v0.1（§38 子集）
  - 老人活动异常规则
  - 跌倒检测推送
  - caregiver 通知链路
```

#### 8.5.3 验收标准（DoD for v0.1）

- [ ] PWA 打开可对话："客厅灯开了吗？" → 管家查后回答
- [ ] 一句话控制："把客厅灯关了" → 反馈环返回 → 状态灯更新
- [ ] 5 条规则在 1 小时内能配置、触发、记录、反馈
- [ ] 老人活动异常 30 分钟内触发告警 → 推 caregiver
- [ ] Telegram 断线 5 分钟 → PWA 仍可对话
- [ ] DeepSeek key 缺 → 自动降级 §42 规则模式
- [ ] 在自家 + 1 个外部家庭（贡献者）跑通
- [ ] README 部署文档更新到 v0.1

#### 8.5.4 预计工期

| 块 | 工期（单人） | 备注 |
|----|-------------|------|
| E2-A LLM 网关 | 2-3 周 | DeepSeek 接入 + 工具调用 |
| E2-B 渠道兜底 | 1 周 | TG + WS |
| E2-C 规则引擎 v0.1 | 1-2 周 | §53 落地 |
| E2-D 老年守护 v0.1 | 1 周 | 复用规则引擎 |
| 集成 + 测试 | 1-2 周 | 双家庭验证 |
| **合计** | **6-9 周** | 单人全职 |

#### 8.5.5 不在 v0.1 范围（明确划开）

- ❌ 视觉管线（摄像头本地推理）—— v0.2
- ❌ 服务代办（外卖 / 维修）—— v0.3
- ❌ 微信渠道—— v3 治理后
- ❌ 多家庭 NAS 集群—— v2.18 限制 ≤3 家庭足够
- ❌ 跨生态（Tuya / Hue）—— v1.0 plugin marketplace
- ❌ 移动原生 App—— v1.0

## 9. 架构专题文档（详版拆开讲）

> 主文档保持精简，以下是各专题的深入设计。改动时请同步更新对应专题文档。

| 专题 | 文件 | 解决的问题 |
|------|------|-----------|
| 可观测性 | [docs/OBSERVABILITY.md](docs/OBSERVABILITY.md) | 日志、指标、追踪、报警 |
| 鲁棒性 | [docs/RELIABILITY.md](docs/RELIABILITY.md) | 重试、限流、宕机恢复、任务队列 |
| 迁移升级 | [docs/MIGRATION.md](docs/MIGRATION.md) | 换路由器/换账号/换设备时怎么平滑过渡 |
| 多品牌插件 | [docs/PLUGINS.md](docs/PLUGINS.md) | 后续接入涂鸦/华为/HomeKit 的扩展机制 |
| Schema 详细字段 | [docs/SCHEMA.md](docs/SCHEMA.md) | 每张表/视图的完整字段定义 |
| PWA UX 流 | [docs/UX_FLOWS.md](docs/UX_FLOWS.md) | 向导、配对、空状态、成员切换、降级状态灯（§13/§16/§19 配套）|
| 服务代办抽象 | [docs/SERVICES.md](docs/SERVICES.md) | §23 服务 adapter 的接口契约与安全设计（v2.7）|
| 家务领域数据 | [docs/HOUSEHOLD.md](docs/HOUSEHOLD.md) | §22 items/calendar/health/finance 的领域模型（v2.7）|
| 规则引擎 DSL | [docs/RULES.md](docs/RULES.md) | §53 跨信号推理规则引擎 DSL 完整手册（v2.19 新增）|

这些文档和 ARCHITECTURE.md 一起构成本项目的完整架构契约。

## 11. 外部依赖失败降级矩阵

> v2.4 新增。开源项目对外部库的稳定性没有承诺——`python-miio` / `micloud` / `fastapi` / DeepSeek SDK 都可能突然停更或出 bug。这一节明确每个依赖挂了之后我们怎么降级。

| 依赖 | 用途 | 失败模式 | 降级方案 | 影响半径 |
|------|------|---------|---------|---------|
| `python-miio` | 局域网 miio 协议 | 协议变动/库停更 | 切换到直发 UDP 包 + 维护自己的 miio 客户端（参考其源码） | 通道 A（局域网控制）失效，可只用云端通道 |
| `micloud` | 登录米家云端 | OAuth 失效 / 库不更新 | 切换到手工 script（`miio cloud dump`）；或社区分叉替代 | sync_from_cloud 失败，token 失效 |
| `fastapi` / `uvicorn` | HTTP / Web 服务 | 大版本升级破坏 API | 锁小版本，或 plan B 退回 aiohttp | PWA 与外部渠道不可用 |
| `openai` SDK (兼容模式) | DeepSeek API 调用 | SDK 改协议 → 调用失败 | 自己手写 4 个 HTTP 调用（messages/stream/tools 不复杂） | agent 不可用，collection 照旧 |
| DeepSeek API | LLM 推理 | 5xx / 配额耗尽 | **切 §42 规则模式**（v2.10.1 优先）；最差用规则模式兜底 | 对话降级，但查询/控制/告警仍可用 |
| `python-miio` 控制 | 子设备类型差异 | 新型号支持不全 | spec 自动发现 + 用户配置兜底（§5.7b） | 单设备不可用 |
| SQLite | 持久化 | 文件损坏 | PRAGMA integrity_check 启用 + 日备份回滚（§RELIABILITY §5） | 全局停服（5 分钟内） |

**依赖被弃用后的回退动作**（用户应能按 README 步骤完成）：

1. 备份 `myhome.db` 和 `.env`
2. 升级到新版本，看 CHANGELOG 是否有 BREAKING
3. 跑 `myhome-agent doctor` 命令：列当前兼容性、缺失依赖、自动迁移评估
4. 数据迁移走 MIGRATION.md 的 schema 版本机制

## 10. 需要用户最终确认的待定项（v2.10.1 同步）

- [x] **门锁型号**：小米智能门锁 M4 Pro（2026-07-30 确认，详见 §5.4）—— 但 §5.4 设计已型号无关化，此项作参考实例
- [x] **文档拆分**：B1 经 B 组评估暂继续保留在主架构（综合考虑维护成本），后续如有外部贡献者反馈再拆
- [x] **部署形式**（v2.5）：Docker Compose 为主、systemd 为可选项（详见 §RELIABILITY §6.1）
- [x] **用户视角缺口**（v2.6）：已补 §13-§21
- [x] **管家定位层**（v2.7）：已补 §22-§27
- [x] **部署前必拍板 5 项 A 类**（v2.8）：硬件自适应 / per-member 账号 / 完整 PWA / 人设默认 / MVP 能力矩阵——已决策并写入架构
- [x] **B 类 7 项**（v2.9）：远程/节假日/搬家/防幻觉/多代/多语言/断电恢复——已决策
- [x] **v2.10 阻塞修复 + 缺失章节**（v2.10）：12 项 + 4 章——已写入
- [x] **v2.10.1 审核修订**（v2.10.1）：R1-R12 已修
- [x] **v2.11 精细化**（v2.11）：20 中 + 20 低 严重度，已写入
- [x] **E0 颗粒度**（v2.7 + v2.10 已建议 §27.2 E0-0~E0-20）：v2.11 推荐 **仅 E0-0~E0-8 启动**（v2.19 决策 A 确认，§27.4 已明确）
- [x] **E0/E1 同步/串行**：v2.11 推荐 **并行**（v2.19 决策 A 确认）
- [x] **首推方向**：v2.19 决策 C 改为 **E2 LLM 网关**（v2.11 推荐 E0-0 已被取代；详见 §8.5）
- [x] **微信渠道方案**：v2.19 决策 B——**不做**（个人微信协议 2023 起高风险，企业微信需要企业主体，第三方 iPad 协议功能强但随时封号）。v0.1 落地后用 Telegram 兜底；v3 治理框架成熟后（预计 v2.21+）再考虑企业微信。详细见 §53.12 修订注记
- [x] **本地模型硬件预算**（v2.19 决策 C）：**分层方案**——轻量本地（N100 8GB）+ 复杂走云端 / 升级路径 RTX 3060 12GB。详见 §6.4
- [x] **v0.1 实施起点**（v2.19 决策 C）：**E2 LLM 网关**（先打通对话链路）。详见 §8.5

**远期（记下但不阻塞 v0.1-v1.0）**：

- 5 年后兼容性（旧 Python / 过期 SSL / 模型过时）—— 不在架构设计范围，靠 README 长期维护
- 社区与生态（plugin marketplace / 第三方 adapter review 流程）—— v2.x 之后考虑
- 多家庭/多语言/数据遗忘权/跨 timezone —— **v2.10 + v2.10.1 已写入** §36/§39/§43/§34.4，**不再是"远期"**，是 v0.5-E7 路线图里的项
- 完整人格与年度回顾（§25.5 + E9）—— 长期

## 13. PWA 首装向导流（v2.6 新增）

> 新用户拿到系统后**没有任何线索**，PWA 默认 URL 是多少？第一步去哪？23 台设备怎么归房？这就是首装向导要解决的。

**五步强制流程**（PWA 路由强约束，未走完无法进入主界面）：

```
Step 1: 欢迎 + 检测（自动）
        ↓
Step 2: 米家账号绑定（输 username/password，跑 sync_from_cloud）
        ↓
Step 3: 设备房间分配（自动启发式预分组 + 用户确认/调整）
        ↓
Step 4: 家庭成员登记 + 关联设备登记
        ↓
Step 5: 门锁 lock_key_map 登记（仅当家庭有锁时出现）
        ↓
完成 → 进入主仪表盘
```

**Step 3 启发式预分组**（v2.6 新增，自动给建议）：
- spec.type=light 且名字含 `卧室/客厅/厨房` → 直接归该房间
- spec.type=light 名字含糊（如 `light_v2`）→ 归入 `未分配` 等用户拖拽
- 用户可单选/拖拽/批量确认
- API：`POST /devices/{id}/assign-room`

**回退路径**：用户在中途退出 → 下次打开 PWA 仍在上次那步，不重新开始。

**Sync 失败处理**：Step 2 若 fail（账号错/网络挂）→ 不阻塞向导，提示"先去 settings 配米家账号"，用户可以从其他路径进入主界面后看到明显 banner 提醒"未同步设备，agent 不会服务这些设备"。

**Step 5 提示来源**：从 devices 表里 type=lock 自动列出锁，每把锁展示 spec.events 中 has_actor_id=true 的类型枚举（"fingerprint 1-9, password 1-N, key a/b/c"），让用户填映射。

## 14. 成员 RBAC 权限矩阵（v2.6 新增，v2.10.1 标注为默认种子）

> §5.8 提了"角色"，但没说每种角色能做什么。这节是把权限**落到表格**，不可省略。
>
> **v2.10.1 重要标注**：**v2.10 起，本表是 `policies` 表（§47）的默认种子快照**。权威表是 `policies`；本表是初始 seed。**用户在 PWA `/settings/policies` 修改后，实际行为由 `policies` 表决定——本表与实际行为可能不一致**。
>
> **v2.10.1 角色扩展**：新增 `assisted_adult`（被守护成人，受限权限）和 `care_taker`（可代看守护对象数据，不继承 adult 全权限）。详见 §47.7。

**预定义角色**：

| role | 含义 | 默认人数 |
|------|------|---------|
| `admin` | 管理员（首装者自动成为） | 1+ |
| `adult` | 成年人 | 多 |
| `child` | 儿童（<14 岁） | 0+ |
| `guest` | 访客（临时在家） | 动态 |

**默认权限矩阵**（用户可在 settings 调整；PWA 提供可视化编辑）：

| 设备类型 / 动作 | admin | adult | child | guest |
|--------------|-------|-------|-------|-------|
| 灯 / 开关 | ✅ | ✅ | ✅ | ✅ |
| 空调 / 调温 | ✅ | ✅ | ❌ | ✅ |
| 摄像头 / 看画面 | ✅ | ✅ | ❌ | ❌ |
| 摄像头 / 转动/对讲 | ✅ | ❌ | ❌ | ❌ |
| 门锁 / 开锁（高危） | ✅（需二次确认） | ✅（需二次确认） | ❌ | ❌ |
| 门锁 / 反锁 | ✅ | ❌ | ❌ | ❌ |
| 燃气阀 / 开关（高危） | ❌（系统级锁定） | ❌（系统级锁定） | ❌ | ❌ |
| 告警规则 / 创建/删除 | ✅ | ❌ | ❌ | ❌ |
| 告警规则 / 确认 | ✅ | ✅ | ❌ | ❌ |
| 场景 / 创建 | ✅ | ✅ | ❌ | ❌ |
| 场景 / 执行 | ✅ | ✅ | ✅ | ✅ |
| 成员管理 | ✅ | ❌ | ❌ | ❌ |
| 系统设置 | ✅ | ❌ | ❌ | ❌ |
| 配置 Redactor 规则 | ✅ | ❌ | ❌ | ❌ |
| 看 chat_history | 自己的 | 自己的 | 自己的 | ❌ |
| 看 events / alerts | ✅ | ✅ | 受限 | ❌ |
| 同步/删除自己数据 | ✅ | ✅ | ❌ | ❌ |

**实现**：`myhome_agent/authz.py`，收到控制指令后查 `member × action → bool`。和 §5.3 渠道分级**正交**：先 RBAC 再渠道分级。

**角色派生**：默认 admin=首装者。其他用户注册时**默认** adult，admin 手动改；新增成员字段 `auto_role`（`invite` 时可填）。

**新增访客**：admin 在 PWA 点"+访客" → 生成临时凭据（含绑定 QR/TG link），过期默认 24h，可调。访客离线后自动清理。

**关键不变式**：燃气阀关闭 `/api/devices/{id}/control gas` 任何渠道任何角色都拒绝（双系统级保护）。

## 15. 场景原子性与部分失败（v2.6 新增，v2.16 补 scenes 表定义）

> §5.5 写了"执行已批准的场景"，没说**失败时怎么办**。半截场景对用户不可理解，必须定义。
>
> **v2.16 重大修订**：§5.0b ER 图（L525）和 §27.2 E0-12 都引用了 `scenes` 表，但全文从未定义。scenes.yaml 是声明式文件，**场景定义必须存 DB**（重新发现 / 跨设备同步 / 备份恢复都有用）。

**scenes 表定义**（v2.16 新增）：

```sql
CREATE TABLE scenes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  household_id INT NOT NULL,        -- §36.6 A 类 DIRECT
  name TEXT NOT NULL,                -- '睡觉模式' / '回家模式'
  description TEXT,
  definition JSON NOT NULL,          -- 步骤 + 失败策略 + dry_run 标志
  enabled INTEGER DEFAULT 1,
  created_by INT,                    -- 创建者 member_id
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (household_id) REFERENCES households(id) ON DELETE CASCADE
);

CREATE INDEX idx_scenes_household ON scenes(household_id);
```

**场景定义扩展**（DB 中的 `definition` JSON 字段）：

```yaml
# scenes.definition 示例
- name: 睡觉模式
  steps:
    - { device_id: "dev_abc", action: off, label: "客厅灯" }      # v2.16 修订：步骤寻址改 device_id + 保留 label 作展示
    - { device_id: "dev_def", action: close, label: "客厅窗帘" }
    - { device_id: "dev_ghi", action: on, brightness: 30, label: "卧室夜灯" }
    - { scene_id: 2, action: trigger, label: "关闭所有空调" }     # v2.16 新增：可嵌套场景
  on_partial_failure: rollback | skip | ask_user
  dry_run_required: true
  triggers:                          # v2.16 新增：除手动触发外的自动化入口
    - { kind: schedule, cron: "0 23 * * *" }     # 23:00 自动
    - { kind: event, event: "person_arrive_home" }
    - { kind: eureka, threshold: 14 }             # 14 天习惯后建议
```

**v2.16 关键修订：步骤寻址改 device_id**（旧 YAML 用 `device:客厅灯` 中文名寻址——设备改名/换 NAS 重新发现后必断）。label 仅作展示，运行时按 device_id 解析。兜底：device_id 失效时按 room + capability 模糊匹配并提示用户。

**v2.17 新增：capability 依赖检查（dry_run 阶段）**

```
每次场景执行前预检：
  1. 对每个 step（device_id + action）：
     - 查 devices.spec_cache.actions[i].disabled？      # §5.7b v2.16 实测降权
     - 查 capabilities.deprecated？                    # §5.7b v2.16 spec 删除
     - 查 devices.online？                              # 设备在线
     - 查 devices.spec_fetched_at &gt; 7 天？           # spec 太旧（token 过期 / 风控中）
  2. 任一不通过：
     - dry_run_required=true → 标步骤 ⚠ + PWA 提示"场景 X 步骤 Y 设备能力失效"
     - 不阻止执行（用户主动批准可继续）；写 events.kind='scene_capability_drift'
  3. 全部通过 → 进入正常执行流程

执行流水（每步独立 transaction）：
  ...
```

**三种失败处理策略**：

| 策略 | 行为 | 适用场景 |
|------|------|---------|
| `rollback` | 已执行的步骤反向回滚（开→关；调到原始） | 关键场景（睡觉、外出） |
| `skip` | 已执行的保留，跳过失败步骤继续 | 弱一致场景（起床、回家） |
| `ask_user` | 暂停，发 PWA 推送"步骤 2/4 失败：客厅窗帘。您想：① 重试 ② 跳过 ③ 回滚全部" | 复杂场景、不想自动化破坏 |

**`dry_run_required=true`**：执行场景前**先空跑一次（dry run）**，只检查设备可达性、参数合法性，给出"可执行性报告"。用户确认才真跑。

**执行流水**（每步独立 transaction）：

```
开始场景（开始 execution_id）
  ↓
dry run（无副作用检查）
  │
  ├─ 失败 → 写 alerts 表 "场景 dry-run 不可执行"+ 停止
  │
  ▼
执行 step 1：控制 device 1 → 反馈环校验
  ├─ 成功 → 写 events detail={step:1, exec:xxx}
  ├─ 失败 → 按 on_partial_failure 策略处理
  │
  ▼
... 后续步骤
  │
  ▼
所有步骤完成
  ↓
  √ rollback=true 且部分失败 → 逆序执行反向 actions
  ↓
  √ 全部 done → 用户群发 "睡觉模式执行成功 / 部分成功"
```

**实现**：`myhome_agent/scenes/executor.py`，事务级 rollback 由 反馈环保证（同 §5.6b）。

**数据库**：`scene_executions` 表（详见 SCHEMA 扩展）：

| 列 | 用途 |
|----|------|
| `id` | execution_id |
| `scene_id` | |
| `status` | `running` / `done` / `partial` / `failed` / `rolled_back` |
| `strategy` | 记录的策略 |
| `started_at` | |
| `finished_at` | |
| `steps_json` | `[{step, status, started, finished, error}]` |

## 16. 系统状态灯 / 降级可视化（v2.6 新增）

> §RELIABILITY §7 矩阵提到降级，但是**静音降级对用户不可察觉**。本节定义状态灯 + PWA UI。

**三态系统健康**：

| 状态 | 含义 | 颜色 | PWA UI |
|------|------|------|--------|
| 🟢 健康 | 所有模块正常 | 绿 | 顶栏不出现警告 |
| 🟡 降级 | 部分功能受限 | 黄 | 顶栏一行，列哪些功能受限 + 预计恢复（如"DeepSeek API 5xx，将自动重试"）|
| 🔴 异常 | 关键不可用 | 红 | 顶栏 + 立即推送通知到所有渠道 |

**触发逻辑**：

```
观测（每分钟）：
  - sync_from_cloud 最近 30 分钟 ≥1 成功 → 通道 B 健康
  - 任一在线设备最近 5 分钟 ≥1 poll 成功 → 网络层健康
  - LLM 最近 5 分钟无错误 → LLM 健康
  - SQLite last_vacuum < 30 天 → 健康
  - **本机 NTP offset ≤30s（v2.15 新增）→ 时钟健康**
  - **磁盘剩余 ≥5%（v2.15 新增）→ 备份与归档可写**
  - **SQLite WAL 文件 <1GB（v2.15 新增）→ 写入无堆积**
  - **过去 24h readings 写入量 < 阈值 20 万行（v2.15 新增，§1b 上限）→ 时序未爆**
  
任一不满足 → 状态灯降级为黄/红（按级别表）

例：
  - LLM 挂了但采集正常 → 黄
  - **磁盘 <5% → 红（自动紧急 checkpoint + 旧备份清理）**
  - **readings 超阈值 → 黄（自动开启增量 retention）**
  - **NTP offset >5 分钟 → 黄（routines/告警时间戳可能错位）**
  - LLM 挂 + SQLite 写失败 → 红
  - 单台设备 5 分钟无响应但其他正常 → 黄（不影响全局）

**v2.18 关键修订：健康检测自身的失效兜底（防"假装正常"）**

```
obs/health.py 是状态灯唯一 owner，必须自身 60s 心跳一次：
  - health 自身协程每 60s 写一次 events.kind='health_self_heartbeat'
  - 检测机制：自身读 events 表找最近心跳
    - 若距上次 &gt; 90s（连续 2 次缺失）→ 强制显示 🟡 + 写 events.kind='health_self_stale'
    - 状态：第 3 类状态（无法判断自己健康）—— 不可沿用旧缓存值
    - PWA 显示："管家健康检测本身已失效，请人工检查"（v2.18 新增）

§4 模块树 obs/health.py L283 加 v2.18 注记：
  - 健康检测是 L1 关键基础设施
  - 不允许"静默失败"——任何失败路径必须产生可见信号
```

**PWA 实现**：顶栏 status pill + `/api/health` 端点供 PWA 轮询。

**透明性原则**：
- 网络断 2 小时恢复后，PWA 顶栏 5 分钟显示"过去 2 小时断网，部分云端数据缺失"（参考 §17）
- LLM quota 90% 用了 → 黄灯 + 设置项显示"建议升级 LLM 套餐"
- 数据库写入失败历史 ≥1 → 红灯 + alert + CRITICAL log

**避免错误风暴**：同一警告 5 分钟内不重复刷出（§OBSERVABILITY §5.3 复用）。

## 17. 数据缺口补录 / backfill（v2.6 新增）

> §MIGRATION §10 说 RPO 24h。但**网络/云端断期间的数据永久缺损**对家庭决策敏感——比如今天网络断 30 分钟，期间 5 次门锁开门事件云端有但本地缺。架构必须给"补录"出口。

**`backfill` 命令**：

```bash
myhome-agent backfill --since 2026-07-29T00:00:00Z --until now --device-type lock
```

**行为**：
- 对时间窗内云端能查到的设备（门锁、传感器、摄像头事件），拉云端历史补 events 表
- 拉到的写 events，detail 里带 `backfilled: true` 标记（区别于实时事件）
- 时序 readings 不补（本地丢失无数据可补）
- 已补录的开始 24h 内 PWA 顶栏显示"过去 X 条事件来自补录"

**前置条件**：

- 必须走云端（local miio 无历史概念）
- 设备类型必须云端支持事件历史（部分锁只支持近期 30 天）
- 受 micloud 速率限制（status 字段返回有时间窗）

**实现位置**：`myhome_agent/backfill.py`，编排 collectors/cloud_api 的历史拉接口。

**PWA 可视化**：在 events 表 detail JSON 中渲染 `🔄 已补录` 标记。

## 18. 自主行为可审计性 / autonomous_id（v2.6 新增）

> 用户问"agent 为什么自动开了灯"答不上来，发生在 agent **自主触发** 的任何动作（不是用户直接说的）。

**与 request_id 区别**：

| id 类型 | 触发者 | 例子 |
|---------|--------|------|
| `request_id` | 用户直接请求（聊天/音箱） | "我睡觉了" → 触发睡觉模式 |
| `autonomous_id` | agent 自主决策 | 异常推送、场景自动触发、定时任务（早晨唤醒） |

**自主行为清单**：

- schedule 触发的定时（"晨间报告 7:30 推送"）
- analytics 检测异常（"凌晨 1 点还在动，检查有人是否正常"）
- 设备信号驱动场景（"全家外出超 2 小时自动切离家"）
- 成员回 home 事件触发的快捷操作
- agent 内部 eureka："检测到你们家总是睡觉前开夜灯，要不要我自动开"

**每次自主行为记录**：

| 字段 | 含义 |
|------|------|
| `autonomous_id` | UUID（链路追踪） |
| `trigger_kind` | `schedule` / `anomaly` / `event` / `eureka` |
| `trigger_reason` | "今日无活动超 4h" / "全家外出超过 2h" |
| `evidence_path` | 引用 events / readings 的 ts/event id |
| `decision_chain` | LLM reasoning（如果有）或 rule chain |
| `trace_id` | **v2.15 新增**：串联 LLM 调用栈（prompt / tools / completion / control），便于排查"为什么推理这么慢/这么烧钱" |
| `actions_taken` | 触发的控制 / 推送 / 场景动作 |
| `review_status` | `pending` / `approved` / `rejected`（用户对决策的评价） |

**用户问"为什么"路径**：
- PWA "审计"面板列出近期 autonomous 事件
- 点开看完整 decision_chain + evidence_path
- 用户可点 👍（从此类似场景自动执行）/ 👎（拉入黑名单）

**数据库**：`autonomous_decisions` 表（见 SCHEMA 扩展字段）。trace_id 串联 §OBSERVABILITY §7。

**权限**：
- 默认所有成年 admin 可见
- 孩子 partial 可见（只看触发不含 LLM reasoning）
- 客人不可见

## 19. 成员首次绑定流程 / 配对 link（v2.6 新增）

> "弟弟从自己 TG 发消息给 agent"，系统不知道让不让进。需要"邀请配对"流程。

**配对流程**：

```
管理员 PWA / 终端:
  $ myhome-agent invite --role=adult --channel=telegram --member-name "弟弟"
  
输出: 
  Pairing link: https://<host>:8000/pair/abcd1234 (有效 5 分钟)
  或: 用 PWA QR code 打印给家人扫描

家人:
  通过 TG bot 输入 /pair abcd1234
  或 PWA 上扫 QR 进入 confirm 页
  
系统:
  验证后 member.channels.telegram 填入 user_id
  角色来源：邀请时的 --role 参数
  events 写 "member_bound" via which channel
```

**撤销/转交**：admin 可在成员列表解除绑定，绑定失效（TG 还能聊但不通过 RBAC）。

**超时**：默认 5 分钟，admin 也可在配置里改。

**失败模式**：
- 过期 link → 用户重试
- 双重邀请 → 后到的拒绝 + 提示管理员
- 角色不在白名单（自邀请）→ 拒绝

**实现**：`myhome_agent/auth/invite.py`，`invite_codes` 表：

| 列 | 用途 |
|----|------|
| `code` | 配对码（短 key） |
| `inviter_member_id` | 谁邀请的 |
| `target_role` | 推荐角色 |
| `target_channels` | 哪个渠道（telegram / wechat / pwa） |
| `expires_at` | 过期时间 |
| `used_at` / `bound_member_id` | 使用记录 |
| `revoked` | 是否被撤销 |

## 20. 设备归房间 / 启发式（v2.6 新增 §13 Step 3 配套细节）

> §13 Step 3 启发式预分组的实现细节。

**来源**：

| 信号 | 权重 | 例子 |
|------|------|------|
| 设备名匹配房间关键词 | 0.7 | "客厅灯" → 客厅 |
| 设备类型 + 位置信号 | 0.5 | type=ac 且 名含"主卧" → 主卧 |
| 米家 APP 里的房间标签 | 0.9 | sync_from_cloud 带 room 字段 |
| 用户历史分配（已分配则保持）| 1.0 | 之前归客厅，再次分配仍归客厅 |

**未分配处理**：
- 仅在 Step 3 显示
- 进入主界面后这些设备归入"未分配"区块，PWA 顶栏 yellow badge 提醒仍有 N 台未分配
- 设备轮询和告警照样跑（未分配不阻断正常服务）

**启发式可关闭**：settings 里 `auto_room_assignment: false` 完全手动。

## 21. 长期对话语义 / `memories` 全文检索（v2.6 新增）

> §5.9 控制聊天输入，但"上周说冰箱牛奶没了——现在有没有"这种提问当前答不上来。要么 FTS5 全文，要么阶段 2 接 embedding。

**P1 方案：SQLite FTS5 全文索引**：

```sql
CREATE VIRTUAL TABLE chat_fts USING fts5(
  content, member_name UNINDEXED,
  content='chat_history', content_rowid='id'
);
-- trigger 同步写
```

**查询工具** `recall_semantic(query)`：
- 先 LIKE 命中（快，便宜）
- 没命中 → 限流提醒"该问题需要 embedding 索引（阶段 2）"
- 永远不把全文 prompt 注入 LLM（只命中后注入匹配行）

**P2 方案**（阶段 2）：接 embedding 模型（Ollama 内置 m3e / BGE-small），向量存储用 `sqlite-vec`，混合 BM25 + 向量检索。

**P1 暂行限制**：仅最近 90 天对话有全文索引（v2.16 修订：与 §43.1 90 天保留对齐；旧版写 30 天是不一致残留）；90 天外的"语义查询"暂答不上来——已通过 §OBSERVABILITY §6 事件可见性兜底。

## 22. 家务领域：管家要"心里有数"的家底（v2.7 新增）

> 一个真正的管家不只懂灯和空调，他/她要知道冰箱里有什么、奶奶的药快吃完了、孩子下周一生日要订蛋糕。这层是管家"对家彻底的了解"。

### 22.1 领域清单（4 个核心 + N 个可选）

| 领域 | 启用方式 | 数据来源 | 隐私敏感度 | 是否进 P1 |
|------|---------|---------|----------|---------|
| **家居物品** `household.items` | 默认开 | 手动 + 设备（冰箱传感器/扫码） | 中 | ✅ 是 |
| **家事日历** `household.calendar` | 默认开 | 手动 + 对话录入 | 低 | ✅ 是 |
| **健康档案** `household.health` | 显式开启 | 手动 + 可穿戴设备 | **高** | ❌ P2+ |
| **家庭账本** `household.finance` | 显式开启 | 手动 + 银行 API（可选）| **高** | ❌ P2+ |
| **关系图** `household.relations` | 默认开 | 手动 | 中 | P2 |
| **宠物 / 车 / 收藏** | 显式开启 | 手动 + 设备 | 低-中 | P3+ |

**v2.17 新增：health 启用后的事件约定（§22.1 之前未声明）**

```
health 领域启用后，会产生三类事件（v2.17 明确）：
  1. events.kind='health_metric', detail={metric, value, ts}
     → 写入 household_health_metrics（§38.11 §22.7）
     → 不上云 + 必加密（§43.1 表格）
  2. events.kind='health_anomaly', detail={metric, threshold, value, ts}
     → §52.1 routing 走 safety 等级（永不汇总 + 阶梯升级）
     → §43.1 表行归属：household_health_* 删成员时级联删除（与 §43.3 步骤 7.5 联动）
  3. events.kind='medication_reminder', detail={drug, schedule_at, taken}
     → §22.4 物品过期扫描联动
     → 提醒未被 ack 30 分钟 → §52.6 ladder attempt 2（care_taker 通知）

§5.11 上云脱敏规则扩展：
  - health_metric：原始数据不上云，仅"近 7 天趋势"摘要可上云（§5.11 类目）
  - health_anomaly：级别（normal/warning/critical）可上云，原始数值不上云
  - medication_reminder：药物类别可上云，剂量/频次不上云

显式声明（v2.17 加注）：管家不替代医疗决策（§23.6）—— 仅通知 + 提醒 + 显示。
```

### 22.2 数据模型与既有 §5.0b 的关系

每个领域一张主表 + 一张事件表（主表存当前态，事件表存状态变迁）：

| 表 | 主字段 | 备注 |
|----|--------|------|
| `household_items` | id, name, category(食物/药品/电子/衣物/其他), location(冰箱/药箱/车库), expires_at, quantity, unit, source(手动/设备), owner_member_id?, updated_at | 食品/药品过期告警驱动 |
| `household_item_events` | item_id, event_type(入库/出库/过期/消耗), delta, ts, source | 物品全周期跟踪 |
| `household_calendar` | id, title, kind(缴费/接送/纪念日/医嘱/聚会), at(UTC), recurrence_rrule, owner_member_ids, related_devices?, reminder_minutes_before, notes | 与 devices.mac 解绑（事件 id 不一定对应设备）|
| `household_calendar_occurrences` | calendar_id, occurrence_at, status, ack_by, ack_at | 实例化每次发生（处理 recurrence 后的展开） |

可选领域（健康/账本）有独立表，本节不展开，定义在 [docs/SCHEMA.md](docs/SCHEMA.md) 末尾的"扩展领域表"章节（v2.12 修订：原 §17 与 ARCHITECTURE.md §17 重号）。

### 22.3 与设备管家的关系

```
            ┌─────────────────────────────┐
            │      家庭私人管家 agent       │
            │  （两轨合一 · 同一进程同一 UI）│
            └────────────┬────────────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
   ┌──────────▼────────┐    ┌───────▼──────────┐
   │  设备管家能力（L1-L4）│    │ 家务管家能力（L1-L4）│
   │  （§5-21 已实）       │    │  （本节 v2.7 新增）   │
   │  • 设备控制/自动化   │    │  • 日历/提醒         │
   │  • 硬件适配/告警    │    │  • 物品追踪/过期告警  │
   │  • 成员识别/场景    │    │  • 家人关系图         │
   │                    │    │  • 健康/账本（可选）  │
   └──────────┬─────────┘    └───────┬──────────┘
              │                     │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  数据底座（共享 SQLite） │
              │  • devices / readings │
              │  • members / presence │
              │  • household_items    │  ← v2.7
              │  • household_calendar │  ← v2.7
              │  ...                  │
              └─────────────────────┘
```

**关键设计**：**两轨合一（同一进程同一 UI）**，不分子项目和子域名——对用户来说这就是一个管家，它既会关灯又会提醒吃药。底层按需调能力模块即可。

### 22.4 P1 最小可用面

只启用"日历+物品"两个最低成本领域：

- **日历**：手动添加 + 对话录入（"管家，明天下午 3 点接娃放学"） + 提醒推送
- **物品**：手动 + 过期告警，冰箱传感器等设备能力暂不接（P2）

**物品录入 UX（PWA）**：扫条码 / 搜名 / 对话"管家我买了 XX 放冰箱，6 月到期" 三选一。

### 22.5 隐私分级

| 数据类别 | 管家默认可见 | 上云 | 端侧加密 |
|---------|------------|------|---------|
| 物品（不含品牌价格） | ✅ | 摘要 | 可选 |
| 日历（不带成员关系） | ✅ | 摘要 | 可选 |
| 健康 | ❌ 默认 | 仅本地 | 必选 |
| 账本 | ❌ 默认 | 仅本地 | 必选 |
| 关系图 | ✅ | 摘要 | 可选 |

**关键不变式**：健康/账本**默认不启用、不上云、即使本地也加密存**。管理员显式开启才进。

## 23. 服务代办：管家能"动手办成事"（v2.7 新增）

> 这一层把管家从"动嘴"升级到"动手"。当前架构（v2.6）的智能体只能控制米家设备；v2.7 起他/她可以调用外卖/电商/网约车/缴费等外部服务，把"帮你"做得更彻底。

### 23.1 服务目录与适配器

**核心抽象**：

```python
# myhome_agent/services/base.py
class ServiceAdapter(ABC):
    @property
    @abstractmethod
    def service_id(self) -> str: ...   # 'meituan' / 'gaode' / '12306'

    @property
    def display_name(self) -> str: ...

    @property
    def category(self) -> str: ...     # 'delivery' / 'transit' / 'utility' / 'shopping'

    @abstractmethod
    async def list_capabilities(self) -> list[Capability]: ...

    @abstractmethod
    async def query(self, intent: dict, ctx: Context) -> list[Option]: ...

    @abstractmethod
    async def execute(self, option_id: str, ctx: Context) -> Order: ...

    @abstractmethod
    async def track(self, order_id: str, ctx: Context) -> Status: ...
```

**启动加载**：

```
myhome_agent/services/
├── base.py             # 抽象
├── registry.py         # 注册中心
├── builtin/
│   ├── router.py       # intent → 服务路由
│   ├── finance_tracker.py  # 家庭账本读取（无对外执行）
│   └── calendar_orchestrator.py  # 跨日历编排（任务链）
└── adapters/           # 第三方服务（按需引入）
    ├── meituan/        # 外卖/生鲜（API + Cookie 登录）
    ├── gaode/          # 地图/打车（高德 API）
    ├── eleme/          # 饿了么
    ├── _12306/         # 火车票（按需爬虫，对接作者责任自负）
    └── ...
```

### 23.2 与设备管家的关系

服务代办**不是取代设备管家**，是**叠加层**：

| 维度 | 设备管家 | 服务代办 |
|------|---------|---------|
| 控制目标 | 局域网设备（确定性）| 云端服务 API（有网络/账号依赖）|
| 响应实时性 | 毫秒-秒 | 秒-分钟 |
| 失败成本 | 关灯失败 → 不亮 | 下单失败 → 没外卖吃/钱未付 |
| 决策权风险 | 低 | **中高（涉及金钱）** |
| 默认 dry_run | 否（直接控制，反馈环兜底）| **是（必须二次确认才真下单）** |

### 23.3 关键安全设计

**四道闸门**，缺一不可：

1. **预算闸门**：单笔交易 > ¥X 必须二次确认（X 默认 200，可在 settings 改）
2. **角色闸门**：孩子/访客**禁止**触发服务代办；guest 可被临时授权
3. **确认闸门**：代办的执行必须经过 §5.3 渠道分级（远程渠道确认更严格）
4. **审计闸门**：每个 order 都记录 autonomous_id，可回放，可撤销（pre-order 5 分钟内可取消）

**资金流程（无代理模式）**：
```
管家的 execute → 服务 API（用户已授权）→ 不经管家中转资金
管家只发出"下单"指令，钱从用户自己的账号走
管家本身不持有支付凭证，**零金融责任**
```

**v2.15 新增：§23.3.5 服务凭据沙箱**

管家"不持有支付凭证"是资金流不变式——但服务代办仍需要**非支付接入凭据**（美团 Cookie / 京东 API key / 12306 账号 / 高德 API key）。这些凭据的威胁模型与资金支付不同：

| 维度 | 支付凭证 | 服务接入凭据 |
|------|---------|------------|
| 例子 | 银行卡密码 | 美团 Cookie |
| 泄露后果 | 直接资金损失 | 账号被冒用下单 |
| 用户可改密码频率 | 低（要换卡） | 高（Cookie 失效快）|
| 攻击面 | 钓鱼为主 | API 滥用 + Cookie 复用 |
| 加密等级 | 必 | 必 |

**凭据沙箱设计**（v2.15 必加）：

```python
# mihome_agent/services/vault.py（v2.15 新增）

# 1. 凭据存 sqlcipher 加密表 service_credentials
CREATE TABLE service_credentials (
  id INTEGER PRIMARY KEY,
  service_id TEXT NOT NULL,          -- 'meituan' / 'gaode' / '_12306'
  member_id INT NOT NULL,            -- 该凭据归属成员
  encrypted_blob BLOB NOT NULL,      -- AES-GCM 加密的原始凭据
  per_adapter_key_id INT NOT NULL,   -- 引用凭据主密钥池（每 adapter 一主密钥）
  created_at TEXT NOT NULL,
  last_used_at TEXT,
  rotation_due_at TEXT,              -- v2.15 新增：定期轮转提示（如美团 Cookie 90 天）
  revoked INTEGER DEFAULT 0
);

# 2. per-adapter 主密钥池（v2.15 新增）
CREATE TABLE adapter_keys (
  id INTEGER PRIMARY KEY,
  service_id TEXT NOT NULL,
  key_version INT,                    -- 轮转版本号
  encrypted_master_key BLOB,         -- 来自系统主密钥（§RELIABILITY §5.1b）+ HKDF
  created_at TEXT NOT NULL,
  revoked INTEGER DEFAULT 0
);

# 3. 进程隔离（v2.15 新增）：adapter 跑在 subprocess
# 一个 adapter 漏洞不会拿到其他 adapter 的凭据
def execute_in_adapter_subprocess(adapter_id, order):
    proc = subprocess.run(
        ['python', '-m', 'myhome_agent.services.adapters.<name>.worker'],
        input={'order': order, 'credentials': decrypt_for_subprocess(adapter_id)},
        timeout=30,
        capture_output=True
    )
    # 凭据仅在 subprocess 内存中存在
    # subprocess 退出时内存清零
```

**4 个核心约束**：
1. **加密**：所有 service_credentials.encrypted_blob 必须用 SQLCipher（§RELIABILITY §5.1b）+ per-adapter 主密钥
2. **轮转**：rotation_due_at 触发 PWA 提示"美团 Cookie 即将过期，请重新授权"
3. **进程隔离**：每个 adapter 跑在 subprocess，主进程持有 master key，subprocess 内存中解密凭据
4. **审计**：service_credentials.last_used_at 记录每次使用，写 events.kind='credential_used'

**降级**：凭据过期/撤销时服务 adapter 自动禁用，events.kind='service_credential_expired'

### 23.4 "管家敢决定"的尺度（L1-L4）

见 §24。默认 L2（"建议+等批准"），用户可调高到 L3（"直接执行+通知"），**永不默认 L4**（无人监督的预决策）。除非显式 per-action 开启。

### 23.5 起步服务优先级

按"什么最值得被自动化"排序：

| Rank | 服务 | 痛点价值 | 数据源 | 上线难度 |
|------|------|---------|--------|---------|
| 1 | **家电食材比价** | 高（冰箱告警→自动比价推荐） | 京东/天猫/拼多多 API | 中（API 接入） |
| 2 | **缴费自动检测+跳转** | 中（每月自动查欠费→推链接） | 国家电网/自来水/燃气公众号 | 高（需政务接口） |
| 3 | **网约车编排** | 中（晚 9 点自动叫车接娃） | 高德/滴滴 API | 中 |
| 4 | **餐厅预订** | 低（生日订位） | 美团/大众点评 | 中 |
| 5 | **火车票/机票** | 中 | 12306/航司 | 高（反爬） |
| 6 | **网购代下单** | 低 | 京东/淘宝 | 中 |
| 7 | **快递追踪聚合** | 低 | 各家 API | 高 |

**P1 起步**：1 + 7 优先。

### 23.6 不做的事（v2.7 公开禁止列表，v2.17 修订：明确"safe-action 自动拨打"白名单）

管家**绝不**做：
- 涉及处方药、保健品、医疗诊断的动作（**只给号码，不替代医疗决策**）
- 法律咨询、金融投资建议（不替用户做金额决策）
- 涉及儿童/老人监护的代签字行为
- 任何"双向资金"代理（管家不持卡不碰钱）

**v2.17 新增：safe-action 自动拨打白名单**（v2.13 之前定义模糊，v2.16 §52.6 attempt 4 与 §38.2 矛盾导致）

管家**可以**在以下场景下自动拨号（不是医疗动作，是家庭紧急联络动作）：

```
白名单场景（v2.17 明确）：
  1. §38.2 老人语音"救命" + §38.7 Level 3 + §38.8 痴呆紧急求助 + §38.11 健康异常
     → 拨给 care_taker / primary contact / 子女（不是 120/110/119）
  2. §52.6 attempt 4 voice phone（同上，仅 safety 等级）
  3. §23.7 explicit safe-action 列表中由 admin 显式启用的动作
```

**白名单之外**（管家**不**自动拨的场景）：
- 急救中心（120 / 110 / 119）—— 仅显示号码 + 一键拨号按钮，**人工触发**
- 医疗咨询（任何形式的"代用户问医生"）
- 财务操作（任何形式的"代用户付款"）

责任边界声明：
- 管家对**白名单内的拨号**承担"通知 + 联系"责任
- 管家对**白名单外的拨号**不承担责任，仅提供号码
- 实际拨打 120 / 110 / 119 必须由人触发

这些边界在 persona.py 显式写入，PWA 设置里以"管家能力清单"展示给用户。

## 24. 管家自主等级：从"提示"到"代决定"（v2.7 新增，v2.10.1 标注为默认种子）

> 管家的自主等级不应该是 on/off 二元——不同场景、不同成员、不同风险应允许不同等级。这是把"决策权"工程化的关键设计。
>
> **v2.10.1 重要标注**：**v2.10 起，§24 等级定义 + §24.2 等级矩阵都是 `policies` 表（§47）的默认种子快照**。`policies.autonomy_level` 字段是权威；§24 矩阵是初始 seed。**用户在 PWA `/settings/policies` 修改后，实际自主等级由 `policies` 表决定**。

### 24.1 等级定义

```
L0: 告知 ─────────────────────────────────────  默认从 L0 起
    仅显示信息，不发起对话，无通知：
    "今晚气温降 5℃"
    
L1: 建议 ─────────────────────────────────────  当前常用
    主动发起对话，等用户决定：
    "今晚气温降 5℃，是否关窗？"
    
L2: 询问即执行（**所有非高危默认**） ─────────  v2.7 推荐默认
    把对话一并推进：
    "已查询；今晚关 30 分钟室温，预计省电 2 度。"
    + 我已关窗。 同时给 PWA 一条可撤销记录
    
L3: 直接执行+事后通知 ─────────────────────  用户显式开启
    不打扰，事后留痕：
    完成时推一条"晚上 23:00 已关窗 30 分钟（节省 2 度）"
    
L4: 预决策 ───────────────────────────────  永远不默认开启
    替用户做出决定，连通知都合并到日报里：
    早晨看日报才发现"昨晚又关窗了"
```

### 24.2 等级矩阵（默认）

| 场景 | admin | adult | child | guest |
|------|-------|-------|-------|-------|
| 关单灯、开关电源 | **L3** | L3 | L3（自己房间）| L2 |
| 关所有灯（场景） | L3 | L3 | L2 | L2 |
| 关窗/拉窗帘 | L2 | L2 | L2 | L2 |
| 调空调（自动温控） | L3 | L3 | L1 | L2 |
| **设备管家门锁开锁**（高危）| **L1 + 二次确认** | L1 + 二次确认 | ❌ | ❌ |
| **服务代办下单**（中介） | **L2**（默认 dry_run）| **L2** | ❌ | ❌ |
| **服务代办 大额**（>¥X）| L1 + 二次确认 | L1 + 二次确认 | ❌ | ❌ |
| 推送家人提醒 | L3 | L3 | L2（向家人推自己）| L2 |
| 发送对外通知（短信/微信）| L2 | L2 | ❌ | ❌ |

**policies 表存矩阵**，管理员可在 PWA 修改。

### 24.3 等级提升的安全保障

**L3 → L4 的硬约束**：
- 只能在 settings 显式开关，二次确认要输"启用 L4"
- L4 对每用户默认只对 admin 开放
- L4 决策要被日报聚合（"今晚 L4 决策 3 条，详见审计"）

**任何等级都需要审计**（§18 不变式），即使 L4 也要可回放。

### 24.4 LLM prompt 注入等级上下文

```
系统 prompt 片段（persona.py 维护）：
"你是一名家庭私人管家。当前自主等级：L2。
 - L2 含义：你做完事要回头告诉家人你做了什么，留痕。
 - 高危操作（门锁/燃气/大额）即使在 L2 下也必须先得到明示确认。
 - 涉及孩子时自动降到 L1。"
```

**myhome_agent/persona.py** 加载当前用户 × 当前场景的等级，prompt 动态注入。

## 25. 管家意识 / 人格：管家不只"做事"还要"有人味"（v2.7 新增）

> 长期使用的核心是用户喜欢这个"人"。人格不是装饰，是长期留存的关键。

### 25.1 五大人格维度

| 维度 | 默认 | 调节范围 | 实现 |
|------|------|---------|------|
| **称呼** | "管家"或 user-defined | 用户命名（"小家""米粒""Doby"） | `home.persona_name` |
| **温度** | 温和务实 | 冷淡 → 热情 | prompt 注入 `tone` 参数 |
| **主动性** | 中等（看场景）| 被动 → 主动 | 自主等级（§24） |
| **表达简洁度** | 平衡 | 短句 → 详细解释 | per-member `loc.concise` |
| **边界感** | 务实主义 | 不越界 → 偶尔劝阻 | 知识范围限制（不替用户做医疗决策）|

### 25.2 人格 vs 工具 — 边界守则

**管家可以做的态度表达**：
- 主动观察："我注意到这周奶奶出门特别早，可能有什么原因？"
- 主动提醒："今晚吃火锅，明天记得买青菜"
- 偶尔劝阻（基于规则）："今晚第 4 杯咖啡，要不要换成茶？"
- 自嘲："我今晚的网络不太好，说话慢了见谅"

**管家绝不做的态度表达**：
- 假装是人（不隐瞒 AI 身份）
- 不当心理医生（情感问题引导找专业）
- 不替决策（金额、医疗、人际关系大事件）
- 不无脑夸赞（不好的事情直接说不好）

### 25.3 学习与适配

管家**会主动记**家人对它的反馈（不靠用户手动设置）：

| 信号 | 收集方式 | 影响 |
|------|---------|------|
| 家人对决策点头/拒绝 | §18 `review_status` | 影响后续自主级别 |
| 家人经常不读某些报告 | 互动分析 | 自动降密 |
| 家人常用语偏好 | persona 模型 | 切换正式/口语 |
| 家人设置的"昵称" | persona.name | 影响称呼 |

**实现**：`myhome_agent/persona.py` 每对话根据 family profile 计算 persona state。

**v2.17 新增：衰减机制（memories 表 schema 已就位，§25.3 之前缺章节）**

```
memories.importance / last_recalled_at 字段已在 v2.16 schema 中（§43.1 矛盾修复时添加），
v2.17 正式接入 §25.3 学习循环：

衰减规则：
  - 每次 recall（§25.3 命中记忆用于对话注入）→ last_recalled_at = now
  - 每周日 04:00 调度：扫描 memories WHERE archived=0
    - importance &lt; 0.2 AND last_recalled_at &lt; now - 90 天
      → 标记 archived=1（不删，可恢复）
    - importance &lt; 0.1 AND archived=1 AND 90 天前
      → 真删（v0.5+ 才实现）
  - importance 更新：
    - 用户显式 remember() → importance += 0.2（上限 1.0）
    - 用户主动 recall() → importance +0.05（防止被冷落）
    - 用户 reject 某条记忆（"这个不对"）→ importance -= 0.3

用户可调：
  - PWA /settings/persona 调全局阈值（默认 0.2）
  - 单条记忆可手调 importance 或 archived
  - §43.3b forget_fact() 单条删除

persona_learn 不接衰减（仅元数据，无事实）：
  - persona_learn 仅记录"信号类型 + 时间戳 + member_id"（§43.3b v2.17 修订）
  - 用户偏好/事实都落到 memories 表，由 memories.importance 衰减
```

### 25.4 形式感

- **PWA 头像**：默认一个简洁图标，用户可上传
- **可选声音**：阶段 2 接入 voice
- **每日问候**：早晨一句"今天周四，全家都出门了 / 外婆今天药吃了吗？" 个性化（基于 presence / calendar）
- **每周回顾**："本周管家主动 23 次，其中你接受了 19 次，反对 1 次，跳过 3 次"

### 25.5 私密性

persona 的学习数据**和 chat_history 同级**——本地优先，脱敏后才上云分析。user_label / display_name 优先级与 §5.11 一致。

## 26. 管家与设备双轨总图（v2.7 终图）

```
┌─────────────────────────────────────────────────────────────┐
│                     家庭私人管家 (Agent Core)                   │
│   DeepSeek (默认) → §5.1 LLM 路由 → §24 自主等级 → §25 人格     │
└─────┬──────────────┬──────────────┬─────────────────┬────────┘
      │              │              │                 │
┌─────▼──────┐ ┌─────▼──────┐  ┌───▼──────┐  ┌───────▼──────┐
│ 设备轨道    │ │ 家务轨道    │  │ 服务轨道   │  │ 人格轨道       │
│ (米家)      │ │ (§22)     │  │ (§23)     │  │ (§25)         │
│  §5-21     │ │ 物品/日历   │  │ 外卖/缴费  │  │ 称呼/温度/边界 │
│  控制/告警  │ │ 健康/账本   │  │ 网约车/票  │  │ per-member    │
│  设备场景   │ │ 关系图     │  │ 全程审计   │  │ 自我学习       │
└─────┬──────┘ └─────┬──────┘  └───┬──────┘  └───────┬──────┘
      │              │             │                  │
      └──────────────┴─────────────┴──────────────────┘
                              │
                   ┌──────────▼──────────┐
                   │  自主等级 §24          │
                   │  L0/L1/L2/L3/L4      │
                   │  per (member × action)│
                   └──────────┬───────────┘
                              │
                   ┌──────────▼───────────┐
                   │  数据底座（共享 SQLite）│
                   │  • §5.0b 基础 +       │
                   │  • §22.2 家务表       │
                   │  • §23 services 注册   │
                   │  • §25 persona 偏好    │
                   └──────────┬───────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
        米家设备/云端        本地交互         PWA / 渠道
```

**两轨合一（不分子项目）**：用户看到的入口仍是 v2.6 §5.12 的七大区。管家的全部能力以"工具"形式被 agent 路由调用。

## 27. 分步实现路线（v2.10 完整映射 §28-§48）

> 用户已确认"先尽量完成设计规划"，未明确分几步实现。本节把 §0-§48 全部章节映射到 E 阶段，作为实施时的依据。
> **v2.10 刷新**：补齐 v2.8-v2.10 新增章节的归属（v2.7 原版 E0-E9 完全没覆盖 §28-§48）。

### 27.1 路线图全景

| 阶段 | 范围 | 对应章节 | 验收 |
|------|------|---------|------|
| **E0：基础设施 + 最小闭环（v2.12 顺序与 §27.2 E0-0~E0-8 对齐）** | E0-0 规则模式 → E0-1 DeepSeek → E0-2 调度 → E0-3 spec_normalizer → E0-4 redactor → E0-5 PWA 必登录 → E0-6 TLS → E0-7 备份 → E0-8 模拟器 | §42 / §5.1 / §5.0a / §5.7b / §5.11 / §5.8b / §30.0 / §44 / §46 / §48 | 没 key 也能用；家用闭环 |
| **E1：身份 + RBAC + 管家意识** | per-member 账号 / 单一 policy 表 / persona / 成员绑定 link / chat 语义 | §29 / §47 / §25 / §19 / §21 | 多人 + 多渠道可用 |
| **E2：家务基线 + 节假日** | items / calendar 展开 / 节假日表 / 老人守护 | §22 / §35 / §38 | 能加物品/加日历/过期告警 |
| **E3：服务代办骨架 + 自主等级 L1-L2** | §23.5 服务 1（用户提供链接/截图）+ §23.3 四道闸门 + §24 | §23 / §24 | 干跑场景能跑通 |
| **E4：场景原子性 + dry_run + 自主 L3** | scenes/executor + 多源验证 + 30/60s 撤销 | §15 / §37 / §18 | 误控制有兜底 |
| **E5：服务代办扩展 + 自主 L3 落地** | 缴费/打车/票务；L3 per 场景 | §23.5 / §24 | 用户能放心让管家夜里关窗 |
| **E6：健康/账本** | §22.1 显式开启 + 加密 + 全本地 | §22.4 / §43 | 奶奶血压异常能主动告知 |
| **E7：远程访问 + 多家庭 + 多语言** | tailscale/Caddy / household_id / per-member locale | §30.0 / §34 / §36 / §39 | 在外可访问；多代多语 |
| **E8：关系图 + 多场景联动** | §22 + §23 跨场景编排 | §22.6 / §23.6 | "明晚聚餐" = 餐厅 + 打车 + 日历 |
| **E9：完整人格 + 年度回顾** | §25 全 + 周年总结 | §25.5 | 一年后看"管家年度回顾" |

### 27.2 E0 实施路线（直接可动工）

| 步骤 | 主题 | 对应章节 | 交付 |
|------|------|---------|------|
| **E0-0** | **规则模式（v2.10 优先级最高）** | §42 | `agent/rule_mode/{intent,responses,actions}.py` + PWA 三态指示器 |
| **E0-1** | DeepSeek agent core | §5.1 | `agent/core.py` + `agent/router.py` |
| **E0-2** | 调度层 + catch_up | §5.0a / §48 | `scheduler.py` + `scheduled_tasks` 表 |
| **E0-3** | spec_normalizer 落代码 | §5.7b | `collectors/spec_norm.py` + `devices.spec_cache` |
| **E0-4** | redactor 强制脱敏 | §5.11 | `agent/redactor.py` + fixtures 测试集 |
| **E0-5** | **PWA 必登录** | §5.8b | `channels/auth/pwa.py` + passkey/PIN/设备 token |
| **E0-6** | **TLS 方案** | §30.0 | `mkcert`/`tailscale`/`caddy` 集成 + `/settings/tls` |
| **E0-7** | **备份与灾备** | §44 | `reliability/backup.py` + RPO/RTO 监控 |
| **E0-8** | **设备模拟器** | §46 | `tests/fixtures/fake_miio_server.py` + cloud_api_mock |
| E0-9 | 控制反馈环 | §5.6b | `collectors/registry.py` 加状态重读 + 本地快照回滚 |
| E0-10 | 五步首装向导 | §13 | `web/onboarding/*` + API endpoints |
| E0-11 | RBAC 矩阵（v2.16 修订：**直接建 policies 表**，不做临时版） | §14 / §47 | `authz.py` + `policies` 表（首次启动 seed 一次性导入 §14 矩阵，**只补不改**）|
| E0-12 | 场景原子性 + dry_run | §15 | `scenes/executor.py` + `scene_executions` 表 |
| E0-13 | 系统状态灯 | §16 | `obs/health.py` + `GET /api/health` + PWA pill |
| E0-14 | backfill 命令 | §17 | `backfill.py` + 拉云端历史 |
| E0-15 | 自主行为审计 | §18 | `autonomous_decisions` 表 + PWA 审计页 |
| E0-16 | 配对 link | §19 | `auth/invite.py` + `invite_codes` 表 |
| E0-17 | FTS5 全文 | §21 | `chat_fts` 虚拟表 + `recall_semantic` 工具 |
| E0-18 | 概念入门 + 非功能需求 | §0 / §1b | README + 测试集 |
| E0-19 | Docker Compose 主部署 | v2.5 Docker Compose 决策 | 文档 + 部署脚本 |
| E0-20 | 风险表 §7 高优先级（v2.12 修订：实际 5 条 🔴——F3 TLS / F4 PWA 必登录 / F5 规则模式 / F12 单一 policy 表 / 一条新发现 §36.6 一致性）全部处理 | §30.0 / §5.8b / §42 / §47 / §36.6 | 部署前必做 |

**v2.10 子代理 A 警告**：原 §27.2 "E0-1~E0-3 + E1，2 周可走完" 过于乐观。**E0-0 ~ E0-8（含规则模式 + 必登录 + TLS + 备份 + 模拟器）才是 v0.1 真正的 8 个最高优先级**——5 个新增（E0-0/5/6/7/8）必须先动。2 周仍可走完，但前提是**只做这 8 个**。

### 27.3 E0-E2 注意事项

- **E0-0 规则模式可最早交付**：不依赖任何 LLM；先做出 v0.1 demo
- **E0-1~E0-4 是基础设施**；E0-5~E0-8 是 v2.10 新增的硬约束——**没有这些直接 v0.1 会被 §7 高风险阻塞**
- **E0-20 高风险 4 条**（§30.0/§5.8b/§42/§47）必须 v0.1 前全部处理
- **E1 与 E0 并行**：persona.py 是纯 prompt 工程，不依赖其他代码
- **E2 不能跳过 E0**：家务轨道依赖设备轨道的存在（presence 推断、对话框架、推送渠道），否则从头做
- **E3 服务代办 E4 前必须有**：等级机制是代办的前提，没有 L1-L4 会失控
- **E6 健康/账本后置**：隐私 + 加密 + 多重确认，需要相对成熟的自主等级体系
- **E7 远程/多家庭/多语言** 可独立 E1/E2 之后做，不依赖 E3-E6
- **E8/E9 长期**——E6 实跑后再决定

### 27.4 拍板建议（v2.11：建议 ≠ 拍板，最终决策在 §10）

**v2.11 修订**：本节是**架构师建议**；最终决策在 §10 待定项（已标 `[/]` 半确认态）。本节不构成拍板。

**当前未定的 3 个分支决策**：

1. **E0 颗粒度**：v2.11 推荐 **E0-0 ~ E0-8**（8 个最高优先级）必做，E0-9 ~ E0-20 后续补
2. **E0/E1 同步/串行**：persona.py 是纯 prompt 工程，**可并行**；推荐基础设施（E0-0~8）+ 人格（E1）**同步做**
3. **先做哪侧**：v2.11 推荐**先 §42 规则模式（E0-0）**——这是"无 key 也能用"的关键，也是开源用户第一个能体验的功能

倾向建议：**E0-0~E0-8（基础设施 + 规则模式）**+ **E1（persona 并行）**先动；不承诺周数。

---

## 28. 硬件自适应策略（v2.8 A 类决策 1）

> **用户拍板（v2.8）**：**不挑硬件，agent 主体要适配从树莓派到高端迷你主机的多个级别**。
> 不同的硬件支持不同的本地模型，agent 启动时自动 probe runtime，决定能力档位。

### 28.1 硬件档位定义

| 档位 | 典型硬件 | RAM | 本地 LLM 可行 | 默认行为 |
|------|---------|-----|--------------|---------|
| **L0 - 极低** | 树莓派 4 / 4GB | 4GB | ❌ 不可行 | 全依赖 DeepSeek 云端；本地仅跑采集 + 调度 |
| **L1 - 低** | 树莓派 5 / 8GB | 8GB | Qwen2-0.5B / 1.5B 量化 | 意图分类/简单查询本地；对话/工具调用走云端 |
| **L2 - 中** | N100 小主机 / 16GB | 16GB | Qwen2-7B Q4_K_M | 日常对话本地；复杂多步推理降级到云 |
| **L3 - 高** | i5 迷你主机 / 32GB | 32GB | Qwen2-14B Q4_K_M | 几乎全本地；云端仅做兜底 |
| **L4 - 顶级** | AMD 7840HS / 64GB | 64GB | Qwen2-32B+ | 全本地，多模型并存 |

### 28.2 Runtime Capability Probe（v2.15 首次安装加 probe 优先）

启动时一次扫描，结果缓存到 `runtime_profile` 表：

```python
# myhome_agent/runtime/probe.py（v2.8 设计占位）

@dataclass
class RuntimeProfile:
    tier: Literal["L0", "L1", "L2", "L3", "L4"]
    ram_total_gb: float
    cpu_cores: int
    disk_free_gb: float
    gpu_available: bool
    local_llm: str | None        # "qwen2-7b" / None
    local_llm_endpoint: str | None  # "http://localhost:11434/v1"
    deepseek_available: bool
    supports_sqlcipher: bool
    supports_web_push: bool
    hardware_fingerprint: str      # 用于跨设备迁移校验


async def probe() -> RuntimeProfile:
    """启动时跑一次，结果缓存；启动间隔 ≥24h 才重跑。"""
    ...
```

**失败模式**：
- 探测脚本本身挂掉 → 兜底 tier=L0 + 红色状态灯（"无法识别硬件"）
- LLM 探测超时 → 默认走云端；UI 提示"本地模型未启用"

### 28.3 LLM 路由与档位联动（v2.7 §5.1 + v2.8 + v2.10 F9）

§5.1 路由决策表 + 档位决策（**v2.10 修订：基于实测 tok/s 而非 RAM**）：

| 任务类型 | L0 (≤2 tok/s) | L1 (≤6 tok/s) | L2 (≤15 tok/s) | L3 (≤30 tok/s) | L4 (30+ tok/s) |
|---------|---------|---------|---------|---------|---------|
| 简单查询（设备状态） | ☁️云 | 🏠本地 | 🏠本地 | 🏠本地 | 🏠本地 |
| 意图分类 | ☁️云 | 🏠本地 | 🏠本地 | 🏠本地 | 🏠本地 |
| **工具调用对话** | ☁️云 | ☁️云 | ☁️云 | 🏠本地 | 🏠本地 |
| 复杂推理（R1 级别） | ☁️云 | ☁️云 | ☁️云 | 🏠本地 | 🏠本地 |
| 长上下文摘要 | ☁️云 | ☁️云 | ☁️云 | 🏠本地 | 🏠本地 |

> **v2.10 F9 修订**：原写"L2 (N100) 跑 Qwen2-7B 流畅"是过度乐观——实测 N100 无 GPU 跑 7B Q4 约 3-6 tok/s，**带工具循环的对话动辄 30-90 秒**远超 §1b ≤3s 首字 SLO。**改为：除 L4 外，工具调用一律走云端**；本地只做"无工具短问答/意图分类"。这才能满足用户对智能体的实时性预期。

**关键不变量**：
- L0 树莓派用户**也能用**全套管家能力（依赖云端 + 规则模式 §42）
- L4 顶级用户**几乎不依赖云端**，隐私最大化
- 路由决策**用户可调**：在 PWA 设置里覆盖默认档位（"为了隐私，强制走本地"——会附带延迟警告）
- 实测 tok/s 由 §28.2 启动 probe 写入 `runtime_profile.local_tps` 字段

**硬熔断（v2.18 关键修订：per-household 配额）**（§5.9 之外的成本约束，v2.15 拆为两档，v2.18 改为按家庭记账）：

```
两档熔断：
- daily_token_budget（24h 滚动窗口）
  超限 → 全局自动回退 §42 规则模式
  滚动窗口：超过 24h 自动回退一部分配额
  例：每日 100k token 上限
  
- monthly_cost_cap（月度硬熔，月初 1 日 0 点重置）
  超限 → 自主调用拒绝（§24 L1-L4），用户主动调用仍允许但提示"配额告罄"
  PWA 顶栏倒计时显示"配额恢复：X 天 Y 小时"
  永久熔断态：用户调用也限（避免月底超支失控）
  
熔断期间体验：
  - PWA 顶栏 🟡 "当前规则模式 - LLM 配额告罄（恢复倒计时 5 天）"
  - 控制指令走 §42 规则模式兜底
  - 聊天请求返回"管家正在省电模式，今日配额已用完"模板
  
**v2.18 关键修订：per-household 配额（防"A 家烧光把 B 家一起熔断"）**

```
配额键从全局改为 (household_id) 维度：
  - daily_token_budget = monthly_cost_cap × (1 / N households)  // 默认均分
  - 各家庭独立计数器：household_token_stats(household_id, day, tokens_in, tokens_out, cost)
  - 任一家庭超限 → 只熔断该家庭；其他家庭不受影响

shared_pool 开关（v2.18 配置项）：
  - 默认：shared_pool=false（每家庭独立配额）
  - 设为 true：所有家庭共享单一计数器（v2.18 前行为，向后兼容）
```

自主 vs 用户调用分开计量：
  - 自主调用（§24 L1-L4 触发）受 daily_token_budget 限制
  - 用户主动调用（PWA chat / TG bot）独立计量
```

### 28.4 本地模型接入契约

阶段 2 实现，本节先定契约：

```python
# myhome_agent/llm/local.py（v2.8 设计占位）

class LocalLLMClient(_LLMClient):
    """通过 Ollama / vLLM 等 runtime 提供 OpenAI 兼容接口。"""

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url  # 默认 http://localhost:11434/v1
        self.model = model        # 用户配置的实际模型 tag
        # 其余与 _LLMClient 完全一致
```

**关键点**：Ollama 自带 OpenAI 兼容 `/v1/chat/completions`，复用 v2.7 的 `_LLMClient.messages()` 方法**无需改一行**。这是把路由层抽出来的好处。

### 28.5 硬件迁移

用户换硬件时：
- DB 可移植（`data/myhome.db` 是单一文件）
- runtime_profile 会自动重 probe
- 历史对话/记忆不受影响（仅跟 member + household 绑）

## 29. per-member 米家账号绑定（v2.8 A 类决策 2）

> **用户拍板（v2.8）**：**每个家庭成员独立绑米家账号**。每人用自己的米家账号，token 隔离。

### 29.1 数据模型扩展

```sql
-- v2.7 §5.0b members 表扩展
ALTER TABLE members ADD COLUMN mi_account_id INT;      -- 绑定的米家账号 ID（多账号）
ALTER TABLE members ADD COLUMN mi_token_encrypted BLOB;  -- 该账号 dump 出的 token 加密存
ALTER TABLE members ADD COLUMN mi_token_expires_at TEXT;
ALTER TABLE members ADD COLUMN mi_device_scope TEXT;    -- JSON：该账号下能看到的设备 ID 列表

CREATE TABLE mi_accounts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  member_id INT NOT NULL,
  mi_user_id TEXT,                -- 米家账号标识（脱敏）
  mi_region TEXT,                 -- cn / sg / us / tw / ru / de / in （v2.15 明确所有 7 个 region）
  encrypted_token_blob BLOB,      -- AES-GCM 加密的 token
  token_expires_at TEXT,
  last_sync_at TEXT,
  last_sync_status TEXT,
  created_at TEXT NOT NULL,
  INDEX idx_mi_accounts_region (mi_region)            -- v2.15 新增：按 region 路由索引
);
```

**v2.15 新增：per-region 路由**

单实例 NAS 服务多个家庭 / 多个区域账号的场景：

- **商旅家庭**（人在国外房子在国内）：同一 NAS 维护 cn + us 两套 token
- **跨国家家庭**（子女在国内 + 父母在海外）：同一 NAS 维护 cn + sg 两套 token
- **多个家庭共用 NAS**（同一硬件租给两家不同区域）：每家独立 token

**路由规则**：
```
sync_from_cloud 改为 per-region 并发（v2.15 修订）：
  - sync_from_cloud(mihome_region='cn') → 调用 micloud cn 端点
  - sync_from_cloud(mihome_region='us') → 调用 micloud us 端点
  - 每个 region 独立 sync_interval（避免一个 region 风控影响另一个）

collectors/cloud_api.py 改动：
  - MiCloudCollector 实例化时按 mi_region 选端点
  - poll / control / dump_token 都接受 mi_region 参数
  - 默认从当前 session member 的 mi_accounts.mi_region 推导

PWA 设备列表展示：
  - 设备名后加 region 标签（"客厅灯 [cn]" / "Living Lamp [us]"）
  - 控制指令按 region 路由到对应 token
```

**风控约束（per-region 独立）**：
- cn 风控与 us 风控是独立账户池——一个 region 触发风控不影响另一个
- 各 region 各自执行 §11 §RELIABILITY §4.1 限流矩阵

### 29.2 绑定流程

1. admin 在 PWA `/settings/accounts` 点"+ 绑定米家账号"
2. 输入账号密码 → 后端用 micloud 登录 → 加密存 token → 询问绑给哪个成员
3. 同步设备：把该账号下能看到的设备塞到 `mi_device_scope`

**关键原则**：
- token 永远不离开本机（存 SQLite 加密列）
- dump 出的设备 token 同样加密存（§5.6b + §RELIABILITY §5.1b 加密）
- admin 可看/解绑任何账号，adult 只能看自己绑的

### 29.3 设备可见性合并

一个家庭可能多账号共享同一台设备（如父母子三账号都"看到"客厅灯）：

- 同一物理设备在不同账号下的 miid 可能不同 → **按 LAN 接入 IP + MAC 做去重**（如果能拿到）
- 实在去重不了 → PWA 显示多份，由用户合并
- 控制时只需**任一**账号 token 可用就行（路由选最快的）

### 29.4 跨账号场景调用

```
管家要控制某设备 X：
  1. 查 devices.spec_cache.transport
  2. 若是 wifi+local_controllable → 用本地 token（不依赖任何账号）
  3. 若必须走云端 → 查 mi_device_scope，找一个未过期的 mi_account
  4. 该账号 token 用于调用
```

**轮转策略**：避免单一账号被频繁风控，每个调用随机选一个未过期的账号。

### 29.5 admin 失效场景

admin 密码改了 / token 失效：
- admin 仍能登录本机（米家密码 ≠ myhome-agent admin 密码）
- admin 控制的米家账号失效 → 该账号下的设备不可控
- **其他成员的账号完全不受影响**

## 30. 完整 PWA 形态（v2.8 A 类决策 3）

> **用户拍板（v2.8）**：**完整 PWA**——manifest + Service Worker + Web Push + 可装桌面。
>
> **v2.10 必读前提**：完整 PWA 要求 secure context（HTTPS 或 localhost）；§30.0 列出三种 TLS 方案（v2.11 修订：原 §30.5 错引，TLS 在 §30.0），**先配 TLS 再启用 §30 的 SW/Push/Install**。

### 30.0 TLS 与可信访问（v2.10 新增，F3）

**问题**：Service Worker、Push API、"安装到主屏"都要求 secure context（HTTPS 或 localhost）。§34.5 默认"不开公网端口、仅 LAN"，但 `http://192.168.x.x:8000` 不是 secure context——手机浏览器会**直接拒绝 SW 注册**与 Push 订阅。

**三种方案**（用户按场景选）：

#### 方案 A：内网自签 CA（推荐 NAS/小主机）

```
mkcert -install                              # 本机信任 CA
mkcert myhome.local 192.168.1.50             # 生成证书
nginx/caddy 反代 + certs 配置
PWA 域名：https://myhome.local:8443
```

- 优点：完全本地，零外部依赖
- 缺点：每台手机/电脑首次要导入 CA（家庭成员少则可接受）
- 工具：`mkcert` + `Caddy` 自动续期

#### 方案 B：Tailscale MagicDNS（推荐远程访问同时解决）

```
tailscale up                                  # 每台设备装 tailscale
# 自动获得 https://<machine>.<tailnet>.ts.net:443
# 自带证书 + 内网穿透 + Web Push 兼容
```

- 优点：HTTPS 自动解决；远程访问也搞定；手机装 tailscale client 即可
- 缺点：依赖 tailscale 账户（免费 100 台够家用）
- 适合：v2.8 §34 远程访问也用此方案

#### 方案 C：Caddy ACME-DNS（适合有公网域名）

```
myhome.example.com {
  tls {
    dns cloudflare {env.CF_API_KEY}
  }
  reverse_proxy 127.0.0.1:8300
}
```

- 优点：标准 HTTPS
- 缺点：需要域名 + DNS API key
- 适合：愿意暴露公网的家庭

**PWA 设置界面**：`/settings/tls` 让用户选方案 + 自动生成 `caddy`/`mkcert` 命令。

**降级**：未配 TLS 时，§30.2 SW / §30.3 Push / §30.5 Install **全部禁用**，PWA 显示黄色横幅"未启用 TLS，部分功能不可用"。基础访问（HTTP）仍可看仪表盘但功能受限。

### 30.1 PWA Manifest

```json
{
  "name": "myhome-agent — 家庭私人管家",
  "short_name": "管家",
  "description": "家里的私人管家，懂这家、办家事",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0a0a0a",
  "theme_color": "#1f6feb",
  "icons": [
    {"src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
    {"src": "/static/icons/maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}
  ],
  "categories": ["lifestyle", "utilities", "productivity"],
  "shortcuts": [
    {"name": "今天家里怎么样", "url": "/chat?preset=morning"},
    {"name": "已开门锁记录", "url": "/household/events?kind=lock"},
    {"name": "物品即将过期", "url": "/household/items?filter=expiring"}
  ],
  "share_target": {
    "action": "/share",
    "method": "POST",
    "enums": ["text/url"]
  }
}
```

### 30.2 Service Worker 策略

```
app shell:
   - /               → cache-first（HTML/JS/CSS）
   - /static/*       → cache-first（永久缓存）
   
API:
   - GET /api/*      → network-first，fallback to cache（最近一次家庭快照）
   - POST /api/*     → network-only，绝不缓存
   
实时:
   - WS /ws/*        → 直接穿透
   
推送:
   - Push API        → 通知触发 + 显示通知
```

**关键边界**：**写操作永不缓存**（control_device / memory.remember 等），保证不会"离线时执行了但云端不知道"。

### 30.2b 设备状态 WebSocket 广播（v2.16 补全）

> v2.16 修订：原 §5.12 ws/events 端点只在 README 提及，ARCHITECTURE 全文未定义消息 schema 和订阅模型。

**端点 + 消息**：

```python
# WebSocket /ws/state（v2.16 新增，与 ws/chat/ws/events 并列）
# 消息 schema:
{
  "type": "state_update",
  "household_id": 1,
  "device_id": "dev_abc",
  "snapshot": {
    "power": "on",            # 设备当前状态
    "brightness": 80,
    "last_changed": "2026-07-31T14:23:11Z",
    "freshness_seconds": 12   # 距上次 poll 的秒数
  },
  "triggered_by": {
    "type": "control",         # 'control' / 'poll' / 'manual'
    "by_member_id": 3,
    "by_channel": "pwa_local",
    "autonomous_id": null
  }
}
```

**订阅模型**：
- 默认：登录 member 加入 `household:{household_id}` WS room → 收到所有本 household 设备状态变更
- 选订（v0.5）：PWA 设置里可勾选"仅关心特定房间"——订阅 `household:{household_id}:room:{room}`

**触发条件**：
- §5.6b 反馈环 done=true 完成后广播
- §5.6b done=false 撤销乐观快照后广播
- 多设备并发（v2.16 §5.6b 新增）—— 任何一方控制后广播
- 60s 周期 poll 触发的状态变化（与"无变化则不广播"配对）

**陈旧度 UI 契约**（v2.16 新增）：
- 设备卡片右上角显示"X 秒前更新"（refresh 时钟 ≤5s 重置）
- X > 60s 标灰 + "上次同步 X 秒前"
- X > 300s 标黄 + 弹"长时间未更新"
- 离线/网络挂时显示"🔴 服务不可达"（§16 状态灯黄/红 + §30.4 离线模式）

**§30.4 SW 缓存修正**：
- SW 缓存 24h 旧快照时**必须**显示"缓存 - 24h 前"标签
- 写操作永不缓存（同 §30.2 关键边界）

### 30.3 Web Push 通知

依赖：VAPID 公私钥；订阅存 `push_subscriptions(member_id, endpoint, p256dh, auth)`

```
流程：
  PWA 启动 → 注册 ServiceWorker → 请求 push 权限 → 订阅 → 上报订阅到后端
  
  后端推送时：
    1. 选订阅（按 member 过滤）
    2. 加密 payload
    3. POST 到 endpoint（FCM / APNs / Mozilla autopush）
    4. 失败清理失效订阅
```

### 30.4 离线体验

| 功能 | 离线可用 | 降级 |
|------|---------|------|
| 看家庭快照 | ✅ | 读最近一次缓存 |
| 看历史事件/记忆 | ✅ | 读 SQLite（无需网络）|
| 与管家对话 | ❌ | 提示"网络不可用，试试本地缓存" |
| 控制设备 | 部分 | 局域网内能直连设备的仍可控；云端不可控 |
| 推送到其他成员 | ❌ | 排队等上线后发送 |

**v2.15 新增：长断期禁用 catch_up**

网络断 ≥24h 后启动：

```
判断条件：now - last_successful_sync > 24h
动作：
  1. 通知所有 admin 用户（"网络断 24h+，系统处于离线模式"）
  2. 禁用 catch_up=true 业务任务（holiday / medication / elder check-in）
     - 仅保留最近 24h 的 catch_up 触发
     - 累积堆积的 catch_up 标记为 skipped，写 events.kind='catch_up_skipped'
  3. 老人 check-in 场景改用"上次正常态快照 + 黄灯告警"——不依赖补跑
  4. 推送队列：调用 LLM 的请求排队等上线；本地控制可直连设备的照常
  5. 状态灯固定显示 🟡 + "离线模式"

恢复条件：网络恢复后首次 sync_from_cloud 成功
  - 黄灯自动消除
  - 但 catch_up 累积在断网期间仍不会被追溯执行
  - 仅在 24h 内的 catch_up 会被触发
```

**为什么不追溯**：
- 老人 7 天没吃药告警——追溯补发会让用户误以为"过去 7 天每天都在告警"，淹没真实告警
- 节假日判断——过去 7 天的判断已无意义（假日已过）
- 系统设计选择"**告警不该追溯**"，符合"告警是有时效性的"原则

### 30.5 安装体验（v2.10.1 R7 加注）

> **v2.10.1 前提**：本节所有安装步骤依赖 §30.0 TLS 已配（secure context 是 SW/Push/Install 的前提）。

- iOS Safari：分享 → 加到主屏（Safari 17+ 完整 PWA）
- Android Chrome：地址栏自动显示"安装"按钮
- 桌面 Chrome：地址栏右上角"安装 myhome-agent"
- 安装后从主屏启动 → 全屏 standalone，**无浏览器地址栏**

## 31. MVP 能力矩阵（v2.8 A 类决策 4）

> **用户拍板（v2.8）**：**安防/门锁/传感器、照明/温控/窗帘、小家电、摄像头/可视门铃**——4 大类全部纳入 v0.1 MVP 目标范围。

### 31.1 四类能力的 spec 自动归一化

每类设备在 §5.7b 的 spec 归一化框架下都有对应的"事件类型 + 指标 + 动作"清单：

#### 类 A：安防/门锁/传感器

```
指标：       离线/在线
事件类型：   door_unlock / door_lock / motion / water_leak / gas_leak / smoke / button / sos
动作：       远程开锁（高危+二次确认）/ 远程反锁 / 重启 / 校准
管家场景：   异常告警（水浸/燃气）、成员回家识别、夜间安全检查
```

#### 类 B：照明/温控/窗帘

```
指标：       brightness / color_temp / target_temperature / current_temperature / position
事件类型：   state_change（亮度/温度/位置变化）
动作：       set_power / set_brightness / set_color_temp / set_temperature / set_position / set_mode
管家场景：   作息联动调光、按房间自动调温、回家/离家模式
```

#### 类 C：小家电

```
指标：       battery / status / mode / filter_life / water_level
事件类型：   task_complete / error / consumable_low
动作：       start / pause / resume / stop / set_mode / find_device
管家场景：   扫地完成通知、耗材告警、过滤网更换提醒
```

#### 类 D：摄像头/可视门铃

```
指标：       online / sd_card_status / last_event_at
事件类型：   motion_detect / person_detect / doorbell_press / sound_detect
动作：       截图（cloud_url）/ 录像回放 / 对讲 / 灯效开关
管家场景：   门口有人推送、入侵告警（与门锁联动）、按成员在家时静音
```

### 31.2 capability 表（v2.8 新增，v2.10.1 标注为默认种子，**v2.16 改名 capabilities 并加 domain 列**）

> **v2.16 重大修订**：表从 `device_capabilities` 改名为 `capabilities`，加 `domain` 列。理由——§24.2 自主等级矩阵已有"服务代办下单 / 发送对外通知（短信/微信）/ 推送家人提醒"三行**非设备能力**；§23 另有独立 `Capability` dataclass。两套能力模型互不相认是 v0.1 实施第一周会撞的 FK 错误（§47 policies.capability_id FK → device_capabilities 会直接拒绝这三行）。

```sql
CREATE TABLE capabilities (
  capability_id TEXT PRIMARY KEY,        -- 'control_light' / 'read_lock_event' / 'service_book_ride'
  domain TEXT NOT NULL,                  -- v2.16 新增：'device' / 'service' / 'notify' / 'household'
  category TEXT,                          -- A/B/C/D（设备类目）或 'delivery' / 'transit' 等
  display_name TEXT,
  requires_role TEXT,                     -- JSON 数组，RBAC 兜底
  confirm_tier TEXT,                      -- 'none' / 'low' / 'medium' / 'high'
  irreversibility_tier TEXT DEFAULT 'reversible',  -- v2.18 新增：'reversible' / 'costly' / 'irreversible'
                                                      -- reversible: 可撤销（关灯、调温）
                                                      -- costly: 有金钱/信任代价（已下单、已发短信）
                                                      -- irreversible: 无法撤销（开锁后外人进入、燃气切断后无法恢复）
  description TEXT,
  created_at TEXT NOT NULL,              -- v2.16 新增：审计 + spec drift 检测
  updated_at TEXT NOT NULL
);
```

**v2.16 迁移**：rename table device_capabilities → capabilities + add column domain + add columns created_at/updated_at。

**域名映射**：
| 现有 capability | domain |
|----------------|--------|
| `control_light` / `read_lock_event` / `doorbell_screenshot` / `control_thermostat` 等设备类 | `device` |
| `service_book_ride` / `service_order_food` 等服务类（§23）| `service` |
| `send_wechat` / `send_sms` / `push_family_member` 等通知类（§24.2）| `notify` |
| `add_calendar_event` / `add_item` / `mark_medication_taken` 等家务类（§22）| `household` |

管家工具按 capability_id 暴露给 LLM，不暴露具体型号。
查询走 `policies` 表（§47），capabilities 是注册中心。

**§47.5 policies FK 同步更新**：FOREIGN KEY 仍 ON DELETE RESTRICT，但 §24.2 矩阵的非设备能力（service / notify）现在能注册了。

### 31.3 MVP 验收清单（v0.1 验收口径）

| 类别 | 验收项 | 覆盖设备类型数 |
|------|-------|----------------|
| A 安防 | 水浸/燃气/烟雾触发本地告警 + PWA 推送 | ≥3 类 |
| A 门锁 | 远程开锁走二次确认 + 开门事件回传 | ≥1 类 |
| B 照明 | 单灯开关 + 场景级"全关/全开" + 调光 | ≥2 类 |
| B 温控 | 空调开关 + 温度设置 + 模式切换 | ≥1 类 |
| B 窗帘 | 开关 + 百分比位置 | ≥1 类 |
| C 小家电 | 扫地机启动/暂停/回充 + 完成通知 | ≥1 类 |
| C 耗材 | 过滤网/水箱低时推送 | ≥1 类 |
| D 摄像头 | motion 触发推送 + 截图（云端） | ≥1 类 |
| D 门铃 | 门铃按下 → 多渠道推送 | ≥1 类 |

**开源后用户自家设备型号千差万别，验收不卡具体型号，卡"这 9 类能力覆盖度"**。

## 32. 管家默认人设（v2.8 A 类决策 5）

> **用户拍板（v2.8）**：**温和务实 + 名字可改**——默认称"管家"（或由用户在 PWA 改名），气质温和，口语化回应，做事靠谱。

### 32.1 默认 persona profile

```yaml
# config/persona_default.yaml（v2.8 设计占位）

persona:
  display_name: "管家"          # 用户在 PWA 可改
  alternate_names: []           # 昵称列表
  tone: "warm_pragmatic"        # 温暖务实档
  temperature: "medium"         # 中等
  verbosity: "balanced"         # 平衡
  formality: "casual"           # 口语化
  
  personality_traits:
    - "负责但不越界"
    - "观察细致但不黏人"
    - "幽默但不轻浮"
    - "主动但不专横"
  
  forbidden_behaviors:
    - "假装人类身份"
    - "代替用户做情感/人际决策"
    - "无脑夸赞"
    - "替用户签字/承诺"
  
  default_greeting: "今天家里{weather_summary}，需要我做点什么？"
  default_self_intro: "我是这家的管家{self.display_name}，已经在你家待了{days}天"
```

### 32.2 多渠道呈现差异

| 渠道 | 表达风格 | 示例 |
|------|---------|------|
| PWA 长回复 | 详细 + Markdown | "今天周X，客厅26℃湿度45%，无人在家..." |
| 微信短消息 | 极简 1-2 句 | "家里没人，灯全关了。" |
| 音箱语音 | 自然口语 | "嗯，客厅灯已经开了，要不要顺手把空调也打开？" |
| Push 通知 | 一行事实 | "🚨 厨房水浸告警" |
| 邮件日报 | 结构化 | "今日家庭管家报告：..." |

**实现**：persona.py 的 `format_message(intent, channel, content)` 按渠道适配。

### 32.3 名字和昵称的处理

- 用户 PWA 设置 `persona.display_name = "米粒"` → 管家所有对外消息自称"米粒"
- 不影响 `persona.id`（内部 ID 永远是 myhome_agent）
- 改名会触发一次内部事件（`events.kind='persona_rename'`），不刷数据库其他部分
- 家庭成员也可以给管家起私人昵称（如爸爸叫"小家"、孩子叫"管管"）——per-member override

### 32.4 人设学习与记忆隔离

人设的学习数据存在 `persona_learn(member_id, kind, value, ts)`，**与 chat_history 隔离**：

- 改名 / 改温度 → 写 persona_learn
- 不污染对话历史（搜索"管家"不会触发巧合）
- 删成员时自动清该成员的 persona_learn（GDPR-style）

> **v2.10.1 R11 加注**：删成员的**完整级联清单**（不只是 persona_learn）见 §43.3——本节假定"删成员时清 persona_learn"是 §43.3 流程的一部分。实施时按 §43.3 统一处理。

## 33. 文档导读路径（v2.8 C 类交付，v2.10.1 同步）

> 架构文档 v2.12 修订后已 3500+ 行 + 8 个专题文件 ~2700 行。新成员（包括 6 个月后忘记细节的自己）该按什么顺序读？

### 33.1 推荐阅读路径

```
1. README.md                       5 分钟    看清是什么
2. ARCHITECTURE.md §0 概念入门     5 分钟    名词扫盲
3. ARCHITECTURE.md §1-2 决策       5 分钟    看清"为什么这样定"
4. ARCHITECTURE.md §3 系统总览     5 分钟    看清"整体长什么样"
   ↑↑↑ 以上 20 分钟建立全局感 ↑↑↑

5. ARCHITECTURE.md §5.7 米家接合   5 分钟    看清"如何与硬件对话"
6. ARCHITECTURE.md §5.1 LLM 路由   5 分钟    看清"大脑怎么运转"
7. ARCHITECTURE.md §22-25 管家层  15 分钟   看清"管家的四轨 + 人格"
   ↑↑↑ 共 45 分钟理解核心设计 ↑↑↑

8. ARCHITECTURE.md §42 规则模式  10 分钟    看清 v0.1 第一个里程碑
9. ARCHITECTURE.md §47 policy 表  10 分钟    看清"单一权威"如何替换 §5.3/§14/§24.2
   ↑↑↑ 共 65 分钟理解 v2.10.1 核心稳定化 ↑↑↑

按角色继续读：
- 想部署  → §27 实施路线（E0-0~E0-20）+ §30.0 TLS 方案 + **§43 隐私合规 + §44 备份灾备 + §45 升级路径 + §48 调度补跑** + docs/RELIABILITY.md
- 想开发  → §4 模块边界 + §5 关键技术方案 全部 + §22-25 + §42 + §47 + docs/SCHEMA.md
- 想贡献  → §46 设备模拟器 + docs/PLUGINS.md + docs/SERVICES.md + docs/HOUSEHOLD.md
- 想做硬件适配 → §5.7b spec 归一化 + docs/PLUGINS.md §插件开发 + §46 模拟器
- 想接家庭生活 → docs/HOUSEHOLD.md + §22
- 想接外卖等服务 → docs/SERVICES.md + §23 + §23.3 四道闸门
- 想看工程一致性 → **§43 / §44 / §45 / §48**（v2.11 强化的 4 个工程保障章）
- 想评估可行性 → §7 风险表（30+ 条）+ §11 依赖降级矩阵 + §33 本节
- 想做合规/隐私 → §43 + §45 + §32.4（GDPR-style）
- 想看备份与灾备 → §44 + docs/RELIABILITY.md
```

### 33.2 索引表（按"想解决什么"反查）

| 我想搞清楚... | 看这里 |
|---------------|--------|
| 数据存在哪里 | ARCHITECTURE §5.0b + docs/SCHEMA.md |
| 设备怎么加进来 | ARCHITECTURE §5.7 + docs/PLUGINS.md |
| 管家怎么"思考" | ARCHITECTURE §5.1 + §24-25 + agent/core.py |
| 怎么加一个家务领域 | ARCHITECTURE §22 + docs/HOUSEHOLD.md |
| 怎么接外卖 | docs/SERVICES.md + ARCHITECTURE §23 |
| 出问题怎么办 | docs/RELIABILITY.md + docs/MIGRATION.md |
| 想看日志 | docs/OBSERVABILITY.md |
| PWA 怎么用 | docs/UX_FLOWS.md |
| 加新硬件 | docs/PLUGINS.md §插件开发 |

### 33.3 文档维护规则

- 主架构变更 → 同步 `ARCHITECTURE.md` 头部版本号 + 末尾 v2.X 修订段
- 某专题深度变更 → 同步 `docs/<topic>.md` + 在 ARCHITECTURE.md 引用处加版本注
- 季度架构审视 → 检查每节是否还成立，标 stale 的节加 `[待审视]`

### 33.4 对开源用户友好的章节

- 章节标题层级尽量不超过 3 级（## / ### / ####）
- 关键概念首现处加粗体 + 缩进解释
- 代码示例尽量可运行；不能运行的明确标注 "示意，非可执行"
- 中英文术语首次并列（如"管家 / butler""告警 / alert"）

### 33.5 架构空白状态（v2.9 已全部填补）

v2.9 之前已写入 §34-§40 共 7 项 B 类设计空白，本节不再列占位。

---

## 34. 远程求助完整场景（v2.9 B 类 1）

> **用户拍板（v2.9）**：**完整远程场景**——设备状态 + 成员在场 + 摄像头快拍 + 多渠道回复。
> 在外面的人问"家里的灯关了吗"，管家要能给出真实、可视化的回答。

### 34.1 三层远程能力

| 能力 | 实现 | 鉴权 | 延迟 |
|------|------|------|------|
| **设备状态** | 通过 cloud API 或 LAN 中继（vpn/反向代理） | §14 RBAC | 秒级 |
| **成员在场** | presence 表读；avatar 是 "在 / 出门 / 离线" | 同上 | 秒级 |
| **摄像头快拍** | cloud API 触发截图 + 临时 URL | 单独 ACL：仅 admin + adult | 5-15 秒 |

### 34.2 上下文补全

远程会话的"上下文补全"策略——必须在 LLM prompt 注入：

```
[远程会话上下文]
- 说话人：爸爸（出差中）
- 渠道：TG 私聊
- 当前位置：东京（按 IP 推断）
- 时差：+1 小时
- 家里有人吗：妈妈在家
- 设备状态快照：客厅灯关、客厅空调关、厨房灯开、扫地机充电中
- 管家是否主动推送：⚠️ 静音模式（爸爸在会议中不主动推送）
```

### 34.3 多渠道回复策略

```
用户问：管家，家里灯全关了没？
   ├─ 优先：TG 回复（用户当前在 TG）
   ├─ 同步：PWA 通知一条副本
   └─ 详细：附 PWA 链接 "查看完整面板"
```

**详细回复分级**（per-member preference）：
- 简短（默认）：1-2 句
- 详细：附设备清单
- 摘要：每小时一次聚合

### 34.4 远程控制的高门槛

远程能"读"，但"写"仍受 §5.3 渠道分级约束：
- TG/微信/TG 远程渠道 → **默认不能控制设备**（除 §5.3b 列的白名单）
- 远程开门/开锁 → **永远 L1 + 二次确认**，二次确认渠道必须与发起渠道不同（TG 发起 → 用 PWA 确认）

### 34.5 反向代理 / VPN（基础设施）

远程访问 myhome-agent 本机：
- 默认：不开公网端口（仅 LAN）
- 可选：`cloudflared` / `frp` / `tailscale` 隧道 —— 用户自配
- 管家帮配：在 PWA 设置里有"远程访问"向导

## 35. 节假日自动识别（v2.9 B 类 2）

> **用户拍板（v2.9）**：**自动识别**——节假日表 + 自动作息漂移 + 预设场景。管家主动切换行为，用户可关。

### 35.1 节假日数据源

| 来源 | 范围 | 精度 |
|------|------|------|
| 系统内置中国节假日表 | 中国大陆法定节假日 | 100% 准确，2024-2030 |
| 用户手动添加的家庭纪念日 | 任意日期 | 用户级 |
| 学校节假日（可选订阅） | 寒暑假 | 按学区，需用户配 |

```sql
CREATE TABLE holidays (
  date TEXT PRIMARY KEY,
  kind TEXT,                      -- national / family / school / custom
  name TEXT,
  recurring_rrule TEXT,           -- iCal RRULE
  family_member_ids TEXT,
  enabled INTEGER DEFAULT 1
);
```

### 35.2 自动作息漂移

节假日 + 学校假期 → 调整个别成员的作息基线：

```
判断逻辑：
  if 节假日 且 member 在 family_member_ids:
    routines.baseline *= 0.5
    异常告警阈值 * 1.5
    主动推送频率 * 0.5
```

**关键**：漂移必须**可逆**——节假日结束后自动恢复。

### 35.3 预设场景

| 节假日 | 自动行为 | 可关 |
|--------|---------|------|
| 春节 | 全屋灯光按时间段渐变 + 门铃静音 + "亲戚来访"高亮 | ✅ |
| 中秋 | 厨房灯定时 + 月亮图标 | ✅ |
| 暑假 | 孩子房间作息漂移 + 提醒写作业 | ✅ |
| 用户纪念日 | 早上提醒 + 当天禁止推送告警 | ✅ |
| 周末 | 早晨提醒延后 + 不打扰休息 | ✅ |

### 35.4 用户可关

- 当天取消：PWA `/holidays/today` 一键关闭
- 长期禁用：`persona.holiday_response[kind] = 'disabled'`

## 36. 多家庭隔离 / 搬家（v2.9 B 类 3）

> **用户拍板（v2.9）**：**多家庭隔离**——household_id 全栈串，老数据只读，新家庭独立。

### 36.1 household 模型

```sql
CREATE TABLE households (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT,                          -- "北京家" / "老家" / "出租屋"
  timezone TEXT,
  locale TEXT,
  is_primary INTEGER DEFAULT 0,
  is_archived INTEGER DEFAULT 0,
  created_at TEXT,
  archived_at TEXT,
  notes TEXT
);

-- 全表加 household_id 列（仅 A 类；events / chat_history / readings 走派生）
ALTER TABLE devices ADD COLUMN household_id INT NOT NULL DEFAULT 1;
ALTER TABLE members ADD COLUMN household_id INT;
ALTER TABLE routines ADD COLUMN household_id INT;
ALTER TABLE memories ADD COLUMN household_id INT;
ALTER TABLE household_items ADD COLUMN household_id INT;
ALTER TABLE household_item_events ADD COLUMN household_id INT;
ALTER TABLE household_calendar ADD COLUMN household_id INT;
ALTER TABLE household_calendar_occurrences ADD COLUMN household_id INT;
ALTER TABLE household_relations ADD COLUMN household_id INT;
ALTER TABLE services_orders ADD COLUMN household_id INT;
ALTER TABLE scene_executions ADD COLUMN household_id INT;
ALTER TABLE autonomous_decisions ADD COLUMN household_id INT;

-- v2.12 修订：readings / events / chat_history 不加列（v2.10.1 R5 已声明 readings 派生；v2.12 扩到 events 和 chat_history），由 device_id / member_id 联表推导（避免 7000 万行 ALTER）
-- 业务查询时（readings）：WHERE EXISTS (SELECT 1 FROM devices WHERE devices.id = readings.device_id AND devices.household_id = ?)
-- 业务查询时（events）：WHERE EXISTS (SELECT 1 FROM devices WHERE devices.id = events.device_id AND devices.household_id = ?)
-- 业务查询时（chat_history）：WHERE EXISTS (SELECT 1 FROM member_households WHERE member_households.member_id = chat_history.member_id AND member_households.household_id = ?)
-- 视图封装：v_household_readings / v_household_events / v_household_chat 自动 JOIN
```

### 36.2 搬家流程

```
1. 用户 PWA → "搬家向导"
2. 选新 household 名称（默认"新家"）
3. 自动建 household + 切换 primary（v2.12 修订）：
   3a. UPDATE households SET is_primary=0 WHERE is_primary=1;  -- 撤销旧 primary
   3b. INSERT INTO households (name, is_primary, created_at, timezone, locale) VALUES (?, 1, now(), ?, ?)
   3c. 配 UNIQUE INDEX uq_households_primary ON households (is_primary) WHERE is_primary=1  -- 唯一性约束
4. 老 household 自动归档（is_archived=1）
5. 老设备全标 offline，停止控制调度
6. 新家庭从零开始 sync_from_cloud + 重新做 §13 五步向导
7. 老历史数据仍可查询（read-only 视图）
8. **persona_learn / memories 跟随 member 而非 household**（v2.15 新增）：搬家后孩子的"爱吃这个菜"偏好跟随孩子走，不绑老家庭
9. **scenes / services_orders 跟随 household**（v2.17 明确）：搬家后老 household 归档保留为只读；场景定义（"睡觉模式"）属家庭共享行为，**不跟人走**
10. **scene_executions / autonomous_decisions 永久保留**（v2.17 §43.1 修订）：审计流，按 household 归档；删成员时该 member 记 anonymous
11. **rules / rule_state / rule_audit_log / rule_feedback 跟随 household**（v0.4 §53.6 修订）：
    - 搬家后老 household 规则自动 `archived_at = now()`，只读保留
    - 新 household 从 §53 默认模板或自己新建
    - **例外**：doctor 创建的"祖辈健康提醒"类规则**跟着 member 走**——通过 `rules.scope='member'` 标识
    - 规则作者撤销（§43.3）→ 该作者规则 archived，不只是 disable
12. **cameras / vision_events 跟随 household**（v0.4 §54.2 修订）：
    - 摄像头是物理设备，跟新家庭走（rtsp_url 重新配置）
    - 老 household 的 vision_events 30 天后清理
    - 快照（snapshot_path）文件系统同步删除
    - **隐私红线**：跨家庭**不**迁移摄像头历史，避免法律风险
```

### 36.3 跨家庭语义

管家能否理解"我老家的灯？"——能：
- 管家 prompt 注入 `[households: 北京(主, 2020-), 老家(冻结, 2018-2019)]`
- "老家的灯" → 自动切到 archived household 上下文
- "帮我在新家关灯" → 默认主 household

### 36.4 成员 × household 关系

```sql
CREATE TABLE member_households (
  member_id INT, household_id INT, role_in_household TEXT,
  PRIMARY KEY (member_id, household_id)
);
```

**默认**：单成员 = 单 household，跨家庭是高级场景。

### 36.5 跨家庭 RBAC

读其他 household 数据 → 需 explicit permission。默认仅"自己的 household + 自己有成员资格的家庭"可见。

### 36.6 household_id CI 断言（v2.10.1 R5 新增，v2.11 完善，v2.12 权威化）

> v2.10 子代理 A 警告："应有 CI 断言（无 household_id 的业务表构建失败）"。
>
> **v2.12 修订**：本节是 household_id 单一权威；§5.0b / §36.1 / §29.1 / §31.2 / §35.1 都按本节分类对齐。v2.11 把 events/chat_history 误入 A 类 + holidays/mi_accounts/device_capabilities 误入 A 类，本节改正。

**白名单分两类**（v2.12 权威）：

**A. 直接持有 household_id 的表**（CI 断言必须有该列；§36.1 ALTER 计划包含这些）：
- `devices`, `members`, `routines`, `memories`
- `household_items`, `household_item_events`, `household_calendar`, `household_calendar_occurrences`, `household_relations`
- `services_orders`, `scene_executions`, `autonomous_decisions`

**B. 派生表**（CI 断言**必须无**该列——按 device_id / member_id JOIN 推导；§5.0b "联表推导"约定覆盖）：
- `events`（按 `device_id` JOIN `devices` 推导；按 `member_id` JOIN `member_households` 推导）
- `chat_history` / `chat_fts`（按 `member_id` JOIN `member_households` 推导）
- `presence`（按 `member_id` JOIN `member_households`）
- `alerts`（按 `source` 类型决定 household；household_id 可空）
- `invite_codes`（按 `inviter_member_id` JOIN 推导；可空）
- `push_subscriptions`（按 `member_id` JOIN 推导）
- `elder_care_profiles`（按 `member_id` JOIN 推导）
- `household_health_*` / `household_finance_*`（按 `member_id` JOIN 推导）
- `holidays`（v2.12 从 A 改 B：表是 household-shared 视图；按 `family_member_ids` JSON JOIN）
- `mi_accounts`（v2.12 从 A 改 B：按 `member_id` JOIN 推导；账号本身是 per-member 不重复家庭语义）
- `policies` / `device_capabilities`（v2.12 从 A 改 B：策略与能力注册是 household-shared，可显式 household_id 但默认 IS NULL 通配；CI 不强约束）

**白名单之外**：基础设施表（`schema_meta` / `task_queue` / `pending_confirm` / `redactor_config` / `runtime_profile`）和 `households` 自身 / `household_*` 领域表（已经显式标注）**不参与**断言。

**断言脚本**（CI 必跑，v2.12 权威版）：

```python
# tests/ci/test_household_id_presence.py
import sqlite3

DIRECT_TABLES = [  # 必须有 household_id 列
    "devices", "members", "routines", "memories",
    "household_items", "household_item_events",
    "household_calendar", "household_calendar_occurrences",
    "household_relations",
    "services_orders", "scene_executions", "autonomous_decisions",
    "scenes",                       # v2.17 新增（§15 scenes 表定义持 household_id）
    "rules", "rule_state", "rule_audit_log", "rule_feedback",  # v2.19 新增（§53 跨信号推理规则引擎）
    "cameras", "vision_events",                                # v0.2 新增（§54 视觉管线）
]

DERIVED_TABLES = [  # 必须无 household_id 列（按外键 JOIN 推导）
    "events", "chat_history", "chat_fts",
    "presence", "alerts", "invite_codes", "push_subscriptions",
    "elder_care_profiles",
    "household_health_members", "household_health_metrics",
    "household_finance_entries",
    "holidays", "mi_accounts", "policies", "capabilities",        # v2.17 修订：capabilities（原 device_capabilities，§31.2 v2.16 改名）
]

def test_direct_tables_have_household_id():
    with sqlite3.connect("data/myhome.db") as c:
        for table in DIRECT_TABLES:
            cols = [r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]
            assert "household_id" in cols, f"{table} 缺 household_id 列"

def test_derived_tables_have_no_household_id():
    with sqlite3.connect("data/myhome.db") as c:
        for table in DERIVED_TABLES:
            cols = [r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]
            assert "household_id" not in cols, f"{table} 不应有 household_id 列（应是派生）"
```

**新增业务表时**：必须选 A 或 B 类，加入对应白名单 + 通过此测试。

**v2.18 关键修订：household_id 隔离从约定变强制**

```
所有 DAO 查询必须经 HouseholdScope 上下文对象取数据：
  - 实现位置：myhome_agent/db/scope.py
  - 接口：scope.query(table, where, member_id) → 自动注入 WHERE EXISTS JOIN households
  - 禁止裸查询（带 _unsafe 后缀并登记豁免清单）

lint 规则（CI 必跑）：
  - 拒绝对 events / readings / chat_history / household_* 等表的裸 SELECT/UPDATE
  - 例外：测试代码（tests/）、管理工具（myhome_agent/admin/）
  - 例外登记：豁免清单文件 .unsafe-query-exceptions.yaml
```

**v2.18 不变式**：单 NAS 服务多 household 时，**所有 household-shared 表的查询必须经 HouseholdScope**——单处漏写 = 跨家庭数据泄漏，且 §36.6 CI 只断言表结构、不断言作用域

## 37. 三源验证防幻觉（v2.9 B 类 4）

> **用户拍板（v2.9）**：**三源验证**——高风险决策要三路独立信号一致。
> 防止管家错关灯、错开锁、错发警告。

### 37.1 多源定义（v2.10 自适应）

| 源 | 是什么 | 典型延迟 | mesh 设备可得 |
|----|------|---------|--------|
| **LAN 主动探针** | 局域网直连轮询 / 心跳包 | 实时（秒） | ❌（mesh 锁无 IP）|
| **云端被动事件** | 米家云端 push / poll | 1-5 秒 | ✅ |
| **第三路独立信号** | 成员手机在网 / 门锁物理按键反馈 / 其他设备交叉验证 | 10-60 秒 | ❌（弱证据）|

> **v2.10 F8 修订**：原设计"必须三源一致"——但 mesh 锁、zigbee 子设备、纯 BLE 设备的家庭普遍缺 LAN 源。**改为"按设备 spec 可得源数自适应"**。

**核心不变量**：**所有**"在线"源必须一致，且**至少 2 个源在线**。少于 2 源在线 → 拒绝执行 + 显式提示。

**mesh 设备替代源**（当 LAN 不可得时）：
- 网关心跳（zigbee 网关设备在线）
- 事件序列连续性（最近 N 次事件无异常）
- 物理联动（人从门前走过，PIR 触发 + 锁状态变化）

### 37.2 何时启用多源验证

**默认仅高危动作走多源**：
- 门锁开/反锁
- 燃气/水浸告警触发
- 陌生成员身份判断（"新成员回家？"）
- 大额服务代办

普通动作（开灯/调温度）不需要，走 §5.3 渠道分级 + 二次确认即可。

### 37.3 验证流程

```
管家决定：客厅灯似乎开着的，但爸爸说"关了"
  ├─ LAN 主动探针：读状态 → "开着"
  ├─ 云端被动事件：最近 1h 状态变化流 → "2h 前 on，无关事件"
  └─ 成员手机在场：妈妈的 iPhone LAN 在线 → 可能误操作？

  源数对比：
    sources_available = 3
    sources_consistent = (LAN=on) ∧ (Cloud=on) ∧ (Phone=在场) → 全一致
  → 通过；执行
```

```
mesh 锁示例（LAN 不可得）：
  ├─ LAN 主动探针：❌（mesh 锁无 IP）
  ├─ 云端被动事件：最近 1h "门状态" → "关"
  └─ 网关心跳：✅（zigbee 网关在线）
  
  sources_available = 2（云端 + 网关）
  sources_consistent = 关 ∧ 关 → 一致
  → 通过；执行
```

### 37.4 决策矩阵（v2.10 补全）

| 可得源数 | 全一致 | 一致率 | 决策 |
|---------|--------|--------|------|
| 3 | ✅ | — | 信任，高危动作执行 |
| 3 | ❌ | — | 拒绝执行 + 报警 |
| 2 | ✅ | — | 信任（降级但通过）|
| 2 | ❌ | — | 拒绝执行 |
| 1 | — | — | **拒绝执行 + 提示"源数不足"** |
| 0 | — | — | **拒绝一切写动作 + 红灯** |
| 任意 | ✅ | < 1.0 | **拒绝执行 + 提示"信号冲突"** |

**关键变更**：把"全矩阵 8 行"改为"按源数分桶 + 全一致要求"。比原版更简洁，对 mesh 设备友好。

### 37.5 误控制补偿（v2.10 延长时间窗）

万一多源验证通过但动作错了：
- 控制后立刻发"我刚 X 了 XX，**30s/60s 内可撤销**"通知
- 撤销窗口从**反馈环判定 done 之时**起算（§5.6b 反馈环需 ≤8 秒判定）
- 普通控制 30 秒撤销窗；高危控制（门锁/燃气）60 秒撤销窗
- 提供撤销快捷方式（TG bot `/undo`、PWA 通知按钮、邮件回执链接）
- 撤销窗关闭后无可撤销操作则完成（事件写 `control_revocable_until`）

## 38. 多代同堂 + 老年人守护（v2.9 B 类 5）

> **用户拍板（v2.9）**：**成员独立 + 老年人守护**——祖父母、父母、孩子各自独立登记、独立作息、独立异常守护。

### 38.1 成员独立

每个成员（无论年龄）：
- 独立作息基线（routines 表 per member）
- 独立 RBAC（孩子是 child，老人是 adult）
- 独立 presence 推断
- 独立渠道偏好

### 38.2 老年人守护

| 关注项 | 实现 |
|--------|------|
| **作息异常** | 老人超过 expected_wake + grace → 高优先级告警给所有 adult |
| **门锁异常** | 老人深夜开门（22:00-6:00）→ 立即推送 |
| **紧急求助** | 老人语音调用管家"救命" → **管家自动拨给子女/care_taker/primary contact** + PWA 显示 120 号码 + 一键拨号按钮（v2.17 修订：管家**不**自动拨 120/110/119；120 仅人工触发；详见 §23.6 safe-action 白名单）|
| **跌倒检测（可选）** | 穿戴设备 / 摄像头 → 异常姿态检测 → 告警 |
| **吃药提醒** | household.items 联动，过期前推送（§22 领域） |
| **联系薄** | household.relations 表，老人的子女/邻居电话自动可读 |

### 38.3 数据模型补充

```sql
CREATE TABLE elder_care_profiles (
  member_id INT PRIMARY KEY,
  emergency_contacts TEXT,
  medical_notes TEXT,             -- 加密列（§5.11 强制本地）
  daily_check_in_window TEXT,
  medication_schedule TEXT,
  fall_detection_enabled INTEGER DEFAULT 0,
  quiet_hours_start TEXT,
  quiet_hours_end TEXT
);
```

### 38.4 子女/照护者视图

PWA 多视图：
- 自己视角（默认）
- 老人视角（"我代管的老人"）—— 仅 adult + 主 care taker 角色可见

**关键不变量**：老人**自己**仍是独立 member，能用管家——只是其他人能"代为查看"。

### 38.5 隐私边界

- 老人的 medical_notes 即使本地也加密
- 跌倒检测原始数据**永远不离开本机**
- 子女能收到异常通知，但**不能读老人所有事件**（仅相关告警）

### 38.6 老人作为使用者（v2.13 新增，v0.4 细化 6 项）

> **v2.13 新增**：之前 §38 聚焦"守护老人"，但**老人自己用管家**的场景缺位。v2.13 老人必须是**独立使用者**（不仅是被守护对象）。
> **v0.4 细化**：把 6 项拆成各自子节，每项给 PWA 实现 + 代码钩子 + 视觉事件触发。

**6 项老年可用性总览**：

| # | 设计项 | PWA 入口 | 代码模块 | 视觉事件触发 |
|---|--------|---------|---------|------------|
| 38.6.1 | 超大字号 / 高对比度 | `/settings/accessibility` | `frontend/accessibility.css` + `members.accessibility` 字段 | 切字号时存 member.preferences |
| 38.6.2 | 方言识别 | 语音输入按钮 | `voice/dialect_asr.py`（v0.4 新增） | ASR 失败时降级到普通话 |
| 38.6.3 | 语音优先（Voice-First） | 启动默认隐藏文字输入 | `frontend/voice-first.css` | member 切换时自动应用 |
| 38.6.4 | 对话简化（Slow Mode） | 管家回复 | `agent/prompt.py` elder_friendly template | 始终 |
| 38.6.5 | 操作回退（Undo Window） | 控制后 30s 浮动按钮 | `agent/core.py` ControlFeedback.undo_stack | 始终 |
| 38.6.6 | 每日问候（Daily Greeting） | PWA 启动后第一屏 | `agent/cron/daily_greeting.py`（v0.4 新增） | 每日早 7 点（按 member.timezone） |

**实现**：
- `members.accessibility` 字段（v2.17 扩展为 9 项）：
  ```json
  {
    "font_size": "lg|xl|xxl",                 // 字号（§38.6.1）
    "voice_first": 1,                          // 语音优先（§38.6.3）
    "slow_mode": 1,                            // 慢节奏（§38.6.4）
    "color_safe": 1,                           // v2.17 新增：色盲友好
    "reduce_motion": 1,                        // v2.17 新增：动效降级
    "touch_target_min_size": 1,                // v2.17 新增：触摸目标 ≥44px
    "hearing_impairment": 1,                   // v2.17 新增：听障视觉替代反馈
    "screen_reader_friendly": 1,               // v2.17 新增：ARIA 标签
    "high_contrast_aaa": 1                     // v2.17 新增：WCAG AAA
  }
  ```
- §32 persona 默认 profile 加 `elder_friendly` 模板
- §42 规则模式覆盖这 6 项（无 LLM 也能用）

#### 38.6.1 超大字号 / 高对比度（v0.4 细化）

**PWA 实现**：
- CSS 变量 `--base-font-size: 18px|24px|32px`，全局应用
- 高对比度模式：背景黑/前景白，文字对比度 21:1（WCAG AAA）
- 触摸目标：所有按钮 ≥ 48×48px
- 图标 + 文字双标签（不只是图标）

**代码钩子**（`frontend/accessibility.css`）：
```css
:root[data-font-size="xxl"] { --base-font-size: 32px; }
:root[data-contrast="aaa"] {
  --bg: #000; --text: #fff;
  --text-on-accent: #fff;  /* 按钮文字 */
}
button { min-width: 48px; min-height: 48px; }
```

**视觉事件触发**：会员切换 / 设置变更时存 `member.preferences.last_accessibility_change`（v0.4 新增字段）。

#### 38.6.2 方言识别（v0.4 新增）

**支持方言**（v0.4 起步）：
- 普通话（必选）
- 粤语（zh-HK）
- 闽南语（zh-TW-min-nan）
- 上海话（zh-CN-shanghai）
- 四川话（zh-CN-sichuan）

**实现**：用 Whisper.cpp 本地 ASR + 方言词典（v0.4 占位实现）：
```python
# voice/dialect_asr.py
class DialectASR:
    DIALECTS = ["zh-CN", "zh-HK", "zh-TW-min-nan", "zh-CN-shanghai", "zh-CN-sichuan"]
    def transcribe(self, audio: np.ndarray, hint: str | None = None) -> str:
        """hint: 会员上次用的方言（避免每次识别）"""
```

**降级链**：
1. 会员方言 hint（最优先）
2. Whisper 自动检测
3. 普通话兜底
4. 失败时弹"请按普通话说话"提示

#### 38.6.3 语音优先（v0.4 细化）

**PWA 默认行为**（member.voice_first=1 时）：
- 启动后**不显示**文字输入框
- 全屏显示大麦克风按钮
- 说完后管家回复**朗读**（TTS）
- 长按麦克风 = 取消说话

**视觉事件触发**：会员切换时，PWA 检测 `member.voice_first` 自动切换 UI 模式。

#### 38.6.4 对话简化（v0.4 细化）

**Slow Mode 规则**（`agent/prompt.py` elder_friendly 模板）：
```
- 单句 ≤ 20 字（v0.4 hard limit）
- 不用反问句（"你要不要开灯？" → "灯开了"）
- 数字读出来（"23 度" → "二十三度"）
- 时间用相对（"3:30" → "现在三点半"）
- 不堆术语（"rule triggered" → "我注意到..."）
- 重复确认（"你说的是关灯，对吗？"）
```

**实现**：v0.4 在 `core.py` `Agent._run_loop` 中按 `member.slow_mode` 加后处理。

#### 38.6.5 操作回退（v0.4 细化）

**Undo Window**（已存在 §5.6b）：
- 默认 30 秒（v0.4 老人场景延长到 60 秒）
- 控制后浮动按钮"刚才那次作废"出现
- 按下 → 调用 `ControlFeedback.undo_last()`
- 不可逆操作（irreversible capability）**不**显示 Undo（安全）

**PWA 实现**：
```js
// 浮动按钮 30s/60s 后自动消失
setTimeout(() => { undoBanner.style.display = 'none'; }, WINDOW);
```

#### 38.6.6 每日问候（v0.4 新增）

**触发**：每日早 7:00（按 `member.timezone` 偏移）

**问候内容**：
```
奶奶早！今天是 8 月 3 号，星期日。外面 28 度，有点热。
今天是小暑，注意防暑。有空记得吃药哦。
```

**数据来源**：
- 日期/时间：本地时钟（按 timezone）
- 天气：天气 API（v0.4 集成和风天气）
- 节气/节日：§35 节假日识别
- 特殊提示：从 rules 引擎拉（如"该吃药了"）

**实现**：`agent/cron/daily_greeting.py`（v0.4 新增）每日 7:00 触发。

#### 38.6.7 视觉事件 + 老人可用性联动（v0.4 整合）

| 视觉事件 | 老人联动 |
|---------|---------|
| 摄像头检测到老人跌倒 | 立即 §38.7 跌倒升级链 + 推送子女 |
| 摄像头检测到老人长时间静止 | §38.6 慢节奏对话询问 + caregiver 通知 |
| 摄像头检测到陌生人 + 老人在家 | 子女+物业 升级（v0.4 老人独有：家属知情） |
| 老人走出家门（独居）| 痴呆走失预警（§38.8） |

**v0.4 视觉 × 老人场景示例**：
```yaml
id: elderly_outdoor_alone_v1
description: 痴呆老人独自出门（v0.4 视觉 + 老人角色联合）
when:
  all:
    - sensor.vision.kind: person
    - sensor.vision.camera.location: 门口
    - member.role: elderly_dementia
    - member.has_caregiver_at_home: false
    - any_family_at_home: false
then:
  - escalate:
      ladder: [primary_caregiver, 110]
      level: safety
      sos_bypass: true
```

### 38.7 跌倒检测机制（v2.13 新增）

> v2.9 写"穿戴设备 / 摄像头 → 异常姿态检测 → 告警"——**这是医疗级判断**，v2.13 必须落到具体机制。

**硬件方案对比**：

| 方案 | 优 | 劣 | 推荐 |
|------|----|----|------|
| **穿戴手环 / 跌倒吊坠**（小米生态已有）| 不依赖摄像头，老人隐私；误报率 < 5% | 老人忘戴 / 不充电；夜间洗澡掉落误报 | ✅ 首选 |
| **毫米波雷达**（Aqara FP2 类）| 不拍照、不穿戴；24h 在线 | 单价 ¥1000+；识别跌倒 vs 弯腰准确率 80% | ✅ 次选 |
| **摄像头视觉** | 已有设备即可用 | 隐私敏感；夜间/遮挡误报；上传视频风险 | ❌ 默认禁用 |
| **地板压力传感**（智能床/地垫）| 准确率高 | 部署复杂；只覆盖指定房间 | P3 远期 |

**算法与训练数据来源**：
- **优先开源模型**：TensorFlow Fall Detection / OpenPose fall detection；自部署训练（基于公开数据集如 UR Fall Detection）
- **次选商业 SDK**：Aqara / 米家自带的跌倒检测能力（已在米家健康手表 / 智能摄像机落地）
- **禁止**：把老人摄像头视频流上传第三方训练平台（§5.7c 影像通道默认禁外发）

**告警四级（medical-grade 风险控制，v2.17 修订：原标题"三级"实为四级）**：

```
Level 0: 跌倒概率 < 30%   → 仅本地记录，无推送
Level 1: 跌倒概率 30-70%  → 推送给所有 care_taker + adult + 主子女（"老人疑似跌倒，请确认"）
Level 2: 跌倒概率 > 70%   → 多渠道并行（推送 + SMS + 语音电话）+ 主子女 + 社区医院
Level 3: 老人 30 分钟无任何动作 + 之前疑似跌倒 → 视为紧急，触发 §38.12 急救流程（v2.17 修订：原写"§38.7 急救流程"是死循环引用；急救流程锚定到 §38.12 新增小节）
```

**§38.12 急救流程（v2.17 新增）**：

> 急救流程不限于跌倒场景——是 §38.7 Level 3 + §38.2 "救命" + §38.8 痴呆场景紧急求助 + §38.11 健康异常的**统一入口**。

```
触发：alerts.priority = 'safety' AND level ≥ 3
动作：
  1. 通知所有 care_taker + 主子女（多渠道并行）
  2. PWA 大字显示急救号码：120 / 110 / 119 + 一键拨号按钮
  3. 30 秒倒计时：默认取消（避免误报）；倒计时结束无人取消 → 通知 primary contact 拨打
  4. **管家不自动拨号 120/110/119**（§23.6 责任边界 + §52.6 attempt 4 修订）
责任边界：
  - 管家只提供"通知 + 号码 + 一键拨号"
  - 实际拨号由人触发（PWA 按钮 / 子女接电话后手动拨）
  - 显式声明"辅助非医疗设备"（§38.13 onboarding 必读）
```

**误报控制**：
- 每 5 分钟最多 1 次 Level 1+ 告警（避免反复打扰）
- 老人可手动按"取消"按钮（5 秒长按 = "我没事"）
- 误报统计写 `events.kind='fall_false_alarm'`，PWA 显示给子女

**合规风险**：
- 误报 → 反复打扰：阈值可调（默认 30%，保守）
- **漏报 → 严重事故**：阈值过高 + 老人没人发现 → 责任
- **声明（v2.13 必加）**：管家跌倒检测是**辅助**，不是医疗设备——紧急情况仍需人工确认

### 38.8 痴呆与认知衰退场景（v2.13 新增）

> **核心问题**：老人认知衰退导致的安全风险——出门走失、忘关火、忘吃药、被骗。

**5 类典型场景 + 守护机制**：

| 场景 | 风险等级 | 守护机制 |
|------|---------|---------|
| **出门走失** | 🔴 高 | §5.4 门锁 + §38.7 摄像头 + GPS 联动（可选）—— 超出家庭半径 500m 立即推送所有子女 |
| **忘关燃气/灶** | 🔴 高 | 联动 §22 items 燃气检测 + 烟感；检测到火源 + 无人 30 分钟 → 自动关阀 + 推送 |
| **忘吃药** | 🟡 中 | §22.4 items 过期告警升级——按 medication_schedule 在应吃时间后 30 分钟未确认 → 提醒 + 通知子女 |
| **被骗接电话** | 🟡 中 | 管家不接电话，但**实时录音+语音关键词识别**（"转账""汇款""验证码"）→ 推送子女 + 自动录音存档 |
| **深夜漫游** | 🟡 中 | §38.2 门锁异常 + 灯光/语音提醒（"奶奶，天还早，回去睡吧"）|

**温和提醒 vs 自动兜底的关键不变量（v2.13 必加）**：
- **可逆行为**（关窗、调温、提醒吃药）→ 温和提醒 + 等待确认
- **不可逆行为**（关燃气阀、通知子女、出门报警）→ 自动执行 + 同时通知，不等老人确认

**认知衰退分级（参考临床）**：
- 轻度（CDR 1）：日常能自理，但易忘事——管家"主动提醒"模式
- 中度（CDR 2）：需协助——管家"自动兜底"模式（不可逆操作自动执行）
- 重度（CDR 3）：完全需照护——**管家不直接决策**，所有动作经 care_taker 确认

`members.cognitive_level` 字段：`normal` / `mild` / `moderate` / `severe` —— 决定 §47 policies 的 autonomy_level 默认值（mild→L3, moderate→L1, severe→L0）

### 38.9 远程子女视图（v2.13 新增）

> §38.4 写"子女/照护者视图"——但没说**不在场的子女**怎么访问。v2.13 补远程访问。

**远程访问四档权限**：

| 等级 | 可看 | 可做 | 适用 |
|------|------|------|------|
| **L1 仅通知** | 收告警 | 任何控制 | 子女默认 |
| **L2 查看+确认** | 看仪表盘 + ack 告警 | 看不可控 | 子女可升级 |
| **L3 受控** | 上面 + 启停场景 | 不能直接控制设备 | 主照护子女 |
| **L4 同本地** | 同 admin | 同 admin | 紧急情况（需 admin 临时授权）|

**远程访问的安全设计（v2.13 必加）**：

1. **双因素认证**：远程登录必须 PIN + 短信验证码（不能用单一密码）
2. **访问时间窗**：默认仅白天 8:00-22:00 可远程控制；夜间只读不控
3. **异地登录告警**：子女账号从新城市登录 → 自动推送老人本人确认
4. **远程控制留痕**：所有远程操作写 `events.kind='remote_control'`，不可删除
5. **5 分钟撤销窗**：远程控制后 5 分钟内老人可在本地撤销（防误操作）

**渠道优先级**：
- 远程访问默认通过**企业微信/Telegram**（比浏览器登录更安全，便于审计）
- 浏览器远程访问需 §30.0 TLS + §5.8b PWA 必登录 + §47 policies 二次确认
- 远程禁止直接控制门锁/燃气（必须本地或语音当面二次确认）

### 38.10 多老人 + 多子女 + 保姆（v2.13 新增）

> 实际家庭常是"4 老人 + 3 子女 + 1 保姆"。v2.13 补这一复杂场景。

**角色矩阵补充**：

| 角色 | 看老人 | 控制老人相关 | 改设置 | 适用 |
|------|--------|------------|--------|------|
| `care_taker`（已有）| ✅ | L3 自动 | ❌ | 主照护子女 |
| `care_proxy`（v2.13 新增）| ✅ | L2 受控 | ❌ | 保姆/护工 |
| `family_viewer`（v2.13 新增）| ✅ | ❌ | ❌ | 远方亲属 |

**多老人 + 多子女的协同机制**：
- **主照护者选举**：每个被守护老人有一个 `primary_caretaker_id`（多数 care_taker 中选）
- **轮值**：可选 `care_rotation` 表（谁本周主照护，本周主照护接收所有告警，其他只收紧急）
- **共识触发**：高风险决策（远程开门、远程燃气、远程切换 care_taker）需 2 个 care_taker ack

**保姆场景**：
- 保姆账号默认 `care_proxy`，有效期默认 3 个月，可续
- 保姆只能访问"老人活动区"设备（房间通过 devices.room 白名单）
- 保姆能看但不能改 §22 items / §47 policies
- 保姆账号被自动记录上下班时间（门锁 + 人体传感器联动）

**多个被守护老人**：
- 各自独立的 `elder_care_profiles`（per-member）
- 各自的 medication_schedule / fall_detection_enabled
- 告警路由：每个老人独立 primary_caretaker，不会合并推送

### 38.11 医疗接口与慢病数据（v2.13 新增）

> §22.1 health 是"按需启用"——但**老人场景几乎一定要启用**。v2.13 把 health 提到 §38 必选。

**慢病数据接入（v2.13 必加 §22 health 启用路径）**：

| 数据类型 | 设备/来源 | 上云 | 加密 | 用途 |
|---------|----------|------|------|------|
| **血压** | 血压计（米家有）→ cloud API 拉历史 | ❌ 仅本地 | ✅ | 异常告警 + 趋势报告 |
| **血糖** | 血糖仪（部分小米生态）| ❌ | ✅ | 同上 |
| **心率 / 血氧** | 手表/手环 | ❌ | ✅ | 实时异常推送 |
| **体重** | 体脂秤 | ❌ | ✅ | 慢病趋势 |
| **睡眠** | 手表 / 床带 | ❌ | ✅ | 睡眠质量趋势 |
| **步数** | 手表 / 手机 | ❌ | ✅ | 活动量告警 |

**用药清单联动**：
- `household_items` 已有"药品"类目——v2.13 加 `medication_schedule` JSON 字段：`{drug_name, dosage, frequency, refill_date}`
- §5.0a 加任务：用药时间 → 推送提醒 → 30 分钟未确认 → 通知子女
- §23 服务代办可对接"在线药房 API"（京东健康 / 美团买药 / 阿里健康）——自动续方下单

**家庭医生对接（v2.13 P2）**：
- 慢病异常（血压连续 3 天 > 160）→ 自动推送家庭医生（微信群 / 短信）
- 医生可远程给建议（异步）
- 不替代医生——是辅助通知

**医疗接口的合规风险**：
- ❌ 管家绝不做出医疗诊断
- ❌ 管家不推荐具体药物
- ✅ 管家只推送数据 + 提醒用药
- ✅ 用户数据完全本地，加密
- **声明（v2.13 必加）**：管家不是医疗器械——所有健康功能仅"通知 + 提醒"，不替代医疗专业人员

### 38.12 老人守护场景总览（v2.13 必加）

```
┌─────────────────────────────────────────────────────┐
│  老人使用 + 守护场景                                   │
│                                                     │
│   §38.6 老人作为使用者 ← 6 项老年可用性设计             │
│   §38.7 跌倒检测 ← 医疗级三级告警 + 误报控制            │
│   §38.8 痴呆与认知衰退 ← 5 类场景 + 温和提醒 vs 自动兜底 │
│   §38.9 远程子女 ← 4 档权限 + 安全设计                │
│   §38.10 多老人 + 保姆 ← care_proxy + 轮值            │
│   §38.11 医疗接口 ← 慢病数据 + 用药清单               │
│                                                     │
│   共 24 个细分场景，覆盖：                              │
│   使用体验（5） / 主动守护（8） / 被动守护（5）         │
│   远程协同（3） / 医疗辅助（3）                       │
└─────────────────────────────────────────────────────┘
```

**v2.13 §7 风险表新增 4 条 🔴**：
- 老人专属对话模式缺位 → P1 必做
- 跌倒检测误报 → 医疗级事故 → P1 必做
- 痴呆场景无机制 → P1 必做（v2.13 §38.8）
- 远程子女访问无 PWA TLS 同级隐私设计 → P1 必做

### 38.13 老人作为使用者：8 主场景（v0.6 展开）

> v0.6 把"老人独立使用管家"的场景全部展开。**与 §38.6 可用性 6 项配合**——6 项是 UI/UX 层面，8 主是实际使用场景。

#### 38.13.1 老人主动询问（最常见场景）

**场景**：老人直接问管家"今天有什么安排？"/"孙子几点放学？"

**数据源**：
- 家庭日历（household_calendar_occurrences）
- 成员画像（persona_learn 偏好）
- 实时事件（events 当日）

**实施**：
- LLM 通过 `query_events` / `query_calendar` 工具拉取
- Slow Mode 模板（§38.6.4）：单句 ≤20 字 / 不用反问 / 数字读法
- 不调任何控制工具（只读）

**关联**：§53 规则 `elderly_active_query_daily_v1`（v0.6 计划种子规则）

#### 38.13.2 老人被动接收（推送场景）

**场景**：管家主动推送"早，奶奶！今天 8 月 3 日，28 度，宜开窗通风"

**数据源**：
- 天气 API
- §35 节假日
- 家庭日程
- 成员偏好（是否喜欢"小知识"/"笑话"）

**实施**：
- §38.6.6 每日问候 cron 任务
- 早 7:00 触发（按 member.timezone）
- 通道：PWA push + 小爱音箱语音（v1.0）

**关联**：§38.6.6 + §52 care 级通知路由

#### 38.13.3 老人说"我不舒服"

**场景**：老人对管家说"我有点头晕"

**数据源**：
- 当下对话
- 老人近期健康数据（vital signs，§38.11.1）
- 子女联系偏好

**实施**：
- 触发关键词检测（"不舒服"/"难受"/"头晕"等）→ LLM 推理
- 询问 2-3 个相关问题（血压？睡眠？吃药了吗？v0.6 简化）
- 必要时通知子女 + 慢病管家（§38.11.2）
- **强制 L1**（safety + 涉及健康）

**关联**：§50.3 治理 safety + 不可逆规则 + §38.11 慢病

#### 38.13.4 老人想控制设备

**场景**：老人说"太暗了，开灯"/"开空调"

**数据源**：
- 当前房间传感器
- 设备能力（capabilities）

**实施**：
- LLM 工具调用 `control_device`
- 走 §5.3 二次确认（高危如关阀/锁门）
- 普通控制（开灯/调温）直接执行
- **强制 L1**：涉及门锁 / 燃气 / 主开关
- **默认 L2**：开灯 / 调温 / 拉窗帘

**关联**：§5.3 + §50 治理等级

#### 38.13.5 老人找不到东西

**场景**："我老花镜放哪了？"

**数据源**：
- 摄像头历史（视觉事件，v0.3+）
- 物品位置记忆（v0.6 计划 items.last_seen）
- 成员画像（已知习惯放哪）

**实施**：
- LLM 通过 `recall` 工具找记忆
- 摄像头查最近 1 小时（v0.6 简化版，v0.7 接视觉管线）
- 找不到时给"通常放在哪"的建议（基于历史）

**关联**：§22.3 household_items + §54 视觉

#### 38.13.6 老人想找家人

**场景**："我儿子在哪？"

**数据源**：
- members 位置（per-member GPS，v0.6 计划）
- 成员状态（在不在线 / 最后在线时间）

**实施**：
- 简单回答 + 不涉及隐私细节
- 仅返回"在 / 不在 / 没信号"
- 详细位置需 PWA 二级授权

**关联**：§51 成员区分度 + §34 隐私边界

#### 38.13.7 老人想看电视

**场景**："我想看新闻联播"

**数据源**：
- 电视 / 投影 / 小爱音箱

**实施**：
- LLM 调 `control_device`（电视频道）
- 或调 §42 场景"看电视模式"（关灯 + 开电视 + 调音量）
- 默认 L2，**睡前不调**（night 维度风险 +0.15 → L1）

**关联**：§42 场景模式 + §50 风险评分

#### 38.13.8 老人紧急求助

**场景**：老人说"救命"/"帮帮我"

**数据源**：
- SOS 关键词检测
- 老人位置 / 房间（最近传感器）

**实施**：
- **直接 SOS 旁路**（§52.1）→ attempt 4 跳过 attempt 1-3
- 通知所有子女 + 物业 + 120（默认）
- LLM 不参与（避免延迟）
- 强制 L1（最高风险）

**关联**：§38.2 SOS 直通 + §52.1 + §50.3.2 强制 L1

### 38.14 老人作为被守护者：5 被场景（v0.6 展开）

> 5 个"被守护"场景——管家主动监护老人，**老人不参与对话**。

#### 38.14.1 跌倒检测（v2.13 §38.7 已有 + 增强）

**场景**：老人在家突然跌倒

**数据源**：
- 智能手环 IMU（v0.6 计划接入）
- 摄像头姿态分析（v0.3 PoseDetector）
- 床垫压力传感器（已有）

**实施**：
- 多信号联合判定：IMU 异常 + 摄像头横卧 + 床压 30min 无变化
- §53 规则 `elderly_fall_v2_v0.6`（扩展 v1）
- **L1 强制**（safety + irreversible health）
- 升级链：primary caregiver → 120 → 邻居

**关联**：§38.7 + §53.4 置信度 + §54 视觉

#### 38.14.2 痴呆走失（v2.13 §38.8 已有 + 视觉增强）

**场景**：痴呆老人独自出门

**数据源**：
- 门锁开关事件
- 摄像头门口人形检测
- 室内传感器（老人在哪个房间）

**实施**：
- §53 规则 `dementia_wander_v0.6`（v0.3 视觉版）：
  - 门锁开 + 老人独自 + 没有家人 → 报警
- 视觉联动：门口摄像头检测到人 + GPS 校核
- **L1 强制**（safety + 不可逆 health）
- 升级链：所有子女 + 110 + 物业

**关联**：§38.8 + §54 视觉 + §50 强制 L1

#### 38.14.3 慢病异常（v2.13 §38.11 增强）

**场景**：老人血压 / 血糖 / 心率突然异常

**数据源**：
- 智能血压计 / 血糖仪 / 手环（v0.6 计划接入）
- 历史基线（persona_learn）

**实施**：
- 与基线比较：偏离 > 2σ → 报警
- §53 规则 `chronic_abnormal_v0.6`（v0.6 计划）
- 通知慢病医生（如果有）+ 子女
- **L1 强制**（health safety）

**关联**：§38.11 慢病 + §53 规则 + §50 L1

#### 38.14.4 失禁 / 跌坐沙发

**场景**：老人坐沙发后长时间无活动（可能失禁或睡着）

**数据源**：
- 沙发压力传感器（v0.6 计划）
- 摄像头姿态分析

**实施**：
- §53 规则 `elderly_inactive_sofa_v0.6`
- 通知子女（care 级）
- **L2 默认**（非紧急）

**关联**：§53 + §52 通知

#### 38.14.5 老人按紧急按钮（硬件）

**场景**：老人按床头 / 卫生间 / 随身 SOS 按钮

**数据源**：
- 物理按钮（Zigbee 设备，v0.6 计划接入）
- 按钮 ID → 位置（卧室/卫生间）

**实施**：
- §53 规则 `physical_sos_button_v0.6`
- **L1 强制**（sos_bypass=true）
- 升级链 + 子女 + 物业 + 120（按位置推）

**关联**：§38.2 SOS + §52.1 + §50

### 38.15 多老人 + 多照护者协同：3 协同场景（v0.6 展开）

#### 38.15.1 照护代理共识

**场景**：3 个子女对老人的某项决策意见不一致（例：是否送养老院）

**数据源**：
- 子女投票（care_taker 角色可投票，§47.7）
- 老人意愿（如果清醒）

**实施**：
- `consensus_required` 规则：需要 ≥ 2 票同意才执行
- 管家不投票，只做"投票统计 + 通知"
- 多数通过 → 提交执行（仍 L1）
- 不通过 → 不执行 + 报告

**关联**：§47 policy + §50 L1 + §22.5 关系

#### 38.15.2 保姆上下班

**场景**：保姆每天 8:00 来 / 18:00 走

**数据源**：
- 保姆指纹 / 门锁密码
- 摄像头门口人形（v0.3）

**实施**：
- §53 规则 `nanny_shift_v0.6`
- 上班：通知子女"保姆已到"
- 下班：通知子女"保姆已走，老人独处 X 小时"
- 持续独处超 4 小时 → L2 通知子女

**关联**：§53 规则 + §52 通知 + §50 治理

#### 38.15.3 多老人角色区分

**场景**：家里 2 个老人，子女不知道哪个需要关注

**数据源**：
- members.role 含 `elder_senior` / `elder_junior`
- per-member 画像

**实施**：
- 每个通知明确指出"是张爷爷，不是李奶奶"
- 报警时按"最需要关注"优先级
- §51 成员区分度 §38.13 老人画像叠加

**关联**：§51 成员区分度 + §38 + §52 通知

### 38.16 医疗接口：3 医疗场景（v0.6 展开）

#### 38.16.1 续方下单（§38.11 已规划）

**场景**：慢病老人需要续方

**数据源**：
- 当前用药记录（household_health_medication）
- 处方周期（v0.6 计划）
- 合作医院 API（v1.0 计划，v0.6 stub）

**实施**：
- §53 规则 `medication_renewal_v0.6`：用药剩 7 天 → 通知子女
- 子女授权 → 调用医院 API 续方（v1.0 实际下单）
- v0.6：仅提醒，**不**自动下单
- **L1 强制**（涉及金钱 + 健康）

**关联**：§23 服务代办 + §38.11 + §50 L1

#### 38.16.2 急救流程（v2.13 §38.12 已有）

**场景**：老人突发心梗 / 脑梗

**数据源**：
- 生命体征剧烈异常
- 老人 SOS
- 子女远程确认

**实施**：
- §38.12 已定义流程
- v0.6 强化：自动调出老人病史（过敏 + 用药 + 既往病史）给 120
- 管家不上传 120（隐私红线，v1.0 计划 + 老人同意书）

**关联**：§38.12 + §43 GDPR + §50 强制 L1

#### 38.16.3 体检报告解读

**场景**：老人体检完，报告上传管家

**数据源**：
- 体检报告 PDF（v0.6 计划 LLM-Vision 读取）
- 既往报告对比

**实施**：
- LLM-Vision 解析（DeepSeek 走云端）
- 与基线对比 + 风险标注
- 子女收到"指标 X 偏离基线 Y%"
- v0.6 仅本地化，**不**自动预约医生
- **L1**（涉及健康）

**关联**：§38.11 + §54 LLM-Vision + §50

### 38.17 §38 19 场景汇总表（v0.6）

| # | 场景 | 类型 | 等级 | 治理 | §53 规则 | §54 视觉 |
|---|------|------|------|------|---------|---------|
| 38.13.1 | 老人主动询问 | 主 | L2 | 自动 | v0.6 加 | - |
| 38.13.2 | 老人被动接收 | 主 | L2 | 自动 + 推 | v0.6 加 | - |
| 38.13.3 | 老人说不舒服 | 主 | L1 | 强制 | v0.6 加 | - |
| 38.13.4 | 老人想控制 | 主 | L1/L2 | 按设备 | v0.6 加 | - |
| 38.13.5 | 找东西 | 主 | L2 | 自动 | v0.7 加 | 已有 |
| 38.13.6 | 找家人 | 主 | L2 | 自动 | - | - |
| 38.13.7 | 看电视 | 主 | L2 | 自动 + 夜间 L1 | v0.6 加 | - |
| 38.13.8 | 紧急求助 | 主 | L1 | SOS 旁路 | v0.6 加 | - |
| 38.14.1 | 跌倒 | 被 | L1 | 强制 | 已加 + 增强 | PoseDetector |
| 38.14.2 | 痴呆走失 | 被 | L1 | 强制 | 已加 + 视觉 | v0.3 |
| 38.14.3 | 慢病异常 | 被 | L1 | 强制 | v0.6 加 | - |
| 38.14.4 | 失禁/久坐 | 被 | L2 | 自动 | v0.6 加 | - |
| 38.14.5 | SOS 按钮 | 被 | L1 | SOS 旁路 | v0.6 加 | - |
| 38.15.1 | 照护代理共识 | 协 | L1 | 投票 | v0.6 加 | - |
| 38.15.2 | 保姆上下班 | 协 | L2 | 自动 | v0.6 加 | 已有 |
| 38.15.3 | 多老人区分 | 协 | L2 | 自动 | - | - |
| 38.16.1 | 续方下单 | 医 | L1 | 强制 | v0.6 加 | - |
| 38.16.2 | 急救流程 | 医 | L1 | SOS + 病史 | 已加 | - |
| 38.16.3 | 体检解读 | 医 | L1 | 强制 | v0.7 加 | LLM-Vision |

### 38.18 §38 实施时间表

| 版本 | 范围 | 数量 |
|------|------|------|
| v0.1-v0.4 | §38.6 + §38.7 + §38.8（跌倒/痴呆/可用性）| 8 项 |
| v0.5 | §38.11 慢病接口 | +2 |
| **v0.6** | **本节 19 场景全部文档化** | **+19** |
| v0.7 | §38.13.5 + §38.16.3 视觉联动 | +2 |
| v1.0 | 急救病史自动打包 / 续方实际下单 | +2 |

**v0.6 累计 §38 覆盖**：23 项（v0.4 8 + v0.5 2 + v0.6 19 - 重叠 6 = 23）

## 39. per-member 语言（v2.9 B 类 6）

> **用户拍板（v2.9）**：**per-member 语言**——管家按说话人切换 locale，自动识别说话人语言回复。

### 39.1 成员 locale

```sql
-- v2.17 修订：实际 ALTER 在 §39.6（locale 4 层分层），本节不重复定义
-- 历史: §39.1 早期版本曾在这里写 ALTER TABLE members ... v2.16 升级时已删除
```

### 39.2 自动识别说话人语言

**多语言家庭的实现**：
- 渠道已知 user_id → 直接查 members.locale
- 渠道未知（如游客） → 短期按当前会话 locale 推断
- 多语种混合输入 → 回复用**主语种**，夹杂说明时给翻译

### 39.3 时区契约

管家处理时间相关问题：
- 用户问"明天中午接娃" → 用 `member.tz` 解释
- "明天的天气" → 查该成员的当地时区
- "家里现在几点" → household 主时区

**实现**：所有时间字段在 SQLite 存 UTC ISO8601；展示时按 `member.tz` 转换。

### 39.4 跨时区成员协作

```
女儿（美东）在 TG 问："外婆今天生日，她那边几点？"
  → member.tz = Asia/Shanghai (当前 14:00) = America/New_York 当前 02:00
  → 答："外婆那边下午 2 点，你那边凌晨 2 点哦。"
```

### 39.5 多语种支持

**P1**：zh-CN（默认）+ en-US（完整支持）
**P2**：ja-JP、ko-KR、es-ES
**P3**：ar-SA（RTL 布局挑战）

**字符串**：所有用户可见字符串走 `i18n/zh-CN.json` / `en-US.json`，不允许代码里硬编码中文字符串。

### 39.6 locale 4 层分层模型（v2.16 修订）

> v2.16 修订：原 §39.1 单 `members.locale` 同时承担 UI 字符串 / LLM 回复 / ASR 方言 / TTS 音色 4 职，混乱。v2.16 拆为 4 个独立字段。

```sql
ALTER TABLE members ADD COLUMN locale TEXT DEFAULT 'zh-CN';
  -- 控制：UI 字符串 + LLM 回复 + 渠道回复
  -- 例：'zh-CN' / 'en-US' / 'ja-JP'

ALTER TABLE members ADD COLUMN tz TEXT;
  -- 控制：所有时间戳的展示时区
  -- 例：'Asia/Shanghai' / 'America/New_York'

ALTER TABLE members ADD COLUMN asr_locale TEXT;
  -- 控制：语音识别（ASR）的方言/口音
  -- 例：'zh-CN' / 'zh-Cantonese' / 'zh-Min-Nan' / 'en-US'
  -- v2.16 新增：从 members.accessibility.locale 独立出来（§38.6 旧写法）

ALTER TABLE members ADD COLUMN tts_voice TEXT;
  -- 控制：TTS 音色（个性化声音）
  -- 例：'female-1' / 'male-1' / 'child-friendly'
  -- v2.16 新增
```

**household.locale 语义**（v2.16 明确）：
- 用于**未识别说话人**（如系统主动消息、PWA 默认模式）
- **优先级低于** members.locale（已知成员用成员的）
- 不参与 ASR / TTS（这两个是个人化）

**§38.6 兼容性**：原 `members.accessibility.locale` 重命名为 `members.asr_locale`，§38.6 引用路径同步更新。

### 39.7 locale 冲突裁决

| 场景 | 规则 |
|------|------|
| 已知成员 + 渠道 user_id 映射 | members.locale（UI + 回复） + members.asr_locale（ASR） + members.tts_voice（TTS）|
| 已知成员 + 渠道未映射 | household.locale（fallback）|
| 未知说话人（访客 / 公共模式）| household.locale + asr 推断 |
| 多语混合输入（"妈妈说 hello"）| 主语种（成员主语言）回复，夹杂术语给翻译 |

## 40. 断电恢复（v2.9 B 类 7）

> **用户拍板（v2.9）**：**自动启动 + 补跑 + 校验核对**——NAS 上电即起，调度补跑延迟周期任务，启动时数据自检。

### 40.1 三层自愈

#### 层 1：服务自起

```
NAS 上电 → systemd / Docker restart policy → 服务拉起
  ↓
启动健康检查：
  - SQLite 可读写？
  - .env 凭据在？
  - 网络通？
  - LLM API 通？
  - **本机 NTP offset ≤30s（v2.15 新增）？** —— 否则黄灯
  ↓
任一不过 → 黄色状态灯，但服务仍提供降级能力
```

#### 层 2：调度补跑

服务挂掉期间**漏跑**的调度任务：
- 采集循环：每分钟 poll，下次正常时间继续（损失 ≤ 60 秒数据，可容忍）
- 分析循环：每 5 分钟，下次正常时间继续
- 节假日判断：启动时跑一次"过去 7 天节假日列表是否已记录"
- 过期告警：启动时跑一次"今天该报的过期"

**实现**：调度框架自带"补跑队列"，任务带 `last_run_at`，启动时检查 `now - last_run_at > period` 则补跑。

**v2.12 限流两个独立变量**：
- **并发上限 ≤4**（同时执行的任务数；保护 CPU / IO）
- **单任务触发上限 ≤3**（单次启动每个周期任务最多补 3 次；保护米家云端 API 节流）

#### 层 3：数据自检

启动后跑完整性校验：
- readings：连续 24h 无空段（如有 → 触发 §17 backfill）
- events：最近 1h 应该有值（如果 0 → 黄色告警）
- chat_history：最后一条 < 24h（如果超 → 提示用户）
- 加密 DB：解密成功

校验失败 → 写 `events.kind='integrity_check_failed'`，通知用户。

### 40.2 启动序列（v2.11 与 §48.4 合并为单一权威）

```
0s    systemd / Docker 拉起
3s    docker 健康检查通过（HEALTHCHECK ✓）
5s    myhome-agent 主进程启动
8s    §40 启动检查（健康、磁盘、加密）
10s   sync_from_cloud 首次执行（**首次执行非 catch_up 补跑**；v2.11 明确）
12s   §40 数据自检（readings 空段登记 events；v2.11 §48 修订）
13s   调度补跑（catch_up=true 业务任务并发补跑，限流 4 并发；v2.11 §48.4）
15s   服务就绪 → PWA 状态灯转绿
18s   后台调度任务首次跑（高频 poll / 采集）
```

**目标**：NAS 上电后 30 秒内管家"准备好"。
**v2.11 修订**：与 §48.4 合并为单一权威时间点；§48.4 已废弃独立时间表，仅保留"补跑限流 4 并发"作为流程说明。

### 40.3 灰启动策略

启动时**不立即推送**：
- 启动完成后**等 60 秒**（避免启动噪声）
- 这期间积累的事件合并推送（"刚才系统重启了，下面是这段时间发生的事"）

### 40.4 频繁重启检测

如果 24h 内重启 ≥3 次 → 自动告警：
- "系统频繁重启，可能磁盘或电源有问题"
- 自动 dump 最近日志供诊断

### 40.5 远程触发重启

admin 可远程触发：
- PWA "重启服务"按钮（仅在重启后产生新 autonomous_id 的前提下保留审计）
- "备份 + 重启"按钮（先 dump 再 restart）

---

## 41. v2.10 修订总览（索引）

> v2.10 是**架构稳定化版本**：补齐 §0-§40 多年迭代中累积的设计空白与矛盾，把架构推到"按这版直接动手实施"的状态。
>
> 本章是 §41-§48 的入口索引；详细在后续章节展开。

| 节 | 标题 | 类别 |
|----|------|------|
| §5.3b | 远程低危白名单 | 阻塞修复（F1，v2.10 新增）|
| §5.7b | 设备 spec 自动发现 | 关键设计（v2.3 已存在）|
| §5.7c | 影像通道 | 阻塞修复（F10）|
| §5.8b | PWA 必登录 | 阻塞修复（F4，F5.8 LAN 免鉴权风险）|
| §5.11 image 类目 | 上云数据契约加 image / URL | 阻塞修复（F11）|
| §30.0 | TLS 与可信访问 | 阻塞修复（F3，PWA Secure Context）|
| §37 | 三源验证防幻觉 | 阻塞修复（F8 多源自适应）|
| §42 | 规则模式（no-LLM 降级） | 阻塞修复（F5，v0.1 第一个里程碑）|
| §43 | 隐私与合规（GDPR-style） | 缺失章节 |
| §44 | 备份与灾备总览 | 缺失章节 |
| §45 | 版本与升级路径 | 缺失章节 |
| §46 | 设备模拟器与测试策略 | 缺失章节 |
| §47 | 单一权威 policy 表 | 阻塞修复（F12，替换 §5.3 / §14 / §24.2 / §31.2 四份分散真相）|
| §48 | 调度补跑与 catch_up 列 | 阻塞修复（F6/F7，解决 §5.0a vs §40.2 矛盾）|

## 42. 规则模式 no-LLM 降级（v2.10 新增，F5）

> **v2.10 用户拍板待确认（推荐采用）**：补齐 v0.1 的"确定性优先"基础——把**规则模式**作为第一个里程碑。即便无 API key / 云端长断 / 本地模型不可用，管家也能工作。

### 42.1 三个动机

| 问题 | 现有方案的缺陷 | 规则模式解决 |
|------|--------------|------------|
| L0 树莓派用户无本地模型 | §28.1 描述 L0 全依赖云端，没云端就没法用 | 规则模式不依赖 LLM，硬件最低档也能用 |
| 开源用户首次启动没 API key | 当前必须先买 key 才能体验 | 规则模式开箱即用，key 后配 |
| 云端挂 / 限流 | §11 降级矩阵只有"预设 FAQ"一句 | 规则模式是完整子集，覆盖查询+控制+告警 |

### 42.2 规则模式覆盖范围（v0.1 必做）

| 能力 | 实现方式 | 不需要 LLM |
|------|---------|-----------|
| **设备查询** | 关键字匹配 → 固定模板回复 | ✅ |
| **设备控制** | 关键字 + 白名单（§5.3b）→ 直接控制 | ✅ |
| **场景触发** | 场景名匹配 → 执行场景 | ✅ |
| **硬规则告警** | §5.3 + §11 + §16 配套（v2.12 修订：§16 是状态灯，硬规则本身定义在 §5.3 高危确认 + §11 降级矩阵）| ✅ |
| **告警确认 / ack** | PWA 按钮 / 命令 | ✅ |
| **历史回看** | SQLite 查询 + 模板 | ✅ |
| **日历 / 物品查询** | SQLite 查询 + 模板 | ✅ |

### 42.3 不在规则模式范围（需要 LLM）

- 多轮对话上下文理解
- 自然语言模糊查询（"今晚家里有点冷"）
- 异常归因（"为什么突然这么多告警"）
- 跨领域推理（"明天要聚餐，今天买菜了没"）
- 服务代办（需 GPT 解析下单意图）
- 任何需要工具链动态组合的操作

**关键边界**：规则模式**不假装是 LLM**——回复模板明确是模板口吻，不假装自然语言推理。

### 42.4 实现位置与回退逻辑

```
myhome_agent/agent/
├── router.py          # 顶层：LLM 模式 vs 规则模式
├── rule_mode/
│   ├── intent.py      # 关键字 + 模板匹配（少量规则就够）
│   ├── responses.py   # 模板回复（zh-CN / en-US）
│   └── actions.py     # 规则模式下的控制触发
└── core.py            # 现有 LLM agent
```

**回退触发**：
- 启动时无 `DEEPSEEK_API_KEY` → 规则模式
- LLM 调用连续失败 ≥3 次 → 自动回退规则模式（黄灯）
- 用户 PWA 切换开关"强制规则模式"（调试/隐私场景）

**v2.15 新增：恢复探测机制**

回退到规则模式后，必须能恢复回 LLM 模式：

```
自动恢复探测：
  - 规则模式期间，每 5 分钟发 1 次 LLM 健康探针（调用最便宜的 deepseek-chat 1 token）
  - 探针成功 → 自动切回 LLM 模式（绿/黄灯恢复）
  - 探针失败 → 延后 5 分钟再试；累计 24 次失败（2 小时）→ 推 PWA "LLM 暂不可用，请检查 API key 或云端状态"
  - 用户主动调用 PWA "重试 LLM" 按钮 → 立即探针

PWA 顶栏模式指示器增强：
  - 🧠 云端（绿）：正常
  - 🧠 云端 🟡（黄）：LLM 部分降级（仍可对话，但慢/失败率高）
  - 📋 规则（黄）：LLM 不可用，规则模式兜底；显示 "下次自动重试 X 分钟"
  - 📋 规则（红）：规则模式 + 24h 探针持续失败；需手动检查
```

**为什么 5 分钟探针（而不是更长）**：
- 太长：用户体验差，半夜 LLM 恢复用户不知道
- 太短：探针本身有成本 + 可能撞米家云端限流
- 5 分钟是平衡点

**模式指示器与 §16 状态灯的整合（v2.11 L 低-#12 加注）**：模式图标贴在 §16 状态灯 pill 左侧，不替换健康灯。三态：🧠 云端 / 🧠 本地 / 📋 规则。

**与 §47 policy 表的集成（v2.10.1 R8 加注）**：
- 规则模式下的所有**写动作**（控制设备、加物品、改日历等）仍走 `policies` 表（§47）`allow` 字段校验
- 规则模式 ≠ 绕过 RBAC；规则模式只是"用关键字匹配代替 LLM 解析"，**安全机制完全一致**
- 规则模式覆盖的能力（§42.2）必须在 `policies` 表里 allow=1 才生效
- 读操作（查询设备、看事件）不走 policy；但走 §5.11 脱敏

### 42.5 v0.1 验收口径

**v0.1 必须有规则模式**——这是 §42 拍板的核心。验收清单：
- 没 API key 时 PWA 能打开、能查设备、能控制灯、能看告警
- 规则模式回复模板清晰可识别
- PWA 模式指示器三态正确

## 43. 隐私与合规（GDPR-style，v2.10 新增）

> **v2.10 新增**——补齐 §32.4 假定但未定义的"删除级联"和"数据导出"。

### 43.1 数据类目分级表（单一权威）

| 类目 | 上云 | 默认状态 | 加密 | 保留期 | 删成员时 |
|------|------|---------|------|--------|---------|
| 设备状态读数 | 摘要 | 开 | 否 | 30 天细粒度 + 365 天小时级聚合 | 保留（设备不属个人）|
| 事件（门锁开门/移动）| 摘要 | 开 | 否 | 365 天 | 保留（审计）|
| 告警 | 摘要 | 开 | 否 | 365 天 | 保留 |
| 对话历史 chat_history | 摘要（脱敏后）| 开 | 否 | 90 天 | **清空该 member_id 行** |
| 对话索引 chat_fts | — | 开 | 否 | 同上 | **级联清空** |
| memories | 摘要 | 开 | 否 | 永久 | **按 member_id 标记 archived** |
| household_items（物品）| 摘要 | 开 | 否 | 永久 | 若 owner_member_id = 该成员，**标 archived_at**；否则保留 |
| household_calendar | 摘要 | 开 | 否 | 永久 | owner_member_ids 移除该成员，事件保留 |
| household_health | **不上云** | 关闭（默认）| **必选** | 永久 | **级联删除** |
| household_finance | **不上云** | 关闭（默认）| **必选** | 永久 | **级联删除** |
| household_relations | 摘要 | 开 | 否 | 永久 | from_member_id/to_member_id 该成员的**匿名化**（不删除，留关系结构）|
| elder_care_profiles | **不上云** | 关闭 | **必选** | 永久 | **级联删除** |
| persona_learn | — | 开 | 否 | 永久 | **级联删除**（最严格）|
| mi_accounts（米家账号）| — | 开 | **必选** | 直到解绑 | **级联删除** |
| push_subscriptions | — | 开 | 否 | 直到退订 | **级联删除** |
| autonomous_decisions | — | 开 | 否 | 永久 | **保留 + 该成员记 anonymous** |
| backup（整库备份）| — | — | **必选** | 见 §44 | 备份含历史，需单独清理流程 |
| voice_template（声纹模板，§51.4 opt-in）| **不上云** | 关闭（默认禁用）| **必选** | 直到启用者删除 | **级联删除**（启用者走 §43.3）|
| **routines（作息基线，v2.17 新增）** | 摘要 | 开 | 否 | 永久 | 按 member_id 标 archived（per-member 作息独立） |
| **presence（在场状态，v2.17 新增）** | — | 开 | 否 | **90 天滑动聚合**（§30.2b 配套）+ 单行当前态永久 | 级联清空（删 member → 立即移除 presence） |
| **scene_executions（场景执行历史，v2.17 新增）** | — | 开 | 否 | 永久（审计） | 保留 + 该 member 记 anonymous（场景是 household 共享行为） |
| **services_orders（服务订单，v2.17 新增）** | 摘要 | 开 | 否 | **180 天细粒度 + 365 天聚合** | 按 member_id 匿名化（订单归属个人）|

**关键不变式**：删成员 ≠ 删历史审计。审计（autonomous_decisions / events）保留但匿名；PII（聊天、个人偏好、健康、token）级联删除。

### 43.2 数据导出（P1 必做）

**单成员导出**：
```
GET /api/members/{id}/export?format=json|zip
   ↓
返回 zip 包：
  - profile.json
  - chat_history.jsonl
  - memories.json
  - autonomous_decisions.jsonl
  - elder_care_profile.json（如有）
  - mi_account_metadata.json（如有，token 不导出）
```

**全家导出**：admin 在 PWA "导出家庭数据"，含全部 household + members 数据 + schema 备份。

**导出延迟**：异步任务，5-30 分钟生成，下载链接 24 小时有效。

### 43.3 遗忘权（删成员完整流程，v2.11 与 §43.1 表对齐）

```
admin 在 PWA 选"删除成员 X"
   ↓
二次确认 "此操作不可逆，会清空 X 的全部个人数据"
   ↓
异步任务（v2.11 与 §43.1 表格逐行对应，10 步）：
  1. 写 events.kind='member_purge', member_id=X, detail='admin triggered'
     **重要**：member_purge 审计事件本身保留 member_id=X 不匿名化；
     其他历史 events 在批处理阶段改 anonymous_n（步骤 10）
  2. 清 chat_history / chat_fts（按 member_id 删行）
  3. 按 member_id 标记 memories.archived=1（§43.1 "按 member_id 标记 archived"）
  4. 解绑 mi_accounts：member_id → NULL，账号行保留（用于审计）；encrypted_token_blob 抹零
     **v2.11 修正**：原写法 "解绑保留" 与表格 "级联删除" 冲突——本节明确为
     "解绑 + 抹零 token + 保留账号 id"（行不删；token 必清；member_id 解绑）
  5. 级联删除 persona_learn（最严格，按 member_id）
  6. 级联删除 push_subscriptions（按 member_id）
  7. 匿名化 household_relations：from_member_id=该成员 → anonymous_n；to_member_id=该成员 → anonymous_n
  8. household_calendar.owner_member_ids JSON 移除该成员
  9. household_items.owner_member_id = null（若 owner 是该成员）
 10. **v2.12 修订**：autonomous_decisions 表 v2.11 后字段是 trigger_reason / decision_chain / actions_taken / review_status / evidence_path / household_id，**没有 member_id 字段**。
     所以匿名化在 JSON 嵌套层：
     `actions_taken` JSON 内嵌的 `member_id` 字段统一改 anonymous_n；
     `decision_chain` JSON 同理。
     其他历史 events：events 表有 `member_id` 字段（按 v2.12 §36.6 B 类派生于 member_id），保留事件本身但 `events.member_id = X → anonymous_n`。
     **v2.11 新增**：health / finance / elder_care_profiles 按 §43.1 都是"级联删除"
     ——步骤 7.5 / 7.6 / 7.7 执行 DELETE（不匿名化）
   ↓
完成推送 "X 数据已清除（除审计外）"
```

**不可删项**：审计事件（events / autonomous_decisions）按 §1b 永久保留，但**所有引用该成员 id 的字段改 anonymous_n**。

### 43.3b per-fact 删除（"忘记 XX"，v2.16 新增）

> v2.16 修订：原 §43 只覆盖 per-member 全量删除，per-fact 删除（用户说"忘记我爱吃辣"）完全缺失。

**API**：

```python
# myhome_agent/memory/forget.py（v2.16 新增）

async def forget_fact(
    fact_id: int | None = None,           # 精确删除（按 memories.id）
    query: str | None = None,             # 模糊删除（按关键词匹配）
    member_id: int | None = None,
    cascade_to: list[str] | None = None,  # 强制级联 ['memories', 'chat_history', 'chat_fts', 'persona_learn', 'routines']
) -> CascadeReport:                        # 引用 §49 UAMS 设计
```

**6 处可能含同一事实的位置的级联**：

| 位置 | 删除策略 |
|------|---------|
| `memories` | 按 `memories.id` 或 `content LIKE '%query%'` 标记 `archived=1` |
| `chat_history` | **单条级**（v2.16 首次定义）——按关键词搜索 → DELETE WHERE member_id=? AND content LIKE '%query%' |
| `chat_fts` | FTS5 trigger 跟随 chat_history（§21），自动同步 |
| `persona_learn` | **v2.17 修订**：不再按 `kind LIKE '%query%'` DELETE（kind 是信号类型不是事实内容，结果是空操作）——改为查关联的 `memories` 行标记 archived=1；persona_learn 仅保留元数据（信号类型 + 时间戳），不存可搜索事实文本 |
| `routines` | 若作息基线被该事实影响——按 routine_kind 关联删除；未关联则不动 |
| embeddings（P2 未来） | `sqlite-vec` DELETE vector WHERE 关联 ID |

**v0.1 限制**：
- 模糊删除基于 LIKE 关键词匹配，**不是语义级**（用户说"别记我下午开会"vs 系统找到"上午会议"）
- 删除前必须 PWA 二次确认 + 预览"找到 N 条匹配"，让用户选保留哪些

**CascadeReport 字段**（v2.16 扩 §49）：
- `deleted_ids[]`：memories / persona_learn 等
- `deleted_count[]`：chat_history 行数
- `failed_cascade[]`：跳过原因（如 routines 关联无）
- `audit_id`：写 events.kind='per_fact_forget' 审计

**与 §43.3 per-member 删除的关系**：
- per-fact 删除是 §43.3 的**精细化子操作**
- per-member 删除时调用 per-fact 删除 N 次（每个相关事实一次）
- 互不冲突：per-fact 删除不删除整个 member 的所有数据

**备份含历史（v2.16 修订）**：
- §43.1 已承认"备份含历史需单独清理流程"
- per-fact 删除后备份中的旧事实**最长 2 个月**可恢复
- 长期合规需 DBA 定期 clean backup（文档级声明）

**v2.11 表格 ↔ 流程对齐确认表**（双向可追溯）：

| §43.1 表行 | §43.3 步骤 |
|-----------|-----------|
| 对话历史 chat_history | 步骤 2 |
| 对话索引 chat_fts | 步骤 2 |
| memories | 步骤 3 |
| mi_accounts | 步骤 4 |
| persona_learn | 步骤 5 |
| push_subscriptions | 步骤 6 |
| household_relations | 步骤 7 |
| household_calendar | 步骤 8 |
| household_items | 步骤 9 |
| household_health | 步骤 7.5 |
| household_finance | 步骤 7.6 |
| elder_care_profiles | 步骤 7.7 |
| autonomous_decisions | 步骤 10 |
| events（历史）| 步骤 10 |
| devices / readings / alerts | 不处理（不属个人）|

### 43.4 未成年人特殊规则

- children (< 14) 的 `chat_history` 写入前**强制过滤 PII**（人名/电话/地址）
- children 的 autonomous_decisions 必须**显式 ack by adult** 才算确认
- children 的 `memories` 内容不参与跨成员场景
- 父母离婚/监护权变更 → 双方各 admin 角色 + elder_care_profiles 需双方各 ack 才能改

> **v2.10.1 R12 加注**：上述特殊规则在 `policies` 表（§47）里通过 `role='child'` + capability 维度实施；§14 RBAC 矩阵里 child 行只列基础权限，**这些 PII 过滤和 ack 约束是 PII 类目的隐式规则**——实施时落到 redactor.py（§5.11） 和 policies.autonomy_level=0（child 自主决策默认 L0，需 adult 升级）。

### 43.5 用户透明（v0.1 必做）

PWA `/settings/privacy` 显示：
- 当前数据类目 + 保留期 + 加密状态
- "导出我的数据" 按钮
- "删除我" 按钮（admin 角色下也给自己）

## 44. 备份与灾备总览（v2.10 新增）

> §RELIABILITY.md 详细技术；本节是主文档的**承诺层**——给用户看的。

### 44.1 承诺指标

| 指标 | 数值 | 说明 |
|------|------|------|
| **RPO**（恢复点目标）| ≤ 24h | 每日本地全量备份，最差丢失 24h 数据 |
| **RTO**（恢复时间目标）| ≤ 60 分钟（v2.11 修订）| 含 v0.1→v0.5 升级停机预告（§45.4）；对单纯恢复 ≤30 分钟 |
| **备份频率** | 每日 **03:00 本地时间**（v2.11 修订；与 §5.0a 03:00 + 03:30 聚合流水线对齐）| 每次重大操作前另增 pre-migration 备份 |
| **备份保留** | 本地：**7 日 + 4 周 + 2 月**（v2.11 修订；30 天滚动 = 7 日 + 4 周 + 2 月）| 与 §RELIABILITY §5.2 一致；总盘 ≤5GB |
| **备份加密** | 必选（§RELIABILITY §5.1b）| 备份独立 key（与 DB key 不同）|
| **异地副本** | 推荐；不开源默认；用户可挂 rclone | — |
| **恢复演练** | 季度一次（自动提醒）| — |
| **备份范围**（v2.16 新增）| **家庭配置包** = 整库 .db + config/*.yaml + i18n 覆盖 + .env 指纹清单（不含明文 key）| §45.3 升级备份同时包含此包 |

### 44.2 备份内容

```
backups/
├── daily/
│   └── backup-YYYY-MM-DD.db     # 整库加密
├── weekly/
│   └── backup-YYYY-Wnn.db       # 整库加密
├── monthly/
│   └── backup-YYYY-MM.db        # 整库加密
├── pre-migration/
│   └── backup-pre-NNNN.db       # 升级前自动
└── pre-purge/
    └── backup-pre-purge-X.db    # §43.3 删成员前
```

### 44.3 灾备等级（用户可配）

| 等级 | 含义 | 配置 |
|------|------|------|
| **L0 基础** | 仅本地 daily，保留 7 天 | 默认 |
| **L1 标准** | 本地 daily 30 天 + weekly 12 周 | 推荐 |
| **L2 异地** | L1 + rclone/S3 异地副本 | 网盘/家用 NAS |

PWA `/settings/backup` 配置 + 状态显示。

### 44.4 故障演练

每季度自动提醒 admin：
- "建议做一次恢复演练，请下载最近一次备份到另一台机器运行 `myhome-agent restore`"
- 演练结果记录到 events（不强制，但强烈建议）

**v2.18 关键修订：恢复后 §43 级联重放（GDPR 兼容）**

```
恢复流程：
  1. 旧备份 .db 覆盖（§44.2）
  2. 启动后扫 events 表，提取所有 events.kind='member_purge' 记录
     （events 表本身**不**随恢复回滚——是 §43.3 不可删项，§1b 永久保留）
  3. 按台账重放 §43.3 步骤 2-10：
     - 清 chat_history / chat_fts（按 member_id 删行）
     - 标记 memories.archived=1（按 member_id）
     - 解绑 mi_accounts + 抹零 token
     - 级联删除 persona_learn / push_subscriptions
     - 匿名化 household_relations
     - 移除 household_calendar.owner_member_ids
     - 清 household_items.owner_member_id
     - 删除 health/finance/elder_care_profiles
     - 匿名化 events.member_id → anonymous_n（除 member_purge 自身保留）
  4. 输出重放报告：清除 / 匿名化 行数统计
  5. 写 events.kind='post_restore_cascade_replay', detail=台账 vs 实际差异

v2.18 关键不变式：删除意图台账（events.member_purge）**永远不随恢复回滚**——
  - 即使从两个月前的备份恢复，已删除的成员仍按删除意图清理
  - 这是 §43 隐私承诺与 §44 灾备机制的硬约束
  - 实施：member_purge 事件写入单独的 append-only 表（events_partition='purge_log'），备份工具特殊处理
```

## 45. 版本与升级路径（v2.10 新增）

> §36 household_id 全栈串、§22 多家庭、§43 GDPR 删除——这些是**破坏性升级**。本节定下升级路径与兼容承诺。

### 45.1 语义化版本 + 运行时兼容矩阵（v2.15 增强）

```
vX.Y.Z
   ↑ ↑ ↑
   │ │ └── patch：bugfix + 数据迁移兼容
   │ └──── minor：新增能力，向后兼容
   └────── major：破坏性 schema/config 变更
```

**v2.15 新增：运行时兼容矩阵**

| binary 版本 \ schema 版本 | schema < binary | schema == binary | schema > binary |
|-------------------------|----------------|----------------|----------------|
| **行为** | 正常运行 | 正常运行 | **拒绝启动**（提示用户升级 binary）|
| **是否触发自动 migration** | 否（binary 不应改 schema）| 否 | — |
| **是否触发 migration 检查** | 是（确保 schema 未被破坏）| 是 | — |

**决策规则**：
1. **binary > schema**（多数情况）：启动时校验 schema_meta.version，发现缺 migration → 自动执行；缺升级脚本 → 警告
2. **binary == schema**：正常运行
3. **binary < schema**（用户没升级完整）：**拒绝启动** + 推送 PWA "binary v0.5 与 schema v0.6 不兼容，请运行 `myhome-agent upgrade`"
4. **major 不匹配**（schema v0.x + binary v1.x）：阻断运行，必须 major 升级路径
5. **patch 自动迁移**：binary patch 高于 schema → 自动执行 `migrations/000_patch_*.sql`；失败 rollback（§45.3）

**实现位置**：`myhome_agent/upgrade.py` 的 `check_compatibility()` 函数，启动时调。

### 45.2 升级契约

- **patch**：DB schema 不变；自动升级，无需用户操作
- **minor**：可能加表/加列；自动升级，旧功能不变；新功能 opt-in
- **major**：可能改 schema；启动前自动备份（§44 pre-migration/）；若失败保留旧版本可回滚

### 45.3 升级流程（v2.11 dry-run 拆分）

```
myhome-agent upgrade
   ↓
1. 检测当前版本（schema_meta.version）
2. 计算待执行 migrations（NNN_*.sql）
3. 调用 §44 backup.create_pre_migration() 创建 pre-migration/ 备份
   **v2.11 契约**：`create_pre_migration(name: str) -> Path` 在 §RELIABILITY §5.2 末尾定义；§44 与 §45 共用同一函数
   **v2.15 新增**：备份目录带镜像 tag 索引 —— pre-migration/<ts>-<from-version>-<to-version>/
   pre-migration 同时记录当前 docker image tag（`docker inspect --format '{{index .Config.Image}}'`）
4a. **dry-run**：模拟执行所有 migration（不写库；只在临时副本上跑）
   ↓ 校验通过
4b. 实际写库
5. 启动后做完整性校验（§40.3）
6. 失败 → 自动 rollback（v2.15 明确）：
   6a. docker compose down（停掉新版本容器）
   6b. docker tag myhome-agent:rollback-<from-version> myhome-agent:latest（用旧镜像 tag 覆盖 latest）
       镜像 tag 必须 pre-migration 之前已 `docker tag myhome-agent:v0.5 myhome-agent:rollback-v0.5` 保留
   6c. docker compose up -d
   6d. 用 pre-migration/ 备份 restore 数据库（§44 backup.restore）
   6e. 写 events.kind='rollback', detail=<reason>
7. 成功 → 写入 schema_meta.version
```

**v2.11 修订**：步骤 4 拆为 4a dry-run + 4b 实际写。**校验失败时按"未提交事务"自然回滚**，避免校验在已写入不可回滚的状态下才发现错误。

**v2.15 关键修订：rollback 与 docker 协调**：
- 步骤 6a-6e 6 步必须按顺序执行，不可跳过任一
- **关键**：pre-migration 备份**必须**在升级前 `docker tag` 保留当前镜像为 `rollback-<from-version>` tag（升级脚本自动执行）
- 若 rollback tag 缺失 → 升级脚本自动拒启动，提示"无可回滚镜像，请手动恢复"

> **v2.10.1 R10 加注**：步骤 3 必须是**调 §44 的 `backup.create_pre_migration()`**——不是另写一份；步骤 6 rollback 用同一份备份 restore。**§44 + §45 是连体设计**，分开实现会导致回滚失败。

### 45.4 关键破坏性升级预告

| 版本 | 变更 | 预计影响 |
|------|------|---------|
| v0.1 → v0.5 | household_id 全栈串、§36 实施 | **单次长时间停机**（估算 30-60 分钟，依 DB 大小）|
| v0.5 → v1.0 | §22 / §23 启用、加密全开 | 配置重置；备份恢复 |
| v1.x → v2.0 | 老数据迁移到新格式 | 工具转换 |

**承诺**：每个 major 版本**至少提前 1 个 minor 版本预告**，写进 changelog。

## 46. 设备模拟器与测试策略（v2.10 新增）

> §8.1 DoD 写"至少一次在自己家和 1 个开源用户家跑通"——这对开源项目是硬伤。

### 46.1 模拟器组成

```
tests/fixtures/
├── fake_miio_server.py        # 假 miio UDP server，能回复常用指令
├── cloud_api_mock.py          # 米家云端 API mock
├── spec_samples/              # 各类设备 spec fixture
│   ├── lock.m4pro.json
│   ├── light.xiaomi.json
│   ├── sensor.water_leak.json
│   ├── camera.xiaomi.json
│   └── ...
├── scenario_fixtures/         # 场景 fixture
│   ├── evening_arrival.yaml
│   ├── night_lockup.yaml
│   └── ...
└── household_fixtures/        # 家庭数据 fixture
    ├── 1family_basic.yaml
    ├── 3gen_elder.yaml
    └── ...
```

### 46.2 测试层次

| 层次 | 工具 | 范围 |
|------|------|------|
| **单元测试** | pytest | 各模块纯函数 + DB CRUD |
| **集成测试** | pytest + fake 模拟器 | 端到端不含真实硬件 |
| **场景测试** | pytest-bdd 或 yaml | §31.3 验收清单 9 项覆盖 |
| **回放测试** | sqlite fixture replay | 用真实生产 DB 快照回放，验证升级安全 |
| **CI 必跑** | GitHub Actions | 单元 + 集成 + 场景；不依赖外部网络 |

### 46.3 模拟器作为开源贡献门槛

**贡献新设备支持**：
1. 在 `tests/fixtures/spec_samples/` 加你的设备 spec JSON
2. 在 `fake_miio_server.py` 加对应指令响应
3. 加测试用例 `tests/integration/test_<your_device>.py`
4. CI 自动跑通过 → 可发 PR

**贡献新功能**（如新服务 adapter）：
1. 在 `tests/fixtures/services/` 加 mock 服务响应
2. 加适配器测试
3. 写 4 道闸门的单元测试
4. CI 通过 → 可发 PR

### 46.4 §31.3 v1.0 验收清单可重写为场景

原本的 §31.3 是 9 项验收；按模拟器可执行化后变成：
- `tests/scenarios/test_lock_water_leak_alert.py` 模拟门锁 + 水浸触发推送
- `tests/scenarios/test_holiday_lights_gradient.py` 模拟春节灯光渐变
- ... 共 ~15 个场景

> **v2.10.1 R9 加注**：这些场景测试是 **§27.2 E0-8（设备模拟器）** 的验收标准；CI 必跑——任何涉及设备的 PR 必须通过场景测试才能合并。

## 47. 单一权威 policy 表（v2.10 新增，F12）

> 解决 §5.3 / §14 / §24.2 / §31.2 四份分散真相的"谁能做、多危险、要不要确认"。

### 47.1 单一权威表（v2.11 补 FK + channel 通配 + seed 补字段）

```sql
CREATE TABLE policies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  capability_id TEXT NOT NULL,
  role TEXT NOT NULL,             -- admin / adult / child / assisted_adult / care_taker / guest
  channel TEXT NOT NULL,          -- pwa_local / telegram / wechat / voice / email / service_adapter / *
  household_id INT,
  
  allow INTEGER NOT NULL,         -- 1 = 允许，0 = 拒绝
  confirm_tier TEXT NOT NULL,     -- none / low / medium / high
  autonomy_level INT NOT NULL,    -- 0..4 (L0-L4)
  
  updated_at TEXT NOT NULL,
  updated_by TEXT,
  notes TEXT,
  
  FOREIGN KEY (capability_id) REFERENCES capabilities(capability_id) ON DELETE RESTRICT,   -- v2.17 修订：原 device_capabilities → capabilities（§31.2 v2.16 改名）
  UNIQUE (capability_id, role, channel, household_id)
);
```

**v2.11 修复点**（v2.17 修订）：
- **FOREIGN KEY** 约束：`capability_id` → `capabilities(capability_id) ON DELETE RESTRICT`——避免孤儿 capability 行（RELIABILITY L109 已启用 `PRAGMA foreign_keys = ON`）
- **channel 枚举扩充**：补 `email`（§34.3 / §32.2 日报邮件）+ `*`（通配兜底）
- **`*` 通配与 UNIQUE 的处理**：SQLite 中通配与具体 channel **优先级在查询层决定**，不是 DB 层。具体 channel 行 > `*` 行；查询算法见 §47.6

**capability_id** 是 §31.2 `capabilities` 表的主键（**唯一权威来源**——v2.17 修订：原 device_capabilities 已改名 capabilities，§36.6 / §47.5 / §5.0b 全面同步）。

### 47.2 §5.3 降级为视图

§5.3 渠道分级表 = `policies` 按 channel × capability 过滤的视图。

### 47.3 §14 RBAC 矩阵降级为默认视图

§14 角色 × 设备类型矩阵 = `policies` 表的默认种子（system 启动时插入）。**v2.11 修复**：seed 写入时自动补 `updated_at = boot, updated_by = system`（避免 NOT NULL 拒）：

```yaml
# 启动时种子（首次安装；updated_at/updated_by 由系统自动补）
- capability_id: control_light, role: child, channel: pwa_local, allow: 1, confirm_tier: none, autonomy_level: 3
- capability_id: control_thermostat, role: child, channel: "*", allow: 0, confirm_tier: high, autonomy: 0
- capability_id: control_lock, role: "*", channel: "*", allow: 0, confirm_tier: high, autonomy: 0
# v2.11 新增：§5.3b 远程低危白名单
- capability_id: control_light, role: "*", channel: telegram, allow: 1, confirm_tier: none, autonomy_level: 2
- capability_id: control_fan, role: "*", channel: telegram, allow: 1, confirm_tier: none, autonomy_level: 2
- capability_id: control_humidifier, role: "*", channel: telegram, allow: 1, confirm_tier: none, autonomy_level: 2
- capability_id: control_lock, role: admin, channel: pwa_local, allow: 1, confirm_tier: high, autonomy_level: 1  # 远程禁，仅本地可
- capability_id: control_gas_valve, role: "*", channel: "*", allow: 0, confirm_tier: high, autonomy_level: 0  # 系统级锁
# ...
# v2.12 修订：seed YAML 仅示例 8 条；完整 seed 由 §14 RBAC 矩阵 + §5.3b 白名单 + §24.2 等级矩阵
# 程序化生成在 `policies_seed.py`，详见 §47.3 README
```

用户可在 PWA `/settings/policies` 修改。修改写审计。

### 47.4 §24.2 自主等级矩阵降级为默认视图

§24.2 矩阵 = `policies` 表 autonomy_level 字段的默认种子。**与 §14 RBAC 严格正交**：RBAC 是硬门（allow=0 拒绝一切），自主等级只在门内生效。

### 47.5 §31.2 capabilities 引用（v2.17 修订：原 §47.5 device_capabilities 引用）

§31.2 `capabilities` 表是 `policies.capability_id` 的**外键来源**——所有 capability 必须先在 capabilities 注册。**v2.11 补 FK 后**：删除 `capabilities` 一行会被 `policies` 引用时 `ON DELETE RESTRICT` 阻断——必须先删引用该 capability 的 policies。

### 47.6 决策流程（v2.11 优先级明确化）

```
agent 收到指令：
   ↓
1. NLU（规则/LLM）解析意图 → capability_id
2. 查 policies WHERE capability_id, role, channel, household
   优先级（v2.12 三维度）：
     a1) 特定 household_id 行（如 5）
     a2) household_id IS NULL 通配行（跨家庭默认）
     b1) 具体 channel 行（如 telegram）
     b2) channel = "*" 通配行
     c) 都没有 → 拒绝
   顺序：household_id 优先于 channel（先 a1→a2，再 b1→b2）
3. allow=0 → 拒绝（解释原因）
4. confirm_tier ≠ none → 进入二次确认流程（§5.3）
5a. **v2.18 新增：profile_confidence 降级**（防新成员冷启动期无画像时同权自主）
    - 查 members.profile_confidence
    - 若 &lt; 0.5 → 无论 policy 如何一律 autonomy_level ≤ 1（强制确认）
    - profile_confidence &gt; 0.7 后恢复 policy 默认 autonomy_level
5b. **v2.18 新增：irreversibility_tier 兜底不变式**
   - 查 capabilities.irreversibility_tier
   - 若为 'irreversible' → 强制 confirm_tier='high' + autonomy_level ≤ 1（即使 policy 设 L2/L3 也降为 L1）
   - §5.6b 撤销窗对 irreversible capability **不生效**——走前置确认（事前确认而非事后撤销）
6. autonomy_level 决定自主 vs 询问（§24）
7. 执行
```

**单一真相，永远是 `policies` 表**。§5.3 / §14 / §24.2 是表的可视化视图，不是规则源。

**v2.18 关键不变式**：irreversible capability 上限 L1 + 强制 confirm，无视 policy 表其他设置。
- 例：开门 capability（已开门外人已进）+ 燃气切断（已停气邻居已在煮饭）+ 已发送短信（已发出无法收回）
- 这三类动作的事前 confirm 是最后防线——撤销窗对它们无效

### 47.7 角色扩展（§38 老人守护）

§47.1 角色枚举新增：
- `assisted_adult`：权限=adult，但金钱/门锁类动作强制经 `care_taker` 复核
- `care_taker`：可代看 care 对象数据；不继承 adult 全部权限

§38.2 紧急求助 + §38.4 子女/照护者视图（v2.12 修订：原 "§38" 未指明子节）：老人守护走 `assisted_adult` 角色，不再用普通 `adult`。

## 48. 调度补跑与 catch_up 列（v2.10 新增，F6/F7）

> 解决 §5.0a "错过不补跑" 与 §40.2 "调度补跑" 直接冲突；§17 "readings 不补" 与 §40.3 "空段触发 backfill" 矛盾。

### 48.1 catch_up 列（v2.11 默认值修订）

`scheduled_tasks` 表加 `catch_up` 列（**默认 false**——v2.11 中-#9 修订；高频任务不应默认补跑）。

| 任务类型 | catch_up | 理由 |
|---------|---------|------|
| poll 采集 | false | 高频幂等，丢失 1 周期可容忍 |
| analytics 分析 | false | 同上 |
| routines 学习 | **true** | 业务任务，错过有意义 |
| alerts 评估 | **true** | 可能漏告警 |
| holiday 判断 | **true** | 业务语义，错过会有错 |
| item 过期扫描 | **true** | 业务必跑 |
| calendar 展开 | **true** | 业务必跑 |
| elder check-in | **true** | 守护任务必跑 |
| web push 重试 | **true** | 用户体验 |
| order 追踪 | **true** | 业务必跑 |
| runtime re-probe | false | 系统级，24h+ 周期重跑 |
| 数据库备份 | **true** | RPO 承诺（§44） |
| RPO/RTO 校验 | **true** | 备份完整性必须跑 |
| TPM 余额对账 | **true** | 业务必跑 |
| chat_history 清理 | **true** | 保留期承诺 |

### 48.2 调度框架行为

```
每次调度任务执行：
  1. 检查 now - last_run_at 是否 > period
  2. 如果 catch_up=true 且 > 1× period → 补跑一次
  3. 如果 catch_up=false → 跳过（next_run_at 不变）
  4. 执行实际任务
  5. 更新 last_run_at = now
```

**关键不变量**：**catch_up=false 的高频任务不补跑**——避免启动后一轮补跑炸服务器。

**v2.18 新增：max_backlog 硬规则 + 恢复后对账（防"两个月漏跑一次性引爆"）**

```
catch_up 触发前加 backlog 阈值检查：
  - 计算 backlog = now - last_run_at
  - backlog &gt; 7× period → 不补跑，写 events.kind='catch_up_backlog_dropped'
    detail={task, period, backlog, dropped_at}
  - 不覆盖 last_run_at（保留真实历史）
  - last_run_at = now - period（重排到正常节拍）
  
rationale：从两个月前的备份恢复时，§44 restore 流程同步重放 §43 级联后，
           §48.2 last_run_at 仍指向两个月前；不设上限则 holiday/用药/老人 check-in
           会全部触发补跑，且 notification_deliveries 的旧 idempotency_key 失效
           导致重复推送

§44.4 恢复演练流程新增"恢复后对账"步骤：
  - 标记恢复窗内 notification_deliveries 为 voided（status='voided_by_restore'）
  - PWA 横幅告知 admin 被跳过的业务量："恢复自 YYYY-MM-DD，共 X 条通知作废"
  - §30.4 离线窗口 + §48.2 max_backlog 联动 → 12-7 = 5 天内的 care 级仍补发，
    超出窗口的丢弃（避免淹没真实告警）
```

### 48.3 readings 空段处理（v2.12 修订：标题从 §40.3 改为正确引用）

**v2.12 修订**：原标题写"§40.3 readings 空段处理"——**错**。§40.3 是"灰启动策略"，数据自检在 §40.1 层 3，readings 空段处理在这条 §48.3 自身。

§40.1 层 3 原写"readings 空段触发 backfill"——**改正**：
- readings 不补（§17 已声明，本地丢失无数据可补）
- 空段改为**登记 `data_gap` 事件**：`events.kind='data_gap', metric=X, start_ts=Y, end_ts=Z`
- PWA 状态灯显示"近 24h 有 N 个数据缺口"
- 用户可选择"接受"（不补）或"用云端历史补"（backfill 仅限 cloud API 可拉的设备 + 时间段）

### 48.4 启动补跑序列（v2.11 已并入 §40.2 单一权威）

启动序列的权威时间表见 [§40.2](#402-启动序列v211-与-484-合并为单一权威)。本节仅保留：

```
13s   调度补跑（catch_up=true 业务任务并发补跑）
      限流 4 并发；触发 §RELIABILITY §4.1 节流
```

补跑累积上限（v2.11 中-#20 修复）：catch_up 路径必须接 §RELIABILITY §4.1 限流矩阵；每次启动补跑 ≤3 次，避免挂机 1 小时后触发 12 次 push / 30 次 order 追踪。

---

## 49. 与 UAMS（universal-agent-memory）的整合决策（v2.13 用户拍板）

> **决策日期**：v2.13 拍板
> **决策内容**：**暂不整合 UAMS**，v0.1 阶段专注 myhome-agent 自实现。

### 49.1 为什么暂不整合

| 因素 | 当前状态 |
|------|---------|
| UAMS 版本 | v0.7.0 Beta / Pre-production |
| UAMS SQLite 后端 | **不支持向量搜索**（v0.7 自承认；需升级到 PG + ChromaDB）|
| UAMS 4 层记忆模型 | 借鉴但 myhome-agent 现状是单层 `memories` 表 |
| UAMS 工具生态 | uams-inspect / uams-doctor / uams-migrate / uams-bench 4 个 CLI |
| 部署依赖 | UAMS 4 后端可插拔（InMemory / SQLite / PG / Redis / Neo4j / ChromaDB），myhome-agent 单 SQLite 哲学不一致 |
| 治理模型 | UAMS 用 `tenant_id`；myhome-agent 用 `household_id`（v2.12 §36.6 权威化）—— 语义重叠但设计不同 |

### 49.2 myhome-agent 自实现路径（v0.1）

**单层 `memories` 表**：
- P1 阶段：content + tags + member_id + household_id（已有）
- 跨 session 复用：靠 §21 chat_fts BM25 + `memories` LIKE 命中
- 上下文注入：手写（§5.10b 端到端示意）

**§43 GDPR cascade forget**：
- P1 阶段：§43.3 手动 10 步流程
- 借鉴 UAMS `CascadeStrategy.ISOLATED/BIDIRECTIONAL/FULL_CASCADE` 思路，但不引入依赖

**§5.11 redactor**：
- P1 阶段：单层脱敏表
- v0.5 升级方向：参考 UAMS PrivacyFilter 的 SECRET/PII 分级

### 49.3 v0.5+ 再评估的触发条件

| 触发条件 | 说明 |
|---------|------|
| 真实用户反馈"对话检索差" | FTS5 BM25 不够，需要向量 + RRF |
| §21 chat_fts 在 30 天以上老对话命中失败 | 阶段 2 FTS 边界到达 |
| 多家庭 + 强 tenant 隔离需求 | 治理模型升级 |
| UAMS 升级到 v1.0 GA | 项目稳定到能引入依赖 |

**任一触发 → 重新评估 §49 决策，方向上：**
- 把 `memories` + `chat_history` cross-session 部分切到 UAMS
- 保留 myhome-agent 自己的 `devices` / `presence` / `household_calendar` / `policies` / `autonomous_decisions`（UAMS 不覆盖）

### 49.4 不变的边界（永远不切给 UAMS）

- `devices` / `readings` / `events` —— 设备数据底座
- `presence` —— 在场状态
- `household_items` / `household_calendar` / `holidays` —— 家务领域
- `services_orders` / `scene_executions` —— 业务执行
- `autonomous_decisions` —— 自主行为审计
- `policies` —— 权限真相
- `elder_care_profiles` —— 老人守护（高度敏感 + 加密）
- `redactor_config` —— 脱敏规则
- `household_id` —— 治理模型

### 49.5 共同技术债（已识别但暂不修）

- OpenAI 兼容 LLM 客户端：UAMS 有，myhome-agent 也有（v2.1 重写为 DeepSeek）—— 后续可提 `myhome_agent/llm/` 共享层
- SQLite schema v2 `tenant_id` 列：UAMS v0.6 加；myhome-agent `household_id`（§36.6 B 类派生）—— 两项目同作者可同步演进

---

## 51. 成员区分度设计（v2.14 新增）

> **核心问题**：myhome-agent 能区分不同的家庭成员吗？——答案是**"按任务区分"**，不需要精准识别每个人的生物特征。v2.14 系统化梳理区分度的 3 层次 + 4 个具体场景。

### 51.1 区分度 3 层次

**L1：基于角色**（v2.13.1 已实现）

- 信号：§47 policies `role` 字段
- 角色枚举：admin / adult / child / assisted_adult / care_taker / care_proxy / family_viewer / guest
- 适合：**公共任务**（查天气、开公共区域灯、查家庭事件）
- 不适合：私人任务、远程 ack

**L2：基于身份**（v2.13.1 已实现 + 待加强）

- 信号：§5.8 渠道身份映射（TG user_id / 企微 openid / PWA passkey）+ §5.4 门锁指纹 UID
- 适合：**私人任务**（私人偏好、吃自己的药、家庭日记、子女远程 ack）
- 加强方向：§51.3 物理设备共用 + §51.6 访客账号生命周期

**L3：基于声纹/人脸**（v2.14 设计决策点）

- 信号：声纹特征 / 人脸特征（生物识别）
- 适合：**高安全场景**（远程开门前的"是谁在说话"、老人意外时的"是奶奶还是外人"）
- 决策：见 §51.4 — **默认禁用**，按场景可启用
- 哲学：**任务越私密，越需要精准识别；越公共，越不需要**

### 51.2 各任务所需区分度对照表

| 任务 | 所需区分度 | 信号来源 | v2.14 状态 |
|------|----------|---------|----------|
| 查温度/天气/家庭总况 | L1 | 不需要 | ✅ |
| 开公共区域灯/调温 | L1 | 不需要 | ✅ |
| 看家庭日历/事件 | L1 | 不需要 | ✅ |
| 私人偏好（"爸爸喜欢 26 度"）| L2 | 渠道身份 + memories 标记 | ✅ |
| 私人日记/备忘录 | L2 | 渠道身份 + 加密字段 | ✅ |
| 吃药提醒（"奶奶的药"）| L2 | 老人账号关联 | ✅ |
| **远程开门确认** | L3 | 声纹 + 视频 | 🟡 §51.4 决策 |
| **远程子女 ack 老人** | L2 强 | 子女账号（必 L2 登录）| ✅ 章节 |
| 老人意外紧急求助 | L3 | 声纹 + 在场推断 | 🟡 §51.4 |
| 访客进入 | L1 + 临时 guest | 访客配对 link | 🟡 §51.6 |

**关键不变量**：任务分类时，**过度精准识别是隐私伤害**——只看家庭总况不应该拿到声纹。

### 51.3 物理设备共用方案（v2.14 新增）

> **场景**：客厅的 iPad 老人 + 妈妈 + 孩子都用——"登录一次就锁定一个人"违反家庭共享现实。

**3 种共用模式**：

| 模式 | 实现 | 适用 |
|------|------|------|
| **A. 自动切换（推荐）** | 摄像头检测人脸识别 → 自动切换当前成员 | 有摄像头 + 启用 face_recognition |
| **B. 物理按钮/手势** | PWA 顶栏点"切换成员"→ 4 位 PIN 验证 | 无摄像头 / 隐私敏感 |
| **C. 公共模式** | 平板默认"家庭公共账号"——只显示全家共享内容；私人内容需主动登录 | 简化场景 |

**默认策略**：**A + C 组合**——
- 默认进入"家庭公共模式"（看天气、家庭事件、通用偏好）
- 涉及私人任务（私人日记、买药、个人偏好修改）→ 触发 L2 登录（passkey/PIN）
- 有摄像头时启用自动切换（v2.14 §51.4 决策）；无摄像头 → 手动"切换成员"按钮

**实现位置**：
- PWA `/settings/who-is-using` 配置
- `sessions.device_id` 字段记录"当前会话是谁用这台设备"
- 摄像头人脸识别是 opt-in（默认关）

**风险与缓解**：
- 自动切换可能误识别（小孩长得像）→ 加"3 秒静默期"——确认后再切换
- 公共模式可能被误用 → 涉及金钱/门锁的强制 L2 登录

### 51.4 声纹识别决策点（v2.14 关键决策）

> **决策**：v2.14 **默认禁用声纹识别**。声纹是隐私敏感生物特征，比人脸轻但仍是 PII。开源家庭场景下不应默认开启。

**默认行为**：

| 维度 | 默认 |
|------|------|
| 声纹采集 | ❌ 默认禁用 |
| 声纹模板存储 | N/A（不采集） |
| 声纹模板上云 | N/A |
| 启用场景 | P3 远期 / 用户显式开启 |
| 替代方案 | §51.3 物理设备共用方案 A（摄像头人脸） |

**为什么默认禁用**：
1. **生物特征不可撤销**——泄露即永久泄露
2. **声纹比密码更脆弱**——录音即可重放攻击
3. **家庭场景不需要 L3 精准**——L2 渠道身份已足够 95% 任务
4. **法律风险**——欧盟 GDPR/中国《个人信息保护法》对生物特征有特殊保护

**何时必须 L3**（即便默认禁用）：

| 场景 | 替代方案 | 启用声纹的条件 |
|------|---------|--------------|
| 远程开门"是谁" | 多重确认（密码 + 视频 + 子女远程 ack） | 永远不 |
| 老人意外"是本人还是外人" | 在场推断（手机/门锁/摄像头）+ L2 | 永远不（摄像头已足够）|
| 紧急求助确认 | 老人 PWA/音箱账号（已绑定）| 永远不（账号绑定更准）|

**声纹启用的硬约束**（用户主动开启时）：

```
1. 显式开启（PWA /settings/biometrics/voice）
2. 仅在用户指定设备启用（不上传到管家后台）
3. 声纹模板本地存储，加密（§22.5 加密分级）
4. 不上云（§5.11 redactor 类目下加 voice_template 强制禁外发）
5. 可一键删除（§43.3 cascade forget 路径已包含 voice_template 表）
```

**未来 v2.x 才考虑的开放问题**：
- 声纹 + 多模态融合（声音 + 视频）的误识别率
- 声纹模型压缩到设备端（小于 50MB）
- 老人声音特征衰退的模型老化问题

### 51.5 同位置多人在场推断（v2.14 新增）

> **场景**：客厅里有奶奶 + 妈妈 + 保姆三个人，谁在说话？

**多人在场推断的 3 个信号叠加**：

```
信号强度（从强到弱）：
1. 物理位置（蓝牙信标 1-3m 精度 + 房间人体传感器）
2. 时间窗口（最近 10 分钟在哪个房间）
3. 设备活跃度（谁的手机/手环最近有运动）
```

**优先级**：物理位置 > 时间窗口 > 设备活跃度

**多人在场时的"指令归属"原则**：

| 场景 | 归属判断 |
|------|---------|
| **单人说话** | L1 角色 + L2 渠道身份 |
| **多人同时说话** | 失效 — 默认按 L1 角色最低权限（如 guest），或提示"请再说一次" |
| **指令明确（"妈妈我饿了"）** | 名字识别 → L2 身份 |
| **指令模糊（"开灯"）** | 默认 L1：公共任务，无需精准 |
| **指令矛盾（A 说开 B 说关）** | 默认拒绝 + 询问 |

**蓝牙信标部署**（可选）：
- 每个成员随身带蓝牙信标（手环 / 手机蓝牙）
- 家庭部署 3-5 个 BLE 接收器（每个房间一个）
- 精度 1-3 米，覆盖所有房间
- 成本：信标 5 元/个，BLE 接收器 30 元/个

**决策**：v0.1 不强制要求蓝牙信标——这是 P2 升级路径

### 51.6 访客账号生命周期（v2.14 新增）

> **场景**：临时访客到家里，第一次用 PWA/TG bot——账号怎么登记？

**访客的 4 种类型**：

| 类型 | 特征 | 账号处理 |
|------|------|---------|
| **临时访客**（朋友、邻居临时来）| 1-7 天 | 自动生成访客账号 + 24h 自动清理 |
| **常客**（每周来的阿姨、保姆）| 长期 | 申请 upgrade 到 care_proxy（§38.10）|
| **跨家庭访客**（在多个家庭用管家）| 多个 | 每个家庭独立访客账号；用户管理"我的家庭清单" |
| **儿童访客**（小朋友来玩）| 临时 | guest 角色 + 自动转交家长视角 |

**访客账号生命周期**：

```
首次登记：
  - admin 邀请 link（§19）/ 临时 QR 码
  - guest 角色默认 + 有效期（默认 24h，可调）
  - 访客接受的权限：公共任务 + 受限控制
  - 访客拒绝的权限：私人内容 / 长期场景 / 高危控制

期间续期：
  - 24h 到期前 1h 推送 admin（"访客 X 即将到期，是否续期？"）
  - admin 同意 → 续期 N 小时
  - 不同意 → 自动清理

到期清理：
  - 访客账号删除（§43.3 cascade forget 路径包含 guest 角色）
  - 该访客的 chat_history / chat_fts 按 member_id 全删；memories 按 member_id 标记 archived=1（v2.16 修订：与 §43.3 步骤 3 一致，不再是"全部清除"）
  - 访客离线后再来 → 需要重新登记
```

**家庭清单（跨家庭）**：

```
访客 A 在 3 个家庭都注册过：
  - 家 1（自己家）：adult 角色
  - 家 2（女友家）：guest 角色
  - 家 3（父母家）：adult 角色

PWA "我的家庭" 列表切换：
  - 当前家庭上下文（household_id）决定可见数据
  - 切换家庭 → 重新加载角色 + 权限
```

### 51.7 成员区分度总览（v2.14 必加）

```
┌─────────────────────────────────────────────────────────┐
│  成员区分度设计 v2.14                                    │
│                                                         │
│   §51.1 区分度 3 层次                                       │
│     - L1 角色（已实现）                                    │
│     - L2 身份（已实现 + 加强）                              │
│     - L3 声纹（v2.14 默认禁用，P3 远期）                   │
│                                                         │
│   §51.2 任务所需区分度对照表                                 │
│     - 10 类任务 × 3 层次映射                                │
│                                                         │
│   §51.3 物理设备共用方案（A+C 默认组合）                     │
│   §51.4 声纹识别决策（默认禁用 + 5 硬约束）                  │
│   §51.5 同位置多人在场推断（3 信号叠加）                     │
│   §51.6 访客账号生命周期（4 类型 + 自动清理）                │
│                                                         │
│   关键不变量：                                               │
│   - 任务越公共，越不需要精准识别                             │
│   - 任务越私密，越需要 L2 登录（passkey/PIN）                │
│   - 永远不上传生物特征到云端                                 │
│   - 访客到期 = 隐私保护默认行为                              │
└─────────────────────────────────────────────────────────┘
```

**v2.14 §7 风险表新增 4 条 🟡**：
- 多人共用 PWA 无快速切换（§51.3 解决）|
- 声纹识别策略需文档化（§51.4 决策）|
- 同位置多人在场细分缺失（§51.5 解决）|
- 访客账号无生命周期（§51.6 解决）|

---

## 52. 通知路由模型（v2.16 新增）

> 全文只有 alerts.level（safety/care/info）+ "safety 不可静音不变式"，但没有任何一节定义**优先级契约 / 免打扰 / 汇总 / 跨渠道去重 / 投递回执 / 阶梯升级**六项。v2.16 一次性补齐。

### 52.1 优先级契约（safety > care > info）

| 等级 | 投递规则 | 静默豁免 | ack 时限 | 可否汇总 |
|------|---------|---------|---------|---------|
| **safety**（水浸/燃气/烟雾/老人紧急）| **全渠道并行** + **阶梯升级**（见 §52.6）| ❌ 永久豁免（不可静音、不可静默时段覆盖）| 30s 内必须有 ack | ❌ **永不汇总**（每条独立）|
| **care**（异常告警/用药提醒/门外人）| 选渠道列表 + 时间窗 | ✅（老人 quiet_hours 可推迟但不可删）| 5min | ✅ 5min 内同类汇总 |
| **info**（场景触发/日常报告/礼貌提醒）| per-member 偏好 | ✅ | 无 | ✅ 1h 汇总 |

**safety 不可静音不变式**（v2.16 强化，v2.18 扩展）：
- 不被 quiet_hours 覆盖（§38.3 老人守护）
- 不被节假日策略覆盖（§35.3 假日）
- 不被灰启动延迟（§40.3 启动 60s 内合并推送）
- **v2.18 新增：系统健康降级（infra_health）继承 safety 不变式**
  - §16 状态灯触发 🔴 时，**也**写入 `alerts.priority_safety=1`（不再走独立推送路径）
  - 路由层只读 priority_safety 字段，不区分"safety 告警"vs"infra 降级"
  - 家人度假 DND 期间，infra 降级仍能穿透（最该知道的人收得到）
- **v2.18 新增：SOS 直通例外（§38.2 老人救命 + §38.7 Level 3 + §38.8 痴呆紧急求助）**
  - 这些 alert 来源的 ladder **跳过 attempt 1-3**，直接执行 attempt 4（voice phone to care_taker）
  - ladder 仅用于其后的重试计数（attempt 4 内重试 3 次 + 跨 attempt 重试）
  - §38.2 反向引用该例外；§52.6 ladder 表加 SOS 旁路说明
- 实现位置：`alerts.priority_safety INTEGER DEFAULT 0` + 通知路由层强制读这个字段

### 52.2 免打扰（per-member 通用化）

```
elder_care_profiles.quiet_hours_* （§38.3 老人专属）
  ↓ v2.16 扩展为
members.notification_prefs (JSON):
  {
    "quiet_hours": [
      {"start": "23:00", "end": "07:00", "days": ["mon","tue","wed","thu","fri"]},
      {"start": "12:00", "end": "14:00", "days": ["sat","sun"]}    # 午休
    ],
    "vacation_until": null,                # v2.18 新增：长期/度假 DND 显式到期时间戳
                                          # 例："2026-08-15T18:00:00Z"  → 到期后自动失效
                                          # safety 仍穿透（§52.1 不变式）
    "channels": {                           # 渠道偏好
      "pwa":   {"enabled": true, "priority": 1},
      "tg":    {"enabled": true, "priority": 2},
      "email": {"enabled": true, "priority": 3},
      "sms":   {"enabled": false}            # 老人不用 SMS
    },
    "digest": {"window_minutes": 60, "max_items": 10}  # care/info 汇总
  }
```

**v2.18 新增：陈旧 DND 检测（防"度假忘了恢复"）**

```
调度任务：每 6 小时跑一次 DND 陈旧检测
  - 条件：DND 连续生效 >48h（含 vacation_until 未到 + quiet_hours 周内反复触发）
    AND 期间 care 级 ack 数为 0
  - 动作：推 admin 一条豁免提醒
    "家人 DND 已生效 X 小时，期间 care 告警未被任何人 ack —— 仍需保留吗？"
  - 不自动关闭 DND（避免误操作）
  - 写 events.kind='dnd_stale_alert', detail={hours_since_start, ack_count}
```

**v2.16 与 §38.3 兼容**：elder_care_profiles.quiet_hours_* 仍存在，但**优先级低于** members.notification_prefs.quiet_hours——后者是通用机制。

### 52.3 汇总（digest）

```
触发条件：time window 内同类别告警 ≥3 条
汇总形式：
  "过去 1 小时您家出现 3 次开门事件：14:30 爸爸回家、15:00 快递、16:45 妈妈回家"
不汇总：
  - safety 等级（每条独立推送）
  - 涉及金额/门锁/燃气（敏感）
  - 用户主动询问的（避免混淆）
```

**v2.18 新增：DND 退出时积压投递策略**

| 积压类型 | 释放策略 |
|---------|---------|
| care 级 | 按 5min 窗切分为多条 digest 并间隔发送（防止洪泛） |
| info 级 | 合并为单条总览（不超过 digest.max_items=10） |
| 超出上限 | 折叠可展开（不丢弃）—— 用户可在 PWA 展开看全部 |


### 52.4 跨渠道去重

```
每个事件有 idempotency_key：
  format: hash(autonomous_id + member_id + category + summary)[:16]
  - 同一 idempotency_key 在 5min 内不重复发送
  - 不同渠道发送同一 key 视为"扩散"而非"重复"

notification_deliveries 表：
  alert_id INT,
  channel TEXT,           -- 'pwa' / 'tg' / 'email' / 'sms' / 'voice'
  member_id INT,
  idempotency_key TEXT,
  sent_at TEXT,
  ack_at TEXT,
  attempt INT DEFAULT 1,  -- 阶梯升级尝试次数
  status TEXT             -- 'pending' / 'delivered' / 'acked' / 'failed'
```

### 52.5 通知订阅矩阵

```
per (member × category × channel) 三维矩阵：
  members.notification_subs (
    member_id INT,
    category TEXT,         -- 'safety' / 'care' / 'info' / 'summarize'
    channel TEXT,
    enabled INTEGER DEFAULT 1,
    priority_rank INT      -- 同等级内渠道优先级（1=最优先）
  )
默认：safety → 全渠道 / care → PWA+TG+Email / info → PWA only
```

### 52.6 阶梯升级（escalation ladder）

> §38.7 跌倒检测的 Level 0-3 是硬编码分段，不是通用升级链。v2.16 抽象出通用 ladder。

```
通用 ladder（per alert，v2.17 修订 attempt 4 责任边界）：
  attempt 1:  PWA push + WS (默认；最快)
  attempt 2:  5min 后无 ack → TG/微信 push（per-member.channels.priority_rank）
  attempt 3:  10min 后无 ack → SMS（紧急情况）
  attempt 4:  15min 后无 ack → voice phone **to care_taker / primary contact**（仅 safety，不打 120/110/119）
    - 120/110/119 走 §38.12 急救流程（§38.7 Level 3 + §38.2 "救命"）→ 管家**不**自动拨，由 PWA 一键拨号按钮人工触发
    - care_taker / primary contact 走 §23.6 safe-action 白名单（v2.17 修订）：管家自动拨属于"家庭紧急联络"动作

每个 step 在 notification_deliveries 写一行 attempt=N
§38.7 Level 0-3 是这套 ladder 在"跌倒"场景的具体参数

**v2.18 新增：阶梯升级终止态（§52.9 终态语义）**

```
safety 全 attempt 失败（即 notification_deliveries.status='failed' on attempt 4）：
  1. 写 alerts.escalation_exhausted=1（v2.18 schema 新增字段）
  2. 状态灯强制 🔴（继承 §16 健康降级路径，与 §52.1 修订联动）
  3. 本地音箱 + PWA 强制横幅（绕过所有渠道偏好）
     "有一条紧急告警从未送达 —— 管理员请人工核查"
  4. 下次任意成员打开 PWA 第一眼看到此横幅（直到 alerts.escalation_exhausted 被人工 ack）
  5. 触发 §15 capability_drift 类似逻辑：events.kind='escalation_exhausted', detail=尝试记录

rationale：海外/度假场景（唯一可用渠道恰好被静音）下这条路径命中概率不低
           ——终态不是"静默失败"，而是"下一次触达时强制可见"
```
```

### 52.7 与 §34.3 的关系

§34.3 是远程访问层；§52 是通知路由层。两者**正交**：
- §34.3 解决"通过什么渠道收到消息"（远程访问能力）
- §52 解决"什么消息走什么渠道 + 什么时机 + 几次重试"（路由策略）

### 52.8 §5.0a 调度任务新增

| 任务 | 周期 | catch_up | 失败降级 |
|------|------|---------|---------|
| **notification_deliveries 重试阶梯（v2.16 新增）** | 1min | ❌ | 阶梯升级 attempt+1 |
| **汇总窗口扫描（v2.16 新增）** | 5min | ❌ | 跳过下次 |

## 53. 跨信号推理规则引擎（v2.19 新增）

> 全文已有 §38 老年守护 24 场景、§52 通知路由 6 维、§5.6b 反馈环、§42 规则模式，但**没有任何一节定义"多信号联合 → 状态判定 → 置信度 → 行动"的完整机制**。v2.19 一次性补齐。
>
> **核心定位**：规则引擎是"管家在没有 LLM 介入时也能主动判断"的引擎。它不替代 LLM，而是**让管家 99% 的时间不需要 LLM**——只有模糊地带才交给 LLM 兜底。

### 53.0 章节地图

```
§53.1 设计目标与边界（什么做 / 什么不做）
§53.2 规则 DSL 规范（YAML 4 段结构）
§53.3 调度与执行模型（窗口聚合 + 周期性扫描）
§53.4 置信度校准（基础 × 4 个因子）
§53.5 误报闭环（用户反馈 + 自动学习）
§53.6 规则治理（4 种来源 + 4 张表）
§53.7 规则与已有模块的对接（不重复造轮子）
§53.8 调试与可观测性（每次 fire 都是结构化记录）
§53.9 性能边界（100 条规则 × 20 设备 ≤ 200ms）
§53.10 实施里程碑（v0.1 → v1.0）
§53.11 与 §50 缺失的处理（v2.19 留 v3 治理）
§53.12 修订注记（v2.19 变更总览）
```

### 53.1 设计目标与边界

#### 53.1.1 为什么需要规则引擎

**三个事实**：

1. **LLM 不适合做实时判定**——单次推理 500ms-3s，token 贵，且不可重现（同一信号不同时间可能不同结论）
2. **米家 App 只做"事件 → 动作"**——单设备触发，无法判断"该发生没发生"
3. **§38 老年守护 24 场景如果全靠 LLM 判定，月度成本会爆**——一个家庭一个月可能 1000+ 次判定

**结论**：管家 99% 的"该发生没发生"判断必须用**确定性规则引擎**。LLM 只在规则覆盖不到、信号矛盾、置信度 < 0.3 时介入。

#### 53.1.2 与 §42 规则模式的关系

| 维度 | §42 规则模式 | §53 规则引擎 |
|------|-------------|-------------|
| 触发方式 | **场景触发**（cron / 事件 / 手动） | **状态触发**（信号窗口函数） |
| 输入 | 单一事件 | **多信号聚合** |
| 输出 | 设备动作 | **判定 + 告警 + 升级** |
| 表达力 | YAML 步骤序列 | YAML 谓词 + 逻辑组合 |
| 复杂度 | 简单序列 | 复杂表达式 + 置信度 |
| 适用 | 出门 / 回家固定流程 | 老人异常 / 漏水 / 陌生人判定 |

**关系**：§42 是"动作编排器"，§53 是"判定器"。两者**正交互补**——判定器触发动作编排器（例：§53 判定"老人起夜异常" → 调 §42 场景"应急呼叫")。

#### 53.1.3 什么不做（边界）

| 不做 | 原因 | 留给 |
|------|------|------|
| 复杂规则表达式（条件嵌套 5 层以上） | 维护成本爆炸 | v3+ |
| 规则市场 / 跨家庭共享 | 隐私 + 责任 | v3 治理框架 |
| CEP 引擎（Drools / Flink CEP） | 性能过剩 | 永远不必 |
| 机器学习自动生成规则 | 不可解释 | v3+ |
| 实时流处理（毫秒级） | 家用场景不需要 1s 内 | 永远不必 |
| 跨家庭规则编排 | 单实例 ≤3 家庭限制 | 不需要 |

### 53.2 规则 DSL 规范

#### 53.2.1 四段结构（YAML 顶层）

每条规则**必须**包含 4 段（缺一段即 YAML 解析失败）：

```yaml
id: <string, unique, kebab-case>             # 唯一标识
description: <human-readable, 一句话>        # 描述（用于 LLM 解释时回显）
when: <predicate tree>                       # 触发条件
then: <action list>                          # 触发动作
```

**可选段**：

```yaml
confidence_base: <0.0-1.0>                   # 基础置信度（默认 0.7）
cooldown: <seconds>                          # 同一规则不反复触发（默认 3600）
window: <window-spec>                        # 窗口规格（默认 1min）
feedback: <feedback-spec>                    # 反馈机制（默认开启）
meta: <key-value>                            # 元数据（作者/创建时间/最后触发/误报次数）
```

#### 53.2.2 谓词（最小集）

**v2.19 谓词白名单**（不允许 v2.19 之外的谓词）：

| 类别 | 谓词 | 例子 |
|------|------|------|
| 数值 | `eq` / `ne` / `gt` / `gte` / `lt` / `lte` / `between` | `sensor.bed_pressure.away_minutes > 30` |
| 时序 | `away_minutes` / `since_minutes` / `duration_minutes` | `sensor.motion.living_room.duration_minutes > 30` |
| 时窗 | `time.in_window` / `weekday.in` / `date.in` | `time.in_window: ["22:00", "06:00"]` |
| 成员 | `member.is_alone` / `member.role` / `member.count` | `member.is_alone_at_home: true` |
| 传感器 | `sensor.fresh` / `sensor.value` / `sensor.changed` | `sensor.fresh(<=60s): true` |
| 聚合 | `all` / `any` / `none` | `all: [pred1, pred2, ...]` |
| 派生 | `household.in_mode` / `weather.condition` | `household.in_mode: "night"` |

**DSL 严格规则**：
- 谓词 ≤ 50 个（v2.19 起步 25 个，剩余 v2.20 视需求补）
- 嵌套深度 ≤ 4 层（强制 + 静态检查）
- 单条规则条件数 ≤ 20（多于 20 强制拆分）
- 任意谓词引用不存在的 sensor → 规则**不加载**，事件进 `rule_audit_log.kind='invalid_predicate'`

#### 53.2.3 完整规则示例：老人起夜异常

```yaml
# v2.19 §53.2.3 示例 1 — 系统预设
id: elderly_fall_suspect_v1
description: |
  独居老人夜间起夜后长时间未归床，疑似摔倒或突发不适。
  联合判定：床压离床 + 客厅人体存在 + 持续 >30 分钟。
confidence_base: 0.7
window: 1min
cooldown: 3600
when:
  all:
    - sensor.bed_pressure.away_minutes > 30
    - sensor.motion.living_room.present == true
    - sensor.motion.living_room.duration_minutes > 30
    - time.in_window: ["22:00", "06:00"]
    - member.is_alone_at_home: true
    - sensor.fresh(<=60s, "bed_pressure"): true
    - sensor.fresh(<=60s, "motion.living_room"): true
then:
  - escalate:
      ladder: [primary_caregiver, secondary_caregiver, neighbor, 120]
      timeout_per_step: 15min
      ack_required: true
  - record_evidence: true
  - capture_snapshot:
      cameras: ["living_room", "hallway"]
      ttl: 30min
feedback:
  ask_user_after_fire: true
  ttl: 24h
  options:
    - label: "是真的异常"
      effect: confidence_boost +0.05
    - label: "误报"
      effect: confidence_penalty -0.05
    - label: "忽略"
      effect: rule_pause 24h
meta:
  author: system
  category: elderly_care
  severity: safety
  created: 2026-08-03
  references: [§38.6, §38.7]
```

#### 53.2.4 完整规则示例：水管微量泄漏

```yaml
# v2.19 §53.2.3 示例 2 — 系统预设
id: water_microleak_night_v1
description: |
  凌晨无人时段水表持续小流量，疑似水管/水龙头微量泄漏。
  关键：没人用水 + 流量持续 = 漏。
confidence_base: 0.85
window: 5min
cooldown: 7200
when:
  all:
    - sensor.water_meter.flow_l_per_hour > 0.5
    - sensor.water_meter.flow_l_per_hour < 5.0
    - sensor.water_meter.duration_minutes > 60
    - member.is_alone_at_home: false
    - time.in_window: ["02:00", "05:00"]
    - sensor.fresh(<=300s, "water_meter"): true
then:
  - escalate:
      ladder: [primary_caregiver]
      timeout_per_step: 30min
      level: care
  - record_evidence: true
  - suggestions:
      - "检查水槽 / 卫生间 / 洗衣机进水管"
      - "看下用水曲线截图"
feedback:
  ask_user_after_fire: true
  ttl: 48h
meta:
  author: system
  category: water_safety
  severity: care
```

#### 53.2.5 完整规则示例：孩子放学异常

```yaml
# v2.19 §53.2.3 示例 3 — 家属自配
id: child_school_pickup_v1
description: |
  孩子平时 16:20-16:40 回家，今日到时未归。
  联合：门锁未开 + 校门口 GPS 静止 + 无活动 = 异常。
confidence_base: 0.6
window: 5min
cooldown: 1800
when:
  all:
    - sensor.front_door.lock.opened_30min == false
    - sensor.gps.child.school_zone_distance < 100
    - sensor.gps.child.duration_minutes > 30
    - time.in_window: ["16:30", "17:30"]
    - weekday.in: ["mon", "tue", "wed", "thu", "fri"]
    - calendar.has_event("school_day"): true
then:
  - notify:
      to: [primary_caregiver]
      level: care
      template: "孩子可能没接到人，已在校门口 30 分钟"
  - suggestions:
      - "打电话给班主任"
      - "看看同学群有没有当天留堂通知"
feedback:
  ask_user_after_fire: true
  ttl: 12h
meta:
  author: family_caregiver
  category: child_care
  severity: care
```

#### 53.2.6 完整规则示例：陌生人在门口停留

```yaml
# v2.19 §53.2.3 示例 4 — LLM 建议 + 人工确认
id: stranger_porch_loiter_v1
description: |
  门口摄像头检测到陌生人停留 >3 分钟，全家都在外。
  联合：人形 + GPS 全家外出 + 门锁未开 = 异常。
confidence_base: 0.75
window: 1min
cooldown: 1800
when:
  all:
    - sensor.camera.porch.person_count > 0
    - sensor.camera.porch.duration_minutes > 3
    - member.is_alone_at_home: false
    - any_family_at_home: false
    - sensor.front_door.lock.opened_10min == false
then:
  - escalate:
      ladder: [primary_caregiver]
      timeout_per_step: 5min
      level: safety
  - capture_snapshot:
      cameras: ["porch", "driveway"]
      ttl: 60min
  - record_evidence: true
feedback:
  ask_user_after_fire: true
  ttl: 12h
meta:
  author: llm_suggested
  validated_by: family_admin
  validated_at: 2026-08-03
  category: security
  severity: safety
```

#### 53.2.7 规则动作（then）合法集

| 动作 | 参数 | 用途 |
|------|------|------|
| `escalate` | ladder / timeout_per_step / level / ack_required / **sos_bypass** | 走 §52 通知路由。**sos_bypass: true → §52.1 SOS 直通例外（跳过 attempt 1-3 直接 attempt 4）** |
| `notify` | to / level / template | 单次通知（不升级） |
| `record_evidence` | true | 记录证据快照（30 天） |
| `capture_snapshot` | cameras / ttl | 拉摄像头快照 |
| `execute_scene` | scene_id | 调 §42 场景模式 |
| `suggestions` | array | 推送建议文案（不自动执行） |
| `log` | level / message | 仅记录不通知（用于观察） |

**非法动作**（v2.19 显式禁止）：
- 任何 `delete_*` / `reset_*` / `modify_*` 类动作（必须经 §5.3 高危确认流程）
- 任何动作直接修改 capabilities / policy 表（必须经 §47 policy 治理）
- 任何动作触发 §42 之外的"动作即编排"

### 53.3 调度与执行模型

#### 53.3.1 三层架构

```
┌─────────────────────────────────────────┐
│ Layer 3: 动作执行                       │
│  - escalate / notify / execute_scene    │
│  - 走 §52 路由 / §42 场景模式           │
└─────────────────────────────────────────┘
              ↑
┌─────────────────────────────────────────┐
│ Layer 2: 规则引擎（§53）                │
│  - 周期性扫描所有启用规则（默认 10s）   │
│  - 状态机 + 置信度计算                  │
│  - 输出：判定 fire / 不 fire            │
└─────────────────────────────────────────┘
              ↑
┌─────────────────────────────────────────┐
│ Layer 1: 数据采集与窗口聚合             │
│  - readings 流（原始时序）              │
│  - 窗口聚合（1min / 5min / 60min）      │
│  - 状态保持（rule_state 表）            │
└─────────────────────────────────────────┘
```

#### 53.3.2 窗口聚合（window 字段）

每条规则必须声明自己需要的窗口粒度：

| window | 含义 | 适用 |
|--------|------|------|
| `1min` | 1 分钟滑窗聚合 | 摔倒检测、陌生人徘徊 |
| `5min` | 5 分钟滑窗聚合 | 漏水、孩子放学 |
| `60min` | 1 小时滑窗聚合 | 用电异常、设备故障 |
| `1day` | 1 天聚合 | 月度趋势、习惯学习 |

**性能约束**（v2.19 草案）：
- 1min 窗口 ≤ 100 条规则
- 5min 窗口 ≤ 50 条规则
- 60min 窗口 ≤ 30 条规则
- 1day 窗口 ≤ 20 条规则
- 单次扫描总耗时 ≤ 200ms（详见 §53.9）

#### 53.3.3 状态机：每条规则 5 个状态

```
disabled → cold_start → armed → firing → cooldown
                            ↑          ↓
                            └──────────┘
```

| 状态 | 含义 | 进入条件 | 退出条件 |
|------|------|---------|---------|
| `disabled` | 规则被关闭 | 人工 / 误报过多 / 传感器失效 | 人工启用 |
| `cold_start` | 数据积累期（窗口未填满） | 刚启用 | 第一个窗口填满 |
| `armed` | 待命扫描 | cold_start 完成 / 上次 cooldown 结束 | 条件匹配 → firing |
| `firing` | 已触发执行 | armed 状态条件匹配 | 动作完成 + 进入 cooldown |
| `cooldown` | 抑制再触发 | firing 完成后 | cooldown 到期 → armed |

**关键设计**：
- `cold_start` 期间**不**触发任何动作（避免冷启动误报）
- `cooldown` 期间规则**仍扫描**，但命中只写 `audit_log` 不执行
- 状态全部持久化到 `rule_state` 表（重启后恢复）

#### 53.3.4 周期性扫描器

```python
# v2.19 §53.3.4 草案伪代码
class RuleEngine:
    SCAN_INTERVAL = 10  # 秒

    async def scan(self):
        for rule in self.rules.where(enabled=True, state__in=['cold_start','armed','cooldown']):
            # 1. 取窗口数据
            window_data = self.window_store.get(rule.window, rule.id)

            # 2. 评估谓词
            try:
                matched = self.evaluator.eval(rule.when, window_data)
            except StaleDataError:
                self.audit(rule, kind='stale_data')
                continue

            # 3. 计算置信度
            confidence = self.calibrate(rule, window_data)

            # 4. 状态机
            if matched and rule.state == 'armed':
                if confidence >= 0.3:
                    await self.fire(rule, confidence)
                    rule.transition('firing')
            elif rule.state == 'cooldown':
                if matched:
                    self.audit(rule, kind='cooldown_suppressed', confidence=confidence)

            # 5. 更新状态
            rule.state_update_at = now()
            self.state_store.save(rule)
```

#### 53.3.5 失败降级

| 失败 | 触发 | 降级 |
|------|------|------|
| 传感器掉线 | `sensor.fresh(<=60s)` == false | 规则自动降级 `armed` → `disabled`，写 `audit_log` |
| 窗口数据缺失 | 聚合器抛 `InsufficientDataError` | 规则保持 `cold_start`，不触发 |
| evaluator 抛异常 | 谓词树评估失败 | 规则**禁用** + 写 `audit_log.kind='eval_error'` + 通知 admin |
| 动作执行失败 | escalate / notify 失败 | 走 §52 重试阶梯（4 attempt） |
| 扫描超时 | 单次扫描 > 200ms | 报警 + 降级到 30s 扫描间隔 |

**核心原则**：**任何失败都不应导致规则"假装正常"**——v2.18 §16 已确立的不变式在这里同样适用。

#### 53.3.6 与 §5.0a 调度任务的关系

§53 调度任务清单（v2.19 新增）：

| 任务 | 周期 | catch_up | 失败降级 |
|------|------|---------|---------|
| **规则扫描（v2.19 新增）** | 10s | ❌ | 降级到 30s 间隔 |
| **窗口聚合清理（v2.19 新增）** | 1min | ❌ | 跳过下次 |
| **cooldown 推进（v2.19 新增）** | 1min | ❌ | 自动 drift |
| **误报自动暂停检测（v2.19 新增）** | 1h | ❌ | 通知 admin |
| **规则文档健康检查（v2.19 新增）** | 1day | ❌ | 记录 |
| **LLM 兜底推理调度（v2.19 新增）** | 按需（≤10/天/家） | ❌ | 超限 → 降级到 §42 + 提示 admin |
| **规则自动学习扫描（v2.19 新增）** | 1day | ❌ | 写 audit_log + 推 PWA |

> 与 §52.8 调度任务去重：通知重试、汇总扫描仍是 §52.8 唯一职责，§53 不重复。

### 53.4 置信度校准

#### 53.4.1 公式

```
final_confidence = base
                 × freshness_factor      # 传感器新鲜度
                 × history_match_factor  # 历史模式匹配度
                 × member_baseline_factor # 成员基线偏离度
                 - false_positive_penalty # 历史误报惩罚
```

| 因子 | 范围 | 默认 | 含义 |
|------|------|------|------|
| `freshness_factor` | 0.5-1.0 | 1.0 | 传感器新鲜 → 1.0；陈旧（>2 倍窗口）→ 0.5 |
| `history_match_factor` | 0.7-1.0 | 1.0 | 该 pattern 历史上 80% 是真异常 → 1.0；20% → 0.7 |
| `member_baseline_factor` | 0.6-1.0 | 1.0 | 该成员历史基线偏离大 → 1.0；正常 → 0.6 |
| `false_positive_penalty` | 0.0-0.5 | 0.0 | 该规则 30 天内误报数 × 0.05 |

#### 53.4.2 置信度区间与处置

| 区间 | 含义 | 处置 |
|------|------|------|
| **≥ 0.9** | **高可信** | 自动执行（acknowledged_by=system） |
| **0.6 – 0.9** | **中可信** | 执行 + 同步通知（家长可见） |
| **0.3 – 0.6** | **低可信** | 仅通知 + 询问（不强执行） |
| **< 0.3** | **不确定** | 进"可疑信号池"，兜底 LLM 推理 |

**关键不变式**（v2.19 确立）：
- `safety` 等级规则**默认 confidence_base ≥ 0.7**，人工配置 ≤ 0.5 强制二次确认
- `irreversible` capability 关联规则**默认 confidence_base ≥ 0.9**（如关阀、删除）
- 任何规则 `false_positive_penalty > 0.4` 自动 `disabled` + 通知 admin

#### 53.4.3 兜底 LLM 推理

触发条件（同时满足）：
1. 规则 final_confidence < 0.3
2. 至少 2 条规则同时进入"低可信"
3. 信号之间存在矛盾（ex：卧室有人 + 床压显示无人）

LLM 推理任务（v2.19 §28.3 LLM 路由）：
- 输入：最近 24h 信号 + 家庭成员画像 + 规则历史
- **所有兜底推理输入强制加 EvalContext.household_id WHERE filter（§36 强制）；§5.11 redactor 输出后再走 LLM（避免 household_id 字段被脱敏掉时丢失隔离锚点）**
- 输出：自然语言解释 + 建议动作 + 置信度
- **关键**：LLM 推理**不直接执行动作**，必须经 §5.3 高危确认（safety）或 §52 通知（care）

**v2.19 修订（审计 A 问题 1 修复）**：兜底推理走 §28.3 LLM 路由，由 §6.4.5 决定本机/云端：
- L2-L4 硬件：优先本机 Layer 2 轻量 LLM（≤10 次/天/家）
- L1 入门硬件（无本地 LLM）：强制走 Layer 4 云端
- **所有层 10 次/天上限指本机层**；云端不计（云端按 §5.11 redactor 后的 token 计费）
- 超限后二次降级：超过 10 次/天 → 降级到 §42 规则模式 + 提示 admin"建议校准规则"

**成本控制**：
- 单家庭 LLM 兜底调用 ≤ 10 次/天（v2.19 草案）
- 超过 → 写 `audit_log` + 提示"该家庭信号吻合度低，建议重新校准规则"

### 53.5 误报闭环

#### 53.5.1 用户反馈机制

**触发时机**：
- 规则 fire 后 24h 内（v2.19 默认；可调）
- safety 等级 fire 立即询问（不等 24h）
- 询问渠道：PWA 横幅 + 推送通知（不走 SMS，避免打扰）

**反馈选项**（4 选 1）：

| 选项 | 效果 | 备注 |
|------|------|------|
| "是真的异常" | `confidence_boost +0.05`、`true_positive_count++` | 上限 0.95 |
| "误报" | `confidence_penalty -0.05`、`false_positive_count++` | 下限 0.10 |
| "忽略" | 规则 `pause 24h`、不增减计数 | 临时抑制 |
| "禁用此规则" | 规则先 `disabled` → 24h 后自动 `archived_at` → 30 天后硬删 | **v2.19 修订**：改为两段式软删除，与 §43 GDPR 兼容 |

**反馈超时**：
- 24h 内未反馈 → 默认"忽略"（不影响置信度）
- 高频规则（30 天内 fire > 10 次）反馈超时率 > 50% → 提示"该规则过于频繁，是否需要调整条件"

**v2.19 修订（审计 A 问题 6 修复）**：
- **author 撤销（GDPR §43.3）级联**：规则 author_id = X 走 §43.3 10 步流程时，author 创建的规则 `archived_at = now()`（不依赖 24h 临时期）
- §43.1 表新增 "rules 4 张表 → author 撤销时 archived_at 级联（v2.19）"
- §36.2 step 9 scenes 同步：搬家时 rules 4 张表跟随 household 切换，老 household 规则归档只读

#### 53.5.2 自动学习

**自动暂停规则**（v2.19 草案）：
- 同一规则 30 天内 `false_positive_count > 5` → 自动 `disabled`
- 提示admin："该规则需要复审，连续 5 次以上误报"
- 不可自动启用——必须人工决策

**自动降级**：
- `final_confidence < 0.3` 连续 14 天 → 提示"建议删除或重写"
- `false_positive_count > 0` 且 `true_positive_count == 0` 持续 30 天 → 提示"该规则 30 天内零命中"

**自动提议**（v2.19 草案，v2.20 完善）：
- LLM 周期性分析 `rule_audit_log`，发现：
  - A 规则误报率高 → 提议收窄条件
  - B 场景无规则覆盖 → 提议新增规则
- 提议**必须**人工确认才能启用（不自动写 rules 表）

#### 53.5.3 反馈审计

每次反馈都进 `rule_feedback` 表，结构化字段：

```sql
CREATE TABLE rule_feedback (
  id INTEGER PRIMARY KEY,
  rule_id TEXT NOT NULL,
  fire_id INTEGER NOT NULL,         -- 关联 rule_audit_log
  member_id INTEGER NOT NULL,       -- 谁反馈的
  feedback TEXT NOT NULL,           -- 'true_positive' | 'false_positive' | 'ignored' | 'disable'
  note TEXT,                        -- 用户备注（可选）
  created_at INTEGER NOT NULL
);
```

**关键设计**：
- 反馈只能由 admin 或 fire 时涉及的家庭成员给出（避免误操作）
- 反馈**不可撤销**——但管理员可手动调整 rule.meta.confidence_base 撤回效果
- 反馈数据用于 v2.20 训练"规则可信度 ML 模型"（v2.19 不做）

### 53.6 规则治理

#### 53.6.1 4 种规则来源

| 来源 | 谁写 | 谁能改 | 谁能停 | 标注 |
|------|------|--------|--------|------|
| **系统预设** | 开发者 | 开发者 | admin | `meta.author: system` |
| **医生建议** | 医生 | 医生 + admin 共审 | admin | `meta.author: doctor` |
| **家属自配** | 家庭成员 | 家庭成员 | 家庭成员 | `meta.author: family_caregiver` |
| **LLM 建议** | LLM 生成 | **必须人工确认**才能启用 | 家庭成员 | `meta.author: llm_suggested` + `meta.validated_by: <member_id>` |

#### 53.6.2 权限矩阵（与 §47 policy 表挂钩）

| 操作 | 系统 | 医生 | 家属 (admin) | 家属 (caregiver) | LLM |
|------|------|------|--------------|------------------|-----|
| 创建规则 | ❌ | ✅ (需 admin 审) | ✅ | ✅ | ⚠️ 仅生成草案 |
| 编辑规则 | ❌ | ✅ (本人创建) | ✅ | ✅ (本人创建) | ❌ |
| 启用规则 | ✅ | ✅ | ✅ | ✅ | ❌ |
| 禁用规则 | ✅ | ✅ | ✅ | ✅ | ❌ |
| 删除规则 | ✅ | ✅ | ✅ | ❌ | ❌ |

**关键不变式**（v2.19 确立）：
- LLM 永远不能直接启用规则（必须人工确认）
- 删除规则**不可逆**（v2.19 行为：删除 = 软删除到 `rules.archived_at`）
- 任何规则变更进 `rule_audit_log`

#### 53.6.3 4 张表（v2.19.1 待补 §5.0b ER 图同步）

```sql
-- 规则定义（v2.19 新增）
CREATE TABLE rules (
  id TEXT PRIMARY KEY,                -- kebab-case 唯一标识
  household_id INTEGER NOT NULL,      -- 多家庭隔离
  description TEXT NOT NULL,
  yaml_body TEXT NOT NULL,            -- 完整 YAML 主体
  confidence_base REAL DEFAULT 0.7,
  enabled INTEGER DEFAULT 1,
  archived_at INTEGER,                -- 软删除
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  author_type TEXT NOT NULL,          -- 'system' | 'doctor' | 'family' | 'llm_suggested'
  author_id INTEGER,                  -- 具体成员 ID
  validated_by INTEGER,               -- LLM 规则必须有人确认
  category TEXT,                      -- 分类标签
  severity TEXT DEFAULT 'care',        -- v2.19 审计 B 修复：与 SCHEMA.md §18 + §23 一致
  version INTEGER DEFAULT 1
);

-- 规则状态（v2.19 新增）
CREATE TABLE rule_state (
  rule_id TEXT PRIMARY KEY,
  household_id INTEGER NOT NULL,
  state TEXT NOT NULL DEFAULT 'cold_start',  -- v2.19 审计 B 修复：与 SCHEMA.md §19 + §23 一致
  last_fire_at INTEGER,
  last_eval_at INTEGER,
  cooldown_until INTEGER,
  true_positive_count INTEGER DEFAULT 0,
  false_positive_count INTEGER DEFAULT 0,
  updated_at INTEGER NOT NULL,
  CHECK (state IN ('disabled','cold_start','armed','firing','cooldown'))  -- v2.19 审计 B 修复：CHECK 约束
);

-- 规则审计日志（v2.19 新增）
CREATE TABLE rule_audit_log (
  id INTEGER PRIMARY KEY,
  rule_id TEXT NOT NULL,
  household_id INTEGER NOT NULL,
  fired_at INTEGER NOT NULL,
  finished_at INTEGER,
  kind TEXT NOT NULL,                 -- 'fire' | 'stale_data' | 'eval_error' | 'cooldown_suppressed' | 'auto_disabled' | 'invalid_predicate' | 'rule_changed'
  confidence REAL,
  matched_predicates TEXT,            -- JSON 数组，命中的谓词
  evidence_snapshot TEXT,             -- JSON，证据快照（30 天）
  detail TEXT,                        -- 其他结构化信息
  ack_at INTEGER,                     -- 有人 ack 的时间
  ack_by INTEGER                      -- 哪个成员 ack
);

-- 规则反馈（v2.19 新增）
CREATE TABLE rule_feedback (
  id INTEGER PRIMARY KEY,
  rule_id TEXT NOT NULL,
  fire_id INTEGER NOT NULL,           -- 关联 rule_audit_log.id
  household_id INTEGER NOT NULL,
  member_id INTEGER NOT NULL,
  feedback TEXT NOT NULL,             -- 'true_positive' | 'false_positive' | 'ignored' | 'disable'
  note TEXT,
  created_at INTEGER NOT NULL,
  CHECK (feedback IN ('true_positive','false_positive','ignored','disable'))  -- v2.19 审计 B 修复：CHECK 约束
);

-- 索引
CREATE INDEX idx_rules_household ON rules(household_id) WHERE archived_at IS NULL;
CREATE INDEX idx_rule_state_household ON rule_state(household_id);
CREATE INDEX idx_rule_audit_rule ON rule_audit_log(rule_id, fired_at DESC);
CREATE INDEX idx_rule_audit_household ON rule_audit_log(household_id, fired_at DESC);
CREATE INDEX idx_rule_feedback_rule ON rule_feedback(rule_id, created_at DESC);
```

**关键约束**：
- 所有表都带 `household_id`（§36 强制隔离）
- `rule_audit_log` 不分表（统一表 + 索引），保证审计查询简单
- 30 天前的 `evidence_snapshot` 自动清理（保留结构化字段）

### 53.7 规则与已有模块的对接

#### 53.7.1 与 §5 capabilities 的关系

**规则 then 引用 capability 名字（不用 did）**：

```yaml
then:
  - execute_scene: "scene_id_xxx"        # 调 §42 场景
  - escalate:
      ladder: [...]                       # 走 §52 通知
    capability_involved:                  # v2.19 新增：声明关联 capability
      - "lock.front_door.unlock"
      - "light.living_room.on"
```

**§5.7b capability 同步时联动**：
- capability 失效 → 关联规则**自动降级**到 `disabled`
- capability 新增 → 提示"是否需要新增规则"
- capability 文档变更 → 规则 `meta.last_validated_at` 自动更新

#### 53.7.2 与 §52 通知路由的关系

**所有 escalate / notify 动作都走 §52**：

```
规则 then.escalate
   ↓
§53.4 置信度判定
   ↓
§52.6 ladder 升级（按置信度区间）
   ↓
§52.1 safety 不可静音不变式自动应用
```

**关键约束**：
- 规则 then **不直接**调 PWA / SMS / 任何渠道
- 规则 then 必须声明 level（safety / care / info），由 §52 路由
- 同一规则 fire 同一成员 ≤ 5min 间隔：自动汇总（§52.3 摘要窗口）

#### 53.7.3 与 §38 老年守护的关系

**v2.19 修订（审计 A 问题 2 修复）**：§38 共 24 场景，v2.19 实际能覆盖的精确子集：

| §38 场景 | 对应规则 | 状态 |
|---------|---------|------|
| §38.6 老人活动异常 | `elderly_fall_suspect_v1` | ✅ v0.1 |
| §38.7 跌倒检测 | `elderly_imu_fall_v1` | ✅ v0.1 |
| §38.8 痴呆走失 | `dementia_wander_v1` | ✅ v0.1 |
| §38.9 远程看孩 | `child_school_pickup_v1` / `baby_cry_v1` | ✅ v0.1 |
| §38.10 用药提醒 | `elderly_medication_miss_v1` | ✅ v0.1 |
| §38.11 子女代理 | `family_care_proxy_activity_v1` | ⏳ v0.2 |
| §38.12 急救流程 | `medical_emergency_sos_v1` / `smoke_detector_v1` / `gas_leak_v1` | ✅ v0.1 |
| **§38.6 老人作为使用者**（6 项可用性：超大字号 / 方言 / 语音优先 / 慢节奏 / Undo Window / 每日问候） | — | ❌ **PWA 层而非规则层** |
| **§38.7 跌倒四级告警**（Level 0-3 完整链路） | 部分覆盖 | ⏳ v0.2 补全 Level 1-2 |
| **§38.8 出门走失 > 500m 推送、忘关燃气 30min 自动关阀、被骗接电话录音、深夜漫游** | `dementia_wander_v1` 部分覆盖 | ⏳ v0.2 |
| **§38.9 异地登录告警、远程 5min 撤销窗、远程禁控门锁燃气** | — | ⏳ v0.2 远程访问层补 |
| **§38.10 多老人轮值、保姆自动上下班、共识触发** | — | ❌ v2.20 后续 |
| **§38.11 慢病异常 > 160 推医生、续方下单** | — | ❌ v2.20 后续（涉及 §23 服务） |

**v2.19 承诺修订**：v0.1 落地 5 条 P0 规则（elderly_fall_suspect / water_microleak / stranger_porch / elderly_no_activity / smoke_detector）；v0.2 补 11 条 P1（覆盖 §38.7 Level 1-2、§38.8 出门走失、§38.9 远程撤销等）。§38.6 老人作为使用者的 6 项可用性**不在规则引擎范围**，是 PWA 章节（§30）的责任。

**v2.19 总规则数修订**：RULES.md §3 列出 16 条全集中，v0.1 实际落地 5 条 P0，v0.2+ 补 11 条 P1。**§53.10.1 与 RULES.md §3 标题必须对齐**——RULES.md §3 标题改为 "v2.19 全集 16 条（v0.1 5 条 P0 + v0.2+ 11 条 P1）"，避免 "v0.1 起步 16 条" 的口径混淆。

#### 53.7.4 与 §42 规则模式的关系

**正交互补**：
- §42 动作编排器：`出发 → 步骤 1 → 步骤 2 → ...`
- §53 判定器：`信号 → 判定 → 调用 §42 场景`

**典型协作**：

```yaml
# §53 规则：判定老人异常
id: elderly_fall_suspect_v1
when:
  all: [...]
then:
  - execute_scene: emergency_call_steps    # 调 §42 场景
  - escalate:
      ladder: [primary_caregiver, 120]
```

```yaml
# §42 场景：应急呼叫动作序列
id: emergency_call_steps
description: 老人异常应急流程
steps:
  - 1. 拉摄像头客厅 + 走廊
  - 2. 调 §52 通知 primary_caregiver
  - 3. 15 分钟无 ack → 调 120
```

**关键约束**：
- §42 场景**不**做"是否触发"的判断（那是 §53 的事）
- §53 规则**不**写具体动作步骤（那是 §42 的事）
- 触发关系：`rules.when → fires → rules.then.execute_scene`

#### 53.7.5 与 §5.6b 反馈环的关系

§5.6b 反馈环是**单次动作**的反馈（开灯成功没有）。
§53 误报闭环是**规则整体**的反馈（这条规则准不准）。

两者**正交**：
- §5.6b：动作执行的反馈（§5.6b undo 栈）
- §53.5：规则判定的反馈（置信度校准）

### 53.8 调试与可观测性

#### 53.8.1 每次 fire 都是结构化记录

```json
{
  "fire_id": 12345,
  "rule_id": "elderly_fall_suspect_v1",
  "fired_at": "2026-08-03T03:35:22Z",
  "confidence": 0.78,
  "matched_predicates": [
    "bed_pressure.away_minutes > 30",
    "motion.living_room.duration_minutes > 45",
    "time.in_window: [22:00, 06:00]"
  ],
  "evidence": {
    "bed_pressure": {"value": 0, "away_minutes": 47, "fresh": true},
    "motion.living_room": {"value": 1, "duration_minutes": 45, "fresh": true},
    "members_at_home": ["grandpa_zhang"],
    "weather": {"temp": 18, "cond": "clear"}
  },
  "actions_taken": [
    {"action": "escalate", "level": "safety", "ladder_attempt": 1, "to": "primary_caregiver"},
    {"action": "capture_snapshot", "cameras": ["living_room", "hallway"], "ttl": 1800}
  ],
  "ack": null
}
```

#### 53.8.2 PWA 调试面板

**Rule Debug UI**（v2.19 v0.1 不强制，v0.2 必有）：

| 视图 | 内容 |
|------|------|
| 规则列表 | 所有启用规则 + 状态 + 命中率 |
| 单规则详情 | 谓词树 + 窗口数据 + 最近 10 次 fire |
| 误报分析 | 30 天内误报 top 10 + 置信度曲线 |
| 规则建议 | LLM 自动提议的"该删 / 该改 / 该加" |
| 实时扫描 | 当前正在评估的规则 + 耗时 |

#### 53.8.3 日志规范

**关键日志事件**（进 `events` 表）：

| kind | 触发 | 严重度 |
|------|------|--------|
| `rule_fired` | 规则触发 | info |
| `rule_false_positive` | 用户反馈误报 | info |
| `rule_auto_disabled` | 误报过多自动停 | warn |
| `rule_eval_error` | 谓词评估异常 | warn |
| `rule_stale_data` | 传感器掉线 | warn |
| `rule_paused` | 规则 pause | info |
| `rule_llm_suggested` | LLM 生成规则草案 | info |

### 53.9 性能边界

#### 53.9.1 性能断言（v2.19 草案）

| 指标 | 目标 | 实测（验证期） |
|------|------|---------------|
| 单次扫描 (100 条规则 × 20 设备) | ≤ 200ms | 验证中 |
| 单条规则评估（1min 窗口） | ≤ 5ms | 验证中 |
| 窗口聚合（20 设备 × 1min × 1h） | ≤ 50ms | 验证中 |
| 规则冷启动（启用 → armed） | ≤ 1 个窗口 | 必达 |
| Cooldown 推进 | ≤ 1ms | 必达 |
| 置信度计算 | ≤ 1ms | 必达 |
| 写入 audit_log | ≤ 10ms | 必达 |

#### 53.9.2 容量边界

| 维度 | 上限 | 触发扩容 |
|------|------|---------|
| 单家庭规则数 | 100 条 | 拒绝创建 |
| 全部规则谓词数 | 2000 个 | 评审架构 |
| 1min 窗口规则 | 100 条 | 强制合并到 5min |
| single scan 耗时 | 200ms | 自动降级到 30s |
| audit_log 7 天细粒度 | 50 万条 | 自动聚合 |
| audit_log 30 天聚合 | 100 万条 | 自动归档（仅保留 kind+count） |
| audit_log 6 个月 | 500 万条 | 触发容量告警 |

**v2.19 修订（审计 A 问题 7 修复）**：audit_log 容量边界分两段：
- 7 天内：保留完整 fire / stale_data / eval_error / cooldown_suppressed 等细粒度记录
- 7-30 天：聚合到 kind+count（每 rule 每 day 一行）
- 30 天后：聚合行进入归档表
- 失败降级加上"audit_log 写入超 10ms → 降级到 30s 间隔 + 聚合写"

#### 53.9.3 与 §1b SLO 对齐

| 维度 | 承诺 |
|------|------|
| 规则引擎可用性 | 99.9%（与管家主进程同） |
| 单次 fire → 通知送达 | ≤ 3s（核心路径） |
| 误报率 | < 10%（默认配置 + 30 天校准） |
| 漏报率 | < 5%（life-safety 规则） |
| 上下文新鲜度 | 传感器读数 ≤ 窗口时间 |

**关键不变式**：**任何性能降级必须主动暴露**，绝不"假装正常"——§16 状态灯不变式扩展。

### 53.10 实施里程碑

#### 53.10.1 v0.1（第一个里程碑）

**v2.19 修订（审计 A 问题 8 修复）**：v0.1 落地 5 条 P0 规则（不是 16 条全集）：

- 4 张表 schema + 迁移脚本
- DSL 解析器（YAML → 内存对象）
- 窗口聚合层（readings → 1min/5min/60min 视图）
- 规则扫描器（基础版，无置信度）
- **5 条 v0.1 P0 系统预设**（elderly_fall_suspect / water_microleak / stranger_porch / elderly_no_activity / smoke_detector）
- 1 个最小 PWA 调试面板（规则列表 + fire 历史）
- 剩余 11 条（v0.2+ P1）：RULES.md §3 完整列出，v0.2 增量补

#### 53.10.2 v0.2

- 完整置信度校准（4 个因子）
- 误报闭环（用户反馈 UI）
- 补 11 条 P1 规则（覆盖 §38.7 Level 1-2、§38.8 出门走失、§38.9 远程撤销）
- 规则变更审计 + soft delete
- LLM 兜底推理（次数限额，§53.4.3）

#### 53.10.3 v0.5

- 自动学习（置信度动态调整）
- 规则市场（v3 治理框架成熟后）
- 多家庭规则共享（v2.18 ≤3 家庭限制下）

#### 53.10.4 v1.0

- 跨实例规则同步（多 NAS 部署）
- ML 自动生成规则（v2.20 起步）
- 规则可视化编排器（拖拽编辑）

### 53.11 与 §50 缺失的处理

> 现有章节从 §49 直接跳到 §51，§50 缺失。v2.19 不补 §50，留给 v3 治理框架专题。
> 本章节 §53 跨信号推理规则引擎是 v2.19 新增，命名延续。

### 53.12 修订注记（v2.19）

- v2.19 §53 新增：跨信号推理规则引擎
- 4 张表 + DSL 规范 + 调度模型 + 置信度校准 + 误报闭环 + 治理
- 明确 §53 与 §42（动作）/ §52（通知）/ §38（守护）/ §5.6b（反馈环）的边界
- 微信渠道决策 B（不做，留 v3）
- 本地模型硬件预算决策 C（分层）
- v0.1 实施起点决策 C（E2 LLM 网关）
- v0.2 视觉管线 §54 + 置信度 §53.4 完整化（4 因子算法 + 误报闭环 + 兜底推理）

## 54. 视觉管线（v0.2 新增）

> v2.19 §4 设备轨道的子章节提及"摄像头"但未定义完整管线。本节是 v0.2 落地：**让管家有"眼睛"**——通过本地推理 + LLM-Vision 兜底实现视觉理解，与 §53 规则引擎 / §52 通知路由 / §38 老年守护联动。

### 54.0 章节地图

```
§54.1 视觉分层架构（3 层：协议 / 推理 / 决策）
§54.2 摄像头协议适配（RTSP / ONVIF / 云端）
§54.3 视觉事件 schema
§54.4 本地推理层（专用模型）
§54.5 LLM-Vision 兜底（云端）
§54.6 视觉能力注册表（capabilities）
§54.7 与已有模块的对接
§54.8 隐私与本地主权
§54.9 性能边界
§54.10 实施里程碑
```

### 54.1 视觉分层架构

```
┌─────────────────────────────────────────┐
│ Layer 4: 决策 / 通知                    │
│  - 视觉事件 → 规则引擎（§53）           │
│  - 视觉事件 → LLM 推理（§28.3）         │
│  - 视觉事件 → §52 通知升级              │
└─────────────────────────────────────────┘
              ↑
┌─────────────────────────────────────────┐
│ Layer 3: 视觉理解                       │
│  - LLM-Vision（云端，按 token 计费）    │
│  - 本地大模型（v0.5+）                  │
└─────────────────────────────────────────┘
              ↑
┌─────────────────────────────────────────┐
│ Layer 2: 本地推理（专用模型）           │
│  - YOLO-nano / MobileNet（人形/姿态/火）│
│  - Whisper.cpp（婴儿哭声/异常声音）     │
│  - 人脸识别（本地 embedding）           │
└─────────────────────────────────────────┘
              ↑
┌─────────────────────────────────────────┐
│ Layer 1: 协议适配                       │
│  - RTSP / ONVIF（局域网拉流）           │
│  - 云端 P2P（萤石 / 大华 / 米家）       │
│  - HTTP MJPEG（廉价云台）               │
└─────────────────────────────────────────┘
```

**关键设计**：
- **Layer 1 永远本地**（摄像头接入不依赖云端厂商）
- **Layer 2 永远本地**（隐私 + 实时）
- **Layer 3 按需云端**（复杂场景才上 LLM-Vision）
- **Layer 4 复用 §52/§53**（不重复造通知 + 规则引擎）

### 54.2 摄像头协议适配

#### 54.2.1 推荐协议优先级

| 优先级 | 协议 | 适用 | 隐私 |
|--------|------|------|------|
| **1** | **ONVIF / RTSP** | 海康 / 大华 / TP-LINK | ✅ 内网拉流 |
| 2 | HTTP MJPEG | 廉价云台 | ✅ 但带宽占用高 |
| 3 | 厂商云端 P2P | 萤石 / 大华云 | ⚠️ 出厂商云 |
| ❌ | 只能云端的型号 | 某些小米 / 米家 | ❌ 不推荐 |

**v0.2 决策**：只支持 ONVIF/RTSP 协议。**明确不支持**只能云端的摄像头（隐私边界）。

#### 54.2.2 摄像头注册表

```sql
CREATE TABLE cameras (
  id TEXT PRIMARY KEY,                  -- 内部 ID
  household_id INTEGER NOT NULL DEFAULT 1,
  name TEXT NOT NULL,                   -- 用户友好名
  rtsp_url TEXT NOT NULL,               -- rtsp://user:pass@ip:554/...
  location TEXT,                        -- 门口/客厅/厨房...
  capabilities TEXT NOT NULL,           -- JSON: ['motion', 'face', 'fall', 'fire']
  enabled INTEGER DEFAULT 1,
  last_seen_at INTEGER,
  created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);
```

**关键约束**：
- `rtsp_url` 凭证加密存储（v0.3+，v0.2 暂用 .env）
- `household_id` 强制隔离（§36）
- `capabilities` 声明这台摄像头能跑什么检测

#### 54.2.3 RTSP 拉流抽象

```python
class CameraSource(ABC):
    @abstractmethod
    def open(self) -> cv2.VideoCapture: ...
    @abstractmethod
    def read(self) -> tuple[bool, np.ndarray]: ...
    @abstractmethod
    def close(self) -> None: ...
```

**v0.2 实现**：基于 OpenCV（cv2）+ ffmpeg fallback。v0.3 接入 GStreamer（更低延迟）。

### 54.3 视觉事件 schema

```sql
CREATE TABLE vision_events (
  id INTEGER PRIMARY KEY,
  camera_id TEXT NOT NULL,
  household_id INTEGER NOT NULL DEFAULT 1,
  kind TEXT NOT NULL,                   -- 'motion' | 'person' | 'face_recognized' | 'fall_detected' | 'fire_detected' | 'cry_detected' | 'stranger' | 'package'
  confidence REAL,                      -- 检测器置信度 [0.0-1.0]
  bbox TEXT,                            -- JSON: {x, y, w, h} 归一化坐标
  attributes TEXT,                      -- JSON: 额外属性（如人脸 ID、声音分贝）
  snapshot_path TEXT,                   -- 截图本地路径（可选）
  started_at INTEGER NOT NULL,
  ended_at INTEGER,                     -- 持续事件结束时间
  ts INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

CREATE INDEX idx_vision_events_camera ON vision_events(camera_id, ts DESC);
CREATE INDEX idx_vision_events_household ON vision_events(household_id, ts DESC);
CREATE INDEX idx_vision_events_kind ON vision_events(household_id, kind, ts DESC);
```

**关键设计**：
- 事件有时间区间（started_at / ended_at）—— 区别于瞬时告警
- `snapshot_path` 可选——v0.2 暂不上传云，30 天后清理
- `kind` 是受限枚举（v0.2 列 8 种，v0.5 扩展）

#### 54.3.1 视觉事件 vs 设备事件

| 维度 | 设备事件（events 表） | 视觉事件（vision_events 表） |
|------|----------------------|---------------------------|
| 来源 | 米家云 / miio | 摄像头本地推理 |
| 结构 | 单点 | 时段（started / ended） |
| 用途 | 触发规则 | 触发规则 + 跨信号关联 |
| 清理 | 365 天 | 30 天（§54.8 隐私） |

**规则引擎统一消费两者**——§53 谓词 `sensor.vision.kind` 自动从 vision_events 取。

### 54.4 本地推理层

#### 54.4.1 模型分工

| 模型 | 用途 | 硬件 | 延迟 |
|------|------|------|------|
| **YOLO-nano** | 人形/车辆/动物检测 | 任意 CPU | <50ms |
| **YOLO-pose** | 跌倒检测 | 树莓派 4+ | <100ms |
| **MobileNet-V3** | 火焰/烟雾视觉复核 | 任意 | <30ms |
| **Whisper.cpp** | 哭声/异常声音检测 | N100+ | <200ms |
| **FaceNet/ArcFace** | 人脸识别（本地 embedding） | N100+ | <300ms |

**v0.2 起步**：仅 YOLO-nano（人形）+ 简单动作识别。v0.3 加 Whisper.cpp。v0.5 加 face embedding。

#### 54.4.2 推理抽象

```python
class LocalDetector(ABC):
    @abstractmethod
    def detect(self, frame: np.ndarray) -> list[Detection]: ...

@dataclass
class Detection:
    kind: str             # 'person' | 'fall' | 'fire' | ...
    confidence: float
    bbox: tuple[int, int, int, int]
    attributes: dict
```

**v0.2 实现**：
- `PersonDetector`（YOLO-nano 包装）
- `MotionDetector`（背景减除，简单）
- 其他检测器 mock 占位

#### 54.4.3 推理调度

```
摄像头 → 拉流（5 FPS）→ 推理队列（per-camera）→ 检测器 → 视觉事件
                            ↓
                       持续 N 秒 → 升级为持续事件
                            ↓
                       触发 §53 规则
```

**关键不变式**：单摄像头推理 ≤ 100ms（5 FPS 下 200ms 内出结果）。

### 54.5 LLM-Vision 兜底

#### 54.5.1 何时上云

| 触发条件 | 调用 |
|---------|------|
| 本地检测到 person 但无法识别人脸 | ✅ |
| 视觉事件触发规则但规则 fire 时证据不足 | ✅ |
| 用户主动询问"刚才客厅发生了什么" | ✅ |
| 持续 30 分钟无活动 + 视觉复核 | ✅ |

**不调用**：
- 简单"有没有人"（本地 YOLO 即可）
- 日常人形/车辆/动物（无意义）

#### 54.5.2 LLM-Vision 协议

```python
class LLMVisionAnalyzer:
    def analyze(
        self,
        image: np.ndarray | str,    # 图像或本地路径
        prompt: str,
        context: dict | None = None,
    ) -> VisionResult:
        """返回结构化结果 + 置信度 + 自然语言解释"""
        pass

@dataclass
class VisionResult:
    answer: str
    confidence: float
    detected_objects: list[str]
    attributes: dict
```

**v0.2 实现**：通过 OpenAI 兼容协议（DeepSeek 暂不支持 Vision，**走 OpenAI GPT-4o / Qwen2-VL**）。v0.3 等 DeepSeek-Vision。

#### 54.5.3 成本控制

- 单家庭 LLM-Vision ≤ 20 次/天
- 超过 → 降级到本地 + 提示"今日视觉智能次数已用完，明日重置"
- 计费按 token，估算单家庭月度 5-20 元

### 54.6 视觉能力注册表

#### 54.6.1 cameras.capabilities 字段

```json
{
  "motion": true,            // 运动检测（必选）
  "person": true,            // 人形检测
  "pose": false,             // 姿态检测（需更强硬件）
  "face": true,              // 人脸识别
  "fire": true,              // 火焰/烟雾视觉
  "cry": false,              // 哭声检测（需麦克风）
  "package": true,           // 包裹识别
  "vehicle": false           // 车辆识别
}
```

#### 54.6.2 与 §5 capabilities 联动

视觉能力是 **capabilities 表的子类**——v0.2 暂用 `cameras.capabilities` 单独存（避免 §5 capabilities 表膨胀）。v0.3 合并到统一表。

**关键不变式**（v0.2）：每台摄像头 `cameras.capabilities` 必须在部署时**手工声明**（v0.2 简化）；v0.3 自动检测（跑一遍本地模型看支持什么）。

### 54.7 与已有模块的对接

#### 54.7.1 与 §53 规则引擎

**规则引用视觉事件**：

```yaml
id: stranger_porch_v2_vision
description: 门口视觉检测到陌生人 + 视觉事件
when:
  all:
    - sensor.vision.kind: person
    - sensor.vision.camera.location: porch
    - sensor.vision.duration_minutes > 3
    - any_family_at_home: false
then:
  - escalate:
      ladder: [primary_caregiver]
      level: safety
```

**v0.2 落地**：
- §53 谓词白名单加 `sensor.vision.kind` / `sensor.vision.camera.location` / `sensor.vision.duration_minutes`
- DSL 解析器允许这些字段
- 评估时从 vision_events 表取最近 N 分钟事件

#### 54.7.2 与 §38 老年守护

| §38 场景 | 视觉增强 |
|---------|---------|
| §38.6 老人活动异常 | 客厅摄像头 YOLO-pose 检测姿态异常 |
| §38.7 跌倒检测 | 摄像头视觉 + 智能手环 IMU 双源 |
| §38.8 痴呆走失 | 门口摄像头捕捉到老人独自外出 → 升级 |
| §38.12 急救 | 视觉复核烟雾/燃气 + 急救流程 |

#### 54.7.3 与 §52 通知路由

视觉事件 fire 时自动走 §52：
- `kind: fall_detected` → §52.1 safety 不可静音
- `kind: stranger` → §52.1 safety 升级链
- `kind: package` → §52.1 info 等级

### 54.8 隐私与本地主权

#### 54.8.1 三层防护

| 层 | 防护 | v0.2 实现 |
|----|------|----------|
| **Layer 1 协议** | 选 ONVIF/RTSP 不出内网 | ✅ 强制 |
| **Layer 2 推理** | 原始视频不持久化 | ✅ 默认 |
| **Layer 3 云端** | 上云前必须经用户同意 | ✅ 每次询问 |

#### 54.8.2 原始视频不持久化

- 摄像头流**不**写入磁盘（除了用户主动拉的 snapshot）
- 推理后只存结构化事件（`vision_events` 表）
- `snapshot_path` 仅在 fire 时保留 30 天

#### 54.8.3 上云脱敏

LLM-Vision 调用前：
- 默认**马赛克**人脸区域（避免泄漏）
- 询问用户"是否把未打码版本发给云端 LLM"
- 凭证不外发（OpenAI key 走 §5.11 redactor）

#### 54.8.4 §43 GDPR 兼容

- 删成员 → 关联 vision_events 中含此人脸的 → 30 天后清理
- 删摄像头 → 关联 vision_events 立即清理
- 删快照 → 立即清理文件系统

### 54.9 性能边界

| 指标 | 目标 | 失败降级 |
|------|------|---------|
| 单摄像头推理 | ≤ 100ms | 降级到 3 FPS |
| 4 路摄像头并发 | ≤ 400ms | 排队 + 提示升级硬件 |
| 视觉事件 fire 延迟 | ≤ 3s | 走 §53 状态机 |
| LLM-Vision 调用 | ≤ 10s | 降级到本地 |
| 视觉事件存储 | 30 天 / 100 万条 | 自动清理 |

### 54.10 实施里程碑

#### 54.10.1 v0.2（当前）

- §54 章节完整
- 视觉管线代码（mock 实现）
- cameras + vision_events schema
- 3 条视觉示例规则
- LLM-Vision 抽象（不接真实云端）

#### 54.10.2 v0.3

- 真实 YOLO-nano 部署
- RTSP 真实拉流
- 视觉规则自动触发
- §38 老年守护视觉增强

#### 54.10.3 v0.5

- Whisper.cpp 接入
- 人脸识别（本地 embedding）
- 视觉事件跨信号关联
- 移动端推送视频片段

#### 54.10.4 v1.0

- 多摄像头网格（家门口 / 院子 / 车库联动）
- 视频摘要（24h 一段，自动生成）
- 与 §23 服务轨道联动（看到快递自动登记）

### 54.11 v0.2 修订注记

- v0.2 §54 视觉管线（v2.19 留 v0.2 落地）
- cameras + vision_events 两张表
- 3 条视觉示例规则（stranger / fall / smoke 视觉复核）
- 视觉抽象层（Layer 1 协议 / Layer 2 推理 / Layer 3 LLM-Vision / Layer 4 决策）
- 与 §53/§52/§38/§5 的对接
- 隐私 3 层防护 + 原始视频不持久化

## 50. 治理框架（v0.4 新增，v2.19 §50 占位的兑现）

> v2.19 留 v3 治理框架的占位，本节落地。**核心问题**：管家能力越来越强，谁来管管家？**答案**：治理 = 规则 + 审计 + 撤销 + 跨家庭策略同步。

### 50.1 治理四要素

```
┌─────────────────────────────────────────┐
│ 1. 规则管理                             │
│  - 规则版本（rules.version）             │
│  - 作者撤销级联（§43.3）                │
│  - 软删除（archived_at）                 │
│  - 跨家庭策略同步（scope=household/member）│
├─────────────────────────────────────────┤
│ 2. 能力注册表                            │
│  - capabilities 不可变                  │
│  - irreversibility_tier 强制 confirm     │
│  - 拒绝默认（deny-by-default）            │
│  - LLM 生成 capability 需人工审           │
├─────────────────────────────────────────┤
│ 3. 资源配额                              │
│  - LLM 调用限流（10 次/天/家）           │
│  - 视觉 LLM 限流（20 次/天/家）          │
│  - rule_audit_log 容量分档（7d/30d/180d）│
│  - 单实例 ≤3 家庭                       │
├─────────────────────────────────────────┤
│ 4. 审计可追溯                            │
│  - 每次 fire/feedback/rule_change 进 audit│
│  - GDPR 撤销时审计不删（合规留痕）        │
│  - 跨家庭隔离（§36.6 HouseholdScope）     │
│  - §17 自主行为可审计                    │
└─────────────────────────────────────────┘
```

### 50.2 规则治理细化

#### 50.2.1 规则版本

| 字段 | 行为 |
|------|------|
| `version` 整数 | 每次编辑 +1（v0.2 已实现） |
| 升级路径 | v0.2 → v0.3 不破坏旧规则（向后兼容） |
| 不兼容变更 | 必须建新 rule_id（v0.4 修订） |
| 回滚 | v0.2 已留 CLI：`myhome-agent rules rollback <id> --to-version N` |

#### 50.2.2 作者撤销级联

**v0.4 触发**：
- 删 member（§43.3 10 步流程）
- member 主动退出家庭
- admin 强制移除成员

**级联行为**（v0.2 §53.5.1）：
```python
# rules/feedback.py
def cascade_author_revoke(rule_store, member_id, household_id):
    UPDATE rules SET archived_at = strftime('%s', 'now')
    WHERE author_id = ? AND household_id = ? AND archived_at IS NULL
```

**例外**：`scope='member'` 规则（跟随 member 走）— 撤销时迁移到新 household（v0.4 §36.2 修订）。

#### 50.2.3 跨家庭策略同步

**v0.4 新增 `rules.scope` 字段**：
- `scope='household'`：绑定到 household，搬家时 archived
- `scope='member'`：跟随 member，搬家时迁移

**示例**：
```yaml
id: granny_medication_reminder
description: 奶奶每天 8 点吃降压药
scope: member              # v0.4 新增
author: family_admin
author_id: <grandson_id>
```

### 50.3 能力治理细化

#### 50.3.1 capabilities 不可变原则

**v0.4 修订**：LLM/医生/家属均**不可**直接写 capabilities 表。所有 capability 必须经：
1. spec_normalizer 自动归一化（§5.7b）
2. 人工审（v0.4 新增 "capability_review" 状态机）
3. enabled 后才进 rules 谓词白名单

#### 50.3.2 irreversibility_tier 三档

| 等级 | 例子 | 行为 |
|------|------|------|
| `reversible` | 开灯、关空调 | L2 自主 + 可撤销 |
| `costly` | 重启路由器 | L1 高危 + 强制 confirm |
| `irreversible` | 删除设备、清空记忆、关阀 | L1 强制 + 二次确认 + §43 审计 |

**v0.4 细化**：irreversible capability 关联的规则 `confidence_base ≥ 0.9`（§53.4.2 不变式强制）。

### 50.4 资源配额细化

| 资源 | 配额 | 超限行为 |
|------|------|---------|
| LLM 兜底 | 10 次/天/家 | 静默跳过（§53.4.3） |
| LLM-Vision | 20 次/天/家 | 降级到本地 |
| rule_audit_log 细粒度 | 7d / 50 万条 | 聚合 |
| rule_audit_log 聚合 | 30d / 100 万条 | 归档 |
| 单实例家庭数 | ≤3 | 启动期检查 |
| 摄像头数 | ≤16 | 性能降级（5 FPS → 3 FPS） |

### 50.5 微信/Telegram 解封条件

**v2.19 决策 B：微信不做（个人微信协议风险）**。

**v0.4 治理框架**：
- 微信**解封**条件 = 治理成熟 + 企业微信合规主体可用
- 解封路径：v2.21+（预计）
- 替代方案：Telegram 始终可用

**Telegram 解封条件**（v0.4 治理）：
- bot token 加密存储（v0.4 新增 `telegram_bot_token` Fernet）
- per-member chat_id 绑定（已实现）
- 群组支持留 v1.0

### 50.6 跨家庭策略同步（v0.4 新增）

#### 50.6.1 家庭模板

允许用户保存"家庭模板"（household_template.yaml）：
```yaml
template: elderly_care_v1
description: 5 老人家庭照护模板
rules:
  - id: elderly_no_activity_v1
    yaml: <rule body>
  - id: elderly_fall_suspect_v1
    yaml: <rule body>
  - id: medication_reminder
    yaml: <rule body>
```

**导入**：`myhome-agent rules import --template elderly_care_v1`

**风险**：
- 模板不能自动升级 irreversible 规则（v0.4 强制）
- 模板需 `validated_by: <community_leader>` 才能上公共市场

#### 50.6.2 跨家庭脱敏同步

- 家庭 A 的"奶奶吃降压药"规则 → 家庭 B 可见，**但** member 引用要脱敏
- v0.4 不实现公共市场（治理不成熟）

### 50.7 §43 GDPR 兼容

| GDPR 条款 | v0.4 实现 |
|----------|----------|
| **被遗忘权** | `forget_member(member_id)` 级联 10 步流程（§43.3） |
| **数据可携权** | `myhome-agent export --member=X` 输出 member 全部数据 |
| **同意管理** | `members.consent_flags`（v0.4 新增）：vision / llm_fallback / cloud / analytics |
| **审计留痕** | 所有 forget / consent 变更进 audit_log |
| **DPIA 文档** | `docs/DPIA.md`（v1.0 计划） |

### 50.8 治理升级路径

| v0.4 | v0.5 | v1.0 |
|------|------|------|
| 规则版本 + 撤销 | 跨家庭模板 | 公共市场 |
| 能力 3 档 | 4 档（加 destructive） | 动态策略 |
| 资源配额 | 动态配额（按时段） | SLA 服务 |
| GDPR 兼容 | DPIA 文档 | 第三方审计 |

### 50.9 v0.4 修订注记

- v0.4 §50 治理框架章节（v2.19 占位兑现）
- rules.scope 新增（household/member）
- 资源配额表完整化
- GDPR 5 条对照
- 治理升级路径（v0.4 → v1.0）

## 55. 公共规则市场（v0.7 §50 升级路径 3）

> v2.19 §50 占位 + v0.4 §50 治理框架 + v0.5 自治决策，v0.7 落地**公共规则市场**。
> 核心：用户可导入社区维护的规则模板，加速"开箱即用"。

### 55.1 治理不变量（v0.7 强约束）

| 不变量 | 行为 |
|--------|------|
| 1. **irreversible capability 关联规则不可市场导入** | 必须医生 + 家人双审，admin 单独不可启用 |
| 2. **market_imported 规则 enabled=0** | 默认禁用，必须人工启用 |
| 3. **LLM 自动生成规则不可发布到市场** | 必须人工创建 + 30 天实测 + 0 误报 |
| 4. **社区评分 < 3 星的规则自动下架** | 评分机制保质量 |
| 5. **market 规则版本绑定 capabilities** | 设备能力变化时规则自动失效（archived）|

### 55.2 规则模板（rule_templates）

```sql
-- 公共市场表（v0.7 新增）
CREATE TABLE rule_templates (
  id TEXT PRIMARY KEY,            -- kebab-case，全局唯一
  name TEXT NOT NULL,             -- "老人照护 5 件套"
  description TEXT NOT NULL,
  category TEXT NOT NULL,          -- elderly_care / water_safety / child_care / security / lifestyle
  severity TEXT NOT NULL,          -- safety / care / info（最高严重度）
  author_id INTEGER NOT NULL,      -- 创作者 member_id
  author_name TEXT,                -- 缓存（避免跨家庭 join）
  validated_by INTEGER,           -- 治理审批人
  validated_at INTEGER,
  scope TEXT DEFAULT 'household',  -- household / member / 公开市场
  license TEXT DEFAULT 'CC-BY-SA-4.0',  -- 许可协议
  yaml_body TEXT NOT NULL,         -- 完整 YAML（多条 rules）
  requires_capabilities TEXT,     -- JSON 数组，依赖的 capability
  irreversibility_tier TEXT DEFAULT 'reversible',
  rating_sum INTEGER DEFAULT 0,
  rating_count INTEGER DEFAULT 0,
  install_count INTEGER DEFAULT 0,
  created_at INTEGER,
  updated_at INTEGER,
  archived INTEGER DEFAULT 0
);
CREATE INDEX idx_templates_category ON rule_templates(category, rating_count DESC) WHERE archived = 0;
```

### 55.3 导入流程

```python
# myhome_agent/governance/marketplace.py
class RuleMarketplace:
    def import_template(self, template_id: str, household_id: int) -> ImportResult:
        template = self.get_template(template_id)
        # 1. DPIA 检查
        dpia = self.check_dpia(template)
        if dpia.requires_review:
            return ImportResult(status='review_required', dpia=dpia)
        # 2. 强制安全不变量
        if template.irreversibility_tier == 'irreversible':
            return ImportResult(status='review_required', reason='irreversible 必须医生 + admin 双审')
        # 3. 复制规则到本家庭
        rules = self.expand_template(template.yaml_body, household_id)
        for r in rules:
            r.enabled = 0  # 强制禁用，必须人工启用
            r.author_type = 'community'
            self.rule_store.upsert_rule(r)
        # 4. 记录市场 import 历史
        self.log_import(template_id, household_id)
        return ImportResult(status='imported', count=len(rules), enabled=False)
```

### 55.4 评分与质量

- 5 星制（用户评分 + 文字评论）
- < 3 星 → 自动下架（archived=1）
- 评分样本 ≥ 10 才显示（避免冷启动）
- 评分带版本：评分 1.0 模板，但模板 v2 后评分重置

### 55.5 模板示例（v0.7 内置）

| ID | 名称 | 严重度 | 规则数 |
|----|------|--------|--------|
| `starter_basic` | 入门 5 件套 | care | 5 |
| `elderly_care_5` | 老人照护 5 件套 | safety | 5 |
| `child_safety_3` | 儿童安全 3 件套 | safety | 3 |
| `water_safety_2` | 用水安全 2 件套 | care | 2 |
| `security_basic_2` | 安防基础 2 件套 | care | 2 |

### 55.6 治理红线

- 任何用户**不能**直接 import irreversible capability 规则到 enabled=1
- 任何模板发布需经 §50 治理审批（DPIA + 治理人审）
- 任何 market 规则 30 天 0 安装 → 自动下架（冷启动保护）
- 任何 market 规则 5 条评论提"误报多" → 强制 disable 7 天 + 警告作者

### 55.7 v0.7 落地 vs 完整市场

| v0.7（实现） | 完整 v1.0 |
|-------------|-----------|
| 本地导入（GitHub gist / URL）| 公共 web UI + 用户上传 |
| 5 个内置模板 | 100+ 模板 |
| 评分机制 stub | 完整 + 防刷 |
| 治理审批人 admin 手动 | 半自动 DPIA + 治理审 |
| import CLI 命令 | PWA 一键 + 预览 |

### 55.8 完整市场版本（v1.0 计划）

- `myhome.marketplace` 公共 web 平台
- 用户上传 / 评分 / 评论
- DPIA 模板自检
- 自动治理审批（基于 risk_score）
- 与 myhome-agent 安装无缝集成


## 56. §34 远程访问完整细化（v0.7）

> v2.9 §34 远程访问基础，v0.7 完整细化：3 层访问控制 + 临时授权 + 撤销窗 + 设备控制权限。

### 56.1 3 层访问控制

| 层级 | 触发条件 | 能力 |
|------|---------|------|
| **L1 LAN** | 同 WiFi / 局域网 | 全功能（控制 + 治理）|
| **L2 远程** | 异地（4G/外网）| 限控制 + 通知 + 治理读 |
| **L3 应急** | LAN 不可达 + 远程授权 | 临时授权（24h TTL）|

### 56.2 临时授权（v0.7 新增）

```sql
-- 临时授权表（v0.7 新增）
CREATE TABLE temporary_grants (
  id INTEGER PRIMARY KEY,
  grantor_id INTEGER NOT NULL,     -- 谁授权
  grantee_id INTEGER NOT NULL,     -- 被授权（care_taker / 子女 / 维修工）
  household_id INTEGER NOT NULL,
  scope TEXT NOT NULL,              -- 'control' | 'view' | 'governance'
  capabilities TEXT,                -- JSON 数组，限定 capability
  expires_at INTEGER NOT NULL,
  revoked_at INTEGER,
  reason TEXT,
  created_at INTEGER NOT NULL
);
```

### 56.3 远程撤销窗（§5.6b + §34 联合）

| 等级 | 撤销窗 | 谁可撤销 |
|------|--------|---------|
| 不可逆（safety）| 60s | 任何人（防冒用）|
| 可逆（care）| 30s | 现场人 |
| 普通（info）| 5s | 系统自撤 |

### 56.4 子女代理协议

子女 = 家庭成员，但有"代理权限"（不破坏 admin）：
- 看老人状态（无条件）
- 远程控制（可逆 L2 + 30s 撤销）
- 紧急升级（safety 自动接收）
- 治理（无 admin 权限，仅 view）

### 56.5 维修工临时授权

- 维修工 = 临时 member（`member_households` 短期）
- 授权范围限定（`scope=control_specific`）
- 24h 自动失效
- 不可继承为家庭成员

## 57. §39 per-member 语言 4 层 locale（v0.7）

> v2.9 §39 基础，v0.7 完整细化。

### 57.1 4 层 locale 模型

```
L1: 系统 locale (system_locale)        # 默认 zh-CN
L2: 家庭 locale (household.locale)    # 家庭主语言
L3: 成员 locale (member.locale)        # 成员主语言
L4: 场景 locale (scene.locale)         # 临时场景（如"和外宾对话"切英文）
```

### 57.2 支持 locale（v0.7 起步 6 种）

| locale | 语言 | 备注 |
|--------|------|------|
| zh-CN | 普通话 | 默认 |
| en-US | 美式英语 | 海外家庭 |
| zh-HK | 粤语 | §38.6 方言 |
| zh-TW-min-nan | 闽南语 | §38.6 |
| zh-CN-shanghai | 上海话 | §38.6 |
| ja-JP | 日语 | v0.8 计划 |

### 57.3 翻译缓存

```python
# 消息翻译：同 (key, locale) 缓存 30 天
TRANSLATION_CACHE = {
    ("rule_fired", "en-US"): "Rule {rule_id} fired",
    ("rule_fired", "zh-CN"): "规则 {rule_id} 触发",
}
```

### 57.4 ICU 消息格式

- 复数：`{count, plural, one {# rule} other {# rules}}`
- 性别：`{gender, select, male {他} female {她} other {TA}}`
- 数字格式：`{value, number, ::currency/CNY}`

### 57.5 字符编码边界

- 全角 → 半角自动转换（输入）
- Emoji 按 `👨‍👩‍👧` 复合字符处理
- 右到左语言（阿拉伯语，v1.0）

## 58. §47 policy 表完整字段 + 9 角色矩阵（v0.7）

### 58.1 policy 表完整 schema

```sql
-- v0.7 完整化 policy 表（§47）
CREATE TABLE policies (
  id INTEGER PRIMARY KEY,
  household_id INTEGER NOT NULL,
  member_id INTEGER NOT NULL,
  role TEXT NOT NULL,           -- 9 角色之一
  scope TEXT NOT NULL,          -- 'household' | 'room' | 'device' | 'capability'
  scope_target TEXT,           -- 范围目标（room_id / device_id / capability_name）
  capability TEXT NOT NULL,     -- 哪个 capability
  permission TEXT NOT NULL,     -- 'allow' | 'deny' | 'require_confirm'
  conditions TEXT,              -- JSON：时段/成员画像条件
  valid_from INTEGER,
  valid_until INTEGER,
  priority INTEGER DEFAULT 100, -- 数字大优先
  reason TEXT,                  -- 为什么这样定
  created_by INTEGER,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  archived_at INTEGER
);
CREATE INDEX idx_policies_member ON policies(household_id, member_id) WHERE archived_at IS NULL;
CREATE INDEX idx_policies_capability ON policies(household_id, capability) WHERE archived_at IS NULL;
```

### 58.2 9 角色矩阵（v0.7 完整化）

| 角色 | 默认 capability | 限制 | 治理权限 |
|------|----------------|------|---------|
| `admin` | 全 allow | - | 全权 |
| `adult` | 中危 allow | 不可逆 confirm | view |
| `elder`（普通）| 低危 allow | 中高危 confirm | view |
| `elder_senior` | 低危 allow | 任何 confirm | view |
| `elder_dementia` | 仅 view | 任何 confirm | 无 |
| `child` | 仅 view | 任何 confirm | 无 |
| `guest` | 限时低危 | 中高危 confirm | view |
| `nanny`（保姆）| 中危 allow | 不可逆 confirm | view |
| `care_taker`（照护者）| 中高危 allow | 不可逆 confirm | view |

### 58.3 per-(role × capability) 决策表（v0.7 完整）

| capability \ 角色 | admin | adult | elder | dementia | child | guest | nanny | care_taker |
|------|------|------|------|------|------|------|------|------|
| light.toggle | allow | allow | allow | deny | deny | require | allow | allow |
| ac.adjust_temp | allow | allow | allow | deny | deny | require | allow | allow |
| lock.unlock | allow | allow | require | require | require | require | require | require |
| lock.lock | allow | allow | allow | require | require | require | allow | allow |
| camera.view | allow | allow | allow | allow | deny | deny | allow | allow |
| camera.snapshot | allow | allow | allow | deny | deny | deny | allow | allow |
| rule.create | allow | allow | deny | deny | deny | deny | deny | allow |
| rule.feedback | allow | allow | allow | deny | deny | deny | allow | allow |
| memory.read | allow | allow | allow | allow | deny | deny | allow | allow |
| memory.forget | allow | allow | allow | require | require | require | require | require |
| history.read | allow | allow | allow | allow | deny | deny | allow | allow |
| emergency.sos | allow | allow | allow | allow | allow | allow | allow | allow |
| irreversible.* | allow | require | require | require | require | require | require | require |

### 58.4 字段级权限（v0.7 新增）

除 capability 外，新增字段级（field-level）权限：
- `member.view.email` - 看邮箱
- `member.view.location` - 看实时位置
- `member.view.health` - 看健康数据
- `member.view.financial` - 看家庭财务

### 58.5 治理审计

每次 policy 修改进 `audit_log.kind='policy_change'`，含：
- 旧值 / 新值
- 修改人 + 时间
- 修改原因（required）
- 7 天回滚窗

### 58.6 policy 决策算法

```python
def check_permission(member, capability, conditions):
    policies = query_policies(
        member_id=member.id,
        capability=capability,
        now=now(),
    )
    # 按 priority 降序，命中第一个 return
    for p in policies:
        if not p.archived and p.valid_in_range(now):
            if p.conditions and not match_conditions(p.conditions, conditions):
                continue
            return p.permission  # allow / deny / require_confirm
    # 默认 deny（§50 治理：deny by default）
    return 'deny'
```

## 59. §30 PWA 完整形态细化（v0.8）

> v2.8 §30 基础，v0.8 完整 PWA 形态：manifest + Service Worker + Web Push + 加桌面 + 离线缓存。

### 59.1 manifest.json 完整字段

```json
{
  "name": "myhome-agent 家庭管家",
  "short_name": "管家",
  "description": "家庭智能体：本地优先 + 跨生态 + AI 管家",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#121212",
  "theme_color": "#4CAF50",
  "icons": [
    {
      "src": "/static/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/static/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ],
  "shortcuts": [
    {
      "name": "聊天",
      "short_name": "Chat",
      "url": "/?tab=chat"
    },
    {
      "name": "规则",
      "short_name": "Rules",
      "url": "/?tab=rules"
    },
    {
      "name": "治理",
      "short_name": "Gov",
      "url": "/?tab=governance"
    }
  ],
  "categories": ["lifestyle", "utilities", "productivity"],
  "lang": "zh-CN",
  "dir": "ltr",
  "prefer_related_applications": false
}
```

### 59.2 Service Worker 离线策略

```javascript
// web/sw.js (v0.8 新增)
const CACHE_NAME = 'myhome-agent-v0.8';
const RUNTIME_CACHE = 'myhome-runtime-v0.8';

const PRECACHE_URLS = [
  '/',
  '/static/css/main.css',
  '/static/js/app.js',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/manifest.json'
];

const CACHE_STRATEGIES = {
  '/': 'network-first',
  '/static/': 'cache-first',
  '/api/rules': 'stale-while-revalidate',
  '/api/devices': 'stale-while-revalidate',
  '/api/readings': 'stale-while-revalidate',
  '/api/chat': 'network-only',
  '/api/control': 'network-only'
};

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(PRECACHE_URLS))
  );
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  const strategy = Object.entries(CACHE_STRATEGIES)
    .find(([prefix]) => url.pathname.startsWith(prefix))?.[1] || 'network-first';
  event.respondWith(handleFetch(event.request, strategy));
});
```

### 59.3 Web Push VAPID 集成

```python
# myhome_agent/notifications/webpush.py (v0.8 新增)
import os

class WebPush:
    def __init__(self):
        from py_vapid import Vapid
        self.vapid = Vapid.from_file('vapid_key.pem')

    def send(self, subscription_info, payload):
        from pywebpush import webpush
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=self.vapid.private_pem(),
            vapid_claims={"sub": "mailto:admin@myhome.local"}
        )

    def get_public_key(self) -> str:
        return self.vapid.public_key_urlsafe_base64
```

### 59.4 加桌面引导

```javascript
// PWA 检测 beforeinstallprompt
let deferredPrompt = null;
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  showInstallBanner();
});

async function installPWA() {
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
  const { outcome } = await deferredPrompt.userChoice;
  if (outcome === 'accepted') logEvent('pwa_installed');
  deferredPrompt = null;
}
```

### 59.5 离线缓存策略表

| 数据 | 策略 | TTL | 说明 |
|------|------|-----|------|
| 静态资源 | cache-first | 永久 | CSS/JS/icons |
| HTML 主页 | network-first → cache fallback | 7 天 | 离线看上次 |
| /api/rules | stale-while-revalidate | 1h | 离线看规则 |
| /api/devices | stale-while-revalidate | 30 min | 离线看设备 |
| /api/readings | stale-while-revalidate | 24h | 离线看曲线 |
| /api/chat | network-only | - | 必须在线 |
| /api/control | network-only + queue | - | 离线入队 |
| Web Push | background sync | - | 系统通知兜底 |

### 59.6 WebSocket 降级长轮询

```javascript
class RobustChannel {
  connect() {
    this.ws = new WebSocket(this.url);
    this.ws.onclose = () => { this.startFallback(); this.scheduleReconnect(); };
  }
  startFallback() {
    this.fallbackInterval = setInterval(() => {
      fetch('/api/events/poll?since=' + lastEventTs)
        .then(r => r.json())
        .then(events => events.forEach(this.onEvent));
    }, 5000);
  }
  scheduleReconnect() {
    const delay = Math.min(30000, 1000 * Math.pow(2, this.reconnectAttempts++));
    setTimeout(() => this.connect(), delay);
  }
}
```

### 59.7 iOS PWA 限制对策

| 限制 | v0.8 对策 |
|------|---------|
| 7 天后台缓存过期 | 提示每周开一次 |
| 后台 sync 不支持 | 切 Web Push |
| 推送到达率低 | 震动 + 加桌面引导 |
| Web Push 需 iOS 16.4+ | 文档提示最低系统版本 |## 60. §52 通知路由深化（v0.8 加 3 维）

### 60.1 v0.7 已实现（6 维）

1. 优先级（safety / care / info）
2. 免打扰（quiet_hours）
3. 汇总（digest）
4. 去重（dedup_key）
5. 回执（ack_required）
6. 阶梯升级（ladder）

### 60.2 v0.8 新增（3 维）

#### 60.2.1 i18n 翻译

```python
# myhome_agent/notifications/i18n.py
TRANSLATIONS = {
    'rule_fired': {
        'zh-CN': '规则 {rule_id} 已触发',
        'en-US': 'Rule {rule_id} fired',
        'zh-HK': '規則 {rule_id} 已觸發',
    },
    'water_leak_alert': {
        'zh-CN': '检测到水管漏水',
        'en-US': 'Water leak detected',
    }
}

def translate(key, locale='zh-CN', **kwargs):
    template = TRANSLATIONS.get(key, {}).get(locale, TRANSLATIONS[key]['zh-CN'])
    return template.format(**kwargs)
```

触发：每次 fire/notify 时按目标 member.locale 翻译。

#### 60.2.2 富媒体（snapshot / 视频片段）

```python
# myhome_agent/notifications/media.py
@dataclass
class MediaPayload:
    type: str  # 'image' | 'video_clip' | 'audio_clip'
    url: str  # NAS 本地路径或 PWA 端点
    caption: str
    ttl: int  # 秒

def build_media_payload(rule, evidence) -> MediaPayload | None:
    if rule.severity == 'safety' and 'vision' in str(evidence):
        return MediaPayload(
            type='image',
            url=evidence.get('snapshot_path'),
            caption=f"规则 {rule.id} 触发快照",
            ttl=3600
        )
    return None
```

通道支持：
- TG：图片 + caption 完整
- Web Push：icon badge（v0.8 image 字段）
- SMS：仅文字

#### 60.2.3 离线队列

```python
# myhome_agent/notifications/offline_queue.py
class OfflineQueue:
    def enqueue(self, alert, recipient_id, channel):
        self.store.execute(
            "INSERT INTO notification_queue (alert_id, recipient_id, channel, payload, attempts, next_attempt_at) "
            "VALUES (?, ?, ?, ?, 0, ?)",
            (alert.id, recipient_id, channel, json.dumps(alert.payload), now() + 60)
        )

    def flush_online(self):
        items = self.store.execute(
            "SELECT * FROM notification_queue ORDER BY next_attempt_at LIMIT 100"
        )
        for item in items:
            try:
                push(item.channel, item.payload)
                self.mark_delivered(item.id)
            except Exception:
                self.increment_attempts(item.id)
                if item.attempts > 5:
                    self.mark_failed(item.id)
```

```sql
-- notification_queue 表（v0.8 新增）
CREATE TABLE notification_queue (
  id INTEGER PRIMARY KEY,
  alert_id INTEGER NOT NULL,
  recipient_id INTEGER NOT NULL,
  channel TEXT NOT NULL,
  payload TEXT,
  attempts INTEGER DEFAULT 0,
  last_error TEXT,
  next_attempt_at INTEGER NOT NULL,
  delivered_at INTEGER,
  failed_at INTEGER,
  created_at INTEGER NOT NULL
);
CREATE INDEX idx_queue_pending ON notification_queue(next_attempt_at)
  WHERE delivered_at IS NULL AND failed_at IS NULL;
```

### 60.3 v0.8 通知路由配置示例

```yaml
# notification_routing.yaml
rules:
  - id: water_leak_alert_v2
    trigger:
      rule_id: water_microleak_night_v1
    actions:
      - channel: tg
        recipients: [primary_caregiver]
        level: care
        media: snapshot
        i18n: water_leak_alert
        ack_required: true
        ladder: [primary_caregiver, secondary_caregiver]
      - channel: web_push
        recipients: [all]
        level: care
        i18n: water_leak_alert
    offline_queue: true
    retry_policy:
      attempts: 5
      backoff: exponential
```## 61. §50 2FA 治理不变量（v0.8 新增）

> v0.7 §50 已建立治理框架基础，v0.8 加重磅不变量：**2FA 强制场景**。

### 61.1 强制 2FA 场景表

| 场景 | 强制等级 | 实现位置 |
|------|---------|---------|
| **远程 irreversible 控制**（关阀 / 解锁） | 🔴 必 | gateway/server.py |
| **远程 marketplace admin 操作**（导入 irreversible / 启用） | 🔴 必 | governance/marketplace.py |
| **跨家庭切换**（§36.2 搬家） | 🔴 必 | governance/household_switch.py（v0.8 新增）|
| **2FA 自身关闭** | 🔴 必 | auth/twofa.py `disable()` |
| **Fernet 主密钥轮换** | 🔴 必 | vision/crypto.py `rotate_key()`（v0.8 新增）|
| **policy 高危变更**（irreversible capability 启用） | 🟠 推荐 | governance/policy.py（v0.8）|
| **删除家庭** | 🟠 推荐 | §36 全套 |
| **删除设备（含 token）** | 🟠 推荐 | §33.5 |

### 61.2 2FA 触发流程

```
用户操作（远程关阀）
   ↓
FastAPI endpoint 检查 action ∈ REQUIRED_ACTIONS
   ↓
是 → 检查 session 是否已通过 2FA（30 分钟内有效）
   ↓
否 → 返回 401 + 要求 2FA 码
   ↓
前端弹 2FA 输入框 → 用户输 6 位 TOTP
   ↓
POST /api/auth/2fa/verify { code: "123456" }
   ↓
后端 TwoFactorManager.verify() → bcrypt/TOTP 验证
   ↓
成功 → 写 session.twofa_verified_at = now()
   ↓
重放原操作（关阀）
```

### 61.3 2FA 不变量

- **任何 irreversible capability 远程控制必 2FA**——不可绕过
- **2FA 设备更换 / 关闭必 2FA + 备用码**——不可单因子关闭
- **Fernet 主密钥泄露 = 全盘失守**——轮换必 2FA
- **5 次失败 → 锁定 5 分钟**——防爆破
- **备用码一次性 + Fernet 加密**——防泄漏

### 61.4 不启用 2FA 的后果

| 角色 | 后果 |
|------|------|
| admin | 强制启用（否则治理仪表盘自动报警）|
| adult | 推荐启用（远程操作前提示）|
| elder | 不要求（避免误操作导致锁住）|
| child | 不要求 |
| guest | 不要求 |

**v0.8 不变量**：admin 首次登录时**强制引导**启用 2FA（不可跳过）。

### 61.5 与 §43 GDPR 兼容

2FA secret_key Fernet 加密 → GDPR 删除 member 时级联删 2FA 行。
备份码 bcrypt 单向 → 删除时一并清。

### 61.6 实施检查表

- [x] `myhome_agent/auth/twofa.py` TwoFactorManager
- [x] TOTP secret + 备用码生成
- [x] Fernet 加密存储
- [x] bcrypt 备用码单向
- [x] 5 次失败锁定
- [x] 强制场景表
- [ ] `@require_2fa` 装饰器集成到 gateway
- [ ] session.twofa_verified_at 字段
- [ ] PWA 2FA 设置 UI
- [ ] PWA 强制 2FA 弹窗

### 61.7 v0.8 vs 未来

| v0.8（实现）| 完整 v1.0 |
|-------------|----------|
| TOTP + 备用码 | + WebAuthn（FIDO2/YubiKey）|
| session 30min TTL | + 设备信任列表 |
| 强制场景表 | + 风险评分自动判定 |
| 本地 Fernet 加密 | + HSM / KMS 集成 |## 62. §36 跨家庭策略共享（v0.9 深化）

> v0.7 §55 公共规则市场 + v0.9 跨家庭共享 + GDPR 数据可携权，v0.9 完整化。

### 62.1 共享模型

```
[家庭 A]            [家庭 B]            [家庭 C]
   |                  |                  |
   |   export()       |                  |
   +-------> Template +-------> Template |
   |       (rules +   |       (rules +   |
   |        members)  |        members)  |
   |                  |                  |
   |   import()       |                  |
   +------------------+------------------+
```

### 62.2 导出格式（myhome-template-v1）

```json
{
  "version": "v0.9",
  "format": "myhome-template-v1",
  "exported_at": "2026-08-04T...",
  "household_id": 1,
  "rules": [
    {
      "id": "elderly_fall_suspect_v1",
      "description": "...",
      "yaml_body": "...",
      "confidence_base": 0.7,
      "severity": "safety",
      "category": "elderly_care",
      "enabled": true
    }
  ],
  "members": [
    {
      "id": 1,
      "name": "张爷爷",
      "role": "elder",
      "accessibility": {"font_size": "xl", "slow_mode": 1},
      "notification_prefs": {"channels": {"pwa": true, "tg": true}}
    }
  ]
}
```

**v0.9 导出范围**：
- ✅ 规则（不含 audit / feedback）
- ✅ 成员 accessibility 偏好
- ✅ 成员 notification_prefs
- ❌ readings / events（隐私 + 数据量大）
- ❌ 摄像头凭证（安全红线）

### 62.3 导入流程

```python
class HouseholdImporter:
    def import_data(self, target_household_id, exported_data, dry_run=True):
        # 1. 校验格式
        if exported_data['format'] != 'myhome-template-v1':
            raise ValueError("格式不兼容")

        # 2. 校验规则不重复
        existing_ids = {r.id for r in self.store.list_enabled_rules(target_household_id)}
        new_rules = [r for r in exported_data['rules'] if r['id'] not in existing_ids]

        # 3. DPIA 检查（v0.7 §55）
        for r in new_rules:
            if r.get('severity') == 'safety' and not self._admin_confirmed(r):
                if dry_run:
                    continue
                else:
                    raise PermissionError(f"规则 {r['id']} 需 admin 二次确认")

        if dry_run:
            return {'would_import': len(new_rules), 'dry_run': True}

        # 4. 真导入
        with self.store._conn() as c:
            for r in new_rules:
                c.execute("""INSERT INTO rules (...) VALUES (...)""", ...)
                # 强制 enabled=0（§55 不变量）
                c.execute("UPDATE rules SET enabled = 0 WHERE id = ?", (r['id'],))

        return {'imported': len(new_rules), 'enabled': False}
```

### 62.4 共享场景

| 场景 | 适用 |
|------|------|
| 父母家 → 子女家导入 | "老人照护"模板复制 |
| 子女家 → 父母家 | 子女家中调试好的规则共享 |
| 模板市场下载 | §55 公共市场 |
| 跨平台迁移 | NAS 切换 / 备份恢复 |
| 数据可携权 | GDPR §43 |

### 62.5 §36 多家庭升级

v0.9 在 v2.18 §36 单实例 ≤3 家庭基础上加**家庭组**概念：

```
households
  │
  ├── household_1 (主)
  ├── household_2 (副, ≤3)
  └── household_3 (副, ≤3)
```

每个 household 独立配置；通过 template 共享规则。**单实例 ≤3 家庭**硬约束不变。

### 62.6 v0.9 vs 完整 v1.0

| v0.9 | 完整 v1.0 |
|------|----------|
| JSON 导出 | 二进制加密（含凭证）|
| HTTP API | WebSocket 实时同步 |
| 单次导入 | 增量同步 |
| 同版本兼容 | 多版本兼容 |
| 手动 dry_run | 自动冲突解决 |## 63. 公共规则市场 web 平台（v1.0 §55 完整化）

> v0.7 §55 占位 + v0.9 跨家庭模板，v1.0 落地**公共 web 平台** `myhome.marketplace`。

### 63.1 平台架构

```
┌─────────────────────────────────────────────────────┐
│ myhome.marketplace (SaaS web platform)               │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ 模板上传 │  │ 浏览搜索 │  │ 评分评论 │           │
│  └──────────┘  └──────────┘  └──────────┘           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ DPIA 自检│  │ 治理审批 │  │ 一键导入 │           │
│  └──────────┘  └──────────┘  └──────────┘           │
│                                                      │
│  Backend API: api.myhome.marketplace                  │
│  Storage: templates, ratings, audit_logs             │
└──────────────────────┬───────────────────────────────┘
                       │ (HTTPS + Bearer)
                       │
┌──────────────────────┴───────────────────────────────┐
│ myhome-agent 客户端                                  │
│                                                      │
│  myhome-agent marketplace list                       │
│  myhome-agent marketplace install <id>               │
│  myhome-agent marketplace publish <path>             │
│  myhome-agent marketplace rate <id> <stars>           │
└─────────────────────────────────────────────────────┘
```

### 63.2 平台 API（公共）

```
GET    /api/v1/templates?category=elderly_care&sort=rating
GET    /api/v1/templates/{id}
POST   /api/v1/templates                  # 上传（需 admin）
PATCH  /api/v1/templates/{id}/validate    # 治理审批
POST   /api/v1/templates/{id}/rate       # 评分 1-5
POST   /api/v1/templates/{id}/comments   # 评论
GET    /api/v1/templates/{id}/comments
POST   /api/v1/templates/{id}/download   # 获取完整 yaml_body
```

### 63.3 DPIA 自动检查（v1.0 核心）

```python
# myhome_agent/governance/marketplace.py
class MarketplaceDPIA:
    """上传模板时自动跑 DPIA 检查"""

    def check_template(self, template_yaml: dict) -> DPIAResult:
        issues = []

        # 1. 检查 irreversible capability
        if self._has_irreversible(template_yaml):
            if not template_yaml.get('requires_doctor_review'):
                issues.append('Irreversible capability must declare doctor_review')

        # 2. 检查 GDPR compliance
        if not self._has_gdpr_clause(template_yaml):
            issues.append('Missing GDPR data retention clause')

        # 3. 检查 §50 治理不变量
        if not self._has_governance_clause(template_yaml):
            issues.append('Missing governance (L1/L2/L3) declaration')

        # 4. 检查 capabilities 依赖
        for cap in template_yaml.get('requires_capabilities', []):
            if not self._is_whitelisted_capability(cap):
                issues.append(f'Unregistered capability: {cap}')

        # 5. 检查 privacy markers
        if not self._has_privacy_markers(template_yaml):
            issues.append('Missing privacy markers (snapshot TTL, evidence handling)')

        return DPIAResult(
            passed=len(issues) == 0,
            issues=issues,
            risk_score=self._calc_risk_score(issues),
        )

    def _has_irreversible(self, template) -> bool:
        for rule in template.get('rules', []):
            if rule.get('severity') == 'safety' and 'irreversible' in str(rule.get('then', '')):
                return True
        return False
```

### 63.4 半自动治理审批

| 风险分 | 处置 |
|--------|------|
| 0.0-0.3 | 🟢 自动上架 |
| 0.3-0.6 | 🟠 治理 reviewer 审 |
| 0.6+ | 🔴 治理 lead + DPO 双审 |

### 63.5 评分与质量

- 5 星制 + 文字评论
- < 3 星且 ≥ 5 评论 → 自动下架（archived=1）
- < 3 星且 < 5 评论 → 标记"待观察"
- 评分 ≥ 4.5 + 安装 ≥ 100 → "推荐"
- 安装次数 top 10 → "热门"

### 63.6 客户端 CLI

```bash
# 浏览
myhome-agent marketplace list --category elderly_care

# 查看详情
myhome-agent marketplace info elderly_care_5_v1

# 安装（dry_run 默认）
myhome-agent marketplace install elderly_care_5_v1 --dry-run

# 真安装（强制 2FA）
myhome-agent marketplace install elderly_care_5_v1 \
    --2fa-token "$(myhome-agent 2fa token)"

# 评分
myhome-agent marketplace rate elderly_care_5_v1 5

# 发布（需上传权限）
myhome-agent marketplace publish my_rule.yaml \
    --name "My Custom Elderly Care" \
    --category elderly_care
```

### 63.7 v1.0 治理不变量（继承 v0.7）

| 不变量 | v1.0 状态 |
|--------|-----------|
| 1. irreversible 不可自动上架 | ✅ 强制 DPIA 审 |
| 2. market_imported 默认禁用 | ✅ 强制 enabled=0 |
| 3. LLM 自动生成不可发布 | ✅ 强制人工审核 |
| 4. < 3 星自动下架 | ✅ 评论 ≥ 5 才触发 |
| 5. 模板版本绑定 capabilities | ✅ capability 失效自动 archived |
| **6. DPO 必审**（v1.0 新增） | ✅ DPO 双审才能上架 safety |
| **7. 数据驻留声明**（v1.0 新增） | ✅ 模板必须声明数据流 |
| **8. 跨境传输声明**（v1.0 新增） | ✅ 涉及云端必须 GDPR DPA |

### 63.8 商业模式

- **免费层**：5 个内置模板 + 浏览社区
- **Pro 层**（¥99/月）：无限模板 + 上传 + 评分 + DPIA 自检
- **Enterprise 层**（¥999/月）：私有市场 + 自定义审批流 + DPO 顾问

### 63.9 与 v0.7 兼容

- v0.7/v0.8/v0.9 安装的本地模板**完全兼容**
- v1.0 升级：自动加 `source='community'|'marketplace'|'local'` 字段
- marketplace 模板 = 公共 v0.7 模板的子集
## 68. 协议分层（v2.1 Matter / Thread / Zigbee）

> v2.0 §64 跨生态 adapter 在 Matter / Thread / Zigbee 上完整化。
> 三协议是智能家居 2024-2026 主流。

### 68.1 智能家居协议栈分层

```
┌─────────────────────────────────────────────┐
│ 应用层：Matter（统一应用协议）              │
│   - Apple Home / Google Home / Alexa 通用  │
│   - device types + clusters                │
├─────────────────────────────────────────────┤
│ 网络层：Wi-Fi / Ethernet / Thread          │
│   - Wi-Fi：高带宽，墙插设备                │
│   - Ethernet：NAS / 永久在线              │
│   - Thread：低功耗 mesh，电池设备          │
├─────────────────────────────────────────────┤
│ 链路层：802.15.4（Zigbee/Thread 共享）    │
│   - 2.4GHz，全球统一                       │
│   - Zigbee 3.0：成熟生态                   │
│   - Thread 1.3：新主流                     │
├─────────────────────────────────────────────┤
│ 其他：Z-Wave / BLE / Wi-Fi HaLow            │
│   - Z-Wave：北美，频段 < 1GHz              │
│   - BLE：配对 / 临时控制                    │
│   - Wi-Fi HaLow：远距离低功耗              │
└─────────────────────────────────────────────┘
```

### 68.2 协议对比矩阵

| 维度 | Wi-Fi | Thread | Zigbee | Matter |
|------|-------|--------|--------|--------|
| **功耗** | 高 | 低 | 低 | 协议无关 |
| **带宽** | 高 | 中 | 中 | 协议无关 |
| **mesh** | ❌ | ✅ | ✅ | 协议无关 |
| **互操作** | ❌ | ⚠️（部分） | ⚠️（多供应商）| ✅ |
| **生态** | 米家/涂鸦 | Apple/Google/Nest | IKEA/Aqara | 跨生态 |
| **v2.1 状态** | ✅ 已有 | ✅ 新增 | ✅ 新增 | ✅ 新增 |

### 68.3 协议选择指南

| 场景 | 推荐协议 |
|------|---------|
| 智能灯 / 摄像头（墙插）| Wi-Fi + Matter |
| 智能门锁 / 窗户传感器（电池）| Thread + Matter |
| 老式 Zigbee 设备（IKEA / Aqara）| Zigbee2MQTT + Matter bridge |
| 大型家电（NAS / 电视）| Ethernet + Matter |
| 户外设备（远距离）| Wi-Fi HaLow / LoRa |

### 68.4 myhome-agent adapter 选择树

```
新设备
   ↓
Q: Matter 认证？
├── 是 → MatterAdapter（v2.1 优先）
│
└── 否：Thread mesh 设备？
    ├── 是 → ThreadAdapter（via Border Router）
    │
    └── 否：Zigbee 3.0 设备？
        ├── 是 → ZigbeeAdapter（via Z2M/deCONZ/ZHA）
        │
        └── 否则：mihome / tuya / hue / homekit
            （v0.x-v2.0 adapter）
```

### 68.5 多协议设备互操作

**场景**：Aqara Zigbee 传感器 → Apple HomeKit 显示

```
Aqara Sensor (Zigbee)
   ↓
Zigbee2MQTT (Z2M)
   ↓
myhome-agent (MQTT subscriber)
   ↓
统一 capability 映射
   ↓
HomeKit Adapter (HAP-python)
   ↓
iOS Home app 显示
```

**v2.1 实现**：EcosystemAdapter 抽象统一 capability 名 → 跨 adapter 互通。

### 68.6 Commissioning（配网）流程

#### Matter

1. 用户扫码 Matter Setup Code
2. 设备进入 BLE 配对模式
3. myhome-agent → Matter commissioner → CASE 认证
4. 设备获得 IP 地址 + OperationalCredentials
5. 设备加入 fabric，订阅 cluster

#### Thread

1. Border Router（如 Nest Hub）在线
2. 设备进入 commissioning 模式（按住按钮 5s）
3. 设备扫描网络 + 选择 PAN ID + 加密密钥交换
4. 设备获得 RLOC16 + Thread mesh 加入

#### Zigbee

1. 用户在 Z2M / deCONZ 触发 "permit join"（60s）
2. 设备进入配对模式
3. 网络密钥交换 + 设备认证
4. 设备获得 NWK 地址 + 加入 Zigbee mesh

### 68.7 §54 视觉 + §68 协议集成

**v2.1 视觉管线**：
- 摄像头（Wi-Fi RTSP）：v0.3 已实现
- 摄像头（Thread mesh）：v2.1+ 计划
- 视觉规则（v2.1 增强）：Matter device type 映射 → 视觉事件

**例**：Aqara 摄像头（Zigbee v2.1 集成）→ 视觉事件 → 规则引擎 → Matter 通知（HomeKit）

### 68.8 协议升级路径

| 版本 | 新增 |
|------|------|
| v2.1 | Matter / Thread / Zigbee adapter |
| v2.1.1 | OpenThread 真实集成 |
| v2.1.2 | Matter fabric 多管理员 + ACL |
| v2.2 | Wi-Fi HaLow / LoRaWAN |
| v3.0 | 全协议 Mesh 自愈 |

### 68.9 性能 / 资源开销

| Adapter | CPU（idle） | 内存 |
|---------|-----------|------|
| Matter | 2-5% | 50MB |
| Thread | 1-2% | 30MB |
| Zigbee2MQTT | 1-3% | 40MB（MQTT broker 共享）|
| HomeKit | 1-2% | 40MB |

### 68.10 v2.1 真实集成路线

| Adapter | v2.1.0 (本次) | v2.1.1 真实 |
|---------|--------------|------------|
| Matter | capability 映射表 + stub | python-matter controller |
| Thread | Border Router HTTP API | OpenThread SDK (csp-subprocess) |
| Zigbee | Zigbee2MQTT HTTP / deCONZ | ZHA 真实接入 |
| HomeKit | HAP-python bridge | HAP-python + iCloud |

### 68.11 §68 与 §64 adapter 抽象

v2.0 §64 定义 EcosystemAdapter 抽象基类（connect / discover / execute_action / get_state / subscribe_events / health_check）。
v2.1 §68 实现 4 个具体 adapter 全部继承此抽象：

```python
class MatterAdapter(EcosystemAdapter):     # §65
class ThreadAdapter(EcosystemAdapter):     # §66
class ZigbeeAdapter(EcosystemAdapter):     # §67
class HomeKitAdapter(EcosystemAdapter):    # v2.0
```

统一 capability 名（`light.toggle` / `ac.target_temp` / `lock.unlock` 等）使任意 adapter 可互通。
## 69. v3.1 自治 Agent Marketplace（§50 升级路径 3 完整化）

> v1.0 §63 公共规则市场 + v3.0 §50 治理框架，v3.1 升级为**自治 Agent Marketplace**。
> 核心：管家之间**交易 + 协作**——不是静态模板市场，是活体 Agent 经济。

### 69.1 平台架构

```
┌──────────────────────────────────────────────────────┐
│  myhome.market（去中心化 Agent 平台）                │
│                                                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  │ Agent 目录  │  │ 任务市场   │  │ 信誉系统   │    │
│  │ (card)     │  │ (exchange) │  │ (rating)   │    │
│  └────────────┘  └────────────┘  └────────────┘    │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  │ 积分钱包   │  │ 仲裁池     │  │ 跨家庭协作 │    │
│  │ (wallet)   │  │ (dispute)  │  │ (consensus) │   │
│  └────────────┘  └────────────┘  └────────────┘    │
│                                                      │
│  协议层：A2A + JSON-RPC + WebSocket + 区块链结算   │
└──────────────────────┬───────────────────────────────┘
                       │ (HTTPS + signed messages)
                       │
┌──────────────────────┴───────────────────────────────┐
│  Client myhome-agent（每家庭 1 个实例）              │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ Agent    │  │ Wallet   │  │ 协作     │         │
│  │ Card     │  │          │  │ Handler  │         │
│  └──────────┘  └──────────┘  └──────────┘         │
└──────────────────────────────────────────────────────┘
```

### 69.2 Agent Card（能力声明）

每个 myhome-agent 实例发布 Agent Card：

```json
{
  "agent_id": "agent_zhang_family_001",
  "version": "v3.1",
  "household": "张爷爷家",
  "capabilities": [
    "elderly_care", "rule_execution", "vision_monitoring",
    "fall_detection", "medication_reminder"
  ],
  "resources": {
    "ai_models": ["deepseek", "qwen-vl"],
    "compute": "RTX 3060",
    "devices": 23
  },
  "availability": {
    "timezone": "Asia/Shanghai",
    "active_hours": ["06:00-23:00"],
    "sla": "best-effort"
  },
  "pricing": {
    "currency": "CARE-token",
    "rate_per_call": 0.5,
    "free_credits_monthly": 100
  },
  "rating": {
    "score": 920,
    "calls_completed": 15234,
    "disputes": 2
  }
}
```

### 69.3 服务目录（5 类可交易）

| 服务 | 卖方 | 买方 | 价格 | SLA |
|------|------|------|------|-----|
| **rule 模板** | 任何家庭 | 公共 | 10 token / 下载 | - |
| **视觉模型** | 算力富余家庭 | 算力不足 | 5 token / 次 | 1s 响应 |
| **兜底推理** | LLM API 配额多 | LLM 用尽 | 0.5 token / 1K token | 3s |
| **异常检测样本** | 真实事件家庭 | 训练 | 100 token / 1K 样本 | 脱敏 |
| **设备控制代理** | 跨生态设备拥有者 | 跨家庭用户 | 1 token / 调用 | 2s |

### 69.4 跨家庭协作场景

#### 场景 1：任务接力
```
A 家庭管家（老人照护）→ 检测到陌生人在门口
   ↓ 查 A 自己的能力
   没有：高级视觉模型
   ↓ Marketplace 查
   B 家庭有：YOLOv8n-pose + 跌倒检测
   ↓
   委托 B（付费 5 token）
   ↓ B 处理
   → 返回结果给 A
```

#### 场景 2：资源池
```
紧急情况：A 家庭摄像头算力不够
↓ Marketplace 查"视觉算力"
C/D/E 家庭富余（深夜 GPU 闲置）
↓ 招标
C 抢单（最低 3 token）
↓ 处理
A + C 都加信誉分
```

#### 场景 3：共识投票
```
5 家庭都遇到同一异常（新设备型号识别不出）
↓
发起"通用规则升级"投票
↓
3/5 家庭同意 → 规则自动同步到所有
```

### 69.5 A2A 协议（v3.1 新增）

```json
// Agent → Agent 消息格式
{
  "a2a_version": "1.0",
  "from_agent": "agent_abc_001",
  "to_agent": "agent_xyz_002",
  "message_id": "msg_20260804153000_abc",
  "timestamp": 1785816800,
  "signature": "ed25519:...",
  "type": "task_request | task_response | negotiation | consensus_vote",
  "payload": {
    "task": "vision.detect",
    "args": {
      "image_url": "https://...",
      "model": "yolov8n-pose",
      "deadline_ms": 5000
    },
    "escrow_tokens": 5.0
  }
}
```

**4 类消息类型**：
- `task_request`：任务委托
- `task_response`：结果返回
- `negotiation`：价格/能力协商
- `consensus_vote`：投票

### 69.6 共识算法（v3.1 简化 PBFT）

| 阶段 | 动作 | 时间窗 |
|------|------|--------|
| 1. **Pre-prepare** | 协调器广播请求 | 0s |
| 2. **Prepare** | 其他 Agent 投票 | 0-2s |
| 3. **Commit** | ≥2/3 同意 → 提交 | 2-3s |
| 4. **Reply** | 协调器返回结果 | 3-4s |

**简化版 PBFT**（家用场景不需要 BFT 完整版）：
- 单协调器（myhome.market 平台）
- Agent 投票（≥2/3 通过）
- 超时 → 重新投票

### 69.7 信誉系统

| 维度 | 公式 | 权重 |
|------|------|------|
| 完成任务率 | completed / total | 30% |
| 响应时间 | avg latency vs SLA | 20% |
| 用户评分 | 1-5 星 | 30% |
| 争议率 | disputes / total | 20% |
| **总评分** | 0-1000 | - |

**降级机制**：
- 评分 < 300：自动下架
- 评分 < 500：限流（每天 10 任务）
- 评分 > 800：搜索排名靠前

### 69.8 经济模型

#### 积分体系（CARE-token）

| 来源 | 数额 | 用途 |
|------|------|------|
| 完成任务 | +1-10 token | 出售给其他家庭 |
| 提供资源 | +0.5/小时 | 算力出租 |
| 数据贡献 | +100/1K 样本 | 训练用（脱敏）|
| 初始赠送 | +100 token | 新家庭加入 |
| 购买 token | 1 token = ¥0.1 | 急用时 |

#### 结算方式（v3.1 stub / v3.5 区块链）

- v3.1：平台中心化记账（MySQL 账本）
- v3.5：迁移到区块链（Polygon / Arbitrum 侧链）
- 用户私钥本地保管（钱包即账户）

### 69.9 隐私边界

| 边界 | 实施 |
|------|------|
| **家庭数据不出门** | 联邦学习 / 梯度上传 |
| **跨家庭只传必要字段** | Agent Card + 任务单 |
| **协商时只传统计** | 不传原始数据 |
| **争议时上链证据** | 哈希 + 时间戳 |

### 69.10 v3.1 实施路线

| 阶段 | 内容 | 时间 |
|------|------|------|
| v3.1.0 | A2A 协议 + Agent Card + 平台 Stub | 3 月 |
| v3.1.1 | 服务目录 + 信誉系统 + 任务市场 | 3 月 |
| v3.1.2 | 跨家庭协作（任务接力 / 资源池）| 2 月 |
| v3.1.3 | 共识投票 + 规则共享 | 2 月 |
| v3.1.4 | 经济模型（积分 / 钱包）| 2 月 |
| v3.1.5 | 区块链结算 | 4 月 |

**总工期 16 月**，跨 3 个 v3.x 版本。

## 70. v4.0 联邦学习（多家庭协作训练）

> v3.1 Agent Marketplace + v3.0 长期记忆 的**自然延伸**：
> 多个家庭协作训练一个共享的"老人照护模型"，**原始数据不出门**。

### 70.1 核心问题

```
问：如何让 1000 个家庭协作训练一个"摔倒检测"模型，
    但每个家庭的摄像头数据不上传到服务器？

答：联邦学习（Federated Learning）
```

### 70.2 架构

```
┌──────────────────────────────────────────────────────┐
│  Cloud Coordinator（v4.0）                            │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐                │
│  │ Global Model │  │ Aggregator   │                │
│  │  (start)     │  │ (FedAvg)     │                │
│  └──────────────┘  └──────────────┘                │
│         │                  │                       │
│         │ 分发模型         │ 收集梯度              │
│         ↓                  ↑                       │
└─────────┼──────────────────┼───────────────────────┘
          │                  │
┌─────────┼──────────────────┼───────────────────────┐
│  Family A              Family B              Family C
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐│
│  │ Local Model  │  │ Local Model  │  │ Local Model ││
│  │ (copy)      │  │ (copy)      │  │ (copy)     ││
│  └──────────────┘  └──────────────┘  └────────────┘│
│         │                  │                  │     │
│         ↓                  ↓                  ↓     │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐│
│  │ Local Data   │  │ Local Data   │  │ Local Data ││
│  │ (cameras)   │  │ (cameras)   │  │ (cameras) ││
│  └──────────────┘  └──────────────┘  └────────────┘│
└──────────────────────────────────────────────────────┘
```

### 70.3 训练流程（v4.0 一轮迭代）

```
T+0s:   Cloud 分发 Global Model v1.0 → 1000 家庭
T+1m:   每家庭本地训练（用本地摄像头数据 + 5 epochs）
T+10m:  每家庭上传梯度（不是数据！是 8-bit 量化 + 加密的梯度）
T+11m:  Cloud Secure Aggregation
        ├─ 同态加密
        ├─ 过滤异常梯度（防恶意）
        └─ FedAvg 加权聚合
T+12m:  生成 Global Model v1.1
T+13m:  分发 v1.1 → 1000 家庭
T+15m:  重新训练 ...
循环 N 轮 → Global Model vN（N=10-50）
```

### 70.4 三大隐私技术

| 技术 | 作用 | v4.0 实施 |
|------|------|----------|
| **Secure Aggregation** | Cloud 看不到单家庭梯度 | 同态加密（Paillier） |
| **Differential Privacy** | 梯度加 noise 防反推 | ε=1.0 Gaussian |
| **Homomorphic Encryption** | 加密域聚合 | TenSEAL / Pyfhel |

### 70.5 模型选型

| 候选 | 参数量 | 边缘可行性 | v4.0 推荐 |
|------|--------|----------|----------|
| YOLOv8n | 3M | ✅ 极易 | ✅ |
| MobileNet-V3 | 5M | ✅ 极易 | ✅ |
| EfficientNet-B0 | 5M | ✅ 易 | ⚠️ |
| YOLOv8s | 11M | ⚠️ 中 | ❌（太大）|
| ResNet-18 | 11M | ⚠️ 中 | ❌ |

**v4.0 推荐**：YOLOv8n + MobileNet（轻量 + 可在 4GB 显存跑）

### 70.6 训练数据分布

```
家庭 A: 10 个摄像头 × 30 天 = ~10K 摔倒样本 + ~1M 背景
家庭 B: 5 个摄像头 × 30 天 = ~5K 摔倒 + ~500K 背景
...
1000 家庭 × 不平衡分布

→ 各家庭数据非独立同分布（Non-IID）
→ 需 FedProx 算法（v4.0 默认）
```

### 70.7 FedAvg vs FedProx

| 算法 | 公式 | 适合 |
|------|------|------|
| **FedAvg** | 简单平均 | IID 数据 |
| **FedProx** | FedAvg + 近端项 | Non-IID（家庭数据）|
| **FedNova** | 归一化平均 | 不等步数 |
| **SCAFFOLD** | 修正梯度 | 高异质性 |

**v4.0 默认 FedProx**（家庭数据天然异质）。

### 70.8 异常检测（防恶意梯度）

```
Cloud 收到 1000 家庭梯度
   ↓
检测：哪些梯度"明显不同"？
   ↓
方法 1: 统计检测（>3σ 异常）
方法 2: Krum（选最接近其他人的）
方法 3: Median 聚合（鲁棒）
   ↓
过滤恶意 / 异常家庭
   ↓
剩余 800+ 家庭聚合
```

### 70.9 异步聚合（不阻塞家庭）

| 同步模式 | 问题 | v4.0 异步 |
|---------|------|----------|
| 同步 | 等最慢家庭 30+ 分钟 | 慢者掉队 |
| 异步 | Cloud 收 1 个就聚合 1 次 | 简单 + 鲁棒 |

**v4.0 异步**：
- Cloud 不等所有家庭
- 每收到 1 个梯度立即更新全局模型
- 优点：高效 + 家庭不阻塞
- 缺点：梯度陈旧（stale gradient）

### 70.10 联邦 vs 中心化训练对比

| 维度 | 中心化 | 联邦学习（v4.0） |
|------|--------|-----------------|
| **数据** | 上传云端 | 留在本地 |
| **隐私** | ❌ | ✅ 原始数据不出门 |
| **算力** | Cloud 集中 | 家庭分布式 |
| **速度** | 快 | 慢（多轮）|
| **法规** | GDPR 复杂 | ✅ GDPR §22 / §25 友好 |
| **异常** | Cloud 看到 | 防恶意检测 |

### 70.11 联邦学习 v4.0 选型

| 库 | 优势 | 适用 |
|----|------|------|
| **Flower** | 易用 / Python / FedAvg/Prox 内置 | ✅ v4.0 推荐 |
| PySyft | 安全聚合 | 高级用法 |
| OpenFL | Intel 优化 | 商业 |
| TensorFlow Federated | TF 生态 | 兼容 TF |

**v4.0 默认 Flower**（最成熟）。

### 70.12 退出机制

```
家庭 A 决定退出（GDPR §17 / 个人原因）
↓
1. 通知 Cloud
2. 删除本地模型（不再更新）
3. 已贡献的梯度已聚合到 Global（无法删除）
4. 不能再影响 Global Model
5. audit log 留痕
```

### 70.13 训练数据自动标注

v4.0 关键创新：**自动标注 + 联邦训练**：

```
每个家庭本地：
1. YOLO 检测到 fall_detected（候选）
2. 询问用户：是否真的摔倒？
   "刚才检测到老人异常姿势，是真的吗？" 是/否
3. 真实样本 → 自动标注（fall / not-fall）
4. 累积 ≥10 样本 → 加入本地训练
5. 训练完 → 上传梯度（不上传样本！）
```

**v4.0 优势**：无需人工标注数据集 → 模型自动学习。

### 70.14 实施路线

| 阶段 | 内容 | 时间 |
|------|------|------|
| v4.0.0 | Flower + FedProx + 异步聚合 | 3 月 |
| v4.0.1 | Secure Aggregation（Paillier）| 2 月 |
| v4.0.2 | DP noise + 异常检测 | 2 月 |
| v4.0.3 | 自动标注 + 联邦训练 | 3 月 |
| v4.0.4 | 1000 家庭实测 | 4 月 |

**总工期 14 月**。

### 70.15 v4.0 价值

```
问题：每个家庭只有 10-50 个摔倒样本
      → 中心化训练数据不足
      → 模型准确率 < 70%

v4.0 联邦：1000 家庭 × 50 样本 = 50K 样本
          → 不上传数据
          → 协作训练
          → 模型准确率 92%+
          → 每个家庭都受益
```

**这是 AI 增强 v3.0 + 跨家庭协作 v3.1 + 联邦学习 v4.0 三者结合的**终极形态**。