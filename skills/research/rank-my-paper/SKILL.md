---
name: rank-my-paper
description: Benchmark and rank a completed manuscript against stratified published/accepted peers (CCF-A, CCF-B, or top domain venues) using independent full-text reviews, multi-dimensional quality bands (soundness, novelty, impact), and an evidence-bound comparison. Use for explicit paper benchmarking; not for ordinary related-work summaries or manuscript editing.
---

# Rank My Paper

Compare a completed manuscript against a carefully selected set of accepted, same-domain peer papers and return an evidence-bound comparison: eight ranked records by default (the target plus up to seven peers), independent reviews with shared-rubric quality scores and multi-dimensional value profiles (soundness, novelty, practical impact), a target rank or rank interval, and revision priorities. Use fewer peers when the eligible same-domain literature is smaller; never pad. Scores inform the comparison; they are not conference recommendations or acceptance probabilities. Proximity selects peers; demonstrated contribution and evidence decide comparisons.

Read [references/review-protocol.md](references/review-protocol.md) first: it defines what “objective” means here, and fixes the candidate gate, the reading and waiver rules, the ordinal contract, the report contract, the JSON schema, and the audit gate. Reader prompts: [references/reader-agent-prompt.md](references/reader-agent-prompt.md).

## Contract

- Read the manuscript completely and record the same evidence profile and anchors used for peers; check available supplements when a decisive claim depends on them.
- Independently review every core paper, including the target: exactly one fresh reader per paper not covered by a reusable peer review. Set and log that exact dispatch budget before launch; readers are leaf agents and do not spawn reviewers, auditors, or critics. No extra agent pass reviews the readers or their synthesis. Readers receive no other papers, prior scores, target identity, or desired outcome. Freeze returned profiles and scores before ranking; see the protocol for the single bounded same-reader follow-up.
- A paper whose official full text is unobtainable leaves the core for `adjacent_papers`, unless the user grants the waiver — then it is capped at `confidence: "low"` and the run reports a rank interval. Never self-grant it.
- Default 8 ranked records including the target, so select up to 7 peers; honor an explicit `N` only when enough eligible peers exist, and rank fewer rather than padding. Stratify peers when possible into `sota_ceiling` (frontier), `median_accepted` (benchmark), and `marginal_pass` (boundary).
- Every peer must be an officially accepted/published paper (including verified pre-proceedings acceptance at flagship venues) in the target's same research domain and pass the frozen venue gate. Default to `domain_peer` (CCF-A/B or an officially verified top venue in the target's field); `any_ccf_a` and `ccf_ab` remain selectable. Venue tier never substitutes for same-domain fit.
- Never modify the manuscript, bibliography, ledger, or code; write only under `<manuscript-directory>/rank_my_paper/`.
- No experiments, training, or installs; read-only inspection and web retrieval only.

## Workflow

1. Freeze scope: manuscript path and hash, venue and track, venue policy, comparison basis, CCF edition, publication cutoff, rank size, reading policy, rubric version, output directory. If a previous run exists, carry its peer set forward by default (protocol §2.1).
2. Profile the target: root question, task, evaluation object, mechanism, setting, demonstrated contribution, closest cited work, strongest alternative explanation. Freeze this evidence profile before assigning relations.
3. Fresh search only (first run or explicit request): search a pool of at least 3x the requested peer count (ranked count minus the target), stratifying across anchor tiers (SOTA ceiling, median accepted, marginal pass) when the literature supports it; deduplicate and freeze each candidate's domain-fit and inclusion reason before judging quality. This discovery pool is not a review budget.
4. Gate each core candidate on same-domain fit, an official accepted/publication record (or verified pre-proceedings acceptance), and a venue classification meeting the frozen policy; keep cross-domain or unverified candidates adjacent instead of ranking them.
5. Dispatch only the precomputed reader budget under the shared rubric (§4.1); preserve each reader's reading evidence and independent review (including optional novelty and impact bands) verbatim, then apply the reading gate.
6. Compare supported contributions on a shared basis using evidence from both papers. Set `above`, `below`, or `unresolved` (default `unresolved` when scores share a band, or explain trade-offs via Pareto co-frontier analysis); give the decisive evidence, strongest counterargument, and reason for any ordering that contradicts the independent scores.
7. Derive the target position from these relations (§4). Unresolved or waived comparisons require a rank interval and null point ranks.
8. Write `review.md`, `ranking.json`, `sources.md`; run `scripts/validate_ranking.py` and require exit 0; for re-runs include `scripts/diff_runs.py` output separating manuscript change from peer-set change; recheck the manuscript hash and protected paths.

## Evidence discipline

Judge the target as written and references from the full text their readers returned. Cite target claims to sections or pages, and reference claims to a full-text URL plus anchor locator; an abstract-level claim belongs in the uncertainty section, not in a relation. For the target use claim → evidence → assumption → strongest alternative → confidence, and treat a positive result, a null result, an interval crossing zero, and a missing measurement as different states.

A high or low rank must survive the same scrutiny. Do not tune the output toward praise, rejection, or a previous review. Historical results concern their recorded revisions; write new runs separately.
