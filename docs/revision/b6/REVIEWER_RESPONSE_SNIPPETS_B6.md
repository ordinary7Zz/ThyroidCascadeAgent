# B6 / R2.9 回复片段（与 B6_ROUTING_STABILITY_CONCLUSIONS.md 数字一致）

> 换队列后：同步改 **n**、**92%**、**8/10**、**2/10**、**60%**、**close-only** 等表述；若出现 easy 层，增加一句分层对比。

---

## 中文（建议贴 R2.9 回复）

**路由器透明性。** 我们在补充材料中提供了完整的路由器规格（`router_spec.md`），包括 LLM 名称与版本、解码参数（temperature、max_tokens）、输入候选摘要字段及 JSON 输出模式；每次路由决策另以 `routing_log.jsonl` 结构化记录（候选质量、是否调用 LLM、最终选择与理由），并附不少于 10 条样例记录供审计。

**5× 稳定性。** 在复用固定专家模型输出的前提下，我们对 **sample** 子集 **10** 例每例重复 **5** 次 LLM 分割路由（Path B 病例另报告分类路由重复）。平均选择一致率为 **92%**（**8/10** 五次完全一致；**2/10** 为 **60%**，对应候选质量接近的 **close** 分层及重复间 Dice 波动）。主队列将按相同协议扩展并报告按 `disagreement_tier` 分层的一致率。

---

## English (draft)

**Router transparency.** We provide full router specifications in the Supplementary Information (model ID, decoding parameters, JSON schema) and append-only structured routing logs (`routing_log.jsonl`) with candidate summaries and parsed decisions, including more than ten exemplar records for audit.

**Five-fold routing repeats.** With frozen expert outputs, we repeated LLM segmentation routing five times per case on a **sample** subset (*n* = **10**). Mean selection agreement was **92%** (eight cases with identical choices across all five repeats; two cases at **60%** under the **close** disagreement stratum, with corresponding Dice variability). We will report the same protocol on the primary cohorts with tier-stratified agreement.
