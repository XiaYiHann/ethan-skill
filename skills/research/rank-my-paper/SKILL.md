---
name: rank-my-paper
description: >-
  基于学术会议 Area Chair (AC) 与 10 个 Reviewer Sub-Agents 的两轮 Bidding 分配机制，从近 3 年候选文献池中严格筛选并分配 8 篇核心同领域已录用对比论文（默认 8 条记录，含目标手稿；如需全量规模须显式传 --target-papers 15），并发独立全文精读评审，由 AC 汇总成对关系生成证据绑定的排位基准 (ranking.json) 并提炼 Related Work 对标矩阵 (related_work_brief.md)。仅用于已完成手稿的同行盲排对标与相关工作对标支持；不用于日常文献综述或论文修改。
metadata:
  category: research-benchmarking
  tags: [paper, ranking, benchmarking, bidding, peer-review, related-work]
  version: "3.4.0"
  last_updated: "2026-10-13"
allowed-tools: Read, Glob, Grep, Bash, Edit, Write
---

# Rank My Paper：基于 AC 两轮 Bidding 的同行盲排基准

主 Agent 扮演 **Area Chair (AC)**，调度 **10 个 Reviewer Sub-Agents**：两轮 Bidding（粗筛竞价 ➔ 二分图匹配）选拔近 3 年核心对比论文并负载均衡（3 篇/人、2 人/篇），并发精读并汇总成对关系。详见 [workflow details](references/workflow-details.md)。

**委派**：一手检索 ➔ `/research`；术语 ➔ `/domain-modeling`；发表态精修 ➔ `/acceptance-polish`；快照存盘 ➔ `/paper-shelf`。

## 工作流骨架 (5-Step)

1. **分析目标手稿**：提取根问题/机制/边界，锁定路径与 hash；差量预算用 `scripts/diff_runs.py`。
2. **两轮 Bidding 分配**：运行 `scripts/bidding_assigner.py` 匹配（默认 8 篇，全量 15 篇加 `--target-papers 15`；近 3 年门禁）。
3. **并发独立评审**：Reviewer Sub-Agents 精读全文，执行内部自洽性验算（表格重算与宣称对照）与硬闸检查（匿名/合规），输出独立报告。
4. **AC 汇总裁决与文献提炼**：执行硬闸熔断（`hard_gate_vetoed`）；汇总成对关系与排位并写 `review.md`；调用 `scripts/generate_related_work_brief.py` 提炼同行聚类、差异矩阵与 LaTeX/BibTeX。
5. **确定性门禁**：运行 `scripts/validate_ranking.py <manuscript>/rank_my_paper/ranking.json` 须 0 failure（含硬闸熔断与自洽性）。

默认策略：Default 8 ranked records including the target；Default to `domain_peer`（CCF-A/B 或同领域旗舰）；近 3 年已录用同行工作。

**输出契约**：`<manuscript>/rank_my_paper/` 下 `ranking.json`、`review.md` 与 `related_work_brief.md`；门禁见 Step 5。

## 边界与评测

- **Do not use for**：日常开题调研 ➔ `/research`；正文修改或实验重跑 ➔ `/acceptance-polish`、`/research-loop`；绝不改动手稿目录外文件。
- **评测**：用例 `evals/eval_cases.json`、基线 `evals/history/baseline_eval.json`；`pytest tests`。

**Reference Map**：`references/`（workflow-details、ac-bidding-protocol、review-protocol、reader-agent-prompt）、`scripts/`（bidding_assigner、validate_ranking、diff_runs、generate_related_work_brief）、`tests/`。

