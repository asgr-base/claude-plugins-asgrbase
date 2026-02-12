# OpenClaw Troubleshooting

Common issues, diagnostic commands, and recovery procedures for OpenClaw.

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

**Last Updated**: 2026-02-11
