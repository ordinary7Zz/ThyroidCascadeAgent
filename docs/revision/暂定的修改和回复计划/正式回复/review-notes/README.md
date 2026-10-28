# 审稿注释与修改历史

与 `latex-viewer` 配合。**只在英文稿上加注释**（English 项目）；中文 PDF/TeX 用于快速理解，不对中文做逐字标注。AI 按 `current.json` 改 **英文** 后，**同步更新** `generated/body_zh.tex` 对应内容。

 **收尾（写 history、清空 current）由你本人完成**；AI 在对话里给出 `entries`，不改 history/current，除非你明确要求。

## 文件

| 文件 | 作用 |
|------|------|
| `current.json` | **当前一轮**待处理注释（viewer 读写） |
| `history.jsonl` | **建议 → 修改** 历史，每行一条 JSON（只追加） |
| `close_review_round.py` | **可选**：你确认改稿后，用 entries 文件一键 append + 清空 |
| `entries.example.json` | entries 格式示例 |

## 推荐流程

1. 在 latex-viewer **English** 项目里对英文 TeX 加注释 → 写入 `current.json`。
2. 在 Cursor 对话 @ `current.json`：请 AI 按注释改 **英文**，并 **同步** `body_zh.tex`；回复里给出 `entries` JSON。
3. 你 **审阅 diff** 后，在 viewer 点 **「写入历史并清空」**（或运行 `close_review_round.py` / 手改 history + 清空 current）。

AI **不应**擅自清空 `current.json` 或改 `history.jsonl`，除非你明确让它只做其中某一步。

## `current.json` 注释条目

```json
{
  "id": "c1709123456789",
  "path": "generated/body_en.tex",
  "range": {
    "start": { "line": 42, "ch": 0 },
    "end": { "line": 44, "ch": 12 }
  },
  "selected_text": "原文快照…",
  "note": "你的修改建议",
  "created_at": "2026-03-28T12:00:00+08:00"
}
```

- `line` / `ch` 均为 **1-based**，与编辑器行号一致。

## `history.jsonl` 每行（一轮）

```json
{
  "schema_version": 1,
  "round_id": "2026-03-28T12:00:00+08:00",
  "closed_at": "2026-03-28T14:30:00+08:00",
  "entries": [
    {
      "comment_id": "c1709123456789",
      "path": "generated/body_en.tex",
      "note": "原注释",
      "action": "applied",
      "summary": "简述实际改动"
    }
  ]
}
```

`action`: `applied` | `skipped` | `partial`

## 手动重置 current（方式 B 第二步）

```json
{
  "schema_version": 1,
  "round_id": null,
  "updated_at": null,
  "comments": []
}
```

对话示例：「请根据 @review-notes/current.json 改英文并同步中文；**不要**动 history 和 current，在回复里给出 entries JSON。」
