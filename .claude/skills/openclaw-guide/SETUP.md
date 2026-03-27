# OpenClaw Setup Guide

Complete installation, configuration, and integration guide for OpenClaw.

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Ubuntu 22.04+, macOS 13+, Windows 10+ | Ubuntu 24.04 LTS |
| **Node.js** | v22.12.0+ | v22 LTS (latest) |
| **RAM** | 2GB | 4-8GB |
| **CPU** | 2 cores | 4 cores |
| **Storage** | 10GB SSD | 40GB+ SSD |
| **Package Manager** | npm | pnpm 10.23.0 |
| **Docker** (optional) | Docker Engine 24+ | Docker Engine 26+ |

## Installation Methods

### Method 1: Official Installer (Recommended)

```bash
# macOS / Linux
curl -fsSL https://openclaw.ai/install.sh | bash

# Windows (PowerShell)
iwr -useb https://openclaw.ai/install.ps1 | iex

# Verify installation
openclaw --version
```

### Method 2: npm Global Install

```bash
npm install -g openclaw@latest
```

### Method 3: Docker Compose

```bash
git clone https://github.com/openclaw/openclaw.git
cd openclaw
cp .env.example .env
# Edit .env with your API keys
docker-compose up -d
```

### Method 4: Build from Source

```bash
git clone https://github.com/openclaw/openclaw.git
cd openclaw
pnpm install
pnpm build
```

### Post-Install: Daemon Setup

```bash
# Interactive onboarding + daemon installation
openclaw onboard --install-daemon

# Daemon locations:
# macOS:  ~/Library/LaunchAgents/
# Linux:  systemd user unit
# Windows: Scheduled task
```

## Environment Variables (.env)

### Required (at least one LLM provider)

```bash
# Authentication token (MUST generate unique token)
OPENCLAW_GATEWAY_TOKEN=<openssl rand -hex 32>

# LLM Provider (at least one required)
ANTHROPIC_API_KEY=sk-ant-...
# or: OPENAI_API_KEY=sk-...
# or: GEMINI_API_KEY=...
# or: OPENROUTER_API_KEY=...
```

### Optional: Channel Tokens

```bash
TELEGRAM_BOT_TOKEN=...
DISCORD_BOT_TOKEN=...
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
MATTERMOST_BOT_TOKEN=...
MATTERMOST_URL=https://...
```

### Optional: Tool APIs

```bash
BRAVE_API_KEY=...              # Web search
ELEVENLABS_API_KEY=...         # Voice TTS
DEEPGRAM_API_KEY=...           # Speech-to-text
FIRECRAWL_API_KEY=...          # Web crawling
```

### Config Precedence

```
process env > ./.env > ~/.openclaw/.env > openclaw.json
```

## Core Configuration (openclaw.json)

Located at `~/.openclaw/openclaw.json` (JSON5 format, Zod-validated).

### Minimal Secure Configuration

```json5
{
  "gateway": {
    "bind": "loopback",
    "port": 18789,
    "auth": {
      "mode": "token",
      "token": "<your-generated-token>"
    }
  },
  "agents": {
    "defaults": {
      "models": ["anthropic/claude-opus-4-6"],
      "dm": { "policy": "pairing" },
      "bash": { "mode": "allowlist" },
      "sandbox": {
        "mode": "all",
        "scope": "session",
        "workspaceAccess": "none",
        "docker": { "network": "none" }
      }
    }
  },
  "logging": {
    "redactSensitive": "tools"
  },
  "discovery": {
    "mdns": { "mode": "minimal" }
  }
}
```

## LLM Provider Setup

### Anthropic (Recommended)

```bash
# In ~/.openclaw/.env
ANTHROPIC_API_KEY=sk-ant-api03-...
```

Model syntax: `anthropic/claude-opus-4-6`, `anthropic/claude-sonnet-4-5`

### OpenAI

```bash
OPENAI_API_KEY=sk-...
```

### Local Models (Ollama)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3

# OpenClaw auto-detects Ollama at http://127.0.0.1:11434/v1
# No API key required (use "ollama" as placeholder)
```

### Cost-Saving Model Routing

Set `agents.defaults.models` as an allowlist. Use cheaper models for simple tasks:

```json5
{
  "agents": {
    "defaults": {
      "models": [
        "anthropic/claude-opus-4-6",     // Complex tasks
        "anthropic/claude-sonnet-4-5",    // Standard tasks
        "ollama/llama3"                   // Simple tasks (free)
      ]
    }
  }
}
```

## Channel Integration

### Telegram

1. Open [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow prompts
3. Copy the bot token
4. Add to `.env`: `TELEGRAM_BOT_TOKEN=<token>`

### Discord

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create New Application -> Bot
3. Enable Message Content Intent
4. Copy bot token
5. Add to `.env`: `DISCORD_BOT_TOKEN=<token>`
6. Invite bot to server with appropriate permissions

### Gmail (OAuth + Pub/Sub)

1. **Google Cloud Console**:
   - Create project
   - Enable Gmail API + Pub/Sub API
   - Create OAuth 2.0 Client ID (Desktop App type)

2. **Pub/Sub Setup**:
   - Create topic (e.g., `openclaw-gmail`)
   - Create subscription (pull type)
   - Grant `gmail-api-push@system.gserviceaccount.com` publish permission on topic

3. **OpenClaw Auth**:
   ```bash
   openclaw gmail auth
   # Follow the OAuth flow in browser
   ```

4. **Start Watching**:
   ```bash
   openclaw gmail watch
   ```

> **Security**: Use a **dedicated email account**, not your primary personal one.

### Slack

1. Create a Slack App at [api.slack.com/apps](https://api.slack.com/apps)
2. Enable Socket Mode -> get App-Level Token (`xapp-`)
3. Add Bot Token Scopes: `chat:write`, `app_mentions:read`, `im:history`
4. Install to workspace -> get Bot Token (`xoxb-`)
5. Add to `.env`:
   ```bash
   SLACK_BOT_TOKEN=xoxb-...
   SLACK_APP_TOKEN=xapp-...
   ```

## Cron Jobs (Autonomous Operation)

### Configuration

```json5
{
  "cron": {
    "enabled": true,
    "maxConcurrentRuns": 1,
    "jobs": [
      {
        "id": "morning-report",
        "cron": "0 7 * * *",
        "timezone": "Asia/Tokyo",
        "prompt": "Summarize today's calendar, unread emails, and weather forecast",
        "deliver": "telegram"
      },
      {
        "id": "email-check",
        "every": 1800000,            // Every 30 minutes
        "prompt": "Check for urgent unread emails and notify if found",
        "deliver": "telegram"
      },
      {
        "id": "one-time-task",
        "at": "2026-03-01T09:00:00+09:00",
        "prompt": "Remind about quarterly report deadline",
        "deliver": "telegram"
      }
    ]
  }
}
```

### Schedule Types

| Type | Syntax | Example |
|------|--------|---------|
| One-shot | `"at": "ISO8601"` | `"at": "2026-03-01T09:00:00+09:00"` |
| Interval | `"every": ms` | `"every": 3600000` (1 hour) |
| Cron | `"cron": "* * * * *"` | `"cron": "0 9 * * 1-5"` (weekdays 9am) |

### Storage

- Job config: `~/.openclaw/cron/jobs.json`
- Run history: `~/.openclaw/cron/runs/<jobId>.jsonl`
- One-shot jobs auto-delete after success
- Recurring jobs use exponential backoff on failure (30s -> 1m -> 5m -> 15m -> 60m)

## Remote Access

### Tailscale (Recommended)

```bash
# Install
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Serve within tailnet only
tailscale serve https / http://127.0.0.1:18789
```

### SSH Tunnel (Alternative)

```bash
# From local machine to remote server
ssh -L 18789:127.0.0.1:18789 user@server
# Then access at http://127.0.0.1:18789
```

**NEVER use**: Direct port exposure, Tailscale Funnel, or nginx without auth for OpenClaw.

## Workspace Files

| File | Purpose |
|------|---------|
| `~/.openclaw/workspace/AGENTS.md` | System prompt bootstrap |
| `~/.openclaw/workspace/SOUL.md` | Personality/identity definition |
| `~/.openclaw/workspace/TOOLS.md` | Tool usage guidance (optional) |
| `~/.openclaw/workspace/skills/` | Custom skill directories |

## Companion Apps

| Platform | Features |
|----------|----------|
| macOS | Menu bar app, Voice Wake, WebChat |
| iOS | Bridge pairing, Canvas, camera |
| Android | Bridge pairing, Canvas, camera, SMS channel |

## Version Management

```bash
# Check current version
openclaw --version

# Update to latest stable
openclaw update

# Switch release channel
openclaw update --channel stable   # Production
openclaw update --channel beta     # Pre-release
openclaw update --channel dev      # Bleeding edge
```

## Verification Checklist

After setup, verify:

- [ ] `openclaw --version` returns >= 2026.2.1
- [ ] `gateway.bind` is `"loopback"` in config
- [ ] Auth token is a 64-char hex string
- [ ] File permissions: `~/.openclaw/` is 700, config files are 600
- [ ] `openclaw doctor` passes all checks
- [ ] `openclaw security audit --deep` shows no critical issues
- [ ] Remote access is via Tailscale only (no direct port exposure)
- [ ] Firewall blocks port 18789 from external access

---

## External Resources

- [Official Getting Started](https://docs.openclaw.ai/start/getting-started)
- [Model Providers Documentation](https://docs.openclaw.ai/concepts/model-providers)
- [Cron Jobs Documentation](https://docs.openclaw.ai/automation/cron-jobs)
- [DigitalOcean Tutorial](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw)
- [freeCodeCamp Tutorial](https://www.freecodecamp.org/news/openclaw-full-tutorial-for-beginners/)
- [Contabo Self-Hosted Guide](https://contabo.com/blog/what-is-openclaw-self-hosted-ai-agent-guide/)

---

**Last Updated**: 2026-02-11
