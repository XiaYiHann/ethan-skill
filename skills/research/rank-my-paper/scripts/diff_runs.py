#!/usr/bin/env python3
"""Compare two rank-my-paper runs and separate manuscript change from peer-set change.

Usage: diff_runs.py OLD/ranking.json NEW/ranking.json
Also prints which peer reviews in OLD are reusable under NEW's rubric_version.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "CLI diff utility comparing consecutive rank-my-paper runs."


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _position(run: dict):
    interval = run.get("run", {}).get("rank_interval")
    if interval:
        return f"{interval['low']}-{interval['high']}"
    return run.get("our_paper_rank")


def _score(paper: dict):
    review = paper.get("independent_review")
    return review.get("score") if isinstance(review, dict) else None


def _peers(run: dict) -> dict:
    return {p["key"]: p for p in run.get("papers", []) if p.get("kind") != "target"}


def _target(run: dict) -> dict:
    return next((p for p in run.get("papers", []) if p.get("kind") == "target"), {})


def reusable(old: dict, rubric_version) -> list[str]:
    """Peer reviews read in full under the same rubric; the target is never reusable."""
    old_rubric = old.get("run", {}).get("rubric_version")
    keys = []
    for key, paper in _peers(old).items():
        review = paper.get("independent_review")
        if not isinstance(review, dict) or (paper.get("reading") or {}).get("mode") != "full_text":
            continue
        source_rubric = (review.get("reused_from") or {}).get("rubric_version", old_rubric)
        if rubric_version and source_rubric == rubric_version:
            keys.append(key)
    return sorted(keys)


def diff(old: dict, new: dict) -> dict:
    old_peers, new_peers = _peers(old), _peers(new)
    shared = sorted(old_peers.keys() & new_peers.keys())
    return {
        "manuscript_changed": old.get("run", {}).get("manuscript_sha256") != new.get("run", {}).get("manuscript_sha256"),
        "target_score": [_score(_target(old)), _score(_target(new))],
        "position": [_position(old), _position(new)],
        "peers_added": sorted(new_peers.keys() - old_peers.keys()),
        "peers_removed": sorted(old_peers.keys() - new_peers.keys()),
        "peers_shared": len(shared),
        "relation_changes": {
            k: [old_peers[k].get("relation_to_target"), new_peers[k].get("relation_to_target")]
            for k in shared
            if old_peers[k].get("relation_to_target") != new_peers[k].get("relation_to_target")
        },
        "peer_score_changes": {
            k: [_score(old_peers[k]), _score(new_peers[k])]
            for k in shared
            if _score(old_peers[k]) != _score(new_peers[k])
        },
        "reusable_from_old": reusable(old, new.get("run", {}).get("rubric_version")),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    args = parser.parse_args(argv)
    try:
        result = diff(_load(args.old), _load(args.new))
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"cannot compare runs: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
