# Overleaf 上传（英文审稿回复）

真源目录：**`response_letter/`**（与 [`latex-viewer/README.md`](latex-viewer/README.md) 一致）。

## 建议打包内容

```
response_letter/
  main.tex
  reviewer_response.sty
  report_side.sty
  manuscript_refs.tex
  generated/
    body_en_merged.tex
    response_asset_registry.tex
  seg_cls_side/tables/*.tex
  report_side/tables/*.tex
  report_side/responses/*.tex
  report_side/figures/*.tex
  figures/*.pdf          ← 回信插图
```

- **表 / 图片段**：`seg_cls_side/tables/`（分割·分类·NHC·路由消融等）、`report_side/`（报告侧回复）。
- **勿再上传** `_archive/overleaf_en_bundle/` 或 `_archive/latex_generated/`。

## 编译

- 主文件：`main.tex`
- 引擎：**pdfLaTeX**，建议连续编译 **2 次**（`longtable` 与交叉引用）。

## 宏包

版式集中在 `reviewer_response.sty` 与 `report_side.sty`（含 CJK 的 `\zh{…}` 在 pdfLaTeX 下用 `CJKutf8`）。