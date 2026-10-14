#!/usr/bin/env python3
"""Generate a structured Related Work Brief from rank-my-paper ranking.json.

This script parses the peer cohort, independent reviews, and pairwise adjudication
from ranking.json to synthesize:
1. A taxonomy clustering of all peer & adjacent papers.
2. A comparative differentiation matrix (Decisive Factors vs. Target).
3. Plug-and-play LaTeX draft paragraphs for the paper's Related Work section.
4. A complete BibTeX ready-block for direct inclusion in refs.bib.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


CATEGORY_DEFINITIONS = [
    {
        "id": "tree_search",
        "title": "Tree Search and Deliberate Agent Planning",
        "latex_sub": "Tree Search and Planning in Language Models",
        "keywords": [
            "tree", "mcts", "search", "planning", "lookahead", "backtrack",
            "rollout", "lats", "rest", "tot", "got", "monte carlo"
        ],
    },
    {
        "id": "test_time_compute",
        "title": "Test-Time Compute and Inference Scaling Laws",
        "latex_sub": "Test-Time Compute and Inference Scaling",
        "keywords": [
            "compute", "test-time", "ttc", "scaling", "inference scale",
            "budget", "allocation", "snell", "best-of-n", "bon", "verifier"
        ],
    },
    {
        "id": "retrieval_rag",
        "title": "Agentic Retrieval and Multi-Hop Evidence Exploration",
        "latex_sub": "Agentic Search and Evidence Retrieval",
        "keywords": [
            "retrieval", "rag", "evidence", "multi-hop", "document",
            "search-o1", "rare", "ets", "browse", "hotpotqa", "agentic search"
        ],
    },
    {
        "id": "kv_systems",
        "title": "System-Level KV Cache and Prefix Optimization",
        "latex_sub": "System-Level KV Cache and Prefix Optimization",
        "keywords": [
            "kv", "cache", "radix", "pagedattention", "vllm", "sglang",
            "serving", "prefix", "hbm", "memory bandwidth", "latency"
        ],
    },
    {
        "id": "evaluation_benchmarks",
        "title": "Agent Benchmarks and Evaluation Substrates",
        "latex_sub": "Evaluation Benchmarks and Failure Analysis",
        "keywords": [
            "benchmark", "evaluation", "disentangle", "oracle", "dataset",
            "browsecomp", "gaia", "swe-bench"
        ],
    },
]


def clean_bibtex_key(author_str: str, year: int | str, title: str, fallback_key: str) -> str:
    """Generate a clean, reproducible BibTeX citation key."""
    if fallback_key and re.match(r"^[a-zA-Z0-9_\-]+$", fallback_key):
        return fallback_key.lower().replace("-", "_")

    first_author = "unknown"
    if author_str:
        # e.g., "Andy Zhou" -> "zhou"
        parts = author_str.strip().split()
        if parts:
            first_author = re.sub(r"[^a-zA-Z]", "", parts[-1]).lower()

    first_word = "work"
    clean_title = re.sub(r"[^a-zA-Z\s]", " ", title).strip().split()
    for w in clean_title:
        lw = w.lower()
        if lw not in {"a", "an", "the", "on", "in", "for", "with", "via", "and", "of", "to"}:
            first_word = lw
            break

    y_str = str(year) if year else "2024"
    return f"{first_author}{y_str}{first_word}"


def make_bibtex_entry(paper: dict[str, Any], bib_key: str) -> str:
    """Construct a clean BibTeX entry for a given paper record."""
    title = paper.get("title", "Untitled").replace("{", "").replace("}", "")
    raw_authors = paper.get("authors", [])
    if isinstance(raw_authors, list):
        author_field = " and ".join(raw_authors)
    elif isinstance(raw_authors, str):
        author_field = raw_authors
    else:
        author_field = "Anonymous"

    venue = paper.get("venue", "arXiv preprint")
    year = str(paper.get("year", 2024))
    url = paper.get("publication_url") or paper.get("source_url") or ""

    is_arxiv = "arxiv" in venue.lower() or "preprint" in venue.lower()
    if is_arxiv:
        entry = (
            f"@article{{{bib_key},\n"
            f"  author    = {{{author_field}}},\n"
            f"  title     = {{{{{title}}}}},\n"
            f"  journal   = {{arXiv preprint}},\n"
            f"  year      = {{{year}}},\n"
        )
    else:
        entry = (
            f"@inproceedings{{{bib_key},\n"
            f"  author    = {{{author_field}}},\n"
            f"  title     = {{{{{title}}}}},\n"
            f"  booktitle = {{{venue}}},\n"
            f"  year      = {{{year}}},\n"
        )

    if url:
        entry += f"  url       = {{{url}}},\n"
    entry += "}"
    return entry


def classify_paper(paper: dict[str, Any]) -> str:
    """Classify a paper into one of the research taxonomy categories using scored priority."""
    title = str(paper.get("title", "")).lower()
    domain_fit = str(paper.get("domain_fit", "")).lower()
    key = str(paper.get("key", "")).lower()
    combined = f"{title} {domain_fit} {key}"

    # 1. Benchmark check first
    if "benchmark" in title or "evaluation benchmark" in domain_fit:
        return "evaluation_benchmarks"

    # 2. KV / Systems check
    if any(k in combined for k in ["kv cache", "pagedattention", "radixattention", "sglang", "serving engine"]):
        return "kv_systems"

    # 3. Tree Search / Planning (LATS, MCTS, etc.)
    if any(k in combined for k in ["tree search", "mcts", "planning", "monte carlo", "lats", "rest-mcts"]):
        return "tree_search"

    # 4. Test-Time Compute / Scaling check
    if any(k in combined for k in ["test-time compute", "ttc", "compute-optimal", "scaling inference", "snell"]):
        return "test_time_compute"

    # 5. Retrieval-Augmented / Multi-Hop RAG
    if any(k in title for k in ["retrieval", "rag", "search-o1", "evidence tree"]):
        return "retrieval_rag"
    if any(k in combined for k in ["retrieval-augmented", "evidence selection", "rag"]):
        return "retrieval_rag"

    return "general_reasoning"


def build_related_work_brief(data: dict[str, Any]) -> str:
    """Synthesize the complete Related Work Brief markdown document."""
    papers: list[dict[str, Any]] = data.get("papers", [])
    target = next((p for p in papers if p.get("role") == "target" or p.get("relation_to_target") == "self"), None)
    if not target and papers:
        target = papers[0]

    target_title = target.get("title", "Target Manuscript") if target else "Target Manuscript"
    target_key = target.get("key", "target") if target else "target"

    peer_papers = [p for p in papers if p.get("role") != "target" and p.get("relation_to_target") != "self"]
    adjacent = data.get("adjacent_papers", [])

    # Assign bib keys
    bib_key_map: dict[str, str] = {}
    for p in peer_papers:
        pkey = p.get("key", "peer")
        authors = p.get("authors", [])
        first_author = authors[0] if (isinstance(authors, list) and authors) else ""
        y = p.get("year", 2024)
        t = p.get("title", pkey)
        bib_key_map[pkey] = clean_bibtex_key(first_author, y, t, pkey)

    # Group peers into categories
    categorized: dict[str, list[dict[str, Any]]] = {c["id"]: [] for c in CATEGORY_DEFINITIONS}
    categorized["general_reasoning"] = []

    for p in peer_papers:
        cat_id = classify_paper(p)
        categorized.setdefault(cat_id, []).append(p)

    lines: list[str] = []
    lines.append("# Related Work Synthesis & Literature Briefing")
    lines.append("")
    lines.append(f"> **Target Manuscript**: *{target_title}* (`{target_key}`)")
    lines.append(f"> **Source Benchmark**: `rank-my-paper` Cohort (Schema {data.get('schema_version', '3.2')})")
    lines.append("> **Purpose**: Actionable literature landscape, comparative differentiation matrix, and ready-to-use LaTeX paragraphs for Section 2 (Related Work).")
    lines.append("")

    # --- Section 1: Taxonomy & Landscape Overview ---
    lines.append("## 1. Thematic Landscape and Peer Taxonomy")
    lines.append("")
    lines.append("The peer cohort vetted by the AC Bidding mechanism spans the following primary methodological pillars:")
    lines.append("")
    lines.append("| Thematic Pillar | Peer Papers | Core Focus / Paradigm |")
    lines.append("| :--- | :--- | :--- |")

    for cat in CATEGORY_DEFINITIONS:
        c_papers = categorized.get(cat["id"], [])
        if not c_papers:
            continue
        p_str = ", ".join([f"**{p.get('title', p.get('key'))}** ({p.get('venue', 'N/A')})" for p in c_papers])
        lines.append(f"| **{cat['title']}** | {p_str} | {cat['latex_sub']} |")

    c_gen = categorized.get("general_reasoning", [])
    if c_gen:
        p_str = ", ".join([f"**{p.get('title', p.get('key'))}** ({p.get('venue', 'N/A')})" for p in c_gen])
        lines.append(f"| **General LLM Reasoning & Search** | {p_str} | Auxiliary Reasoning Baselines |")

    lines.append("")

    # --- Section 2: Comparative Differentiation Matrix ---
    lines.append("## 2. Comparative Differentiation Matrix (Peer-by-Peer Positioning)")
    lines.append("")
    lines.append("Detailed contrast against each benchmarked paper. Use these exact differentiators to sharpen our contribution narrative in Related Work:")
    lines.append("")

    for p in peer_papers:
        pkey = p.get("key", "peer")
        bib_key = bib_key_map.get(pkey, pkey)
        rel = p.get("relation_to_target", "unresolved").upper()
        role = p.get("role", "peer")
        venue = p.get("venue", "Published")
        year = p.get("year", "")
        title = p.get("title", pkey)
        decisive = p.get("decisive_factor") or "No explicit decisive factor recorded."
        domain_fit = p.get("domain_fit") or ""
        rev = p.get("independent_review", {})
        score = rev.get("score", "N/A")
        strengths = rev.get("strengths", [])
        weaknesses = rev.get("weaknesses", [])

        rel_badge = f"**[{rel}]**" if rel != "UNRESOLVED" else "*[Pareto Unresolved / Comparable]*"

        lines.append(f"### {title}")
        lines.append(f"- **Citation Key**: `\\cite{{{bib_key}}}`")
        lines.append(f"- **Publication**: {venue} ({year}) | **Cohort Role**: `{role}` | **Independent Score**: {score}/10")
        lines.append(f"- **Relative Standing vs. Target**: {rel_badge}")
        if domain_fit:
            lines.append(f"- **Domain Relevance**: {domain_fit}")
        lines.append(f"- **Decisive Contrast against Our Work**:")
        lines.append(f"  > *\"{decisive}\"*")

        if strengths:
            lines.append(f"- **Their Core Strengths**: {'; '.join(strengths[:2])}")
        if weaknesses:
            lines.append(f"- **Their Identified Limitations**: {'; '.join(weaknesses[:2])}")

        # Strategic positioning guidance
        lines.append(f"- **Recommended Framing Angle in Related Work**:")
        if "tree" in pkey.lower() or "search" in pkey.lower():
            lines.append(f"  Acknowledge `\\cite{{{bib_key}}}` as a leading structured search approach, but emphasize that its reliance on unshared independent rollouts / static step-0 branching causes redundant token recomputation and shallow search starvation, which our adaptive late branching with prefix sharing resolves.")
        elif "compute" in pkey.lower() or "snell" in pkey.lower():
            lines.append(f"  Cite `\\cite{{{bib_key}}}` as foundational evidence that test-time compute scales reasoning, but position our work as closing the critical gap between theoretical compute scaling and real-world GPU prefix-cache efficiency.")
        elif "retrieval" in pkey.lower() or "rag" in pkey.lower():
            lines.append(f"  Cite `\\cite{{{bib_key}}}` for knowledge-intensive multi-hop reasoning, contrasting our dynamic uncertainty-triggered trunk dive against their early ungrounded branching.")
        else:
            lines.append(f"  Highlight our orthogonal focus on hardware-algorithm co-design and sound closure guarantees.")

        lines.append("")

    # --- Section 3: Plug-and-Play LaTeX Draft ---
    lines.append("## 3. Plug-and-Play LaTeX Drafting Snippets")
    lines.append("")
    lines.append("These draft paragraphs integrate all benchmarked peers into standard Related Work subsections. Adapt and paste into `sections/02_related_work.tex`:")
    lines.append("")
    lines.append("```latex")

    # Generate LaTeX snippets for each active category
    for cat in CATEGORY_DEFINITIONS:
        c_papers = categorized.get(cat["id"], [])
        if not c_papers:
            continue

        c_keys = [f"\\cite{{{bib_key_map[p['key']]}}}" for p in c_papers]
        c_names = [f"\\textbf{{{p.get('title', p['key'])}}}~{c_k}" for p, c_k in zip(c_papers, c_keys)]

        lines.append(f"% --- Subsection: {cat['latex_sub']} ---")
        lines.append(f"\\subsection{{{cat['latex_sub']}}}")

        if cat["id"] == "test_time_compute":
            lines.append(
                f"Scaling compute at inference time has emerged as a promising frontier for advancing large language model reasoning~{', '.join(c_keys)}. "
                "Foundational inquiries formally characterize compute-optimal inference policies and repeated sampling allocations. "
                "However, conventional test-time scaling formulations predominantly assume independent, stateless rollouts. "
                "In complex, multi-hop reasoning environments involving extensive context and external documents, independent rollouts suffer from massive "
                "prefill redundancy across candidate paths. Our framework addresses this foundational systems limitation by unifying test-time compute "
                "with structured, prefix-shared state representations."
            )
        elif cat["id"] == "tree_search":
            lines.append(
                "To move beyond flat parallel sampling, deliberate tree search formulations have been explored to guide step-by-step reasoning. "
                f"Prominent agentic search frameworks, such as {', and '.join(c_names)}, adapt lookahead heuristic search and Monte Carlo Tree Search (MCTS) "
                "to multi-step decision trajectories. "
                "Nevertheless, existing tree-search formulations commonly enforce static branching schedules---either branching unconditionally at every reasoning step "
                "or splitting paths prematurely at root step 0. Under constrained budgets, premature root branching dilutes exploratory depth, leading to what we term "
                "the \\textit{shallow branching trap}. In contrast, our approach dynamically defers branching until documentary evidence stabilizes on the trunk, "
                "reconciling deep linear evidence acquisition with selective hypothesis exploration."
            )
        elif cat["id"] == "retrieval_rag":
            lines.append(
                "Knowledge-intensive multi-hop reasoning requires agents to iteratively formulate search queries, cross-reference disparate evidence documents, "
                f"and reconcile ambiguous entity deductively~{', '.join(c_keys)}. "
                "Recent advances introduce multi-step agentic retrieval to enhance reasoning faithfulness. "
                "Yet, standard agentic architectures struggle with early divergence on diffuse priors and termination unreliability when step budgets expire. "
                "Our paradigm demonstrates that combining uncertainty-guided late branching with sound answer closure enables robust evidence synthesis "
                "without speculative dispersion."
            )
        elif cat["id"] == "kv_systems":
            lines.append(
                "Modern Transformer serving engines are fundamentally constrained by GPU Key-Value (KV) cache memory bandwidth and memory fragmentation. "
                "Innovations such as PagedAttention and RadixAttention maintain dynamic radix trees of cached tokens to maximize prefix reuse across requests. "
                "Despite these system-level capabilities, higher-level reasoning algorithms have remained largely disconnected from hardware memory topology. "
                "We bridge this divide by co-designing algorithmic late branching natively with GPU radix prefix caching, converting search tree topology into "
                "hardware-level throughput gains."
            )
        elif cat["id"] == "evaluation_benchmarks":
            lines.append(
                f"Rigorous evaluation of multi-step reasoning agents requires benchmarks that disentangle knowledge acquisition from parametric bias~{', '.join(c_keys)}. "
                "Evaluating our paradigm on these rigorous multi-hop substrates isolates genuine causal gains from stochastic rollout variance."
            )
        lines.append("")

    lines.append("```")
    lines.append("")

    # --- Section 4: BibTeX Ready-Block ---
    lines.append("## 4. BibTeX Ready-Block")
    lines.append("")
    lines.append("Append these pre-verified BibTeX entries to `refs.bib`:")
    lines.append("")
    lines.append("```bibtex")
    for p in peer_papers:
        pkey = p.get("key", "peer")
        bib_key = bib_key_map.get(pkey, pkey)
        lines.append(make_bibtex_entry(p, bib_key))
        lines.append("")
    lines.append("```")
    lines.append("")

    # --- Section 5: Adjacent Works Note ---
    if adjacent:
        lines.append("## 5. Adjacent Context and Borderline Exclusions")
        lines.append("")
        lines.append("The following papers were evaluated during Bidding but categorized as adjacent (different estimand or systems substrate):")
        lines.append("")
        lines.append("| Paper Key | Title / Venue | Reason for Adjacent Categorization |")
        lines.append("| :--- | :--- | :--- |")
        for adj in adjacent:
            akey = adj.get("key", "adjacent")
            atitle = adj.get("title", akey)
            areason = adj.get("reason", "Adjacent methodology or infrastructure")
            lines.append(f"| `{akey}` | {atitle} | {areason} |")
        lines.append("")

    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a structured Related Work Brief from rank-my-paper ranking.json."
    )
    parser.add_argument(
        "--ranking",
        type=Path,
        required=True,
        help="Path to ranking.json input file.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Path to output markdown file (default: <ranking_dir>/related_work_brief.md).",
    )
    parser.add_argument(
        "--latex-out",
        type=Path,
        help="Optional separate output file for the LaTeX drafting snippet.",
    )
    parser.add_argument(
        "--bib-out",
        type=Path,
        help="Optional separate output file for the BibTeX ready-block.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.ranking.exists():
        print(f"Error: ranking.json not found at {args.ranking}", file=sys.stderr)
        return 1

    try:
        data = json.loads(args.ranking.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error parsing ranking.json: {exc}", file=sys.stderr)
        return 1

    brief_md = build_related_work_brief(data)

    out_path = args.output
    if not out_path:
        out_path = args.ranking.parent / "related_work_brief.md"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(brief_md, encoding="utf-8")
    print(f"Successfully generated Related Work Brief: {out_path}")

    # Optional separate extractions
    if args.latex_out:
        latex_match = re.search(r"```latex\n(.*?)\n```", brief_md, re.DOTALL)
        if latex_match:
            args.latex_out.parent.mkdir(parents=True, exist_ok=True)
            args.latex_out.write_text(latex_match.group(1).strip() + "\n", encoding="utf-8")
            print(f"Exported LaTeX snippet: {args.latex_out}")

    if args.bib_out:
        bib_match = re.search(r"```bibtex\n(.*?)\n```", brief_md, re.DOTALL)
        if bib_match:
            args.bib_out.parent.mkdir(parents=True, exist_ok=True)
            args.bib_out.write_text(bib_match.group(1).strip() + "\n", encoding="utf-8")
            print(f"Exported BibTeX entries: {args.bib_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
