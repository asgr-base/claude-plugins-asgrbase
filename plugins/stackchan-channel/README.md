# stackchan-channel

StackChan ([M5Stack 公式 AI デスクトップロボット](https://docs.m5stack.com/ja/StackChan)) と Claude Code Agent をローカル HTTP で橋渡しする channel plugin。

家庭内チャットボット用途で、ユーザーの音声発話 (STT 結果) を Claude Code Agent (`stackchan-companion`) に渡し、Agent の応答を VOICEVOX で音声化してスピーカーから再生する設計の中核 plugin。

## アーキテクチャ

```
StackChan 実機
   ↕ Opus over WebSocket
stackchan-server (audio handler、Mac mini ローカル Python)
   ↕ HTTP localhost:8001
[ this plugin ]
   ↕ MCP stdio + notifications/claude/channel
Claude Code Agent (stackchan-companion)
```

ユーザーが話しかける → STT → この plugin の `POST /input` → MCP `notifications/claude/channel` で agent に push → agent が `reply` tool を呼ぶ → plugin が HTTP response として stackchan-server に返す → VOICEVOX → スピーカー。

## API

### `POST /input` （stackchan-server → plugin）

```json
{
  "text": "こんにちは",
  "chat_id": "stackchan",
  "message_id": "uuid-optional"
}
```

レスポンス（agent の reply まで long-poll、最大 60 秒）:

```json
{
  "message_id": "uuid",
  "text": "こんにちは！何してたの？"
}
```

### `GET /health`

```json
{ "status": "ok", "pending": 0 }
```

### MCP tool: `reply` （agent → plugin）

```json
{
  "chat_id": "<inbound message_id>",
  "text": "応答テキスト（短い日本語）"
}
```

## 環境変数

- `STACKCHAN_CHANNEL_PORT` (default `8001`): HTTP listener port

## 必要環境

- Bun >= 1.0
- macOS / Linux (Mac mini Apple Silicon arm64 で動作確認)

## セットアップ

```bash
cd plugins/stackchan-channel
bun install
```

## Agent 側の起動例

```bash
claude --agent stackchan-companion \
       --channels server:stackchan-channel \
       --resume <session-id>
```

加えて、`claude mcp add` で MCP server を登録しておく必要がある:

```bash
claude mcp add --scope user stackchan-channel \
  -- bun run --cwd <plugin-path> --shell=bun --silent start
```

## 関連プロジェクト

- [M5Stack/StackChan](https://github.com/m5stack/StackChan): 物理ハードウェア
- [asgr-base/stackchan-server](https://github.com/asgr-base/stackchan-server): Mac mini 上の audio handler / STT / TTS
