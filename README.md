# Pensieve Obsidian Skill

**[English](README.md)** | [中文](README.zh-CN.md)

A Pensieve for your AI agents — externalize knowledge into a structured Obsidian vault with **Index -> Summary -> Detail** hierarchy. Append-only, agent-retrievable, zero dependencies.

## Why This Skill?

AI agents (Claude Code, Cursor, Codex, etc.) are powerful but **stateless** — each session starts from scratch, and each agent has its own isolated memory. When you run multiple agents in parallel across projects, knowledge fragments scatter across conversations and vanish when sessions end.

This skill solves the problem by **externalizing agent knowledge to a local Obsidian vault**:

- **Persistent**: conversation insights, decisions, and analysis are archived to disk, surviving session resets and context window limits
- **Shared**: any agent can read the same vault directory — knowledge produced by Agent A is immediately available to Agent B
- **Retrievable**: the three-layer Index -> Summary -> Detail structure lets agents locate relevant context in 1-3 file reads instead of re-deriving from scratch
- **Evolving**: append-only design means knowledge accumulates over time — agents build on previous sessions rather than repeating work

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│  Agent A │  │  Agent B │  │  Agent C │
└─────┬────┘  └─────┬────┘  └─────┬────┘
      │             │             │
    write      read/write       read
      │             │             │
      ▼             ▼             ▼
┌──────────────────────────────────────────┐
│          Obsidian Vault (local)          │
│    Index  ──>  Summary  ──>  Detail      │
└──────────────────────────────────────────┘
```

In practice: after a deep debugging session, one agent archives its findings. Days later, a different agent working on a related issue reads the Index, finds the relevant topic, and picks up exactly where the first agent left off — no repeated analysis, no lost context.

## Features

- **Three-layer structure**: Index (project) -> Summary (topic, grouped by month) -> Detail (session)
- **Append-only**: never overwrites or skips — same topic, same day, similar content all get appended
- **Same-day collision safe**: auto-increments filename (`topic-date-2.md`, `-3.md`, ...)
- **Agent-friendly Index**: each topic shows type/conclusion/date for quick retrieval
- **Customizable templates**: edit `obsidian-note/templates/*.md` to match your vault style
- **Zero dependencies**: Python 3.6+ standard library only

## Quick Start

```bash
# 1. Clone
git clone https://github.com/agoodboywlb/pensieve-obsidian-skill.git
cd pensieve-obsidian-skill

# 2. Install skill (copy to Claude Code skills path)
cp -r obsidian-note ~/.claude/skills/

# 3. Set your vault path
export OBSIDIAN_VAULT=~/ObsidianVault
```

Then use trigger keywords in your conversation:

> "archive note: Sprint-Review meeting — shipped v2.0 auth module on time"

The agent will follow SKILL.md to generate Index / Summary / Detail files automatically.

## Project Structure

```
pensieve-obsidian-skill/
├── README.md
├── README.zh-CN.md
├── LICENSE
└── obsidian-note/                  <- Skill directory (copy to ~/.claude/skills/)
    ├── SKILL.md
    ├── create_obsidian_note.py
    └── templates/
        ├── Index.md
        ├── L1-Summary.md
        ├── L2-Detail.md
        └── CONTEXT.md
```

## Generated Structure

```
ObsidianVault/
  MyProject/
    Index.md                              <- Project index (agent entry point)
    CONTEXT.md                            <- Cross-agent memory (auto-generated)
    Sprint-Review/
      Summary.md                          <- Entries grouped by month
      Details/
        Sprint-Review-2026-03-08.md       <- Full record
        Sprint-Review-2026-03-08-2.md     <- Same-day append (auto-increment)
    API-Design/
      Summary.md
      Details/
        API-Design-2026-03-09.md
```

Navigation: `Index` -> `{topic}/Summary` -> `Details/{date}` (each layer has `up:` backlink)

## Output Examples

### Index.md — Project-level entry point

```markdown
---
type: index
project: "MyProject"
updated: 2026-03-08
---
# MyProject

## Topics

### Sprint-Review
- **Type**: meeting | **Updated**: 2026-03-08
- **Conclusion**: Shipped v2.0 auth module on time
- **Link**: [[Sprint-Review/Summary]]

### API-Design
- **Type**: decision | **Updated**: 2026-03-09
- **Conclusion**: gRPC for internal, REST for public
- **Link**: [[API-Design/Summary]]
```

### Summary.md — Topic-level, grouped by month

```markdown
---
up: "[[../Index]]"
type: summary
project: "[[MyProject]]"
updated: 2026-03-15
---
# Sprint-Review

## 2026-03
### 2026-03-15
- **Conclusion**: Hotfix for token refresh bug
- ![[Details/Sprint-Review-2026-03-15#^Sprint-Review-2026-03-15-a1b2c3]]

### 2026-03-08
- **Conclusion**: Shipped v2.0 auth module on time
- ![[Details/Sprint-Review-2026-03-08#^Sprint-Review-2026-03-08-d4e5f6]]

## 2026-02
### 2026-02-22
- **Conclusion**: Sprint planning for auth module
- ![[Details/Sprint-Review-2026-02-22#^Sprint-Review-2026-02-22-g7h8i9]]
```

### Detail — Full session record

```markdown
---
up: "[[../Summary]]"
type: detail
project: "MyProject"
tags: [work/MyProject, task/meeting]
created: 2026-03-08
---
# Sprint-Review — 2026-03-08

## Key Outcomes ^Sprint-Review-2026-03-08-d4e5f6
- OAuth2 PKCE flow implemented
- Token refresh tested

## Analysis
Compared session vs JWT, chose JWT for stateless scaling...

## Action Items
- [ ] Write migration guide
- [ ] Update API docs
```

## Agent Retrieval Flow

An agent (e.g., Claude Code) can locate relevant content in 1-3 file reads:

1. **Read `Index.md`** — scan topic type/conclusion/date to identify the target topic
2. **Read `{topic}/Summary.md`** — find the relevant month and entry by conclusion text
3. **Read `Details/{date}.md`** only when full context is needed

This avoids scanning every file in the vault.

## Configuration

| Option | CLI Flag | Env Var | Default |
|--------|----------|---------|---------|
| Vault path | `--vault` | `OBSIDIAN_VAULT` | *(required)* |
| Task type | `--task-type` | — | `note` |
| Date format | `--date-format` | — | `%Y-%m-%d` |

## Customizing Templates

Edit files in `obsidian-note/templates/` to change note structure, frontmatter fields, or tag conventions.

| Template | Purpose |
|----------|---------|
| `obsidian-note/templates/Index.md` | Project index skeleton |
| `obsidian-note/templates/L1-Summary.md` | Topic summary skeleton |
| `obsidian-note/templates/L2-Detail.md` | Detail note with frontmatter and sections |
| `obsidian-note/templates/CONTEXT.md` | Cross-agent memory summary (auto-generated) |

Placeholders use `{{variable_name}}` syntax. Month grouping and append logic are handled by the script, not templates.

## Agent Integration

### Install Skill (Claude Code)

```bash
cp -r obsidian-note ~/.claude/skills/
```

Triggered by keywords: `archive note`, `obsidian archive`, `obsidian 归档`, `三层归档`.

### Cross-Agent Memory Bootstrap

After archiving, the skill auto-generates `{project}/CONTEXT.md` — a condensed memory file containing key conclusions and open action items from your vault. Add the following bootstrap block to your agent's config file:

```
# Project Memory Guide
1. **Bootstrap**: Always `cat {vault_path}/{project}/CONTEXT.md` at the start of a session.
2. **Knowledge Retrieval**: Use CONTEXT.md as the map to find relevant Summary/Detail files.
3. **Task Alignment**: Sync current progress with "Open Action Items" in CONTEXT.md.
```

| Agent | Config File |
|-------|------------|
| Claude Code | `CLAUDE.md` (project root) |
| Codex | `AGENTS.md` or `codex.md` |
| Gemini CLI | `GEMINI.md` |
| Cursor | `.cursor/rules/*.mdc` |
| OpenCode | `AGENTS.md` |

No MCP server, no plugin — just a plain text file that any agent reads natively.

### Example: CONTEXT.md

```markdown
---
type: context
project: "MyProject"
updated: 2026-03-08
---
# MyProject — Project Memory

## Key Decisions & Conclusions

### Sprint-Review
- **Conclusion**: Shipped v2.0 auth module on time | **Updated**: 2026-03-08

### API-Design
- **Conclusion**: gRPC for internal, REST for public | **Updated**: 2026-03-09

## Open Action Items

- [ ] Write migration guide *(Sprint-Review, 2026-03-08)*
- [ ] Update API docs *(Sprint-Review, 2026-03-08)*
```

## License

MIT
