#!/usr/bin/env python3
"""
Claude Code Insights レポート 静的翻訳辞書スクリプト

レポートHTML内の固定UI要素（ナビ、見出し、ラベル、ボタン、JS文字列等）を
一括で日本語に置換する。動的コンテンツ（ナラティブ段落）は対象外。

Usage:
    python3 translate_static.py <input.html> <output.html>
    python3 translate_static.py <file.html>  # in-place

所要時間: <1秒（サブエージェント不要）
"""

import sys
import os

# =============================================================================
# 静的翻訳辞書: レポート構造が変わらない限り再利用可能
# =============================================================================

STATIC_REPLACEMENTS = [
    # --- A. HTML属性 ---
    ('<title>Claude Code Insights</title>', '<title>Claude Code インサイト</title>'),

    # --- B. ナビゲーション/TOCリンク ---
    ('>What You Work On</a>', '>作業内容</a>'),
    ('>How You Use CC</a>', '>Claude Codeの使い方</a>'),
    ('>Impressive Things</a>', '>注目すべき成果</a>'),
    ('>Where Things Go Wrong</a>', '>問題が発生する箇所</a>'),
    ('>Features to Try</a>', '>試すべき機能</a>'),
    ('>New Usage Patterns</a>', '>新しい活用パターン</a>'),
    ('>On the Horizon</a>', '>今後の展望</a>'),
    ('>Team Feedback</a>', '>チームフィードバック</a>'),

    # --- C. セクション見出し ---
    ('<h1>Claude Code Insights</h1>', '<h1>Claude Code インサイト</h1>'),
    ('>What You Work On</h2>', '>作業内容</h2>'),
    ('>How You Use Claude Code</h2>', '>Claude Codeの使い方</h2>'),
    ('>Impressive Things You Did</h2>', '>注目すべき成果</h2>'),
    ('>Where Things Go Wrong</h2>', '>問題が発生する箇所</h2>'),
    ('>Existing CC Features to Try</h2>', '>試すべきClaude Code既存機能</h2>'),
    ('>Suggested CLAUDE.md Additions</h3>', '>CLAUDE.mdへの追加提案</h3>'),
    ('>New Ways to Use Claude Code</h2>', '>Claude Codeの新しい活用方法</h2>'),
    ('>On the Horizon</h2>', '>今後の展望</h2>'),

    # --- D. 統計ラベル ---
    ('class="stat-label">Messages</div>', 'class="stat-label">メッセージ</div>'),
    ('class="stat-label">Lines</div>', 'class="stat-label">行数</div>'),
    ('class="stat-label">Files</div>', 'class="stat-label">ファイル</div>'),
    ('class="stat-label">Days</div>', 'class="stat-label">日数</div>'),
    ('class="stat-label">Msgs/Day</div>', 'class="stat-label">メッセージ/日</div>'),

    # --- E1. チャートタイトル ---
    ('>What You Wanted</div>', '>あなたが求めたこと</div>'),
    ('>Top Tools Used</div>', '>よく使ったツール</div>'),
    ('>Languages</div>', '>言語</div>'),
    ('>Session Types</div>', '>セッションタイプ</div>'),
    ('>User Response Time Distribution</div>', '>ユーザー応答時間分布</div>'),
    ('>Multi-Clauding (Parallel Sessions)</div>', '>マルチClaude（並列セッション）</div>'),
    ('User Messages by Time of Day', '時間帯別ユーザーメッセージ'),
    ('>Tool Errors Encountered</div>', '>発生したツールエラー</div>'),
    (">What Helped Most (Claude's Capabilities)</div>", '>最も役立った機能（Claudeの能力）</div>'),
    ('>Outcomes</div>', '>成果</div>'),
    ('>Primary Friction Types</div>', '>主な摩擦の種類</div>'),
    ('>Inferred Satisfaction (model-estimated)</div>', '>推定満足度（モデル推定）</div>'),

    # --- E2. "What You Wanted" バーラベル ---
    ('Observation And Documentation', '観察・ドキュメント作成'),
    ('Research Investigation', '調査・リサーチ'),
    ('Documentation Observation', 'ドキュメント観察'),
    ('Report Generation', 'レポート生成'),
    ('Documentation Update', 'ドキュメント更新'),
    ('Progress Checkpoint', '進捗チェックポイント'),
    ('Documentation Creation', 'ドキュメント作成'),
    ('Configuration Setup', '設定セットアップ'),
    ('Bug Fix', 'バグ修正'),
    ('Feature Implementation', '機能実装'),
    ('Code Refactoring', 'コードリファクタリング'),

    # --- E3. セッションタイプ ---
    ('Single Task', '単一タスク'),
    ('Exploration', '探索'),
    ('Iterative Refinement', '反復改善'),
    ('Multi Task', 'マルチタスク'),
    ('Quick Question', 'クイック質問'),

    # --- E4. Multi-Clauding ---
    ('Overlap Events', '重複イベント'),
    ('Sessions Involved', '関連セッション'),
    ('Of Messages', 'メッセージ比率'),

    # --- E5. 時間帯 ---
    ('Morning (6-12)', '午前 (6-12)'),
    ('Afternoon (12-18)', '午後 (12-18)'),
    ('Evening (18-24)', '夜 (18-24)'),
    ('Night (0-6)', '深夜 (0-6)'),

    # --- E6. ツールエラー ---
    ('>Other<', '>その他<'),
    ('Command Failed', 'コマンド失敗'),
    ('User Rejected', 'ユーザー拒否'),
    ('File Too Large', 'ファイル過大'),
    ('File Not Found', 'ファイル未検出'),
    ('Edit Failed', '編集失敗'),

    # --- E7. 最も役立った機能 ---
    ('Multi-file Changes', '複数ファイル変更'),
    ('Good Explanations', '分かりやすい説明'),
    ('Fast/Accurate Search', '高速・正確な検索'),
    ('Correct Code Edits', '正確なコード編集'),
    ('Good Debugging', '優れたデバッグ'),
    ('Proactive Help', '先回りした支援'),

    # --- E8. 成果 ---
    ('Not Achieved', '未達成'),
    ('Partially Achieved', '部分達成'),
    ('Mostly Achieved', '概ね達成'),
    ('Fully Achieved', '完全達成'),
    ('>Unclear<', '>不明<'),

    # --- E9. 摩擦の種類 ---
    ('Wrong Approach', '誤ったアプローチ'),
    ('Buggy Code', 'バグのあるコード'),
    ('Authentication Errors', '認証エラー'),
    ('Misunderstood Request', 'リクエスト誤解'),
    ('Authentication Failure', '認証失敗'),
    ('User Rejected Action', 'ユーザーによるアクション拒否'),
    ('Timeout Issue', 'タイムアウト問題'),
    ('Permission Denied', '権限拒否'),

    # --- E10. 満足度 ---
    ('>Dissatisfied<', '>不満<'),
    ('Likely Satisfied', 'おそらく満足'),
    ('>Satisfied<', '>満足<'),

    # --- F1. ボタン ---
    ('>Copy</button>', '>コピー</button>'),
    ('>Copy All Checked</button>', '>チェック済みを全てコピー</button>'),

    # --- F2. JS文字列 ---
    ("'Copied!'", "'コピー済み！'"),
    ("'Copy All Checked'", "'チェック済みを全てコピー'"),

    # --- F3. タイムゾーン ---
    ('>PT (UTC-8)<', '>太平洋時間 (UTC-8)<'),
    ('>ET (UTC-5)<', '>東部時間 (UTC-5)<'),
    ('>London (UTC)<', '>ロンドン (UTC)<'),
    ('>CET (UTC+1)<', '>中央ヨーロッパ時間 (UTC+1)<'),
    ('>Tokyo (UTC+9)<', '>東京 (UTC+9)<'),
    ('>Custom offset...<', '>カスタムオフセット...<'),
    ('placeholder="UTC offset"', 'placeholder="UTCオフセット"'),

    # --- F4. ヘルパーテキスト ---
    ('Just copy this into Claude Code to add it to your CLAUDE.md.', '以下をClaude Codeにコピーして、CLAUDE.mdに追加してください。'),
    ("Just copy this into Claude Code and it'll set it up for you.", '以下をClaude Codeにコピーすると、自動でセットアップされます。'),
    ("Just copy this into Claude Code and it'll walk you through it.", '以下をClaude Codeにコピーすると、手順を案内してくれます。'),
    ('>Paste into Claude Code:</div>', '>Claude Codeに貼り付け:</div>'),
    ('>Paste into Claude Code:</span>', '>Claude Codeに貼り付け:</span>'),

    # --- G1. At a Glance ラベル ---
    ('>At a Glance</div>', '>概要</div>'),
    ("<strong>What's working:</strong>", "<strong>うまくいっていること:</strong>"),
    ("<strong>What's hindering you:</strong>", "<strong>妨げになっていること:</strong>"),
    ("<strong>Quick wins to try:</strong>", "<strong>すぐに試せる改善:</strong>"),
    ("<strong>Ambitious workflows:</strong>", "<strong>意欲的なワークフロー:</strong>"),

    # --- G1. At a Glance セクションリンク ---
    ('Impressive Things You Did', '注目すべき成果'),
    ('Where Things Go Wrong', '問題が発生する箇所'),
    ('Features to Try', '試すべき機能'),
    ('On the Horizon', '今後の展望'),

    # --- H. Feature Cardタイトル ---
    ('>Custom Skills</div>', '>カスタムスキル</div>'),
    ('>Headless Mode</div>', '>ヘッドレスモード</div>'),

    # --- Feature Card共通ラベル ---
    ('<strong>Why for you:</strong>', '<strong>あなたにとっての理由:</strong>'),
    ('<strong>Getting started:</strong>', '<strong>始め方:</strong>'),

    # --- G2. Key pattern ラベル ---
    ('<strong>Key pattern:</strong>', '<strong>主要パターン:</strong>'),
]


def translate(input_path: str, output_path: str) -> dict:
    """静的翻訳を適用し、結果統計を返す"""
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    applied = 0
    not_found = []

    for old, new in STATIC_REPLACEMENTS:
        if old in content:
            content = content.replace(old, new)
            applied += 1
        else:
            not_found.append(old[:60])

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return {
        'applied': applied,
        'not_found_count': len(not_found),
        'not_found': not_found,
        'total': len(STATIC_REPLACEMENTS),
    }


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input.html> [output.html]")
        print(f"  If output is omitted, overwrites input (in-place).")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else input_path

    if not os.path.exists(input_path):
        print(f"ERROR: File not found: {input_path}")
        sys.exit(1)

    result = translate(input_path, output_path)

    print(f"Static translation complete:")
    print(f"  Applied: {result['applied']}/{result['total']}")
    print(f"  Not found: {result['not_found_count']}")
    if result['not_found']:
        print(f"  Missing items (may indicate report structure change):")
        for item in result['not_found'][:10]:
            print(f"    - {item}...")

    # 動的コンテンツの翻訳が必要な箇所をカウント
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 英語ナラティブの残存を検出（簡易チェック）
    dynamic_markers = [
        'class="glance-section"',
        'class="narrative"',
        'class="big-win-desc"',
        'class="friction-desc"',
        'class="area-desc"',
        'class="feature-why"',
        'class="pattern-detail"',
        'class="horizon-possible"',
        'class="horizon-tip"',
    ]
    dynamic_count = sum(1 for m in dynamic_markers if m in content)
    if dynamic_count > 0:
        print(f"\n  Dynamic sections remaining (need Claude translation): ~{dynamic_count} sections")
        print(f"  Run the SKILL.md Stage 2 subagent for these, or use:")
        print(f'    claude -p "Read {output_path} and generate a translation map for ONLY the narrative paragraphs (glance-section, narrative, big-win-desc, friction-desc, area-desc, feature-why, pattern-detail, horizon-possible, horizon-tip, fun-ending). Output Python replacement tuples."')


if __name__ == '__main__':
    main()
