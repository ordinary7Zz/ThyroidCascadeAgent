# B5 进度看板

**最后更新**：2026-10-27

> **本机范围**：NHC 为私密数据、不在当前机器；本地 B5 以 **9 个公开/院内可访问 cohort**（不含 `nhc_misd_tus`）为准。NHC 热图与 `full` 跑数由协作方环境完成后并入稿面。

---

## 总览

| 交付项 | 状态 | 说明 |
|--------|------|------|
| 代码骨架（metadata_mode、batch、表、分析） | ✅ | 见 [`B5_BUILD_PLAN_ZH.md`](./B5_BUILD_PLAN_ZH.md) §2.1 |
| B3 波次 2 `llm`（各正式 cohort） | 🟡 | 多数队列尚未全量；阻塞 `full` 复用与 B4 L3 |
| `output/ablation/b5/` 跑数 | 🟡 | **sample** 已试跑（2026-10-15）；正式队列 ⬜ |
| 稿面主表（TN5K × 五 mode） | 🟡 | 回信 **R17–R18** 已定稿；稿面 Supp. 统稿待 |
| 补图 NHC 中心×专家 | ⬜ | 待 NHC labels + `full` routing_log |
| 回复 R3.2 正文 | ✅ | `正式回复/latex/generated/body_*.tex` + **R17**；`\rpending` 标 TN5K/NHC/修订稿 |

---

## 按 cohort（实验勾选，跑后更新）

| cohort | intermediate | B3 llm | B5 5 mode | 备注 |
|--------|:------------:|:------:|:---------:|------|
| sample | ✅ | 🟡 | 🟡 | 4 mode + `_smoke_*`（n=10）；`full` 用 B3 `llm`；见 §sample 验证 |
| tn3k | ✅ | ⬜ | ⬜ | |
| tn5k | ✅ | ⬜ | ✅ | `test_for_llm_malignancy`；四 mode 已跑；**表内 `full` = R13/R14 策略 7**（回信 R17–R18 已定稿；无 `b5/tn5k/full/` 目录） |
| thyroidxl | ✅ | ⬜ | ⬜ | |
| zjh8k | ✅ | ⬜ | ⬜ | |
| rjh7k | ✅ | ⬜ | ⬜ | seg only |
| ddti_cls | ✅ | ⬜ | ⬜ | cls only |
| ddti_seg | ✅ | ⬜ | ⬜ | seg only |
| pktn | ✅ | ⬜ | ⬜ | seg only |
| nhc_misd_tus | — | — | — | **本机不跑**；私密数据，热图待院方环境 |

图例：✅ 已有　🟡 部分/未确认　⬜ 未做

---

## sample 可行性验证（2026-10-15）

路径：`output/ablation/b5/sample/`  
已跑：`drop_device`、`drop_source`、`drop_both`、`quality_only`，以及 `_smoke_drop_device`；各目录含 `results.json`、`b3_metrics.json`、`routing_log.jsonl`（`metadata_mode` 字段正确），`n_total=10`。  
**未**在 `b5/sample/` 下单独存 `full`（设计上复用 `output/ablation/b3/sample/llm`）。  
同 n=10 下 Dice/AUROC 多数 mode 相同，`drop_source` Dice 略低（0.8488 vs 0.8542）——仅说明链路通，**不能**外推元数据效应。  
未记录是否跑过 `build_b5_tables.py` / `analyze_routing_bias` 全链路；单元测见 `tests/test_metadata_prompt.py`。

---

## 下一步（推荐）

1. 推进各 cohort **B3 `llm`**（与 B4 L3 同一波次）。  
2. `sample` → 1 个非 full mode 试跑，核对 `routing_log` 与 prompt。  
3. `run_b5_batch.py --skip-full` 批量四 mode。  
4. 更新本表 + 将关键 Δ 写入回复计划 R3.2 草稿。
