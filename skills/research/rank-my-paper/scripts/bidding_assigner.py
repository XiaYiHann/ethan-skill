#!/usr/bin/env python3
"""Area Chair (AC) multi-reviewer two-round bidding and quota-balanced assignment solver.

Simulates and executes conference-grade reviewer bidding and assignment (e.g. OpenReview / TPMS)
to select top representative peer papers and balance workload across sub-agents.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Deterministic CLI solver for two-round AC-reviewer paper bidding and capacity-balanced assignment."

BID_WEIGHTS = {
    "very_high": 5.0,
    "high": 4.0,
    "neutral": 3.0,
    "low": 1.0,
    "conflict": -100.0,
}


@dataclass
class PaperCandidate:
    id: str
    title: str
    venue: str
    abstract: str
    primary_area: str
    year: int = 0
    score_round1: float = 0.0


@dataclass
class ReviewerProfile:
    id: str
    name: str
    areas: list[str]
    capacity: int = 3


def compute_affinity(reviewer: ReviewerProfile, paper: PaperCandidate) -> float:
    """Calculate semantic/area affinity between a reviewer and a paper candidate."""
    paper_tokens = set(paper.primary_area.lower().split() + paper.title.lower().split())
    matches = 0
    for area in reviewer.areas:
        for token in area.lower().split():
            if token in paper_tokens:
                matches += 1
    return min(1.0, matches * 0.3)


def round1_coarse_bidding(
    papers: list[PaperCandidate],
    reviewers: list[ReviewerProfile],
    bids: dict[str, dict[str, str]],  # reviewer_id -> paper_id -> bid_label
    shortlist_size: int = 25,
    min_year: int | None = None,
) -> list[PaperCandidate]:
    """Round 1: Filter by recency gate (min_year) and aggregate bids to prune the pool into a shortlist."""
    if min_year is not None:
        papers = [p for p in papers if p.year == 0 or p.year >= min_year]

    for paper in papers:
        scores = []
        for rev in reviewers:
            bid_label = bids.get(rev.id, {}).get(paper.id, "neutral")
            bid_score = BID_WEIGHTS.get(bid_label.lower(), 3.0)
            if bid_score < 0:
                continue
            affinity = compute_affinity(rev, paper)
            combined = bid_score + (affinity * 2.0)
            scores.append(combined)

        paper.score_round1 = sum(scores) / len(scores) if scores else 0.0

    # Sort descending by aggregated score
    sorted_papers = sorted(papers, key=lambda p: p.score_round1, reverse=True)
    return sorted_papers[:shortlist_size]


def round2_assignment_solver(
    shortlist: list[PaperCandidate],
    reviewers: list[ReviewerProfile],
    bids: dict[str, dict[str, str]],
    target_paper_count: int = 15,
    coverage_per_paper: int = 2,
    max_capacity_per_reviewer: int = 3,
) -> dict[str, Any]:
    """Round 2: Select exact target_paper_count papers and solve max-weight bipartite matching with capacities."""
    n_papers = min(len(shortlist), target_paper_count)
    selected_papers = shortlist[:n_papers]

    # Build cost/utility matrix for (reviewer, paper)
    cost_matrix: dict[tuple[str, str], float] = {}
    for rev in reviewers:
        for paper in selected_papers:
            bid_label = bids.get(rev.id, {}).get(paper.id, "neutral")
            bid_val = BID_WEIGHTS.get(bid_label.lower(), 3.0)
            affinity = compute_affinity(rev, paper)
            cost_matrix[(rev.id, paper.id)] = bid_val + (affinity * 2.0)

    # Greedy maximum weight matching with degree/capacity constraints
    assignment: dict[str, list[str]] = {rev.id: [] for rev in reviewers}  # reviewer -> [paper_ids]
    paper_coverage: dict[str, list[str]] = {p.id: [] for p in selected_papers}  # paper -> [reviewer_ids]

    edges = []
    for (r_id, p_id), weight in cost_matrix.items():
        if weight > 0:  # exclude conflicts
            edges.append((weight, r_id, p_id))

    # Sort edges by descending weight
    edges.sort(key=lambda x: x[0], reverse=True)

    # Multi-pass matching to satisfy coverage_per_paper
    for weight, r_id, p_id in edges:
        if (
            len(paper_coverage[p_id]) < coverage_per_paper
            and len(assignment[r_id]) < max_capacity_per_reviewer
            and p_id not in assignment[r_id]
        ):
            assignment[r_id].append(p_id)
            paper_coverage[p_id].append(r_id)

    # Fallback backfill if any paper is under-covered
    for p_id, assigned_revs in paper_coverage.items():
        if len(assigned_revs) < coverage_per_paper:
            available_reviewers = [
                r for r in reviewers
                if len(assignment[r.id]) < max_capacity_per_reviewer and p_id not in assignment[r.id]
            ]
            available_reviewers.sort(key=lambda r: cost_matrix.get((r.id, p_id), 0.0), reverse=True)
            for rev in available_reviewers:
                if len(paper_coverage[p_id]) >= coverage_per_paper:
                    break
                assignment[rev.id].append(p_id)
                paper_coverage[p_id].append(rev.id)

    total_assignments = sum(len(papers) for papers in assignment.values())
    total_needed = n_papers * coverage_per_paper
    success = total_assignments >= total_needed

    return {
        "ok": success,
        "selected_paper_count": len(selected_papers),
        "selected_papers": [
            {
                "id": p.id,
                "title": p.title,
                "venue": p.venue,
                "score_round1": round(p.score_round1, 3),
                "reviewers": paper_coverage[p.id],
            }
            for p in selected_papers
        ],
        "reviewer_assignments": {
            r_id: {
                "assigned_count": len(papers),
                "paper_ids": papers,
            }
            for r_id, papers in assignment.items()
        },
        "stats": {
            "total_reviewers": len(reviewers),
            "total_papers_selected": len(selected_papers),
            "target_coverage_per_paper": coverage_per_paper,
            "max_capacity_per_reviewer": max_capacity_per_reviewer,
            "total_assignments_made": total_assignments,
            "quota_fulfilled": success,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="AC-Reviewer two-round bidding and assignment solver.")
    parser.add_argument("--candidates-file", help="Path to JSON file containing paper candidates.")
    parser.add_argument("--reviewers-file", help="Path to JSON file containing reviewer profiles.")
    parser.add_argument("--bids-file", help="Path to JSON file containing reviewer bids.")
    parser.add_argument("--target-papers", type=int, default=15, help="Number of papers to select (default: 15).")
    parser.add_argument("--coverage", type=int, default=2, help="Reviewers per paper (default: 2).")
    parser.add_argument("--capacity", type=int, default=3, help="Max papers per reviewer (default: 3).")
    parser.add_argument("--recency-years", type=int, default=3, help="Recency window in years (default: 3).")
    parser.add_argument("--target-year", type=int, default=None, help="Target manuscript publication year.")
    parser.add_argument("--dry-run", action="store_true", help="Run with synthetic fixtures for sanity check.")
    parser.add_argument("--json", action="store_true", help="Output result as JSON.")
    args = parser.parse_args()

    if args.dry_run or not args.candidates_file:
        # Generate synthetic benchmark fixtures (30 candidates, 10 reviewers)
        synthetic_papers = [
            PaperCandidate(
                id=f"P_{i:02d}",
                title=f"Research Breakthrough in Area {i % 5} Variant {i}",
                venue="ICLR 2026" if i % 2 == 0 else "NeurIPS 2025",
                abstract=f"We study empirical and theoretical foundations of mechanism {i % 4}.",
                primary_area=f"Area_{i % 5}",
                year=2026 - (i % 4),
            )
            for i in range(1, 31)
        ]
        synthetic_reviewers = [
            ReviewerProfile(
                id=f"REV_{j:02d}",
                name=f"Reviewer {j}",
                areas=[f"Area_{j % 5}", f"Area_{(j+1) % 5}"],
                capacity=args.capacity,
            )
            for j in range(1, 11)
        ]
        synthetic_bids = {
            r.id: {
                p.id: "very_high" if p.primary_area in r.areas else "neutral"
                for p in synthetic_papers
            }
            for r in synthetic_reviewers
        }

        papers = synthetic_papers
        reviewers = synthetic_reviewers
        bids = synthetic_bids
    else:
        with open(args.candidates_file, encoding="utf-8") as f:
            raw_papers = json.load(f)
            papers = [PaperCandidate(**p) for p in raw_papers]

        with open(args.reviewers_file, encoding="utf-8") as f:
            raw_reviewers = json.load(f)
            reviewers = [ReviewerProfile(**r) for r in raw_reviewers]

        with open(args.bids_file, encoding="utf-8") as f:
            bids = json.load(f)

    # 1. Round 1 Coarse Bidding with Recency Gate
    min_year = (args.target_year - args.recency_years) if args.target_year else None
    shortlist = round1_coarse_bidding(papers, reviewers, bids, shortlist_size=25, min_year=min_year)

    # 2. Round 2 Matching & Assignment
    result = round2_assignment_solver(
        shortlist=shortlist,
        reviewers=reviewers,
        bids=bids,
        target_paper_count=args.target_papers,
        coverage_per_paper=args.coverage,
        max_capacity_per_reviewer=args.capacity,
    )

    if args.json or True:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
