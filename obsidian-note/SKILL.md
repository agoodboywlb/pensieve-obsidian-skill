---
name: obsidian-note-expert
description: >
  Obsidian Knowledge Architect based on Progressive Summarization.
  Generates three-layer structure: Index -> Summary -> Detail.
  Always appends, never overwrites.
triggers:
  - archive note
  - obsidian archive
  - obsidian 归档
  - 三层归档
---

# Role: Obsidian Knowledge Architect

## 1. Storage Logic (Index -> Summary -> Detail)

```
vault/{project}/
├── Index.md                         <- Project index (agent reads this first)
├── CONTEXT.md                       <- Cross-agent memory file (auto-generated)
└── {topic}/
    ├── Summary.md                   <- Entries grouped by month, newest first
    └── Details/
        ├── {topic}-2026-03-08.md
        ├── {topic}-2026-03-08-2.md  <- Same-day collision: auto-increment
        └── {topic}-2026-03-15.md
```

Agent retrieval flow: read `Index.md` -> locate topic by type/conclusion -> drill into `Summary.md` -> read specific `Detail` if needed.

## 2. Append-Only Rules

- **Detail**: always creates a new file (same-day: `-2`, `-3`, ...)
- **Summary**: always appends entry under month group, never skips similar content
- **Index**: updates topic metadata (latest conclusion/date) for quick scanning; history preserved in Summary

## 3. Configuration

| Config | CLI Flag | Env Var | Default |
|--------|----------|---------|---------|
| Vault path | `--vault` | `OBSIDIAN_VAULT` | *(required)* |
| Task type | `--task-type` | — | `note` |
| Date format | `--date-format` | — | `%Y-%m-%d` |

Templates in `templates/` can be freely customized:
- `templates/Index.md` — Project index
- `templates/L1-Summary.md` — Topic summary
- `templates/L2-Detail.md` — Detail note
- `templates/CONTEXT.md` — Cross-agent memory summary

## 4. Cross-Agent Memory: CONTEXT.md

After each archive operation, the skill **auto-generates** `{project}/CONTEXT.md` — a condensed memory file distilled from `Index.md`.

### What goes into CONTEXT.md
- Each topic's **latest conclusion** and **date** (one line per topic)
- **Open action items** collected from the most recent Detail of each topic
- Total ≤ 150 lines to fit agent context limits

### How agents consume it
Add the following bootstrap block to the agent's config file:

```
# Project Memory Guide
1. **Bootstrap**: Always `cat {vault}/{project}/CONTEXT.md` at the start of a session.
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

This makes archived knowledge available to **any agent** on first message — no MCP, no plugin, no extra setup.

## 5. Usage Example

```bash
export OBSIDIAN_VAULT=~/ObsidianVault
python create_obsidian_note.py \
  --project AI-Project \
  --topic Protocol-Design \
  --task-type meeting \
  --conclusion "Decided on gRPC over REST for internal services" \
  --outcomes "- gRPC chosen for latency\n- REST kept for public API" \
  --analysis "Compared latency, DX, and ecosystem support..." \
  --todos "- [ ] Draft .proto files\n- [ ] Setup envoy proxy"
```
