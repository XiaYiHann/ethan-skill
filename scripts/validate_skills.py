#!/usr/bin/env python3
"""Check that the skills on disk, the READMEs, and the plugin manifest agree.

Run from anywhere:

    python3 scripts/validate_skills.py

Checked rules:

1. Every `skills/<bucket>/<skill>/SKILL.md` starts with YAML frontmatter
   containing a non-empty `name` and `description`.
2. `name` matches the folder name.
3. Promoted skills (bucket outside `misc/`, `in-progress/`, `deprecated/`) are
   listed in `.claude-plugin/plugin.json` and linked from the top-level README.
4. `.claude-plugin/plugin.json` lists no missing or non-promoted skill.
5. Every bucket has a `README.md` that links each of its skills.
6. `SKILL.md` stays under `MAX_SKILL_LINES` lines.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
PLUGIN_MANIFEST = ROOT / ".claude-plugin" / "plugin.json"
TOP_README = ROOT / "README.md"

NON_PROMOTED_BUCKETS = {"misc", "in-progress", "deprecated"}
MAX_SKILL_LINES = 250

problems: list[str] = []


def problem(message: str) -> None:
    problems.append(message)


def read_frontmatter(path: Path) -> tuple[dict[str, str] | None, str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            front: dict[str, str] = {}
            for line in lines[1:index]:
                if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
                    continue
                key, _, value = line.partition(":")
                front[key.strip()] = value.strip().strip('"').strip("'")
            return front, text
    return None, text


def discover_skills() -> list[tuple[str, str, Path]]:
    found: list[tuple[str, str, Path]] = []
    for skill_md in sorted(SKILLS_DIR.glob("*/*/SKILL.md")):
        found.append((skill_md.parent.parent.name, skill_md.parent.name, skill_md))
    return found


def check_frontmatter(bucket: str, name: str, skill_md: Path) -> None:
    front, text = read_frontmatter(skill_md)
    relative = skill_md.relative_to(ROOT)
    if front is None:
        problem(f"{relative}: missing YAML frontmatter")
        return
    declared = front.get("name", "")
    if not declared:
        problem(f"{relative}: frontmatter has no name")
    elif declared != name:
        problem(f"{relative}: frontmatter name '{declared}' does not match folder '{name}'")
    if not front.get("description"):
        problem(f"{relative}: frontmatter has no description")
    line_count = len(text.splitlines())
    if line_count > MAX_SKILL_LINES:
        problem(f"{relative}: {line_count} lines, over the {MAX_SKILL_LINES} line budget")


def check_plugin_manifest(skills: list[tuple[str, str, Path]]) -> set[str]:
    if not PLUGIN_MANIFEST.is_file():
        problem(f"{PLUGIN_MANIFEST.relative_to(ROOT)}: missing")
        return set()
    manifest = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    listed = manifest.get("skills", [])
    promoted = {
        f"./skills/{bucket}/{name}": (bucket, name)
        for bucket, name, _ in skills
        if bucket not in NON_PROMOTED_BUCKETS
    }
    for entry in listed:
        if entry not in promoted:
            problem(f"plugin.json lists '{entry}', which is missing or not in a promoted bucket")
    for entry, (bucket, name) in promoted.items():
        if entry not in listed:
            problem(f"plugin.json does not list the promoted skill '{entry}'")
    return set(listed)


def check_readmes(skills: list[tuple[str, str, Path]]) -> None:
    top = TOP_README.read_text(encoding="utf-8") if TOP_README.is_file() else ""
    if not top:
        problem("README.md: missing")
    buckets = sorted({bucket for bucket, _, _ in skills})
    for bucket in buckets:
        bucket_readme = SKILLS_DIR / bucket / "README.md"
        if not bucket_readme.is_file():
            problem(f"skills/{bucket}/README.md: missing")
            continue
        bucket_text = bucket_readme.read_text(encoding="utf-8")
        for skill_bucket, name, _ in skills:
            if skill_bucket != bucket:
                continue
            link = f"./{name}/SKILL.md"
            if link not in bucket_text:
                problem(f"skills/{bucket}/README.md: does not link {link}")
            top_link = f"./skills/{bucket}/{name}/SKILL.md"
            if bucket in NON_PROMOTED_BUCKETS:
                continue
            if top_link not in top:
                problem(f"README.md: does not link {top_link}")


def main() -> int:
    skills = discover_skills()
    if not skills:
        problem("skills/: no SKILL.md found")
    for bucket, name, skill_md in skills:
        check_frontmatter(bucket, name, skill_md)
    check_plugin_manifest(skills)
    check_readmes(skills)

    if problems:
        print(f"validate_skills: {len(problems)} problem(s)")
        for item in problems:
            print(f"  - {item}")
        return 1
    print(f"validate_skills: OK ({len(skills)} skill(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
