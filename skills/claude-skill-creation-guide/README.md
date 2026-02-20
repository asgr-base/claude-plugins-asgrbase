# claude-skill-creation-guide

Comprehensive guide for designing, implementing, and evaluating Claude Code Agent Skills.

## What It Does

Provides the full lifecycle of skill development: from Progressive Disclosure design to evaluation-driven iteration. Includes automation scripts for initialization, validation, and packaging.

## Key Topics

- **Progressive Disclosure** — Level 1 (name/description), Level 2 (SKILL.md), Level 3+ (reference files)
- **YAML Frontmatter** — Required fields (name, description) and constraints
- **Workflow Phases** — Initialize → Design → Validate → Package → Evaluate
- **Evaluation-Driven Development** — Gap identification, test scenarios, Two-Instance pattern
- **Code Skills** — Executable scripts with error handling
- **Claude Code Integration** — Hooks, Subagents, model selection

## Usage

```
/claude-skill-creation-guide
```

Use when creating new skills or improving existing ones.

## Scripts

```bash
# Initialize a new skill
python3 scripts/init_skill.py my-new-skill --path ~/.claude/skills

# Validate skill structure
python3 scripts/quick_validate.py ~/.claude/skills/my-new-skill

# Package for distribution
python3 scripts/package_skill.py ~/.claude/skills/my-new-skill ./dist
```

## File Structure

```
claude-skill-creation-guide/
├── SKILL.md                  # Main guide
├── QUICK-START.md            # Beginner quick start
├── PROGRESSIVE-DISCLOSURE.md # Progressive Disclosure details
├── WORKFLOWS.md              # Workflow and feedback loops
├── CODE-SKILLS.md            # Executable code skills
├── EVALUATION.md             # Evaluation and iteration
├── PATTERNS.md               # Common patterns
├── PLATFORMS.md              # Platform-specific notes
└── scripts/
    ├── init_skill.py         # Skill scaffolding
    ├── quick_validate.py     # Structure validation
    └── package_skill.py      # .skill packaging
```

## Requirements

- Python 3.10+
- PyYAML (`pip install pyyaml`)

## License

Apache 2.0
