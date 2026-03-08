---
name: obsidian-note-expert
description: >
  Obsidian Knowledge Architect based on Progressive Summarization.
  Generates three-layer structure: Index -> Summary -> Detail.
  Always appends, never overwrites.
triggers:
  - obsidian
  - knowledge card
  - archive note
---

# Role: Obsidian Knowledge Architect

## 1. Storage Logic (Index -> Summary -> Detail)

```
vault/{project}/
├── Index.md                         <- Project index (agent reads this first)
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

## 4. Usage Example

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
