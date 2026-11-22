# 正式回复 LaTeX 预览（内网）

**以 TeX 为唯一编辑源**。编译并预览两个 Overleaf 工程：

| 工作区 | 目录 | 主文件 | 引擎 |
|--------|------|--------|------|
| 审稿回复 | `../response_letter/` | `main.tex` | pdfLaTeX |
| Nature 主稿 | `../26_Nature_ThyroidAgent/` | `main_v2.tex` | XeLaTeX + BibTeX |

不再编译或维护 `latex/` 下的旧 EN/ZH 分轨回信。

## 编辑哪里（回信）

| 文件 | 作用 |
|------|------|
| `../response_letter/generated/body_en_merged.tex` | 合并后的英文回复正文 |
| `../response_letter/generated/*.tex` | 表图、附录片段 |
| `../response_letter/main.tex` | 导言区、`\input` |
| `../response_letter/reviewer_response.sty` | 版式、表格环境 |

## 依赖

- Python 3 + Flask
- `pdflatex`（回信）、`xelatex` + `bibtex`（主稿）；`texlive-latex-extra` 等

## 用法

```bash
cd latex-viewer
python3 app.py
# 默认 http://0.0.0.0:8765
```

浏览器：左侧文件树 → 中间 TeX 编辑（Ctrl+S 保存）→ 右侧 PDF。顶栏在 **审稿回复** / **Nature 主稿** 间切换。

保存后约每 3 秒自动重编，也可点「编译」。

## 手动编译（不用网页）

```bash
cd latex-viewer
bash compile_response.sh    # ../response_letter/main.pdf
bash compile_manuscript.sh  # ../26_Nature_ThyroidAgent/main_v2.pdf
```

## `app.py` 行为

`full_build()`：**回信** pdfLaTeX ×3（`response_letter/`）；**主稿** XeLaTeX → BibTeX → XeLaTeX ×2（若目录存在）。`TEXINPUTS` 含各工程根目录及 `response_letter/figures/`。

### 主稿与 Overleaf 一致（不改 `main_v2.tex`）

`wlscirep` 先加载无 `table` 的 `xcolor`，稿中再 `\usepackage[table]{xcolor}` 时，本地 XeLaTeX 易出现 **Option clash**，`\rowcolor` 失效（表头出现字面 `gray!20`）。Overleaf 环境往往仍能正常出表。

本地编译只做两件事（均在 `latex-viewer/`，不改正稿）：

1. **`manuscript-overlay/wlscirep.cls`** 通过 `TEXINPUTS` 优先于工程内同名类，将 `xcolor` 以 `[table]` 加载。
2. **`main_v2._local_build.tex`** 自动生成：删去稿内两行重复 `\usepackage{xcolor}`，用 `-jobname=main_v2` 输出仍是 `main_v2.pdf`。

`main_v2.tex` / 工程内 `wlscirep.cls` 与 Overleaf 保持一致即可；overlay 与 wrap 勿上传 Overleaf。