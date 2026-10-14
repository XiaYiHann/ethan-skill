import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from bidding_assigner import (
    PaperCandidate,
    ReviewerProfile,
    compute_affinity,
    round1_coarse_bidding,
    round2_assignment_solver,
)


def test_affinity_calculation():
    rev = ReviewerProfile(id="R1", name="Expert", areas=["reinforcement learning", "reasoning"])
    paper_match = PaperCandidate(
        id="P1", title="Deep Reasoning in LLMs", venue="ICLR", abstract="", primary_area="Reasoning"
    )
    paper_mismatch = PaperCandidate(
        id="P2", title="Computer Vision Segmentation", venue="CVPR", abstract="", primary_area="Vision"
    )

    assert compute_affinity(rev, paper_match) > 0.0
    assert compute_affinity(rev, paper_mismatch) == 0.0


def test_round1_coarse_bidding():
    papers = [
        PaperCandidate(id=f"P_{i}", title=f"Paper {i}", venue="ICLR", abstract="", primary_area="RL")
        for i in range(30)
    ]
    reviewers = [
        ReviewerProfile(id=f"R_{j}", name=f"Rev {j}", areas=["RL"])
        for j in range(10)
    ]
    bids = {
        "R_0": {"P_0": "very_high", "P_1": "high"}
    }

    shortlist = round1_coarse_bidding(papers, reviewers, bids, shortlist_size=20)
    assert len(shortlist) == 20
    # P_0 and P_1 have highest scores
    assert shortlist[0].id in {"P_0", "P_1"}


def test_round2_bipartite_assignment():
    papers = [
        PaperCandidate(id=f"P_{i:02d}", title=f"Paper {i}", venue="ICLR", abstract="", primary_area=f"Area_{i%5}")
        for i in range(20)
    ]
    reviewers = [
        ReviewerProfile(id=f"REV_{j:02d}", name=f"Rev {j}", areas=[f"Area_{j%5}"], capacity=3)
        for j in range(10)
    ]
    bids = {
        r.id: {p.id: "very_high" if p.primary_area in r.areas else "neutral" for p in papers}
        for r in reviewers
    }

    res = round2_assignment_solver(
        shortlist=papers,
        reviewers=reviewers,
        bids=bids,
        target_paper_count=15,
        coverage_per_paper=2,
        max_capacity_per_reviewer=3,
    )

    assert res["ok"] is True
    assert res["selected_paper_count"] == 15
    assert res["stats"]["total_assignments_made"] == 30
    assert res["stats"]["quota_fulfilled"] is True

    # Check each reviewer has exactly 3 papers
    for r_id, info in res["reviewer_assignments"].items():
        assert info["assigned_count"] == 3

    # Check each paper has exactly 2 reviewers
    for p in res["selected_papers"]:
        assert len(p["reviewers"]) == 2


def test_round1_recency_gate():
    papers = [
        PaperCandidate(id="P_old", title="Old Paper", venue="ICLR", abstract="", primary_area="RL", year=2020),
        PaperCandidate(id="P_recent", title="Recent Paper", venue="ICLR", abstract="", primary_area="RL", year=2025),
    ]
    reviewers = [ReviewerProfile(id="R1", name="Rev 1", areas=["RL"])]
    bids = {"R1": {"P_old": "very_high", "P_recent": "very_high"}}

    shortlist = round1_coarse_bidding(papers, reviewers, bids, min_year=2023)
    assert len(shortlist) == 1
    assert shortlist[0].id == "P_recent"
