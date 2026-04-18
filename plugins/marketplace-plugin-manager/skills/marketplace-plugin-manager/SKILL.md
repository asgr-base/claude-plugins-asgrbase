---
name: marketplace-plugin-manager
description: asgr-base マーケットプレイスへのプラグイン追加・更新・公開管理スキル。新規プラグイン作成、既存プラグインのバージョンアップ（plugin.json / marketplace.json / README.md × 2の4ファイル一括更新）、整合性チェック、GitHub pushまで一貫して実行。「マーケットプレイスにプラグインを追加して」「asgr-baseにXXXを追加して」「プラグインをバージョンアップして」「plugin.jsonを更新してリリースして」「プラグインを公開して」「marketplace.jsonを更新して」「整合性チェックして」など、マーケットプレイスやプラグイン公開に明示的に言及した依頼でのみ使用すること。「スキルを作って」「スキルを追加して」だけでは使用しないこと（個人用ローカルスキルの可能性があるため）。
version: 1.2.4
author: claude_code
createDate: 2026-04-10
updateDate: 2026-04-18
---

# Marketplace Plugin Manager

`asgr-base` マーケットプレイスのプラグイン管理スキル。

**このマーケットプレイス**
- **GitHub**: https://github.com/asgr-base/claude-plugins-asgrbase
- **ローカルパス**: `Repos/asgr-base/claude-plugins-asgrbase/`（ワークスペース相対）

**Anthropic 公式リファレンス**
- **プラグイン仕様**: https://github.com/anthropics/claude-code/tree/main/plugins
- **公式マーケットプレイス**: https://github.com/anthropics/claude-code/blob/main/.claude-plugin/marketplace.json
- **plugin.json スキーマ**: https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/plugin-structure/references/manifest-reference.md

> **重要**: plugin.json のフィールド・marketplace.json の構造・SKILL.md frontmatter の仕様は変更される可能性がある。操作前に上記の公式リファレンスを WebFetch で取得し、最新仕様に基づいて対応すること。ローカルの `references/plugin-structure.md` は参考として使用し、公式仕様と差異がある場合は公式を優先する。

プラグイン構造の詳細は [`references/plugin-structure.md`](references/plugin-structure.md) を参照。

## 操作の判定

ユーザーの依頼から操作を判定して実行する:

| 操作 | トリガー例 |
|------|-----------|
| **[A] 新規追加** | 「マーケットプレイスに新しいプラグインを追加して」「asgr-baseにXXXを追加して」「プラグインとして公開したい」 |
| **[U] 更新** | 「プラグインをバージョンアップして」「plugin.jsonを更新してリリースして」「marketplace.jsonを更新して」 |
| **[V] 整合性検証** | 「プラグインのバージョンを確認して」「整合性チェックして」 |

> **注意**: 「スキルを作って」「スキルを追加して」だけでは本スキルを使用しないこと。個人用スキル作成は `skill-creator` スキルを使用する。

---

## 前提条件（全操作共通）

### GitHub 認証と権限確認

```bash
# 認証状態
gh auth status

# push 権限確認（[A][U] で必要。[V] は不要）
gh api repos/asgr-base/claude-plugins-asgrbase --jq '.permissions.push'
```

`push` が `true` でない場合はユーザーに通知して処理を中止する。

### リポジトリのローカルパス特定

```bash
REPO=""
for candidate in \
  "$(pwd)/Repos/asgr-base/claude-plugins-asgrbase" \
  "$(dirname $(pwd))/claude-plugins-asgrbase" \
  "$HOME/Obsidian/MyVault/Repos/asgr-base/claude-plugins-asgrbase"; do
  if [ -d "$candidate/.git" ]; then
    REPO="$candidate"
    break
  fi
done

if [ -z "$REPO" ]; then
  echo "リポジトリが見つかりません。gh repo clone asgr-base/claude-plugins-asgrbase でクローンしてください。"
fi

echo "リポジトリ: $REPO"
```

### git コミッター設定確認

```bash
cd "$REPO"
CURRENT_NAME=$(git config user.name)
CURRENT_EMAIL=$(git config user.email)
echo "現在の設定: $CURRENT_NAME <$CURRENT_EMAIL>"
# asgr-base チームの場合は設定する:
# git config user.name "asgr-base"
# git config user.email "dev@asgr-base.dev"
```

---

## [A] 新規プラグイン追加

### Step 0: スコープ確認（必須）

**実行前に必ずユーザーに確認する**:

```
作成するスキルの公開範囲を確認させてください。

[1] マーケットプレイス（チーム共有）
    asgr-base に追加し、GitHub push します。
    インストールコマンド: claude plugin install <name>@asgr-base

[2] 個人用（ローカルのみ）
    ~/.claude/skills/ または ワークスペースの .claude/skills/ に SKILL.md を作成します。
    マーケットプレイスには追加しません。
```

**[2] 個人用** を選択した場合:
- このスキル（marketplace-plugin-manager）の処理は**ここで終了**する
- 代わりに `skill-creator` スキルを呼び出してローカルスキルを作成する

**[1] マーケットプレイス** を選択した場合のみ、以下の Step 1 以降を実行する。

> **ヒント**: マーケットプレイス向けの場合も、SKILL.md 自体の設計・テスト・改善には `skill-creator` を利用できる（推奨）。`skill-creator` で完成した SKILL.md を Step 3 でプラグイン構造に配置すればよい。

### Step 1: 情報収集

未確定の場合、ユーザーに確認する:

- **プラグイン名**（kebab-case 例: `my-tool-manager`）
- **説明**（日本語 50字以内）
- **スキルパターン**:
  - シンプル: スキル1つ（atlassian-manager パターン）
  - マルチ: サブスキル複数（pr-creator パターン）→ サブスキル名を確認
- **キーワード**（タグ）
- **カテゴリ**（設定・共通 / ツール統合系 / タスク実行系）

### Step 2: ディレクトリ作成

```bash
# REPO は前提条件セクションで特定済みの変数を使用
NAME="<plugin-name>"

mkdir -p "$REPO/plugins/$NAME/.claude-plugin"
# シンプルパターン:
mkdir -p "$REPO/plugins/$NAME/skills/$NAME"
# マルチパターン (サブスキル分):
# mkdir -p "$REPO/plugins/$NAME/skills/<subskill1>"
# mkdir -p "$REPO/plugins/$NAME/skills/<subskill2>"
```

### Step 2.5: SKILL.md の作成方針を確認

SKILL.md の作成には2通りある:

| 方針 | 手順 |
|------|------|
| **A. skill-creator を使う（推奨）** | `skill-creator` スキルで SKILL.md を設計・テスト・改善した後、Step 3 でそのファイルをプラグイン構造に配置する |
| **B. スケルトンを作成** | Step 3 のテンプレートから最小限の SKILL.md を作成し、後から肉付けする |

`skill-creator` を使うと eval・テストケース・反復改善まで行えるため、品質の高いスキルになる。

### Step 3: 4ファイル作成（必須・漏れ禁止）

#### `.claude-plugin/plugin.json`

```json
{
  "name": "<name>",
  "version": "1.0.0",
  "description": "<説明>",
  "author": { "name": "asgr-base" },
  "license": "Apache-2.0",
  "keywords": ["<tag1>", "<tag2>"]
}
```

#### `skills/<name>/SKILL.md`（シンプルパターン）

frontmatter キーは `name:`（マルチパターンのサブスキルは `skill:`）:

```markdown
---
name: <name>
description: <スキルの説明と使用タイミング。自動トリガーされる文脈も含める>
version: 1.0.0
author: claude_code
createDate: <YYYY-MM-DD>
updateDate: <YYYY-MM-DD>
---

# <スキルタイトル>

（スキル本文）
```

マルチパターンの各サブスキルは frontmatter を `skill: <subskill-name>` にする。

#### `plugins/<name>/README.md`

```markdown
# <name>

<説明>

## インストール

\`\`\`bash
claude plugin install <name>@asgr-base
\`\`\`

## スキル

### <name>（または サブスキル一覧）

...

## 前提条件

...
```

#### `.claude-plugin/marketplace.json`（`example-plugin` エントリーの直前に追加）

```json
{
  "name": "<name>",
  "description": "<説明>",
  "source": "./plugins/<name>",
  "version": "1.0.0",
  "author": { "name": "asgr-base" },
  "license": "Apache-2.0",
  "tags": ["<tag1>", "<tag2>"]
}
```

#### `README.md`（トップレベル・適切なカテゴリの表に行追加）

```markdown
| [<name>](./plugins/<name>) | <説明> | 1.0.0 |
```

カテゴリ:
- **設定・共通**: チームルール・ワークスペース設定
- **ツール統合系**: 外部サービス連携（Slack, Atlassian 等）
- **タスク実行系**: ビジネスタスク一気通貫

### Step 4: git commit & push

```bash
cd "$REPO"
git add plugins/<name>/ .claude-plugin/marketplace.json README.md
git commit -m "feat(<name>): v1.0.0 — <説明の要約>"
git push origin main
```

---

## [U] 既存プラグイン更新（バージョンアップ）

**プラグインのファイルを変更した後、必ずこの手順を実行する。**

### Step 1: 現在バージョンと変更内容を確認

```bash
# REPO は前提条件セクションで特定済みの変数を使用
NAME="<plugin-name>"
python3 -c "import json; print(json.load(open('$REPO/plugins/$NAME/.claude-plugin/plugin.json'))['version'])"
```

### Step 2: バージョン種別を決定

| 変更内容 | バンプ | 例 |
|---------|-------|-----|
| 誤字修正・表記修正 | PATCH | `1.0.0 → 1.0.1` |
| 機能追加・テスト追加・ドキュメント充実 | MINOR | `1.0.0 → 1.1.0` |
| 破壊的変更・大規模リファクタ | MAJOR | `1.0.0 → 2.0.0` |

### Step 3: 4ファイル一括更新（必須・漏れ禁止）

以下を**必ず全て**更新すること。1つでも漏れると整合性が崩れる。

| # | ファイル | 更新内容 |
|---|---------|---------|
| 1 | `plugins/<name>/.claude-plugin/plugin.json` | `"version"` フィールド |
| 2 | `.claude-plugin/marketplace.json` | 該当プラグインの `"version"` フィールド |
| 3 | `plugins/<name>/README.md` | 変更内容を反映（テスト一覧・新機能等） |
| 4 | `README.md`（トップレベル） | 該当行のバージョン番号 |

**一括バージョン更新スクリプト**（JSON の 2ファイルを確実に更新）:

```python
import json, re
from pathlib import Path

repo = Path("Repos/asgr-base/claude-plugins-asgrbase")  # ワークスペースからの相対パス
name = "<plugin-name>"
new_ver = "<new-version>"

# 1. plugin.json
pj = repo / f"plugins/{name}/.claude-plugin/plugin.json"
d = json.loads(pj.read_text())
d["version"] = new_ver
pj.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
print(f"✅ plugin.json: {new_ver}")

# 2. marketplace.json
mj = repo / ".claude-plugin/marketplace.json"
d = json.loads(mj.read_text())
for p in d["plugins"]:
    if p["name"] == name:
        p["version"] = new_ver
        break
mj.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
print(f"✅ marketplace.json: {new_ver}")

print("⚠️  README.md × 2 を手動で更新してください")
```

README.md × 2 はバージョン番号の行をテキスト検索して置換する。

### Step 4: git commit & push

```bash
cd "$REPO"
git add plugins/<name>/ .claude-plugin/marketplace.json README.md
git commit -m "chore(<name>): v<new-version> — <変更内容の要約>"
git push origin main
```

---

## [V] 整合性チェック

全プラグインの4ファイル間バージョン整合性を確認する:

```python
import json, re
from pathlib import Path

repo = Path("Repos/asgr-base/claude-plugins-asgrbase")
mj = json.loads((repo / ".claude-plugin/marketplace.json").read_text())
readme = (repo / "README.md").read_text()

print("=== バージョン整合性チェック ===\n")
ok = True
for entry in mj["plugins"]:
    name = entry["name"]
    mkt_ver = entry["version"]
    pj_path = repo / f"plugins/{name}/.claude-plugin/plugin.json"

    if not pj_path.exists():
        print(f"❌ {name}: plugin.json が存在しない")
        ok = False
        continue

    pj_ver = json.loads(pj_path.read_text())["version"]
    in_readme = bool(re.search(rf"\[{re.escape(name)}\].*\|\s*{re.escape(mkt_ver)}\s*\|", readme))

    status = "✅" if pj_ver == mkt_ver and in_readme else "❌"
    if status == "❌":
        ok = False
    print(f"{status} {name}")
    if pj_ver != mkt_ver:
        print(f"   plugin.json={pj_ver} vs marketplace.json={mkt_ver} — 不一致!")
    if not in_readme:
        print(f"   README.md にバージョン {mkt_ver} が見当たらない")

print(f"\n{'全プラグイン整合性OK ✅' if ok else '不整合あり ❌ — 上記を修正してください'}")
```
