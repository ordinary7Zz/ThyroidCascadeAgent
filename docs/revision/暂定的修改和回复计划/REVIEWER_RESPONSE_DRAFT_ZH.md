# 审稿意见回复草稿（中文）

手稿：ThyroidXAgent（Nature Communications 大修）。
每条结构：**审稿意见** → **回复** → **支撑图表**（与先前 docx 嵌入内容同源）。

## 暂缓回复

- R1.2、R2.8、R3.1 — 路由与组件消融（补充实验进行中）。
- R1.5–6、R2.13、R2.16–19、R3.4–5 — 报告生成与读者研究（Shiyu / Fei Chen）。
- R2.5 — 参考标准与标注协议。R2.6 — NHC-MISD-TUS 中心级分析。
- R2.15、R2.22–23、R2 代码 — 伦理、语言、TI-RADS、代码发布。
- R3.2 — 路由元数据消融。

---

## 审稿人 1 — 意见 1（R1.1）

**审稿意见：**
分割与分类结果大多以图像层面报告。作者应澄清患者层面与检查层面的划分、跨数据集的去重，以及同一患者的多个帧或视图是否会跨划分出现。患者层面的再分析和聚类感知的置信区间会增强对报告性能的信心。

**回复：**

- 感谢审稿人。我们已按下列方式修订统计报告。
- 独立性与近重复：在 **TN3K、TN5K、ThyroidXL、DDTI、PKTN、ZJH-8K** 等**各来源队列之间**做感知哈希（dHash，Hamming ≤ 5）筛查（见下表）。其中与 R2.4 最相关的是：TN3K（官方 train+val+test）与 ZJH-8K 共 **1156** 对 H=0 图像对；若仅看 TN3K **官方 test** 与 ZJH-8K，则为 **2** 对 H=0。
- 聚类定义：ZJH-8K、ThyroidXL 使用可复现 patient ID；无 ID 队列 **一图一簇**。Bootstrap **1000** 次、**seed=42**，CI 为 cluster-aware。
- 患者级分类：ZJH-8K、ThyroidXL 对图像概率 **簇内/患者内算术平均** 后报告 AUROC/AUPRC。
- 聚类 bootstrap 置信区间：均用 **1000** 次聚类 bootstrap（**seed=42**）重算 **95% CI**。下方嵌入表为修订稿 **Table S4** 的完整版式（**7** 个方法 × **5** 个外测队列，含 AUROC 与 AUPRC 两块），与正文补充表结构一致；**Table S3**（分割）在补充材料中同样更新。**DDTI** 分类外测 **n=349**。

**支撑图表**

#### dHash 跨基础队列近重复筛查（Hamming ≤ 5）

| 队列 A | 队列 B | n (A) | n (B) | 配对数 (H≤5) | H=0 | 仅近重复 (1–5) |
| --- | --- | --- | --- | --- | --- | --- |
| TN3K（官方 train+val+test） | ZJH-8K | 5347 | 7958 | 1333 | 1156 | 177 |
| TN3K（test） | ZJH-8K | 614 | 7958 | 39 | 2 | 37 |

每行均为两个**独立来源队列**之间的 pairwise 筛查（非模型训练池合并口径）。

#### 修订 Table S4 — AUROC

| 方法 | TN3K | ThyroidXL | TN5K | DDTI | ZJH-8K |
| --- | --- | --- | --- | --- | --- |
| ResNet-50 | 0.7681 (0.7276–0.8074) | 0.9029 (0.8845–0.9208) | 0.9321 (0.9132–0.9479) | 0.6155 (0.5334–0.6982) | 0.9125 (0.8965–0.9262) |
| RepViT | 0.8298 (0.7969–0.8598) | 0.9087 (0.8903–0.9269) | 0.8981 (0.8750–0.9194) | 0.7631 (0.6971–0.8244) | 0.8332 (0.8127–0.8549) |
| LSNet | 0.8094 (0.7738–0.8431) | 0.9178 (0.8999–0.9353) | 0.9091 (0.8862–0.9289) | 0.7749 (0.7065–0.8405) | 0.8455 (0.8253–0.8647) |
| UltraFedFM | 0.8474 (0.8137–0.8763) | 0.9231 (0.9062–0.9379) | 0.9277 (0.9087–0.9452) | 0.7819 (0.7095–0.8533) | 0.8718 (0.8536–0.8890) |
| MedSigLIP | 0.8293 (0.7968–0.8618) | 0.9122 (0.8937–0.9279) | 0.9084 (0.8864–0.9284) | 0.7486 (0.6671–0.8302) | 0.8481 (0.8291–0.8654) |
| BiomedCLIP | 0.7539 (0.7139–0.7901) | 0.7765 (0.7474–0.8027) | 0.8043 (0.7727–0.8344) | 0.6440 (0.5691–0.7253) | 0.7342 (0.7110–0.7578) |
| ThyroidXAgent | 0.8511 (0.8183–0.8824) | 0.9312 (0.9142–0.9458) | 0.9475 (0.9316–0.9612) | 0.7937 (0.7107–0.8719) | 0.9374 (0.9277–0.9472) |

#### 修订 Table S4 — AUPRC

| 方法 | TN3K | ThyroidXL | TN5K | DDTI | ZJH-8K |
| --- | --- | --- | --- | --- | --- |
| ResNet-50 | 0.6900 (0.6281–0.7469) | 0.8863 (0.8604–0.9089) | 0.9677 (0.9544–0.9793) | 0.5312 (0.4423–0.6586) | 0.9160 (0.8961–0.9322) |
| RepViT | 0.7518 (0.6946–0.8055) | 0.8851 (0.8553–0.9125) | 0.9525 (0.9340–0.9685) | 0.6133 (0.5149–0.7554) | 0.8790 (0.8569–0.8982) |
| LSNet | 0.7580 (0.7054–0.8065) | 0.9039 (0.8790–0.9284) | 0.9551 (0.9378–0.9703) | 0.6178 (0.5232–0.7696) | 0.8742 (0.8513–0.8944) |
| UltraFedFM | 0.7954 (0.7446–0.8392) | 0.9086 (0.8854–0.9293) | 0.9687 (0.9581–0.9784) | 0.6938 (0.5750–0.8561) | 0.9115 (0.8933–0.9271) |
| MedSigLIP | 0.7403 (0.6788–0.7968) | 0.8899 (0.8624–0.9142) | 0.9596 (0.9470–0.9708) | 0.6302 (0.5195–0.7877) | 0.8804 (0.8566–0.9019) |
| BiomedCLIP | 0.6439 (0.5767–0.7098) | 0.7224 (0.6752–0.7680) | 0.9095 (0.8880–0.9309) | 0.5452 (0.4600–0.6648) | 0.8014 (0.7740–0.8305) |
| ThyroidXAgent | 0.8001 (0.7347–0.8562) | 0.9135 (0.8872–0.9351) | 0.9786 (0.9707–0.9854) | 0.7070 (0.5989–0.8649) | 0.9544 (0.9440–0.9635) |

均为 cluster-bootstrap 95% CI（1000 次，seed 42）。VLM 行版式与投稿稿一致，正式补表将同步更新其 CI。


---

## 审稿人 1 — 意见 3（R1.3）

**审稿意见：**
尽管在私有多中心队列上的总体性能令人鼓舞，但中心层面差异很大。例如，某些中心的结节分割性能低得多。作者应研究其与扫描仪类型、图像质量、病例构成与标注协议的关联，并为低置信病例定义校准、拒答或强制人工复核策略。

**回复：**

- 我们同意中心异质性重要。NHC-MISD-TUS 中心级分析（审稿人 2 意见 6）待中心元数据齐备后单独报告（见对审稿人 2 意见 6 的回复）。此处就五个有良恶性病理标签的外测队列报告校准与送复核策略。
- 在 OpenThyroid **validation** 合并集（**n=875**，与非 LLM 测试协议一致）上，以投票熵、top-2 margin、分割专家最小 pairwise IoU 定义不确定度，各指标取 **95 分位数** 定阈（**不在测试集调参**）。
- 有标签 validation 子集 pooled **ECE≈0.088**、**Brier≈0.078**（见下图表）。
- TN3K、TN5K、ThyroidXL、ZJH-8K、DDTI 外测报告 ECE/Brier、送复核比例及 risk–coverage 曲线（见下方）。四个主要公开外测队列在固定 **validation 95 分位**联合阈下送复核约 **43–48%**；**DDTI** 为 **3.7%**（阈值相同，该队列不确定度分布更集中）。
- 送复核比例较高**不等同于模型失效**：阈值为满足审稿人要求的**保守送复核策略**（投票熵、top-2 margin、分割专家最小 IoU **任一**超阈即送复核，且按 validation **95 分位**固定、不在测试集调参）。risk–coverage 曲线显示随覆盖率降低，**保留子集**上的错误风险下降；我们将其表述为「自动判决 + 强制人工复核」的回顾性工作流，而非追求全覆盖自动部署。送复核病例的临床处置与读者研究边界在 Limitations / 讨论中说明。

**支撑图表**

#### 验证集校准（定阈用 validation 合并集）

| n | ECE | Brier |
| --- | --- | --- |
| 725 | 0.0881 | 0.0777 |


![验证集可靠性图](/mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent/output/b8/fit_q95/reliability_val.png)

#### 外测校准与送复核（验证集 95 分位定阈）

| 队列 | n | ECE | Brier | 送复核% |
| --- | --- | --- | --- | --- |
| TN3K | 614 | 0.1825 | 0.1996 | 48.2% |
| TN5K | 1000 | 0.0661 | 0.0832 | 44.4% |
| ThyroidXL | 2090 | 0.0734 | 0.1101 | 44.9% |
| ZJH-8K | 7958 | 0.0971 | 0.1101 | 43.1% |
| DDTI | 349 | 0.0934 | 0.1098 | 3.7% |


![风险–覆盖率曲线（合图子标题：TN3K、TN5K、ThyroidXL、ZJH-8K、DDTI）](/mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent/output/b8/figures/risk_coverage_panels.png)


---

## 审稿人 1 — 意见 4（R1.4）

**审稿意见：**
ZJH-8K 被描述为分割与良恶性分类的外部测试集，而它的恶性图像又被用于 LNM 与 FTC/PTC 任务的开发。由于任务不同，这也许可以接受，但稿件应提供一张完整的数据流图，说明每个组件分别用了哪些数据做训练、验证、阈值选择与测试。

**回复：**

- 分割与通用良恶性专家 **未在 ZJH-8K 训练**；ZJH 恶性子集仅用于 LNM/FTC 任务开发，外测分别为 LymphUs C2 与 FangDai。图像侧数据流见下方图/表（正式稿拟为补充图 S-X）。

**支撑图表**

图源：[`DATAFLOW_FIGURE.mmd`](/mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent/docs/revision/b11_b12/DATAFLOW_FIGURE.mmd)（导出 PNG 后可替换上图）。
#### 图像侧数据流（文字版）

| 阶段 | 数据 / 阈值 |
| --- | --- |
| 模型开发训练 | TN3K、TN5K、ThyroidXL、PKTN 等公开队列合并（约 1.8 万图）→ DINO-UNet 等专家 |
| 验证集（850 张） | 专家选择、路由、拒答阈值（外测不调参） |
| AutoGluon 放射组学 | dataset_3、GT mask、17,774 训练样本 |
| 通用外测 | TN3K、TN5K、ThyroidXL、DDTI、ZJH-8K、RJH-7K、NHC 等 |
| LNM / FTC-PTC | ZJH 恶性子集 + LymphUs；外测 LymphUs C2 / FangDai |
| ZJH-8K 角色 | 良恶性/分割外测；专家未在 ZJH 训练；恶性子集仅用于 LNM/FTC 开发 |


---

## 审稿人 1 — 总评（可部署性）

**审稿意见：**
该工作有明显优点……然而，当前证据支持的是一条有前景的回顾性工作流，而非已确立的临床获益或广泛可部署性。因此，我建议至少给「大修」。

**回复：**

- 我们已在全稿弱化可部署性表述，强调回顾性评估、修订后的统计报告（数据审计与 cluster-bootstrap 置信区间）及明确局限性；代码可用性见数据与代码可用性声明。

---

## 审稿人 2 — 意见 1（R2.1）

**审稿意见：**
若干关键数值在摘要、正文、图与补充材料之间不一致。

**回复：**

- 我们致歉并已按源结果逐项核对。
- 良恶性分类「均值」（摘要、§2.2）：更正为 Table S4 **五队列等权宏平均** AUROC **0.9001**、AUPRC **0.8705**（见下表）；加权均值 AUROC **0.9228**、AUPRC **0.9533**。
- Fig.3b：AUROC/AUPRC 轴标签标反，已与 Table S5 对齐。
- LNM 训练池更正为 **4936** 图（4756 ZJH 恶性 + 180 LymphUs C1）；五折 CV 合并 manifest **4753** 图（见 Table S5 摘录）。

**支撑图表**

#### 良恶性分类五队列汇总均值（两行：AUROC / AUPRC）

| 指标 | 等权宏平均 | 按测试图像数加权 |
| --- | --- | --- |
| AUROC | 0.9001 | 0.9228 |
| AUPRC | 0.8705 | 0.9533 |

#### Table S5 摘录：ThyroidXAgent LNM / FTC（interim OOF）

| 任务 | 簇数 n | AUROC | 95% CI | AUPRC | 95% CI |
| --- | --- | --- | --- | --- | --- |
| LNM（ThyroidXAgent OOF） | 882 | 0.718 | 0.678–0.754 | 0.598 | 0.536–0.655 |
| FTC/PTC（ThyroidXAgent OOF） | 722 | 0.521 | 0.442–0.602 | 0.109 | 0.076–0.160 |


---

## 审稿人 2 — 意见 2（R2.2）

**审稿意见：**
许多分析以图像层面报告，尽管同一患者、检查或结节可能有多个图像。例如 ZJH-8K 包含来自 1,149 例的 7,958 张图像。把相关图像当作独立观测可能产生过窄的置信区间。作者应使用患者层面或检查层面的 bootstrap 重采样重算置信区间，并对具有临床意义的分类任务报告患者层面性能。

**回复：**

- 我们同意。Tables S3–S5 等 CI 均改为 cluster bootstrap（1000，seed 42）。ZJH-8K、ThyroidXL 在簇/患者内对图像概率取平均后报告患者级 AUROC/AUPRC；ZJH-8K 示例如下表。

**支撑图表**

#### ZJH-8K 分类：图像级 vs 患者级（示例）

| 层级 | n | 分类 AUROC（95% CI，图像级 bootstrap） | 患者级 AUROC |
| --- | --- | --- | --- |
| 图像级 | 7958 | 0.937 (0.928–0.947) | — |
| 患者级 | 1149 例 | — | 0.982 |


---

## 审稿人 2 — 意见 3（R2.3）

**审稿意见：**
请澄清为什么把 28,458 个观测描述为「non-overlapping test cases」，因为这个数字似乎把 19,737 张测试图像与 8,721 个 NHC-MISD-TUS 病例合并在一起。

**回复：**

- 审稿人正确：28,458 = 七个分割/分类队列 **19,737** 张测试图 + NHC **8,721** 例之和；称「cases」不准确且未含报告生成与恶性子任务测试。已改为分层计数，见数据流图/表。

**支撑图表**

图源：[`DATAFLOW_FIGURE.mmd`](/mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent/docs/revision/b11_b12/DATAFLOW_FIGURE.mmd)（导出 PNG 后可替换上图）。
#### 图像侧数据流（文字版）

| 阶段 | 数据 / 阈值 |
| --- | --- |
| 模型开发训练 | TN3K、TN5K、ThyroidXL、PKTN 等公开队列合并（约 1.8 万图）→ DINO-UNet 等专家 |
| 验证集（850 张） | 专家选择、路由、拒答阈值（外测不调参） |
| AutoGluon 放射组学 | dataset_3、GT mask、17,774 训练样本 |
| 通用外测 | TN3K、TN5K、ThyroidXL、DDTI、ZJH-8K、RJH-7K、NHC 等 |
| LNM / FTC-PTC | ZJH 恶性子集 + LymphUs；外测 LymphUs C2 / FangDai |
| ZJH-8K 角色 | 良恶性/分割外测；专家未在 ZJH 训练；恶性子集仅用于 LNM/FTC 开发 |


---

## 审稿人 2 — 意见 4（R2.4）

**审稿意见：**
ZJH-8K 与 TN3K 都采集自南方医科大学珠江医院。除非能证明它们在患者人群、采集时段、队列构成与临床流程上确实独立，否则 ZJH-8K 不应被描述为外部中心队列。

**回复：**

- ZJH-8K 与 TN3K 虽同属珠江医院来源，但队列用途与采集框架不同；我们在修订稿中弱化「外部中心」表述，并报告**各基础队列之间**的 dHash 近重复（与 R1.1 相同口径，见下表）。TN3K（train+val+test）与 ZJH-8K：**1156** 对 H=0；TN3K **官方 test** 与 ZJH-8K 仅 **2** 对 H=0，提示公开 test 子集与 ZJH 几乎无逐像素重复。具备患者 ID 时，患者层面重叠在 Methods / Limitations 中说明。

**支撑图表**

#### dHash 跨基础队列近重复筛查（Hamming ≤ 5）

| 队列 A | 队列 B | n (A) | n (B) | 配对数 (H≤5) | H=0 | 仅近重复 (1–5) |
| --- | --- | --- | --- | --- | --- | --- |
| TN3K（官方 train+val+test） | ZJH-8K | 5347 | 7958 | 1333 | 1156 | 177 |
| TN3K（test） | ZJH-8K | 614 | 7958 | 39 | 2 | 37 |

每行均为两个**独立来源队列**之间的 pairwise 筛查。


---

## 审稿人 2 — 意见 7（R2.7）

**审稿意见：**
作者应澄清所报告的「均值」是跨队列的无权重宏平均、按样本量加权的平均，还是其他计算方式。

**回复：**

- 跨五个 Table S4 外测队列的「均值」均为 **等权宏平均**；更正数字与分队列点估计见下表。

**支撑图表**

#### 良恶性分类五队列汇总均值（两行：AUROC / AUPRC）

| 指标 | 等权宏平均 | 按测试图像数加权 |
| --- | --- | --- |
| AUROC | 0.9001 | 0.9228 |
| AUPRC | 0.8705 | 0.9533 |


---

## 审稿人 2 — 意见 9（R2.9）

**审稿意见：**
稿件称 LLM 路由器通过「推理」选择最佳专家输出，但未报告 prompt 设计、LLM 版本、解码参数、可复现性，以及当候选输出质量相近时的决策稳定性。……作者应提供至少 10 个代表性病例的结构化路由记录……

**回复：**

- 补充材料提供 router 完整规格、结构化 routing_log，并在固定专家输出下对 **10** 例每例 **5** 次重复路由：平均选择一致率 **92%**（8/10 全稳，2/10 为 60%，close 层）。见下表与 router_spec 摘录。

**支撑图表**

#### 路由稳定性（5 次重复）

| 病例 | 分层 | 5 次选择一致率 |
| --- | --- | --- |
| TN3K_test_0002.jpg | close | 100% |
| TN3K_test_0006.jpg | close | 100% |
| TN3K_test_0007.jpg | close | 100% |
| TN3K_test_0009.jpg | close | 80% |
| TN3K_test_0010.jpg | close | 100% |
| TN3K_test_0011.jpg | close | 100% |
| TN3K_test_0019.jpg | close | 100% |
| TN3K_test_0025.jpg | close | 100% |
| TN3K_test_0026.jpg | close | 100% |
| TN3K_test_0031.jpg | close | 100% |

Router 规格：[`router_spec.md`](/mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent/docs/supplementary/router_spec.md)


---

## 审稿人 2 — 意见 10（R2.10）

**审稿意见：**
对 FTC/PTC 分类，训练队列由经典型 PTC 与滤泡变异型 PTC 组成，而外部测试集由 FTC 与 PTC 组成。由于滤泡变异型 PTC 并不等同于 FTC，训练与测试的目标定义不同。……

**回复：**

- 我们承认 FVPTC≠组织学 FTC，将 FangDai 外测表述为 **探索性域迁移**，与主结论区分。
- ThyroidXAgent 内部验证：ZJH **4756** 图、**722** 簇、五折 OOF（下表；interim DINO OOF，全栈融合后可能更新）。FangDai（n=199）ThyroidXAgent 外测将在全开发集重训后更新；组织学 FTC 与训练标签不一致之处在 Limitations 中与临床合作者说明。

**支撑图表**

#### Table S5 摘录：ThyroidXAgent LNM / FTC（interim OOF）

| 任务 | 簇数 n | AUROC | 95% CI | AUPRC | 95% CI |
| --- | --- | --- | --- | --- | --- |
| LNM（ThyroidXAgent OOF） | 882 | 0.718 | 0.678–0.754 | 0.598 | 0.536–0.655 |
| FTC/PTC（ThyroidXAgent OOF） | 722 | 0.521 | 0.442–0.602 | 0.109 | 0.076–0.160 |


---

## 审稿人 2 — 意见 11（R2.11）

**审稿意见：**
LNM 任务只使用了 4,753 张恶性图像，而 Table S5 显示验证只有 20 例……请澄清：(a) 是否使用了迁移学习或多任务学习；(b) 是否做了数据增强；(c) 如何避免过拟合……

**回复：**

- 训练规模更正为 **4936** 图；将 20 例 val 改为 **882** 簇上 **患者级分层五折 OOF**（seed 42），cluster bootstrap 95% CI。Table S5 ThyroidXAgent LNM：AUROC **0.718（0.678–0.754）**，AUPRC **0.598（0.536–0.655）**（下表）。LymphUs C2（n=158）全栈外测将在开发集重训与评估完成后更新 Table S5。

**支撑图表**

#### Table S5 摘录：ThyroidXAgent LNM / FTC（interim OOF）

| 任务 | 簇数 n | AUROC | 95% CI | AUPRC | 95% CI |
| --- | --- | --- | --- | --- | --- |
| LNM（ThyroidXAgent OOF） | 882 | 0.718 | 0.678–0.754 | 0.598 | 0.536–0.655 |
| FTC/PTC（ThyroidXAgent OOF） | 722 | 0.521 | 0.442–0.602 | 0.109 | 0.076–0.160 |


---

## 审稿人 2 — 意见 12（R2.12）

**审稿意见：**
对淋巴结转移预测，稿件不一致地使用总体 LNM、侧颈 LNM 与 CN0/CN1 标签。……

**回复：**

- 我们统一标签键与聚类规则（ZJH：**年/姓名**；LymphUs C1：**一图一簇**）；簇内概率平均与 R2.11 一致。临床定义句待与病理/临床合作者定稿；统计协议见 Table S5。

**支撑图表**

#### Table S5 摘录：ThyroidXAgent LNM / FTC（interim OOF）

| 任务 | 簇数 n | AUROC | 95% CI | AUPRC | 95% CI |
| --- | --- | --- | --- | --- | --- |
| LNM（ThyroidXAgent OOF） | 882 | 0.718 | 0.678–0.754 | 0.598 | 0.536–0.655 |
| FTC/PTC（ThyroidXAgent OOF） | 722 | 0.521 | 0.442–0.602 | 0.109 | 0.076–0.160 |


---

## 审稿人 2 — 意见 14（R2.14）

**审稿意见：**
不清楚所有专家基线是在同一批开发数据上重训、使用原始权重评估，还是零样本测试。……

**回复：**

- 新增补充表 S[X] 记录基线训练与推理协议（下表为摘录）。监督分割/分类基线在 TN3K、TN5K、ThyroidXL、PKTN 等合并开发集上微调；VLM 等单独说明；所列外测队列仅用于 test。

**支撑图表**

#### 基线训练与推理协议（Supp. Table S[X] 摘录）

| model | task | protocol | upstream_pretraining | thyroid_development_set | checkpoint_for_tables | inference_input |
| --- | --- | --- | --- | --- | --- | --- |
| BiomedCLIP | classification | full_finetune_on_stacked_dev | OpenCLIP BiomedCLIP + dataset_3_cls head finetune | OpenThyroid stacked cls development: dataset_3 (TN3K + ThyroidXL + TN5K); train_val_test/Superimposed_multitask/dataset_3_cls/train (ResNet-50 / DINO multitask: dataset_3 with JSON, same image count) | ./infer_biomedclip/checkpoints/BM_2cls/best_model.pth | US image (image_only) |
| LSNet | classification | full_finetune_on_stacked_dev | ImageNet-pretrained LSNet | OpenThyroid stacked cls development: dataset_3 (TN3K + ThyroidXL + TN5K); train_val_test/Superimposed_multitask/dataset_3_cls/train (ResNet-50 / DINO multitask: dataset_3 with JSON, same image count) | ./infer_lsnet/checkpoints/checkpoint_best.pth | US image (image_only) |
| MedSAM2 | segmentation | full_finetune_on_stacked_dev | SAM2.1 Hiera pretrained | OpenThyroid stacked seg development: dataset_4 (TN3K + ThyroidXL + PKTN + TN5K); train under train_val_test/Superimposed_experiment/dataset_4/train | ./infer_medsam2/checkpoints/Nodule/checkpoint_15.pt | US image + GT box/mask for expert (gt_mask) |
| MedSegX | segmentation | full_finetune_on_stacked_dev | SAM ViT-B + MedSegX thyroid adapter | OpenThyroid stacked seg development: dataset_4 (TN3K + ThyroidXL + PKTN + TN5K); train under train_val_test/Superimposed_experiment/dataset_4/train | ./infer_medsegx/checkpoints/Nodule/model_best.pth | US image + GT box/mask for expert (gt_mask) |
| MedSigLIP | classification | full_finetune_on_stacked_dev | Google MedSigLIP + partial finetune on dataset_3_cls | OpenThyroid stacked cls development: dataset_3 (TN3K + ThyroidXL + TN5K); train_val_test/Superimposed_multitask/dataset_3_cls/train (ResNet-50 / DINO multitask: dataset_3 with JSON, same image count) | ./infer_medsiglip/checkpoints/BM_2cls/best_model.pt | US image (image_only) |
| RepViT | classification | full_finetune_on_stacked_dev | ImageNet-pretrained RepViT | OpenThyroid stacked cls development: dataset_3 (TN3K + ThyroidXL + TN5K); train_val_test/Superimposed_multitask/dataset_3_cls/train (ResNet-50 / DINO multitask: dataset_3 with JSON, same image count) | ./infer_repvit/checkpoints/BM/repvit_m1_0_224_0.025_0.001_0.25/checkpoint_best.pth | US image (image_only) |
| ResNet-50 | classification | full_finetune_on_stacked_dev | ImageNet ResNet-50 + dataset_3 finetune | OpenThyroid stacked cls development: dataset_3 (TN3K + ThyroidXL + TN5K); train_val_test/Superimposed_multitask/dataset_3_cls/train (ResNet-50 / DINO multitask: dataset_3 with JSON, same image count) | ./infer_resnet50/checkpoints/resnet50_thyroid_cls_epoch_50.pth | US image (image_only) |
| TransUNet | segmentation | full_finetune_on_stacked_dev | ImageNet-21k ViT-B/16 (TransUNet default) | OpenThyroid stacked seg development: dataset_4 (TN3K + ThyroidXL + PKTN + TN5K); train under train_val_test/Superimposed_experiment/dataset_4/train | ./infer_transunet/checkpoints/Nodule/epoch_49.pth | US image + GT box/mask for expert (gt_mask) |
| … | … | *（其余行见源文件）* |

源文件：[`baseline_training_protocol.md`](/mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent/docs/revision/b10/tables/baseline_training_protocol.md)


---

## 审稿人 2 — 意见 20（R2.20）

**审稿意见：**
后处理中连通域分析的阈值未说明。……(a) 最小连通域面积阈值；(b) 小于 5 mm 的结节是否可能被误删；(c) 分离多个结节的算法。

**回复：**

- Methods 已更正：报告 Dice 与 radiomics **共用 selected mask**；专家内部 ≥**50** 像素连通域、5×5 闭运算；**单图单 ROI**。<5 mm 统计见下表（**mm_per_pixel=0.1** 敏感性假设；M 为整条流水线失败，非 radiomics 前删除）。

**支撑图表**

#### R2.20(b) <5 mm 结节 — 流水线失败统计

| 队列 | n 匹配 | <5.0 mm (N) | 失败 (M) | 小结节子集 mean Dice | GT 等价径 <50 px |
|------|--------|------------------|----------|----------------------|------------------|
| ddti_seg | 637 | 54 | 1 | 0.734 | 54 |
| pktn | 150 | 15 | 1 | 0.741 | 15 |
| rjh7k | 7288 | 366 | 1 | 0.766 | 366 |
| thyroidxl | 2090 | 0 | 0 | — | 0 |
| tn3k | 614 | 68 | 2 | 0.771 | 68 |
| tn5k | 1000 | 103 | 12 | 0.696 | 103 |
| zjh8k | 7958 | 1001 | 44 | 0.818 | 1001 |

源文件：[`R2_20_SUMMARY.md`](/mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent/docs/revision/b11_b12/tables/R2_20_SUMMARY.md)


---

## 审稿人 2 — 意见 21（R2.21）

**审稿意见：**
基于 AutoGluon 的放射组学分支描述不足。

**回复：**

- 已扩充 Methods §4.3 与补充材料中的放射组学规范；要点表与示例外测可靠性图见下方。

**支撑图表**

#### 放射组学分支要点

规范全文：[`reproducibility_radiomics.md`](/mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent/docs/reproducibility_radiomics.md)。

![TN3K 外测可靠性图（示例）](/mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent/output/b8/cohorts_q95/tn3k/reliability_test.png)


---

## 审稿人 3 — 意见 3（R3.3）

**审稿意见：**
「28,458 non-overlapping test cases」的定义不清楚。请清楚描述数据层级，并确认所有训练/验证/测试划分都是患者互斥的。此外，一张展示患者、检查、图像/视频、病灶与任务之间关系的简单流程图会大有帮助。

**回复：**

- 与 R2.3、R1.4 合并回应：见下方数据流与 R1.1 跨队列 dHash 表；「40 datasets」在修订稿中定义或改为明示列表。

**支撑图表**

图源：[`DATAFLOW_FIGURE.mmd`](/mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent/docs/revision/b11_b12/DATAFLOW_FIGURE.mmd)（导出 PNG 后可替换上图）。
#### 图像侧数据流（文字版）

| 阶段 | 数据 / 阈值 |
| --- | --- |
| 模型开发训练 | TN3K、TN5K、ThyroidXL、PKTN 等公开队列合并（约 1.8 万图）→ DINO-UNet 等专家 |
| 验证集（850 张） | 专家选择、路由、拒答阈值（外测不调参） |
| AutoGluon 放射组学 | dataset_3、GT mask、17,774 训练样本 |
| 通用外测 | TN3K、TN5K、ThyroidXL、DDTI、ZJH-8K、RJH-7K、NHC 等 |
| LNM / FTC-PTC | ZJH 恶性子集 + LymphUs；外测 LymphUs C2 / FangDai |
| ZJH-8K 角色 | 良恶性/分割外测；专家未在 ZJH 训练；恶性子集仅用于 LNM/FTC 开发 |

#### dHash 跨基础队列近重复筛查（Hamming ≤ 5）

| 队列 A | 队列 B | n (A) | n (B) | 配对数 (H≤5) | H=0 | 仅近重复 (1–5) |
| --- | --- | --- | --- | --- | --- | --- |
| TN3K（官方 train+val+test） | ZJH-8K | 5347 | 7958 | 1333 | 1156 | 177 |
| TN3K（test） | ZJH-8K | 614 | 7958 | 39 | 2 | 37 |

每行均为两个**独立来源队列**之间的 pairwise 筛查。
