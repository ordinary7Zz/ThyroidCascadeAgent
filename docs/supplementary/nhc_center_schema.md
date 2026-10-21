# NHC 中心 manifest 字段约定

用于 B7/B8 的 `center_id` join，任选其一：

## CSV（推荐）

| 列名 | 必填 | 说明 |
|------|------|------|
| `stem` 或 `image_name` | 是 | 与 `results.json` 的 `image_name` stem 一致 |
| `center_id` 或 `centre_id` | 是 | 如 `THYB_S_ZJ24` |

配置：`pipeline.revision.center_manifest: /path/to/nhc_center_index.csv`

## labels.json

列表项或 dict 值中可含：`center_id` / `centre_id` / `site_id` / `hospital_id`。  
未配置 manifest 时，`backfill_results_metadata.py` 与 `build_nhc_center_table.py` 会尝试从 `--label-file` 解析。
