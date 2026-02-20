# openclaw-guide

Security-first operational guide for self-hosted OpenClaw AI agent.

## What It Does

Provides installation, configuration, security hardening, and operational guidance for OpenClaw — a self-hosted AI agent platform with 50+ integrations. Emphasizes vulnerability patching, malicious skill detection, and secure baseline configuration.

## Key Topics

- **Architecture** — Gateway (Node.js), Pi Agent (LLM orchestration), 15+ channel adapters
- **Security Hardening** — 6-step setup, secure baseline config, loopback binding, token auth
- **Known CVEs** — CVE-2026-25253 (RCE 8.8), CVE-2026-25157 (SSH injection 7.8), CVE-2026-24763 (Docker escape 8.8)
- **ClawHub Safety** — 341 malicious skills detected, scanning with mcp-scan
- **LLM Providers** — Anthropic, OpenAI, OpenRouter, Gemini, Ollama configuration
- **Cost Control** — Subscriptions, local models, model routing, spending limits
- **Backup** — Encrypted tar.gz with GPG-AES256 for critical paths
- **Monitoring** — Health checks, security audit, system diagnostics

## Usage

```
/openclaw-guide
```

OpenClaw setup, security, or troubleshooting questions.

## File Structure

```
openclaw-guide/
├── SKILL.md              # Main guide (overview + quick reference)
├── SECURITY.md           # CVE details, kill chains, hardening
├── SETUP.md              # Installation, integrations
└── TROUBLESHOOTING.md    # Common errors, recovery
```

## Requirements

- Node.js
- Docker (optional)
- Tailscale (recommended for remote access)
- LLM provider API keys

## License

Apache 2.0
