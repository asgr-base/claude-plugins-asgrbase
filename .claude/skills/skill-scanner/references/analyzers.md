# アナライザー詳細リファレンス

## コアアナライザー（APIキー不要）

### static_analyzer
- YAMLルール + YARAパターンでSKILL.mdとスクリプトを検査
- 検出対象: 既知の危険パターン、シークレット、疑わしいURL
- カスタムYARAルール追加: `--custom-rules /path/to/rules/`

### bytecode
- `.pyc`ファイルの整合性を検証
- ソースと対応するバイトコードの一致を確認

### pipeline
- シェルパイプラインのtaint分析
- 検出対象: 信頼できない入力がシェルコマンドに流れるパターン

### behavioral_analyzer
- PythonファイルのAST（抽象構文木）解析
- データフロー追跡: 機密ファイル読み取り → 外部送信 のチェーン検出
- 有効化: `--use-behavioral`

### trigger_analyzer
- スキルのdescriptionフィールドの曖昧さを検出
- 過度に広い/汎用的なトリガー条件を警告
- 有効化: `--use-trigger`

## 外部APIアナライザー（APIキー必要）

### llm_analyzer
- SKILL.mdとスクリプトをLLMでセマンティック解析
- プロバイダー: `anthropic` または `openai`
- 環境変数:
  ```bash
  export SKILL_SCANNER_LLM_API_KEY="your_api_key"
  export SKILL_SCANNER_LLM_MODEL="claude-sonnet-4-20250514"
  export SKILL_SCANNER_LLM_PROVIDER="anthropic"
  ```
- 有効化: `--use-llm --llm-provider anthropic`

### meta_analyzer
- LLMアナライザーの結果を二次検査して偽陽性を除去
- `--use-llm` と併用することで精度向上
- 有効化: `--enable-meta`
- 環境変数: `SKILL_SCANNER_META_LLM_API_KEY`（未設定時は`SKILL_SCANNER_LLM_API_KEY`を流用）

### virustotal
- バイナリファイルのSHA256ハッシュをVirusTotal APIで照合
- 環境変数: `VIRUSTOTAL_API_KEY`
- 有効化: `--use-virustotal`
- 未知ファイルのアップロード: `--vt-upload-files`

### aidefense
- Cisco AI Defenseクラウドサービスによる解析
- 環境変数: `AI_DEFENSE_API_KEY`
- 有効化: `--use-aidefense`

## 推奨スキャン構成

### 最速（コアのみ）
```bash
skill-scanner scan /path/to/skill
```

### バランス（振る舞い解析追加）
```bash
skill-scanner scan /path/to/skill --use-behavioral --use-trigger
```

### 高精度（LLM + 偽陽性フィルタ）
```bash
SKILL_SCANNER_LLM_API_KEY="..." skill-scanner scan /path/to/skill \
  --use-behavioral --use-trigger \
  --use-llm --llm-provider anthropic \
  --enable-meta
```

### フル（全エンジン）
```bash
skill-scanner scan /path/to/skill \
  --use-behavioral --use-trigger \
  --use-llm --llm-provider anthropic --llm-consensus-runs 3 \
  --enable-meta \
  --use-virustotal \
  --use-aidefense
```

## 脅威タクソノミー（Cisco AI Security Framework）

| 脅威 | AITech | AISubtech |
|------|--------|-----------|
| プロンプトインジェクション | AITech-1.1 | AISubtech-1.1.1 |
| 間接インジェクション | AITech-1.2 | AISubtech-1.2.1 |
| データ窃取 | AITech-8.2 | AISubtech-8.2.3 |
| ハードコードシークレット | AITech-8.2 | AISubtech-8.2.2 |
| コマンドインジェクション | AITech-9.1 | AISubtech-9.1.4 |
| コード実行 | AITech-9.1 | AISubtech-9.1.1 |
| 難読化 | AITech-9.2 | AISubtech-9.2.1 |
| サプライチェーン攻撃 | AITech-9.3 | AISubtech-9.3.1 |
| ツールポイズニング | AITech-12.1 | AISubtech-12.1.2 |
| リソース乱用 | AITech-13.1 | AISubtech-13.1.1 |
