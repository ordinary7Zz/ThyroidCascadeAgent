# B3 / B4　路由消融与组件消融（实现计划）

> **对应审稿意见**  
> - **B3**：R1.2、R2.8、R3.1  
> - **B4**：R2.8（含 Table S6 与 S4 数字对账）  
>  
> **范围**：ThyroidCascadeAgent + 论文专家池/评测协议（与投稿稿一致）；单专家重训若不在本仓库，在计划中单独标注路径。  
> **关联文档**：`docs/REVISION_B5_B6_B8_B11_PLAN.md`（B6 日志宜在 B3 LLM 全量跑之前就绪）、`返修计划自我理解.md`（任务语义）、根目录 `ThyroidXAgent_返修计划与回复_中文.md`（交付物清单）。

---

## 1. 任务一句话

| 任务 | 回答的问题 | 主交付物 |
|------|------------|----------|
| **B3** | 在**同一专家池**上，换八种「选专家」方式，**LLM 排第几**？离 Oracle 多远？ | 正文图或表；8 策略 × 分割/分类 × 全测试集（含 NHC-MISD-TUS）；配对 **cluster bootstrap** |
| **B4** | **哪一层组件**在贡献？为何 S6 单专家在 ZJH-8K 上反而高于 S4 全系统？ | **三层组件主表**（L1–L3）+ **Path B 放射组学分解附录** + 与投稿 **S4 逐位校验行**；更正 S6 表注；Results 段落 |

**B3 管决策层**（同一池，换选法）；**B4 管组件层**（单专家 → 池 → 路由；放射组学增量在 **Path B 子集**单独报告，避免与 B3 策略 7 重复计数）。B4 **不需要**在每层再跑八种策略。

---

## 2. 并行 vs 顺序（组织方式）

**不必等 B3 全部完成再开始 B4**；**必须先统一「共享地基」**，再两条线并行，在汇合点抄数填表。

```
                    ┌─ B4-A：S6/S4 对账、放射组学层级定义、与 B1 联动（立刻可做）
                    │
  共享地基 ─────────┼─ B4-B：单专家（完整堆叠数据）训练 + 全队列评测（GPU，与 B3 并行）
  (intermediate     │
   + 统一评测       ├─ B3 波次 0–1：Oracle / 单专家 / 平均 / 投票 / 置信度 / 规则
   + bootstrap)     │
                    ├─ B3 波次 2：LLM 路由 + 一致/分歧分层
                    └─ B3 波次 3：非 LLM 学习型路由（最后）

汇合点 1：B3「平均」完成 → 填 B4 L2（专家池）
汇合点 2：B3「LLM」完成   → 填 B4 L3（+ 路由，与投稿 S4 配置一致）
汇合点 3：L1–L3 + Path B 附录 + S4 校验 + 对账结论 → B4 定稿、S6 表注、回复 R2.8
```

**与 B5/B6 的先后**（勿与 B3/B4 混为一谈）：

- **B6**（`routing_log.jsonl`、`run_routing_stability.py`）：建议在 B3 **LLM 全量**之前完成。
- **B5**（`metadata_mode`）：依赖 B3 同一套 cache + 只重跑路由；在 B3 框架稳定后做。
- **B2**（患者级 cluster bootstrap）：B3 主表最终口径须与 B2 一致；开发期可用 `pipeline/evaluate.py` 的 bootstrap **打通管道**，全表定稿前升级为 **按患者/检查聚类** 的重采样。

---

## 3. 实验契约（动手前冻结）

以下全部策略共用，否则审稿人可质疑「不公平」：

| 项 | 约定 |
|----|------|
| 专家池 | 与论文 Table S3/S4 一致的分割池、分类池（Phase 1/2 **不含** AutoGluon；Path B 与附录叙事见 §6） |
| 专家输出 | 所有策略读**同一批** `intermediate/seg/*.npz`、`intermediate/cls/*.json`（及级联所需的 radiomics 输入） |
| 验证集 | 最优单专家、学习型路由、任何阈值 **仅在验证集** 拟合/选定，**不碰测试集** |
| 一致短路 | 分类：多模型 top_class 一致时不调 LLM → **建议保留**（真实系统行为）；**所有策略**在「一致子集」上行为须对齐定义，并 **分层报告** |
| 测试覆盖 | **所有**主文/补充测试队列，**必须包含 NHC-MISD-TUS**（35 未见中心） |
| 统计 | 策略间比较：**配对** cluster bootstrap（与 B2 同口径）；每格报告点估计 + 95% CI |
| Oracle | 用 GT 事后选最优专家 → **仅上界标尺**，图上/表中标为 upper bound，不可当作可部署策略 |
| **R3.1（路由泛化）** | B3 主表须含 **NHC-MISD-TUS** 及院内/外部队列；正文或补充中报告 **LLM vs 最佳非 LLM** 在 NHC 上与在 ZJH 等队列上 **排序是否一致**（可一句 + 分面图）。中心级细拆、I² 等交给 **B7**，B3 只证明「路由增益不是单中心技巧」 |
| **B2 统计截止** | 主表定稿前由 **B2 负责人**将 bootstrap 升级为 **患者/检查级 cluster**；B3 开发期可用 `evaluate.py` 图像级 CI，但投稿前必须替换并 **重算 B3/B4 表** |
| **Phase 4 协议** | B3 **不修改** Phase 4 的 ROI mask 来源（与当前 S4 一致，通常优先 `all_datasets` npz）；分类路由消融只动 Phase 5（及 Path B 的裁决逻辑），避免因换 mask 协议引入混杂 |
| **验证集划分** | 每个 `dataset_id` 在 `config/ablation_b3.yaml`（或附录表）中写明 **val 列表/比例**；策略 1 在 val 上按 **Dice（seg）/ AUROC（cls）** 各选一名专家，test **冻结**该选择 |
| **intermediate 指纹** | 每个 `output_dir` 写出 `intermediate_manifest.json`（`seg`/`cls` 文件列表 + sha256）；`ablation_summary` 汇总前校验 B4 L2/L3 与 B3 对应 mode **同 manifest** |
| **Phase 3 缓存（硬性）** | 仅改 `routing_mode` 时 **不得**因 `selected_masks.npz` 已存在而跳过 Phase 3；`run_routing_ablation.py` 须提供 `--force-phase3` 或 **每 mode 独立 `output_dir`**（推荐后者） |
| **Path B 与 AutoGluon** | B3 策略 **2/3/4/5/6**：Path B 分类裁决 **仅 3 个独立模型**，**不**并入 Phase 4 AutoGluon（与现 `_resolve_classification_path_b_static` 默认行为 **刻意脱钩**，见 §3.1.1）。策略 **7** 与投稿 S4 一致：Path B **含** AutoGluon + LLM 全信号 |
| **`routing_mode` vs `enable_agent`** | **`routing_mode` 为策略唯一开关**；`enable_agent` 仅在 `routing_mode=llm` 时表示调用 LLM API，**不再**用 `enable_agent=false` 隐式代表多种非 LLM 策略 |

### 3.1 级联输出与 Path A/B（与 `pipeline/cascade.py` 一致）

**推理顺序（与 Path 无关）：** Phase 1 分割专家 → Phase 2 独立分类专家 → 写入 `intermediate/`。B3 **不重跑** Phase 1–2，只在后续阶段换「选法」。

**每张图在 Phase 3 开头：** 用 Phase 2 结果判 **分类共识**。若独立模型 `top_class` 一致 → **Path A**，得到 **锚点** `anchor_class`（`"良性"` / `"恶性"`，非 GT、非最终 `final_label`）；否则 **Path B**，锚点为 `None`。

| 最终产物 | 如何得出 |
|----------|----------|
| **分割** | Phase 3 的 `selected_mask` → `intermediate/selected_masks.npz`（评测 Dice/HD95） |
| **分类** | Phase 5 的 `final_label` → `results.json`（Path A：采纳锚点，不调分类 LLM、AutoGluon **不进终裁**；Path B：按 `routing_mode` 裁决——**B3 主表**见 §3.1.1；投稿 S4 = 策略 7，Path B 含 AutoGluon） |

**B3 在级联里的插槽（主表 S4 协议）：**

- **分割 B3：** 插在 **Phase 3**（替换 `select_best_mask` / `_select_mask_static`，或在 `intermediate/seg` 上做平均/投票/Oracle 等 **不经 Agent** 的后处理）。**Path A 与 Path B 都要跑**；差别仅为是否传入 `classification_anchor`。
- **分类 B3（级联）：** 插在 **Phase 5 的 Path B 子集**（替换 `resolve_path_b` / `_resolve_classification_path_b_static`）。**Path A 上分类无需再「选专家」**——各策略在共识短路下应 **等价**（仅锚点采纳）；主表须 **分层报告**（全量 vs 仅 Path B），或单独注明「分类路由指标仅在分歧病例上定义」。
- **独立分类池上的八种策略**（论文五专家 + LLM 选 `selected_model`）：用 **`run_cls.py` + 固定 mask** 做 **补充表（Supp.）**；与级联 S4 主表 **分开写 Methods**，正文主表以 **级联 seg + 级联 cls（全量 + Path B）** 为准。

**换策略重跑：** 复用同一 `intermediate/seg`、`intermediate/cls`；切换分割/分类路由时须 **删除或隔离** `selected_masks.npz`（及该策略下的 `results.json`），或 **每个 `routing_mode` 使用独立 `output_dir`**，避免 Phase 3 因缓存跳过而静默用错 mask。

**分割消融与级联耦合：** 更换 Phase 3 选 mask 策略会改变 Phase 4 ROI 输入；**分割 B3 主指标**以 Dice/HD95（`selected_masks` vs GT）为主；**分类 B3** 在固定 Phase 4 缓存协议下只动 Phase 5（§3 契约「Phase 4 协议」）。Methods 中一句交代即可。

### 3.1.1 策略–代码注册表（S4 主表八种策略的唯一入口）

下列映射为 **投稿前冻结** 的实现契约；禁止用「改 `enable_agent`」代替多种非 LLM 策略。单元测试：每种 `routing_mode` 在固定 fixture 上 `seg_decision.method` / `cls_decision.method` **互不相同**（Oracle 仅评测脚本）。

| # | `routing_mode` | 分割 Phase 3（Path A/B 均执行，差别为 `anchor_class`） | 分类 Phase 5 **仅 Path B**（Path A 各策略等价，只报一次） |
|---|----------------|------------------------------------------------------|-----------------------------------------------------------|
| 1 | `best_single` | val 选定一名专家，test 固定取其 mask | val 选定一名独立模型，test 固定 `top_class` |
| 2 | `soft_voting` / `average` | 离线掩膜/概率平均 → 写入 `selected_masks.npz` | **仅 3 个独立模型**概率平均，**不含 AutoGluon** |
| 3 | `majority` | 像素级多数投票 | 独立模型类别多数票，**不含 AutoGluon** |
| 4 | `static_rule` | **`CascadePipeline._select_mask_static`**（batch 非 LLM 默认；**不是** `SegmentationAgent._fallback_selection`） | 与策略 2 同级的静态组合规则，或单独 `path_b_static_rule`；**不含 AutoGluon** |
| 5 | `max_confidence` | 取 `mean_confidence` 最高专家的 mask | 取 `top_confidence` 最高独立模型，**不含 AutoGluon** |
| 6 | `learned` | 全图特征路由（分割无 Path 子集） | **仅在 Path B 子集**训练/推理，触发与 LLM 一致；**不含 AutoGluon** |
| 7 | `llm` | `SegmentationAgent.select_best_mask`（含 Phase 3 `radiomics_judge` 注入 prompt，与 S4 一致） | `LLMClassificationAgent.resolve_path_b`（**含** Phase 4 AutoGluon 与分割 reasoning） |
| 8 | `oracle` | `routing/oracle.py`，GT mask 选最优 Dice/HD95 | GT label 选最优独立模型 AUROC 代理（每例），**不含 AutoGluon**；定义写入 `routing/oracle.py` 注释 |

**与现代码差异（实施时必须改）：**

- 今日 `enable_seg_agent=false` 时 batch 已走 `_select_mask_static` → 注册为 **`static_rule`（策略 4）**，与 `max_confidence`（策略 5）**分岔实现**。
- 今日 `enable_cls_agent=false` 时 Path B 走 `_resolve_classification_path_b_static`（**含 AutoGluon 软投票**）→ B3 策略 2–6 须改为 **独立模型-only** 的 Path B 分支；**仅策略 7** 保留现 S4 行为。

**P1（不挡主表）：** 与 prompt【决策序】逐条等价的 `static_rule_prompt_order` 可作为策略 4 备稿或 Supp. 行，**不**替代上表「生产默认 `_select_mask_static`」。

### 3.2 `config/ablation_b3.yaml` 闸门（开跑 B3 前填表归档）

与投稿 **Table S3（分割）/ S4（分类）** 逐行对照，缺一行不得全队列跑 LLM。建议用表格或 YAML 注释维护：

| 字段 | 说明 |
|------|------|
| `name` | 与 `intermediate/{seg,cls}/<name>.*` 文件名一致 |
| `type` / `model_path` | 与稿中 checkpoint、训练数据描述一致 |
| `in_phase1_seg` / `in_phase2_cls` | 是否进入 B3 专家池 |
| `paper_table_row` | 如「S4 ThyroidXAgent 池成员 #3」 |
| `notes` | 与当前 `config.yaml` 差异（若开发机仍用 MedSAM2 等占位） |

文件路径建议：`config/ablation_b3.yaml`（从论文池复制，**不要**长期用未对齐的 `config.yaml` 跑 B3 主表）。

---

## 4. B3：八种策略与实施波次

### 4.0 策略与级联阶段的对应关系

八种策略 **不限于**「LLM 开关 vs 静态 fallback」：平均、投票、最优单专家、Oracle 等可在 **只读缓存** 的路径实现，**不必进入** Agent。与级联阶段的对应建议如下：

| 任务 | Phase | Path A | Path B |
|------|-------|--------|--------|
| 分割路由 | **3** | 有锚点选 mask | 无锚点选 mask |
| 分类路由（级联） | **5** | 固定锚点（B3 分类策略 **无实质差异**，可只算一次） | LLM / 软投票 / 学习型等 **全部可比** |

实施时 `run_routing_ablation.py` 的 `--task seg|cls|both`：**`seg`** 只重跑 Phase 3（+评测）；**`cls`** 在级联下重跑 Phase 4–5（或 **固定 Phase 4 缓存** 后只重跑 5）；**`both`** 为完整 S4 链路。B4 的 L2/L3 抄数时 **分割、分类各取一列**：L2 = B3 策略 2 的 **seg 行 + cls 行**（级联 cls 建议同时报 **全量** 与 **Path B 子集**，见 §4.3）；L3 = B3 策略 7 的 **seg 行 + cls 行**，而非整张表只有一个合并数字。

### 4.1 策略梯子

| # | 策略 | 实现要点（目标代码形态） |
|---|------|--------------------------|
| 1 | 验证集最优单专家 | `routing_mode: best_single` + `routing/best_single_expert.py`（val 选参，见 §3 验证集划分） |
| 2 | 概率/掩膜平均 | `routing_mode: soft_voting`；seg 离线平均；cls Path B **独立模型-only**（§3.1.1） |
| 3 | 多数投票 | `routing_mode: majority`；seg 像素票；cls Path B 独立模型-only |
| 4 | 静态规则（生产默认） | `routing_mode: static_rule` → **`CascadePipeline._select_mask_static`**；cls Path B 静态规则分支，**不含 AutoGluon** |
| 5 | 置信度路由 | `routing_mode: max_confidence`；与策略 4 **不同代码路径** |
| 6 | 非 LLM 学习型路由 | `routing_mode: learned`；特征与 `routing_log` / prompt 对齐；cls **仅 Path B** |
| 7 | LLM 路由 | `routing_mode: llm`（`enable_agent=true`）；完整 S4 Path B（**含 AutoGluon**）。复用 `intermediate/`，不重跑 Phase 1–2 |
| 8 | Oracle | `routing_mode: oracle`（仅 `run_routing_ablation` / 评测）；`routing/oracle.py` |

**闭合率**（写在图注或 Results）：

\[
\text{closure} = \frac{\text{metric}(\text{strategy}) - \text{metric}(\text{best single})}{\text{metric}(\text{Oracle}) - \text{metric}(\text{best single})}
\]

### 4.2 实施波次（不要一次改完八种再跑）

| 波次 | 内容 | 是否调 LLM API | 依赖 |
|------|------|----------------|------|
| **0** | 契约 + `config/ablation_b3.yaml`；Phase 1–2 写满 `intermediate/`；`run_routing_ablation.py` 骨架；**策略注册表 smoke test**（每 mode `method` 字段可区分） | 否 | 数据集路径、专家权重 |
| **1** | **seg**：`compare_models` + 离线 2/3/5/8 + `static_rule`；**cls**：有 cache 时 **Phase 3+5 轻量重跑**（固定 Phase 4），Path B 独立模型-only 分支；**1 个小队列 + sample** | 否 | 波次 0 |
| **2** | 策略 7；`log_routing`；一致 vs 分歧分层 | 是 | B6 建议已就绪 |
| **3** | 策略 6；策略 1 全队列 val 选参 | 否（训练轻量） | 波次 2 的 Path B 定义 |
| **全量** | 所有测试集；配对 bootstrap；`b3_routing_table.csv` + 主文图 | 视策略 | B1/B2 口径冻结后定稿 |

### 4.3 代码修改计划（本仓库）

**原则**：专家推理只跑一次；路由是可插拔的 **Phase 3（分割）与 Phase 5 Path B（分类）** 决策，或基于缓存的离线策略；Path A 分类不参与路由对比（见 §3.1）。

| 优先级 | 项 | 说明 |
|--------|-----|------|
| P0 | `classification` Phase 5 **Path B 分支** | 按 `routing_mode` 分派；实现 **独立模型-only**（2/3/4/5/6）与 **S4 全信号**（7）；**先于**分割八种策略打通 cls 主表 |
| P0 | `segmentation.agent.routing_mode` / `classification.agent.routing_mode` | 枚举见 §3.1.1；`oracle` 仅评测脚本允许 |
| P0 | `pipeline/cascade.py` Phase 3 分派 | `routing_mode` 调度：`llm` → `select_best_mask`；`static_rule` → `_select_mask_static`；2/3/5/8 → 离线或专用函数；**禁止**仅用 `enable_seg_agent` 隐含策略 |
| P0 | `scripts/run_routing_ablation.py` | `--config`、`--output-dir`、`--routing-mode`、`--task seg\|cls\|both`、`--force-phase3`；每 mode 写 **`results.json`** + **`intermediate_manifest.json`** |
| P0 | `pipeline/routing_ablation.py` | cache → strategy → `evaluate.py` 同指标 |
| P0 | `pipeline/ablation_summary.py` | `b3_routing_table.csv`、`b3_paired_bootstrap.json`；**`metrics_all`** + **`metrics_path_b_only`**；manifest 校验 |
| P0 | `pipeline/compare_models.py` | 波次 1 分割侧 Oracle/单模型对比；与 `routing_ablation` 共用加载逻辑 |
| P1 | `routing/learned_router.py` | 特征与 `routing_log` 对齐；`artifacts/learned_router_{task}.joblib` |
| P1 | `routing/oracle.py` | `gt_mask_dir` + label；禁止写入生产默认路径 |
| P1 | `static_rule_prompt_order`（可选） | prompt 决策序 if-else；Supp.，不替代 `static_rule` |
| P2 | `pipeline/evaluate.py` 或新模块 | 患者/检查级 cluster bootstrap（B2）；`paired_bootstrap_diff` |
| 已有可复用 | `pipeline/cascade.py` | Path A/B 共识、Phase 4 缓存、`_select_mask_static` |
| 已有可复用 | `classification/agent.py` | `resolve_path_b`（策略 7）；一致短路 |
| 已有可复用 | `segmentation/agent.py` | `select_best_mask`（策略 7）；`_fallback_selection` 仅 LLM 失败降级，**不是** B3 策略 4 |
| 已有可复用 | `run_routing_stability.py` | B6；与 B3 共用 cache |

**配置示例（片段，待实现后写入 `config/ablation_b3.yaml`）**：

```yaml
segmentation:
  agent:
    routing_mode: "max_confidence"   # 策略 5；策略 7 时 routing_mode: llm + enable_agent: true
    enable_agent: false              # 仅 routing_mode=llm 时为 true

classification:
  agent:
    routing_mode: "soft_voting"      # 策略 2（Path B 独立模型-only，见 §3.1.1）
    enable_agent: false

pipeline:
  log_routing: true
  output:
    output_dir: "output/ablation/b3/zjh8k/avg"
```

**目录约定**：

```text
# 推荐：共享 intermediate 的只读副本或 symlink，每种 mode 独立子目录，避免 selected_masks 冲突
output/ablation/b3/<dataset_id>/<routing_mode>/
  intermediate/seg/*.npz      # 或与 ../shared/intermediate 共用
  intermediate/cls/*.json
  intermediate/selected_masks.npz
  results.json
  routing_log.jsonl          # LLM / 审计
  b3_metrics.json            # 本数据集该策略汇总
  intermediate_manifest.json # seg/cls 文件 sha256（B4 交叉校验）
output/ablation/b3/_summary/
  b3_routing_table.csv
  b3_paired_bootstrap.json
  figures/b3_ladder_seg.png
  figures/b3_ladder_cls.png
```

---

## 5. B4：三层组件主表、S4 校验与 S6/S4 对账

### 5.1 三层主表 + S4 校验 + Path B 放射组学附录

**设计说明：** 投稿 S4（ThyroidXAgent 全系统）在代码上 **等于 B3 策略 7**（Path B 已含 AutoGluon）。若再设「L4 = L3 + 放射组学」，主表会出现 **零增量**。因此 B4 **主表止于 L3**，放射组学贡献在 **Path B 子集附录** 报告；另增 **S4 校验行** 与投稿 Table S4 **逐位一致**（配置 = `config/ablation_b3.yaml` 投稿快照）。

#### 5.1.1 三层组件主表（正文或 Supp. Table）

| 行 | 系统配置 | 决策方式 | 与 B3 关系 |
|----|----------|----------|------------|
| **L1** | 单个 DINOv3 专家（**完整堆叠训练数据**） | 无「选」 | **B4 独跑**（训练可能在 `my_Thyroid_Infer` 等） |
| **L2** | DINO **专家池**（独立 Phase 1/2 模型，**不含** AutoGluon 作第五分类候选） | **固定掩膜/概率平均**（策略 2；Path B cls **独立模型-only**） | **= B3 策略 2** 的 seg 行 + cls 行（全量 + Path B） |
| **L3** | L2 + **LLM 路由器** | 分割 Phase 3 LLM + 分类 Phase 5 Path B LLM（**含** AutoGluon，与 S4 一致） | **= B3 策略 7**；备稿可加「B3 最佳非 LLM（策略 6 或 4/5）」一行对比 |

| **S4 校验** | 投稿 ThyroidXAgent 全系统 | 与 L3 **应同配置、同数字**（允许独立 `output/ablation/b4/<ds>/s4_replica/` 重跑校验） | 与 Table S4 对照；不一致则停表查 manifest / 配置漂移 |

逐层报告 **Δmetric（相对上一层）** 与 95% CI。**表结构：** 每个测试集分 **`task=seg`**（Dice/HD95）、**`task=cls`**（AUROC/AUPRC）；cls 同时报 **全量** 与 **`metrics_path_b_only`**。L2/L3 与 B3 对应 mode 须 **`intermediate_manifest.json` 一致**。

#### 5.1.2 Path B 放射组学分解附录（回答「放射组学加了什么」）

在 **同一 Path B 病例集**上固定 Phase 3 mask（取自 L3 或策略 7），只改 Phase 5 信号组合（Phase 4 缓存不变）：

| 附录行 | Path B 裁决 | 用途 |
|--------|-------------|------|
| **B-a** | 仅 3 个独立模型软投票/平均 | 与 B3 策略 2 在 Path B 上一致（**无 AutoGluon**） |
| **B-b** | 独立模型 + AutoGluon 加权软投票（**无 LLM**） | 对应将实现的 `path_b_static_with_autogluon`（现 `_resolve_classification_path_b_static`） |
| **B-c** | 策略 7 全信号 LLM | 与 L3 cls（Path B）一致 |

报告 **Δ(B-b − B-a)**、**Δ(B-c − B-b)** 及 CI，用于 Results 中放射组学与 LLM 的 **可分贡献**；**不**与 L1–L3 主表混为额外的「L4」行。

### 5.2 S6 vs S4 对账（与 B4 并行，不依赖八种策略）

| 现象 | 待核实来源 |
|------|------------|
| S6 单专家 ZJH-8K AUROC **0.992–0.994**，S4 ThyroidXAgent **0.9175** | 训练数据累加方式、单次 vs 多次平均、划分、标签键 |
| S6 单专家 Dice **94.57–94.85** vs S4 **94.30** | 同上 + 评测 mask 是否同一路由输出 |
| 「仅 TN3K」在 ZJH-8K 极高 AUROC | 与 **B1** 患者/近重复审计联动 |

**交付**：`docs/B4_S6_S4_reconciliation.md`（或本节附录）写清结论类型：

- **A 类**：协议/表注错误 → 更正 S6 caption + 统一数字；  
- **B 类**：协议正确但路由劣于单专家 → Results 如实写 + 调整主张；**须同时报告 L1 全图 cls** 与 **L3 全图 + Path B**，避免仅用 Path B 子集掩盖全队列 AUROC 落差（与 R2.8 回复模板绑定）；  
- **C 类**：疑似泄漏/重叠 → 与 B1 合并处理，再谈消融叙事。

### 5.3 B4 代码与跑数

| 项 | 说明 |
|----|------|
| L1 单专家 | 不在 ablation 脚本内训练；`results_single_expert.json` → `ablation_summary` |
| L2–L3 | 自 B3 mode 目录 **`results.json`**（`soft_voting` / `llm`）引用；**manifest 校验** |
| S4 校验 | `run_pipeline.py` + 投稿配置，`output/ablation/b4/<dataset>/s4_replica/`；与 L3 **diff 应为空**（或仅随机种子/API 噪声在 CI 内） |
| Path B 附录 | 同一 `output_dir` 下跑 B-a/B-b/B-c 三种 Phase 5 模式 → `b4_pathb_radiomics_table.csv` |
| 汇总 | `b4_component_table.csv`（L1–L3 + Δ）+ `b4_pathb_radiomics_table.csv` |

---

## 6. 放射组学 / AutoGluon：必须先决与级联中的角色

论文写放射组学为 **independent signal（池外）**；代码中 AutoGluon 常为分类池 **第 5 个候选（池内）**（`run_cls` 五专家叙事）。

**同一 `radiomics_judge` 在级联里的三种用法（写 Methods 时勿混为一谈）：**

| 角色 | 阶段 | 作用 |
|------|------|------|
| **Mask 级裁判** | Phase 3，`judge_batch` 各候选 mask | 预筛选 / 分割 prompt 中的 `radiomics_judge` 字段；**不是** S4 分类终裁 |
| **ROI 分类信号** | Phase 4 → `autogluon.json` | 对固定 ROI 协议的良恶性预测；Path A **终裁不用**，Path B **可进** Phase 5 |
| **五专家池成员** | 仅 `run_cls` + 注册 `autogluon_radiomics` | LLM **选 `selected_model`**；与 S4 级联 Path B **综合裁决**不同 |

B3/B4 主实验默认 **S4 级联**；`run_cls` 五专家表为 **Supp.**，不与 L3/S4 校验混排。

**Methods 冻结叙事（与 §5.1 一致，开跑 B4 主表前签字）**：

- **专家池（Phase 1/2）**：仅 DINO 系列独立模型（与 Table S3/S4 一致）；AutoGluon **不作为** Phase 2 池成员。  
- **L2**：池内 **平均/投票**（B3 策略 2），Path B 分类 **不含** AutoGluon。  
- **L3 / 投稿 S4**：LLM 路由 + Phase 3 `radiomics_judge` + Path B **含** Phase 4 AutoGluon（策略 7）。  
- **放射组学「独立信号」**：在正文用 **§5.1.2 Path B 附录** 表述（B-a→B-b→B-c），而非再叠一层「L4 全系统」。

未冻结前可先跑 B3（策略 2–7），但 **B4 主表与 Path B 附录不要对外定稿**。

---

## 7. 期望结果：跑通后应看到什么

下列为 **计划完成并全量跑数后** 在磁盘与论文侧应出现的产物；数值为 **形状示例**，不是承诺的论文结论。

### 7.1 工程产物（每个测试集）

| 检查项 | 期望 |
|--------|------|
| `intermediate/seg` | 每个分割专家一个 `.npz`，病例数 = 测试集图像数 |
| `intermediate/cls` | 每个分类专家一个 `.json`，与 seg 病例对齐 |
| 各 mode 下 `results.json` | 路径：`output/.../<routing_mode>/results.json`；每例含 `path`、`classification_consensus`、`final_label`、`seg_decision` 等；与 `evaluate.py` 可消费 |
| `b3_metrics.json` | 含 `dice_mean`, `hd95_mean`, `auroc`, `auprc` 及 CI；含 `n_total`, `n_consensus`, `n_disagreement`；级联分类须含 **`metrics_path_b_only`** 块 |
| `b3_routing_table.csv` | 行 = 策略，列 = 数据集 × 任务 × 指标；含 Oracle 行 |
| `b3_paired_bootstrap.json` | 关键对比的差值 CI，如 `llm vs learned`, `llm vs average` |
| `b4_component_table.csv` | L1–L3 + 每层 Δ + **S4 校验行**；`b4_pathb_radiomics_table.csv` 为 Path B 附录 |

### 7.2 波次 0–1 完成后（小队列 / sample）

**应能回答**：

- Oracle 行是否 **严格高于** 所有可部署策略（除数值 tie）；若 Oracle ≤ 平均，说明 Oracle 实现或 GT 对齐有 bug。  
- 最优单专家 vs 平均：gap 是否合理（通常较小）。  
- 同一 `intermediate` 下换 `routing_mode` **不重跑 Phase 1–2**（日志里应出现「已有缓存，跳过」）。

**示例（虚构 sample，仅说明表形态）**：

| strategy | task | AUROC | 95% CI |
|----------|------|-------|--------|
| best_single | cls | 0.88 | 0.82–0.93 |
| soft_voting | cls | 0.90 | 0.85–0.94 |
| oracle | cls | 0.96 | 0.92–0.99 |

### 7.3 B3 全量完成后的「科学形态」期望

主文读者应能读出以下 **结构**（具体谁最高由数据决定）：

1. **阶梯图**：横轴 8 种可部署策略 + Oracle 虚线；纵轴 Dice 或 AUROC；分割、分类各一张。  
2. **NHC 子集（R3.1）**：LLM 相对平均/学习型 **不应只在 ZJH 涨、在 NHC 崩**；补充 **分队列分面图** 或表注一句「NHC 上策略排序与院内队列一致/不一致及解释」（细节异质性见 B7；元数据依赖见 B5）。  
3. **分层**：报告例如「分类 62% 病例一致短路、38% 分歧；LLM 仅作用于 38%」；在分歧子集上 LLM 相对平均的 Δ 可大于全量 Δ。  
4. **闭合率**：LLM 相对单专家的闭合率若为 0.2–0.6，可叙述为「部分吃掉 Oracle 增益」；若 ≈0，叙事走 A9 备选（可审计、跨任务复用）。

**三种结论形态与回复信**（实现前备好模板）：

| 结局 | 期望在表中的表现 | 回复 R1.2 / R2.8 方向 |
|------|------------------|------------------------|
| LLM 显著优于学习型与平均 | 全量或分歧子集上配对 CI 不含 0 | 强调 agentic routing 的独立增益 + 闭合率 |
| LLM ≈ 学习型 | 差值 CI 跨 0 | 承认；强调可审计理由、无重训跨任务（LNM/FTC） |
| LLM 劣于简单基线 | 诚实报告 | 调整摘要主张；B4 备「最佳非 LLM」行 |

### 7.4 B4 全量完成后的「科学形态」期望

1. **三层主表 + S4 校验**：L1 → L2 → L3 **不保证单调**（允许路由略差），但 **每层 Δ 带 CI**；**S4 校验行与 L3 一致**（否则先查配置/manifest）。  
2. **Path B 附录**：B-a / B-b / B-c 清晰分离「无 AG → 有 AG 无 LLM → 全系统 LLM」；至少一项 Δ 的 CI 可支撑放射组学或 LLM 叙事。  
3. **S6/S4**：对账备忘录 **A/B/C**；B 类须 **全图 + Path B** 同时报告（§5.2）。  
4. **与 B3 一致**：L2/L3 与 B3 策略 2/7 **同 manifest**；cls 分 **全量** 与 **Path B**。  
5. **单专家 L1**：ZJH-8K 上若仍 **远高于** L3，回复中主动解释（域偏移、路由目标与 AUROC 不一致等）。

### 7.5 失败/报警信号（出现则需停表查因）

| 信号 | 可能原因 |
|------|----------|
| 不同策略用了不同病例数 | cache 不完整或 mode 间 intermediate 不一致 |
| Oracle 低于某简单策略 | GT/mask 对齐错误、或 Oracle 定义错 |
| 重跑 Phase 1 而只改 routing_mode | ablation 脚本未走 cache-only 路径 |
| B4 L2 ≠ B3 average | 汇总脚本、池定义或 Path B 仍含 AutoGluon |
| L3 ≠ S4 校验行 | 配置漂移或未用投稿 `ablation_b3.yaml` 快照 |
| 策略 2–6 cls 与策略 7 同 `method` | Path B 未实现独立模型-only 分支 |
| 仅 TN3K 训练在 ZJH-8K AUROC > 0.98 | 优先 B1 泄漏审计，暂停夸大外部泛化 |

---

## 8. 实施检查清单

### 共享地基

- [ ] **`config/ablation_b3.yaml` 与论文 S3/S4 对照表**（模板：每行 `model_name` | `type` | `checkpoint路径` | 进 Phase1/2 池 | 与稿中表注一致）已签字  
- [ ] 论文专家池与 `config/ablation_b3.yaml` 一致  
- [ ] 全测试集 Phase 1–2 完成或可按数据集批量调度  
- [ ] `run_routing_ablation.py` + `ablation_summary.py` 在 sample 上端到端通过  
- [ ] **策略注册表 smoke test**（§3.1.1）通过  
- [ ] 每 mode 写出 `intermediate_manifest.json`  
- [ ] Bootstrap 口径与 B2 对齐（或文档注明过渡期用 image bootstrap）

### B3

- [ ] 波次 1：**6 种非 LLM 策略（1–5、规则 4）+ Oracle(8)** 在小队列通过；分割侧可先用 `compare_models` 读 `intermediate/seg` 校验  
- [ ] 波次 2 LLM + `routing_log.jsonl` + 一致/分歧分层  
- [ ] 波次 3 学习型路由 + 与 LLM 配对检验  
- [ ] 全队列 `b3_routing_table.csv` + 主文图稿  
- [ ] 回复信 R1.2 / R2.8 / R3.1 段落引用具体数字与 CI  

### B4

- [ ] `B4_S6_S4_reconciliation.md` 定稿  
- [ ] 放射组学池内/池外定义写入 Methods  
- [ ] L1 单专家全队列结果  
- [ ] L2/L3 与 B3 交叉校验（manifest）  
- [ ] S4 校验跑通且与 L3 一致  
- [ ] Path B 附录 `b4_pathb_radiomics_table.csv`  
- [ ] `b4_component_table.csv` 定稿  
- [ ] S6 表注更新 + Results 讨论段落  

---

## 9. 粗算工时（单人，仅供参考）

| 模块 | 天 |
|------|-----|
| P0 脚手架（含 Path B cls 分派 + manifest）+ 波次 0–1 | 5–7 |
| B3 波次 2 LLM 全量（含 API；多队列前建议小批量估时/费用） | 3–7 |
| B3 波次 3 学习型路由 + 策略 1 全队列 val | 3–5 |
| 汇总、配对 bootstrap、作图（含 B2 cluster 重算一轮） | 4–5 |
| B4 对账 + L1 训练协调 | 并行，视训练 5–10+ |
| B4 表与文稿 | 1–2 |

---

## 10. 文档变更记录

| 日期 | 说明 |
|------|------|
| 2026-10-13 | 初版：集成 B3/B4 并行实施、波次计划、代码项、期望结果与检查清单 |
| 2026-10-13 | §3.1 / §4.0：级联 Path A/B、锚点、B3 插槽（Phase 3 分割 / Phase 5 Path B 分类）、`run_cls` 分轨；目录与 `selected_masks` 缓存说明 |
| 2026-10-13 | 缺口修订：R3.1/B2 截止、Phase 4 固定、§6 AutoGluon 三角色、B4 分 task 抄数、`metrics_path_b_only`、`compare_models`、检查清单与 §7.1 路径统一 |
| 2026-10-13 | **策略–代码注册表**（§3.1.1）；Path B 独立模型-only vs 策略 7；B4 改为 **L1–L3 + S4 校验 + Path B 附录**；契约增 val/manifest/force-phase3；P0 实施顺序与波次/工时调整 |
