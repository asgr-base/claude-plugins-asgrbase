---
name: openclaw-guide
description: Guide for OpenClaw self-hosted AI agent setup, security hardening, and operation. Covers installation, configuration, vulnerability mitigation (CVE-2026-25253/25157/24763), ClawHub skill safety, backup strategies, device pairing (1008 error), Mac mini server setup, and monitoring. Use when user asks about OpenClaw, Clawdbot, Moltbot setup, security, hardening, troubleshooting, 1008 pairing required error, or device approval.
version: 1.0.0
author: asgr-base
createDate: 2026-02-13
updateDate: 2026-02-21
license: Apache-2.0
---

# OpenClaw Guide

OpenClaw is a self-hosted autonomous AI agent (MIT license) that bridges LLM providers with 50+ integrations (messaging, email, browser, cron). This skill provides **security-first guidance** for safe deployment and operation.

## Quick Reference

| Problem | Solution |
|---------|----------|
| `1008: pairing required` | `openclaw devices list` → `openclaw devices approve <ID>` |
| Exposed to internet | Set `gateway.bind: "loopback"`, use Tailscale |
| Unknown CVEs unpatched | Update to v2026.2.1+, run `openclaw security audit --deep` |
| Malicious ClawHub skill | Block external skills, use `mcp-scan` before install |
| Credential leakage | Set file perms 600/700, enable `logging.redactSensitive` |
| API cost spike | Set provider-side spending limits, use model routing |
| Docker escape risk | Use gVisor, `--cap-drop ALL`, non-root, read-only rootfs |
| DM from unknown sender | Set `dmPolicy: "pairing"` or `"allowlist"` |
| Prompt injection via email | Use read-only "reader" agent for untrusted content |
| Gateway won't start | Kill zombie process: `lsof -ti :18789 \| xargs kill -9` |
| `openclaw: command not found` | Use full path: `/opt/homebrew/bin/node .../openclaw/dist/index.js` |
| Check health | `curl -s http://localhost:18789/health` |
| View logs | `tail -n 50 /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log` |

## Architecture Overview

```
Messaging Channels (WhatsApp, Telegram, Slack, Discord, Gmail, etc.)
         |
         v
   +-----------+
   |  Gateway   |  ws://127.0.0.1:18789 (WebSocket + HTTP)
   +-----------+
     |    |    |
     v    v    v
  Pi Agent  CLI  Control UI  Mobile Apps
```

- **Gateway**: Central control plane (Node.js). WebSocket + HTTP on port 18789
- **Pi Agent**: LLM orchestration layer (plan -> act -> verify -> repeat)
- **Channel Adapters**: 15+ platform adapters (WhatsApp, Telegram, Slack, Discord, Signal, iMessage, Gmail, etc.)
- **Storage**: `~/.openclaw/` (config, sessions, credentials, cron jobs, skills)

## Security-First Setup (MUST Follow)

**IMPORTANT**: OpenClaw has had **3 high-severity CVEs** (all with public exploit code), **135,000+ exposed instances**, and **341 malicious ClawHub skills**. Security hardening is NOT optional.

### Step 1: Install (Latest Version Only)

```bash
# Always install the latest patched version
curl -fsSL https://openclaw.ai/install.sh | bash

# Verify version is >= 2026.2.1
openclaw --version

# Install as daemon
openclaw onboard --install-daemon
```

### Step 2: Generate Strong Authentication Token

```bash
# Generate cryptographically strong token
export OPENCLAW_GATEWAY_TOKEN=$(openssl rand -hex 32)
```

### Step 3: Apply Secure Baseline Configuration

```json5
// ~/.openclaw/openclaw.json
{
  "gateway": {
    "bind": "loopback",       // NEVER use "lan" or "custom" without VPN
    "port": 18789,
    "auth": {
      "mode": "token",
      "token": "<generated-token>"
    }
  },
  "agents": {
    "defaults": {
      "dm": { "policy": "pairing" },    // Require verification code
      "bash": { "mode": "allowlist" },   // Require approval for commands
      "sandbox": {
        "mode": "all",                   // Sandbox ALL sessions
        "scope": "session",              // Fresh container per session
        "workspaceAccess": "none",       // No workspace mount
        "docker": { "network": "none" }  // No network in sandbox
      }
    }
  },
  "logging": {
    "redactSensitive": "tools"  // Redact tool output in logs
  },
  "discovery": {
    "mdns": { "mode": "minimal" }  // Minimize broadcast info
  }
}
```

### Step 4: Set File Permissions

```bash
chmod 700 ~/.openclaw/
chmod 600 ~/.openclaw/openclaw.json
chmod 600 ~/.openclaw/.env
find ~/.openclaw/credentials/ -type f -exec chmod 600 {} \;
```

### Step 5: Run Security Audit

```bash
openclaw security audit --deep --fix
```

### Step 6: Remote Access via Tailscale (Recommended)

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Expose OpenClaw only within tailnet
tailscale serve https / http://127.0.0.1:18789

# NEVER use Tailscale Funnel for OpenClaw (public exposure)
```

## Web UI Access

```
# Local (same machine)
http://localhost:18789/?token=<your-token>

# Via Tailscale Serve (remote)
https://<hostname>.tailnet-name.ts.net/?token=<your-token>
```

The first access from any browser requires Device Pairing (see below).

## Device Pairing (1008 Error)

When accessing from a new browser/device, you see: `disconnected (1008): pairing required`

**How it works**: Each browser stores a unique device ID in localStorage. Unverified devices are rejected by the Gateway.

- Chrome and Chrome Canary use separate localStorage → treated as different devices
- Clearing localStorage generates a new device ID → re-pairing required
- Pairing requests **expire after 5 minutes**

**Approval steps**:

```bash
# 1. List pending devices
openclaw devices list

# 2. Approve by Request ID
openclaw devices approve <Request-ID>
# → "Approved" means success

# 3. Reload browser → connected
```

If running on a remote server (e.g., Mac mini), SSH in first, then run the commands.
If `openclaw` is not in PATH, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

**Alternative (localStorage copy)**:

```javascript
// Run in DevTools Console of approved browser
JSON.stringify({
  'openclaw-device-id': localStorage.getItem('openclaw-device-id'),
  'openclaw-device-keys': localStorage.getItem('openclaw-device-keys')
})
// → Set same keys in new browser via localStorage.setItem
```

## Gateway Management (macOS)

```bash
# Status check
openclaw gateway status

# Start / Stop
openclaw gateway start
openclaw gateway stop

# macOS: LaunchAgent (recommended - enables auto-start)
PLIST=$(ls ~/Library/LaunchAgents/ | grep openclaw | head -1)
launchctl load   ~/Library/LaunchAgents/$PLIST
launchctl unload ~/Library/LaunchAgents/$PLIST

# Config repair (removes invalid keys)
openclaw doctor --fix
```

## Log Investigation

```bash
# Latest logs
tail -n 100 /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log

# Errors only
grep -i 'error\|warn\|fail' /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log | tail -30

# Real-time monitoring
tail -f /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log
```

**Harmless error**: `Failed to discover Ollama models: TypeError: fetch failed` — appears when Ollama is not running; does not affect Gateway operation.

## Known CVEs (All Patched in v2026.1.29+)

| CVE | CVSS | Type | Impact |
|-----|------|------|--------|
| CVE-2026-25253 | 8.8 | WebSocket Hijacking -> RCE | Full host compromise via 1-click |
| CVE-2026-25157 | 7.8 | macOS SSH Command Injection | Arbitrary command execution |
| CVE-2026-24763 | 8.8 | Docker PATH Manipulation -> Escape | Container escape to host |

**All three have public exploit code.** Update immediately if running < v2026.1.29.

See [SECURITY.md](SECURITY.md) for detailed kill chains, mitigation steps, and hardening configuration.

## ClawHub Skill Safety

**CRITICAL**: 341 malicious skills detected on ClawHub (7.1% of scanned skills).

**Rules**:
1. **NEVER install skills from unknown publishers**
2. Block known malicious publishers: `zaycv`, `Aslaep123`, `pepe276`, `moonshine-100rze`, `hightower6eu`
3. Always scan before install: `npx mcp-scan <skill-path>`
4. Review skill source code for: `curl`, `wget`, `eval`, Base64-encoded strings, external URLs
5. Prefer self-authored skills only

## LLM Provider Configuration

### Provider Priority (Default)

```
Anthropic > OpenAI > OpenRouter > Gemini > ... > Ollama (local)
```

### Recommended: Anthropic Claude

```bash
# In ~/.openclaw/.env
ANTHROPIC_API_KEY=sk-ant-...
```

> Claude Opus 4.6 is recommended for best prompt injection resistance and long-context handling.

### Cost Control

| Strategy | Savings |
|----------|---------|
| Use existing subscription (Claude Pro/Max) | Zero additional API cost |
| Local models via Ollama | Zero API cost |
| Smart model routing (cheap for simple, expensive for complex) | 50-70% reduction |
| Set provider-side monthly spending limit | Prevents runaway costs |

## Cron Jobs (Autonomous Operation)

```json5
{
  "cron": {
    "enabled": true,
    "maxConcurrentRuns": 1,
    "jobs": [
      {
        "id": "daily-briefing",
        "cron": "0 7 * * *",         // Every day at 7:00 AM
        "timezone": "Asia/Tokyo",
        "prompt": "Summarize today's schedule, unread emails, and weather",
        "deliver": "telegram"          // Deliver to Telegram
      }
    ]
  }
}
```

**Schedule Types**: one-shot (`at`), fixed interval (`every`), cron expression (`cron`)
**Delivery**: WhatsApp, Telegram, Discord, Slack, Signal, iMessage, Mattermost

## Gmail Integration

1. Create Google Cloud project and enable Gmail API + Pub/Sub API
2. Create OAuth client ID
3. Run `openclaw gmail auth` for OAuth flow
4. Configure Pub/Sub for real-time email monitoring

> **Security Warning**: Use a dedicated email account, NOT your primary personal account.

## Backup Strategy

### Critical Paths to Back Up

| Path | Content | Priority |
|------|---------|----------|
| `~/.openclaw/openclaw.json` | Main config | Critical |
| `~/.openclaw/.env` | API keys/tokens | Critical |
| `~/.openclaw/credentials/` | Channel auth | Critical |
| `~/.openclaw/agents/` | Sessions/memory | High |
| `~/.openclaw/cron/` | Job config/history | High |
| `~/.openclaw/workspace/` | Skills, AGENTS.md | High |

### Automated Backup (Encrypted)

```bash
# Create encrypted backup
tar czf - ~/.openclaw/ | \
  gpg --symmetric --cipher-algo AES256 -o openclaw_backup_$(date +%Y%m%d).tar.gz.gpg

# Restore
gpg --decrypt openclaw_backup_YYYYMMDD.tar.gz.gpg | tar xzf -
```

**IMPORTANT**: Always encrypt backups (they contain API keys and credentials).

## Monitoring

```bash
# Service status
systemctl --user status openclaw

# Health check
curl -sf http://127.0.0.1:18789/health

# Diagnostics
openclaw doctor

# Security audit (run regularly)
openclaw security audit --deep
```

## Detailed References

| File | Content |
|------|---------|
| [SECURITY.md](SECURITY.md) | CVE details, kill chains, hardening config, ClawHub analysis |
| [SETUP.md](SETUP.md) | Installation, server requirements, Docker, integrations |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common errors, diagnostics, recovery procedures |
| [CONFIG.md](CONFIG.md) | Configuration file reference, Tailscale Serve, LaunchAgent |
| [MACMINI-SETUP.md](MACMINI-SETUP.md) | Mac mini server setup, sleep management, remote access |

## External Resources

- [OpenClaw Documentation](https://docs.openclaw.ai/)
- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [OpenClaw Security Docs](https://docs.openclaw.ai/gateway/security)
- [OpenClaw Sandboxing Docs](https://docs.openclaw.ai/gateway/sandboxing)
- [freeCodeCamp Tutorial](https://www.freecodecamp.org/news/openclaw-full-tutorial-for-beginners/)

---

**Version**: 1.1.0
**Last Updated**: 2026-02-18
