# Overleaf 英文回信包说明

## zip 里有什么（仅编译必需）

```
main.tex
reviewer_response.sty    ← 自定义版式宏包（1 个），不是“多余 sty”
generated/*.tex          ← 正文 + 信末分块表
figures/*.png
```

与仓库 `latex/` **不是同一份工程**：`overleaf_en_bundle/` 是**导出快照**（sty 含 pdfLaTeX 分支）；日常编辑仍在 `latex/generated/body_en.tex` 等，再同步进 bundle 打 zip。

## 为什么要有 `.sty`？

回信用了大量自定义命令（`\\authorresponse`、`\\responsetableref`、表图 R 编号、`longtable` 版式等）。这些集中在 **`reviewer_response.sty`**，相当于 Nature 回信专用的“小宏包”。**一个 Overleaf 项目只需要这一个 sty**，没有第二个同类文件。

## 上传

`reviewer_response_en_overleaf.zip` → Main = `main.tex` → Recompile ×2。