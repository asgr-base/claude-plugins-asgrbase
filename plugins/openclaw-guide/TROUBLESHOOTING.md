# OpenClaw Troubleshooting

Common issues, diagnostic commands, and recovery procedures for OpenClaw.

## Quick Symptom Guide

| Symptom | Likely Cause | Jump To |
|---------|-------------|---------|
| `1008: pairing required` | Browser not approved | [#device-pairing-1008-error](#device-pairing-1008-error) |
| `1008: gateway token missing` | Missing `?token=` in URL | [#gateway-token-error](#gateway-token-error) |
| Gateway won't start | Zombie process / lock conflict | [#gateway-wont-start-macos](#gateway-wont-start-macos) |
| `gateway already running` | Existing process still running | [#gateway-wont-start-macos](#gateway-wont-start-macos) |
| `openclaw: command not found` | Homebrew PATH not set in SSH session | [#openclaw-command-not-found](#openclaw-command-not-found) |
| Invalid config key error | Old config keys remaining | [#config-repair](#config-repair) |
| Repeated Ollama fetch errors | Ollama not running (harmless) | [#ollama-fetch-errors](#ollama-fetch-errors) |

---

## Device Pairing (1008 Error)

### Symptom

```
disconnected (1008): pairing required
```

Displayed when opening OpenClaw Web UI in a browser.

### Cause

OpenClaw Gateway requires Device Pairing per browser. Each browser stores a unique device ID in localStorage, and unapproved devices are rejected.

- Chrome and Chrome Canary use separate localStorage → treated as separate devices
- After clearing localStorage → re-pairing required

### Solution

```bash
# 1. List pending pairing requests
openclaw devices list

# 2. Approve by Request ID
openclaw devices approve <Request-ID>
# → "Approved" = success

# 3. Reload browser → connected
```

**Notes**:
- Pairing requests **expire after 5 minutes** — approve immediately after browser access
- If `openclaw` is not in PATH, see [#openclaw-command-not-found](#openclaw-command-not-found)

---

## Gateway Token Error

### Symptom

```
1008: gateway token missing
```

or in logs: `unauthorized: gateway token missing`

### Cause

URL is missing `?token=...` parameter, or token is incorrect.

### Solution

```bash
# Correct URL format
http://localhost:18789/?token=<your-token>
https://<hostname>.tailnet-name.ts.net/?token=<your-token>

# Check token in config
cat ~/.openclaw/openclaw.json | jq .gateway.auth
```

---

## Gateway Won't Start (macOS)

### Symptom

LaunchAgent is loaded but Gateway is not responding.

### Solution A: Zombie process occupying the port (most common)

```bash
OPENCLAW_PORT=18789

# Identify occupying process
lsof -ti :$OPENCLAW_PORT

# Force kill
lsof -ti :$OPENCLAW_PORT | xargs kill -9

# Remove lock files
rm -f ~/.openclaw/*.lock

# Repair config (just in case)
openclaw doctor --fix

# Reload LaunchAgent
PLIST=$(ls ~/Library/LaunchAgents/ | grep openclaw | head -1)
launchctl unload ~/Library/LaunchAgents/$PLIST
sleep 2
launchctl load ~/Library/LaunchAgents/$PLIST
sleep 3

# Verify
ps aux | grep openclaw | grep -v grep
curl -s http://localhost:$OPENCLAW_PORT/health
```

### Solution B: Invalid config keys

```bash
openclaw doctor --fix
# Removes invalid keys: cache, heartbeat, rate_limits, budgets, _meta
```

### macOS LaunchAgent Restart

```bash
# Normal stop → restart
openclaw gateway stop

PLIST=$(ls ~/Library/LaunchAgents/ | grep openclaw | head -1)
launchctl unload ~/Library/LaunchAgents/$PLIST
sleep 2
launchctl load ~/Library/LaunchAgents/$PLIST

# Verify (wait 3 seconds)
sleep 3
ps aux | grep openclaw | grep -v grep
curl -s http://localhost:18789/health && echo "OK"
```

---

## openclaw Command Not Found

### Symptom

```
openclaw: command not found
```

Occurs in SSH sessions or certain shell environments.

### Cause

Installed via Homebrew but PATH not set in SSH session.

**Solution A: Use full path**

```bash
/opt/homebrew/bin/node /opt/homebrew/lib/node_modules/openclaw/dist/index.js devices list
```

**Solution B: Source shell config in SSH**

```bash
ssh <user>@<host> 'source ~/.zshrc && openclaw devices list'
```

**Solution C: Use interactive session**

```bash
ssh -t <user>@<host>
# Then run interactively on server
openclaw devices list
```

---

## Config Repair

Old versions of OpenClaw may leave invalid keys in config.

```bash
# Check current config
cat ~/.openclaw/openclaw.json | jq .

# Repair (auto-removes invalid keys)
openclaw doctor --fix

# Verify after repair
cat ~/.openclaw/openclaw.json | jq .
```

---

## Ollama Fetch Errors

### Symptom (repeated in logs)

```
Failed to discover Ollama models: TypeError: fetch failed
```

### Cause and Response

Ollama service is not running. **This warning does NOT affect Gateway operation** (safe to ignore).

To use Ollama:
```bash
ollama serve
# Or configure LaunchAgent for auto-start
```

---

## Health Check Script

```bash
echo "=== OpenClaw Process ==="
ps aux | grep openclaw | grep -v grep || echo "Not running"

echo ""
echo "=== Port 18789 ==="
lsof -i :18789 | grep LISTEN || echo "Not listening"

echo ""
echo "=== Health Endpoint ==="
curl -sf http://localhost:18789/health && echo "OK" || echo "FAILED"

echo ""
echo "=== Recent Error Logs ==="
grep -i "error\|panic\|fatal" /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log 2>/dev/null \
  | grep -v "Ollama" | tail -10

echo ""
echo "=== LaunchAgent Status ==="
launchctl list | grep openclaw || echo "Not loaded"
```

---

## Diagnostic Commands

```bash
# Built-in diagnostics
openclaw doctor

# Security audit
openclaw security audit --deep

# Auto-fix known security issues
openclaw security audit --fix

# Check Gateway status
systemctl --user status openclaw

# Gateway health check
curl -sf http://127.0.0.1:18789/health

# Check version
openclaw --version
```

## Common Issues

### Gateway Won't Start

| Symptom | Cause | Solution |
|---------|-------|---------|
| `EADDRINUSE: port 18789` | Port already in use | Kill existing process: `lsof -i :18789` then stop it |
| `Invalid JSON in openclaw.json` | Config syntax error | Validate: `node -e "require('~/.openclaw/openclaw.json')"` |
| `Unknown key in config` | Deprecated/invalid field | Check docs for valid keys, remove unknown fields |
| `EACCES: permission denied` | File permission issue | `chmod 700 ~/.openclaw/ && chmod 600 ~/.openclaw/openclaw.json` |
| `Node.js version mismatch` | Node.js < 22 | Install Node.js 22+: `nvm install 22` |

### Connection Issues

| Symptom | Cause | Solution |
|---------|-------|---------|
| Can't access Control UI | Firewall/binding issue | Check `gateway.bind` is `"loopback"`, access via `http://127.0.0.1:18789` |
| WebSocket disconnects | Token mismatch | Verify `OPENCLAW_GATEWAY_TOKEN` matches config |
| Tailscale can't connect | Service not running | `tailscale status` to verify, `sudo tailscale up` to reconnect |
| Remote CLI fails | Token/TLS mismatch | Check `gateway.remote.token` and `tlsFingerprint` |

### LLM Provider Issues

| Symptom | Cause | Solution |
|---------|-------|---------|
| `401 Unauthorized` | Invalid API key | Verify key in `~/.openclaw/.env`, check expiration |
| `429 Too Many Requests` | Rate limit hit | Wait for cooldown; note: built-in backoff has known issues (GitHub #5159) |
| All models unavailable | Provider-wide rate limit | Rate limit on one model marks all same-provider models unavailable |
| High latency | Model overloaded | Switch to alternative provider or local model |
| Unexpected high API cost | Token-intensive loop | Set provider-side spending limits; reduce `session.historyLimit` |

### Channel Issues

| Symptom | Cause | Solution |
|---------|-------|---------|
| Telegram bot not responding | Token invalid/expired | Regenerate token via @BotFather |
| Discord bot offline | Missing intents | Enable Message Content Intent in Developer Portal |
| WhatsApp disconnected | Session expired | Re-scan QR code, check `~/.openclaw/credentials/whatsapp/` |
| Gmail not receiving | Pub/Sub watch expired | Re-run `openclaw gmail watch` (watches expire after 7 days) |
| Slack messages not received | Socket mode issue | Verify `SLACK_APP_TOKEN` (xapp-...) is correct |

### Cron Job Issues

| Symptom | Cause | Solution |
|---------|-------|---------|
| Job not running | Cron disabled | Check `cron.enabled: true` in config |
| Job runs at wrong time | Timezone issue | Set `timezone` in job config (e.g., `"Asia/Tokyo"`) |
| Job stuck | Max concurrent reached | Check `cron.maxConcurrentRuns`; review `~/.openclaw/cron/runs/` |
| Exponential backoff | Consecutive failures | Check job logs in `~/.openclaw/cron/runs/<jobId>.jsonl` |

### Docker / Sandbox Issues

| Symptom | Cause | Solution |
|---------|-------|---------|
| Container won't start | Image not found | Pull latest: `docker pull openclaw:latest` |
| Permission denied in container | Non-root user restriction | Check volume ownership matches container user (1000:1000) |
| Network unreachable in sandbox | `docker.network: "none"` | Expected behavior for security; change only if network needed |
| Sandbox escape concern | Outdated version | Update to >= v2026.1.29 (fixes CVE-2026-24763) |

## Recovery Procedures

### Config Corruption Recovery

```bash
# 1. Backup current (possibly corrupt) config
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak

# 2. Validate JSON
node -e "JSON.parse(require('fs').readFileSync('$HOME/.openclaw/openclaw.json', 'utf8'))"

# 3. If invalid, create fresh config
openclaw config reset

# 4. Re-apply security settings (see SKILL.md Step 3)
```

### Session History Memory Issues

```bash
# If OpenClaw uses too much memory, reduce session history
# In openclaw.json:
# "session": { "historyLimit": 100 }

# Clear old sessions
rm ~/.openclaw/agents/*/sessions/old-*.jsonl
```

### Credential Recovery After Compromise

1. **Stop OpenClaw immediately**:
   ```bash
   systemctl --user stop openclaw
   ```
2. **Rotate ALL credentials** (see [SECURITY.md](SECURITY.md) Incident Response section)
3. **Review logs** for unauthorized activity
4. **Reinstall from backup** if necessary

### Backup Restoration

```bash
# 1. Decrypt backup
gpg --decrypt openclaw_backup_YYYYMMDD.tar.gz.gpg > backup.tar.gz

# 2. Extract
tar xzf backup.tar.gz -C /tmp/openclaw-restore/

# 3. Stop OpenClaw
systemctl --user stop openclaw

# 4. Restore files
cp -r /tmp/openclaw-restore/.openclaw/ ~/

# 5. Fix permissions
chmod 700 ~/.openclaw/
chmod 600 ~/.openclaw/openclaw.json
chmod 600 ~/.openclaw/.env
find ~/.openclaw/credentials/ -type f -name "*.json" | xargs chmod 600

# 6. Restart
systemctl --user start openclaw
```

## Performance Tuning

### Reduce API Costs

| Setting | Effect |
|---------|--------|
| `session.historyLimit: 100` | Limit context window, reduce tokens per request |
| Use Ollama for simple tasks | Zero API cost for routine operations |
| Smart model routing | Route simple tasks to cheaper models |
| Provider spending limits | Hard cap on monthly API spend |

### Reduce Memory Usage

| Action | Effect |
|--------|--------|
| Lower `session.historyLimit` | Less memory per session |
| Use `sandbox.scope: "session"` | Containers cleaned up per session |
| Prune old session files | Free disk space |
| Limit concurrent cron runs | Reduce parallel resource usage |

## Log Locations

| Log | Path |
|-----|------|
| Gateway log | `/tmp/openclaw/openclaw-YYYY-MM-DD.log` |
| Session transcripts | `~/.openclaw/agents/<id>/sessions/*.jsonl` |
| Cron run history | `~/.openclaw/cron/runs/<jobId>.jsonl` |
| systemd journal | `journalctl --user -u openclaw` |
| macOS LaunchAgent | `~/Library/Logs/openclaw.log` |

## Getting Help

- [Official Documentation](https://docs.openclaw.ai/)
- [Official Troubleshooting](https://docs.openclaw.ai/gateway/troubleshooting)
- [GitHub Issues](https://github.com/openclaw/openclaw/issues)
- [Discord Community](https://discord.gg/openclaw)
- [Error Troubleshooting Center](https://www.aifreeapi.com/en/posts/openclaw-error-troubleshooting-center)

---

**Last Updated**: 2026-02-18
