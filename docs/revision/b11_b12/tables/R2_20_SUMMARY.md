# R2.20(b) 小结节统计摘要（自动生成）

**生成命令**: `scripts/revision/b11/run_r2_20_small_nodules_all.sh`  
**主口径**: GT 等价直径 **&lt;50 px**（`min_component_px=50`，与 DINO 专家最小连通域规则对齐；**不依赖** DICOM spacing）  
**可选参数**: `MM_PER_PIXEL` / `MAX_DIAMETER_MM` 仅用于 JSON 内 mm 敏感性字段；回复信表 R11 以 **&lt;50 px** 列为准。

**失败定义**: selected mask 为空或 Dice < 0.1（整条分割+路由流水线，非 radiomics 前 CCA）。

| 队列 | n 匹配 | GT 等价径 <50 px (N) | 失败 (M) | 子集 mean Dice | （参考）<5 mm @0.1 mm/px |
|------|--------|----------------------|----------|----------------|-------------------------|
| ddti_seg | 637 | 54 | 1 | 0.734 | 54 |
| pktn | 150 | 15 | 1 | 0.741 | 15 |
| rjh7k | 7288 | 366 | 1 | 0.766 | 366 |
| thyroidxl | 2090 | 0 | 0 | — | 0 |
| tn3k | 614 | 68 | 2 | 0.771 | 68 |
| tn5k | 1000 | 103 | 12 | 0.696 | 103 |
| zjh8k | 7958 | 1001 | 44 | 0.818 | 1001 |

逐队列 JSON：`r2_20_*.json`（含 `selected_masks_npz` 路径，便于核对主结果 config）。
