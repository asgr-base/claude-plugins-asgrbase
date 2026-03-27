# 後処理の実装詳細

このファイルはpdf2md-doclingスキルの後処理に必要なPythonコードを提供します。

## 統合後処理スクリプト

以下のスクリプトを実行して、全ての後処理を一括で行います：

```python
#!/usr/bin/env python3
"""
Docling PDF変換後処理スクリプト
- 画像の移動とパス更新
- Unicode問題文字の除去
- JSON整形
- テーブル最適化
"""
import os
import re
import shutil
from pathlib import Path

def process_docling_output(md_file: str, output_dir: str, basename: str):
    """Docling出力を整理・最適化"""

    # 1. 画像ディレクトリの準備
    images_dir = Path(output_dir) / "assets" / f"{basename}_docling"
    images_dir.mkdir(parents=True, exist_ok=True)

    # 2. artifacts内の画像を移動
    for artifacts_dir in Path(output_dir).rglob("*_artifacts"):
        for png in artifacts_dir.glob("*.png"):
            shutil.move(str(png), str(images_dir / png.name))
        # 空のartifactsディレクトリを削除
        shutil.rmtree(artifacts_dir, ignore_errors=True)

    # 深いディレクトリ構造を削除（Doclingが作成するもの）
    for item in Path(output_dir).iterdir():
        if item.is_dir() and item.name not in ["assets"]:
            shutil.rmtree(item, ignore_errors=True)

    # 3. Markdownファイルの後処理（順序厳守）
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Phase B: クリーンアップ（問題文字除去→構造認識精度向上）
    content = remove_problematic_unicode(content)
    content = update_image_paths(content, f"assets/{basename}_docling")
    content = format_json_blocks(content)

    # Phase C: 構造再構築（不要行削除→再構築→統合）
    content = remove_repeated_headers(content)
    content = remove_orphaned_code_fences(content)
    content = format_long_code_lines(content)
    content = fix_missing_table_headers(content)
    content = reconstruct_definition_tables(content)
    content = merge_split_tables(content)

    # Phase D: 最終整形（統合後にフォーマット整理）
    content = optimize_tables(content)
    content = add_table_linebreaks(content)

    # 4. 処理済みファイルを保存
    final_md = Path(output_dir) / f"{basename}_docling.md"
    with open(final_md, 'w', encoding='utf-8') as f:
        f.write(content)

    # 元ファイルが別名なら削除
    if Path(md_file) != final_md and Path(md_file).exists():
        Path(md_file).unlink()

    return final_md, images_dir


def update_image_paths(content: str, images_dir: str) -> str:
    """画像パスを相対パスに更新"""
    # パターン: ![Image](/absolute/path/or/relative/path_artifacts/image_xxx.png)
    pattern = r'!\[Image\]\([^)]*?_artifacts/(image_[^)]+\.png)\)'
    replacement = f'![Image]({images_dir}/\\1)'

    new_content = re.sub(pattern, replacement, content)
    count = len(re.findall(pattern, content))
    if count > 0:
        print(f"✅ Updated {count} image paths")
    return new_content


def remove_problematic_unicode(content: str) -> str:
    """問題のあるUnicode文字を除去"""
    # 除去対象の文字範囲
    problematic_ranges = [
        (0xE000, 0xF8FF),  # Private Use Area
    ]
    problematic_codes = [
        0x00AD,  # Soft Hyphen
        0x200B,  # Zero Width Space
        0x200C,  # Zero Width Non-Joiner
        0x200D,  # Zero Width Joiner
        0xFEFF,  # BOM
        0xFFFC,  # Object Replacement
        0xFFFD,  # Replacement Character
    ]

    removed = {}
    for char in content:
        code = ord(char)

        # 範囲チェック
        for start, end in problematic_ranges:
            if start <= code <= end:
                removed[code] = removed.get(code, 0) + 1
                break

        # 個別コードチェック
        if code in problematic_codes:
            removed[code] = removed.get(code, 0) + 1

    # 除去実行
    for code in removed:
        content = content.replace(chr(code), '')

    if removed:
        total = sum(removed.values())
        print(f"✅ Removed {total} problematic Unicode characters")
        for code, count in sorted(removed.items()):
            print(f"   - U+{code:04X}: {count}")

    return content


def format_json_blocks(content: str) -> str:
    """コードブロック内のJSONを整形"""

    def format_json_like(json_str: str) -> tuple[str, bool]:
        """単一行JSONを整形"""
        if '\n' in json_str or len(json_str) < 50:
            return json_str, False

        result = []
        indent = 0
        i = 0

        while i < len(json_str):
            char = json_str[i]

            if char == '{':
                result.append('{\n')
                indent += 1
                result.append('  ' * indent)
            elif char == '}':
                indent -= 1
                result.append('\n' + '  ' * indent + '}')
            elif char == ',':
                result.append(',\n' + '  ' * indent)
                if i + 1 < len(json_str) and json_str[i + 1] == ' ':
                    i += 1
            elif char == ':':
                result.append(':')
                if i + 1 < len(json_str) and json_str[i + 1] == ' ':
                    i += 1
            elif char == ' ' and i + 1 < len(json_str) and json_str[i + 1] in ',}':
                pass  # スキップ
            else:
                result.append(char)

            i += 1

        formatted = ''.join(result)
        formatted = re.sub(r' +\n', '\n', formatted)
        formatted = re.sub(r'\n{2,}', '\n', formatted)
        return formatted, True

    lines = content.split('\n')
    result = []
    in_code_block = False
    format_count = 0

    for line in lines:
        if line.strip().startswith('```'):
            if not in_code_block:
                in_code_block = True
                # そのまま保持（孤立した```はremove_orphaned_code_fencesで削除）
                result.append(line)
            else:
                in_code_block = False
                result.append(line)
            continue

        if in_code_block and line.startswith('{ ') and ' }' in line and ': ' in line:
            formatted, changed = format_json_like(line)
            if changed:
                result.extend(formatted.split('\n'))
                format_count += 1
            else:
                result.append(line)
        else:
            result.append(line)

    if format_count > 0:
        print(f"✅ Formatted {format_count} JSON blocks")

    return '\n'.join(result)


def add_table_linebreaks(content: str) -> str:
    """テーブルセル内の番号付き/箇条書きリスト、および文の境界に<br>タグを追加"""
    lines = content.split('\n')
    processed = []
    modified_count = 0

    for line in lines:
        if line.startswith('|') and '|' in line[1:]:
            original = line

            # 1. 番号付きリストの前に<br>を追加（例: "text 1. item" → "text<br>1. item"）
            # ただし行頭や"|"直後の番号は除く
            line = re.sub(r'(?<=[a-zA-Z\.\)\]\u3002\u3001])(\s*)(\d+)\.\s', r'<br>\2. ', line)

            # 2. "1. -2." パターンを修正（例: "1. -2." → "1. -<br>2."）
            line = re.sub(r'(\d+)\. -(\d+)\.', r'\1. -<br>\2.', line)
            line = re.sub(r'(\d+)\. - (\d+)\.', r'\1. -<br>\2.', line)

            # 3. 箇条書き（•, -, *）の前に<br>を追加
            # "text • item" → "text<br>• item"
            # "text - item" → "text<br>- item" （ただしハイフンは文脈で判断）
            line = re.sub(r'(?<=[a-zA-Z\.\)\]\u3002\u3001])\s+([\u2022\u2023\u2043\u25E6\u00B7])\s', r'<br>\1 ', line)
            # ハイフン箇条書き: 文末+スペース+ハイフン+スペース+大文字開始
            line = re.sub(r'(?<=[a-zA-Z\.\)\]\u3002\u3001])\s+(-)\s+(?=[A-Z])', r'<br>\1 ', line)
            # アスタリスク箇条書き
            line = re.sub(r'(?<=[a-zA-Z\.\)\]\u3002\u3001])\s+(\*)\s+(?=[A-Z])', r'<br>\1 ', line)

            # 4. 小文字終わり+スペース+大文字始まりのパターンに<br>を追加
            # "processing Other values" → "processing<br>Other values"
            # 条件: 4文字以上の小文字で終わる単語 + スペース + 大文字で始まり3文字以上の単語
            # これにより句読点なしで連結された独立した文を分割する
            line = re.sub(r'\b([a-z]{4,}) ([A-Z][a-z]{2,})\b', r'\1<br>\2', line)

            # 5. ピリオド+スペース+大文字始まりのパターンに<br>を追加
            # "encoding Ne > 0. Maximum number" → "encoding Ne > 0.<br>Maximum number"
            # 条件: 3文字以上の単語または数字+ピリオド + スペース + 大文字始まり単語
            # ただし、一般的な略語（Mr., Dr., etc.）は除外
            def add_sentence_break(match):
                """略語を除外して文の境界に<br>を追加"""
                abbreviations = r'\b(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|Ph|St|Ave|etc|Inc|Ltd|Corp)\.'
                full = match.group(0)
                if re.search(abbreviations, full):
                    return full
                return f"{match.group(1)}<br>{match.group(2)}"

            line = re.sub(r'(\w{3,}\.|\d+\.)\s+([A-Z][a-z]{2,})', add_sentence_break, line)

            # 6. セミコロン+スペース+引用符または大文字のパターンに<br>を追加
            # "processing; '6A84' Not enough" → "processing;<br>'6A84' Not enough"
            # "file; Other values" → "file;<br>Other values"
            # 条件: セミコロン + スペース + ('引用符 または 大文字始まり3文字以上の単語)
            line = re.sub(r'(;)\s+([\'\"]|[A-Z][a-z]{2,})', r'\1<br>\2', line)

            # 7. 二重パイプ（||）をHTMLエンティティ化して改行を追加
            # "Object (tag '54') || Discretionary" → "Object (tag '54') &#124;&#124;<br>Discretionary"
            # 条件: 非空白文字 + スペース + || + スペース + 非空白文字
            # 前後に非空白文字があることでテーブル区切りの| |と区別
            # ||を&#124;&#124;にエスケープしてMarkdownテーブルと混同を防ぐ
            line = re.sub(r'(\S)\s+\|\|\s+(\S)', r'\1 &#124;&#124;<br>\2', line)

            if line != original:
                modified_count += 1
        processed.append(line)

    if modified_count > 0:
        print(f"✅ Added <br> tags to {modified_count} table rows")

    return '\n'.join(processed)


def remove_repeated_headers(content: str) -> str:
    """各ページの繰り返しヘッダー（ページ番号、文書タイトル等）を検出・削除"""
    lines = content.split('\n')

    # 繰り返しパターンを検出（3回以上出現する短い行）
    from collections import Counter
    line_counts = Counter()
    for line in lines:
        stripped = line.strip()
        # 短い行（5-100文字）で、見出し・コードブロック・テーブルでないものをカウント
        if (5 <= len(stripped) <= 100 and
            not stripped.startswith('#') and
            not stripped.startswith('```') and
            not stripped.startswith('|')):
            line_counts[stripped] += 1

    # 3回以上出現する行をヘッダー候補として特定
    repeated_headers = {line for line, count in line_counts.items() if count >= 3}

    # ページ番号パターン（数字のみの行）も検出
    page_number_pattern = re.compile(r'^\d{1,4}$')

    # フィルタリング
    filtered = []
    removed_count = 0
    for line in lines:
        stripped = line.strip()
        # 繰り返しヘッダーまたはページ番号を削除（ただしコードブロック・テーブルは保護）
        if (stripped in repeated_headers or page_number_pattern.match(stripped)) and \
           not stripped.startswith('```') and not stripped.startswith('|'):
            removed_count += 1
            continue
        filtered.append(line)

    if removed_count > 0:
        print(f"✅ Removed {removed_count} repeated headers/page numbers")
        if repeated_headers:
            print(f"   Detected patterns: {list(repeated_headers)[:3]}...")

    return '\n'.join(filtered)


def remove_orphaned_code_fences(content: str) -> str:
    """孤立したコードフェンス（```のみの行）を検出・削除

    Doclingが誤って挿入する単独の```記号を削除する。
    ただし、正しいコードブロック（```と```のペア）は保護する。
    """
    lines = content.split('\n')
    result = []
    i = 0
    removed_count = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # コードフェンス候補を検出
        if stripped.startswith('```'):
            # 正規のコードブロック開始（```json, ```python など）は保護
            if len(stripped) > 3:
                result.append(line)
                i += 1
                continue

            # 単独の```の場合、ペアを探す
            # 前後の行をチェックして、コードブロックとして意味があるか判定
            prev_line = lines[i-1].strip() if i > 0 else ''
            next_line = lines[i+1].strip() if i < len(lines) - 1 else ''

            # 前の行が空行またはテキスト、次の行もテキストなら孤立と判断
            # （正規のコードブロックなら、次の行はコード内容のはず）
            is_orphaned = False

            # パターン1: 前後が空行
            if not prev_line and not next_line:
                is_orphaned = True
            # パターン2: 次が通常のテキスト（URL、見出し、段落など）
            elif next_line and (
                next_line.startswith('http') or
                next_line.startswith('#') or
                next_line.startswith('-') or
                (len(next_line) > 40 and not next_line.startswith('```'))
            ):
                is_orphaned = True
            # パターン3: 前がURLで終わる
            elif prev_line and prev_line.startswith('http'):
                is_orphaned = True

            if is_orphaned:
                removed_count += 1
                i += 1
                continue

        result.append(line)
        i += 1

    if removed_count > 0:
        print(f"✅ Removed {removed_count} orphaned code fences (```)")

    return '\n'.join(result)


def format_long_code_lines(content: str) -> str:
    """極端に長いコード行（XML/ASN.1等）を検出してコードブロック化

    Doclingが改行せずに出力した長いコード（WSDL、XML、ASN.1等）を検出し、
    適切にフォーマットしてコードブロックとして整形する。
    """
    lines = content.split('\n')
    result = []
    formatted_count = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        # XML/WSDL検出（2000文字以上）
        if len(stripped) > 2000 and (
            '<' in stripped and '>' in stripped and
            ('<?xml' in stripped or '<wsdl:' in stripped or '<xs:' in stripped or '<soap:' in stripped)
        ):
            # XMLとして整形を試みる
            try:
                from xml.dom import minidom

                # XMLを整形
                dom = minidom.parseString(stripped)
                pretty_xml = dom.toprettyxml(indent="  ")

                # 余分な空行を削除
                pretty_lines = [l for l in pretty_xml.split('\n') if l.strip()]
                formatted_xml = '\n'.join(pretty_lines)

                # コードブロックとして追加
                result.append('```xml')
                result.append(formatted_xml)
                result.append('```')

                formatted_count += 1

            except Exception:
                # パースエラーの場合は基本的な改行のみ
                formatted = re.sub(r'>\s*<', '>\n<', stripped)
                result.append('```xml')
                result.append(formatted)
                result.append('```')
                formatted_count += 1

        # ASN.1検出（1000文字以上、DEFINITIONS/BEGIN/END等を含む）
        elif len(stripped) > 1000 and (
            'DEFINITIONS' in stripped and 'BEGIN' in stripped and 'END' in stripped
        ):
            # ASN.1コードとして整形
            formatted = stripped

            # 主要なASN.1構文で改行を追加
            formatted = re.sub(r'\s*DEFINITIONS\s+', '\nDEFINITIONS ', formatted)
            formatted = re.sub(r'\s*IMPLICIT TAGS\s*::=\s*BEGIN\s+', ' IMPLICIT TAGS ::= BEGIN\n\n', formatted)
            formatted = re.sub(r'\s*IMPORTS\s+', 'IMPORTS\n  ', formatted)
            formatted = re.sub(r'\s*FROM\s+', '\n  FROM ', formatted)
            formatted = re.sub(r'\}\s*;', '}\n;\n', formatted)
            formatted = re.sub(r';\s*([A-Z][a-zA-Z0-9]+\s*::=)', r';\n\n\1', formatted)  # 型定義間
            formatted = re.sub(r'::=\s*SEQUENCE\s*\{', '::= SEQUENCE {\n  ', formatted)
            formatted = re.sub(r'::=\s*CHOICE\s*\{', '::= CHOICE {\n  ', formatted)
            formatted = re.sub(r'::=\s*INTEGER\s*\{', '::= INTEGER {\n  ', formatted)
            formatted = re.sub(r'::=\s*SET OF\s+', '::= SET OF ', formatted)
            formatted = re.sub(r',\s*([a-zA-Z][a-zA-Z0-9]*\s+)', r',\n  \1', formatted)  # フィールド間
            formatted = re.sub(r'\}\s*([A-Z][a-zA-Z0-9]+\s*::=)', r'\n}\n\n\1', formatted)  # SEQUENCE終了
            formatted = re.sub(r'--([^\n]+)', r'\n--\1', formatted)  # コメント
            formatted = re.sub(r'\s*OPTIONAL\s*,', ' OPTIONAL,', formatted)
            formatted = re.sub(r'\s*OPTIONAL\s+--', ' OPTIONAL\n  --', formatted)
            formatted = re.sub(r'id-([a-zA-Z0-9\-]+)\s+OBJECT IDENTIFIER\s*::=', r'\nid-\1 OBJECT IDENTIFIER ::=', formatted)
            formatted = re.sub(r'\}\s*END\s*$', r'\n}\n\nEND', formatted)

            # 行頭の余分な空白を削除
            formatted_lines = []
            for l in formatted.split('\n'):
                # 既にインデントがある行はそのまま、先頭スペースが多すぎる行は調整
                if l.strip():
                    formatted_lines.append(l)
                else:
                    formatted_lines.append('')

            formatted = '\n'.join(formatted_lines)

            # コードブロックとして追加
            result.append('```asn1')
            result.append(formatted)
            result.append('```')

            formatted_count += 1

        else:
            result.append(line)

    if formatted_count > 0:
        print(f"✅ Formatted {formatted_count} long code lines as code blocks")

    return '\n'.join(result)


def merge_split_tables(content: str) -> str:
    """改ページで分断されたテーブルを統合

    改ページによりテーブルが分断され、ヘッダー行が繰り返される場合に
    重複ヘッダーを削除してテーブルを結合する。
    """
    lines = content.split('\n')
    result = []
    i = 0
    merged_headers = 0

    while i < len(lines):
        line = lines[i]

        # テーブル行を検出
        if line.startswith('|') and '|' in line[1:]:
            # テーブル行を収集
            result.append(line)
            i += 1

            # テーブルの続きを処理
            while i < len(lines):
                current = lines[i]

                # テーブル行ならそのまま追加
                if current.startswith('|') and '|' in current[1:]:
                    result.append(current)
                    i += 1
                    continue

                # 空行の場合、後続をチェック
                if current.strip() == '':
                    # 空行の後にテーブルが続くか確認
                    next_non_empty = i + 1
                    while next_non_empty < len(lines) and lines[next_non_empty].strip() == '':
                        next_non_empty += 1

                    if next_non_empty < len(lines):
                        next_line = lines[next_non_empty].strip()

                        # 次がテーブルヘッダー+セパレータのパターンか確認
                        if (next_line.startswith('|') and
                            next_non_empty + 1 < len(lines)):
                            potential_sep = lines[next_non_empty + 1].strip()

                            # ヘッダー+セパレータの組み合わせ（改ページで重複したヘッダー）
                            if re.match(r'^\|[\s\-:|]+\|$', potential_sep):
                                # 重複ヘッダー+セパレータをスキップして統合
                                merged_headers += 1
                                i = next_non_empty + 2
                                continue

                        # 次がテーブルデータ行（セパレータでない）なら統合継続
                        if (next_line.startswith('|') and
                            not re.match(r'^\|[\s\-:|]+\|$', next_line)):
                            # 空行をスキップしてテーブル継続
                            i = next_non_empty
                            continue

                    # テーブル終了、空行を追加して次へ
                    result.append(current)
                    i += 1
                    break
                else:
                    # テーブル以外の行でテーブル終了
                    break
        else:
            result.append(line)
            i += 1

    # 連続する空行を1つに圧縮
    final = []
    prev_empty = False
    for line in result:
        if line.strip() == '':
            if not prev_empty:
                final.append(line)
            prev_empty = True
        else:
            final.append(line)
            prev_empty = False

    if merged_headers > 0:
        print(f"✅ Merged {merged_headers} split tables (removed duplicate headers)")

    return '\n'.join(final)


def fix_missing_table_headers(content: str) -> str:
    """セパレータ行がないテーブルにヘッダー+セパレータを追加

    Doclingが2列の定義リストテーブルをヘッダーなしで出力した場合に、
    適切なヘッダー行とセパレータ行を追加する。

    検出パターン:
    - 段落（ピリオドで終わる文）の直後に空行を挟んでテーブル（|で始まる行）が開始
    - テーブルの2行目がセパレータ行でない（データ行である）
    """
    lines = content.split('\n')
    result = []
    i = 0
    fixed_count = 0

    while i < len(lines):
        line = lines[i]

        # テーブル行を検出
        if line.startswith('|') and '|' in line[1:]:
            # 前の行をチェック（段落の後か？）
            prev_non_empty_idx = i - 1
            while prev_non_empty_idx >= 0 and lines[prev_non_empty_idx].strip() == '':
                prev_non_empty_idx -= 1

            prev_line = lines[prev_non_empty_idx] if prev_non_empty_idx >= 0 else ''

            # 次の行がセパレータ行か確認
            next_idx = i + 1
            is_separator = (next_idx < len(lines) and
                          re.match(r'^\|[\s\-:|]+\|$', lines[next_idx].strip()))

            # 前の行が段落（ピリオドで終わる）で、次がセパレータでない場合
            if (prev_line.endswith('.') and not is_separator):
                # 列数を計算
                col_count = line.count('|') - 1

                # ヘッダー行とセパレータ行を追加
                if col_count == 2:
                    header = '| Item | Value |\n'
                    separator = '|---|---|\n'
                elif col_count == 3:
                    header = '| Column 1 | Column 2 | Column 3 |\n'
                    separator = '|---|---|---|\n'
                elif col_count == 4:
                    header = '| Column 1 | Column 2 | Column 3 | Column 4 |\n'
                    separator = '|---|---|---|---|\n'
                else:
                    # その他の列数には対応しない
                    result.append(line)
                    i += 1
                    continue

                result.append(header)
                result.append(separator)
                result.append(line)
                fixed_count += 1
                i += 1
                continue

        result.append(line)
        i += 1

    if fixed_count > 0:
        print(f"✅ Added headers and separators to {fixed_count} tables")

    return '\n'.join(result)


def reconstruct_definition_tables(content: str) -> str:
    """罫線なしテーブル（定義リスト）をMarkdownテーブルに再構成

    Doclingが罫線のない2列テーブルをテーブルとして認識できず、
    各セルを個別の行として出力する問題に対応。

    検出パターン:
    - "## Header" の後に "Col2Header" が続く（2列目ヘッダー）
    - 交互に出現する短い行（用語）と長い行（定義）のペア

    用語パターン:
    - 略語: ABC, 3DES, eMRTD（大文字/数字）
    - 一般用語: "Algorithm", "Adobe RGB", "1:1 application case"
    """
    lines = content.split('\n')
    result = []
    i = 0
    reconstructed_count = 0

    def is_term_like(text: str) -> bool:
        """用語らしいテキストかどうかを判定"""
        if not text or len(text) > 60:
            return False
        # 略語パターン: 大文字のみ、または大文字+数字
        if re.match(r'^[A-Z0-9_\-]+$', text):
            return True
        # キャメルケース: eMRTD, ePassport
        if re.match(r'^[a-z]+[A-Z]', text):
            return True
        # 一般用語パターン: 大文字開始、スペース/括弧を含む可能性
        # 例: "Algorithm", "Adobe RGB", "1:1 application case", "Application Identifier (AID)"
        if re.match(r'^[A-Z0-9][A-Za-z0-9\s\-\(\):,/]+$', text):
            # 定義文のような長い文ではないことを確認
            # 文末がピリオドで終わらない、または短い
            if not text.endswith('.') or len(text) < 40:
                return True
        return False

    while i < len(lines):
        line = lines[i]

        # パターン: "## Term" + "Definition" のような見出し+ヘッダーパターン
        if line.startswith('## ') and not line.startswith('### '):
            header_text = line[3:].strip()

            # 次の行がテーブルの2列目ヘッダーか確認
            if i + 2 < len(lines) and lines[i + 1].strip() == '':
                potential_col2_header = lines[i + 2].strip()

                # ヘッダーパターンの検出（短い単語）
                if (potential_col2_header and
                    not potential_col2_header.startswith('#') and
                    not potential_col2_header.startswith('|') and
                    len(potential_col2_header) < 50):

                    # 以降の行が交互パターンか確認
                    pairs = []
                    j = i + 3  # potential_col2_header の次

                    while j + 2 < len(lines):
                        # 空行をスキップ
                        if lines[j].strip() == '':
                            j += 1
                            continue

                        term = lines[j].strip()

                        # 次の空行をスキップ
                        k = j + 1
                        while k < len(lines) and lines[k].strip() == '':
                            k += 1

                        if k >= len(lines):
                            break

                        definition = lines[k].strip()

                        # 終了条件: 見出し、テーブル
                        if (term.startswith('#') or term.startswith('|') or
                            definition.startswith('#') or definition.startswith('|')):
                            break

                        # 用語パターンチェック
                        if is_term_like(term) and len(definition) > 0:
                            # 定義が用語より十分長いことを確認（誤検出防止）
                            if len(definition) > len(term):
                                pairs.append((term, definition))
                                j = k + 1
                                continue

                        break

                    # 5ペア以上あればテーブルとして再構成
                    if len(pairs) >= 5:
                        # テーブルヘッダーを生成
                        result.append(f'## {header_text}')
                        result.append('')
                        result.append(f'| {header_text} | {potential_col2_header} |')
                        result.append('|---|---|')

                        for term, definition in pairs:
                            # パイプ文字をエスケープ
                            definition = definition.replace('|', '\\|')
                            result.append(f'| {term} | {definition} |')

                        result.append('')
                        reconstructed_count += 1
                        i = j
                        continue

        result.append(line)
        i += 1

    if reconstructed_count > 0:
        print(f"✅ Reconstructed {reconstructed_count} definition tables")

    return '\n'.join(result)


def optimize_tables(content: str) -> str:
    """テーブル形式を最適化"""
    original_size = len(content)

    # URL内のハイフン後スペースを削除
    content = re.sub(r'-\s+(?=[a-zA-Z0-9])', '-', content)

    # テーブル行の複数スペースを圧縮
    lines = content.split('\n')
    cleaned = []
    separator_count = 0

    for line in lines:
        if '|' in line and not line.strip().startswith('```'):
            # 複数スペースを単一に
            line = re.sub(r'  +', ' ', line)

            # セパレータ行の最適化
            stripped = line.strip()
            if stripped and all(c in '|- ' for c in stripped):
                if re.search(r'[-]{4,}', stripped):
                    parts = line.split('|')
                    minimized = []
                    for part in parts:
                        s = part.strip()
                        if s and all(c == '-' for c in s):
                            minimized.append('---')
                        else:
                            minimized.append(part)
                    line = '|'.join(minimized)
                    separator_count += 1

        cleaned.append(line)

    content = '\n'.join(cleaned)

    new_size = len(content)
    reduction = original_size - new_size
    if reduction > 0:
        pct = reduction / original_size * 100
        print(f"✅ Table optimization: {original_size:,} → {new_size:,} bytes ({pct:.1f}% reduction)")
        print(f"   - Minimized {separator_count} separator rows")

    return content


# 使用例
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python process_docling.py <md_file> <output_dir> [basename]")
        sys.exit(1)

    md_file = sys.argv[1]
    output_dir = sys.argv[2]
    basename = sys.argv[3] if len(sys.argv) > 3 else Path(md_file).stem

    final_md, images_dir = process_docling_output(md_file, output_dir, basename)
    print(f"\n✅ Processing complete:")
    print(f"   - Markdown: {final_md}")
    print(f"   - Images: {images_dir}")
```

## 個別処理スクリプト

必要に応じて個別の処理のみを実行する場合は、以下のスクリプトを使用：

### 画像パス更新のみ

```python
import re

file_path = "output_directory/filename.md"
images_dir = "assets/filename_docling"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r'!\[Image\]\([^)]*?_artifacts/(image_[^)]+\.png)\)'
replacement = f'![Image]({images_dir}/\\1)'
new_content = re.sub(pattern, replacement, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

count = len(re.findall(pattern, content))
print(f"✅ Updated {count} image paths")
```

### Unicode除去のみ

```python
file_path = "output_directory/filename.md"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Private Use Area (U+E000-F8FF) を除去
cleaned = ''.join(c for c in content if not (0xE000 <= ord(c) <= 0xF8FF))

# その他の問題文字
for code in [0x00AD, 0x200B, 0x200C, 0x200D, 0xFEFF, 0xFFFC, 0xFFFD]:
    cleaned = cleaned.replace(chr(code), '')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(cleaned)

print(f"✅ Cleaned Unicode: {len(content)} → {len(cleaned)} chars")
```

### テーブル最適化のみ

```python
import re

file_path = "output_directory/filename.md"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

original_size = len(content)

# 複数スペース圧縮とセパレータ最適化
lines = []
for line in content.split('\n'):
    if '|' in line and not line.strip().startswith('```'):
        line = re.sub(r'  +', ' ', line)
        if re.match(r'^[\s|:-]+$', line.strip()):
            parts = line.split('|')
            line = '|'.join('---' if p.strip() and all(c == '-' for c in p.strip()) else p for p in parts)
    lines.append(line)

content = '\n'.join(lines)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ Optimized: {original_size:,} → {len(content):,} bytes")
```

### テーブルセル内改行追加のみ

```python
import re

file_path = "output_directory/filename.md"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
processed = []
modified_count = 0

for line in lines:
    if line.startswith('|') and '|' in line[1:]:
        original = line
        # 番号付きリストの前に<br>を追加
        line = re.sub(r'(?<=[a-zA-Z\.\)\]\u3002\u3001])(\s*)(\d+)\.\s', r'<br>\2. ', line)
        # "1. -2." パターン修正
        line = re.sub(r'(\d+)\. -(\d+)\.', r'\1. -<br>\2.', line)
        # 箇条書き（•等）の前に<br>を追加
        line = re.sub(r'(?<=[a-zA-Z\.\)\]\u3002\u3001])\s+([\u2022\u2023\u2043\u25E6\u00B7])\s', r'<br>\1 ', line)
        # ハイフン箇条書き（文末+ハイフン+大文字開始）
        line = re.sub(r'(?<=[a-zA-Z\.\)\]\u3002\u3001])\s+(-)\s+(?=[A-Z])', r'<br>\1 ', line)
        if line != original:
            modified_count += 1
    processed.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(processed))

print(f"✅ Added <br> tags to {modified_count} table rows")
```

## Bashワンライナー

簡易的な処理はBashでも可能：

```bash
# 画像移動
ARTIFACTS=$(find output_dir -type d -name "*_artifacts" | head -1)
mkdir -p output_dir/assets/basename_docling
mv "$ARTIFACTS"/*.png output_dir/assets/basename_docling/
rm -rf "$ARTIFACTS"

# Private Use Area文字カウント（確認用）
python3 -c "
with open('file.md', 'r') as f:
    pua = [c for c in f.read() if 0xE000 <= ord(c) <= 0xF8FF]
    print(f'PUA chars: {len(pua)}')
"
```

---
**関連**: [SKILL.md](SKILL.md) | [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
