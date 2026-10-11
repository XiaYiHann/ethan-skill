#!/usr/bin/env bash
set -euo pipefail

# Print every SKILL.md in the repo, repo-relative and sorted.

REPO="$(cd "$(dirname "$0")/.." && pwd)"

cd "$REPO"
find . -name SKILL.md -not -path '*/node_modules/*' | sed 's|^\./||' | sort
