# ThyroidCascadeAgent 返修增量：B5 / B6 / B8 / B11 计划

> 范围：仅本仓库代码与配置；不引入新数据集；专家模型不重训。  
> 与论文返修任务 B3/B4 的关系：本四项为先导工程（可审计、可消融、可校准），B3 跑表前应完成 B6，B5 宜在 B3 的 LLM 策略全量跑之前完成。

---

## 实施顺序

```
B6（日志 + prompt 固化） + B11（放射组学可复现文档）
        ↓
B5（metadata_mode 消融）          B8（校准 + 拒答，可并行）
        ↓
（后续）B3 路由消融框架 → B4 组件表跑数
```

---

## B6　路由器透明性与可复现性

### 目的

- 满足 R2.9：公开 prompt、LLM 版本与解码参数，证明「可审计」而非黑箱自述。
- 为 B5 多配置重跑、稳定性实验提供统一日志格式。

### 代码计划（概要）

| 项 | 内容 |
|----|------|
| 配置 | `pipeline.log_routing`、`pipeline.routing_log_path`（默认与 `output_dir` 同目录 `routing_log.jsonl`） |
| Agent | `segmentation/agent.py`、`classification/agent.py`：LLM 调用前后写入结构化记录；静态路径也记「未调 LLM」及规则理由 |
| Pipeline | `pipeline/cascade.py`：Phase 3/5 传递 `image_name`、`path`、`classification_consensus`、`metadata_mode` |
| 可选 | `shared/llm_client.py` 记录请求摘要；`scripts/export_prompt_templates.py` 导出 Supp. 用模板 |
| 稳定性 | `run_routing_stability.py`：仅在分歧子集（`classification_consensus=false` 且 agent 开启）上每例 5 次路由 |

### 日志字段（最小集）

`image_name`, `task`（seg/cls）, `path`, `classification_consensus`, `metadata_mode`, `candidates_summary[]`, `selected_model`, `reasoning`, `llm_model`, `parse_ok`, `true_label`（若有）

### 预期输出

| 交付物 | 形态 |
|--------|------|
| Supplementary Note | 完整 system/user prompt、双 LLM 名、temperature/max_tokens、JSON 输出约定 |
| 补充表 | 稳定性：一致率 + 按「候选质量接近程度」分层（`disagreement_tier`） |
| 补充表 | 10–12 条匿名化结构化路由记录（含错例/摇摆例） |
| 仓库产物 | `output/.../routing_log.jsonl`；`docs/supplementary/prompts/`（可选） |

---

## B5　路由元数据消融

### 目的

- 回答 R3.2：路由依赖病例质量信号，还是依赖设备/数据来源等元数据（中心偏好）。

### 代码计划（概要）

| 项 | 内容 |
|----|------|
| 配置 | `segmentation.agent.metadata_mode`、`classification.agent.metadata_mode`：`full` \| `drop_device` \| `drop_source` \| `drop_both` \| `quality_only` |
| Agent | 按 mode 屏蔽 prompt 中的设备行、`input_data_info`、专家 `dataset_info` / 训练设备描述；`quality_only` 仅保留质量与分歧指标 |
| Pipeline | 输出目录按 mode 区分（如 `output/ablation/drop_device/`）；复用 `intermediate/seg`、`intermediate/cls`，只重跑 Phase 3/5（`enable_agent=true`） |
| 分析 | `pipeline/analyze_routing_bias.py`：`full` 模式下中心/dataset × `selected_model` 频数 → 熵或互信息，供热图 |

### 预期输出

| 交付物 | 形态 |
|--------|------|
| 补充表 | 5 种 metadata 配置 × 各测试集：Dice / AUROC（+ 与 `evaluate.py` 一致的 CI） |
| 关键数 | `full → quality_only` 的 ΔDice、ΔAUROC；中心–专家互信息（或等价统计） |
| 补充图 | 中心 × 专家选择热图（数据来自日志或 results 汇总） |
| 回复草稿要点 | NHC 等未见中心子集是否仍稳健（若有 per-centre 字段） |

---

## B8　校准与拒答

### 目的

- R1.3 / R1.6：报告概率是否校准；定义何时送人工复核（不改模型权重，仅后处理）。

### 代码计划（概要）

| 项 | 内容 |
|----|------|
| 新模块 | `pipeline/calibration.py`：ECE、Brier、可靠性图数据 |
| 新模块 | `pipeline/abstention.py`：规则引擎 + 验证集定阈 + risk–coverage |
| 配置 | `abstention.rules`、`abstention.combination`（any/k-of-n）、`abstention.val_results` 路径 |
| Pipeline | Phase 5 在 `results.json` 中写入拒答所需标量（如 `vote_entropy`, `margin_top2`, 分割分歧指标）；缺失则从当次 `indie_preds` / `seg_decision` 计算 |
| CLI | `run_calibration.py` 或在 `evaluate` 后调用：读 `results.json` → `calibration.json`、`figures/` |

### 拒答输入（沿用现有信号）

- 分类：`num_models_same_class`、`vote_entropy`、`margin_top2`、`final_confidence`
- 分割：专家间 IoU/HD95、`area_cv` 等（与返修文档一致）
- 阈值：**仅验证集**拟合，测试集只评估

### 预期输出

| 交付物 | 形态 |
|--------|------|
| 图 | 可靠性图（分队列；可选最差中心） |
| 图 | Risk–coverage 曲线（分类为主） |
| 补充表 | 各队列/中心 ECE、Brier、默认工作点拒答率与保留子集性能 |
| 仓库产物 | `abstention_thresholds.json`（供临床 F4 复核复用） |
| Methods 一句 | 明确未在测试集调阈、未重训模型 |

---

## B11　放射组学可复现性（R2.21；连通域不在本仓库范围内）

### 范围说明

- **本计划不实现、不扩展连通域（connected-component）后处理。** 当前 Cascade 中 `radiomics_judge/feature_extractor.py` 对 router 选定的 mask 直接提特征，与旧稿 Methods 中「radiomics 前连通域精修」表述不一致。
- **R2.20（连通域）**：在 **论文返修稿 + 回复信** 中处理——删除或更正该句，写明 radiomics 使用 **selected mask**、主文 Dice/HD95 基于 **路由选中的分割 mask**（与 `pipeline/evaluate.py` 一致）；**不在 ThyroidCascadeAgent 为本项新增 CCA 代码**。
- **本仓库 B11 仅覆盖 R2.21** 及与 radiomics 管线相关的可复现材料。

### 目的

- R2.21：PyRadiomics / AutoGluon 版本与关键超参可复现；训练数据与特征配置与推理侧一致。

### 代码 / 文档计划（概要）

| 项 | 内容 |
|----|------|
| 文档 | 新增 `docs/reproducibility_radiomics.md`：PyRadiomics 版本、`radiomics_judge/radiomics_2d.yaml` 要点（归一化、bin、滤波器、shape2D 等）；AutoGluon `model_dir`、训练队列说明（GT mask 训练）、推理入口（`RadiomicsJudge` / Phase 4） |
| 配置 | 确保 `config/*.yaml` 中 `radiomics_judge` 段路径明确；必要时在 README 链到上述文档 |
| 一致性核对 | 确认 `feature_extractor.py` 与训练侧 `extract_radiomics_2d` 约定一致（灰度、spacing、yaml）——已有注释，文档中复述即可 |
| 可选 | `requirements.txt` 中注明 `pyradiomics`、`autogluon` 版本区间或锁定版本（若团队有固定环境） |

### 预期输出

| 交付物 | 形态 |
|--------|------|
| Methods / Supp. | 放射组学分支数据流一句：**selected mask → PyRadiomics → AutoGluon**（无额外 CCA） |
| Supp. Note | 参数表 + 仓库内 yaml / 模型目录说明 |
| 回复 R2.20 | 更正稿面表述，说明实现与修订后 Methods 一致（**非**「忽略审稿人」） |
| 仓库 | `docs/reproducibility_radiomics.md`；config 与 `radiomics_2d.yaml` 可点击复现 |

---

## 验收 checklist（四项完成标准）

- [ ] **B6**：外人仅凭 Supp. + 本仓库 config 可复现 prompt；`routing_log.jsonl` 可对照输入与 `reasoning`
- [ ] **B5**：五种 `metadata_mode` 各有一套 `metrics`；Δ 与互信息可填回复 R3.2
- [ ] **B8**：阈值来源仅为验证集；图 + 表 + `abstention_thresholds.json` 齐全
- [ ] **B11**：`reproducibility_radiomics.md` 齐全；稿面已去掉/更正连通域句并与本仓库行为一致

---

## 工作量粗估（仅实现，不含全队列实验）

| 任务 | 代码体感 | 说明 |
|------|----------|------|
| B11 | 很小 | 文档 + 配置引用；无连通域工程 |
| B5 | 小 | Prompt 分支 + 分目录重跑 |
| B6 | 小～中 | 日志 + 稳定性脚本 |
| B8 | 中 | 新子模块 + 补 results 字段 |

合计约 **3～7 个工作日**（熟悉本仓库）；全量 API 稳定性与多 config 重跑另计。

---

*文档版本：与返修计划自我理解（B5/B6/B8/B11 节）及 ThyroidCascadeAgent 现有五阶段 pipeline 对齐；B11 连通域按稿面更正处理，不纳入本仓库增量。*
