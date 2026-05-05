#!/usr/bin/env bun
/**
 * StackChan local channel for Claude Code.
 *
 * Self-contained MCP server + HTTP bridge between stackchan-server (audio
 * handler) and Claude Code Agent on Mac mini.
 *
 * Architecture:
 *
 *   stackchan-server  --HTTP-->  this plugin (port 8001)
 *                                    |
 *                                    v
 *                        notifications/claude/channel (MCP)
 *                                    |
 *                                    v
 *                        Claude Code Agent (stackchan-companion)
 *                                    |
 *                                    | tool: reply(chat_id, text)
 *                                    v
 *                              this plugin
 *                                    |
 *                                    v
 *                        stackchan-server <--HTTP--  (long-poll response)
 *
 * The plugin is started by Claude Code as an MCP server (stdio transport)
 * via `--channels plugin:stackchan-channel`. It also listens on HTTP
 * localhost:8001 for stackchan-server input/output.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const HTTP_PORT = parseInt(process.env.STACKCHAN_CHANNEL_PORT ?? "8001", 10);

// Pending requests: stackchan-server から来た user message を保持
// agent の reply tool が呼ばれるまで待機する。
type PendingRequest = {
  message_id: string;
  chat_id: string;
  user_text: string;
  created_at: number;
  resolve: (text: string) => void;
  reject: (err: Error) => void;
};

const pending: Map<string, PendingRequest> = new Map();

function logErr(msg: string) {
  process.stderr.write(`stackchan-channel: ${msg}\n`);
}

// ============================================================
// MCP server
// ============================================================

const mcp = new Server(
  { name: "stackchan-channel", version: "0.1.0" },
  { capabilities: { tools: {} } },
);

mcp.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "reply",
      description:
        "Reply to the user via StackChan voice. The reply text will be synthesized by VOICEVOX and played from the StackChan speaker. Pass chat_id from the inbound message metadata.",
      inputSchema: {
        type: "object",
        properties: {
          chat_id: { type: "string" },
          text: {
            type: "string",
            description: "Reply text (Japanese, 1-2 short sentences).",
          },
        },
        required: ["chat_id", "text"],
      },
    },
  ],
}));

mcp.setRequestHandler(CallToolRequestSchema, async (req) => {
  const args = (req.params.arguments ?? {}) as Record<string, unknown>;
  if (req.params.name === "reply") {
    const chat_id = String(args.chat_id ?? "");
    const text = String(args.text ?? "");
    if (!chat_id || !text) {
      return {
        content: [
          { type: "text", text: "reply: chat_id and text are required" },
        ],
        isError: true,
      };
    }
    // chat_id == message_id を採用する（1:1 対応）
    const req_obj = pending.get(chat_id);
    if (req_obj) {
      pending.delete(chat_id);
      req_obj.resolve(text);
      return {
        content: [
          { type: "text", text: `reply delivered to ${chat_id}` },
        ],
      };
    } else {
      return {
        content: [
          {
            type: "text",
            text: `reply: no pending request for chat_id=${chat_id}`,
          },
        ],
        isError: true,
      };
    }
  }
  return {
    content: [
      { type: "text", text: `unknown tool: ${req.params.name}` },
    ],
    isError: true,
  };
});

await mcp.connect(new StdioServerTransport());
logErr("MCP server connected via stdio");

// ============================================================
// HTTP server (Bun built-in)
// ============================================================

const server = Bun.serve({
  port: HTTP_PORT,
  hostname: "127.0.0.1",
  async fetch(req) {
    const url = new URL(req.url);

    // POST /input - stackchan-server からの user message 受信
    if (url.pathname === "/input" && req.method === "POST") {
      let body: { text?: string; chat_id?: string; message_id?: string };
      try {
        body = await req.json();
      } catch {
        return new Response("invalid JSON", { status: 400 });
      }
      const message_id = body.message_id ?? crypto.randomUUID();
      const chat_id = body.chat_id ?? "stackchan";
      const text = body.text ?? "";
      if (!text) {
        return new Response("text required", { status: 400 });
      }

      // pending に登録 → agent からの reply tool で resolve される
      const responsePromise = new Promise<string>((resolve, reject) => {
        pending.set(message_id, {
          message_id,
          chat_id,
          user_text: text,
          created_at: Date.now(),
          resolve,
          reject,
        });
        // 60s タイムアウト
        setTimeout(() => {
          if (pending.has(message_id)) {
            pending.delete(message_id);
            reject(new Error("timeout"));
          }
        }, 60_000);
      });

      // agent に push（chat_id == message_id にして reply で逆参照可能に）
      try {
        await mcp.notification({
          method: "notifications/claude/channel",
          params: {
            content: text,
            meta: {
              chat_id: message_id,
              message_id,
              user: chat_id,
              ts: new Date().toISOString(),
            },
          },
        });
      } catch (err) {
        pending.delete(message_id);
        return new Response(`mcp notify failed: ${err}`, { status: 500 });
      }

      // long poll: 応答を待つ
      try {
        const reply = await responsePromise;
        return Response.json({ message_id, text: reply });
      } catch (err) {
        return new Response((err as Error).message, { status: 504 });
      }
    }

    // GET /health - ヘルスチェック
    if (url.pathname === "/health") {
      return Response.json({
        status: "ok",
        pending: pending.size,
      });
    }

    return new Response("not found", { status: 404 });
  },
});

logErr(`HTTP server listening on http://127.0.0.1:${server.port}`);

// クリーンアップ用 (MCP transport が close したら HTTP も止める)
process.on("SIGTERM", () => {
  logErr("SIGTERM received, shutting down");
  server.stop();
  process.exit(0);
});
process.on("SIGINT", () => {
  logErr("SIGINT received, shutting down");
  server.stop();
  process.exit(0);
});
