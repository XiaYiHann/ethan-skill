#!/usr/bin/env python3
"""Validate comparison-only rankings, source evidence, and rank uncertainty.

PASS certifies the output contract, not the scientific judgment or source truth.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SUPPORTED_SCHEMAS = {"3.1", "3.2"}
SUPPORTED_SCHEMA = "3.2"
PEER_SET_MODES = {"fresh_search", "carried_forward"}

CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}
MAX_CONFIDENCE_BY_EVIDENCE = {
    "full_paper": "high",
    "abstract_only": "low",
    "metadata_only": "low",
}

READING_MODES = {"full_text", "full_text_partial", "full_text_unavailable"}
OBTAINED_VIA = {
    "local_file",
    "publisher_html",
    "publisher_pdf",
    "proceedings_pdf",
    "aclanthology_pdf",
    "arxiv_pdf",
    "openreview_pdf",
    "none",
}
READ_BY = {"subagent", "self"}
DISPATCH_METHODS = {"subagent_parallel", "self"}
MIN_ANCHORS = 3
MAX_ANCHOR_WORDS = 40

KINDS = {"target", "ccf_a_reference", "ccf_b_reference", "domain_reference"}
ROLES = {
    "target",
    "direct",
    "method",
    "foundational",
    # Stratified cohort roles (Schema 3.2)
    "sota_ceiling",
    "median_accepted",
    "marginal_pass",
}
RELATIONS = {"self", "above", "below", "unresolved"}
CCF_STATUSES = {"A", "B", "domain_top", "ccf_unverified", "not_applicable"}
PUBLICATION_STATUSES = {
    "published",
    "accepted_pre_proceedings",
    "publication_unverified",
    "not_applicable",
}
ABSTRACT_STATUSES = {"verified", "abstract-unverified", "not_applicable"}
EVIDENCE_LEVELS = {"full_paper", "abstract_only", "metadata_only"}
CONFIDENCES = {"low", "medium", "high"}

# The comparator venue gate is about CCF provenance, not about matching the
# target's own venue: any paper accepted at the required tier is a valid
# comparator, and proximity is carried separately by `role`.
ALLOWED_CCF_BY_POLICY = {
    "any_ccf_a": {"A"},
    "ccf_ab": {"A", "B"},
    "domain_peer": {"A", "B", "domain_top"},
}

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class _Report:
    def __init__(self):
        self.failures: list[dict] = []
        self.notes: list[str] = []
        self.derived_interval: tuple[int, int] | None = None

    def fail(self, code: str, message: str) -> None:
        self.failures.append({"code": code, "message": message})

    def note(self, message: str) -> None:
        self.notes.append(message)


def _is_str(value) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _check_scope(run: dict, report: _Report) -> str:
    ccf_scope = run.get("ccf_scope")
    if not isinstance(ccf_scope, dict):
        report.fail("ccf_scope_missing", "run.ccf_scope is required.")
        return "any_ccf_a"
    policy = ccf_scope.get("comparator_venue_policy")
    if policy not in ALLOWED_CCF_BY_POLICY:
        report.fail(
            "ccf_scope_policy_invalid",
            f"comparator_venue_policy must be one of {sorted(ALLOWED_CCF_BY_POLICY)}, got {policy!r}.",
        )
        return "any_ccf_a"
    if not _is_str(ccf_scope.get("source_url")):
        report.fail("ccf_scope_source_missing", "run.ccf_scope.source_url is required.")
    return policy


def _check_manuscript(run: dict, report: _Report) -> None:
    digest = run.get("manuscript_sha256")
    if not isinstance(digest, str) or not SHA256_RE.match(digest):
        report.fail(
            "manuscript_hash_missing",
            "run.manuscript_sha256 must be a 64-character hex digest of the reviewed revision.",
        )


def _check_peer_set(run: dict, report: _Report) -> None:
    if not _is_str(run.get("rubric_version")):
        report.fail("rubric_version_missing", "run.rubric_version is required; reused reviews must match it.")
    peer_set = run.get("peer_set")
    if not isinstance(peer_set, dict) or peer_set.get("mode") not in PEER_SET_MODES:
        report.fail(
            "peer_set_missing",
            f"run.peer_set.mode must be one of {sorted(PEER_SET_MODES)}; record whether the core was searched afresh or carried forward.",
        )
        return
    for field in ("added", "removed"):
        if not isinstance(peer_set.get(field), list):
            report.fail("peer_set_delta_missing", f"run.peer_set.{field} must be a list (empty when unchanged).")
    if peer_set.get("previous_run") is None:
        if peer_set["mode"] == "carried_forward":
            report.fail("peer_set_previous_missing", "A carried-forward peer set must name run.peer_set.previous_run.")
    elif not _is_str(peer_set.get("previous_run")):
        report.fail("peer_set_previous_missing", "run.peer_set.previous_run must be a path or null.")


def _check_structural(payload: dict, run: dict, papers: list, report: _Report) -> tuple[int, int | None]:
    ranked_count = run.get("ranked_count")
    if ranked_count != len(papers):
        report.fail(
            "ranked_count_mismatch",
            f"run.ranked_count={ranked_count!r} but papers has {len(papers)} records.",
        )

    targets = [p for p in papers if p.get("kind") == "target"]
    if len(targets) != 1:
        report.fail(
            "target_count_invalid",
            f"Exactly one paper must have kind='target'; found {len(targets)}.",
        )

    ranks = [p.get("rank") for p in papers]
    n = len(papers)
    unresolved = any(p.get("relation_to_target") == "unresolved" for p in papers)
    if unresolved:
        if payload.get("our_paper_rank") is not None or any(r is not None for r in ranks):
            report.fail("rank_false_precision", "Unresolved comparisons require null ranks and a target rank interval.")
    elif sorted(r for r in ranks if type(r) is int) != list(range(1, n + 1)):
        report.fail(
            "rank_permutation_invalid",
            f"ranks must be a permutation of 1..{n}; got {ranks}.",
        )

    target_rank = targets[0].get("rank") if targets else None
    if payload.get("our_paper_rank") != target_rank:
        report.fail(
            "our_paper_rank_mismatch",
            f"our_paper_rank={payload.get('our_paper_rank')!r} disagrees with the target record's rank={target_rank!r}.",
        )

    if not isinstance(payload.get("adjacent_papers"), list):
        report.fail(
            "adjacent_papers_missing",
            "adjacent_papers must be present (an empty list is allowed when none were found).",
        )

    return n, target_rank if type(target_rank) is int else None


def _check_relations(papers: list, our_rank: int | None, report: _Report) -> None:
    above = 0
    for paper in papers:
        relation = paper.get("relation_to_target")
        is_target = paper.get("kind") == "target"
        if relation not in RELATIONS:
            report.fail(
                f"relation_invalid:{paper.get('key')}",
                f"relation_to_target must be one of {sorted(RELATIONS)}, got {relation!r}.",
            )
            continue
        if is_target:
            if relation != "self":
                report.fail(
                    "target_relation_invalid",
                    "The target record must carry relation_to_target='self'.",
                )
            continue
        if relation == "self":
            report.fail(
                "target_relation_invalid",
                f"Non-target paper {paper.get('key')!r} cannot carry relation_to_target='self'.",
            )
            continue
        if relation == "above":
            above += 1
        rank = paper.get("rank")
        if type(rank) is int and our_rank is not None and relation in {"above", "below"}:
            if (relation == "above" and rank >= our_rank) or (relation == "below" and rank <= our_rank):
                report.fail("rank_relation_mismatch", f"Paper {paper.get('key')!r} rank contradicts its relation to the target.")
        if not _is_str(paper.get("decisive_factor")):
            report.fail(
                "decisive_factor_missing",
                f"Paper {paper.get('key')!r} ({relation}) needs a non-empty decisive_factor.",
            )

    if our_rank is not None and above + 1 != our_rank:
        report.fail(
            "rank_relation_mismatch",
            f"our_paper_rank={our_rank} but {above} peer(s) are recorded as 'above' "
            f"(rank must equal count(above)+1={above + 1}). The rank is not supported by "
            "the head-to-head relations.",
        )


def _check_reading_policy(run: dict, papers: list, report: _Report) -> tuple[dict, set]:
    policy = run.get("reading_policy")
    if not isinstance(policy, dict):
        report.fail(
            "reading_policy_missing",
            "run.reading_policy is required: full-text reading is the minimum evidence for a "
            "core comparator, and the run must declare how the reading was dispatched.",
        )
        policy = {}

    if policy.get("full_text_required") is not True:
        report.fail(
            "full_text_required_false",
            "run.reading_policy.full_text_required must be true. An abstract-only comparison "
            "is not a comparison; if the user granted the waiver, record it under "
            "reading_policy.waiver instead of disabling the requirement.",
        )

    if policy.get("dispatch_method") not in DISPATCH_METHODS:
        report.fail(
            "dispatch_method_invalid",
            f"reading_policy.dispatch_method must be one of {sorted(DISPATCH_METHODS)}, "
            f"got {policy.get('dispatch_method')!r}.",
        )

    waived: set = set()
    waiver = policy.get("waiver")
    if waiver is not None:
        if not isinstance(waiver, dict):
            report.fail("waiver_invalid", "reading_policy.waiver must be null or an object.")
        else:
            if waiver.get("granted_by_user") is not True:
                report.fail(
                    "waiver_not_user_granted",
                    "A waiver may only be recorded when the user granted it: set "
                    "waiver.granted_by_user=true after the user accepted the abstract-level "
                    "records. The producing agent must not self-grant it.",
                )
            if not _is_str(waiver.get("reason")):
                report.fail(
                    "waiver_reason_missing",
                    "reading_policy.waiver.reason must name which papers are unreachable in "
                    "full and why.",
                )
            records = waiver.get("records")
            if not isinstance(records, list) or not records:
                report.fail(
                    "waiver_records_missing",
                    "reading_policy.waiver.records must list the record keys covered by the waiver.",
                )
            else:
                waived = {r for r in records if isinstance(r, str) and r.strip()}
                known = {p.get("key") for p in papers if isinstance(p, dict)}
                unknown = sorted(waived - known)
                if unknown:
                    report.fail(
                        "waiver_records_unknown",
                        f"waiver.records names papers that are not in the core: {unknown}.",
                    )
    return policy, waived


def _check_dispatch(run: dict, papers: list, policy: dict, report: _Report) -> None:
    dispatch = run.get("reading_dispatch")
    reviewed_papers = [p for p in papers if isinstance(p, dict)]
    if not isinstance(dispatch, dict):
        report.fail(
            "reading_dispatch_missing",
            "run.reading_dispatch is required: it records one reader per comparator, the "
            "method, and the date. A reading nobody can audit is not evidence.",
        )
        return

    method = dispatch.get("method")
    if method not in DISPATCH_METHODS:
        report.fail(
            "dispatch_method_invalid",
            f"reading_dispatch.method must be one of {sorted(DISPATCH_METHODS)}, got {method!r}.",
        )
    elif policy.get("dispatch_method") not in (None, method):
        report.fail(
            "dispatch_method_mismatch",
            f"reading_dispatch.method={method!r} disagrees with "
            f"reading_policy.dispatch_method={policy.get('dispatch_method')!r}.",
        )

    count = dispatch.get("reader_count")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        report.fail(
            "reader_count_invalid",
            f"reading_dispatch.reader_count must be a non-negative integer, got {count!r}.",
        )
    else:
        reused = sum(
            1 for p in reviewed_papers
            if isinstance(p.get("independent_review"), dict) and "reused_from" in p["independent_review"]
        )
        if method == "subagent_parallel":
            expected = len(reviewed_papers) - reused
            if count < expected:
                report.fail(
                    "reader_count_insufficient",
                    f"reading_dispatch.reader_count={count} but the core needs exactly {expected} "
                    "fresh readers after review reuse.",
                )
            elif count > expected:
                report.fail(
                    "reader_count_excessive",
                    f"reading_dispatch.reader_count={count} but the core needs exactly {expected} "
                    "fresh readers after review reuse; do not dispatch extra reviewers.",
                )

    if not _is_str(dispatch.get("dispatched_on")):
        report.fail(
            "dispatch_date_missing",
            "reading_dispatch.dispatched_on is required.",
        )


def _check_reading(paper: dict, waived: set, method, report: _Report) -> None:
    """The target and peers need evidence anchors; only peers can be waived."""
    key = paper.get("key")
    is_target = paper.get("kind") == "target"

    reading = paper.get("reading")
    if not isinstance(reading, dict):
        report.fail(
            f"reading_evidence_missing:{key}",
            f"Paper {key!r} has no reading object. A comparator may only be ranked from its "
            "full text: record mode, the URL actually opened, the coverage note, and anchors.",
        )
        return

    mode = reading.get("mode")
    if mode not in READING_MODES:
        report.fail(
            f"reading_mode_invalid:{key}",
            f"reading.mode must be one of {sorted(READING_MODES)}, got {mode!r}.",
        )
        return

    is_waived = key in waived and not is_target
    if is_target and (mode != "full_text" or paper.get("evidence_level") != "full_paper"):
        report.fail("target_reading_incomplete", "Read the target completely before comparing it.")
    obtained_via = reading.get("obtained_via")
    if obtained_via not in OBTAINED_VIA:
        report.fail(
            f"obtained_via_invalid:{key}",
            f"reading.obtained_via must be one of {sorted(OBTAINED_VIA)}, got {obtained_via!r}.",
        )

    read_by = reading.get("read_by")
    if read_by not in READ_BY:
        report.fail(
            f"read_by_invalid:{key}",
            f"reading.read_by must be one of {sorted(READ_BY)}, got {read_by!r}.",
        )
    elif method == "subagent_parallel" and mode == "full_text" and read_by != "subagent":
        report.fail(
            f"read_by_mismatch:{key}",
            f"Paper {key!r} claims a full-text read by {read_by!r} while the run declares "
            "subagent_parallel dispatch; a full-text relation must come from a dispatched reader.",
        )

    if mode == "full_text":
        if not _is_str(reading.get("full_text_url")):
            report.fail(
                f"full_text_url_missing:{key}",
                f"Paper {key!r} claims a full-text read but records no full_text_url. A pair of "
                "mode=full_text and no URL is unfalsifiable.",
            )
        if not _is_str(reading.get("coverage_note")):
            report.fail(
                f"coverage_note_missing:{key}",
                f"Paper {key!r} needs a coverage note saying which parts were actually read.",
            )
        if obtained_via == "none":
            report.fail(
                f"obtained_via_invalid:{key}",
                f"Paper {key!r} claims mode=full_text with obtained_via='none'.",
            )
        anchors = reading.get("anchors")
        if not isinstance(anchors, list) or len(anchors) < MIN_ANCHORS:
            report.fail(
                f"anchors_insufficient:{key}",
                f"Paper {key!r} needs at least {MIN_ANCHORS} anchors (locator + verbatim "
                f"quote); got {0 if not isinstance(anchors, list) else len(anchors)}.",
            )
        else:
            for index, anchor in enumerate(anchors):
                if not isinstance(anchor, dict):
                    report.fail(
                        f"anchor_invalid:{key}",
                        f"Paper {key!r} anchor {index} is not an object.",
                    )
                    continue
                if not _is_str(anchor.get("locator")):
                    report.fail(
                        f"anchor_locator_missing:{key}",
                        f"Paper {key!r} anchor {index} needs a locator (section/table/page).",
                    )
                quote = anchor.get("quote")
                if not _is_str(quote):
                    report.fail(
                        f"anchor_quote_missing:{key}",
                        f"Paper {key!r} anchor {index} needs a verbatim quote.",
                    )
                elif len(quote.split()) > MAX_ANCHOR_WORDS:
                    report.fail(
                        f"anchor_quote_too_long:{key}",
                        f"Paper {key!r} anchor {index} quotes {len(quote.split())} words; keep "
                        f"anchors at or below {MAX_ANCHOR_WORDS} words so the locator stays "
                        "the thing being checked.",
                    )
        return

    # Not a full-text read: only legal under a user-granted waiver, capped low.
    if not is_waived:
        report.fail(
            f"reading_gate_failed:{key}",
            f"Paper {key!r} has reading.mode={mode!r} and is not covered by a user-granted "
            "waiver. A comparator whose full text was not read does not belong in the ranked "
            "core: move it to adjacent_papers with the reason 'full text unavailable', or "
            "obtain the waiver and cap it at confidence='low'.",
        )
        return
    if not _is_str(reading.get("blocked_by")):
        report.fail(
            f"blocked_by_missing:{key}",
            f"Paper {key!r} is waived at mode={mode!r} but does not say what blocked the read.",
        )
    if paper.get("evidence_level") not in ("abstract_only", "metadata_only"):
        report.fail(
            f"waived_evidence_level_invalid:{key}",
            f"Waived paper {key!r} must use evidence_level 'abstract_only' or 'metadata_only'; "
            f"got {paper.get('evidence_level')!r}.",
        )
    if paper.get("confidence") != "low":
        report.fail(
            f"waived_confidence_invalid:{key}",
            f"Waived paper {key!r} must carry confidence='low'; got {paper.get('confidence')!r}. "
            "Evidence that could not be read cannot support a confident comparison.",
        )


def _check_interval(run: dict, papers: list, waived: set, report: _Report) -> tuple[int, int] | None:
    """Unresolved relations bound the target's position without forcing winners."""
    peers = [p for p in papers if p.get("kind") != "target"]
    for paper in peers:
        if paper.get("key") in waived and paper.get("relation_to_target") != "unresolved":
            report.fail("waived_relation_resolved", "Waived papers must carry relation_to_target='unresolved'.")
    uncertain = [p for p in peers if p.get("relation_to_target") == "unresolved" or p.get("key") in waived]
    declared = run.get("rank_interval")
    if not uncertain:
        if declared is not None:
            report.fail("rank_interval_unexpected", "Omit rank_interval (or set null) when all relations are resolved.")
        return None
    low = sum(p.get("relation_to_target") == "above" and p.get("key") not in waived for p in peers) + 1
    high = low + len(uncertain)
    if not isinstance(declared, dict):
        report.fail("rank_interval_missing", "Unresolved comparisons require run.rank_interval {low, high}.")
    elif type(declared.get("low")) is not int or type(declared.get("high")) is not int or (declared["low"], declared["high"]) != (low, high):
        report.fail("rank_interval_mismatch", f"Relations imply rank_interval=({low}, {high}), got {declared!r}.")
    return low, high


def _check_evidence(paper: dict, report: _Report) -> None:
    key = paper.get("key")
    evidence = paper.get("evidence_level")
    confidence = paper.get("confidence")
    if evidence not in EVIDENCE_LEVELS:
        report.fail(
            f"evidence_level_invalid:{key}",
            f"evidence_level must be one of {sorted(EVIDENCE_LEVELS)}, got {evidence!r}.",
        )
        return
    if confidence not in CONFIDENCES:
        report.fail(
            f"confidence_invalid:{key}",
            f"confidence must be one of {sorted(CONFIDENCES)}, got {confidence!r}.",
        )
        return
    ceiling = MAX_CONFIDENCE_BY_EVIDENCE[evidence]
    if CONFIDENCE_RANK[confidence] > CONFIDENCE_RANK[ceiling]:
        report.fail(
            "confidence_exceeds_evidence",
            f"Paper {key!r} claims confidence={confidence!r} from evidence_level={evidence!r}; "
            f"the most that level supports is {ceiling!r}.",
        )


def _check_provenance(paper: dict, policy: str, waived: set, report: _Report) -> None:
    key = paper.get("key")
    is_target = paper.get("kind") == "target"

    if paper.get("kind") not in KINDS:
        report.fail(
            f"kind_invalid:{key}",
            f"kind must be one of {sorted(KINDS)}, got {paper.get('kind')!r}.",
        )
    if paper.get("role") not in ROLES:
        report.fail(
            f"role_invalid:{key}",
            f"role must be one of {sorted(ROLES)}, got {paper.get('role')!r}.",
        )
    if not is_target and not _is_str(paper.get("domain_fit")):
        report.fail(
            "domain_fit_missing",
            f"Core comparator {key!r} needs a concise, evidence-based explanation of how it matches the target's research domain.",
        )

    publication_status = paper.get("publication_status")
    if publication_status not in PUBLICATION_STATUSES:
        report.fail(
            f"publication_status_invalid:{key}",
            f"publication_status must be one of {sorted(PUBLICATION_STATUSES)}, got {publication_status!r}.",
        )
    elif is_target:
        if publication_status != "not_applicable":
            report.fail(
                f"publication_status_invalid:{key}",
                "The target record must use publication_status='not_applicable'.",
            )
    elif publication_status not in {"published", "accepted_pre_proceedings"}:
        report.fail(
            "publication_evidence_missing",
            f"Core comparator {key!r} must have an official accepted/published record; got publication_status={publication_status!r}.",
        )
    elif not _is_str(paper.get("publication_url")):
        report.fail(
            "publication_evidence_missing",
            f"Paper {key!r} claims a published or accepted record but has no publication_url.",
        )

    abstract_status = paper.get("abstract_status")
    if abstract_status not in ABSTRACT_STATUSES:
        report.fail(
            f"abstract_status_invalid:{key}",
            f"abstract_status must be one of {sorted(ABSTRACT_STATUSES)}, got {abstract_status!r}.",
        )
    elif is_target:
        if abstract_status != "not_applicable":
            report.fail(
                f"abstract_status_invalid:{key}",
                "The target record must use abstract_status='not_applicable'.",
            )
    elif abstract_status == "not_applicable":
        report.fail(
            "abstract_evidence_missing",
            f"Paper {key!r} is a core comparator but carries abstract_status='not_applicable'.",
        )
    elif not _is_str(paper.get("abstract_url")):
        report.fail(
            "abstract_evidence_missing",
            f"Paper {key!r} has abstract_status={abstract_status!r} but no abstract_url. A pair of "
            "verified|abstract-unverified without the URL it was checked against is unfalsifiable.",
        )
    reading = paper.get("reading") if isinstance(paper.get("reading"), dict) else {}
    full_text_read = reading.get("mode") == "full_text"
    if (
        not is_target
        and not full_text_read
        and abstract_status == "abstract-unverified"
        and paper.get("evidence_level") not in (None, "metadata_only")
    ):
        report.fail(
            "evidence_level_exceeds_abstract_status",
            f"Paper {key!r} marks its abstract unverified but claims evidence_level="
            f"{paper.get('evidence_level')!r}. An abstract that was not retrieved cannot be the "
            "basis for abstract-level evidence.",
        )

    if not is_target and key not in waived and paper.get("evidence_level") != "full_paper":
        report.fail(
            "evidence_level_below_full_text",
            f"Paper {key!r} carries evidence_level={paper.get('evidence_level')!r} but is not "
            "covered by a waiver. Every core comparator must be read in full "
            "(evidence_level='full_paper'); move unread papers to adjacent_papers instead.",
        )

    ccf_status = paper.get("ccf_status")
    if ccf_status not in CCF_STATUSES:
        report.fail(
            f"ccf_status_invalid:{key}",
            f"ccf_status must be one of {sorted(CCF_STATUSES)}, got {ccf_status!r}.",
        )
    elif is_target:
        if ccf_status != "not_applicable":
            report.fail(
                f"ccf_status_invalid:{key}",
                "The target record must use ccf_status='not_applicable'.",
            )
    else:
        allowed = ALLOWED_CCF_BY_POLICY[policy]
        if ccf_status not in allowed:
            report.fail(
                "ccf_gate_failed",
                f"Paper {key!r} has ccf_status={ccf_status!r}, which fails the venue gate "
                f"for policy {policy!r} (allowed: {sorted(allowed)}). Venue classification is a "
                "property of the official list, not of the paper's venue name.",
            )
        source_field = "domain_status_source_url" if ccf_status == "domain_top" else "ccf_source_url"
        if not _is_str(paper.get(source_field)):
            code = "domain_status_source_missing" if ccf_status == "domain_top" else "ccf_source_missing"
            report.fail(
                code,
                f"Paper {key!r} needs {source_field} for its venue classification.",
            )

    if not _is_str(paper.get("source_url")):
        report.fail(
            f"source_url_missing:{key}",
            f"Paper {key!r} needs a non-empty source_url.",
        )
    if not _is_str(paper.get("justification")):
        report.fail(
            f"justification_missing:{key}",
            f"Paper {key!r} needs a non-empty justification.",
        )
    if "scores" in paper and paper["scores"]:
        report.fail(
            "score_axes_retired",
            f"Paper {key!r} carries the retired five-axis `scores` table. Rank is now expressed "
            "ordinally via relation_to_target and decisive_factor.",
        )


def _check_reuse(paper: dict, review: dict, rubric_version, report: _Report) -> None:
    source = review.get("reused_from")
    if source is None:
        return
    key = paper.get("key")
    if paper.get("kind") == "target":
        report.fail("target_review_reused", "The target must get a fresh reader on every run; only peer reviews may be reused.")
        return
    if not isinstance(source, dict) or not all(_is_str(source.get(f)) for f in ("run", "reviewed_on", "rubric_version")):
        report.fail("reuse_provenance_missing", f"Paper {key!r} reused_from needs run, reviewed_on, and rubric_version.")
        return
    if source["rubric_version"] != rubric_version:
        report.fail("reuse_rubric_mismatch", f"Paper {key!r} was reviewed under rubric {source['rubric_version']!r}, not {rubric_version!r}; dispatch a fresh reader.")


def _check_independent_reviews(papers: list, method, rubric_version, report: _Report) -> None:
    """Scores inform comparison; a contrary ordering needs an explicit reason."""
    targets = [p for p in papers if p.get("kind") == "target"]
    target_review = targets[0].get("independent_review") if len(targets) == 1 else None
    target_score = target_review.get("score") if isinstance(target_review, dict) else None
    reviewers = set()
    same_band = []
    for paper in papers:
        review = paper.get("independent_review")
        reading = paper.get("reading")
        if not isinstance(reading, dict) or reading.get("mode") != "full_text":
            if review is not None:
                report.fail("unread_review_scored", "Unread papers must use independent_review=null.")
            continue
        if not isinstance(review, dict):
            report.fail("independent_review_missing", f"Paper {paper.get('key')!r} needs a returned independent review.")
            continue
        _check_reuse(paper, review, rubric_version, report)
        reviewer = review.get("reviewer_id")
        if _is_str(reviewer) and method == "subagent_parallel":
            if reviewer in reviewers:
                report.fail("reviewer_reused", "Each paper, including the target, needs a distinct independent reader.")
            reviewers.add(reviewer)
        for field in ("reviewer_id", "summary", "score_rationale", "next_level_requirement"):
            if not _is_str(review.get(field)):
                report.fail("review_boundary_missing", f"Paper {paper.get('key')!r} needs independent_review.{field}.")
        for field in ("strengths", "weaknesses"):
            values = review.get(field)
            if not isinstance(values, list) or not values or not all(_is_str(v) for v in values):
                report.fail("review_evidence_missing", f"Paper {paper.get('key')!r} needs anchored {field}; state an evidence-bound absence if none were found.")
        score = review.get("score")
        if type(score) is not int or not 1 <= score <= 5:
            report.fail("review_score_invalid", "Independent quality scores must be integers 1..5 under the shared rubric.")
            continue
        # Optional multi-dimensional value bands (Schema 3.2)
        novelty_band = review.get("novelty_band")
        if novelty_band is not None and (type(novelty_band) is not int or not 1 <= novelty_band <= 5):
            report.fail("novelty_band_invalid", f"Paper {paper.get('key')!r} novelty_band must be an integer 1..5 if provided.")
        impact_band = review.get("practical_impact_band")
        if impact_band is not None and (type(impact_band) is not int or not 1 <= impact_band <= 5):
            report.fail("practical_impact_band_invalid", f"Paper {paper.get('key')!r} practical_impact_band must be an integer 1..5 if provided.")
        relation = paper.get("relation_to_target")
        if type(target_score) is int and (
            (relation == "above" and score < target_score)
            or (relation == "below" and score > target_score)
        ) and not _is_str(paper.get("score_override_reason")):
            report.fail("score_override_unexplained", f"Paper {paper.get('key')!r} is ordered against its independent score; explain the evidence without changing the score.")
        if type(target_score) is int and relation in {"above", "below"} and score == target_score:
            same_band.append(paper.get("key"))
            if not _is_str(paper.get("same_band_reason")):
                report.fail(
                    "same_band_direction_unexplained",
                    f"Paper {paper.get('key')!r} shares the target's score band but is marked {relation!r}; "
                    "give same_band_reason with decisive evidence from both papers, or use 'unresolved'.",
                )
    if same_band:
        report.note(f"Directional relations within the target's score band: {same_band}.")


def validate(payload: dict) -> dict:
    report = _Report()

    if not isinstance(payload, dict):
        report.fail("payload_invalid", "ranking.json must parse to a JSON object.")
        return _finalize(report)

    if payload.get("schema_version") not in SUPPORTED_SCHEMAS:
        report.fail(
            "schema_version_unsupported",
            f"schema_version must be one of {sorted(SUPPORTED_SCHEMAS)}, got {payload.get('schema_version')!r}. "
            "Preserve historical runs; re-evaluate them in a "
            "new directory rather than relabeling an old artifact.",
        )

    run = payload.get("run")
    if not isinstance(run, dict):
        report.fail("run_missing", "run must be an object.")
        run = {}

    papers = payload.get("papers")
    if not isinstance(papers, list):
        report.fail("papers_missing", "papers must be an array.")
        return _finalize(report)

    policy = _check_scope(run, report)
    _check_manuscript(run, report)
    _check_peer_set(run, report)
    if "acceptance_bar" in payload or any(
        key in run for key in ("target_acceptance_rate", "target_acceptance_rate_source_url", "acceptance_rate_note")
    ):
        report.fail("acceptance_assessment_retired", "Rankings compare papers only; omit acceptance assessments and rate inputs.")
    n, our_rank = _check_structural(payload, run, papers, report)
    _check_relations(papers, our_rank, report)
    reading_policy, waived = _check_reading_policy(run, papers, report)
    _check_dispatch(run, papers, reading_policy, report)
    for paper in papers:
        if not isinstance(paper, dict):
            report.fail("paper_invalid", f"Every entry in papers must be an object; got {paper!r}.")
            continue
        _check_reading(paper, waived, reading_policy.get("dispatch_method"), report)
        _check_evidence(paper, report)
        _check_provenance(paper, policy, waived, report)

    _check_independent_reviews(papers, reading_policy.get("dispatch_method"), run.get("rubric_version"), report)
    interval = _check_interval(run, papers, waived, report)

    report.derived_interval = interval
    return _finalize(report)


def _finalize(report: _Report) -> dict:
    return {
        "decision": "PASS" if not report.failures else "FAIL",
        "failure_count": len(report.failures),
        "failures": report.failures,
        "notes": report.notes,
        "derived_interval": list(report.derived_interval) if report.derived_interval else None,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Validate a rank-my-paper ranking.json run.")
    parser.add_argument("ranking", type=Path, help="Path to ranking.json")
    parser.add_argument("--report", type=Path, help="Write the JSON report here.")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        payload = json.loads(args.ranking.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ranking.json not found: {args.ranking}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ranking.json is not valid JSON: {exc}", file=sys.stderr)
        return 2

    report = validate(payload)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    summary = {
        "decision": report["decision"],
        "failure_count": report["failure_count"],
        "derived_interval": report["derived_interval"],
    }
    print(json.dumps(summary, ensure_ascii=False))
    for failure in report["failures"]:
        print(f"  [{failure['code']}] {failure['message']}", file=sys.stderr)
    return 1 if report["decision"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
