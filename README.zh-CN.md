# Pensieve Obsidian Skill

[English](README.md) | **[中文](README.zh-CN.md)**

AI Agent 的冥想盆 — 将知识外置到结构化的 Obsidian Vault，支持 **索引 -> 摘要 -> 详情** 三层检索。仅追加、agent 可检索、零依赖。

## 为什么需要这个 Skill？

AI Agent（Claude Code、Cursor、Codex 等）能力强大，但本质上是**无状态**的 —— 每次会话从零开始，且各 agent 的记忆彼此隔离。当你日常开启多个 agent 并行协作时，知识碎片散落在各个对话中，会话结束即消失。

本 Skill 通过**将 agent 知识外置到本地 Obsidian Vault** 来解决这个问题：

- **持久化**：对话中的洞察、决策、分析归档到磁盘，不受会话重置和上下文窗口限制
- **跨 Agent 共享**：任何 agent 都能读取同一个 vault 目录 —— Agent A 产出的知识，Agent B 立即可用
- **结构化检索**：三层 索引 -> 摘要 -> 详情 结构，让 agent 仅需 1-3 次文件读取即可定位目标内容
- **渐进进化**：append-only 设计使知识随时间积累，agent 在前序成果上继续推进而非重复劳动

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

实际场景：一次深度 debug 后，agent 将发现归档。数天后，另一个 agent 处理相关问题时读取 Index，找到对应 topic，直接在前次分析的基础上继续 —— 无需重复推导、零上下文丢失。

## 特性

- **三层结构**：索引（项目级）-> 摘要（主题级，按月分组）-> 详情（单次会话）
- **仅追加**：永不覆盖或跳过 —— 同 topic、同日、相似内容均追加保存
- **同日防碰撞**：文件名自动递增（`topic-date-2.md`、`-3.md`、...）
- **Agent 友好索引**：每个 topic 带 type/conclusion/date，便于快速检索
- **可定制模板**：编辑 `obsidian-note/templates/*.md` 适配你的 vault 风格
- **零依赖**：仅需 Python 3.6+ 标准库

## 快速开始

```bash
# 1. 克隆
git clone https://github.com/agoodboywlb/pensieve-obsidian-skill.git
cd pensieve-obsidian-skill

# 2. 安装 Skill（复制到 Claude Code skills 路径）
cp -r obsidian-note ~/.claude/skills/

# 3. 设置 vault 路径
export OBSIDIAN_VAULT=~/ObsidianVault
```

然后在对话中使用触发关键词：

> "archive note：Sprint-Review 会议 —— v2.0 认证模块按时交付"

Agent 会按照 SKILL.md 的指引自动生成 Index / Summary / Detail 文件。

**希望其他 Agent（Codex、Gemini、Cursor）也能共享这些知识？** 参见 [跨 Agent 记忆引导](#跨-agent-记忆引导)，只需将它们指向 Index.md。

## 项目结构

```
pensieve-obsidian-skill/
├── README.md
├── README.zh-CN.md
├── LICENSE
└── obsidian-note/                  <- Skill 目录（复制到 ~/.claude/skills/）
    ├── SKILL.md
    ├── create_obsidian_note.py
    └── templates/
        ├── Index.md
        ├── L1-Summary.md
        └── L2-Detail.md
```

## 生成结构

```
ObsidianVault/
  MyProject/
    Index.md                              <- 项目索引 + 跨 Agent 记忆（agent 检索入口）
    Sprint-Review/
      Summary.md                          <- 按月分组的摘要条目
      Details/
        Sprint-Review-2026-03-08.md       <- 完整记录
        Sprint-Review-2026-03-08-2.md     <- 同日追加（自动递增）
    API-Design/
      Summary.md
      Details/
        API-Design-2026-03-09.md
```

导航路径：`Index` -> `{topic}/Summary` -> `Details/{date}`（每层通过 `up:` 反向链接回溯）

## 输出示例

### Index.md — 项目级入口

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
- **Conclusion**: v2.0 认证模块按时交付
- **Link**: [[Sprint-Review/Summary]]

### API-Design
- **Type**: decision | **Updated**: 2026-03-09
- **Conclusion**: 内部用 gRPC，外部用 REST
- **Link**: [[API-Design/Summary]]

## Open Action Items

- [ ] 编写迁移指南 *(Sprint-Review, 2026-03-08)*
- [ ] 更新 API 文档 *(Sprint-Review, 2026-03-08)*
```

### Summary.md — 主题级，按月分组

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
- **Conclusion**: 修复 token 刷新 bug
- ![[Details/Sprint-Review-2026-03-15#^Sprint-Review-2026-03-15-a1b2c3]]

### 2026-03-08
- **Conclusion**: v2.0 认证模块按时交付
- ![[Details/Sprint-Review-2026-03-08#^Sprint-Review-2026-03-08-d4e5f6]]

## 2026-02
### 2026-02-22
- **Conclusion**: 认证模块 Sprint 规划
- ![[Details/Sprint-Review-2026-02-22#^Sprint-Review-2026-02-22-g7h8i9]]
```

### Detail — 完整会话记录

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
- OAuth2 PKCE 流程已实现
- Token 刷新已测试

## Analysis
对比了 session 与 JWT，选择 JWT 以支持无状态扩展...

## Action Items
- [ ] 编写迁移指南
- [ ] 更新 API 文档
```

## Agent 检索流程

Agent（如 Claude Code）可通过 1-3 次文件读取定位内容：

1. **读取 `Index.md`** — 通过 type/conclusion/date 定位目标 topic
2. **读取 `{topic}/Summary.md`** — 按月份和摘要找到相关条目
3. **读取 `Details/{date}.md`** — 仅在需要完整上下文时深入

避免遍历 vault 中的所有文件。

## 配置

| 选项 | CLI 参数 | 环境变量 | 默认值 |
|------|----------|----------|--------|
| Vault 路径 | `--vault` | `OBSIDIAN_VAULT` | *（必填）* |
| 任务类型 | `--task-type` | — | `note` |
| 日期格式 | `--date-format` | — | `%Y-%m-%d` |

## 自定义模板

编辑 `obsidian-note/templates/` 中的文件以调整笔记结构、frontmatter 字段或标签规则。

| 模板 | 用途 |
|------|------|
| `obsidian-note/templates/Index.md` | 项目索引骨架 |
| `obsidian-note/templates/L1-Summary.md` | 主题摘要骨架 |
| `obsidian-note/templates/L2-Detail.md` | 详情笔记（含 frontmatter 和章节） |

占位符使用 `{{variable_name}}` 语法。月份分组和追加逻辑由脚本处理，不在模板中。

## Agent 集成

### 安装 Skill（Claude Code）

```bash
cp -r obsidian-note ~/.claude/skills/
```

通过关键词触发：`archive note`、`obsidian archive`、`obsidian 归档`、`三层归档`。

### 跨 Agent 记忆引导

`Index.md` 同时充当项目地图和跨 Agent 记忆文件。在 agent 的配置文件中加入以下 bootstrap 块，即可在每次新对话时自动加载：

```
# Project Memory Guide
1. **Bootstrap**: 每次新对话启动时，先读取 `cat {vault_path}/{project}/Index.md`。
2. **Knowledge Retrieval**: 以 Index.md 为地图，按需定位 Summary/Detail 文件。
3. **Task Alignment**: 对齐 Index.md 中的 "Open Action Items"，同步当前进度。
```

| Agent | 配置文件 |
|-------|---------|
| Claude Code | `CLAUDE.md`（项目根目录） |
| Codex | `AGENTS.md` 或 `codex.md` |
| Gemini CLI | `GEMINI.md` |
| Cursor | `.cursor/rules/*.mdc` |
| OpenCode | `AGENTS.md` |

无需 MCP Server、无需插件 —— 只是一个纯文本文件，任何 agent 都能原生读取。

## 许可证

MIT
