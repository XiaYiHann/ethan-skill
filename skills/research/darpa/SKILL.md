---
name: darpa
description: 以海尔迈耶之问 (Heilmeier Catechism) 八问严苛审查当前工作区与最新进展：评估真实价值、致命风险、成本开销与里程碑，给出带反证判据的中期与期末考试。触发场景：/darpa、『海尔迈耶之问』、『DARPA 八问』、要求拷问或严苛评估某个实验/方向是否值得继续、评估项目的风险成本与里程碑、判断一个工作是自嗨还是有真实价值。默认直接在对话中给出八问回复，写盘须经用户同意。不用于只解释概念、只要总结或翻译、单点代码调试、论文排名与文字润色，也不用于仅把问题清单整理成文档。
---

# DARPA (Heilmeier Catechism Review)

当用户输入 `/darpa`、要求用「海尔迈耶之问」审视，或要求严苛评估当前工作与进展时执行本流程。
本 skill 不做空洞赞美，以 DARPA 局长 George H. Heilmeier 的标准，结合工作区真实一手事实深度审查，并直接在对话中生成纯文本回复。评审结论可写入项目共享评审文件（见「共享评审文件」）——**写盘必须经用户同意**。

## 执行顺序（Matt Pocock 三段式）

1. **概念解毒**（domain-modeling）：取项目 CONTEXT / GLOSSARY，做行话过滤，保证 Q1 在无背景的读者那里可懂。
2. **一手源穿透**（research）：读工作区代码、commit、日志与 raw 评测；Q2/Q3 落到源码行号或论文根因，Q6 统计真实耗费。
3. **攻击性防御审查**（grilling）：Q4 刺破自嗨假象，Q5 列出致命脆弱点，Q8 给出带反证判据的考试。

三段式与 Matt 原语的映射理由见 [references/pocock-alignment.md](references/pocock-alignment.md)。

## 硬规则

- **禁用粉饰**：某一问回答很弱时（例如未做多卡泛化、本质只是系统工程调优而非底层理论突破）直接指出软肋与边界，不包装、不避重就轻。
- **严守一手事实**：性能数字、源码缺陷、崩溃日志必须有本仓库证据（实验日志、脚本输出、代码行）。取不到证据时显式写「未取证」并计入 Q5 风险，不用推测填空。
- **八问格式**：按 Q1 → Q8 顺序输出。每问的详细规则、禁用写法与合格标准见 [references/heilmeier-questions.md](references/heilmeier-questions.md)，回答前先读它。

## Out of scope（何时不用）

- 只解释概念、做总结、翻译，或只把问题清单整理成文档：不触发。
- 单点代码缺陷定位、性能回归调试：走诊断类流程。
- 论文横向排名、文字润色、投稿合规检查：走各自的专用流程。
- 用户明确说「先不要评审 / 只讨论」时，只讨论，不产出八问。

边界再收一句：本 skill 只在「要不要继续投、这件事值不值得做」这类判断上介入，不接管执行与写作。

## 共享评审文件（持久化）

评审不只是一次性回复。项目内可维护**同一份**八问文件：计划版（事前判据）、评审版（本 skill 写入）、Gate 0 只读引用版。项目没有那两段流程时，本 skill 只维护评审版。

- **路径**：默认 `docs/research/darpa-review.md`；项目无 `docs/research/` 时用 `<repo>/DARPA-REVIEW.md`。文件头记录路径身份、最后评审日期、证据基线（commit / run 目录）与评审次数。
- **更新协议**：先在对话给出完整 8 问；再与文件比对，列出拟改动摘要（新证据、判定变化、风险关闭/新增、考试状态）；**征得用户同意后**才写盘。用户拒绝则只交付对话回复。
- **写盘纪律**：历史判定不得改写；每次更新在 Changelog 追加一行（日期、基线、变化点）。文件只保留当前最新判定，不堆砌过程稿。

## 维护

- 触发边界评测：`evals/trigger_cases.json` + `evals/semantic_config.json`，用 yao-meta-skill 的 `trigger_eval.py` 运行；已知弱项记录在 [evals/failure-cases.md](evals/failure-cases.md)。
- 治理元数据：`manifest.json`。平台契约：`agents/interface.yaml`；Codex 另读 `agents/openai.yaml`。
