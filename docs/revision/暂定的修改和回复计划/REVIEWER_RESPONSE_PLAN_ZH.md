# 审稿意见回复计划（中文）

> **审稿原文**：`docs/Nature Communications Reviews.pdf`  
> **意见索引**：`docs/ThyroidXAgent_返修计划与回复_中文.md` 第二部分（R1.x–R3.x）  
> **本表目的**：标明哪些意见**现在就能写回复**（框架+要点+多数数字），哪些只能写「将进行」或依赖他人。定稿前替换 CI/占位数字即可。  
> **回复信素材**：优先从 `docs/revision/b*/` 摘录，勿直接改返修计划原件。  
> **范围**：本表 **B1–B12 可主笔/可引用的回复**；**Shiyu S1–S10** 相关审稿条见文末「范围外」，不在本目录起草正文。  
> **语言**：仅维护本中文计划（无英文平行稿）。  
> **B11 / B12**：**无需补充实验**；以下为改稿与回信要点。  
> **进行中（2026-10-26）**：**B5**（R3.2，**接近定稿**：五 mode + **sample→TN5K 换数**）、**B7**（R1.3 NHC + R2.6）。  
> **已归档**：**B1–B4、B6、B8–B12**（含正式回信 `正式回复/latex` 中已写入条目）；本表 **专项小节** 仍作索引，**勿**重复扩写长表。快照见 [`README.md`](./README.md)。

---

## 图例

| 回复就绪 | 含义 |
|----------|------|
| **接近定稿** | 实验与结论文档已齐；回信/改稿可写完整段落；仅统稿、Supp. 编号或少量核对 |
| **是** | 实验/审计/叙事已具备；可起草完整回复段落 |
| **部分** | 主论点可回复；需保留占位或 Limitations（列出缺项） |
| **否** | 尚无定稿材料；仅可承诺或说明局限 |

---

## 审稿人 1

| 编号 | 主题 | 回复就绪 | 可回复要点（基于当前结论） | 素材路径 | 定稿前必改/待补 |
|------|------|----------|---------------------------|----------|-----------------|
| **R1.1** | 划分、去重、cluster CI、患者级 | **是**（图像侧） | ① **独立性**：**dHash** 筛查；堆叠 train↔ZJH **995** 对 H=0、TN5K test **38** 对、TN3K test↔ZJH **2** 对；② 仅 **ZJH、ThyroidXL** 可复现 patient ID；无 ID 队列 **一图一簇**；③ **患者级** AUROC/AUPRC（ZJH/ThyroidXL）；④ S3/S4 **cluster CI**（主系统 8 队列 + 基线 **58/58**，**DDTI_cls n=349**）；⑤ ZJH **敏感性**（剔除 992 train-matched 图）见 Supp. | `b1/B1_结论与回复素材.md` §三；`b2/conclusions/B2_结论与回复素材.md` | F6 **患者**重叠（可选）；近重复 **spot check** 10–20 对；1149 vs 1146 一句；**NHC** 未纳入 B2 |
| **R1.2** | 路由消融 | **接近定稿** | 固定专家池；波次 1（策略 1–5、8）**九队列** `_summary` 已齐；**cluster-bootstrap CI**（与 B2 同）；**无单一静态策略全胜**；max-conf 分割在 TN3K/TN5K 明显差于集成；Path B ~40–45%；Oracle 上界 | `../b3/`；`recompute_b3_cluster_ci.py` | **策略 6 learned、7 LLM** 表行；**NHC**；配对策略差分 CI（可选） |
| **R1.3** | NHC 异质性、校准、拒答 | **部分** | **校准/拒答（B8，可写）**：validation **n=875**、**95 分位** 定阈（无 LLM）；五 BM 外测 **ECE/Brier** + 送复核 **~44–48%**（TN3K/ZJH 等）+ Supp. 可靠性图与 risk–coverage；**保留子集 Acc** 略高于全量；如实说明 test 复核率高于 val 分位数设计（margin 分布偏移）。**NHC 异质性（B7）**：仍仅可承认中心差异、THYB_S_ZJ24 等；中心表/I² 待 G3 | `../b8/`；`output/b8/fit/`、`cohorts/`；`MANUSCRIPT` **§12** | **B7** 中心元数据；刷新 `B8_CALIBRATION_ABSTENTION_CONCLUSIONS.md`；Supp. 编号；**勿用 smoke** |
| **R1.4** | 数据流图、ZJH 用于 LNM/FTC | **是**（图假定已定） | 专家未在 ZJH 训练；恶性子集仅 LNM/FTC；回复称已补充数据流图（图像臂） | `b11_b12/DATAFLOW_*`；`b9` | 统稿 Fig 编号；ZJH/TN3K 脚注可引 B1/F6 |
| **R1 代码** | 回顾性、可部署性（**图像侧主张**） | **部分** | 弱化「广泛可部署」；强调回顾性与可审计统计（B1/B2） | B1/B2 叙事 | 全文代码发布（G4，非 B 包） |

---

## 审稿人 2

| 编号 | 主题 | 回复就绪 | 可回复要点 | 素材路径 | 定稿前必改/待补 |
|------|------|----------|------------|----------|-----------------|
| **R2.1** | 数字不一致 | **部分** | **分类宏平均** **0.9001/0.8705**（B12 已核对）；加权 0.9228/0.9533；其余项 Fig.3、LNM N、9.11s 等见 A7/B9 | `b11_b12/README.md` | 全文 sweep 旧均值；非 B12 项单独对齐 |
| **R2.2** | cluster CI、患者级 | **是** | 同 **R1.1**；bootstrap **1000/seed 42**；患者级聚合规则；ZJH 全量主结果 + Supp. excl. 敏感性 | B1+B2；`b2/tables/` | 统稿刷 S3/S4；Supp. 敏感性表编号 |
| **R2.3** | 28,458 cases | **部分** | 承认混用层级；**图像侧**分层计数（S1）；数据流 **假定已有** | B12；B1 | 28,458 全量、报告/视频计数协作 |
| **R2.4** | ZJH vs TN3K 同院 | **部分** | 同意关切；**dHash**：TN3K splits↔ZJH **1156** 对 H=0（图级，同院收录重叠）；TN3K **test**↔ZJH 仅 **2** 对 H=0；主结果 **全量 ZJH** + train-matched **敏感性** Supp.；**患者**重叠待 F6 或 Limitation | `b1/tables/near_duplicates.json`；B1 §三 | F6；勿用 stem=0 论证 |
| **R2.5** | 参考标准与标注 | **部分** | 回复信已起草（Methods §4.1 + 补充表；红色待补充合作者确认） | F5 | 标注者、病理确认表 |
| **R2.6** | NHC 描述与中心性能 | **部分** | 回复信已起草（中心表/异质性；红色待补充元数据与分析） | B7；G3 | 35 中心元数据 |
| **R2.7** | 「均值」定义 | **是** | **无权重宏平均** AUROC **0.9001**、AUPRC **0.8705**；修订稿摘要/§2.2/S4 注统一 | `b11_b12/README.md`；`MANUSCRIPT_REVISION_PLAN_ZH.md` §9 | 统稿写入 `ThyroidXAgent.md` |
| **R2.8** | 增益来源、路由价值 | **接近定稿** | **B4 L1→L2→L3** 九队列表已写入 **B4 专项**（L3=**B3 策略 7**=稿面 S3/S4）；叠 **B3 波次 1**、**B10** 公平性；ZJH L1&gt;L2 AUROC 用对账句 | `../b4/B4_STATUS_ZH.md`；`../b3/B3_LLM_RESULTS.md`；`MANUSCRIPT` **§15** | Path B 附录 B-a/b/c；Δ 配对 bootstrap CI（可选） |
| **R2.9** | 路由 prompt、稳定性 | **接近定稿**（sample）；TN3K 换数 | **透明性**：`router_spec.md` + `routing_log.jsonl`（≥10 例审计）；**5×**：*n*=**10**、均值 **92%**、8/10 全稳、2/10 为 60%（close 层） | `b6/REVIEWER_RESPONSE_SNIPPETS_B6.md`；`MANUSCRIPT_REVISION_PLAN_ZH.md` **§11** | TN3K：替换 §11 数据卡 + snippets；`export_router_spec` 若模型变更 |
| **R2.10** | FTC/PTC 标签域 | **部分**（**B9 已归档**） | FVPTC≠FTC；OOF **722 簇** AUROC **0.521**；FangDai **TBD** — 见 **B9 专项** / b9 §4.2 | `../b9/B9_ThyroidXAgent_修改与回复计划.md` | E4；F7 |
| **R2.11** | LNM 样本量、CV | **部分**（**B9 已归档**） | 5 折 OOF **882 簇** AUROC **0.718**；C2 外测 **TBD** — **B9 专项** / b9 §4.1 | 同上 | E2；全栈 OOF 换数 |
| **R2.12** | LNM 术语 CN0/CN1 | **部分**（**B9 已归档**） | 簇聚合与五折；临床定义句待协作 — b9 §4.3 | 同上；`需要确认.md` | 协作定稿 |
| **R2.14** | 基线公平性 | **接近定稿** | 监督基线 **dataset3/4 微调**（非 off-the-shelf）；新增 Supp. **S[X]**（`baseline_training_protocol.md`，13 行）；VLM **零样本** 分块；S3/S4 **cluster CI** 与 B2 一致 | `b10/B10_结论与回复素材.md` §一–§二；`b10/tables/` | 定 Supp. 编号；Methods/S3/S4 表注入稿；§6.2 核对（A7） |
| **R2.20** | 连通域、小结节 | **是**（待间距脚注） | **(a)(c)**：`selected_masks`、无 radiomics CCA、专家 ≥50 px、单图单 ROI；**(b)** 七队列 N/M 已算（`mm_per_pixel=0.1` 假设，见下表）；重点 **zjh8k N=1001/M=44** | `b11_b12/REVIEWER_SNIPPETS_ZH.md`；`tables/R2_20_SUMMARY.md`；`scripts/revision/b11/run_r2_20_small_nodules_all.sh` | 定稿：间距校准或敏感性一句；核对 JSON 内 `selected_masks_npz` 与投稿主 config |
| **R2.21** | AutoGluon/PyRadiomics | **是** | 版本、预设、特征数、无 radiomics CCA | `docs/reproducibility_radiomics.md` | 统稿时并入 Methods 4.3 / Supp. |
| **R2.22** | 语言 | — | **范围外** | G5 | — |
| **R2.23** | TI-RADS 体系 | — | **范围外** | F8 | — |
| **R2 code** | 代码许可与测试 | — | **范围外** | G4 | — |

---

## 审稿人 3

| 编号 | 主题 | 回复就绪 | 可回复要点 | 素材路径 | 定稿前必改/待补 |
|------|------|----------|------------|----------|-----------------|
| **R3.1** | 非 LLM 学习型路由 | **接近定稿** | 与 R1.2/B3 同；Methods 已定义 **策略 6（learned）** 与 **7（LLM）**；波次 1 静态基线九队列可写；回复说明 6/7 **性能待补**后与静态策略同表对照 | `../b3/`；`MANUSCRIPT` **§13** | 策略 **6/7** 跑完入表；**NHC** |
| **R3.2** | 元数据消融 | **接近定稿** | **正式回信已写** → 审稿人 3 意见 2 + **表 R17**（`metadata_ablation_tables_*.tex`；表内 **sample 占位**，红色 `\rpending` 标 **TN5K *n*=250/Δ+CI**、**NHC 热图**、修订稿 Methods/Results）。要点同 **B5 专项**；性能主表设计为 **仅 TN5K for_llm**（不与 B3 九队列对齐） | `正式回复/latex/generated/body_*.tex`；**§14**；`../b5/` | **TN5K 换 R17 表**；删/改 pending；NHC 图 |
| **R3.3** | 数据层级、40 datasets | **部分** | 与 R2.3、R1.4 合并；B1 审计（**dHash**、**DDTI_cls=349**） | B1 `DATASET_AUDIT.md`；B12 | 流程图定稿；NHC 行待数据 |

---

## 范围外（非 B1–B12；本目录不起草回复正文）

| 编号 | 内部任务（参考） | 说明 |
|------|------------------|------|
| R1.5–6 | S1–S4、S10；F1–F3 | 报告、ThyClinScore、读者研究、安全叙事 |
| R2.5 | F5 | 参考标准与标注者 |
| R2.13 | F1/F2 | 读者研究混杂 |
| R2.15 | F9、G3 | 伦理、NHC DUA |
| R2.16–19 | S5–S7 | ReAct、并发、模板 |
| R3.4–5、R3 minor | S2、S7；F3 | 读者统计、证据→文本 |

**为何曾出现在旧版计划**：初稿按 `ThyroidXAgent_返修计划与回复_中文.md` **全文 R 索引** 填表，把 Shiyu/Fei 条与 B 包混在同一表里，便于总览返修；**不等于** B1–B12 的工作范围。

---

## B11 专项（R2.20–21）— 可起草回复，无需新实验

| 项 | 状态 |
|----|------|
| 新训练 / 加 radiomics CCA | **不需要** |
| R2.20(b) 分析 | **已完成**（读 `output/*/pipeline_run/.../selected_masks.npz` + GT；约 1 分钟/全队列） |
| 回复信 R2.20–21 | **可写**；英文回信从 `b11_b12/REVIEWER_SNIPPETS_ZH.md` 扩写 |
| 修订稿 Methods | **仅计划**（`MANUSCRIPT_REVISION_PLAN_ZH.md` §8.3–8.4）；**暂不直接改** `ThyroidXAgent.md` |

**R2.20(b) 数字（`mm_per_pixel=0.1`，`max_diameter_mm=5`；失败=空 mask 或 Dice&lt;0.1）**

| 队列 | n 匹配 | N (&lt;5 mm) | M | 小结节 mean Dice |
|------|--------|-------------|---|------------------|
| zjh8k（外测，回复主报） | 7958 | 1001 | 44 | 0.818 |
| tn3k | 614 | 68 | 2 | 0.771 |
| tn5k | 1000 | 103 | 12 | 0.696 |
| rjh7k | 7288 | 366 | 1 | 0.766 |
| ddti_seg | 637 | 54 | 1 | 0.734 |
| pktn | 150 | 15 | 1 | 0.741 |
| thyroidxl | 2090 | 0 | 0 | — |

回复 (b) 建议：主文强调 **M/N 比例低**（如 zjh8k 44/1001≈4.4%），并说明 **M 为整条 agent 流水线失败，非 radiomics 前删除**；脚注 **0.1 mm/px 为敏感性假设**（或定稿后替换为校准间距并重跑 `./scripts/revision/b11/run_r2_20_small_nodules_all.sh`）。

---

## B12 专项（R2.7 / R2.1 分类均值 / R2.3 / R1.4）— 无新实验

| 项 | 状态 |
|----|------|
| 补充实验 | **不需要** |
| 宏平均数字 | **已核对**（`b11_b12/README.md`） |
| 数据流图 | **组内假定已完成**；回复写「已补充」+ 简述阈值在 validation |
| 待做 | **修改计划 §9 条目统稿进 `ThyroidXAgent.md`**；起草 R2.7/R2.1/R2.3/R1.4 回复段 |

**回复要点（中文逻辑，非英文全文）**

- **R2.7**：感谢指出；「mean」= 五队列 **等权宏平均**；更正为 AUROC **0.9001**、AUPRC **0.8705**；图注与 S4 一致；可选报告加权均值。  
- **R2.1（分类部分）**：与 R2.7 同一组数字；说明原摘要/正文为未定义加权方式所致笔误。  
- **R2.3**：承认 test 「cases」混用图像/病例/报告；修订稿用 **分层计数**（OpenThyroid 图像 test、NHC 等）；28,458 全拆解若未齐则写 Limitation 或「见补充图/表」。  
- **R1.4**：已补充数据流图；ZJH 在通用外测与 LNM/FTC 开发上的数据 **分边**；分割/分类专家 **未在 ZJH 训练**。

素材：`b11_b12/REVIEWER_SNIPPETS_ZH.md`（R2.7/R2.1、R1.4）；改稿清单：`MANUSCRIPT_REVISION_PLAN_ZH.md` **§9**。

---

## B1+B2 专项（R1.1 / R2.2 / R2.4）— 计算已闭环（2026-10-22 更新）

| 项 | 状态 |
|----|------|
| dHash 近重复 | **已完成** → `b1/tables/near_duplicates.json` |
| ZJH excl. 敏感性 B2 | **已完成** → `zjh8k_b2_excl_train_dup.json` + `baseline_*_zjh8k_*_b2_excl_train_dup.json` |
| 主系统 + 基线 CI | **58/58 + 8 队列**（**不含 NHC**） |
| DDTI_cls | **n=349**（与 pipeline/B2 一致） |
| 待写作 | Methods 4.1/4.6 条文；Supp. ZJH 敏感性表；回复信摘 `B1_结论` §三 |
| 待可选 | F6 患者数；近重复人工 spot check |

**回复要点**：独立性叙事用 **dHash + 敏感性**（见 `B1_结论`）；勿在回复中声称原稿用过 filename stem 论证（原稿无此表述，故勿写「不再」）。

**ZJH 敏感性数字（主系统，供回信/Supp.）**：全量图级 AUROC **0.937** → excl. **0.927**；患者级 **0.982** → **0.958**；Dice **0.836** → **0.831**（6966 图 / 1078 患者）。

---

## B6 专项（R2.9）— **可起草完整回复**（sample 已闭环；TN3K 仅换数）

| 项 | 状态 |
|----|------|
| `router_spec.md` | **已有** → `docs/supplementary/router_spec.md` |
| 结构化 routing log（≥10 条） | **已有** → `output/sample/pipeline_run/routing_log.jsonl`（75 行；撰稿筛 ≥10 例制表） |
| 5× 稳定性汇总 | **已有** → `output/sample/pipeline_run/stability_summary.json`（*n*=10，`repeats`=5） |
| 回复信 R2.9 中英文 | **可起草** → `b6/REVIEWER_RESPONSE_SNIPPETS_B6.md`（与下表数字一致） |
| 修订稿 Methods/Supp. | **计划正文** → `MANUSCRIPT_REVISION_PLAN_ZH.md` **§11** |
| TN3K for_llm | **pipeline 进行中**；B6 定量需 `run_routing_stability.py --max-cases 10`（或与稿面 *n* 一致） |

**数据卡（与 snippets / §11.1 同步；换 TN3K 时只改右列来源）**

| 字段 | 当前（sample） |
|------|----------------|
| *n*（稳定性子集） | **10** |
| 平均选择一致率 | **92%**（`mean_selection_agreement`≈0.92） |
| 全稳定 | **8 / 10** |
| 低一致 | **2 / 10** 为 **60%**（`0002.jpg`、`0003.jpg`；0003 另 cls 80%） |
| 分层 | 本批 **均为 close**（10/10）；无 easy 层对比句 |
| 配置 / 产物 | `config/revision/b6/sample_stability.yaml`；`output/sample/pipeline_run/` |

**回复要点（中文逻辑，英文见 snippets）**

1. **透明性**：补充材料公开路由器完整规格（模型、解码参数、JSON schema）及结构化 `routing_log`（候选摘要、是否调用 LLM、选择与理由），附 **≥10** 条样例供审计。  
2. **5× 稳定性**：专家输出固定后，对 **10** 例每例 **5** 次 LLM 分割路由；平均选择一致率 **92%**；**8/10** 五次完全相同，**2/10** 为 **60%**，处于候选接近的 **close** 分层并伴重复间 Dice 波动。  
3. **外测队列**：说明 TN3K（for_llm）按**相同协议**报告（**TN3K `stability_summary.json` 产出后**把本段 cohort 名与上表数字替换；若仍用 sample 作主证据则可写「development sample 试点 + TN3K 复现」双句）。

**TN3K 完成后替换**：`MANUSCRIPT_REVISION_PLAN_ZH.md` §11.1、§11.3 → 本表 → `B6_ROUTING_STABILITY_CONCLUSIONS.md` → `REVIEWER_RESPONSE_SNIPPETS_B6.md`。**不必**改 R2.9 三条结构。

**补充实验**：sample **不需要**；TN3K 仅需 **stability 脚本**（非重训、非全量 250×5，除非稿面承诺）。

---

## B8 专项（R1.3 校准与送复核）— **接近定稿**（2026-10-24）

| 项 | 状态 |
|----|------|
| Validation pipeline + 合并 | **已完成** → `output/validation/no_llm_primary/`（**n=875**） |
| 定阈（**quantile=0.95**） | **已完成** → `output/b8/fit/abstention_thresholds.json` |
| 五 BM test 队列 eval | **已完成** → `output/b8/cohorts/{tn3k,tn5k,thyroidxl,zjh8k,ddti_cls}/` |
| 可靠性图 + risk–coverage PNG | **已完成** → `reliability_*.png`；`output/b8/figures/` |
| F4 阈值与 flagged 结果 | **JSON 已齐** → `fit/abstention_thresholds.json`；各队列 `results_flagged.json` |
| 稿面范围 | **五队列 + val**；**不含 NHC**；**不含** RJH-7K / DDTI_seg / PKTN（无分类标签） |
| 统稿待做 | Methods §4.x 段落；Supp. **校准表 + 送复核表**；`B8_CALIBRATION_ABSTENTION_CONCLUSIONS.md` 刷新 q95 |
| 与 B7 分工 | **R1.3 校准/拒答** 本包；**NHC 中心异质性/I²** 仍归 **B7**（**R2.6** 同条不同段） |

**回复要点（英文/中文可扩写）**：

1. 感谢审稿人关注 **概率校准** 与 **低置信/人工复核** 策略。  
2. 我们在 OpenThyroidDB **validation**（合并 **875** 张，与主评估相同 **非 LLM** 协议）上，按分类分歧（vote entropy、top-2 margin）与分割专家不一致（最小 pairwise IoU）定义不确定度，并以 **95th percentile** 固定阈值（**不在测试集上调参**）。  
3. **Validation** 上有病理标签子集（*n*=**725**）pooled **ECE≈0.088**、**Brier≈0.078**（可靠性图见 Supp.）。  
4. 在 **TN3K、TN5K、ThyroidXL、ZJH-8K、DDTI_cls** 测试集上报告 ECE/Brier 与 **送复核比例**（主队列约 **43–48%**）；剔除 flagged 病例后，保留子集分类准确率 **略高于** 全量（详见 Supp. 表）。我们说明：固定 validation 阈值在外测上触发更多复核，与 **队列间 margin 分布差异** 有关；并提供 **risk–coverage** 曲线供解读覆盖率–准确率权衡。  
5. **临床工作量与安全叙事**（R1.6）与合作者 **F4** 衔接，工程侧提供 `abstention_thresholds.json` 与逐例 `flagged_for_review` 标记。  
6. **NHC 多中心异质性**与个案中心（如 THYB_S_ZJ24）将随 **B7** 与中心元数据单独补充（本条 **不** 用 B8 烟雾或伪 validation 数字）。

**补充实验**：**不需要**（除非 B3 重跑后需 `run_b8_all_cohorts.sh --skip-backfill` 刷新 eval）。

---

## B3 专项（R1.2 / R2.8 / R3.1）— **接近定稿**（2026-10-25）

| 项 | 状态 |
|----|------|
| 波次 1（策略 1–5、8） | **已完成** → 九队列 `output/ablation/b3/<cohort>/_summary/b3_routing_table.csv` |
| 队列覆盖 | TN3K、TN5K、ThyroidXL、PKTN、DDTI_seg、DDTI_cls、ZJH-8K、RJH-7K（+ 开发 sample） |
| 结论文档 | **可起草** → `../b3/B3_WAVE1_RESULTS.md` §6；统稿明细 `MANUSCRIPT_REVISION_PLAN_ZH.md` **§13** |
| 回信 snippets | `../b3/REVIEWER_RESPONSE_SNIPPETS_B3.md`（定稿前并入 learned/LLM 一句） |
| **策略 6 learned** | **进行中 / 待齐** → val fit + test infer（`fit_learned_router.py`、`run_learned_cohort.py`） |
| **策略 7 LLM** | **稿面数字已齐** → `manuscript_llm_metrics.yaml` / `B3_LLM_RESULTS.md`（**非** `b3/*/llm/` 重跑）；与 **B4 L3** 同源 |
| CI | **cluster bootstrap**（1000, seed 42）已写入 `b3_metrics.json`；全队列 `--all-wave1` 重算后可刷 `export_b3_tables.py` |
| **NHC** | **未纳入** B3 主表；R3.1 最终须含 → 单独跑或 Limitation |
| B4 / 配对显著性 | 可选；`b3_paired_bootstrap.json` 待 B2 口径 |

**回复要点（中文逻辑，英文见 snippets）**

1. 感谢审稿人要求在同一 **固定专家池** 上系统比较路由；我们补充 **八种策略** 定义，并在 **九组外测/开发队列** 上报告波次 1（静态策略 1–5 + Oracle 上界）。  
2. **主要发现（波次 1）**：不存在全面占优的单一静态策略；**最大置信度** 分割路由在多个队列上明显劣于集成；分类与分割均在各队列测试集上报告（回复信 **表 R14–R15**，不单独向审稿人展开内部分歧子集）；**Oracle** 与最佳可部署策略之间仍有可观间隙。  
3. **策略 4（static_rule）** 在 B3 中为 **专家一致度** 规则（非完整 radiomics 级联），与主系统部署路径区分说明。  
4. **学习型路由（策略 6）** 与 **LLM 路由（策略 7）** 已纳入 Methods；**策略 7 性能** 与主文 Table S3/S4 一致（见 `B3_LLM_RESULTS.md`）；**策略 6 test 行** 仍待 disk 汇总后与静态策略及 Oracle 对照（R3.1「排第几」）。  
5. **NHC** 与多中心扩展将按协议并入主表或于 Limitations 说明时间表（与 **B7** 中心叙事衔接）。  
6. **95% CI** 定稿采用与主结果一致的 **cluster bootstrap**（与 B2 同 seed/层级）。

**补充实验**：波次 1 **不需要重跑**（除非统一专家池或 static_rule 口径变更）；**需要** 完成策略 **6** 的 test 评估并更新汇总 CSV（策略 **7** 见 yaml，与 B4 L3 共用）。

**B3 状态小结**：波次 1 **实验与叙事已闭环** → **接近定稿**；**策略 7** 已冻结于 yaml；**仍缺策略 6 全队列入主表** + **CI 口径定稿** + **NHC 行**。

---

## B4 专项（R2.8 / S6 对账）— **已归档**（L1+L2+L3；正式回复 R15–R16）

> **L3 数据源**：与 **B3 策略 7** 相同 → `docs/revision/b3/manuscript_llm_metrics.yaml`（`ThyroidXAgent.md` Table S3/S4，冻结 **2026-10-26**）。**不要求** `output/ablation/b3/<cohort>/llm/` API 重跑；与 L1/L2（shared-intermediate 消融栈）**协议不同**，Δ(L3−L2) 为稿面对照，见 `B3_LLM_RESULTS.md` §1。  
> **L1/L2 数据源**：`../b4/B4_STATUS_ZH.md` §3；机器表 `output/ablation/b4/<cohort>/b4_component_table.csv`（当前 CSV **仅含 L1/L2**，L3 以本专项为准）。  
> **换数约定**：主文 S3/S4 修订后 **只改 yaml** 并同步本表；L1/L2 若重跑 L1 cohort 则改 STATUS §3。

| 项 | 状态 |
|----|------|
| L1 九队列（无 NHC） | **已完成** → `artifacts/b4_l1_<cohort>.json` |
| L2（B3 策略 2 `soft_voting`） | **已完成** → 已写入 `b4_component_table.csv` |
| L3（B3 策略 7 / 稿面 LLM） | **已定稿（文档）** → 本表；可选物化 `b3/<cohort>/llm/b3_metrics.json` + `build_b4_tables` |
| Path B 附录 B-a/B-b/B-c | **待** `path_b_autogluon` + L3 Path B 子集（稿面 S3/S4 无分列） |
| S6 vs S4 对账备忘录 | **待写** → `docs/B4_S6_S4_reconciliation.md` |
| NHC L1 | **搁置**（标签路径缺失） |

### 三层定义（简）

| 层 | 含义 | 来源 |
|----|------|------|
| **L1** | 单 DINO `all_datasets` 专家 | L1 pipeline，`enable_agent=false` |
| **L2** | 专家池 + 软投票（B3 策略 2） | `b3/<cohort>/soft_voting` |
| **L3** | 全系统 LLM 路由（B3 策略 7 ≈ 投稿 S4） | **yaml / 策略 7 表** |

### 分割 Dice（点估计；Δ 为 L3−L2）

| cohort | *n* | L1 | L2 | **L3** | Δ(L3−L2) |
|--------|-----|-----|-----|--------|----------|
| tn3k | 614 | 0.8454 | 0.8559 | **0.8528** | −0.0031 |
| tn5k | 1000 | 0.8292 | 0.8097 | **0.8326** | +0.0229 |
| thyroidxl | 2090 | 0.8792 | 0.8640 | **0.8758** | +0.0118 |
| ddti_seg | 637 | 0.8492 | 0.8451 | **0.8562** | +0.0111 |
| pktn | 150 | 0.8388 | 0.8376 | **0.8299** | −0.0077 |
| zjh8k | 7958 | 0.8376 | 0.8356 | **0.9430** | +0.1074 |
| rjh7k | 7288 | 0.9128 | 0.8931 | **0.9146** | +0.0215 |

`sample`（*n*=10）仅作开发试点，L3 **不以** 旧 `b3/sample/llm` 为准，正式叙事用上表七队列。

### 分类 AUROC（点估计；Δ 为 L3−L2）

| cohort | *n* | L1 | L2 | **L3** | Δ(L3−L2) |
|--------|-----|-----|-----|--------|----------|
| tn3k | 614 | 0.7695 | 0.8282 | **0.8692** | +0.0410 |
| tn5k | 1000 | 0.9544 | 0.9437 | **0.9472** | +0.0035 |
| thyroidxl | 2090 | 0.9288 | 0.9359 | **0.9676** | +0.0317 |
| ddti_cls | 349 | 0.7506 | 0.7537 | **0.7991** | +0.0454 |
| zjh8k | 7958 | 0.9571 | 0.9322 | **0.9175** | −0.0147 |

### 回复要点（R2.8；英文可扩写）

1. 感谢审稿人追问 **增益来自堆叠、集成还是路由**；我们补充 **组件消融**：L1 单专家 → L2 固定软投票 → L3 **稿面全系统 LLM**（与 Table S3/S4 ThyroidXAgent 行一致）。  
2. **L2 vs L1**：队列依赖（如 TN3K 分类/分割均有提升；ZJH **L1 AUROC 高于 L2**）→ 说明「池化平均」非普适最优，需 **路由/全系统**（L3）与 **S6 对账** 一并解释。  
3. **L3 vs L2**：多数队列 L3 分类 AUROC 高于 L2；ZJH 分割 Dice **L3 远高于 L2**（稿面全系统 vs 消融 intermediate 协议差异，**勿**写成同一 pipeline 的逐步加和）。  
4. 与 **B3 波次 1** 交叉：静态路由无全胜；**B10** 澄清监督基线微调公平性。  
5. **Limitation**：层间 Δ 当前为点估计；Path B 放射组学分解表待附录脚本；NHC 未纳入 L1。

**统稿入口**：`MANUSCRIPT_REVISION_PLAN_ZH.md` **§15**；仓库细节 `../b4/B4_STATUS_ZH.md`、`../b4/README.md`。

**补充实验**：L3 **不需要 API 重跑**（稿面数已定）；Path B 附录与可选 `build_b4_tables` 物化 **非阻塞** 本专项回信。

---

## B5 专项（R3.2）— **接近定稿**（五 mode 已齐；**sample 占位 → TN5K 换数**）

> **稿面范围**：**性能消融仅 TN5K for_llm 单列表**（*n*=**250**），**不要求**九队列五 mode（与 B3/B4 区分）。  
> **换数约定**：下表数字来自 **sample（*n*=10）**，供当前起草；**TN5K 跑完后**用 `output/ablation/b5/tn5k/<mode>/` + `output/ablation/b3/tn5k/llm`（`full`）**只替换数字与 CI**，与 `MANUSCRIPT` **§14.1** 同步。

| 项 | 状态 |
|----|------|
| 五种 `metadata_mode` 定义 | **✅** → `docs/REVISION_B5_PLAN.md`；`shared/metadata_prompt.py` |
| sample 四 mode + B3 `llm`=`full` | **✅** → `output/ablation/b5/sample/{drop_device,drop_source,drop_both,quality_only}/`；`full` → `output/ablation/b3/sample/llm/` |
| 回复/改稿表结构与主对比叙事 | **✅**（**sample 数字**）→ 本专项 + **§14** |
| **正式回信 R3.2** | **✅** → `正式回复/latex/generated/body_{zh,en}.tex` + **表 R17**（sample 占位 + `\rpending` 换数项） |
| TN5K 四 mode（`--skip-full`） | **换数槽** → 更新 R17 + 删相关 `\rpending`；`build_b5_tables.py --cohort tn5k` |
| NHC 中心×专家热图（`full`） | **⬜** 院方/G3；不阻塞性能主表 |
| 九队列五 mode | **不做**（非 R3.2 最小集） |

**性能表（稿面队列：TN5K；**当前格内数字 = sample 占位**）**

| metadata_mode | *n*（占位→定稿） | Dice | HD95 | AUROC | AUPRC | 备注 |
|---------------|-------------------|------|------|-------|-------|------|
| **full**（B3 `llm`） | 10 → **250** | 0.837 | 14.0 | 0.92 | 0.927 | 非 `b5/sample/full/` |
| drop_device | 10 → **250** | 0.837 | 12.1 | 0.92 | 0.927 | 本批与 `quality_only` 同 seg 路由 |
| drop_source | 10 | 0.838 | 12.0 | 0.92 | 0.927 | |
| drop_both | 10 | 0.827 | 12.3 | 0.92 | 0.927 | 本批最低 Dice |
| quality_only | 10 → **250** | 0.837 | 12.1 | 0.92 | 0.927 | R3.2 主对比端点 |

**主对比（占位）**：**full → quality_only** → ΔDice **≈ −0.0002**、ΔAUROC **0**（TN5K 换数后重写并加 CI）。

**回复要点（TN5K 换数后保留条目）**

1. 在与 B3 **策略 7** 相同专家池与 shared intermediate 上，**仅**消融 prompt 中 **设备/数据来源** 等元数据（五档 + **`quality_only`**）。  
2. **性能（单队列 TN5K for_llm）**：五 mode 并列；主对比 **`full` vs `quality_only`**（占位 sample 上 Δ 近零；**以 TN5K 表为准**）。  
3. **选择模式**：`routing_log`；**NHC `full`** 热图 **将补充** 或 Limitation（与 **B7** 分条）。  
4. **限定**：Path B 短路致分类 LLM 少；Path B LLM 输入未做 metadata 消融（Methods 一句）。

**统稿入口**：`MANUSCRIPT_REVISION_PLAN_ZH.md` **§14**；`../b5/B5_UNDERSTANDING_ZH.md`；正式回信 **`正式回复/latex/generated/`**（R3.2 段落 + **R17**）。

**TN5K 换数清单**：① `metadata_ablation_tables_{zh,en}.tex` 数字（+CI）；② `body_*` R3.2 与 R17 表题/表注中的 `\rpending`；③ 本专项表与 **§14.1** 同步。

**补充实验**：**TN5K 换数**投稿前必做；**不必**九队列五 mode；NHC 热图加强 R3.2 但非性能表替代。

---

## B9 专项（R2.10–12 · LNM/FTC）— **已归档**（改稿真源在 `b9/`）

> **单一真源**：[`../b9/B9_ThyroidXAgent_修改与回复计划.md`](../b9/B9_ThyroidXAgent_修改与回复计划.md)（§2 S5 数、§3 改稿、§4 回复信）。  
> **本目录**：`MANUSCRIPT_REVISION_PLAN_ZH.md` **§16** 为索引；换数只改 b9 **§2**，再更新下文 **一行** 与 **§16.2**（保持同步）。

| 项 | 状态 |
|----|------|
| 5 折 OOF 协议 + DINO 五折 | **✅** |
| S5 ThyroidXAgent 灰底（LNM/FTC） | **🟡** OOF 可回复；全栈融合后换格 |
| E2 LNM C2、E4 FangDai 外测 | **⬜** |
| 专家 S5（LLNM / Tiger） | **✅** 独立素材 |
| 回复 R2.11 / R2.10 / R2.12 | **可起草** → b9 **§4** |

**S5 灰底一行**（与 `MANUSCRIPT` **§16.2** 同步，2026-10-26）：LNM **882** 簇 AUROC **0.718** / AUPRC **0.598**；FTC **722** 簇 AUROC **0.521** / AUPRC **0.109** — CI 与表注仅 [`b9` 主文档 §2](../b9/B9_ThyroidXAgent_修改与回复计划.md)。

**补充实验**：全栈 OOF、双外测为 **进行中/待排**；不在本目录计划里重复列 E1–E6（见 b9 §1 覆盖度表）。

---

## B10 专项（R2.14）— **接近定稿**（2026-10-23）

| 项 | 状态 |
|----|------|
| 仓库训练协议审计 | **已完成** → `b10/B10_基线训练协议总结.md` |
| Supp. 协议表 | **已完成** → `b10/tables/baseline_training_protocol.md`（`build_b10_protocol_table.py`） |
| 与 B2 出表 checkpoint | **已对齐** → `b2_exports/*/manifest.json` |
| R2.14 英文/中文回信 | **可起草** → `B10_结论与回复素材.md` |
| 统稿待做 | Methods 4.3、S3/S4 表注、LaTeX Supp.、**S[X]** 编号 |
| 定稿前核对 | ResNet DDTI vs ZJH 同 AUROC（A7）；MedSAM2/MedSegX run 名 |

**回复要点**：感谢审稿人；澄清 S3/S4 **监督**基线均在 **dataset_4 / dataset_3** 堆叠开发集上微调；ThyroidXAgent 满堆叠用同一开发数据（S6 逐级消融另表）；VLM 零样本/API 单独说明；外测仅用于 test；详见 **Supp. Table S[X]** 与 Methods §4.6 CI。可与 **R2.2** 中 S3/S4 数字 **同段或紧邻** 发出。

**补充实验**：**不需要**。

---

## 建议优先推进（2026-10-26）

**进行中包**：**B5**（R3.2，**接近定稿**：sample 占位、**TN5K 换数**）→ **B5 专项** + **§14**；**B7**（R1.3 NHC 段 + R2.6）→ G3 + `b7/`。

**已归档包**：B1–B4、B6、B8–B12 的回复要点见各 **专项** 与 `正式回复/latex/generated/body_*.tex`；统稿时按 [`README.md`](./README.md) 归档表取真源。

## 建议标注「修订稿将补充」、暂不写死数字（仍在 B1–B12 内）

- **R1.3 / R2.6（NHC 中心异质性）**：**B7（进行中）**、G3 元数据（B8 校准/拒答已归档，与 NHC 分条）
- **R3.2（元数据消融）**：正式回信 **已写入 R17**（sample 占位 + pending）；投稿前 **TN5K 换 R17**；NHC 热图 pending  
- R2.4 **患者**定位：**F6**（图级重复与敏感性已在 B1 可写）  
- **NHC**：B2 未批跑；稿面/回复单独说明或 Limitation  
- R2.5 标注：回复信占位已写；数字与表待 **F5** / 合作者确认  

---

## 与 `Nature Communications Reviews.pdf` 的对应说明

本计划按内部编号 **R1.1–R3.x** 与返修计划第二部分对齐（与 PDF 中 Reviewer 1/2/3 分条一致）。起草回复信时，每条先 **引用审稿原文** 一句，再接上表或 B11/B12 专项「可回复要点」。

**稿件修改计划**：[`MANUSCRIPT_REVISION_PLAN_ZH.md`](./MANUSCRIPT_REVISION_PLAN_ZH.md)
