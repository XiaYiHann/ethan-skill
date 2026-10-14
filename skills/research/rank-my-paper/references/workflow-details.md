# Rank My Paper：机制细节、工作流与边界（细则）

本文件是 `SKILL.md` 的细则层：Pocock 对齐、两轮 Bidding 协议细节、5-Step 工作流原表与边界/评测原文。
SKILL.md 只保留触发面、流程骨架、输出契约与指针；规则以本文件为准。

## Pocock 生态原语对齐

- **文献一手检索** ➔ `/research`；**领域建模与术语** ➔ `/domain-modeling`；
- **手稿发表态精修** ➔ `/acceptance-polish`；**快照封存** ➔ `/paper-shelf`；
- **Unique Delta**：学术会议级 AC-Reviewer 盲排评审体系。两轮确定性 Bidding 分配（[`bidding_assigner.py`](../scripts/bidding_assigner.py)），10 个 Reviewer 并发无串通评审，严格由 [`validate_ranking.py`](../scripts/validate_ranking.py) 执行成对关系与断言一致性校验。

## 核心机制：AC-Reviewer 两轮 Bidding 协议

1. **Round 1 (粗筛竞价 / Coarse Bidding)**：
   - AC 基于目标手稿课题构建 30~50 篇同领域已录用候选池；
   - **时效性硬门禁（Recency Gate）**：严格限定近 3 年内发表（$\text{year} \ge \text{target\_year} - 3$），彻底排除年代久远的经典工作或陈旧基线，历史工作仅作为引用背景；
   - 10 个 Reviewer Agents 针对 Abstract/Keywords 评估意向并计算 Affinity 得分；
   - 淘汰边缘文献，快速收敛至 **20~25 篇短名单**。
2. **Round 2 (二分图最大权匹配 / Assignment Solver)**：
   - 运行 [`scripts/bidding_assigner.py`](../scripts/bidding_assigner.py)；
   - 满足三大刚性约束：**锁定目标文献数（默认 8；显式传 15 时走全量 AC Bidding 规模）**、**每篇文章 2 人交叉复核**、**每个 Reviewer 上限 3 篇**；
   - 求解最优分配矩阵，达成零过载的完全负载均衡。详见 [ac-bidding-protocol.md](ac-bidding-protocol.md)。
- **默认策略与规模**：Default 8 ranked records including the target（单组快速模式）或 15 篇已录用核心文献（全量 AC Bidding 模式）；Default to `domain_peer`（限定 CCF-A/B 或同领域旗舰级同行评议已发表论文）；**时效性硬门禁**：仅纳选近 3 年顶级已录用文献。

## 工作流 (5-Step Benchmarking Pipeline)

1. **分析目标手稿**：提取根问题、任务、机制、设定与边界，锁定 `manuscript_path` 与 hash；
2. **两轮 Bidding 与分配**：
   ```bash
   python3 skills/rank-my-paper/scripts/bidding_assigner.py \
     --candidates-file candidates.json \
     --reviewers-file reviewers.json \
     --bids-file bids.json \
     --target-papers 15 --coverage 2 --capacity 3 --recency-years 3
   ```
3. **并发独立评审**：派发 10 个 Reviewer Sub-Agents，按指定配额阅读全文并输出独立 Review 报告（遵循 [review-protocol.md](review-protocol.md) 与 [reader-agent-prompt.md](reader-agent-prompt.md)）；
4. **AC 汇总裁决与文献提炼**：
   - 汇总打分，计算成对相对关系（Above / Below / Unresolved），推导排位区间并撰写 Meta-Review（`review.md`）；
   - 运行 [`scripts/generate_related_work_brief.py`](../scripts/generate_related_work_brief.py) 自动提炼同领域的聚类分布、决定性差异化矩阵与可以直接嵌入正文的 LaTeX / BibTeX 引用块（生成 `related_work_brief.md`），为撰写与修订手稿的 Related Work 提供扎实的证据支撑；
5. **确定性门禁校验**：运行 `python3 skills/rank-my-paper/scripts/validate_ranking.py <manuscript>/rank_my_paper/ranking.json`，确保 0 failure（含 4 道门禁与 Recency Gate 校验）。全部核心产物（`ranking.json`、`review.md`、`related_work_brief.md`）落盘于 `<manuscript>/rank_my_paper/`。

## 边界与评测 (Boundaries & Evals)

- **Out of scope / Do not use for**：
  - 日常开题调研或单篇文章总结（转至 `/research`）；
  - 手稿正文修改或实验重跑（转至 `/acceptance-polish` 或 `/research-loop`）；
  - 绝不修改手稿目录以外的文件，所有产物严格局限于 `<manuscript>/rank_my_paper/`。
- **自动化评测与验证**：
  - 评测基准用例见 [evals/eval_cases.json](../evals/eval_cases.json) 与 [evals/history/baseline_eval.json](../evals/history/baseline_eval.json)；
  - 单元测试运行 `pytest skills/rank-my-paper/tests`。
