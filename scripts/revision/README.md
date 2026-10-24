# `scripts/revision/` — 返修脚本（B1–B12）

返修实验脚本 **仅在本目录**（`b1`–`b11`）。级联地基 CLI 在 [`../README.md`](../README.md)。

- **总索引**：[`../README_REVISION.md`](../README_REVISION.md)
- **可复制命令**：[`../../docs/RUN_REVISION_COMMANDS.md`](../../docs/RUN_REVISION_COMMANDS.md)
- **Python 引导**：各 `*.py` 顶部 `__revision_bootstrap()` → [`_path_setup.py`](_path_setup.py)
- **Shell 仓库根**：各 `*.sh` 内 `_find_revision_repo_root()`（查找 `run_pipeline.py`）

## 目录

```text
revision/
├── b1/ … b11/       # 与返修工作包一一对应
├── b3/zjh/          # ZJH-8K 大队列 B3 运维（chunk / OOM）
├── b3/rjh/          # RJH-7K 大队列 B3 运维（chunk 重推 + B3）
├── _path_setup.py
├── _repo_root.sh
└── README.md
```

## 新增脚本请放这里

1. 放入对应 `b*/` 子目录  
2. Python：复制任意现有文件的 `__revision_bootstrap()` 块  
3. Shell：复制 `_find_revision_repo_root` 片段  
4. 在 `../README_REVISION.md` 登记
