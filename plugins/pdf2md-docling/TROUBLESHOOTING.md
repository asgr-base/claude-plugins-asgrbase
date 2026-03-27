# トラブルシューティング

## インストール関連

### Error: "command not found: docling"

```bash
# インストール
pipx install docling
pipx ensurepath

# パス確認
which docling
# 期待値: docling
```

### Error: "ModuleNotFoundError: No module named 'cv2'"

```bash
pipx inject docling opencv-python
```

## 出力関連

### Markdownファイルが大きすぎる（MB単位）

**原因**: 画像がBase64で埋め込まれている

**対処**:
```bash
# 正しいオプションで再実行
docling "input.pdf" \
  --image-export-mode referenced \
  --to md
```

### 画像が表示されない

**原因**: 絶対パスのまま、または相対パスが間違っている

**確認**:
```bash
grep -o '!\[Image\]([^)]*)' filename.md | head -5
```

**対処**: パスが`assets/basename_docling/image_*.png`形式であることを確認

### 文字化け・ゴミ文字（「」等）

**原因**: Private Use Area文字（U+E000-F8FF）が残っている

**確認**:
```bash
python3 -c "
with open('file.md', 'r') as f:
    pua = [c for c in f.read() if 0xE000 <= ord(c) <= 0xF8FF]
    if pua:
        print(f'Found {len(pua)} PUA chars')
        print(f'First 5: {[hex(ord(c)) for c in pua[:5]]}')
    else:
        print('Clean')
"
```

**対処**: [IMPLEMENTATION.md](IMPLEMENTATION.md) のUnicode除去スクリプトを実行

### JSONが読みにくい（単一行）

**原因**: JSON整形処理がスキップされた

**対処**: [IMPLEMENTATION.md](IMPLEMENTATION.md) のJSON整形スクリプトを実行

### テーブルが肥大化している

**原因**: Doclingが余分なスペース・ハイフンを出力

**対処**: [IMPLEMENTATION.md](IMPLEMENTATION.md) のテーブル最適化スクリプトを実行

## 変換品質関連

### MRZ等の`<`記号がHTMLエンティティ化

**症状**: MRZ（Machine Readable Zone）や他のテキストで使用される`<`記号が`&lt;`にHTMLエンティティ化される

**具体例（ICAO Doc 9303 Part 11, Appendix C）**:
```markdown
# Docling出力（不正）
I&lt;UTOSTEVENSON&lt;&lt;PETER&lt;JOHN&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;
D23145890&lt;UTO3407127M95071227349&lt;&lt;&lt;8

# 正しい形式
I<UTOSTEVENSON<<PETER<JOHN<<<<<<<<<<<
D23145890<UTO3407127M95071227349<<<8
```

**原因**:
1. Doclingの後処理で`<`を自動的にHTMLエンティティ化
2. MRZではフィラー文字として`<`が大量に使用される
3. Markdown内でHTMLとして誤認識される可能性を回避する意図的な処理と推測

**検出方法**:
```bash
# MRZ部分での&lt;を検索（暗号記法の<g>、<G>は除外）
grep -n "&lt;" filename_docling.md | grep -v "<g>" | grep -v "<G>"
```

**対処**:
1. MRZセクション（Appendix C等）で`&lt;`を`<`に置換
2. 暗号プロトコルの記法（`<g>`、`<G>`等）は`&lt;g&gt;`のまま維持
3. 一括置換は危険なため、MRZセクションのみ個別に対処

**予防**:
- 現状ではDocling側の仕様のため予防不可
- 後処理スクリプトでMRZパターン検出と自動置換を実装可能

**影響**: MRZは仕様書での参照頻度が高く、読みづらさが目立つ。技術的には`&lt;`も`<`も同じ意味だが、視認性が低下

### テーブル内の特殊記号による列分割

**症状**: テーブルセル内の`||`（論理OR、連結演算子）や角括弧 `[]` がMarkdownの列区切りとして誤認識され、列数が増加

**具体例1（ICAO Doc 9303 Part 11, Table 8 - 二重パイプ）**:
```markdown
# Docling出力（不正・7列）
| Password | Encoding                 |     |               |     |                 |
| MRZ      | SHA-1(Document Number    |     | Date of Birth |     | Date of Expiry) |

# 正しい構造（2列）
| Password | Encoding                                                                   |
| MRZ      | SHA-1(Document Number &#124;&#124; Date of Birth &#124;&#124; Date of Expiry) |
```

**具体例2（ICAO Doc 9303 Part 11, Table K-2 - 角括弧）**:
```markdown
# Docling出力（不正・7列）
| Content | [CARi ][ |     | CARi-1][ |     | 0x00..00] |

# 正しい構造（2列）
| Content | \[CAR<sub>i</sub>\]\[CAR<sub>i-1</sub>\]\[0x00..00\] |
```

**原因**:
1. Doclingが`||`や角括弧 `[]` を含むセルを複数列に分割して出力
2. 後処理v3.3.0で二重パイプのHTMLエンティティ化を追加したが、既に列分割されたケースには適用されない
3. 角括弧は配列表記として使用されるが、Markdownでは特殊文字として扱われることがある

**検出方法**:
```bash
# 列数が不自然に多いテーブルを検索（連続する空セル）
grep -n "| .* |     |.*|     |" filename_docling.md

# 角括弧を含む行を検索
grep -n "\[.*\]\[" filename_docling.md
```

**対処**:
1. テーブルヘッダーの列数を正しい数（通常2列の定義リスト形式）に修正
2. 分割されたセル内容を結合
3. 特殊記号をエスケープ:
   - `||` → `&#124;&#124;`
   - `[]` → `\[` と `\]`
4. 添字がある場合は `<sub>i</sub>` で表現

**予防**: 現時点では手動確認が必要。演算子、配列表記、数式を含むテーブルは特に注意

**影響**: 定義表（Field/Value形式）が7列に分割され、内容が理解不能になる

### 数式が変換できない (`<!-- formula-not-decoded -->`)

**症状**: 数式が`<!-- formula-not-decoded -->`というプレースホルダーに置き換えられる

**具体例（ICAO Doc 9303 Part 11, Appendix B.1）**:
```markdown
The curve is defined over the prime field
<!-- formula-not-decoded -->
where p is the characteristic...
```

**原因**:
1. Doclingが数式を画像として認識するが、OCRで正確にテキスト化できない
2. 数式が特殊なフォント（Symbol、数式専用フォント）で記述されている
3. 上付き・下付き文字、ギリシャ文字、特殊記号が含まれる

**検出方法**:
```bash
# 変換できなかった数式を検索
grep -n "<!-- formula-not-decoded -->" filename_docling.md
```

**対処**:
1. 元のPDFを参照して数式を確認
2. 周辺のコンテキストから数式を推測
3. 標準的な数学記法でMarkdownに記述
   - 上付き: `x²` → `x²` または `x^2`
   - 下付き: `E[q]` → `E[q]` または `E_q`
   - ギリシャ文字: `α`, `β`, `γ`等をUnicodeで記述
   - 分数: `a/b` または LaTeX形式 `$\frac{a}{b}$`

**例（ICAO Doc 9303 Part 11, Appendix B.1で実際に対処した例）**:
```markdown
# 1つ目: 楕円曲線の定義式
<!-- formula-not-decoded -->
→ <!-- formula-not-decoded: 楕円曲線の定義式 E: y² = x³ + ax + b (mod p) が記載されていると推測 -->

# 2つ目: 入力パラメータの制約
<!-- formula-not-decoded -->
→ <!-- formula-not-decoded: 入力tの制約条件 0 < t < p が記載されていると推測 -->

# 3つ目: 座標系の関係式
<!-- formula-not-decoded -->
→ <!-- formula-not-decoded: アフィン座標(x,y)とヤコビアン座標(X,Y,Z)の関係式 (x,y) = (X/Z², Y/Z³) が記載されていると推測 -->

# 4つ目: アルゴリズムのステップ書き換え
<!-- formula-not-decoded -->
→ <!-- formula-not-decoded: Step 2のX²計算を -ba⁻¹(1+(α+α²)⁻¹) mod p から (α+α²)^(p-2) mod p を用いた形に書き換えた式が記載されていると推測 -->
```

**コメント追加の指針**:
- 周辺文脈から数式の内容を推測
- 「が記載されていると推測」を明記して推測であることを示す
- 変数名、演算子、関係性を可能な限り具体的に記述
- 元のPDFを参照できる場合は正確な数式に置き換える

**予防**:
- Doclingのバージョンアップで改善される可能性あり
- 数式が多い文書は変換後に全数確認が必要
- 代替案: LaTeX数式を含むPDFの場合、LaTeX→Markdown変換ツールの併用を検討

**影響**: 技術仕様書、暗号プロトコル、アルゴリズム定義で発生。数式は情報の核心部分のため、必ず手動修正が必要

### テーブル構造が崩れる

**対処**: `--table-mode accurate`オプションを確認（TableFormer使用）

```bash
docling "input.pdf" \
  --table-mode accurate \
  --to md
```

### 画像が欠落している

**確認**:
1. PDFの画像数を確認
2. 出力ディレクトリの画像数を確認

```bash
ls output_dir/assets/basename_docling/*.png | wc -l
```

**対処**: Doclingのバージョンを確認（v2.0以上推奨）

## FAQ

### Q: pdf2mdとpdf2md-doclingの使い分けは？

| ケース | 推奨 |
|--------|------|
| 簡易プレビュー | pdf2md |
| RAG/本番 | pdf2md-docling |
| テーブル重視 | pdf2md-docling |
| 速度重視 | pdf2md |

### Q: 変換に時間がかかりすぎる

**目安**: ~1秒/ページ（50ページで約50秒）

大きなPDFの場合:
- `--table-mode fast`で高速化可能（品質低下あり）
- ページ分割して並列処理

### Q: 複数PDFを同じディレクトリに変換したい

命名規則により自動的に分離される：
```
output/
├── doc1_docling.md
├── doc2_docling.md
└── assets/
    ├── doc1_docling/
    └── doc2_docling/
```

### Q: JPEG出力したい

Doclingは現在PNGのみ。変換が必要な場合：

```bash
cd output_dir/assets/basename_docling
for f in *.png; do
    convert "$f" "${f%.png}.jpg"
    rm "$f"
done
# Markdown内のパスも更新
sed -i '' 's/\.png/.jpg/g' ../../basename_docling.md
```

## 構造・順序の問題

### セクションの順序が入れ替わっている

**症状**: 改ページで分断されたセクションの順序が入れ替わる（例: Appendix D.1.1.1 Inputsセクションが本来の位置より前に出現）

**原因**: Doclingが改ページを検出してセクションを分割する際に、元の順序を保持できない

**検出方法**:
```bash
# 見出し構造を確認
grep -n "^##" filename_docling.md | grep "D\.1"
```

**対処**: 手動でセクションを正しい順序に並び替える

**具体例（ICAO Doc 9303 Part 11, Section 9.6-9.7）**:
```markdown
# Docling出力（不正な順序）
9.7.1 Key Derivation Function  ← 誤った位置
9.6 Key Agreement Algorithms
9.7 Key Derivation Mechanism
9.7.1.1 3DES                    ← 親(9.7.1)がない

# 正しい順序
9.6 Key Agreement Algorithms
9.7 Key Derivation Mechanism
  9.7.1 Key Derivation Function  ← 9.7の直後に配置
    9.7.1.1 3DES
    9.7.1.2 AES
```

**検出方法の改善**:
```bash
# セクション階層の不整合を検出
grep -n "^##" filename_docling.md | awk '{print $2}' | sort -V | diff - <(grep -n "^##" filename_docling.md | awk '{print $2}')
```

**予防**: 現時点では自動対応困難。変換後に見出し構造を目視確認する

### テーブルヘッダーが欠落している

**症状**: Appendix A EXAMPLE 1, 2, 3のような2列テーブルにヘッダー行とセパレータ行がない

**原因**: Doclingが定義リスト形式のテーブルをヘッダーなしで出力

**対処**: `fix_missing_table_headers`関数により自動修正（v3.0.0以降）

**確認**: 段落の後に直接テーブルが始まる箇所をチェック

### 縦結合セルの構造が崩れる

**症状**: 縦に結合されたセルが隣の行のセルと結合される

**具体例（Table 6 READ BINARY）**:
```markdown
元のPDF:
  P1  }
  P2  } See Table 7  (結合セル)
  Lc field | Length...

Docling出力（不正）:
  | P1 | See Table 7 |
  | P2 Lc field | Length... |

期待される出力:
  | P1 | |
  | P2 | See Table 7 |
  | Lc field | Length... |
```

**原因**: Doclingが縦結合セルを検出できず、次の行のセル名と結合してしまう

**検出方法**:
```bash
# "P1/P2 + セル名" のパターンを検索
grep "| P[12] [A-Z]" filename_docling.md
```

**対処**: 手動修正が必要
1. 結合セルを持つ行を空欄に変更: `| P1 | |`
2. 次の行を正しく分割: `| P2 | See Table 7 |`
3. 誤って結合された部分を独立行に: `| Lc field | Length... |`

**予防**: 現時点では自動対応困難。複雑なテーブル構造は変換後に目視確認が必要

### テーブルの列数不整合・情報欠落

**症状**: 複雑なテーブル(複数行セル、縦結合等)で列が統合され、情報が欠落する

**具体例**:
```markdown
# Docling出力（不正・3列）
| Data | 0x91 | Ephemeral Public Key REQUIRED |
| Data | 0x84 | Reference of a private key CONDITIONAL |

# 期待される出力（正・4列）
| Data | 0x91 | *Ephemeral Public Key*<br>説明文... | REQUIRED |
|      | 0x84 | *Reference of a private key*<br>説明文... | CONDITIONAL |
```

**原因**:
- Doclingが複数行にわたるセル内容を正しく認識できない
- 複数列が1列に統合される(例: 説明列とステータス列)
- セル内の改行や構造情報が失われる

**検出方法**:
```bash
# REQUIREDやCONDITIONALが他の内容と結合されている行を検索
grep "REQUIRED\|CONDITIONAL" filename_docling.md | grep -v "^\s*|.*|.*|.*|"
```

**対処**: 手動修正が必要
1. 元のPDF/画像を参照して正しい列構造を確認
2. テーブルヘッダーの列数を修正
3. 各行のセルを正しい列に分割
4. セル内の複数行内容を`<br>`で区切る
5. 強調部分を`*斜体*`や`**太字**`でマークアップ
6. **結合セルは空欄で表現** (繰り返しを避ける)

**例（ICAO Doc 9303 Part 11, Section 6.2.4.1）**:
- 修正前: "Ephemeral Public Key REQUIRED" (1セル)
- 修正後: "*Ephemeral Public Key*<br>Ephemeral public key..." (説明セル) + "REQUIRED" (別セル)

**結合セルの空欄表現**:
```markdown
# 悪い例（繰り返し）
| Command | Command | Command |
| Data | 0x80 | ... | REQUIRED |
| Data | 0x84 | ... | CONDITIONAL |

# 良い例（空欄）
| Command |      |     |             |
| Data    | 0x80 | ... | REQUIRED    |
|         | 0x84 | ... | CONDITIONAL |
```

**メリット**:
- 可読性向上: 視覚的にグループ化が明確
- PDF原本に忠実: 元の結合セル構造を再現
- メンテナンス性: 行の追加・削除が容易

**適用箇所**: Command/Response/Status Bytes等、複数行にわたる同一カテゴリのセル

**予防**: 現時点では自動対応困難。APDUコマンド仕様等の構造化テーブルは変換後に要確認

### 構造化コンテンツの箇条書き化による情報欠落

**症状**: 構造化された仕様（Input/Output/Actions等）が全て箇条書きとして認識され、整形時に情報が欠落する

**具体例（ICAO Doc 9303 Part 11, Section 9.7.1）**:
```markdown
# Docling出力（誤認識）
- The shared secret value K (REQUIRED)
- A 32-bit, big-endian integer counter c (REQUIRED)
- keydata = H (K || c)
- Output octet string keydata

# 正しい構造
**Input**:
- K (REQUIRED)
- c (REQUIRED)

**Actions**:
1. Compute: keydata = H(K || c)
2. Output octet string keydata

**Output**:
- keydata (octet string)
```

**原因**:
1. Doclingが構造的なセクション（Input/Output/Actions）を認識できず、全て同一レベルの箇条書きとして出力
2. 手動整形時に、計算式と出力ステートメントを分離せず、片方を削除してしまう危険性

**検出方法**:
```bash
# 元のPDFと変換後のMarkdownで行数を比較
# 特にアルゴリズム仕様、プロトコル定義セクションを重点的に確認
```

**対処**:
1. 元のPDFを参照して、正しい構造を確認
2. Input/Output/Actionsの3セクション構造を復元
3. 計算式とステートメントを適切に分離

**予防**:
- 構造化コンテンツ（アルゴリズム、プロトコル仕様）は変換後に元PDFと比較確認
- 箇条書きを整形する際は、削除ではなく再構成を優先

### MRZ例が段落形式で読みづらい

**症状**: MRZ（Machine Readable Zone）の例が箇条書き+段落形式で出力され、元PDFの表形式と大きく異なる

**具体例（ICAO Doc 9303 Part 11, Appendix C）**:
```markdown
# Docling出力（不正）
1. Read the MRZ

MRZ =

I<UTOSTEVENSON<<PETER<JOHN<<<<<<<<<<<

D23145890<UTO3407127M95071227349<<<8

2. Construct the 'MRZ information' from the MRZ

Document number

= D23145890734

check digit = 9

Date of Birth

= 340712

check digit = 7

# 正しい形式（表形式）
1. Read the MRZ
   ```
   MRZ = I<UTOSTEVENSON<<PETER<JOHN<<<<<<<<<<<
         D23145890<UTO3407127M95071227349<<<8
   ```

2. Construct the 'MRZ information' from the MRZ

   | Field            | Value                      | Check Digit |
   |------------------|----------------------------|-------------|
   | Document number  | D23145890734               | 9           |
   | Date of Birth    | 340712                     | 7           |
   | Date of Expiry   | 950712                     | 2           |
   | MRZ_information  | D23145890734934071279507122 |             |
```

**原因**:
1. DoclingがPDFの表レイアウトを検出できず、段落として出力
2. MRZは固定長フォーマットで、元PDFでは視覚的な整列が重要
3. フィールド名と値の対応関係が視覚的に分かりにくい

**検出方法**:
```bash
# MRZサンプルセクションを検索
grep -n "TD[12] MRZ" filename_docling.md
```

**対処**:
1. MRZ文字列をコードブロック（```）で囲み、インデントを揃える
2. Document number, Date of Birth等のフィールドを表形式に整形
3. TD1 MRZは3行形式、TD2 MRZは2行形式に従う

**予防**:
- 現時点では自動対応困難
- 後処理スクリプトでMRZセクションパターンを検出し、自動整形を実装可能

**影響**: MRZサンプルは仕様書の重要な参照ポイント。視認性低下により実装時のエラーリスク増加

### 暗号プロトコル例の変数代入が分離される

**症状**: 暗号プロトコルのWorked Exampleで、変数名と値が別々の段落に分離され、代入関係が不明瞭になる

**具体例（ICAO Doc 9303 Part 11, Appendix D.3）**:
```markdown
# Docling出力（不正）
4. Calculate session keys (KS Enc and KS MAC):

KS Enc =

KS MAC

'979EC13B1CBFE9DCD01AB0FED307EAE5'

= 'F1CB1F1FB5ADF208806B89DC579DC1F8'

# 正しい形式
4. Calculate session keys (KS_Enc and KS_MAC):
   ```
   KS_Enc = '979EC13B1CBFE9DCD01AB0FED307EAE5'
   KS_MAC = 'F1CB1F1FB5ADF208806B89DC579DC1F8'
   ```
```

**原因**:
1. PDFで表形式または整列されたレイアウトを段落として誤認識
2. 変数名と`=`と値が別々の段落ノードとして抽出される
3. 暗号値（長い16進数文字列）が独立した段落として認識される

**検出方法**:
```bash
# 単独の16進数文字列行を検索（変数名なし）
grep -n "^'[0-9A-F ]\\+'\$" filename_docling.md

# 「=」で終わる行を検索（値が次行にある可能性）
grep -n "= \$" filename_docling.md
```

**対処**:
1. 変数名、等号、値を同一行のコードブロックに統合
2. 複数の変数代入は縦に整列してコードブロック化
3. ステップ番号を太字（`**Step N.**`）で明確化

**予防**:
- 現時点では自動対応困難
- 後処理スクリプトで変数代入パターン（`VAR =`と次行の16進数値）を検出し、統合可能

**影響**: 暗号プロトコルの実装時に変数の対応関係が不明瞭になり、実装エラーの原因となる

### ASN.1構文が1行に連結される

**症状**: ASN.1定義(SEQUENCE, CHOICE, OBJECT IDENTIFIER等)が改行なしで1行に連結される

**具体例**:
```asn1
LDSSecurityObject ::= SEQUENCE { version LDSSecurityObjectVersion, hashAlgorithm DigestAlgorithmIdentifier, dataGroupHashValues SEQUENCE SIZE (2..ub-DataGroups) OF DataGroupHash, ldsVersionInfo LDSVersionInfo OPTIONAL --If present, version MUST be V1 }
```

**期待される出力**:
```asn1
LDSSecurityObject ::= SEQUENCE {
    version LDSSecurityObjectVersion,
    hashAlgorithm DigestAlgorithmIdentifier,
    dataGroupHashValues SEQUENCE SIZE (2..ub-DataGroups) OF DataGroupHash,
    ldsVersionInfo LDSVersionInfo OPTIONAL
    --If present, version MUST be V1
}
```

**原因**: Doclingが構造化データをプレーンテキストとして1行で出力

**検出方法**:
```bash
# 長いASN.1定義を検索(100文字以上の::=行)
grep "::=" filename_docling.md | awk 'length > 100'
```

**対処**: 手動修正が必要
1. コードブロックの言語を`json`から`asn1`に変更
2. SEQUENCE/CHOICE定義を複数行に分割
3. フィールドごとに改行とインデントを追加
4. コメント(`--`)を適切な位置に配置

**予防**: 現時点では自動対応困難。ASN.1を含む仕様書は変換後に確認が必要

### テーブル内の不要なセパレータ行

**症状**: テーブルデータ行の間に`| --- | --- | --- |`形式の不要なセパレータ行が挿入される

**具体例**:
```markdown
| 1. | SCOPE | 1 |
| --- | --- | --- |
| 2. | ASSUMPTIONS | 1 |
| --- | --- | --- |
| 3. | SECURING DATA | 3 |
```

**原因**: Doclingが入れ子の箇条書き(2)の下のa), b), c)など)をテーブル行として誤認識し、各グループ間にセパレータを挿入

**検出方法**:
```bash
# テーブルデータ行後の不要なセパレータを検索
grep -B1 "^| --- |" filename_docling.md | grep -v "^--$" | grep -v "^| --- |"
```

**対処**: 自動修正可能
```python
import re
lines = content.split('\n')
result = []
for i, line in enumerate(lines):
    if re.match(r'^\|\s*---\s*\|', line):
        # 前行が通常のテーブルデータ行なら削除
        if i > 0 and '|' in lines[i-1] and not re.match(r'^\|[-:]+\|', lines[i-1]):
            continue  # スキップ
    result.append(line)
content = '\n'.join(result)
```

**対応箇所**: 後処理Step 8-10 (テーブル最適化)で実装を検討

**影響**: 目次や手順説明のテーブルでよく発生。可読性を損ねるが情報は失われない

### 番号付きリストの途中断絶

**症状**: 番号付きリスト(1, 2, 3...)の途中で、`<br>4<br>`のような不正な形式が挿入される

**具体例**:
```markdown
1. The terminal sends a certificate chain...
2. The IC verifies the certificates...
3. The IC randomly chooses a challenge...
<br>4<br>The terminal responds with the signature...
<br>5<br>The IC checks that Verify...
```

**期待される出力**:
```markdown
1. The terminal sends a certificate chain...
2. The IC verifies the certificates...
3. The IC randomly chooses a challenge...
4. The terminal responds with the signature...
5. The IC checks that Verify...
```

**原因**:
1. Doclingが改ページや複雑なレイアウトで番号付きリストの連続性を認識できない
2. 後処理Step 12「テーブルセル内改行」で番号パターン(`\d+\.`)を`<br>`で置換するルールが、リスト外のコンテキストで誤適用される

**検出方法**:
```bash
# <br>数字<br>パターンを検索
grep "<br>[0-9]<br>" filename_docling.md
```

**対処**: 手動修正
1. `<br>数字<br>`パターンを削除
2. 正しい番号付きリスト形式(`数字. `)に変換
3. 下付き文字や数式記号を適切にマークアップ(`<sub>IFD</sub>`等)

**例（ICAO Doc 9303 Part 11, Section 7.1.2）**:
```markdown
# 修正前
<br>4<br>The terminal responds with the signature s IFD = Sign (SK IFD , ID IC || r IC || Comp (PK DH,IFD )).

# 修正後
4. The terminal responds with the signature s<sub>IFD</sub> = Sign(SK<sub>IFD</sub>, ID<sub>IC</sub> || r<sub>IC</sub> || Comp(PK<sub>DH,IFD</sub>)).
```

**予防**: 後処理Step 12で、リストコンテキスト内かどうかを判定する必要がある（要実装改善）

**影響**: プロトコル仕様、手順説明等の番号付きリストで発生。情報は失われないが可読性が大幅に低下

### 入れ子リストの誤った構文

**症状**: 入れ子のリストアイテムが`- -item`形式で出力される

**具体例**:
```markdown
- For 3DES and AES-128 (l=128):
- -c0=0xa668892a7c41e3ca739f40b057d85904
- -c1=0xa4e136ac725f738b01c1f60217c188ad
```

**期待される出力**:
```markdown
- For 3DES and AES-128 (l=128):
  - c0=0xa668892a7c41e3ca739f40b057d85904
  - c1=0xa4e136ac725f738b01c1f60217c188ad
```

**原因**: Doclingがインデントレベル(入れ子構造)を認識するが、Markdown構文への変換が不完全

**検出方法**:
```bash
# "- -" パターンを検索
grep "^- -" filename_docling.md
```

**対処**: 自動修正可能
```python
import re
for line in lines:
    if re.match(r'^-\s+-(.*)$', line):
        # "- -item" → "  - item" (2スペースインデント)
        content = re.match(r'^-\s+-(.*)$', line).group(1)
        line = f"  - {content}"
```

**対応箇所**: 後処理Step 5-6で実装を検討

**Doclingからのインデント情報**:
- Markdown出力(`--to md`)では構造情報が限定的
- JSON出力(`--to json`)にはbounding box、インデントレベル等の詳細情報あり
- ただしJSON→Markdown変換の追加実装が必要

**影響**: 定数定義、技術仕様の階層リストで発生。可読性が大幅に低下

---
**関連**: [SKILL.md](SKILL.md) | [IMPLEMENTATION.md](IMPLEMENTATION.md)
