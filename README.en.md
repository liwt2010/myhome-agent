# 🏠 myhome-agent · Personal Home Butler

A local-first home agent: collect smart-device data, learn household routines, run a deterministic rule engine, chat naturally through an LLM, and audit or require confirmation for autonomous actions.

Other languages: 简体中文（[README.md](README.md)）· 繁體中文（[README.zh-TW.md](README.zh-TW.md)）

## Core Capabilities

- Device integrations: Mi Home (micloud/miio), Tuya, Hue, Matter, Zigbee, Thread (Matter/Zigbee/Thread code is wired; real-device testing awaits chip-tool/hardware)
- Rule engine: cross-signal reasoning, confidence calibration, LLM fallback, false-positive feedback loop
- Vision pipeline: RTSP + YOLO person/fall/fire detection, snapshot storage and access control
- Natural interaction: DeepSeek (default) and multi-LLM routing, tool calling, long-term memory
- Governance: L0-L4 autonomy levels, risk scoring, decision audit
- Security by default: gateway auth, member login/RBAC, 2FA/WebAuthn, second confirmation for high-risk devices
- Notifications & audit: Telegram/in-app notifications, unified audit API, pending actions
- Federated learning: real Paillier homomorphic encryption + differential privacy

## What Makes It Different from Mainstream Smart Home

| Dimension | Mainstream platforms (Mi Home / Huawei / Home Assistant, etc.) | myhome-agent |
|-----------|-------------------------------------------------------------|--------------|
| Positioning | Device control and scene automation platform | Personal home butler: understands members, routines, memory, and is auditable |
| Decision logic | Fixed if-else automations | Deterministic rule engine + confidence calibration + LLM fallback for low-confidence cases |
| Data ownership | Depends on vendor or platform cloud | Local-first, SQLite closed loop, encrypted RTSP credentials |
| Security | Weak auth or platform account | Gateway auth + member RBAC + 2FA/WebAuthn + second confirmation for high-risk devices + full audit |
| Cross-ecosystem | Usually locked to one brand | Unified management for Mi Home / Tuya / Hue / Matter / Zigbee / Thread |
| Autonomy | Fixed scene automations | L0-L4 autonomy levels + risk scoring + replayable audit |
| Notifications | Simple push | Alert → notification → pending action (confirm / cancel / expire) |
| Privacy | Heavy cloud data collection | Optional local models, federated learning with Paillier HE + DP |

Core idea: turn every device and member of the home into one cohesive picture a butler can understand, instead of a pile of switches and automations. **A deterministic rule engine handles safety-critical cases (water leak / gas / smoke); the LLM only handles ambiguous cases; high-risk actions always ask a human first, and every decision is auditable.**

## Quick Start

### 1. Install

```bash
cd myhome-agent
pip install -e .
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env; DEEPSEEK_API_KEY is the minimum requirement
```

On first start, these secrets are generated and written to `.env` (keep them private, never distribute):

- `MYHOME_API_TOKEN`: gateway API token (also usable from the login page "API Token" tab)
- `MYHOME_JWT_SECRET`: signing key for member JWTs and 2FA
- `MYHOME_FERNET_KEY`: encryption key for RTSP credentials

### 3. Run

```bash
python -m myhome_agent
```

Open `http://localhost:8300`. The first visit shows a login page: sign in with a member password (set via the admin API first) or paste `MYHOME_API_TOKEN`.

### 4. Common Commands

```bash
python -m myhome_agent serve          # start the web service (default)
python -m myhome_agent chat "How is home?"
python -m myhome_agent sync           # Mi Home cloud sync (requires micloud)
python -m myhome_agent analyze        # routine learning + anomaly detection
python -m myhome_agent init           # seed rules
python -m myhome_agent rules list     # list rules
```

## Directory Layout

```text
myhome-agent/
├── myhome_agent/
│   ├── gateway/        # FastAPI gateway (REST + WebSocket)
│   ├── auth/           # API token, member login/RBAC, 2FA, WebAuthn
│   ├── collectors/     # device adapters (Mi Home/Tuya/Hue/Matter, etc.)
│   ├── memory/         # SQLite storage
│   ├── rules/          # rule engine
│   ├── agent/          # LLM clients and agent loop
│   ├── vision/         # RTSP/YOLO vision pipeline
│   ├── governance/     # autonomy, quotas, consensus, marketplace
│   ├── federation/     # federated learning and privacy
│   └── security/       # KMS and secret management
├── web/                # PWA frontend
├── docs/               # documentation
├── tests/              # pytest unit tests
└── scripts/            # hardware integration scripts
```

## API Summary

### Authentication

- `POST /api/auth/login`: member password login, returns a 24h JWT
- `POST /api/auth/credentials`: admin sets a member password
- `GET /api/auth/members`: public member list (used by the login page)
- `/api/auth/2fa/*`, `/api/auth/webauthn/*`: TOTP and FIDO2

### Home & Devices

- `GET /api/summary`, `GET /api/devices`, `GET /api/members`, `GET /api/presence`
- `POST /api/devices/control` (high-risk devices require `X-2FA-Token`)
- `POST /api/devices/control/secure` (mandatory 2FA)

### Rules & Scenes

- `GET /api/rules`, `POST /api/rules/feedback`
- `GET/POST /api/scenes`, `POST /api/scenes/run`
- `GET /api/privacy`, `POST /api/privacy/vision|llm|remote`

### Audit & Pending Actions

- `GET /api/audit/rules|decisions|notifications|summary|export`
- `GET /api/actions/pending`, `POST /api/actions/{token}/confirm|cancel`

### WebSocket

- `/ws/chat`: real-time chat
- `/ws/events`: alert push (requires `?token=`)

See [ARCHITECTURE.md](ARCHITECTURE.md#6-api-清单) for the full endpoint list.

## Configuration

| Variable | Description |
|----------|-------------|
| `DEEPSEEK_API_KEY` | default LLM key |
| `MI_USERNAME` / `MI_PASSWORD` / `MI_REGION` | Mi Home cloud account |
| `MYHOME_DB_PATH` / `MYHOME_HOST` / `MYHOME_PORT` | database path and bind address |
| `MYHOME_API_TOKEN` / `MYHOME_JWT_SECRET` | gateway/JWT secrets (auto-generated) |
| `MYHOME_A2A_SECRET` | shared A2A secret for cross-home messaging |
| `MYHOME_TELEGRAM_ALLOWED_CHAT_IDS` | Telegram chat-id allowlist |
| `MYHOME_VISION_ENABLED` / `MYHOME_SNAPSHOT_DIR` | vision toggle and snapshot directory |
| `MYHOME_LLM_BUDGET` / `MYHOME_LLM_PREFERRED` / `MYHOME_LLM_PRIVACY` | LLM budget and privacy mode |

## Security Notes

- Every API and WebSocket (except health, login, and 2FA/WebAuthn login) requires a Bearer credential.
- Lock/gas/camera/curtain controls require 2FA.
- Direct control actions triggered by rules enter `pending_actions` and wait for user confirmation.
- `.env` holds real credentials: set permissions to `600` and never distribute it.
- Use an HTTPS reverse proxy before exposing the service.

## Development & Tests

```bash
pip install -e ".[dev]"
python -m pytest
```

Currently 35 unit tests cover auth, 2FA, rule engine, notifications, audit, wallet, consensus, federated encryption, and snapshots.

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md): architecture and implementation status
- [docs/CHANGELOG.md](docs/CHANGELOG.md): change log
- [docs/DOCS_SYNC.md](docs/DOCS_SYNC.md): documentation sync record
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md): deployment
- [docs/REAL_PROTOCOL_TESTING.md](docs/REAL_PROTOCOL_TESTING.md): real protocol testing

## License

MIT
