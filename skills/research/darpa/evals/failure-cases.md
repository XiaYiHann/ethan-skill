# 已知弱项（触发边界）

用 yao-meta-skill 的 `trigger_eval.py` 对本 skill 的 description 跑过一轮评测（用例见 `trigger_cases.json`，阈值沿用推荐值 0.33）：

| 版本 | precision | recall | should_trigger | should_not_trigger | near_neighbor |
| --- | --- | --- | --- | --- | --- |
| 旧 description | 0.909 | 0.833 | 10/12 | 9/10 | 8/8 |
| 现 description | 0.917 | 0.917 | 11/12 | 9/10 | 8/8 |

现存两个已知弱项，都属于评测器的短语匹配限制，保留记录而不是调阈值掩盖：

1. **无关键词的价值提问漏触发**：`评估当前算法项目的风险、成本和里程碑` 得 0.221，低于阈值。整句没有任何「海尔迈耶 / DARPA / 八问」标记，纯靠语义。结论：模型在有 skill 列表上下文时通常仍会命中，但 description 无法独立召回这类问法。
2. **「把八问写进文档，不要评审」误触发**：得 0.331，刚过阈值。`八问` 命中了 `heilmeier_review` 概念，负向词 `不要评审` 的惩罚不足以压下去。

另外，near_neighbor 8/8 说明与 grilling、research-idea、academic-debugging、rank-my-paper、code-review 之间没有路由冲突。
