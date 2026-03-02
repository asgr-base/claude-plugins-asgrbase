# トラブルシューティング

## インストール

### `command not found: skill-scanner`
`uv tool install` 後もPATHに含まれていない場合:
```bash
# uv run 経由で実行（インストール不要）
uv run --with cisco-ai-skill-scanner skill-scanner scan /path/to/skill

# または uv tool の PATH を確認
uv tool dir
# 出力先を PATH に追加: export PATH="$HOME/.local/bin:$PATH"
```

### `No virtual environment found` エラー（pip使用時）
```bash
# systemに直接インストール
pip install --break-system-packages cisco-ai-skill-scanner

# または uv を使う（推奨）
uv tool install cisco-ai-skill-scanner
```

### モジュールが見つからない
```bash
# ソースからの場合
cd /path/to/skill-scanner
uv sync --all-extras
uv run skill-scanner --version
```

## LLMアナライザー

### `API key required` エラー
```bash
# 環境変数をエクスポートしてから実行
export SKILL_SCANNER_LLM_API_KEY="your_api_key"
skill-scanner scan /path/to/skill --use-llm --llm-provider anthropic

# または uv run で渡す
SKILL_SCANNER_LLM_API_KEY="..." uv run --with cisco-ai-skill-scanner \
  skill-scanner scan /path/to/skill --use-llm --llm-provider anthropic
```

### Meta-Analyzerが初期化されない
LLM APIキーが設定されていない。Meta-AnalyzerはLLMアナライザーに依存:
```bash
export SKILL_SCANNER_LLM_API_KEY="your_api_key"
# または専用キーを設定
export SKILL_SCANNER_META_LLM_API_KEY="your_api_key"
```

## スキャン結果

### `Skill not found` / スキルディレクトリエラー
SKILL.mdが存在するディレクトリを指定すること:
```bash
# 正しい例（SKILL.mdを含むディレクトリ）
skill-scanner scan .claude/skills/my-skill

# 誤った例（SKILL.md自体を指定）
skill-scanner scan .claude/skills/my-skill/SKILL.md
```

### マルフォームスキルでクラッシュ
フィールドが不正なスキルでもスキャンを続行する:
```bash
skill-scanner scan /path/to/skill --lenient
skill-scanner scan-all /path/to/skills --recursive --lenient
```

### 偽陽性が多い
ポリシーを緩くするか、メタアナライザーで絞り込む:
```bash
# 緩いポリシーを使用
skill-scanner scan /path/to/skill --policy permissive

# LLM + メタで偽陽性除去
skill-scanner scan /path/to/skill --use-llm --enable-meta
```

## CI/CD

### GitHub Actions でSARIF出力が空
`--format sarif` と `--output` の両方を指定すること:
```bash
skill-scanner scan-all ./skills \
  --fail-on-severity high \
  --format sarif \
  --output results.sarif
```

### pre-commitフックが全スキルをスキャンしない
デフォルトでは変更のあるスキルのみスキャン。全スキャンは:
```bash
skill-scanner-pre-commit --all
```

## バージョン確認

```bash
uv run --with cisco-ai-skill-scanner skill-scanner --version
skill-scanner list-analyzers
skill-scanner validate-rules
```
