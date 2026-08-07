# Contributing to myhome-agent

感谢你愿意参与 myhome-agent。以下是贡献前需要知道的事。

## 开发环境

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -e ".[dev]"
```

## 测试

```bash
python -m pytest
```

新增或修改功能时，请在 `tests/` 中补充对应的 pytest 用例。当前测试覆盖鉴权、2FA、规则引擎、通知、审计、待确认动作、钱包、共识、联邦加密与快照。

## 代码约定

- Python 3.10+，保持模块边界：`collectors` 只通过 `memory.Store` 写数据。
- 不要在代码中硬编码密钥；一律走 `.env` 与 `security/env_secret.py`。
- SQLite 连接使用 `with store._conn() as c:`，由上下文管理器负责提交与关闭。
- 新端点默认受认证中间件保护，敏感操作挂 RBAC 权限。

## 提交与 PR

- 建议小步提交，一个 PR 对应一个主题。
- PR 标题与描述使用中文或英文均可，说明改动目的与验证方式。
- 提交前运行 `python -m compileall myhome_agent` 与 `python -m pytest`。

## 安全

- 发现安全漏洞请走 GitHub Security Advisories 私有报告，不要公开提交漏洞细节。
- 永远不要提交 `.env`、数据库文件或模型权重（`.gitignore` 已排除）。
