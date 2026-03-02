# moneyforward-manager

MoneyForward クラウドひとり法人プランの管理・操作スキル。

## What It Does

MoneyForward クラウドひとり法人プランの利用ガイドと、Chrome DevTools MCP 経由での仕訳自動化操作を提供します。

- **ひとり法人プラン ガイド** — 料金・機能制限・各サービスの使い方
- **仕訳自動化** — Chrome DevTools MCP（evaluate_script）での仕訳追加・編集
- **月次バッチ** — Playwright CDP スクリプトによる定型仕訳の自動登録

## Key Topics

- **プラン概要** — 年額払い・月額払い料金、含まれる12サービス
- **機能制限** — 年間仕訳数、AI-OCR回数、部門数、消費税申告
- **クイックスタート** — 会計初期設定、給与計算、年末調整、社会保険
- **仕訳自動化** — Chrome DevTools MCP のヘルパー関数、ボタン構造、操作手順
- **月次バッチ** — `add-payment-journal.js` の使い方

## Usage

```
/moneyforward-manager
```

マネーフォワード、MFクラウド、仕訳入力・修正・確認関連の操作時に使用。

## File Structure

```
moneyforward-manager/
├── SKILL.md                    # メインガイド（ひとり法人 + 自動化概要）
├── REFERENCE.md                # サービス別詳細・サポートURL
├── references/
│   └── automation.md           # 仕訳自動化の詳細手順・コード
└── README.md                   # このファイル
```

## Requirements

- Claude Code CLI
- WebSearch tool（最新情報の取得に使用）
- Chrome DevTools MCP（仕訳自動化に使用）
- Chrome: `--remote-debugging-port=9222` で起動済み

## License

Apache 2.0
