# Independent Reviewer Prompt

Dispatch exactly one fresh reader for each core paper not covered by reusable peer review; the target is always fresh. Each reader is a leaf agent: it sees only one paper and the shared rubric from [review-protocol.md §4.1](review-protocol.md), and does not spawn agents or review another reader. A reader must not receive target identity, other papers, previous reviews or scores, or the intended ranking. Preserve the returned profile before synthesis. Use the same questions and rubric for every paper; candidate provenance checks remain the coordinator's job. The same-reader follow-up limit in review-protocol §3.2 is the only exception; never dispatch a replacement reviewer.

## Dispatch rules

1. For each paper that needs a fresh review, use one reader with an isolated conversation context (`fork_turns: "none"` or the host equivalent). The target always receives its own independent reader; no reader inherits the coordinator transcript or sees a comparator.
2. Schedule independent readers concurrently within the host's capacity.
3. For the target, read the supplied manuscript and supplements. For published peers, obtain the **official full text**: publisher HTML/PDF via the DOI or
   proceedings entry first; conference proceedings PDF second; author-manuscript or
   preprint PDF (arXiv, OpenReview, institutional repository) only as a documented
   supplement, never as a substitute for the published record's content when both exist.
4. An abstract page, a search snippet, a citation entry, or a "similar papers" list is not
   full text. If only those are reachable, the reader returns `mode: "full_text_unavailable"`
   with the reason and everything it could and could not verify.
5. The reader returns one JSON profile plus a short prose note. Save the original profile; copy its evidence and `independent_review` unchanged into the run artifacts.
6. The producing agent records the exact fresh-reader budget in `ranking.json → run.reading_dispatch`
   (`method`, `reader_count` = one per non-reused core review, `dispatched_on`) and lists each reader in `sources.md`. Do not launch separate critique, audit, synthesis, or review-of-review agents.
7. In a carried-forward run (review-protocol §2.1), a peer whose saved review is reusable gets no new reader: copy its saved profile unchanged and add `reused_from`. The target always gets a fresh reader.

## Prompt template

```text
Independently review ONE paper in full and score its demonstrated scientific quality under the supplied rubric. You are not ranking it or recommending acceptance at a conference. Judge its own claims, with evidence proportionate to them.

PAPER
  Title: <title>
  Paper identifier: <neutral id>
  Full-text locations and available supplements: <paths or URLs>
  Shared rubric: <paste review-protocol.md §4.1 unchanged>

TASK
1. Read the supplied local manuscript or obtain its published full text. Record exactly what you opened. Inspect available supplements where needed to verify a central claim; no experiments or installs.
2. Read it completely enough to answer the profile questions below; at minimum the method,
   the results (including tables/figures), and the limitations must be read, not skimmed
   from the abstract.
3. Extract 3-8 verbatim anchors. An anchor is a locator plus an exact quote of at most 30
   words. Anchors must be the spans that decide your profile answers, not decorative ones.
4. Assign the highest quality band supported by the evidence. Explain why it meets that band and what prevents the next one; do not use publication status as evidence.
5. If you cannot verify something, put it in could_not_verify. Never guess, never infer a
   number from a snippet, and never quote the abstract as if it were the full text.

PROFILE QUESTIONS
- claim: what does the paper claim, and what contribution is actually established? Separate them when they differ.
- identification: does the evidence actually identify the claimed effect or mechanism?
  Name the design element that decides this (controls, splits, randomisation, uncertainty
  unit, multiplicity treatment, held-out evaluation), and say what it does not cover.
- scope: what data, models, scale, or deployment regime was tested, and what is claimed
  beyond it?
- limitations: what does the paper itself concede? Which limitations threaten its claim, and which are deliberate scope choices? Do not penalize a paper for not solving an unstated application.
- alternatives: what is the strongest explanation other than the paper's own, and is it
  excluded by the design or merely unmentioned?
- presentation: how is the visual presentation, figure storytelling, table craftsmanship, and layout execution? Does Page 1 offer a self-contained teaser/architecture figure? Do tables follow booktabs without vertical lines? Are figures vector quality with coherent palette? Is the layout tightly budgeted without orphan gaps?
- internal_consistency:
  1. table_recomputation: recompute at least one key table row/column/metric (e.g. Table 1 or 2). Check if arithmetic, percentages, and cost accounting (Tokens / Latency / GPU hours / Memory) hold without unexplained anomalies.
  2. claim_vs_baseline_alignment: compare headline claims from Abstract/Intro (e.g. "higher accuracy at lower cost") against every comparator arm in tables and ablations. Does any baseline or ablation branch outperform the proposed method unexpectedly? Does token/compute cost contradict the efficiency claim?
  3. fatal_flaw_cluster: classify any critical defect into 8 clusters: A (Internal Contradiction/Misattribution), B (Missing Isolating Baseline), C (Anonymity/Compliance), D (Generalization Limits), E (Inferential Deficit), F (Artifact Gap), G (Unreal Environment), H (Unproven Cost). Note: A-cluster flaws are individually fatal.
- hard_gates:
  1. anonymity: does the paper leak author identity or institutional affiliation in text, acknowledgments, PDF metadata, or data/code availability links (e.g. personal GitHub URLs)?
  2. scope: does the paper fall within the hard subject scope of the target conference?
  3. fatal_violations: list concrete hard gate violations; empty list if compliant.
- relation_material: the strongest demonstrated contribution, its strongest evidence, and the most consequential unresolved alternative. Apply the same evidential scrutiny to each.

OUTPUT (strict JSON, then <=200 words of prose)
{
  "obtained": {
    "mode": "full_text" | "full_text_partial" | "full_text_unavailable",
    "full_text_url": "<the exact URL you read>",
    "obtained_via": "local_file" | "publisher_html" | "publisher_pdf" | "proceedings_pdf" |
                    "aclanthology_pdf" | "arxiv_pdf" | "openreview_pdf" | "none",
    "coverage_note": "<what parts you actually read, e.g. 'all sections; appendices skimmed';
                      if the text was reconstructed via indexed/verbatim extraction rather
                      than a linear open, say so here and list the sections covered>",
    "blocked_by": "<paywall, no PDF, only abstract page, ... when mode is not full_text>"
  },
  "claim": "...", "identification": "...", "scope": "...",
  "limitations": "...", "alternatives": "...",
  "internal_consistency": {
    "table_recomputed": "<Table X row/col recomputed and outcome>",
    "claim_vs_baseline_alignment": "<headline claim vs comparator numbers>",
    "contradiction_found": false,
    "fatal_flaw_cluster": null,
    "details": "<concrete evidence or 'self-consistent'>"
  },
  "hard_gates": {
    "anonymity_preserved": true,
    "scope_compliant": true,
    "fatal_violations": []
  },
  "relation_material": "...",
  "anchors": [
    {"locator": "Section 4.2 / Table 2", "quote": "<=30 words verbatim", "supports": "identification"}
  ],
  "could_not_verify": ["..."],
    "independent_review": {
      "reviewer_id": "<actual reader id>",
      "summary": "<claim versus established contribution>",
      "strengths": ["<strength and source anchor>"],
      "weaknesses": ["<material limitation and source anchor>"],
      "score": "<integer 1..10 from the shared rubric: defense/identification rigor>",
      "novelty_band": "<optional integer 1..5: problem ambition and conceptual originality>",
      "practical_impact_band": "<optional integer 1..5: systems utility and economic dividend>",
      "presentation_band": "<optional integer 1..5: visual presentation, layout craftsmanship, and table rigor>",
      "score_rationale": "<evidence that earns this level>",
      "next_level_requirement": "<what prevents the next level; at 10 why it exceeds 9>"
    }
  }

RULES
- You are a leaf reviewer: assess only the one assigned paper; do not call or spawn subagents, request another reviewer, or review another reader's work.
- Every statement about the paper must be traceable to one of your anchors.
- Quote verbatim inside "quote"; do not paraphrase inside quotation marks.
- The mode reflects coverage, not access path: a verbatim indexed extraction of the
  official text can be full_text when every claim-deciding main-text element (abstract,
  intro/contributions, complete method, complete setup and results incl. table/figure
  content, limitations/conclusion) was actually read. Use full_text_partial only when
  one of those parts was genuinely not covered; unread appendix internals, figure
  pixels, and checklist answers belong in could_not_verify and do not force partial.
- If the paper is not reachable in full, return mode full_text_unavailable with the URLs you
  tried, independent_review: null, and a could_not_verify list naming what could not be assessed.
- Do not soften or harden findings to be useful. Report what the paper does and does not
  establish.
```

## What the producing agent does with the result

- Copies `obtained` into `reading` (`mode`, `full_text_url`, `obtained_via`, plus
  `read_by: "subagent"`, `coverage_note`, `anchors`, `could_not_verify`). Copy
  `independent_review` separately without changing its score or justification.
- Preserves `internal_consistency` and `hard_gates` in the paper record.
  If `hard_gates.anonymity_preserved == false` or `hard_gates.fatal_violations` is non-empty,
  mark the paper `hard_gate_vetoed: true`; a vetoed paper receives a fatal veto ticket and
  is segregated from clean peer intervals.
  If `internal_consistency.contradiction_found == true` with an A-cluster flaw, record it as a
  fatal flaw, blocking top-tier placement regardless of external novelty.
- Uses `identification`, `scope`, `limitations`, `internal_consistency` and `alternatives` when writing the
  `decisive_factor` and the justification paragraph, and cites at least one anchor in
  `review.md`.
- Writes directional relations only from full-text reviews. A waived record remains
  `unresolved`, with `independent_review: null` and `confidence: "low"`, and widens the rank interval.
- Carries `could_not_verify` items into the review's residual-uncertainty section.
