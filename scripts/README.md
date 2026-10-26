# `scripts/` — 级联运行与地基 CLI

与仓库根目录 **`run_pipeline.py`** 配套的外壳脚本（**非** `pipeline/` 库代码）。返修专用批处理见 [`revision/`](revision/README.md) 与 [`README_REVISION.md`](README_REVISION.md)。

| 文件 | 作用 |
|------|------|
| [`repo_path.py`](repo_path.py) | 从 `scripts/*.py` 定位仓库根并加入 `sys.path` |
| [`run_routing_ablation.py`](run_routing_ablation.py) | B3 路由消融：共享 `intermediate` 上重跑 Phase 3–5（实现见 `pipeline/routing_ablation.py`） |
| [`build_test_for_llm.py`](build_test_for_llm.py) | 构建 `test_for_llm_*` 小子集 |
| [`build_all_test_for_llm.sh`](build_all_test_for_llm.sh) | 多队列批量建 for_llm |
| [`README_test_for_llm.md`](README_test_for_llm.md) | for_llm 路径与用法 |
| [`run_pipeline_all_cohorts.sh`](run_pipeline_all_cohorts.sh) | 串行调用根目录 `run_pipeline.py`（各 `config/revision/b3/<id>.yaml`） |
| [`generate_ablation_configs.py`](generate_ablation_configs.py) | 从 `config/revision/b3/sample.yaml` 生成 `revision/b3`、`b4`、`b5`、`b4/l1` |
| [`test_llm_connectivity.py`](test_llm_connectivity.py) | 读 config 测 LLM API |

典型顺序：**for_llm 子集** → **`run_pipeline` / `run_pipeline_all_cohorts.sh`** 写满 intermediate → **`run_routing_ablation` 或 `revision/b3` 批量** 做消融。
