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
├── Index.md                         <- Project index + cross-agent memory (agent reads this first)
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
- **Index**: updates topic metadata (latest conclusion/date) and aggregates open action items for quick scanning; history preserved in Summary

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

## 4. Cross-Agent Memory

Index.md doubles as the cross-agent memory file. After each archive, append an `## Open Action Items` section at the bottom of Index.md, aggregating uncompleted todos from the latest Detail of each topic. Any agent can read Index.md to get both the knowledge map and pending tasks in a single file read.

## 5. How to Archive (IMPORTANT)

**Always use the script** — do NOT manually create files with Write/Edit tools. One command generates all three layers + aggregates action items:

```bash
python3 ~/.claude/skills/obsidian-note/create_obsidian_note.py \
  --project "{project}" \
  --topic "{topic}" \
  --task-type "{type}" \
  --conclusion "{one-line summary}" \
  --outcomes "{bullet list of key outcomes}" \
  --analysis "{detailed analysis}" \
  --todos "{markdown checklist of action items}"
```

Vault path is read from `OBSIDIAN_VAULT` env var. If not set, add `--vault {path}`.
