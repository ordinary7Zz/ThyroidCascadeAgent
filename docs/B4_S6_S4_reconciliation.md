# B4：Table S6 与 S4 对账（草稿）

> 状态：**占位模板**。定稿前须填入实测数字与结论类型（A/B/C，见 `REVISION_B3_B4_PLAN.md` §5.2）。

## 待核实现象

| 指标 | S6 单专家（范围/代表值） | S4 ThyroidXAgent | 备注 |
|------|--------------------------|------------------|------|
| ZJH-8K cls AUROC | （填） | （填） | |
| ZJH-8K seg Dice | （填） | （填） | |

## 协议核对清单

- [ ] 训练数据累加方式（堆叠 vs 单数据集）与表注一致  
- [ ] 评测划分、标签键、mask 来源（路由输出 vs 单专家直连）  
- [ ] S6 与 S4 是否同一测试集、同一预处理  

## 结论类型（择一）

- **A 类**：表注/协议错误 → 更正 S6 caption，统一数字  
- **B 类**：协议正确，全系统路由劣于单专家 → Results 如实写；同时报告 **L1 全图 cls** 与 **L3 全图 + Path B**  
- **C 类**：疑似泄漏/重叠 → 与 B1 联动  

## 与本仓库产物

- L3 / S4 校验：`output/ablation/b4/<ds>/` 下 `b4_component_table.csv` 的 `L3`、`S4_check` 行  
- B3 策略 7：`output/ablation/b3/<ds>/llm/b3_metrics.json`  
