# NHC-MISD-TUS：对话梳理 — 代码构建、回复稿件与修改历史

**整理日期**：2026-10-28  
**范围**：本对话线程中与 **NHC 私有队列**相关的政策、示例流水线、正式回复 LaTeX 及规划文档变更。  
**全量数据**：本机仅有 **10 图 / 2 中心** 示例子集；目标 **35 中心、8721 张测试图** 待数据与 **G3** 元数据就绪后整表替换。

---

## 1. 审稿条目与分工（NHC 相关）

| 审稿意见 | 内容要点 | 负责包 | 回信位置 |
|----------|----------|--------|----------|
| **R2.6** | 35 中心定义、描述表、中心级性能、$I^2$/τ² | **B7** | R2.6；表 **R18–R20** |
| **R1.3**（异质性） | 承认中心差异、个案中心；与 R2.6 交叉引用 | **B7** + **B8** | R1.3 异质性段 → R2.6；**校准/送复核/ECE** → B8、`tab_calib_referral` |
| **R2.3 / R3.3** | 「28,458 test cases」混用图像与 NHC 计数 | **B12 / G2** | 数据流图；NHC **8721** 与 OpenThyroid **19,737** 图分层叙述 |
| **R3.1 / R3.2** | 八策略主表、元数据消融 | **B3 / B5** | NHC：**策略 7 N/A**；**无 B5**（无 LLM） |
| **R2.9** | LLM 5× 稳定性 | **B6** | **NHC 不列入**表 R9 |
| **R2.8** | 组件消融 L1–L3 | **B4** | NHC：**L1/L2 可报**；**L3 N/A** |

**B7 不负责**：在 NHC 上 **fit** B8 拒答阈值（阈值仅 OpenThyroid validation，`output/b8/fit/abstention_thresholds.json`）。

---

## 2. 托管政策（写进回复与 Methods 的硬约束）

来源：`docs/revision/nhc_sample/MODEL_POLICY_ZH.md`、`MANUSCRIPT_REVISION_PLAN_ZH.md` §17。

| 禁止 | 允许 |
|------|------|
| 任何 **LLM API**（闭源 + Qwen/DashScope 等开源在线路由） | **本地 DINO 专家** + **非 LLM** 级联（`enable_agent: false`） |
| **B3 策略 7**、**B4 L3**、B5 元数据消融 / 中心×专家热图 | **B3 策略 1–5、8** + **策略 6 仅推理**（joblib 来自开发队列，**不在 NHC fit**） |
| **B8 在 NHC 上定阈** | **B8 在 NHC 上 eval**（应用冻结阈值） |
| **B6** 在 NHC 上重复 LLM 路由 | **九模型** `my_Thyroid_Infer` 本地 infer（稿面 S7–S12 对比列） |

回复用语：**「不适用（N/A）」**，**不是**「待补实验」留空。

---

## 3. 代码与配置构建（示例子集 `nhc_prepared_sample`）

### 3.1 路径索引（真源）

| 用途 | 路径 |
|------|------|
| 配置/manifest 索引 | `config/revision/nhc_sample/manifest.yaml` |
| 逐步命令 | `docs/revision/nhc_sample/README.md` |
| 模型政策 | `docs/revision/nhc_sample/MODEL_POLICY_ZH.md` |
| GPU / 权重 | `docs/revision/b7/NHC_GPU_AND_WEIGHTS_ZH.md` |

### 3.2 B7 专有代码

| 层 | 路径 |
|----|------|
| Pipeline | `pipeline/revision/b7/` — `nhc_prepare_data.py`、`nhc_stem.py`、`nhc_heterogeneity.py`、`nhc_config.py` |
| Scripts | `scripts/revision/b7/` — `run_nhc_prepare.py`、`run_b7_analysis.py`、`build_nhc_center_table.py`、`run_b7_nhc.sh`、`run_b7_sample_canonical.sh`、`run_nhc_cascade_sample.sh` |
| 测试 | `tests/revision/test_b7_nhc_stem.py` |

共享：`scripts/revision/b8/backfill_results_metadata.py`（补 `center_id`）、`docs/supplementary/nhc_center_schema.md`。

### 3.3 示例数据与产出目录

| 阶段 | 目录 / 文件 |
|------|-------------|
| 预处理（10 图） | `output/b7/nhc_prepared_smoke/` — `labels.json`、`center_manifest.json`、`center_stats.json` |
| Cascade（无 LLM） | `output/b7/nhc_cascade_sample/` — `results.json`、`intermediate/` |
| B7 汇总（canonical） | `output/b7/nhc_sample_canonical/` — `b7_report.json`、`csv/nhc_center_*.csv` |
| B3 | `output/ablation/b3/nhc_prepared_sample/`（含 `learned/`） |
| B4 L1 | `output/ablation/b4/l1/nhc_prepared_sample/run1/`、`artifacts/b4_l1_nhc_prepared_sample.json` |
| B8 eval | `output/b8/nhc_prepared_sample/eval_formal/` |
| B2 | `output/b2/nhc_prepared_sample/` |
| 九模型 infer | `my_Thyroid_Infer/results/nhc_prepared_sample/` |

**一键示例（推荐验表结构）**：

```bash
conda activate .../thyroid_infer
bash scripts/revision/b7/run_b7_sample_canonical.sh
```

`FORCE_REFRESH=1` 默认会清 `intermediate`，避免旧 `max_images` 缓存与当前 10 图不一致。

### 3.4 跨任务 yaml 清单

| 任务 | 配置 |
|------|------|
| Cascade 主跑 | `config/revision/nhc_prepared_sample.yaml` |
| B3 静态 + learned | `config/revision/b3/nhc_prepared_sample.yaml` |
| B4 L1 | `config/revision/b4/l1/nhc_prepared_sample.yaml` |
| B4 汇总表 | `config/revision/b4/nhc_prepared_sample.yaml` |
| B8 eval | `config/revision/b8/nhc_prepared_sample.yaml` |
| B2 簇 CI | `config/revision/b2/nhc_prepared_sample.yaml` |
| 九模型 | `config/revision/infer/nhc_prepared_sample.yaml` |
| 全量拟用（无 LLM） | `config/revision/nhc_no_llm_primary.yaml` |

**learned 路由**：`nhc_prepared_sample` 的 b3 yaml 中 `learned_router` 指向 **TN5K 等开发队列** 已拟合 `*.joblib`（`allow_missing_artifact` 等），**禁止**在 NHC 上 `fit_learned_router`。

**B8 注意**：eval 使用 `abstention_thresholds.json`（非 `thresholds.json`）；`--rule-subset nhc`。

---

## 4. 示例子集已填入的数字（暂行，*n*=10）

用于回信 **R18–R20** 与 `body_*.tex` R1.3 / R2.6；**全量定稿后整表替换**。

| 指标 | 示例值 | 备注 |
|------|--------|------|
| 中心 | THYB_S_AH04 (*n*=2)、THYB_S_AN01 (*n*=8) | G3：患者数/扫描仪/医院 **待 merge** |
| 池化结节 Dice | **93.4%**（95% CI 89.8–96.2） | Cascade 非 LLM |
| 分类 AUROC | **0.813**（CI 宽） | *n*=10 |
| 中心 Dice | AH04 **83.3%**，AN01 **96.0%** | macro ≈ **89.6%** |
| 结节 Dice $I^2$ | **≈98.5%**（τ²≈0.025） | 2 中心 |
| 分类 score $I^2$ | **≈39.0%** | 2 中心 |
| B8 送复核 | **0/10** | 冻结 validation 阈值 |
| B8 ECE / Brier | **≈0.234 / ≈0.160** | *n* 过小，仅流程核对 |
| 全腺体 Dice | **勿发表** | 示例曾用 GT 占位；需真实腺体预测后替换 |

与投稿 Fig.2h / Supp. 池化数（如结节 82.31%、AUROC 0.819）**待全量对账**（`\rpending`）。

---

## 5. 正式回复 LaTeX 修改历史（本对话相关）

**根目录**：`docs/revision/暂定的修改和回复计划/正式回复/latex/`

### 5.1 表编号（以 registry 为准）

| LaTeX label | 回信编号 | 文件 |
|-------------|----------|------|
| `tab_nhc_center_descriptive` | **R18** | `generated/nhc_b7_tables_zh.tex` / `_en.tex` |
| `tab_nhc_center_performance` | **R19** | 同上 |
| `tab_nhc_heterogeneity` | **R20** | 同上 |

> 旧稿 `B7_NHC_SCOPE_SUMMARY_ZH.md` 曾写 R19–R21；**统稿后以 `response_asset_registry.tex` 的 R18–R20 为准**。`MANUSCRIPT_REVISION_PLAN` §17 标题仍写 R19–R21 时，编译与回信以 registry 为准。

### 5.2 正文修改要点（`generated/body_zh.tex` / `body_en.tex`）

1. **R1.2 / 策略总述**：NHC **不**进八策略 LLM 子表；报告非 LLM 级联 + 静态 + **策略 6 推理**。
2. **R1.3**：NHC 校准用 **同一冻结 validation 阈值**；示例 0/10 送复核、ECE/Brier；异质性交叉 R2.6。
3. **R2.6**：队列 35 中心 / 8721 图叙述；暂行 10 图 2 中心表；**策略 7 / L3 / B5 on NHC = N/A**。
4. **R2.9 / R3.2**：NHC **排除** LLM 稳定性（R9）与 TN5K 元数据表范围说明。
5. **R3.2**：性能消融改为 **TN5K 测试集**（去掉内部子集名、仓库路径）。
6. **审稿人可见措辞**：`latex/README.md` — 回信**不得**出现仓库路径、脚本名、`enable_agent`、`abstention_thresholds.json` 文件名、内部 subset 名等（部分 NHC 表注仍用 `\rpendingzh{…}` 占位院方字段）。

### 5.3 编译与已知问题

- 编译：`xelatex REVIEWER_RESPONSE_ZH.tex`（两遍）。
- `nhc_b7_tables_zh.tex` 曾出现 `\textbf{\rpendingzh{…}}` 嵌套导致 **`Extra }`**；应改为表格外层 `\rpendingzh` 或纯文本表注。
- NHC 表内数字为 **暂行子集真值**；全量替换前保留红色 `\rpending` 标记。

---

## 6. 规划文档同步（非 LaTeX）

| 文档 | NHC 相关更新 |
|------|----------------|
| `docs/revision/暂定的修改和回复计划/MANUSCRIPT_REVISION_PLAN_ZH.md` | **§17 B7** — 政策、示例数字、B3/B4/B5/B8 交叉、checklist |
| `docs/revision/暂定的修改和回复计划/REVIEWER_RESPONSE_PLAN_ZH.md` | B7 专项、与 B8 分条 |
| `docs/revision/暂定的修改和回复计划/README.md` | 归档表 B7 状态 |
| `docs/revision/nhc_sample/README.md` | B3/B4/B8/B2/infer 示例命令 |

---

## 7. 本对话中的工程决策（便于后续接手）

1. **示例 vs 全量**：先在 `nhc_prepared_sample` 跑通 **结构 + 回复表**，不在信里写 250/8721 假数；全量 NHC 路径就绪后 **同脚本换目录**，刷新 R18–R20。
2. **B6 与 NHC**：稳定性实验 **不含 NHC**（无 LLM）；勿用 B6 yaml 跑 NHC。
3. **B8**：NHC 只做 **eval**；阈值文件 `output/b8/fit/abstention_thresholds.json`。
4. **腺体指标**：示例 GT 占位 **不得**进稿；B7 canonical 脚本中 `gland_pred_for_b7` 仅为列结构验证。
5. **G3**：扫描仪、医院、患者数、结节数等 — `build_nhc_center_table.py --g3-csv`；表 R18 表注 `\rpending`。
6. **与 B6 对话的边界**：OpenThyroid 队列 B6 改为 10 例 + `stop_after_phase2` **不适用于 NHC**；二者勿混配置。

---

## 8. 全量 NHC 定稿前 checklist

- [ ] 全量 `labels.json` + `center_manifest` / G3 CSV
- [ ] `nhc_no_llm_primary.yaml`（或等价）全队列 `pipeline_run` + `results.json`
- [ ] `run_b7_nhc.sh` → 刷新 `b7_report.json`、CSV、**R18–R20 全部单元格**
- [ ] B3 静态 + learned **推理**、B4 L1/L2、B8 eval_formal（**仍无** 策略 7 / B5）
- [ ] 真实腺体预测 → 更新 R19 腺体行
- [ ] 对账投稿 Fig.2h / S7–S12；去掉 `\rpending` 中与院方相关的占位
- [ ] 回信 `body_*` 中「暂行子集 *n*=10」改为全量叙述或删暂行限定句

---

## 9. 相关文档索引（本目录）

| 文件 | 用途 |
|------|------|
| [B7_NHC_SCOPE_SUMMARY_ZH.md](./B7_NHC_SCOPE_SUMMARY_ZH.md) | 实验/元数据总表、E7-x 清单 |
| [NHC_GPU_AND_WEIGHTS_ZH.md](./NHC_GPU_AND_WEIGHTS_ZH.md) | 环境与权重 |
| [README.md](./README.md) | B7 入口与命令 |
| [../nhc_sample/README.md](../nhc_sample/README.md) | 示例 10 图多任务跑法 |
| [../暂定的修改和回复计划/MANUSCRIPT_REVISION_PLAN_ZH.md](../暂定的修改和回复计划/MANUSCRIPT_REVISION_PLAN_ZH.md) §17 | 拟改稿数字与位置 |
| [../暂定的修改和回复计划/正式回复/latex/README.md](../暂定的修改和回复计划/正式回复/latex/README.md) | 回信 LaTeX 规范 |

---

## 10. 变更日志（对话摘要）

| 日期 | 事项 |
|------|------|
| 2026-10（对话） | 跑通 `nhc_prepared_sample`：B7 canonical、B3 static+learned、B4 L1/tables、B8 formal eval、B2、九模型 infer |
| 2026-10 | 修正 B8 eval 阈值文件名；NHC b3/b8 yaml 对齐 sample |
| 2026-10 | 规划 §17 + nhc_sample README + manifest |
| 2026-10 | LaTeX：R18–R20 表、`body_*` R1.3/R2.6/R3.x NHC 与 TN5K 措辞； scrub 内部路径/术语 |
| 2026-10-28 | 本文档：汇总 NHC 代码构建与回复修改历史（与 B6 多队列稳定性分流说明） |
