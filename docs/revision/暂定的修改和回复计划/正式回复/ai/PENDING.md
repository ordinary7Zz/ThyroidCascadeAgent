# 待 AI 处理的修改（用户维护）

新对话请 AI 读 `INSTRUCTIONS.md` + 本文件。完成后由 AI 将条目移到 `HISTORY.md` 并从这里删除或勾选。

---

## 待办

- [x] **R2.9 / `tab_routing_stability`**：多队列分割+分类 LLM 路由稳定性已填入（B6 `stability_summary`）
- [ ] **R2.5 / F5**：与合作者确认后写 Methods + 各队列缺失/无效标注补充表；回信 `\rpending` 整块替换（见 `docs/需要确认.md` R2.5 行）
- [ ] **R1.3 / R2.6**：NHC 全量 35 中心 + scanner/case-mix 关联分析（正文 `\rpending`）
- [ ] **R2.10 / R2.12**：LNM/FTC 临床定义书面确认（`\rpending`）
- [ ] **R3.2 专家占比**：手改 `latex/generated/expert_selection_tables_{zh,en}.tex`
- [ ] **R3.3**：绘制 **患者—检查—图像/视频—病灶—任务** 层级流程图（与 `fig_image_dataflow` 数据划分图分开）；入信后注册 `\responsefigureref`、替换正文红色 `\rpending`
- [ ] **`tab_malig_ext`**：RepViT–Gemini 等通用基线——全开发集训练 → LymphUs Center 2（LNM）与 Dai 等（FTC/PTC）外测；替换表中红色 `\rpending` / `\rpendingzh` 单元格；表注删 `\rpending{… baseline…}` 占位；同步正文 R2.7 与投稿 Table S5a（若扩基线）
