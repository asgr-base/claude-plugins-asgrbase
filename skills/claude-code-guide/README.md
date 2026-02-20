# claude-code-guide

Comprehensive guide to Claude Code features, configuration, and best practices.

## What It Does

Provides practical guidance on Claude Code's core components based on extensive hands-on experience. Covers Skills, Hooks, Subagents, MCPs, Plugins, context management, token optimization, and parallelization patterns.

## Key Topics

- **Skills & Commands** — Reusable workflows and slash commands
- **Hooks** — Lifecycle automation (PreToolUse, PostToolUse, UserPromptSubmit, Stop, etc.)
- **Subagents** — Task delegation for context savings
- **MCPs** — Model Context Protocol integrations
- **Plugins** — Bundled Skills + MCP + Hooks packages
- **Context Management** — Session persistence, strategic compaction
- **Token Optimization** — Model selection, efficient tool usage
- **Parallelization** — Fork, Git worktrees, concurrent agents

## Usage

```
/claude-code-guide
```

Ask any question about Claude Code features or configuration.

## File Structure

```
claude-code-guide/
├── SKILL.md          # Main guide (overview + quick reference)
├── BASICS.md         # Skills, Hooks, Subagents, MCPs, Plugins
├── ADVANCED.md       # Context management, token optimization
├── EXAMPLES.md       # Configuration examples
└── PATTERNS.md       # Best practice patterns
```

## Requirements

- Claude Code CLI

## License

Apache 2.0
