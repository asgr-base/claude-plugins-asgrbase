# Feedly Intelligence Report

Claude Code Agent Skill for generating intelligence reports from Feedly RSS feeds.

## Features

- Fetch articles from Feedly categories via API
- Score articles based on multiple metrics:
  - **Engagement**: Feedly engagement + Hatena Bookmark + Hacker News points
  - **Relevance**: Keyword matching with synonym expansion
  - **Freshness**: Publication time decay
  - **Source Trust**: Configurable source credibility
- Deduplicate similar articles
- Generate prioritized Markdown reports (MUST READ / SHOULD READ / OPTIONAL / SKIP)
- Mark processed articles as read on Feedly

## Requirements

- Python 3.10+
- Feedly account with [Developer Access Token](https://feedly.com/v3/auth/dev)
- `requests` library

## Installation

1. Clone or copy this skill to your Claude Code skills directory:
   ```bash
   cp -r feedly-intelligence-report ~/.claude/skills/
   ```

2. Install Python dependency:
   ```bash
   pip install requests
   ```

3. Create Feedly configuration:
   ```bash
   mkdir -p ~/.feedly
   echo 'YOUR_FEEDLY_TOKEN' > ~/.feedly/token
   chmod 600 ~/.feedly/token
   cp config-sample.json ~/.feedly/config.json
   # Edit ~/.feedly/config.json with your categories and keywords
   ```

## Configuration

See [CONFIG.md](CONFIG.md) for full configuration options.

### Basic config.json structure

```json
{
  "token_file": "~/.feedly/token",
  "output_dir": "Daily",
  "fetch_count": 100,
  "time_range_hours": 24,
  "global_keywords": ["AI", "LLM", "your-topic"],
  "synonym_groups": [
    ["AI", "artificial intelligence", "machine learning"]
  ],
  "categories": [
    {
      "name": "Tech",
      "slug": "tech",
      "stream_id": "user/YOUR_USER_ID/category/Tech"
    }
  ]
}
```

## Usage

### With Claude Code

```
/feedly-intelligence-report
```

### Manual CLI

```bash
# Fetch articles
python scripts/feedly_fetch.py --config ~/.feedly/config.json --output /tmp/articles.json

# Generate scored report
python scripts/feedly_score.py --config ~/.feedly/config.json --input /tmp/articles.json

# Mark as read (optional)
python scripts/feedly_fetch.py --mark-read /tmp/articles.json
```

## Output

Reports are generated at: `{output_dir}/YYYY-MM/YYYY-MM-DD（weekday）_feeds-report.md`

Example: `Daily/2024-01/2024-01-15（月）_feeds-report.md`

## Documentation

| File | Description |
|------|-------------|
| [SKILL.md](SKILL.md) | Claude Code skill definition |
| [SETUP.md](SETUP.md) | Feedly API token setup guide |
| [CONFIG.md](CONFIG.md) | Configuration file specification |

## License

MIT

## Author

Created with Claude Code
