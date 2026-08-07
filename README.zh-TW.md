# 🏠 myhome-agent · 家庭私人管家

本地優先的家庭智慧體：採集智慧裝置資料、學習作息、執行確定性規則引擎、透過 LLM 自然對話，並對自主行為進行稽核與二次確認。

其他語言：简体中文（[README.md](README.md)）· English（[README.en.md](README.en.md)）

## 核心能力

- 裝置整合：米家（micloud/miio）、塗鴉、Hue、Matter、Zigbee、Thread
- 規則引擎：跨訊號推理、信賴度校正、LLM 兜底、誤報回饋閉環
- 視覺管線：RTSP + YOLO 人形/跌倒/火焰偵測、快照儲存與存取控制
- 自然互動：DeepSeek（預設）等多 LLM 路由、工具呼叫、長期記憶
- 自主治理：L0-L4 等級、風險評分、決策稽核
- 安全預設：閘道鑑權、成員登入/RBAC、2FA/WebAuthn、高風險裝置二次確認
- 通知與稽核：Telegram/站內通知、統一稽核 API、待確認動作
- 聯邦學習：真實 Paillier 同態加密 + 差分隱私

## 與傳統全屋智能的差異

| 面向 | 傳統全屋智能（米家 / 華為 / Home Assistant 等） | myhome-agent |
|------|-----------------------------------------------|--------------|
| 定位 | 裝置控制與場景自動化平台 | 家庭私人管家：懂成員、懂作息、能記憶、可稽核 |
| 判斷邏輯 | 固定 if-else 自動化 | 確定性規則引擎 + 信賴度校正 + 低信賴度 LLM 兜底 |
| 資料主權 | 依賴廠商雲或平台雲 | 本地優先，SQLite 本地閉環，RTSP 憑證加密 |
| 安全 | 弱鑑權或平台帳號 | 閘道鑑權 + 成員 RBAC + 2FA/WebAuthn + 高風險裝置二次確認 + 全量稽核 |
| 跨生態 | 通常綁定單一品牌 | 米家 / 塗鴉 / Hue / Matter / Zigbee / Thread 統一管理 |
| 自主能力 | 固定場景自動化 | L0-L4 自主等級 + 風險評分 + 可回放稽核 |
| 通知與確認 | 簡單推播 | 告警 → 通知 → 待確認動作（確認 / 取消 / 過期） |
| 隱私 | 大量資料上雲 | 本地模型可設定，聯邦學習用 Paillier 同態加密 + DP |

核心理念：把家中所有裝置和成員變成一個「管家」能理解的整體，而不是一堆開關與自動化。**確定性規則引擎兜底安全（水浸 / 瓦斯 / 煙霧），LLM 只處理模糊地帶；高風險動作永遠先問人，所有決策可稽核。**

## 快速開始

### 1. 安裝

```bash
cd myhome-agent
pip install -e .
```

### 2. 設定

```bash
cp .env.example .env
# 編輯 .env，至少設定 DEEPSEEK_API_KEY
```

首次啟動會自動產生並寫入以下金鑰（請妥善保管，不要散佈）：

- `MYHOME_API_TOKEN`：閘道 API token（登入頁也可選擇 API Token 模式）
- `MYHOME_JWT_SECRET`：成員 JWT 與 2FA 簽章金鑰
- `MYHOME_FERNET_KEY`：RTSP 憑證加密金鑰

### 3. 啟動

```bash
python -m myhome_agent
```

瀏覽器開啟 `http://localhost:8300`。首次造訪會顯示登入頁：可輸入成員密碼（需先透過管理 API 設定）或貼上 `MYHOME_API_TOKEN`。

### 4. 常用指令

```bash
python -m myhome_agent serve          # 啟動 Web 服務（預設）
python -m myhome_agent chat "家裡怎麼樣？"
python -m myhome_agent sync           # 米家雲端同步（需安裝 micloud）
python -m myhome_agent analyze        # 作息學習 + 異常偵測
python -m myhome_agent init           # 初始化規則種子
python -m myhome_agent rules list     # 規則清單
```

## 目錄結構

```text
myhome-agent/
├── myhome_agent/
│   ├── gateway/        # FastAPI 閘道（REST + WebSocket）
│   ├── auth/           # API token、成員登入/RBAC、2FA、WebAuthn
│   ├── collectors/     # 裝置採集介面卡（米家/塗鴉/Hue/Matter 等）
│   ├── memory/         # SQLite 儲存
│   ├── rules/          # 規則引擎
│   ├── agent/          # LLM 用戶端與 Agent 迴圈
│   ├── vision/         # RTSP/YOLO 視覺管線
│   ├── governance/     # 自治、配額、共識、市場
│   ├── federation/     # 聯邦學習與隱私
│   └── security/       # KMS 與金鑰管理
├── web/                # PWA 前端
├── docs/               # 文件
├── tests/              # pytest 單元測試
└── scripts/            # 硬體聯調腳本
```

## API 摘要

### 認證

- `POST /api/auth/login`：成員密碼登入，回傳 24h JWT
- `POST /api/auth/credentials`：管理員設定成員密碼
- `GET /api/auth/members`：公開成員清單（登入頁使用）
- `/api/auth/2fa/*`、`/api/auth/webauthn/*`：TOTP 與 FIDO2

### 家庭與裝置

- `GET /api/summary`、`GET /api/devices`、`GET /api/members`、`GET /api/presence`
- `POST /api/devices/control`（高風險裝置需 `X-2FA-Token`）
- `POST /api/devices/control/secure`（強制 2FA）

### 規則與場景

- `GET /api/rules`、`POST /api/rules/feedback`
- `GET/POST /api/scenes`、`POST /api/scenes/run`
- `GET /api/privacy`、`POST /api/privacy/vision|llm|remote`

### 稽核與待確認動作

- `GET /api/audit/rules|decisions|notifications|summary|export`
- `GET /api/actions/pending`、`POST /api/actions/{token}/confirm|cancel`

### WebSocket

- `/ws/chat`：即時對話
- `/ws/events`：告警推播（需 `?token=`）

完整端點見 [ARCHITECTURE.md](ARCHITECTURE.md#6-api-清單)。

## 設定項目

| 變數 | 說明 |
|------|------|
| `DEEPSEEK_API_KEY` | 預設 LLM 金鑰 |
| `MI_USERNAME` / `MI_PASSWORD` / `MI_REGION` | 米家雲端帳號 |
| `MYHOME_DB_PATH` / `MYHOME_HOST` / `MYHOME_PORT` | 資料庫與監聽位址 |
| `MYHOME_API_TOKEN` / `MYHOME_JWT_SECRET` | 閘道與 JWT 金鑰（自動產生） |
| `MYHOME_A2A_SECRET` | 跨家庭 A2A 共用金鑰 |
| `MYHOME_TELEGRAM_ALLOWED_CHAT_IDS` | Telegram chat_id 白名單 |
| `MYHOME_VISION_ENABLED` / `MYHOME_SNAPSHOT_DIR` | 視覺開關與快照目錄 |
| `MYHOME_LLM_BUDGET` / `MYHOME_LLM_PREFERRED` / `MYHOME_LLM_PRIVACY` | LLM 預算與隱私模式 |

## 安全說明

- 除健康檢查、登入、2FA/WebAuthn 登入外，所有 API 與 WebSocket 都需要 Bearer 憑證。
- 門鎖/瓦斯/攝影機/主窗簾控制必須通過 2FA。
- 規則觸發的直接控制動作進入 `pending_actions`，等待使用者確認。
- `.env` 包含真實憑證，請設定 `600` 權限並確保不隨專案散佈。
- 建議使用 HTTPS 反向代理後再對外提供服務。

## 開發與測試

```bash
pip install -e ".[dev]"
python -m pytest
```

目前 35 項單元測試涵蓋鑑權、2FA、規則引擎、通知、稽核、錢包、共識、聯邦加密與快照。

## 文件索引

- [ARCHITECTURE.md](ARCHITECTURE.md)：架構與實作現況
- [docs/CHANGELOG.md](docs/CHANGELOG.md)：變更記錄
- [docs/DOCS_SYNC.md](docs/DOCS_SYNC.md)：文件同步記錄
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)：部署
- [docs/REAL_PROTOCOL_TESTING.md](docs/REAL_PROTOCOL_TESTING.md)：真實協定聯調

## License

MIT
