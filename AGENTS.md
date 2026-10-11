# Agent instructions

How this repo is organised, and what must stay in sync when a skill changes. Read this before editing anything under `skills/`.

## Layout

```text
skills/<bucket>/<skill-name>/SKILL.md
```

There are two kinds of bucket, and a skill's bucket says which one it is in:

- **Topical, promoted**: `research/`, `visuals/`, and later `engineering/`, `productivity/`. Shipped in the plugin, listed in every README.
- **Maturity, never promoted**: `in-progress/` (public on purpose, feedback wanted), `misc/` (kept around, rarely used), `deprecated/` (retired).

Create a topical bucket when the first skill that belongs in it lands. Never commit an empty bucket. A skill moves between maturity buckets freely; moving between topical buckets is a rename and needs the sync steps below.

## Sync rules

When you add, rename, remove, or repurpose a skill:

1. `skills/<bucket>/README.md` lists it: one line, skill name linked to its `SKILL.md`.
2. The top-level `README.md` lists it the same way, grouped under the bucket, with a **Model-invoked** or **User-invoked** heading. Promoted buckets only.
3. `.claude-plugin/plugin.json`'s `skills` array contains `./skills/<bucket>/<name>`. Promoted buckets only.
4. `python3 scripts/validate_skills.py` passes. Run it before every commit; it checks all of the above against the files on disk.
5. Add a `CHANGELOG.md` entry and bump `version` in `.claude-plugin/plugin.json` when behaviour changes.

To (re)link every skill outside `deprecated/` and `misc/` into the local harness directories (`~/.claude/skills`, `~/.agents/skills`), run `scripts/link-skills.sh`. Entries are symlinks into this repo, so `git pull` keeps installed skills current. Re-run it after adding, renaming, or removing a skill.

## SKILL.md rules

- YAML frontmatter with `name` (identical to the folder name) and `description`.
- `description` says what the skill does and when to reach for it, third person, including the phrases a user or model would actually say. It is the only thing an agent sees before loading the skill, so vague descriptions mean the skill never fires.
- A skill is either model-invoked (default) or user-invoked: `disable-model-invocation: true` in the frontmatter plus `policy.allow_implicit_invocation: false` in `agents/openai.yaml`. User-invoked skills orchestrate; model-invoked skills hold reusable discipline.
- Keep `SKILL.md` short and put detail in sibling files under `references/`, linked by relative path. A skill that must be read in full before it does anything is a document, not a skill.
- Scripts a skill ships live in its own `scripts/`, take arguments rather than environment assumptions, and keep their tests next to them. A skill's scripts must run from a clean checkout with the standard library of the language they are written in, plus anything the skill itself documents.
- Every `SKILL.md` in `deprecated/` keeps its content; do not delete history to tidy up.

## Portability and privacy

Skills in this repo are public and shared across machines. They must not contain:

- absolute paths from a private machine, private hostnames, or internal URLs;
- credentials, tokens, or personal data;
- scratch output (`reports/`, `drafts/`, generated images, `.pytest_cache/`, `__pycache__/`). Keep only the small, illustrative assets a skill genuinely needs, and prefer text over binaries. README images live in `assets/` and stay under about 1 MB.

## Prose

Write plainly and in the active voice. State what to do, not how impressive it is. No emoji headers, no marketing adjectives, no "not only ... but also" padding. Prefer a concrete example over an abstract rule.
