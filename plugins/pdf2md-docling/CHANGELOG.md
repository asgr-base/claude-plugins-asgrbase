# Changelog - pdf2md-docling

All notable changes to the PDF to Markdown converter (Docling edition) are documented in this file.

## [3.20.0] - 2026-01-26

### Improved
- Doclingパス確認手順を「Step 0」として追加
- 環境依存のパス問題を解決（macOS Python、pipx、venv等に対応）
- Quick Referenceから固定パス表記を削除し、動的確認手順に変更

### Added
- 一般的なDoclingインストール場所のリストを追加
- パス確認用のワンライナーコマンドを追加

## [3.18.0] - 2026-01-14

### Fixed
- テーブル内の角括弧による列分割問題を修正
- ICAO Doc 9303 Part 11 Table K-2 (Elementary File EF.CVCA)で発見
- 原因: `[CARi ][CARi-1][0x00..00]`の角括弧がMarkdownの列区切りとして誤認識
- 対処: 7列→2列（Field/Value形式）に修正、角括弧をエスケープ `\[`
- 添字を `<sub>i</sub>` で表現

### Updated
- TROUBLESHOOTING.mdの「テーブル内の二重パイプによる列分割」セクションを拡張
  - タイトル変更: 「テーブル内の特殊記号による列分割」
  - 角括弧 `[]` のケースを追加（具体例2）
  - 検出コマンド追加: `grep -n "\[.*\]\["`

## [3.17.0] - 2026-01-14

### Fixed
- 暗号プロトコルWorked Exampleの変数代入レイアウトを改善
- ICAO Doc 9303 Part 11 Appendix D.3, D.4, Fを修正
  - D.3: eMRTD's contactless IC / Inspection systemセクション（Lines 2452-2523）
  - D.4: Secure Messagingセクションは比較的問題なし
  - F: Active Authentication全ステップ（Lines 2770-2903）
- 変数名と値が分離されていた問題を修正
  - 変数代入をコードブロック化: `KS_Enc = 'xxx'`
  - 複数行の16進数値をインデント付きで整形
  - ステップ番号を太字化: `**Step N.**`
- 添字記号を適切に表現: M₁, M₂, L_M1等
- 連結演算子を明示: `M = M₁ || M₂`

### Added
- TROUBLESHOOTING.mdに「暗号プロトコル例の変数代入が分離される」セクション追加
- 検出コマンド追加: `grep -n "^'[0-9A-F ]\\+'\$"`, `grep -n "= \$"`

## [3.16.0] - 2026-01-14

### Improved
- MRZ例のレイアウトを段落形式から表形式に改善
- ICAO Doc 9303 Part 11 Appendix Cの4つのMRZサンプルを修正
  - TD2 MRZ (document number exceeds 9 characters): Lines 2323-2337
  - TD2 MRZ (document number 9 characters): Lines 2342-2356
  - TD1 MRZ (document number exceeds 9 characters): Lines 2360-2375
  - TD1 MRZ (document number 9 characters): Lines 2380-2399
- MRZ文字列をコードブロックで囲み、複数行のインデントを統一
- Document number/Date of Birth/Date of Expiry等をMarkdownテーブル形式に整形
- 視認性向上により、元PDFのレイアウトとの整合性が改善

### Added
- TROUBLESHOOTING.mdに「MRZ例が段落形式で読みづらい」セクション追加
- 検出コマンド追加: `grep -n "TD[12] MRZ" filename.md`

## [3.15.0] - 2026-01-14

### Fixed
- MRZの`<`記号がHTMLエンティティ化（`&lt;`）される問題を修正
- ICAO Doc 9303 Part 11 Appendix Cの4つのMRZサンプルで発見
  - TD2 MRZ (document number exceeds 9 characters)
  - TD2 MRZ (document number 9 characters)
  - TD1 MRZ (document number 9 characters)
- MRZ内の`&lt;`を`<`に置換（フィラー文字の視認性向上）
- 暗号プロトコルの`<g>`、`<G>`記法は`&lt;g&gt;`のまま維持

### Added
- TROUBLESHOOTING.mdに「MRZ等の`<`記号がHTMLエンティティ化」セクション追加
- 検出コマンド追加: `grep -n "&lt;" file.md | grep -v "<g>" | grep -v "<G>"`

## [3.14.0] - 2026-01-14

### Fixed
- 数式デコード失敗(`<!-- formula-not-decoded -->`)への対処を完了
- ICAO Doc 9303 Part 11 Appendix B.1で4つの数式プレースホルダーを発見
- 各プレースホルダーに周辺文脈から推測した説明コメントを追加
  - Line 2180: 楕円曲線の定義式 `E: y² = x³ + ax + b (mod p)`
  - Line 2184: 入力tの制約条件 `0 < t < p`
  - Line 2193: アフィン座標とヤコビアン座標の関係式 `(x,y) = (X/Z², Y/Z³)`
  - Line 2228: Step 2の書き換え式（モジュラ逆数を用いた指数計算）

### Updated
- TROUBLESHOOTING.mdの「数式が変換できない」セクションを実際の修正例で更新
- コメント追加の指針を追加: 「が記載されていると推測」で推測であることを明示

## [3.13.0] - 2026-01-14

### Fixed
- テーブル内の二重パイプ(`||`)による列分割問題を修正
- ICAO Doc 9303 Part 11 Table 8 (Password encodings)で列数が7列に誤認識
- 原因: `SHA-1(Document Number || Date of Birth || Date of Expiry)`の`||`が列区切りとして認識
- 対処: 列数を2列に修正し、`||`を`&#124;&#124;`にエスケープ

### Added
- TROUBLESHOOTING.mdに「テーブル内の二重パイプによる列分割」セクション追加
- 検出コマンド追加: `grep -n "| .* |     |.*|     |"`

## [3.12.0] - 2026-01-14

### Fixed
- 構造化コンテンツの情報欠落問題を発見・修正
- ICAO Doc 9303 Part 11 Section 9.7.1で「Output octet string keydata」が欠落
- 原因: Doclingが構造的セクションを箇条書きとして誤認識、手動整形時に削除
- 対処: Actionsセクションに「1. Compute hash, 2. Output keydata」を明示

### Added
- TROUBLESHOOTING.mdに「構造化コンテンツの箇条書き化による情報欠落」セクション追加

## [3.11.0] - 2026-01-14

### Fixed
- セクション順序の誤認識問題を修正
- ICAO Doc 9303 Part 11 Section 9.6-9.7の構造を再構成
- 問題: 9.7.1が9.6より前に配置され、階層が崩壊
- 対処: 9.7.1を9.7の直後に移動し、正しい親子関係を復元

### Updated
- TROUBLESHOOTING.mdの「セクションの順序が入れ替わっている」に具体例を追加

## [3.10.0] - 2026-01-14

### Fixed
- APDUコマンド仕様テーブルの結合セル空欄化を大規模実施
- ICAO Doc 9303 Part 11で8個のテーブルを修正
  - 4.3.4.1 GET CHALLENGE
  - 4.3.4.2 EXTERNAL AUTHENTICATE
  - 6.2.4.2 MSE:Set AT + GENERAL AUTHENTICATE (2テーブル)
  - 7.1.5.1 MSE:Set DST
  - 7.1.5.2 PSO:Verify Certificate
  - 7.1.5.3 MSE:Set AT
  - 7.1.5.4 Get Challenge
  - 7.1.5.5 External Authenticate
- Status Bytes行の不正な構造を修正（混在していた複数ステータスを分離）
- 下付き文字の適切なマークアップ（E<sub>IFD</sub>, r<sub>IC</sub>等）

## [3.9.0] - 2026-01-14

### Added
- 番号付きリストの途中断絶問題に関する知見を追加
- TROUBLESHOOTING.mdに「番号付きリストの途中断絶」セクション追加
- 検出コマンド追加: `grep "<br>[0-9]<br>"`

### Fixed
- ICAO Doc 9303 Part 11 Section 7.1.2の番号付きリスト(1-5)を修正
- 原因: Doclingの認識エラー + 後処理Step 12の副作用を文書化

## [3.8.0] - 2026-01-14

### Added
- 結合セルの空欄表現ベストプラクティスを追加
- TROUBLESHOOTING.mdに「結合セルの空欄表現」セクション追加
- 品質チェックリストに結合セル確認項目を追加

### Fixed
- ICAO Doc 9303 Part 11 Section 6.2.4.2のテーブルを修正（Command/Response/Status Bytes等を空欄化）
- 可読性向上: 同一値の繰り返しを排除し、視覚的グループ化を実現

## [3.7.0] - 2026-01-14

### Added
- 複雑なテーブルの列数不整合・情報欠落に関する知見を追加
- TROUBLESHOOTING.mdに「テーブルの列数不整合・情報欠落」セクション追加
- APDUコマンド仕様テーブル等での手動修正方法を文書化

### Fixed
- ICAO Doc 9303 Part 11 Section 6.2.4.1のテーブルを修正（4列構造に復元）

## [3.6.0] - 2026-01-14

### Fixed
- 入れ子リストの誤った構文(`- -item`)を自動修正
- Doclingが入れ子リストを不正な形式で出力する問題に対応
- パターン: `- -item` → `  - item` (2スペースインデント)
- ICAO Doc 9303 Part 11で33行の入れ子リストを修正

### Added
- TROUBLESHOOTING.mdに「入れ子リストの誤った構文」セクション追加

## [3.5.0] - 2026-01-14

### Fixed
- テーブル内の不要なセパレータ行(`| --- |`)の自動削除機能を追加
- 入れ子の箇条書きがテーブルとして誤認識される問題に対応
- ICAO Doc 9303 Part 11で699行の不要なセパレータを削除

### Added
- TROUBLESHOOTING.mdに「テーブル内の不要なセパレータ行」セクション追加

## [3.4.0] - 2026-01-14

### Added
- ASN.1構文の改行問題をTROUBLESHOOTING.mdに追加
- 品質チェックリストにASN.1確認項目を追加
- 長いASN.1定義検出コマンド追加: `grep "::=" | awk 'length > 100'`

## [3.3.0] - 2026-01-14

### Added
- 二重パイプ(`||`)のHTMLエンティティ化を追加（step 7）
- Markdownテーブル内で`||`が列区切りとして誤認識される問題に対応

## [3.2.0] - 2026-01-14

### Added
- セミコロン区切りリストの改行サポート追加（step 6）
- ピリオド+大文字パターンの改行追加（step 5、略語除外機能付き）

## [3.1.0] - 2026-01-14

### Improved
- テーブルセル内の文の境界検出改善（step 4）
- 誤検出パターンの除外リスト追加

## [3.0.0] - 2025-12-27

### Added
- 初版リリース
- 12ステップの後処理パイプライン実装
