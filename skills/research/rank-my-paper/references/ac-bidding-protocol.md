# AC-Reviewer 两轮 Bidding 与二分图分配协议

## 1. 架构总览：AC 与 10 个 Reviewer Sub-Agents

在对完成的手稿进行同领域同行对标（Benchmarking）时，为杜绝审稿人与论文的“领域错配（Domain Mismatch）”并防止单智能体算力瓶颈，引入学术会议级 **Area Chair (AC) - Reviewer 协作范式**：

```
[Target Manuscript] ──► AC (主 Agent) ──► 构建 Candidate Pool (30~50 篇候选论文)
                                  │
      ┌───────────────────────────┴───────────────────────────┐
      ▼                                                       ▼
【Round 1: 粗筛竞价 (Coarse Bidding)】          【Round 2: 容量受限二分图匹配】
 10 个 Reviewer Agents 针对 Abstract 打分       确定性求解最大权二分匹配 (bidding_assigner.py)
 淘汰边缘论文 ➔ 收敛至 20~25 篇短名单          锁定 15 篇核心对比文献 ➔ 严格每人 3 篇 / 每篇 2 人
      │                                                       │
      └───────────────────────────┬───────────────────────────┘
                                  ▼
【并发审稿执行 (Parallel Full-Text Reviews)】
 10 个 Reviewer 并发精读分配到的论文全文，出具独立打分与锚点证据
                                  │
                                  ▼
【AC 终审汇总与排序 (Meta-Review & Ranking)】
 AC 汇总多方审稿意见，计算成对优劣矩阵与 Bradley-Terry 相对排位，输出 ranking.json 与 review.md
```

---

## 2. 两轮 Bidding 机制详解

### Round 1: 粗筛竞价 (Coarse Bidding)
- **输入与时效硬约束**：AC 根据被评测论文的根问题（Question）、任务（Task）、机制（Mechanism）与设定（Setting），检索出 30~50 篇同领域**近 3 年已录用/已发表候选论文**（Title + Abstract + Keywords + Venue）。**严格执行近 3 年时效性门禁（$\ge \text{target\_year} - 3$）**，自动剔除年代久远的历史经典文献，确保对标的是真实的当前学术前沿；
- **执行**：10 个 Reviewer Sub-Agents 依据自身专长画像快速评估意向：
  - `very_high` (5.0)：高度契合，强烈申请评阅；
  - `high` (4.0)：领域相近，能够评阅；
  - `neutral` (3.0)：可作一般评审；
  - `low` (1.0)：领域偏离；
  - `conflict` (-100.0)：利益冲突或严重不匹配。
- **产出**：综合聚合得分，淘汰低相关度论文，产生 **Top 20~25 篇候选短名单（Shortlist）**。无需下载全文，耗时仅数秒。

### Round 2: 精准匹配与容量受限二分图分配
- **问题建模**：
  设选拔论文集 $P$，$|P| = 15$；审稿人集 $R = \{R_1, \dots, R_{10}\}$。
  - **覆盖约束（Paper Coverage）**：每篇入选论文必须由恰好 $c = 2$ 名独立 Reviewer 交叉审阅；
  - **容量约束（Reviewer Capacity）**：每个 Reviewer 承担的任务量不得超过 $q = 3$ 篇；
  - **总任务数**：$15 \times 2 = 30$ 个审稿槽位，恰好 $10 \times 3 = 30$，实现**零浪费、零过载的完美负载均衡**！
- **求解算法**：
  运行 [`scripts/bidding_assigner.py`](scripts/bidding_assigner.py)，构建以 $\text{Bid} + 2 \times \text{Affinity}$ 为权重的二分图，求解最大权匹配并回填短缺，最终输出确切的任务派发矩阵。

---

## 3. 并发执行与 AC 终审

1. **并行阅读**：
   通过宿主的 sub-agents 机制并发派发 10 个 Reviewer，每位 Reviewer 仅阅读分配到的 3 篇文章全文，严格遵循 [review-protocol.md](review-protocol.md) 的打分与锚点规则（Soundness, Novelty, Impact）；
2. **AC 裁决**：
   主 Agent（AC）汇总全部审阅意见，对目标手稿与 15 篇核心 peer papers 进行成对优劣判断（Above / Below / Unresolved），生成最终的 `ranking.json`，并通过 `validate_ranking.py` 严格校验。
