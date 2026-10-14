import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from generate_related_work_brief import (
    build_related_work_brief,
    clean_bibtex_key,
    classify_paper,
    make_bibtex_entry,
)


def _make_sample_ranking():
    return {
        "schema_version": "3.2",
        "papers": [
            {
                "key": "target",
                "role": "target",
                "relation_to_target": "self",
                "title": "My Target Paper: Adaptive Search",
                "authors": ["Alice Smith", "Bob Jones"],
                "venue": "WWW 2027",
                "year": 2027,
            },
            {
                "key": "lats",
                "role": "sota_ceiling",
                "relation_to_target": "above",
                "title": "Language Agent Tree Search Unifies Reasoning",
                "authors": ["Andy Zhou", "Kai Yan"],
                "venue": "ICML 2024",
                "year": 2024,
                "domain_fit": "Tree search for agent planning",
                "decisive_factor": "LATS explores with MCTS whereas our target uses late branching.",
                "publication_url": "https://proceedings.mlr.press/v235/zhou24r.html",
                "independent_review": {
                    "score": 4,
                    "strengths": ["Strong tree search", "Good benchmarks"],
                    "weaknesses": ["Unshared rollouts"],
                },
            },
            {
                "key": "snell_ttc",
                "role": "sota_ceiling",
                "relation_to_target": "above",
                "title": "Scaling LLM Test-Time Compute Optimally",
                "authors": ["Charlie Snell", "Jaehoon Lee"],
                "venue": "ICLR 2025",
                "year": 2025,
                "domain_fit": "Test-time compute scaling laws",
                "decisive_factor": "Snell models compute allocation, while our work optimizes KV cache sharing.",
                "publication_url": "https://proceedings.iclr.cc/paper/2025/123",
                "independent_review": {
                    "score": 4,
                    "strengths": ["Clean allocation models"],
                    "weaknesses": ["Single benchmark"],
                },
            },
        ],
        "adjacent_papers": [
            {
                "key": "vllm",
                "title": "PagedAttention",
                "reason": "Different systems level estimand",
            }
        ],
    }


def test_clean_bibtex_key():
    assert clean_bibtex_key("Andy Zhou", 2024, "Language Agent Tree Search", "lats") == "lats"
    assert clean_bibtex_key("Andy Zhou", 2024, "Language Agent Tree Search", "") == "zhou2024language"


def test_make_bibtex_entry():
    paper = {
        "title": "Language Agent Tree Search",
        "authors": ["Andy Zhou", "Kai Yan"],
        "venue": "ICML 2024",
        "year": 2024,
        "publication_url": "https://example.com/paper.pdf",
    }
    entry = make_bibtex_entry(paper, "zhou2024lats")
    assert "@inproceedings{zhou2024lats," in entry
    assert "author    = {Andy Zhou and Kai Yan}" in entry
    assert "booktitle = {ICML 2024}" in entry


def test_classify_paper():
    p_tree = {"title": "MCTS Language Agent Tree Search", "domain_fit": "tree search"}
    assert classify_paper(p_tree) == "tree_search"

    p_ttc = {"title": "Scaling LLM Test-Time Compute Optimally", "domain_fit": "test-time compute"}
    assert classify_paper(p_ttc) == "test_time_compute"

    p_bench = {"title": "BrowseComp-Plus: A Fair Evaluation Benchmark", "domain_fit": "benchmark"}
    assert classify_paper(p_bench) == "evaluation_benchmarks"


def test_build_related_work_brief():
    data = _make_sample_ranking()
    brief_md = build_related_work_brief(data)

    assert "# Related Work Synthesis & Literature Briefing" in brief_md
    assert "My Target Paper: Adaptive Search" in brief_md
    assert "## 1. Thematic Landscape and Peer Taxonomy" in brief_md
    assert "## 2. Comparative Differentiation Matrix (Peer-by-Peer Positioning)" in brief_md
    assert "Language Agent Tree Search Unifies Reasoning" in brief_md
    assert "Scaling LLM Test-Time Compute Optimally" in brief_md
    assert "## 3. Plug-and-Play LaTeX Drafting Snippets" in brief_md
    assert "\\subsection{Tree Search and Planning in Language Models}" in brief_md
    assert "\\subsection{Test-Time Compute and Inference Scaling}" in brief_md
    assert "## 4. BibTeX Ready-Block" in brief_md
    assert "@inproceedings{" in brief_md
    assert "## 5. Adjacent Context and Borderline Exclusions" in brief_md
    assert "PagedAttention" in brief_md


def test_cli_execution(tmp_path):
    data = _make_sample_ranking()
    ranking_file = tmp_path / "ranking.json"
    ranking_file.write_text(json.dumps(data), encoding="utf-8")

    out_file = tmp_path / "related_work_brief.md"
    latex_file = tmp_path / "related_work.tex"
    bib_file = tmp_path / "related_work.bib"

    script_path = Path(__file__).resolve().parent.parent / "scripts" / "generate_related_work_brief.py"

    cmd = [
        sys.executable,
        str(script_path),
        "--ranking",
        str(ranking_file),
        "--output",
        str(out_file),
        "--latex-out",
        str(latex_file),
        "--bib-out",
        str(bib_file),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert res.returncode == 0
    assert out_file.exists()
    assert latex_file.exists()
    assert bib_file.exists()

    content = out_file.read_text(encoding="utf-8")
    assert "Related Work Synthesis" in content

    latex_content = latex_file.read_text(encoding="utf-8")
    assert "\\subsection{" in latex_content

    bib_content = bib_file.read_text(encoding="utf-8")
    assert "@inproceedings{" in bib_content
