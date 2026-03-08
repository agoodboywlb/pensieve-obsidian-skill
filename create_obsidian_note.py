import os
import re
import hashlib
import datetime
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(SCRIPT_DIR, "templates")

DEFAULT_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_TASK_TYPE = "note"


def _load_template(name):
    path = os.path.join(TEMPLATES_DIR, name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _block_ref_id(topic, date_str):
    """Generate a globally unique block reference ID."""
    raw = f"{topic}-{date_str}-{os.getpid()}-{datetime.datetime.now().timestamp()}"
    short_hash = hashlib.md5(raw.encode()).hexdigest()[:6]
    return f"^{topic}-{date_str}-{short_hash}"


def _resolve_vault(cli_vault):
    vault = cli_vault or os.environ.get("OBSIDIAN_VAULT")
    if not vault:
        raise SystemExit(
            "Error: vault path required. Use --vault or set OBSIDIAN_VAULT env var."
        )
    return os.path.expanduser(vault)


def _unique_detail_filename(details_dir, topic, date_str):
    """Collision-safe filename: topic-date.md, topic-date-2.md, topic-date-3.md, ..."""
    base = f"{topic}-{date_str}"
    filename = f"{base}.md"
    counter = 2
    while os.path.exists(os.path.join(details_dir, filename)):
        filename = f"{base}-{counter}.md"
        counter += 1
    return filename


def _update_frontmatter_date(content, date_str):
    """Update 'updated:' field in YAML frontmatter."""
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("updated:"):
            lines[i] = f"updated: {date_str}"
            break
    return "\n".join(lines)


def _upsert_index(index_path, project_name, topic, task_type, conclusion, date_str):
    """Create or update project Index — each topic shows latest metadata for quick retrieval."""
    topic_block = (
        f"\n### {topic}\n"
        f"- **Type**: {task_type} | **Updated**: {date_str}\n"
        f"- **Conclusion**: {conclusion}\n"
        f"- **Link**: [[{topic}/Summary]]\n"
    )

    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()

        content = _update_frontmatter_date(content, date_str)

        if f"### {topic}\n" in content:
            pattern = re.compile(
                rf"### {re.escape(topic)}\n"
                rf"- \*\*Type\*\*:.*\n"
                rf"- \*\*Conclusion\*\*:.*\n"
                rf"- \*\*Link\*\*:.*\n"
            )
            content = pattern.sub(
                f"### {topic}\n"
                f"- **Type**: {task_type} | **Updated**: {date_str}\n"
                f"- **Conclusion**: {conclusion}\n"
                f"- **Link**: [[{topic}/Summary]]\n",
                content,
            )
        else:
            content = content.rstrip() + topic_block

        with open(index_path, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        template = _load_template("Index.md")
        content = (
            template
            .replace("{{project_name}}", project_name)
            .replace("{{current_date}}", date_str)
            .replace("{{topic_entry}}", topic_block)
        )
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(content)


def _upsert_summary(summary_path, topic, project_name, conclusion, detail_filename,
                     block_ref, date_str):
    """Create or update Summary — always append entry, grouped by month (newest first)."""
    month_str = date_str[:7]  # "YYYY-MM"
    month_header = f"## {month_str}"

    entry = (
        f"\n### {date_str}\n"
        f"- **Conclusion**: {conclusion}\n"
        f"- ![[Details/{detail_filename[:-3]}#{block_ref}]]\n"
    )

    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            content = f.read()

        content = _update_frontmatter_date(content, date_str)

        if month_header in content:
            # Insert entry right after the month header line (newest entry at top of month)
            idx = content.index(month_header) + len(month_header)
            content = content[:idx] + entry + content[idx:]
        else:
            # New month — insert before the first existing ## YYYY-MM (newest month at top)
            first_month = re.search(r"\n## \d{4}-\d{2}", content)
            if first_month:
                pos = first_month.start()
                content = content[:pos] + f"\n{month_header}" + entry + content[pos:]
            else:
                content = content.rstrip() + f"\n\n{month_header}" + entry

        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        template = _load_template("L1-Summary.md")
        content = (
            template
            .replace("{{project_name}}", project_name)
            .replace("{{current_date}}", date_str)
            .replace("{{topic}}", topic)
        )
        content = content.rstrip() + f"\n\n{month_header}" + entry
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(content)


def create_obsidian_note(vault_path, project_name, topic, summary_data, detail_data,
                         date_fmt=DEFAULT_DATE_FORMAT):
    """
    Generate Index + Summary + Detail notes in an Obsidian vault.
    Always appends — never overwrites or skips existing content.

    Directory structure:
        {vault}/{project}/Index.md
        {vault}/{project}/{topic}/Summary.md
        {vault}/{project}/{topic}/Details/{topic}-{date}.md
    """
    assert "conclusion" in summary_data, "summary_data must contain 'conclusion'"
    for key in ("outcomes", "analysis", "todos"):
        assert key in detail_data, f"detail_data must contain '{key}'"

    project_dir = os.path.join(vault_path, project_name)
    topic_dir = os.path.join(project_dir, topic)
    details_dir = os.path.join(topic_dir, "Details")
    os.makedirs(details_dir, exist_ok=True)

    date_str = datetime.datetime.now().strftime(date_fmt)
    filename = _unique_detail_filename(details_dir, topic, date_str)
    block_ref = _block_ref_id(topic, date_str)
    task_type = detail_data.get("task_type", DEFAULT_TASK_TYPE)

    # 1. Write Detail (always new file)
    template = _load_template("L2-Detail.md")
    detail_content = (
        template
        .replace("{{topic}}", topic)
        .replace("{{project_name}}", project_name)
        .replace("{{task_type}}", task_type)
        .replace("{{current_date}}", date_str)
        .replace("{{block_ref_id}}", block_ref)
        .replace("{{bullet_points_of_outcomes}}", detail_data["outcomes"])
        .replace("{{detailed_analysis}}", detail_data["analysis"])
        .replace("{{todos}}", detail_data["todos"])
    )
    with open(os.path.join(details_dir, filename), "w", encoding="utf-8") as f:
        f.write(detail_content)

    # 2. Upsert Summary (always append entry)
    summary_path = os.path.join(topic_dir, "Summary.md")
    _upsert_summary(
        summary_path, topic, project_name,
        summary_data["conclusion"], filename, block_ref, date_str,
    )

    # 3. Upsert Index (update topic metadata to latest)
    index_path = os.path.join(project_dir, "Index.md")
    _upsert_index(
        index_path, project_name, topic, task_type,
        summary_data["conclusion"], date_str,
    )

    print(f"Notes generated at: {project_dir}")
    print(f"  Index:   Index.md")
    print(f"  Summary: {topic}/Summary.md")
    print(f"  Detail:  {topic}/Details/{filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Obsidian Index + Summary + Detail notes",
        epilog="Tip: set OBSIDIAN_VAULT env var to skip --vault every time.",
    )
    parser.add_argument("--vault", default=None,
                        help="Obsidian vault root path (or set OBSIDIAN_VAULT env var)")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--topic", required=True, help="Topic name")
    parser.add_argument("--task-type", default=DEFAULT_TASK_TYPE,
                        help=f"Task type tag (default: {DEFAULT_TASK_TYPE})")
    parser.add_argument("--date-format", default=DEFAULT_DATE_FORMAT,
                        help="Date format string (default: %%Y-%%m-%%d)")
    parser.add_argument("--conclusion", required=True, help="One-sentence summary")
    parser.add_argument("--outcomes", required=True, help="Key outcomes (bullet points)")
    parser.add_argument("--analysis", required=True, help="Detailed analysis text")
    parser.add_argument("--todos", required=True, help="Action items (markdown checklist)")

    args = parser.parse_args()
    vault = _resolve_vault(args.vault)

    create_obsidian_note(
        vault_path=vault,
        project_name=args.project,
        topic=args.topic,
        summary_data={"conclusion": args.conclusion},
        detail_data={
            "outcomes": args.outcomes,
            "analysis": args.analysis,
            "todos": args.todos,
            "task_type": args.task_type,
        },
        date_fmt=args.date_format,
    )
