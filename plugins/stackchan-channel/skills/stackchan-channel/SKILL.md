---
name: stackchan-channel
description: StackChan voice chatbot agent channel — bridges Mac mini Claude Code Agent and stackchan-server via local HTTP + MCP notifications/claude/channel. Use this when configuring StackChan to run Claude Code Agent as the voice response source. The plugin itself is an MCP server with HTTP bridge; not directly invoked by users.
version: 0.1.0
author: asgr-base
createDate: 2026-05-05
updateDate: 2026-05-05
license: Apache-2.0
disable-model-invocation: true
---

# stackchan-channel

This plugin's main purpose is the MCP server (see `server.ts` at the plugin root). It is **not a user-invokable skill** — it runs in the background as a Claude Code channel server.

## Installation

```bash
claude plugin marketplace update asgr-base
claude plugin install stackchan-channel@asgr-base
```

## Setup

```bash
cd ~/.claude/plugins/cache/asgr-base/stackchan-channel/0.1.0/
bun install
```

Then register as MCP server (user scope):

```bash
claude mcp add --scope user stackchan-channel \
  -- bun run --cwd ~/.claude/plugins/cache/asgr-base/stackchan-channel/0.1.0/ \
     --shell=bun --silent start
```

## Architecture

```
StackChan 実機
   ↕ Opus over WebSocket
stackchan-server (audio handler)
   ↕ HTTP localhost:8001
[ this plugin: MCP + HTTP bridge ]
   ↕ MCP stdio + notifications/claude/channel
Claude Code Agent (stackchan-companion)
```

Agent uses the plugin's `reply` tool to send Japanese text back to stackchan-server, which synthesizes via VOICEVOX and plays through the StackChan speaker.

## API & Details

See [README.md](../../README.md) at the plugin root for full HTTP API spec, MCP tool spec, and environment variables.

## Related Components

- [asgr-base/stackchan-server](https://github.com/asgr-base/stackchan-server): Audio handler, STT (mlx-whisper), TTS (VOICEVOX), `AgentChannelLLM` HTTP client
- `~/.claude/agents/stackchan-companion.md`: StackChan persona definition for the Claude Code Agent
- `~/Library/LaunchAgents/com.endalnova.stackchan-companion.plist`: launchd auto-start
