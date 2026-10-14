#!/usr/bin/env python3
"""Tests for the rank-my-paper ranking.json contract validator.

Fixtures are hand-built from the written contract in
references/review-protocol.md, not derived from the validator implementation.
"""

from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "validate_ranking.py"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_ranking", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def full_text_reading(rank: int) -> dict:
    """A reading block with inspectable evidence anchors."""
    return {
        "mode": "full_text",
        "full_text_url": f"https://proceedings.example.org/{rank}.pdf",
        "obtained_via": "proceedings_pdf",
        "read_by": "subagent",
        "coverage_note": "All sections; appendices skimmed.",
        "anchors": [
            {
                "locator": f"Section {index + 1}",
                "quote": f"verbatim anchor {index + 1} from peer paper {rank}",
                "supports": "identification",
            }
            for index in range(3)
        ],
        "could_not_verify": [],
    }


def compliant_run():
    """A valid 15-record explicit-N run, with three verified peers above the target."""
    papers = []
    for rank in range(1, 16):
        is_target = rank == 4
        papers.append(
            {
                "key": "target" if is_target else f"ref-{rank}",
                "kind": "target" if is_target else "ccf_a_reference",
                "role": "target" if is_target else "direct",
                "domain_fit": None if is_target else "Same workflow-settlement problem and evaluation object as the target.",
                "title": "Target Manuscript" if is_target else f"Peer Paper {rank}",
                "authors": ["A. Author"],
                "venue": "ICLR" if is_target else "NeurIPS",
                "year": 2027 if is_target else 2024,
                "rank": rank,
                "relation_to_target": "self"
                if is_target
                else ("above" if rank < 4 else "below"),
                "decisive_factor": ""
                if is_target
                else f"Reason this peer is {'above' if rank < 4 else 'below'} the target.",
                "ccf_status": "not_applicable" if is_target else "A",
                "publication_status": "not_applicable" if is_target else "published",
                "abstract_status": "not_applicable" if is_target else "verified",
                "evidence_level": "full_paper",
                "confidence": "high" if is_target else "medium",
                "reading": {
                    **full_text_reading(rank),
                    "full_text_url": "/abs/path/manuscript.tex",
                    "obtained_via": "local_file",
                    "read_by": "subagent",
                } if is_target else full_text_reading(rank),
                "independent_review": {
                    "reviewer_id": f"reader-{rank}",
                    "summary": "The paper tests a stated mechanism under a frozen comparison.",
                    "strengths": ["Table 2 supports the bounded primary effect."],
                    "weaknesses": ["Section 5 leaves transfer to another population open."],
                    "score": 4 if rank < 4 else (3 if is_target else 2),
                    "score_rationale": "The reported evidence meets this level within the stated scope.",
                    "next_level_requirement": "A stronger identification argument is needed for the broader claim.",
                },
                "justification": "One self-contained comparative paragraph.",
                "source_url": "/abs/path/manuscript.tex" if is_target else f"https://example.org/{rank}",
                "publication_url": None if is_target else f"https://proceedings.example.org/{rank}",
                "abstract_url": None if is_target else f"https://example.org/{rank}/abstract",
                "ccf_source_url": None if is_target else "https://ccf.example.org/list",
            }
        )
    return {
        "schema_version": "3.1",
        "run": {
            "manuscript_path": "/abs/path/manuscript.tex",
            "manuscript_sha256": "a" * 64,
            "run_date": "2026-09-15",
            "ranked_count": 15,
            "rank_includes_target": True,
            "target_venue": "ICLR 2027",
            "publication_cutoff": None,
            "reading_policy": {
                "full_text_required": True,
                "dispatch_method": "subagent_parallel",
                "waiver": None,
            },
            "reading_dispatch": {
                "method": "subagent_parallel",
                "reader_count": 15,
                "dispatched_on": "2026-09-15",
            },
            "rank_interval": None,
            "rubric_version": "4.1-r1",
            "peer_set": {"mode": "fresh_search", "previous_run": None, "added": [], "removed": []},
            "ccf_scope": {
                "edition": "2022",
                "category": "AI",
                "comparator_venue_policy": "any_ccf_a",
                "source_url": "https://ccf.org.cn/list",
                "verified_on": "2026-09-15",
            },
        },
        "papers": papers,
        "our_paper_rank": 4,
        "top_weaknesses": ["w1", "w2", "w3"],
        "top_strengths": ["s1", "s2"],
        "revision_priorities": [
            {
                "priority": 1,
                "locus": "Section 5",
                "problem": "p",
                "direction": "d",
                "comparison_relevance": "r",
            }
        ],
        "adjacent_papers": [],
    }


class SkillDefaultTests(unittest.TestCase):
    def test_default_count_and_same_domain_policy_stay_aligned(self):
        root = SCRIPT.parent.parent
        skill = (root / "SKILL.md").read_text()
        protocol = (root / "references" / "review-protocol.md").read_text()
        interface = (root / "agents" / "openai.yaml").read_text()
        self.assertIn("Default 8 ranked records including the target", skill)
        self.assertIn("Default to `domain_peer`", skill)
        self.assertIn("`domain_peer` (default", protocol)
        self.assertIn('"ranked_count": 8', protocol)
        self.assertIn('"reader_count": 8', protocol)
        self.assertIn('"domain_fit":', protocol)
        self.assertIn("officially accepted, peer-reviewed publication", protocol)
        self.assertIn("default 8-record comparison", interface)


def waived_run(*keys):
    """A run with some comparators unreachable in full and waived by the user.

    Waived papers are unresolved and widen the interval without forcing a winner.
    """
    keys = keys or ("ref-1",)
    run = compliant_run()
    waived = set(keys)
    for paper in run["papers"]:
        if paper["key"] in waived:
            paper["independent_review"] = None
            paper["relation_to_target"] = "unresolved"
            paper["evidence_level"] = "abstract_only"
            paper["confidence"] = "low"
            paper["reading"] = {
                "mode": "full_text_unavailable",
                "full_text_url": None,
                "obtained_via": "none",
                "read_by": "subagent",
                "coverage_note": "",
                "anchors": [],
                "could_not_verify": ["everything below the abstract"],
                "blocked_by": "publisher paywall; no repository copy located",
            }
    run["run"]["reading_policy"]["waiver"] = {
        "granted_by_user": True,
        "reason": f"User accepted abstract-level records for {sorted(waived)}: the full texts are paywalled.",
        "records": sorted(waived),
    }
    low = sum(p["relation_to_target"] == "above" for p in run["papers"]) + 1
    run["run"]["rank_interval"] = {"low": low, "high": low + len(waived)}
    run["our_paper_rank"] = None
    for paper in run["papers"]:
        paper["rank"] = None

    return run


def failure_codes(report):
    return {f["code"] for f in report["failures"]}


class CompliantFixtureTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def test_compliant_run_passes(self):
        report = self.mod.validate(compliant_run())
        self.assertEqual(report["failures"], [], report["failures"])
        self.assertEqual(report["decision"], "PASS")


class RankConsistencyTests(unittest.TestCase):
    """The rank must be constructed from the head-to-head relations."""

    def setUp(self):
        self.mod = load_module()

    def test_rank_not_matching_above_count_fails(self):
        run = compliant_run()
        run["papers"][0]["relation_to_target"] = "below"  # 3 above -> rank must be 4
        report = self.mod.validate(run)
        self.assertIn("rank_relation_mismatch", failure_codes(report))

    def test_declared_rank_above_the_relation_count_fails(self):
        # Historical failure mode: reported rank 6 while 14 peers were 'above'.
        run = compliant_run()
        for paper in run["papers"]:
            if paper["kind"] == "target":
                paper["rank"] = 6
            elif paper["rank"] < 4:
                paper["rank"] = paper["rank"]
        run["our_paper_rank"] = 6
        for paper in run["papers"]:
            if paper["kind"] != "target":
                paper["relation_to_target"] = "above"
                paper["rank"] = 1 if paper["rank"] == 4 else paper["rank"]
        # rebuild a consistent permutation: target at 6, others 1..5,7..15
        order = [p for p in run["papers"] if p["kind"] != "target"]
        slots = [r for r in range(1, 16) if r != 6]
        for paper, slot in zip(order, slots):
            paper["rank"] = slot
        target = [p for p in run["papers"] if p["kind"] == "target"][0]
        target["rank"] = 6
        report = self.mod.validate(run)
        self.assertIn("rank_relation_mismatch", failure_codes(report))

    def test_target_with_non_self_relation_fails(self):
        run = compliant_run()
        [p for p in run["papers"] if p["kind"] == "target"][0]["relation_to_target"] = "above"
        report = self.mod.validate(run)
        self.assertIn("target_relation_invalid", failure_codes(report))

    def test_empty_decisive_factor_fails(self):
        run = compliant_run()
        run["papers"][0]["decisive_factor"] = ""
        report = self.mod.validate(run)
        self.assertIn("decisive_factor_missing", failure_codes(report))


class UnresolvedComparisonTests(unittest.TestCase):
    def test_full_text_can_leave_the_target_rank_unresolved(self):
        run = compliant_run()
        run["papers"][0]["relation_to_target"] = "unresolved"
        run["papers"][0]["decisive_factor"] = "Different strengths; neither has demonstrated superiority."
        for paper in run["papers"]:
            paper["rank"] = None
        run["our_paper_rank"] = None
        run["run"]["rank_interval"] = {"low": 3, "high": 4}
        report = load_module().validate(run)
        self.assertEqual(report["decision"], "PASS", report["failures"])
        self.assertEqual(report["derived_interval"], [3, 4])
        run["our_paper_rank"] = 3
        self.assertIn("rank_false_precision", failure_codes(load_module().validate(run)))

    def test_pairwise_order_must_agree_even_when_above_count_is_correct(self):
        run = compliant_run()
        run["papers"][0]["relation_to_target"] = "below"
        run["papers"][4]["relation_to_target"] = "above"
        self.assertIn("rank_relation_mismatch", failure_codes(load_module().validate(run)))


class ComparisonOnlyTests(unittest.TestCase):
    def test_comparison_neither_requires_nor_emits_acceptance_fields(self):
        report = load_module().validate(compliant_run())
        self.assertEqual(report["decision"], "PASS", report["failures"])
        self.assertNotIn("derived_verdict", report)
        self.assertNotIn("derived_band", report)
        self.assertNotIn("declared_verdict", report)

    def test_acceptance_assessment_is_rejected(self):
        run = compliant_run()
        run["acceptance_bar"] = "meets"
        self.assertIn("acceptance_assessment_retired", failure_codes(load_module().validate(run)))


class EvidenceTests(unittest.TestCase):
    """An abstract cannot support a confirmed score."""

    def setUp(self):
        self.mod = load_module()

    def test_high_confidence_on_abstract_only_fails(self):
        run = waived_run()
        [p for p in run["papers"] if p["key"] == "ref-1"][0]["confidence"] = "high"
        report = self.mod.validate(run)
        self.assertIn("confidence_exceeds_evidence", failure_codes(report))

    def test_metadata_only_high_confidence_fails(self):
        run = compliant_run()
        run["papers"][1]["evidence_level"] = "metadata_only"
        run["papers"][1]["confidence"] = "high"
        report = self.mod.validate(run)
        self.assertIn("confidence_exceeds_evidence", failure_codes(report))

    def test_full_paper_high_confidence_is_allowed(self):
        run = compliant_run()
        run["papers"][0]["evidence_level"] = "full_paper"
        run["papers"][0]["confidence"] = "high"
        report = self.mod.validate(run)
        self.assertNotIn("confidence_exceeds_evidence", failure_codes(report))

    def test_unverified_abstract_cannot_claim_abstract_level_evidence(self):
        run = waived_run()
        [p for p in run["papers"] if p["key"] == "ref-1"][0]["abstract_status"] = "abstract-unverified"
        report = self.mod.validate(run)
        self.assertIn("evidence_level_exceeds_abstract_status", failure_codes(report))

    def test_unverified_abstract_with_metadata_level_is_allowed(self):
        run = compliant_run()
        run["papers"][0]["abstract_status"] = "abstract-unverified"
        run["papers"][0]["evidence_level"] = "metadata_only"
        run["papers"][0]["confidence"] = "low"
        report = self.mod.validate(run)
        self.assertNotIn("evidence_level_exceeds_abstract_status", failure_codes(report))


class IndependentReviewTests(unittest.TestCase):
    def test_each_full_text_paper_needs_an_anchored_independent_score(self):
        for index in (0, 3):
            with self.subTest(index=index):
                run = compliant_run()
                run["papers"][index]["independent_review"] = None
                self.assertIn("independent_review_missing", failure_codes(load_module().validate(run)))
        run = compliant_run()
        run["papers"][3]["independent_review"]["score"] = 11
        self.assertIn("review_score_invalid", failure_codes(load_module().validate(run)))
        run["papers"][3]["independent_review"]["score"] = 0
        self.assertIn("review_score_invalid", failure_codes(load_module().validate(run)))
        run["papers"][3]["independent_review"]["score"] = 3
        run["papers"][3]["independent_review"]["next_level_requirement"] = ""
        self.assertIn("review_boundary_missing", failure_codes(load_module().validate(run)))

    def test_target_gets_its_own_independent_reader(self):
        run = compliant_run()
        run["papers"][3]["reading"]["read_by"] = "self"
        self.assertIn("read_by_mismatch:target", failure_codes(load_module().validate(run)))
        run = compliant_run()
        run["papers"][3]["independent_review"]["reviewer_id"] = "reader-1"
        self.assertIn("reviewer_reused", failure_codes(load_module().validate(run)))

    def test_score_disagreement_needs_an_explicit_ranking_reason(self):
        run = compliant_run()
        run["papers"][0]["independent_review"]["score"] = 2
        self.assertIn("score_override_unexplained", failure_codes(load_module().validate(run)))
        run["papers"][0]["score_override_reason"] = "Section 4 establishes the shared comparison's effect; its lower independent score concerns a separate broader claim."
        self.assertEqual(load_module().validate(run)["decision"], "PASS")


class PeerReuseTests(unittest.TestCase):
    def reuse(self, run, index, rubric="4.1-r1"):
        run["papers"][index]["independent_review"]["reused_from"] = {
            "run": "../run-20260920", "reviewed_on": "2026-09-20", "rubric_version": rubric}

    def test_peer_set_record_is_required(self):
        run = compliant_run()
        del run["run"]["peer_set"]
        self.assertIn("peer_set_missing", failure_codes(load_module().validate(run)))
        run = compliant_run()
        run["run"]["peer_set"]["mode"] = "carried_forward"
        self.assertIn("peer_set_previous_missing", failure_codes(load_module().validate(run)))

    def test_reused_peer_reviews_reduce_required_fresh_readers(self):
        run = compliant_run()
        run["run"]["peer_set"] = {"mode": "carried_forward", "previous_run": "../run-20260920", "added": [], "removed": []}
        for i in range(15):
            if i != 3:
                self.reuse(run, i)
        run["run"]["reading_dispatch"]["reader_count"] = 1
        report = load_module().validate(run)
        self.assertEqual(report["failures"], [], report["failures"])

    def test_target_review_cannot_be_reused(self):
        run = compliant_run()
        self.reuse(run, 3)
        self.assertIn("target_review_reused", failure_codes(load_module().validate(run)))

    def test_reuse_requires_matching_rubric_and_provenance(self):
        run = compliant_run()
        self.reuse(run, 0, rubric="old")
        self.assertIn("reuse_rubric_mismatch", failure_codes(load_module().validate(run)))
        run = compliant_run()
        run["papers"][0]["independent_review"]["reused_from"] = {"run": "x"}
        self.assertIn("reuse_provenance_missing", failure_codes(load_module().validate(run)))


class SameBandTests(unittest.TestCase):
    def test_same_band_direction_needs_reason(self):
        run = compliant_run()
        run["papers"][0]["independent_review"]["score"] = 3
        report = load_module().validate(run)
        self.assertIn("same_band_direction_unexplained", failure_codes(report))
        run["papers"][0]["same_band_reason"] = "Table 3 of ref-1 controls the confound that target Section 5.2 leaves open."
        report = load_module().validate(run)
        self.assertEqual(report["decision"], "PASS", report["failures"])
        self.assertTrue(any("score band" in n for n in report["notes"]))

    def test_same_band_unresolved_needs_no_reason(self):
        run = compliant_run()
        run["papers"][14]["independent_review"]["score"] = 3
        run["papers"][14]["relation_to_target"] = "unresolved"
        self.assertNotIn("same_band_direction_unexplained", failure_codes(load_module().validate(run)))


class TargetEvidenceTests(unittest.TestCase):
    def test_target_requires_the_same_reading_evidence_as_peers(self):
        run = compliant_run()
        target = next(p for p in run["papers"] if p["kind"] == "target")
        target["reading"] = None
        self.assertIn("reading_evidence_missing:target", failure_codes(load_module().validate(run)))
        target["reading"] = full_text_reading(4)
        target["reading"]["anchors"] = []
        self.assertIn("anchors_insufficient:target", failure_codes(load_module().validate(run)))


class V1SchemaRetirementTests(unittest.TestCase):
    """The five absolute score axes are retired in favour of ordinal relations."""

    def setUp(self):
        self.mod = load_module()

    def test_score_table_fails(self):
        run = compliant_run()
        run["papers"][0]["scores"] = {
            "novelty": 4,
            "soundness": 4,
            "rigor": 4,
            "clarity": 4,
            "significance": 4,
        }
        report = self.mod.validate(run)
        self.assertIn("score_axes_retired", failure_codes(report))

    def test_old_schema_version_fails(self):
        run = compliant_run()
        run["schema_version"] = "1.0"
        report = self.mod.validate(run)
        self.assertIn("schema_version_unsupported", failure_codes(report))


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def test_reference_without_publication_evidence_fails(self):
        run = compliant_run()
        run["papers"][0]["publication_status"] = "publication_unverified"
        run["papers"][0]["publication_url"] = None
        report = self.mod.validate(run)
        self.assertIn("publication_evidence_missing", failure_codes(report))

    def test_core_reference_cannot_mark_publication_not_applicable(self):
        run = compliant_run()
        run["papers"][0]["publication_status"] = "not_applicable"
        run["papers"][0]["publication_url"] = None
        report = self.mod.validate(run)
        self.assertIn("publication_evidence_missing", failure_codes(report))

    def test_core_reference_requires_domain_fit(self):
        run = compliant_run()
        del run["papers"][0]["domain_fit"]
        report = self.mod.validate(run)
        self.assertIn("domain_fit_missing", failure_codes(report))

    def test_reference_without_abstract_or_flag_fails(self):
        run = compliant_run()
        run["papers"][0]["abstract_status"] = "abstract-unverified"
        run["papers"][0]["abstract_url"] = None
        report = self.mod.validate(run)
        self.assertIn("abstract_evidence_missing", failure_codes(report))

    def test_abstract_unverified_with_url_is_accepted(self):
        run = compliant_run()
        run["papers"][0]["abstract_status"] = "abstract-unverified"
        report = self.mod.validate(run)
        self.assertNotIn("abstract_evidence_missing", failure_codes(report))

    def test_ccf_unverified_reference_fails_the_venue_gate(self):
        run = compliant_run()
        run["papers"][0]["ccf_status"] = "ccf_unverified"
        report = self.mod.validate(run)
        self.assertIn("ccf_gate_failed", failure_codes(report))

    def test_domain_top_uses_official_field_venue_source(self):
        run = compliant_run()
        run["run"]["ccf_scope"]["comparator_venue_policy"] = "domain_peer"
        peer = run["papers"][0]
        peer["ccf_status"] = "domain_top"
        peer["ccf_source_url"] = None
        report = self.mod.validate(run)
        self.assertIn("domain_status_source_missing", failure_codes(report))

        peer["domain_status_source_url"] = "https://field.example/official-venue-list"
        report = self.mod.validate(run)
        self.assertEqual(report["failures"], [], report["failures"])

    def test_any_ccf_a_venue_is_accepted_regardless_of_target_venue(self):
        run = compliant_run()
        run["papers"][0]["venue"] = "ISMIR"
        run["papers"][0]["ccf_status"] = "A"
        report = self.mod.validate(run)
        self.assertNotIn("ccf_gate_failed", failure_codes(report))
        self.assertEqual(run["run"]["ccf_scope"]["comparator_venue_policy"], "any_ccf_a")

    def test_missing_manuscript_hash_fails(self):
        run = compliant_run()
        run["run"]["manuscript_sha256"] = None
        report = self.mod.validate(run)
        self.assertIn("manuscript_hash_missing", failure_codes(report))


class StructuralTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def test_missing_target_fails(self):
        run = compliant_run()
        for paper in run["papers"]:
            if paper["kind"] == "target":
                paper["kind"] = "ccf_a_reference"
        report = self.mod.validate(run)
        self.assertIn("target_count_invalid", failure_codes(report))

    def test_rank_permutation_fails(self):
        run = compliant_run()
        run["papers"][0]["rank"] = 4
        report = self.mod.validate(run)
        self.assertIn("rank_permutation_invalid", failure_codes(report))

    def test_ranked_count_mismatch_fails(self):
        run = compliant_run()
        run["run"]["ranked_count"] = 14
        report = self.mod.validate(run)
        self.assertIn("ranked_count_mismatch", failure_codes(report))

    def test_our_paper_rank_mismatch_fails(self):
        run = compliant_run()
        run["our_paper_rank"] = 5
        report = self.mod.validate(run)
        self.assertIn("our_paper_rank_mismatch", failure_codes(report))

    def test_missing_adjacent_list_fails(self):
        run = compliant_run()
        del run["adjacent_papers"]
        report = self.mod.validate(run)
        self.assertIn("adjacent_papers_missing", failure_codes(report))


class FullTextReadingTests(unittest.TestCase):
    """Schema 2.1: no head-to-head relation without a full-text reading."""

    def setUp(self):
        self.mod = load_module()

    def test_missing_reading_object_fails(self):
        run = compliant_run()
        run["papers"][0]["reading"] = None
        report = self.mod.validate(run)
        self.assertIn("reading_evidence_missing:ref-1", failure_codes(report))

    def test_missing_policy_fails(self):
        run = compliant_run()
        del run["run"]["reading_policy"]
        report = self.mod.validate(run)
        self.assertIn("reading_policy_missing", failure_codes(report))

    def test_disabling_the_requirement_fails(self):
        run = compliant_run()
        run["run"]["reading_policy"]["full_text_required"] = False
        report = self.mod.validate(run)
        self.assertIn("full_text_required_false", failure_codes(report))

    def test_missing_dispatch_log_fails(self):
        run = compliant_run()
        del run["run"]["reading_dispatch"]
        report = self.mod.validate(run)
        self.assertIn("reading_dispatch_missing", failure_codes(report))

    def test_unread_paper_without_waiver_fails(self):
        run = compliant_run()
        run["papers"][0]["reading"]["mode"] = "full_text_partial"
        report = self.mod.validate(run)
        self.assertIn("reading_gate_failed:ref-1", failure_codes(report))

    def test_abstract_only_evidence_outside_waiver_fails(self):
        run = compliant_run()
        run["papers"][0]["evidence_level"] = "abstract_only"
        report = self.mod.validate(run)
        self.assertIn("evidence_level_below_full_text", failure_codes(report))

    def test_too_few_anchors_fails(self):
        run = compliant_run()
        run["papers"][0]["reading"]["anchors"] = run["papers"][0]["reading"]["anchors"][:2]
        report = self.mod.validate(run)
        self.assertIn("anchors_insufficient:ref-1", failure_codes(report))

    def test_anchor_without_locator_fails(self):
        run = compliant_run()
        run["papers"][0]["reading"]["anchors"][0]["locator"] = " "
        report = self.mod.validate(run)
        self.assertIn("anchor_locator_missing:ref-1", failure_codes(report))

    def test_full_text_claim_without_url_fails(self):
        run = compliant_run()
        run["papers"][0]["reading"]["full_text_url"] = None
        report = self.mod.validate(run)
        self.assertIn("full_text_url_missing:ref-1", failure_codes(report))

    def test_self_read_full_text_under_subagent_dispatch_fails(self):
        run = compliant_run()
        run["papers"][0]["reading"]["read_by"] = "self"
        report = self.mod.validate(run)
        self.assertIn("read_by_mismatch:ref-1", failure_codes(report))

    def test_reader_count_below_core_size_fails(self):
        run = compliant_run()
        run["run"]["reading_dispatch"]["reader_count"] = 3
        report = self.mod.validate(run)
        self.assertIn("reader_count_insufficient", failure_codes(report))

    def test_reader_count_above_core_size_fails(self):
        run = compliant_run()
        run["run"]["reading_dispatch"]["reader_count"] = len(run["papers"]) + 1
        report = self.mod.validate(run)
        self.assertIn("reader_count_excessive", failure_codes(report))

    def test_self_granted_waiver_fails(self):
        run = waived_run()
        run["run"]["reading_policy"]["waiver"]["granted_by_user"] = False
        report = self.mod.validate(run)
        self.assertIn("waiver_not_user_granted", failure_codes(report))

    def test_waived_run_without_interval_fails(self):
        run = waived_run()
        run["run"]["rank_interval"] = None
        report = self.mod.validate(run)
        self.assertIn("rank_interval_missing", failure_codes(report))

    def test_waived_run_with_wrong_interval_fails(self):
        run = waived_run()
        run["run"]["rank_interval"] = {"low": 1, "high": 2}
        report = self.mod.validate(run)
        self.assertIn("rank_interval_mismatch", failure_codes(report))

    def test_interval_without_waiver_fails(self):
        run = compliant_run()
        run["run"]["rank_interval"] = {"low": 3, "high": 4}
        report = self.mod.validate(run)
        self.assertIn("rank_interval_unexpected", failure_codes(report))

    def test_waived_run_passes_and_reports_its_interval(self):
        run = waived_run()
        report = self.mod.validate(run)
        self.assertEqual(report["failures"], [], report["failures"])
        self.assertEqual(report["derived_interval"], [3, 4])

    def test_multiple_waivers_expand_the_rank_interval(self):
        report = self.mod.validate(waived_run("ref-1", "ref-5", "ref-6"))
        self.assertEqual(report["failures"], [], report["failures"])
        self.assertEqual(report["derived_interval"], [3, 6])


class CliTests(unittest.TestCase):
    def test_failing_run_exits_nonzero(self):
        import json
        import tempfile

        run = compliant_run()
        run["acceptance_bar"] = "borderline"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ranking.json"
            path.write_text(json.dumps(run), encoding="utf-8")
            code = load_module().main([str(path)])
        self.assertEqual(code, 1)

    def test_compliant_run_exits_zero(self):
        import json
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ranking.json"
            path.write_text(json.dumps(copy.deepcopy(compliant_run())), encoding="utf-8")
            code = load_module().main([str(path)])
        self.assertEqual(code, 0)

    def test_unparseable_json_exits_two(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ranking.json"
            path.write_text("{not json", encoding="utf-8")
            code = load_module().main([str(path)])
        self.assertEqual(code, 2)


class Schema32Tests(unittest.TestCase):
    def test_schema_32_compliant_run(self):
        run = copy.deepcopy(compliant_run())
        run["schema_version"] = "3.2"
        # Test stratified peer roles
        run["papers"][0]["role"] = "sota_ceiling"
        run["papers"][1]["role"] = "median_accepted"
        run["papers"][2]["role"] = "marginal_pass"
        # Test accepted_pre_proceedings status
        run["papers"][0]["publication_status"] = "accepted_pre_proceedings"
        # Test optional novelty and practical impact bands
        run["papers"][0]["independent_review"]["novelty_band"] = 5
        run["papers"][0]["independent_review"]["practical_impact_band"] = 4
        run["papers"][0]["independent_review"]["presentation_band"] = 4
        
        report = load_module().validate(run)
        self.assertEqual(report["decision"], "PASS", report.get("failures"))

    def test_invalid_novelty_band_fails(self):
        run = copy.deepcopy(compliant_run())
        run["schema_version"] = "3.2"
        run["papers"][0]["independent_review"]["novelty_band"] = 6
        report = load_module().validate(run)
        self.assertEqual(report["decision"], "FAIL")
        self.assertTrue(any(f["code"] == "novelty_band_invalid" for f in report["failures"]))

    def test_invalid_presentation_band_fails(self):
        run = copy.deepcopy(compliant_run())
        run["schema_version"] = "3.2"
        run["papers"][0]["independent_review"]["presentation_band"] = 6
        report = load_module().validate(run)
        self.assertEqual(report["decision"], "FAIL")
        self.assertTrue(any(f["code"] == "presentation_band_invalid" for f in report["failures"]))

    def test_recency_gate_fails_for_older_papers(self):
        run = copy.deepcopy(compliant_run())
        # Target is 2027; 2023 is > 3 years older than target
        run["papers"][1]["year"] = 2023
        report = load_module().validate(run)
        self.assertEqual(report["decision"], "FAIL")
        self.assertTrue(any(f["code"] == "recency_gate_failed" for f in report["failures"]))

    def test_schema_3_3_compliant_run(self):
        run = copy.deepcopy(compliant_run())
        run["schema_version"] = "3.3"
        for p in run["papers"]:
            p["hard_gates"] = {
                "anonymity_preserved": True,
                "scope_compliant": True,
                "fatal_violations": [],
            }
        target = next(p for p in run["papers"] if p.get("kind") == "target")
        target["independent_review"]["internal_consistency"] = {
            "table_recomputed": "Table 1 accuracy and latency verified consistent.",
            "claim_vs_baseline_alignment": "Headline throughput improvement aligned with 38% token reduction in Table 2.",
            "contradiction_found": False,
            "fatal_flaw_cluster": None,
        }
        report = load_module().validate(run)
        self.assertEqual(report["decision"], "PASS", report.get("failures"))

    def test_hard_gate_anonymity_violation_unmarked_fails(self):
        run = copy.deepcopy(compliant_run())
        run["schema_version"] = "3.3"
        target = next(p for p in run["papers"] if p.get("kind") == "target")
        target["hard_gates"] = {
            "anonymity_preserved": False,
            "scope_compliant": True,
            "fatal_violations": ["Personal GitHub repo linked in Data Availability."],
        }
        report = load_module().validate(run)
        self.assertEqual(report["decision"], "FAIL")
        self.assertTrue(any(f["code"] == "target_veto_unmarked" for f in report["failures"]))

    def test_hard_gate_vetoed_target_with_ranks_fails(self):
        run = copy.deepcopy(compliant_run())
        run["schema_version"] = "3.3"
        target = next(p for p in run["papers"] if p.get("kind") == "target")
        target["hard_gate_vetoed"] = True
        target["hard_gates"] = {
            "anonymity_preserved": False,
            "scope_compliant": True,
            "fatal_violations": ["Personal GitHub URL exposed."],
        }
        # Still carries numerical rank 4
        report = load_module().validate(run)
        self.assertEqual(report["decision"], "FAIL")
        self.assertTrue(any(f["code"] == "vetoed_target_ranked" for f in report["failures"]))

    def test_hard_gate_vetoed_target_null_ranks_passes(self):
        run = copy.deepcopy(compliant_run())
        run["schema_version"] = "3.3"
        target = next(p for p in run["papers"] if p.get("kind") == "target")
        target["hard_gate_vetoed"] = True
        target["hard_gates"] = {
            "anonymity_preserved": False,
            "scope_compliant": True,
            "fatal_violations": ["Personal GitHub URL exposed."],
        }
        target["rank"] = None
        run["our_paper_rank"] = None
        for p in run["papers"]:
            p["rank"] = None
        run["run"]["rank_interval"] = None
        report = load_module().validate(run)
        self.assertEqual(report["decision"], "PASS", report.get("failures"))

    def test_fatal_contradiction_cluster_a_scored_high_fails(self):
        run = copy.deepcopy(compliant_run())
        run["schema_version"] = "3.3"
        target = next(p for p in run["papers"] if p.get("kind") == "target")
        target["independent_review"]["score"] = 7
        target["independent_review"]["internal_consistency"] = {
            "table_recomputed": "Table 1 shows 48M vs 38M tokens.",
            "claim_vs_baseline_alignment": "Claim of efficiency contradicted by higher token usage.",
            "contradiction_found": True,
            "fatal_flaw_cluster": "A",
        }
        report = load_module().validate(run)
        self.assertEqual(report["decision"], "FAIL")
        self.assertTrue(any(f["code"] == "fatal_contradiction_scored_high" for f in report["failures"]))


if __name__ == "__main__":
    unittest.main()
