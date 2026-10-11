#!/usr/bin/env bash
set -euo pipefail

# Dev-only helper for this repo's maintainer. Not an installer.
#
# Symlinks every skill in the repo into the local skill directories each harness
# reads, so a single `git pull` keeps the installed skills current:
#   ~/.claude/skills  Claude Code
#   ~/.agents/skills  Codex, Pi, and other Agent Skills compatible harnesses
#
# `misc/` (kept, not promoted) and `deprecated/` (retired) are skipped, same as
# everywhere else non-promoted skills are kept out. `in-progress/` is linked on
# purpose: a local install is where that feedback loop runs.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DESTS=("$HOME/.claude/skills" "$HOME/.agents/skills")

names=()
srcs=()
while IFS= read -r -d '' skill_md; do
  src="$(dirname "$skill_md")"
  names+=("$(basename "$src")")
  srcs+=("$src")
done < <(find "$REPO/skills" -name SKILL.md -not -path '*/misc/*' -not -path '*/deprecated/*' -print0)

if [ "${#names[@]}" -eq 0 ]; then
  echo "no skills found under $REPO/skills" >&2
  exit 1
fi

for DEST in "${DESTS[@]}"; do
  # Guard against writing the per-skill symlinks back into the repo's own tree
  # when the destination itself is a symlink into the repo.
  if [ -L "$DEST" ]; then
    resolved="$(readlink -f "$DEST")"
    case "$resolved" in
      "$REPO"|"$REPO"/*)
        echo "error: $DEST is a symlink into this repo ($resolved)." >&2
        echo "Remove it (rm \"$DEST\") and re-run; the script recreates it as a real directory." >&2
        exit 1
        ;;
    esac
  fi

  mkdir -p "$DEST"

  for i in "${!names[@]}"; do
    name="${names[$i]}"
    src="${srcs[$i]}"
    target="$DEST/$name"

    if [ -e "$target" ] && [ ! -L "$target" ]; then
      rm -rf "$target"
    fi

    ln -sfn "$src" "$target"
    echo "linked $name -> $src ($DEST)"
  done
done
