# Agent instructions

How this repo is organised, and what must stay in sync when a skill changes. Read this before editing anything under `skills/`.

## Layout

```text
skills/<bucket>/<skill-name>/SKILL.md
```

The bucket describes maturity, not topic:

- Promoted buckets (`visuals/`, and later `engineering/`, `productivity/`, ...): shipped in the plugin, listed in both READMEs.
- `in-progress/`: public on purpose, feedback wanted. Linked locally, not shipped.
- `misc/`: kept around, rarely used, not promoted.
- `deprecated/`: retired. Not linked, not shipped.

Create a topical bucket when the first skill that belongs in it lands. Never commit an empty bucket.

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
- Every `SKILL.md` in `deprecated/` keeps its content; do not delete history to tidy up.

## Portability and privacy

Skills in this repo are public and shared across machines. They must not contain:

- absolute paths from a private machine, private hostnames, or internal URLs;
- credentials, tokens, or personal data;
- scratch output (`reports/`, `drafts/`, generated images). Keep only the small, illustrative assets a skill genuinely needs, and prefer text over binaries.

## Prose

Write plainly and in the active voice. State what to do, not how impressive it is. No emoji headers, no marketing adjectives, no "not only ... but also" padding. Prefer a concrete example over an abstract rule.
