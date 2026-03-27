---
name: jp-eltax-guide
description: eLTAX（地方税ポータルシステム）の利用方法を検索・確認。給与支払報告書、法人住民税、電子納付の手続きを案内。Windows/macOS両環境に対応。eLTAX、エルタックス、地方税、PCdesk関連の質問時に使用。
version: 2.0.0
author: claude_code
createDate: 2026-01-11
updateDate: 2026-01-11
license: Apache-2.0
---

# eLTAX（地方税ポータルシステム）ガイド

## 重要: 最新情報の取得

**このスキルで回答する際は、必ずWebSearchで公式サイトから最新情報を取得してから回答すること。**

```
必須ワークフロー:
1. ユーザーの質問内容を特定
2. WebSearchで「eLTAX [手続き名] [キーワード]」を検索
3. 取得した最新情報に基づいて回答
4. 情報源のURLを明記
```

## 環境別の機能対応

| 機能 | Windows（DL版） | Windows（WEB版） | macOS（WEB版） |
|------|-----------------|------------------|----------------|
| 利用届出（新規） | × | ○ | ○ |
| 申告書作成・送信 | ○ | × | × |
| 給与支払報告書作成 | ○ | × | × |
| 法人住民税申告 | ○ | × | × |
| 電子署名付与 | ○ | ○ | ○ |
| 電子納付 | ○ | ○ | ○ |
| メッセージ照会 | ○ | ○ | ○ |

**推奨環境**:
- **申告書作成が必要**: Windows + Edge + PCdesk DL版
- **納付・届出のみ**: Windows/macOS + ブラウザ + PCdesk WEB版

## Windows環境（推奨）

### PCdesk DL版のセットアップ

```
手順:
1. https://www.eltax.lta.go.jp/ にアクセス
2. 「PCdesk（DL版）」→「ダウンロード」を選択
3. インストーラを実行
4. 利用者IDでログイン
```

### 動作環境

- **OS**: Windows 10/11（日本語版）
- **ブラウザ**: Microsoft Edge（最新版推奨）
- **電子証明書**:
  - 公的個人認証サービス（マイナンバーカード）
  - 商業登記電子証明書
  - その他対応証明書

### 主な手続き（Windows DL版）

**給与支払報告書の作成・送信**:
```
手順:
1. PCdesk DL版を起動
2. 「申告書作成」→「給与支払報告書」を選択
3. 従業員情報を入力（または給与ソフトからインポート）
4. 電子署名を付与
5. 送信
```

**法人住民税・事業税の申告**:
```
手順:
1. PCdesk DL版を起動
2. 「申告書作成」→該当税目を選択
3. 申告データを作成
4. 電子署名を付与
5. 送信
```

### Edgeの設定

```
手順:
1. Edge 設定 → Cookie とサイトのアクセス許可
2. ポップアップとリダイレクト → 許可に「eltax.lta.go.jp」を追加
3. JavaScript → 有効を確認
```

## macOS環境

### 制約事項

**PCdesk DL版はWindows専用です。macOSでは使用できません。**

| 機能 | macOS対応 | 備考 |
|------|-----------|------|
| PCdesk WEB版 | ○ | Safari対応 |
| PCdesk DL版 | × | Windows専用 |
| 申告書作成 | × | DL版が必要 |
| 電子納付 | ○ | WEB版で実行 |

### macOSでの代替手段

1. **税務ソフト連携**: マネーフォワード クラウド給与等からeLTAX連携
2. **税理士に依頼**: 代理申告
3. **Windows仮想環境**: Parallels Desktop、VMware Fusion等

### Safari設定

```
手順:
1. Safari メニュー → 設定
2. 「Webサイト」タブ → 「ポップアップウィンドウ」
3. portal.eltax.lta.go.jp を「許可」に設定
```

**詳細**: [REFERENCE.md](REFERENCE.md) の「macOS/Safari環境での設定」

## 共通手続き

### 利用届出（新規）- WEB版

```
手順:
1. https://www.eltax.lta.go.jp/ にアクセス
2. 「PCdesk（WEB版）」をクリック
3. 「利用届出（新規）」を選択
4. 必要事項を入力
5. 利用者IDと仮暗証番号を取得
```

### 電子納付 - WEB版/DL版共通

- インターネットバンキング（ペイジー）
- クレジットカード（手数料あり）
- ダイレクト納付

## よくある質問

### Q: WindowsとmacOSどちらを使うべき？

A: 申告書作成が必要な場合はWindows + PCdesk DL版を推奨。納付や届出のみならどちらでも可。

### Q: 利用時間は？

A: 月〜金曜日 8:30〜24:00（土日祝日・年末年始を除く）

### Q: 電子証明書は必要？

A: 原則必要。Windowsでは複数種類対応、macOSでは公的個人認証サービスのみ対応。

## 詳細リファレンス

より詳細な情報は [REFERENCE.md](REFERENCE.md) を参照してください。

## 公式リソース

- [eLTAX公式サイト](https://www.eltax.lta.go.jp/)
- [マニュアルコーナー](https://www.eltax.lta.go.jp/support/manual/)
- [よくあるご質問](https://eltax.custhelp.com/)
- [PCdesk（DL版）ダウンロード](https://www.eltax.lta.go.jp/eltax/junbi/pcdesk/)
- [パソコン環境の準備](https://www.eltax.lta.go.jp/eltax/junbi/pckankyou/)
