# Rank My Paper: Review Protocol and Output Contract

This reference is read when `$rank-my-paper` is invoked. It supplies the details that must remain stable across runs while allowing the candidate search to adapt to the manuscript's field.

**What “objective” means here.** Candidate inclusion, source gates, reading depth, comparison relations and rank arithmetic are explicit, reproducible, and checked by `scripts/validate_ranking.py` rather than by the producing agent's prose. The comparison itself remains an expert judgment: surface its uncertainty instead of presenting a rank as ground truth, and treat the validator as the floor, not as a certificate of correctness.

## 1. Scope freeze

Record these fields at the top of the run and in `sources.md`:

- manuscript path, file type, revision hash, and read date;
- target venue or track, target field, and publication cutoff;
- recency window: 3 years (default: strictly papers published within `target_year - 3` to `target_year` are eligible for the core comparator cohort);
- comparator venue policy: `domain_peer` (default; CCF-A/B or an officially verified top venue
  in the target's field), `any_ccf_a`, or `ccf_ab`; same-domain fit is a separate mandatory gate;
- shared comparison basis, chosen before judging winners;
- CCF list edition, category, official source URL, and verification date;
- requested ranked count and whether the target is included;
- peer-set mode (`fresh_search` or `carried_forward`), the previous run it continues, and the
  rubric version (§2.1);
- reading policy: full-text reading required for every core comparator, the dispatch method
  (`subagent_parallel` or `self`), and whether the user granted the abstract-level waiver
  (§3);
- output directory and the fact that no experiments were rerun.

Venue classification establishes publication quality and provenance, not topical fit. A paper accepted at a
CCF-A venue passes only the venue gate; it must still pass the same-domain proximity and comparability checks below. CCF membership alone does not justify ranking it. Do not shrink the candidate pool to the target's own venue
or venue family, and do not admit a paper merely because it shares a venue with the target.

The CCF label is a venue classification, not a property that can be inferred from a paper's title, arXiv identifier, citation count, or the assistant's memory. If the official list edition is unavailable or the venue cannot be mapped unambiguously, use `ccf_unverified`, do not call the paper a verified core comparator, and state the resulting limitation. When domain flagship venues outside CCF are admitted under `domain_peer`, record the explicit domain status as `domain_top` with justification.

Every core peer must be an officially accepted, peer-reviewed publication: conference papers need an official proceedings/publisher record, and journal papers need the official version-of-record entry. Record the publication URL. A preprint-only record, workshop page, acceptance claim without an official publication record, or search-result snippet is not sufficient; mark unverifiable records `publication_unverified` and keep them out of the core. If the venue uses online-first publication, record the official publication date and the rule used.

## 2. Target profile and candidate search

Read the complete manuscript before selecting neighbors. Extract:

1. the root scientific question and the decision the paper is meant to change;
2. the task/data/model/operating setting;
3. the estimand, objective, or evaluation target;
4. the central mechanism or algorithmic object;
5. the strongest claimed contribution and its scope boundary;
6. the paper's own nearest cited work and explicit comparator set.

Build a discovery pool at least three times the requested peer count (ranked count minus the target) when the literature supports it. This is a candidate-screening pool, not a reader or review budget: only selected, eligible core peers receive independent readers. Use several independent routes:

- exact title, abstract, keyword, and mechanism searches;
- backward citations in the manuscript and its closest papers;
- forward citations and “similar papers” only for discovery;
- official proceedings, journal archives, the target field's major venues, and the official CCF list.

Use bibliographic indexes and search engines to find candidates, not as the final evidence for technical claims. Prefer English queries and primary sources. Search-result snippets, citation counts, rankings, and a paper's own “state of the art” wording are not evidence of method quality.

For each candidate, record a relevance profile before applying the CCF gate:

| Dimension | Question |
|---|---|
| Domain fit | Is it in the target's same research domain? State the specific field and evidence for the match. |
| Root question | Does it address the same scientific or system-level question? |
| Task/object | Does it study the same task, estimand, objective, or decision object? |
| Mechanism | Does it use or challenge the same technical mechanism? |
| Setting | Does it operate under a comparable data, model, feedback, or deployment regime? |
| Evaluation | Does success mean a comparable outcome, not merely a related metric? |

The default is eight ranked records including the target: select up to seven peer papers (or 15 core papers in full AC Bidding mode). Every ranked peer must pass all **four gates**:
1. **Publication Gate**: officially accepted, peer-reviewed publication;
2. **Venue Gate**: tier within the frozen policy (`domain_peer` by default);
3. **Same-domain Gate**: technical and estimand proximity in the same research field;
4. **Recency Gate (近 3 年时效性门禁)**: published within the last 3 calendar years ($\text{year} \ge \text{target\_year} - 3$). The peer set benchmarks against the current empirical and theoretical frontier; foundational or older historical works (>3 years) belong in background citations and related work, not in the active competitive comparator cohort.

**Stratified Comparator Cohort (Schema 3.2):** To prevent uncalibrated ranks where peers are all unassailable classics or all marginal entries, the peer set should ideally stratify across three anchor tiers when the literature supports it:
- `sota_ceiling`: 2–3 flagship publications establishing the empirical or theoretical frontier in the field;
- `median_accepted`: 3–4 standard accepted papers representing the median publication quality at the target tier;
- `marginal_pass`: 1 borderline paper representing the viable entry threshold.
Legacy role labels (`direct`, `method`, `foundational`) remain supported.

Define the target's field from its question, task/object, mechanism, and setting; require each peer's inclusion rationale to identify a concrete overlap in the same field. If fewer than seven papers pass, rank fewer—never relax the gates or pad with cross-domain analogues. Maintain an adjacent list for unverified work, cross-domain candidates, and candidates that are materially less relevant.

Freeze each candidate's domain-fit and inclusion reason before assigning quality relations. Search the strongest accepted direct alternatives and relevant negative results, not only work cited favorably by the target. A different task, older publication date, or absence of the target's named mechanism is not by itself a quality deficit. Report the domain-fit basis for every ranked peer in `ranking.json` and the report, as well as how many eligible same-domain peers were found. The selected set is not a random sample of submissions or accepted papers.

### 2.1 Re-runs: carry the peer set forward

A rank is conditional on its peer set, so re-searching peers on every revision mixes two changes: the manuscript and the comparators. Historical re-runs of one paper shared only 9 of 15 papers between consecutive runs, which makes rank movement uninterpretable.

When a previous run of the same paper exists under `<manuscript-directory>/rank_my_paper/`, default to `peer_set.mode: "carried_forward"`:

1. Run `scripts/diff_runs.py <previous>/ranking.json <draft>/ranking.json` (or read the previous run) to list peers whose independent reviews are reusable: read in full, under the same `rubric_version`.
2. Keep the previous core. Reuse those peer reviews unchanged, adding `independent_review.reused_from: {run, reviewed_on, rubric_version}`; copy their `reading` object too. A peer review judges only the peer, so it does not depend on the target revision.
3. Always dispatch a fresh reader for the target. Never reuse a target review.
4. Re-read a peer when its official version changed, the rubric changed, or its prior reading was partial or disputed.
5. Change the core only for a stated reason (new publication before the cutoff, a revised target scope, a found error). Record every change in `peer_set.added` / `peer_set.removed` with the reason in `sources.md`.

Use `fresh_search` for the first run, when the user asks for a new search, or when the target's root question changed. After any run, `diff_runs.py` separates target-score change, relation changes, and peer-set change; report that separation instead of a bare rank delta.

## 3. Full-text reading and source verification

### 3.1 Why the abstract is not enough

The ranking turns on whether a paper's evidence identifies its claim and whether
alternative explanations were excluded — axes that an abstract does not report. An
abstract says what a paper asserts, never what it controlled, split, held out, or left
unresolved. A run that assigns head-to-head relations from abstracts is therefore ranking
on the authors' own claims, and the confidence cap that used to be attached to
`abstract_only` did not travel to the rank, which aggregates all relations at once. Full
text is now the minimum evidence for a core record.

### 3.2 What counts as full text

The **official full text** is the publisher's article (HTML or PDF) reached from the DOI,
the proceedings entry, or the journal record. A proceedings PDF, an ACL Anthology PDF, a
NeurIPS/ICLR proceedings page, or an OpenReview camera-ready PDF all qualify. An author
manuscript or preprint PDF qualifies only as a documented supplement to a published record,
and the run must say which was read. The following never count as full text: an abstract
page, a search snippet, a citation entry, a "similar papers" list, a slide deck, or a
reviewer's summary.

**Mode reflects content coverage, not the access path.** The mode names what was
actually read, not how the bytes were reached. A linear PDF open and a verbatim indexed
extraction of the official text (search-index snippets of a proceedings PDF, arXiv/ar5iv
HTML, an OpenReview text render) are equivalent access paths when the coverage is
complete; the path is recorded in `obtained_via` and `coverage_note`, not in the mode.

- `full_text`: every claim-deciding main-text element was read verbatim — the abstract,
  introduction/contributions, the complete method section, the complete experimental
  setup and results (including the reported content of tables and figures), and the
  limitations/discussion/conclusion. Appendix proof internals, figure pixel data,
  checklist answers, related-work fragments, and reference entries are *not*
  claim-deciding: when unread they belong in `could_not_verify` and do not force a
  partial mode.
- `full_text_partial`: some claim-deciding main-text part was genuinely not covered
  (e.g. a results table, a method subsection, or the limitations section could not be
  reached). A partial reading cannot support a scored core review.
- `full_text_unavailable`: the official text could not be reached at all; §3.5 applies.

**Bounded same-reader follow-up.** A reader may receive at most one targeted follow-up
for a paper, only to resolve a material factual error or a coverage ambiguity; combine
both questions if they arise. Continue the same reader context—never dispatch a
replacement reviewer. For a `full_text_partial` result whose `coverage_note` suggests
claim-deciding elements were covered through a non-linear access path, enumerate the
required elements and ask whether each was read. If the reader confirms complete
coverage, it re-emits the profile with `mode: "full_text"`, retains the access-path note
and residual `could_not_verify` items, and leaves the independent review unchanged. If
not, keep `full_text_partial` and remove the paper from the core under §3.5. If the same
reader cannot be continued or the issue remains unresolved after this one follow-up,
record the limitation and apply the reading gate; do not launch another agent. Record
any follow-up and outcome in `sources.md`. Never upgrade a mode silently or on the
producing agent's inference.

### 3.3 Dispatch

Every core paper, including the target, must have a full-text review. Dispatch a **fresh reader agent in an isolated context** for each review not covered by a reusable peer review. Before dispatch, compute the exact fresh-reader budget: one reader for each core paper without a reusable peer review (the target is always fresh). Dispatch no other agents for critique, audit, synthesis, or review-of-review; each reader is a leaf agent and must not spawn agents. The validator requires `reading_dispatch.reader_count` to equal this budget. Each reader sees only its assigned paper, available supplements, and the shared rubric. Do not reveal which paper belongs to the user, previous scores, the candidate set, or the emerging ranking. Use neutral paper identifiers and omit venue prestige cues from the prompt; do not alter source content to manufacture anonymity. The prompt template, the structured output schema, and the dispatch rules are in
[reader-agent-prompt.md](reader-agent-prompt.md). A run may fall back to `read_by: "self"`
only when the host provides no dispatch mechanism. Label that run as lacking independent reviews; self-review is not equivalent to independent assessment.

### 3.4 What the run records

Each core record, including the target, carries a `reading` object with the mode, the full-text URL actually
opened, how it was obtained, who read it, a coverage note, and 3–8 short anchors. An anchor is a
locator plus a verbatim quote of at most 30 words; it is the only thing that lets a human
spot-check the reading without re-reading the paper. Anchors and the reader's
`could_not_verify` list are copied verbatim, never paraphrased. `review.md` reproduces at
least one anchor per ranked paper and carries the full dispatch log.

### 3.5 When the full text cannot be obtained

Default policy: the paper cannot be a core comparator. It moves to `adjacent_papers` with
the reason `full text unavailable` (naming what was reachable), and the core is ranked with
fewer records rather than padded. The protocol already prefers ranking fewer genuine peers
over padding the core.

**Explicit waiver.** If the user, having been told which papers are unreachable and why,
grants a waiver, those records may enter the core with `reading.mode` of
`full_text_unavailable`, `evidence_level: "abstract_only"` and `confidence: "low"`. A
waived run must mark these relations `unresolved` and report a rank interval under §4. An abstract-level waiver permits inclusion, not a directional superiority claim.

The waiver is never self-granted by the producing agent: `granted_by_user` must be `true`
and the reason must name the unreachable papers.

### 3.6 Provenance rows

Every selected or adjacent candidate still gets a provenance row with:

- canonical title, authors, venue, year, and publication status;
- official publication/proceedings URL;
- CCF list URL and edition for `A`/`B` papers, or the official domain-venue status URL for `domain_top` papers;
- venue tier classification: `A`, `B`, `domain_top`, `ccf_unverified`, or `not_applicable`;
- direct abstract URL or official full-paper URL;
- official full-text URL actually opened, with `obtained_via` and a coverage note (required
  for every core record; see §3.2 for what qualifies);
- abstract status: `verified` or `abstract-unverified` (the URL is required in both cases: it
  records what was actually opened, including when the abstract could not be retrieved);
- evidence level: `full_paper` for every core record; `abstract_only` and `metadata_only`
  exist only for waived records (§3.5) and for adjacent entries;
- candidate role: `direct`, `method`, `foundational`, or `adjacent`;
- notes on identifier corrections, version deduplication, or venue ambiguity.

A direct arXiv abstract is acceptable for abstract verification when the title and authors match, but it does not replace publication, CCF verification, or full-text reading. Prefer the official venue abstract when available. If sources disagree, retain both URLs, explain the conflict, and use the more authoritative source rather than silently choosing the convenient one.

Under a §3.5 waiver, a record whose abstract is also unavailable uses `abstract_status: "abstract-unverified"` and `evidence_level: "metadata_only"`; the validator rejects abstract-level evidence from an unverified abstract.

## 4. Comparative ranking contract

Judge scientific contribution as supported by evidence, conditional on the selected peer set. Relevance determines inclusion, not quality. Use this order:

1. whether the evidence supports each paper's central claim in its own stated scope;
2. the contribution and significance that remain after unsupported claims are removed;
3. robustness and generality within that scope;
4. technical depth and clarity when the preceding points do not distinguish them.

Apply the same standard to both sides. For an empirical effect, inspect fair controls and uncertainty; for a theorem, inspect assumptions and proof; for a benchmark, inspect construction and validation. A narrow claim supported convincingly can outrank a broader unsupported claim. An empirical paper need not have a theorem, and a theoretical paper need not demonstrate the target's application. Credit breadth only where it strengthens the claimed contribution. Publication, oral/spotlight status, citation counts, and popularity are not substitutes for evidence.

After all independent reviews and scores have been saved unchanged, compare every non-target core paper:

- `relation_to_target`: `above`, `below`, or `unresolved`;
- `decisive_factor`: the shared basis and the verified difference that decides it, or why the available evidence cannot decide;
- `justification`: cite target and peer anchors, state the strongest case for the opposite relation, and explain why it does or does not prevail.

Use the independent scores as a first reference, not a deterministic sort key. Scores in the same band do not establish an order. A directional relation that reverses the score order requires `score_override_reason` with concrete evidence from both papers; preserve the original scores. Do not average arbitrary dimension scores.

**Same-band default and Pareto Resolution.** When a peer's score equals the target's, the default relation is `unresolved`. A direction requires `same_band_reason`: a specific verified difference on the shared basis, anchored in both papers, that the rubric band is too coarse to express.
In Schema 3.2, when two papers exhibit orthogonal dominant strengths (e.g., Paper A achieves higher raw accuracy with $3\times$ compute, while Target achieves parity at 38% lower compute with early stopping), mark the relation `unresolved` with `decisive_factor: "Pareto co-frontier trade-off: [details]"`, or provide a verified asymmetric dominance argument under `same_band_reason` if one strictly Pareto-dominates the other across efficiency, quality, or visual presentation craftsmanship dimensions. In particular, when scientific identification rigor is tied, a demonstrably superior `presentation_band` (execution rigor and layout credibility) serves as a valid verified differentiator under `same_band_reason`.

Use `unresolved` for indistinguishable evidence, competing strengths without a justified priority, or a material verification gap. Keep relevant unresolved peers in the core instead of excluding inconvenient comparisons. Waived records are always unresolved. Use `adjacent_papers` for papers without a defensible shared basis and explain the exclusion.

**Dual-Axis Adjudication and Hard Gates (Schema 3.3).** Peer review adjudication operates across two orthogonal axes:
1. **Internal Soundness & Compliance Axis (The Floor):**
   - **Hard Gates Layer (`hard_gates`):** Checks non-negotiable compliance before ranking. Anonymity leakage (e.g. personal GitHub URLs in data availability), out-of-scope submission, or ethical violations trigger an immediate hard gate veto (`hard_gate_vetoed: true`). Vetoed manuscripts are segregated from the valid comparative interval.
   - **Internal Consistency Audit (`internal_consistency`):** Recomputes key tables (Table 1/2 arithmetic and cost accounting) and aligns headline claims against all internal comparator and ablation arms. Flaws are categorized into 8 clusters:
     - `A (Internal Contradiction)`: Headline claims contradicted by table numbers or hidden ablation arms. **Individually fatal**; blocks top-tier placement regardless of external SOTA novelty.
     - `B (Missing Isolating Baseline)`: Fatal only when an explicit mechanism-isolating arm is defined but omitted.
     - `C (Anonymity/Compliance)`: Hard-gate fatal.
     - `D (Generalization Limits)`, `E (Inferential Deficits)`, `F (Artifact Gap)`, `G (Unreal Environment)`, `H (Unproven Cost)`: Qualitative penalty items.
2. **External Frontier Axis (The Ceiling):**
   Once internal soundness holds, evaluate relative position against the 3-year accepted peer cohort (`above`, `below`, `unresolved`). External ranking never pardons internal self-contradiction.

The target uses `relation_to_target: "self"`. Compute:

```
low  = count(above) + 1
high = low + count(unresolved)
```

When `low == high`, `our_paper_rank` and the target's `rank` equal `low`; `run.rank_interval` is null. Core ranks form `1..n` with every `above` paper before the target and every `below` paper after it. Ordering among peers on the same side is editorial unless additional peer-to-peer evidence supports it; disclose this in the table.

When `low < high`, set `our_paper_rank` and every paper's `rank` to null and set `run.rank_interval` to `{"low": low, "high": high}`. Display the above / unresolved / below groups and the target's interval instead of an invented total order. This is an uncertainty range conditional on the chosen peers, not a statistical confidence interval. If there are no comparable peers, report insufficient comparative evidence rather than describing rank 1/1 as a strong result.

### 4.1 Shared quality rubric for independent reviews

Rubric version: `4.2-r1`. Record it as `run.rubric_version`; any wording change to this table bumps the version and invalidates reuse of earlier reviews. Freeze this rubric before dispatch and apply it to every paper's own scientific claims. Scores are ordinal quality bands, not equal-interval measurements or conference review ratings. Use integer levels (1..10); no decimal precision, preset score distribution, or target-specific cap.

| Score | Level Name | Evidence needed for the level |
|---|---|---|
| 1 | Fatal Defect / Contradicted | The central claim is contradicted by verified evidence, or a demonstrated fatal flaw (such as Cluster A internal contradiction or unrecoverable validity breach) defeats the primary contribution. |
| 2 | Severe Deficit | An interesting premise or problem setup, but missing multiple foundational baselines, essential proofs, or critical controls; alternative explanations easily defeat the main claims. |
| 3 | Clear Reject | Preliminary or suggestive results exist, but at least one essential control, ablation, fair baseline comparison, or statistical measurement needed for the central claim is absent. Leaves major alternatives open. |
| 4 | Borderline Reject | A bounded technique or empirical result is shown, but material identification weaknesses, narrow evaluation, significant leakages, or unaddressed plausible confounders prevent confidence in the findings. |
| 5 | Borderline Accept | A useful, marginally supported contribution with clear bounds. Meets minimal standards of scientific integrity, but limited in depth, robustness, or generalization scope; incremental advance over existing baselines. |
| 6 | Weak Accept (Standard Accepted) | A clear, sound, and verified contribution. Methodology is sound, standard baselines and controls are present, and the central claim is supported within its stated scope, though scope or impact remains moderate. |
| 7 | Clear Accept | A well-executed, substantial contribution. The central claims are convincingly supported by rigorous experiments or solid proofs; all primary alternative explanations are anticipated and addressed by appropriate ablations or controls. |
| 8 | Strong Accept (High Quality) | A rigorous, comprehensive, and high-impact contribution. Exceptional depth in identification and validation, thoroughly establishing superiority or novel insight across diverse benchmarks or theoretical frontiers. |
| 9 | Top-Tier / Oral Caliber | An unusually consequential advance combining deep scientific novelty, exemplary experimental/theoretical rigor, and broad utility; withstands the most stringent adversarial critique and ablation scrutiny. |
| 10 | Landmark / Paradigm Shift | Groundbreaking contribution of historic or field-defining significance, introducing foundational mechanisms or solving long-standing open challenges with flawless execution (Best Paper caliber). |

Use the highest level whose requirements the observed evidence supports, and record uncertainty in `confidence`. A central missing control cannot be compensated by polished writing, a novel name, or many unrelated experiments. Strong proofs or a decisive narrow experiment can suffice when appropriate to the claim; dataset count, model size, recency, and reputation do not mechanically raise the level. A score of 10 is allowed when justified; neither high scores nor low scores are quotas.

Each reader returns `independent_review` with `reviewer_id`, a claim/evidence `summary`, anchored `strengths` and `weaknesses`, `score`, `score_rationale` (why this level is earned), and `next_level_requirement` (what prevents the next level). At 10, the last field explains why 10 rather than 9 is justified and names remaining limits.

**Multi-Dimensional Value Profile (Schema 3.2):** To decouple conceptual breakthrough from empirical defense depth and craftsmanship, readers optionally return three orthogonal 1–5 diagnostic bands:
- `novelty_band` (1–5): Evaluates problem ambition and conceptual originality (1: trivial increment, 3: useful new module/insight, 5: groundbreaking paradigm shift);
- `practical_impact_band` (1–5): Evaluates systems utility, efficiency dividend, or commercial deployability (1: purely synthetic/toy, 3: clear bounded practical utility, 5: decisive orders-of-magnitude systems breakthrough);
- `presentation_band` (1–5): Evaluates visual presentation craftsmanship, figure storytelling, table rigor, and layout discipline (representing ~15%–20% weight in peer review first impressions):
  1. *Crude / Amateur (1)*: Missing teaser; pixelated raster screenshots; tables with vertical lines (`|c|c|`); glaring overflows/widows/orphans or broken layout.
  2. *Marginal / Draft (2)*: Basic structure present but unpolished; default raw matplotlib/jet colormaps; unaligned table decimals; significant blank space on final page.
  3. *Standard Accepted (3)*: Clean publication-grade layout; vector PDF diagrams; standard `booktabs` three-line tables; tight page budgeting ($\ge 95\%$ fill); clear visual flow.
  4. *Polished / Flagship-like (4)*: High-concept, self-contained Page-1 teaser figure; coherent academic color palette (Okabe-Ito/Paul Tol); champion tables with standard errors ($\pm \text{std}$) and bolded SOTA highlights; impeccable float rhythm.
  5. *Showcase / Artifact-level (5)*: Flawless visual storytelling (the core contribution can be deduced purely from figures and tables); exhibition-grade vector infographics matching top-tier flagship papers (Nature/ICLR spotlight caliber).

The primary `score` remains the governing index for ordinal ranking, while `novelty_band`, `practical_impact_band`, and `presentation_band` populate the multidimensional radar in `review.md`. An inaccessible or partially read paper has `independent_review: null`, not an invented score.

Store each returned profile before synthesis and keep the reader identity in the dispatch log. If a reader made a material factual error, use the single same-reader follow-up allowed by §3.2, preserving both versions and the reason. If that follow-up was already used or is unavailable, retain and disclose the unresolved issue rather than dispatching another reviewer. The coordinator must not rewrite scores to fit the desired ranking.

### 4.2 Comparison-only boundary

Do not emit `acceptance_bar`, acceptance probabilities, or rate-derived thresholds. A selected set of published neighbors supplies neither a submission-population distribution nor a calibrated acceptance model. The shared 1–10 quality bands are not a conversion to ICLR or other conference ratings. A conference recommendation, if explicitly requested, is a separate review task.

Schema 3.x replaced the old acceptance-rate conversion with independent anchored reviews; 3.1 adds peer-set carry-forward, review reuse, and the same-band rule. Preserve historical runs as historical artifacts; a new assessment needs a new run directory and current evidence, not a schema relabel.

## 5. Symmetric evidence review

Before assigning relations, complete the target's independent review using the reader's claim / identification / scope / limitations / alternatives questions. Use manuscript evidence, not prior praise, the author's novelty framing, or planned work. Record target reading anchors as for peers; full text permits high confidence but does not guarantee it.

Check supplied supplements, code, logs, and summary tables read-only where a decisive claim depends on them: reconcile the claimed procedure, denominator, comparison budget, and evaluation split with the accessible artifacts. State exactly what was checked. Missing access is a verification limit, not proof of failure. Do not run experiments or require unavailable code as a blanket condition of quality.

For both target and peers, test positive and negative interpretations:

- Is the main construct actually the deployment or decision object named in the claim?
- Could the headline ordering be caused by near ties, selection, leakage, an implementation choice, or an unmeasured nuisance variable?
- Are the comparator, baseline, data split, randomization, uncertainty unit, and multiplicity treatment fair and explicit?
- Does the external-validity claim exceed the model, data, scale, geometry, or feedback regime tested?
- Does an inconclusive estimate get reported as inconclusive rather than as zero effect or proof of failure?

The review should name the strongest remaining alternative explanation and the smallest evidence or argument that would distinguish it. Suggest revision priorities, not unrequested experiment execution. A priority must identify the manuscript locus, the problem, the proposed repair or evidence needed, and which comparison the repair could change.

Confidence is capped by evidence level (validator-enforced): `full_paper` → up to `high`; `abstract_only` and `metadata_only` → `low`, and these appear only in waived records (§3.5) or adjacent entries. Do not write technical claims that were not observed.

## 6. Required `review.md` structure

The Markdown report follows the user's language and contains, at minimum:

1. review basis, date, manuscript identity, reading policy and dispatch method, source/evidence boundary, and no-rerun statement;
2. a comparison snapshot explicitly stating the target rank or interval conditional on the selected set, up to three material weaknesses and two strengths;
3. scope and candidate-count resolution, including the default count (8 records including the target), same-domain gate, officially accepted-publication gate, venue policy, and which candidates could not be read in full and why;
4. a full-text verification table with one row for every listed ranked or adjacent paper: the full-text URL opened and how it was obtained, the coverage note, anchor count, abstract status, publication URL, and CCF/domain-venue status source URL;
5. a comparison table for the core set — same-domain fit, accepted publication/venue evidence, independent quality score, rank or group, relation, decisive factor, confidence, and any score-order override;
6. one paragraph per ranked paper stating its contribution, its relation to the target and the strongest counterargument, the target comparison when useful, the reader's verification basis — including **at least one verbatim anchor with its locator** — and direct source links;
7. the target's claim → evidence → alternative → confidence analysis;
8. each paper's frozen independent review, score justification, next-level requirement, plus target revision priorities;
9. adjacent, excluded, unread-in-full, or abstract-unverified candidates and why they are not in the verified core;
10. a reading-dispatch log naming each paper, the reader agent, the URL it opened, its coverage note, and every `could_not_verify` item the reader returned.

Every target claim must include a section or page anchor. Every reference-paper claim must cite the full-text URL and the anchor locator it came from; a claim that rests only on an abstract belongs in the report's uncertainty section, not in a relation. Do not use a bibliography citation without a clickable source URL in the review.

Also write `sources.md` beside the report. It is the audit trail for the scope freeze, search routes and queries, each candidate's same-domain fit and inclusion/exclusion reason, CCF/domain-venue provenance, official accepted-publication records, full-text URLs with `obtained_via` and coverage notes, abstract URLs/statuses, the dispatch log, any waiver and the user's grant, version corrections, and evidence levels. Keep it factual and concise; do not duplicate the full review prose.

## 7. `ranking.json` schema

Write valid UTF-8 JSON with this shape. The field names and enum values are part of the output contract; additional fields are allowed only when they preserve these fields.

```json
{
  "schema_version": "3.1",
  "run": {
    "manuscript_path": "/absolute/path/to/manuscript.tex",
    "manuscript_sha256": "64-char hex digest of the reviewed revision",
    "run_date": "YYYY-MM-DD",
    "ranked_count": 8,
    "rank_includes_target": true,
    "target_venue": "...",
    "publication_cutoff": "YYYY-MM-DD or null",
    "reading_policy": {
      "full_text_required": true,
      "dispatch_method": "subagent_parallel|self",
      "waiver": null
    },
    "reading_dispatch": {
      "method": "subagent_parallel|self",
      "reader_count": 8,
      "dispatched_on": "YYYY-MM-DD"
    },
    "rank_interval": null,
    "rubric_version": "4.2-r1",
    "peer_set": {
      "mode": "fresh_search|carried_forward",
      "previous_run": "../<previous-run-dir> or null",
      "added": ["key"],
      "removed": ["key"]
    },
    "ccf_scope": {
      "edition": "...",
      "category": "...",
      "comparator_venue_policy": "any_ccf_a|ccf_ab|domain_peer",
      "source_url": "https://official-ccf-source.example/...",
      "verified_on": "YYYY-MM-DD"
    }
  },
  "papers": [
    {
      "key": "target-or-stable-reference-key",
      "kind": "target|ccf_a_reference|ccf_b_reference|domain_reference",
      "role": "target|sota_ceiling|median_accepted|marginal_pass|direct|method|foundational",
      "domain_fit": "<evidence-based same-domain match for a peer; null for the target>",
      "title": "...",
      "authors": ["..."],
      "venue": "...",
      "year": 2024,
      "rank": 1,
      "relation_to_target": "self|above|below|unresolved",
      "decisive_factor": "The single thing that decides this head-to-head comparison, as verified in the full text.",
      "ccf_status": "A|B|domain_top|not_applicable",
      "publication_status": "published|accepted_pre_proceedings|not_applicable",
      "abstract_status": "verified|abstract-unverified|not_applicable",
      "evidence_level": "full_paper|abstract_only|metadata_only",
      "confidence": "high|medium|low",
      "reading": {
        "mode": "full_text|full_text_partial|full_text_unavailable",
        "full_text_url": "https://the-url-actually-opened.example/...",
        "obtained_via": "local_file|publisher_html|publisher_pdf|proceedings_pdf|aclanthology_pdf|arxiv_pdf|openreview_pdf|none",
        "read_by": "subagent|self",
        "coverage_note": "What parts were actually read.",
        "anchors": [
          {"locator": "Section 4.2 / Table 2", "quote": "<=30 words verbatim", "supports": "identification"}
        ],
        "could_not_verify": ["..."]
      },
      "independent_review": {
        "reviewer_id": "reader-paper-id",
        "summary": "Claim and demonstrated contribution",
        "strengths": ["Strength with source anchor"],
        "weaknesses": ["Material limitation with source anchor"],
        "score": 7,
        "novelty_band": "optional integer 1..5 (Schema 3.2)",
        "practical_impact_band": "optional integer 1..5 (Schema 3.2)",
        "score_rationale": "Why the observed evidence earns this level",
        "next_level_requirement": "What prevents the next level; for 10 explain why above 9",
        "reused_from": "optional, peers only: {run, reviewed_on, rubric_version}"
      },
      "score_override_reason": "Only required when the relation reverses the independent score order",
      "same_band_reason": "Only required for a directional relation when the peer's score equals the target's",
      "justification": "Comparison with anchors from both sides and the strongest counterargument.",
      "source_url": "https://canonical-primary-source.example/...",
      "publication_url": "https://official-publication.example/...",
      "abstract_url": "https://direct-abstract.example/...",
      "ccf_source_url": "https://official-ccf-source.example/... (A/B only)",
      "domain_status_source_url": "https://official-field-venue-list.example/... (domain_top only)"
    }
  ],
  "our_paper_rank": 1,
  "top_weaknesses": ["...", "...", "..."],
  "top_strengths": ["...", "..."],
  "revision_priorities": [
    {
      "priority": 1,
      "locus": "Section or page",
      "problem": "Evidence-bound problem",
      "direction": "Revision or argument direction",
      "comparison_relevance": "Which comparison this could change"
    }
  ],
  "adjacent_papers": [
    {
      "key": "...",
      "title": "...",
      "reason_excluded": "Outside the comparator venue policy, unpublished, unverified, not readable in full, or materially less close",
      "source_url": "https://..."
    }
  ]
}
```

The old five-axis `scores` table remains retired. The only numerical quality assessment is the independently returned `independent_review.score` under §4.1; do not invent additional scales or weighted totals.

For the target record use `not_applicable` statuses and null publication, abstract, and CCF URLs. Its `reading` object is required: use the exact manuscript path as `full_text_url`, `obtained_via: "local_file"` for a local manuscript, and the actual `read_by` value. Its evidence level is `full_paper`; confidence reflects verification quality, not target status. The manuscript hash must identify the reviewed content; for multi-file LaTeX, record the compiled PDF hash or an additional source-bundle hash, not just an unchanged entrypoint.

Every core record requires a non-empty source URL, justification, and evidence level with compatible confidence. Every full-text record, including the target, requires the opened path/URL, coverage note, and at least three anchors with non-empty locators and quotes. Each non-target record needs publication and CCF provenance, abstract status and URL, and a decisive factor. Partial or unavailable reading requires a user-granted waiver naming that peer, a reason, `abstract_only` or `metadata_only` evidence, `low` confidence, and an `unresolved` relation. Rank fields and intervals follow §4.

## 8. Final audit

The contract checks are mechanical and are run, not read:

```
python3 scripts/validate_ranking.py <output-dir>/ranking.json --report <output-dir>/validation.json
```

Exit `0` = PASS, `1` = contract violation, `2` = unreadable or unparseable JSON. A non-zero exit
means the run is not handed off as a finished review; fix the artifact and re-run, or report the
run as incomplete. Do not paraphrase a failing check into a caveat — the checks exist precisely
because the producing agent is the one being graded, and its own prose audit is not independent
evidence that its output is sound.

The validator enforces the schema, target count, relation/rank consistency, unresolved intervals, independent review completeness, shared-rubric score range, explained score-order reversals and same-band directions, peer-set record, review-reuse provenance (target never reused, rubric must match), official publication provenance and a non-empty domain-fit rationale for every peer, the retirement of acceptance assessments and old score tables, manuscript hash presence, source provenance, confidence caps, and the reading/waiver contract. PASS verifies these structural conditions only; it cannot judge whether a quoted source is real or a scientific comparison is fair.

Whatever the validator cannot see still needs a human pass:

- count the ranked-paper headings and source-table rows in `review.md` against `ranked_count`;
- verify every ranked peer is an officially accepted/published paper in the same research domain, that its `domain_fit` basis is supported by the cited sources, and that cross-domain candidates are adjacent rather than ranked;
- confirm target claims have section/page anchors and reference claims carry a full-text URL plus
  an anchor locator;
- spot-check that each ranked paper's quoted anchor exists in the linked full text at the stated
  locator — the validator can check that a quote is present and well-formed, not that it is real;
- for a carried-forward run, include the `diff_runs.py` output and state which rank change comes from the manuscript and which from the peer set;
- confirm the dispatch log names a reader per core paper (fresh or reused, with its source run), and that unavailable reading yields `unresolved`, not a directional relation;
- spot-check that saved independent scores are copied unchanged and each score names evidence for its level and the next-level boundary;
- confirm each directional relation uses evidence from both sides; task distance, a novel name, venue prestige, or a promise of future evidence does not decide it;
- compare the manuscript hash and protected-path status with the pre-run snapshot;
- report adjacent candidates, source conflicts, waiver scope, and evidence-level limitations
  instead of hiding them.
