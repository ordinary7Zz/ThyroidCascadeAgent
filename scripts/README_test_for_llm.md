# LLM 专用测试子集（`build_test_for_llm.py`）

## 输出目录命名

- `.../TN3K/test` → `.../TN3K/test_for_llm_<label_key>/`（默认 `test_for_llm_malignancy`）
- `.../DDTI/all_seg` → `.../DDTI/all_seg_for_llm_<label_key>/`

## 分类字段

`--label-key` 指定分层用的 JSON 字段（默认 `malignancy`）。ZJH-8K 等可多任务标签时，分别跑：

```bash
LABEL_KEY=malignancy bash scripts/build_all_test_for_llm.sh
LABEL_KEY=LNM_CN01 python scripts/build_test_for_llm.py --src .../ZJH-8K --n 250 --label-key LNM_CN01 ...
```

## 抽样规则

- 设 `--n 250`：若源测试集 **≤ 250**，**全部复制**（`copied_all: true`），不做随机筛选。
- 若源测试集 **> 250**：分层（有 `--label-key`）或随机抽 **250** 张。

## 批量

```bash
bash scripts/build_all_test_for_llm.sh
# 或
LABEL_KEY=malignancy bash scripts/build_all_test_for_llm.sh
```
