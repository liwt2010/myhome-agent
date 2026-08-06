# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| v3.0.1+ | ✅ Active          |
| v0.7.x  | ⚠️ Security fixes only |
| < v0.7  | ❌ End of life     |

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security problems.**

Report security issues privately to: **security@myhome-agent.local**

Include:
- Description of the vulnerability
- Steps to reproduce
- Affected version
- Potential impact

We aim to respond within **72 hours** and provide a fix timeline within **7 days** for critical issues.

## Security Architecture

myhome-agent is designed with **local-first privacy** as the core principle.

### Data Storage
- All data stored locally on user's NAS (SQLite + WAL mode)
- 30-day automatic cleanup for sensor data, events, vision snapshots
- household_id strict isolation in all queries (CI enforced)
- Fernet encryption for sensitive data (rtsp_url, snapshots, 2FA secrets)

### Authentication
- TOTP-based 2FA (RFC 6238) — see `auth/twofa.py`
- WebAuthn/FIDO2 support (YubiKey / TouchID / Windows Hello) — see `auth/webauthn.py`
- JWT session tokens (30-minute TTL) — see `auth/session.py`
- Per-member chat_id binding for Telegram

### Authorization
- 9-role policy matrix (admin / adult / elder / child / nanny / etc.) — see `governance/policy.py`
- 4-dimensional risk assessment for autonomous actions
- L0-L4 autonomy levels with mandatory confirm for safety operations
- Audit log for all governance decisions

### LLM Integration
- Privacy modes: `public` (cloud) / `sensitive` (local only)
- 国货 LLM 优先 (DeepSeek, Qwen, Zhipu, Kimi, Wenxin) — data sovereignty
- 80/20 budget split: 80% 国货 / 20% 国外
- redactor removes sensitive fields before cloud LLM calls
- API keys stored in `.env` (NEVER commit — see `.gitignore`)

### Federation (v4.0+)
- Secure Aggregation: Cloud never sees individual household data
- Differential Privacy: Gaussian noise added to gradients
- 8-bit gradient compression to save bandwidth
- Multi-firm federated training with consent + GDPR right-to-be-forgotten

## Security Best Practices for Users

1. **Never commit `.env`** — `.gitignore` includes it, but always verify
2. **Use environment variables** for secrets in production
3. **Rotate Fernet keys** every 90 days
4. **Enable 2FA** for admin accounts
5. **Use WebAuthn** for irreversible capability operations
6. **Review audit logs** monthly
7. **Backup `.env` securely** (e.g., password manager)
8. **Update regularly** for security patches

## Reporting Security Issues Timeline

| Severity | Initial Response | Fix Target |
| -------- | ---------------- | ----------- |
| Critical | 24 hours | 7 days |
| High     | 72 hours | 30 days |
| Medium   | 1 week | 90 days |
| Low      | 2 weeks | Next release |

## Acknowledgments

We thank the security community for responsible disclosure.

## See Also

- [DEPLOYMENT.md](DEPLOYMENT.md) — Production deployment guide
- [DPIA.md](DPIA.md) — Data Protection Impact Assessment
- [DPA.md](DPA.md) — Data Processing Agreement
- [ISO27001.md](ISO27001.md) — ISO 27001 preparation
- [SOC2.md](SOC2.md) — SOC2 Type II preparation
- [AUDIT_CHECKLIST.md](AUDIT_CHECKLIST.md) — Third-party audit checklist
- [TODO.md](TODO.md) — Project roadmap

---

**Last updated**: 2026-08-04 (v3.0.1)
**License**: MIT (or as specified in LICENSE file)