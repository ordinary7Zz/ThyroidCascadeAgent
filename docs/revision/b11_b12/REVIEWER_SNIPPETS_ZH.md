# B11 / B12 回复素材（中文，与当前代码一致）

## R2.21（AutoGluon / PyRadiomics）

感谢审稿人意见。我们已在 Methods 4.3 与补充说明中补充放射组学分支细节。该分支对 **路由器选定的结节 mask** 提取 **二维 PyRadiomics** 特征（配置见代码仓库 `radiomics_judge/radiomics_2d.yaml`：归一化 scale=100、binWidth=25、八类滤波器与 shape2D/GLCM 等），推理实现与训练侧 `extract_radiomics_2d` 一致（pyradiomics **3.1.0**）。特征经 **AutoGluon-Tabular 1.4.0**（`best_quality` 预设，总时限 600 s，**8-fold** bagging，**ROC-AUC** 优化）在 **dataset_3** 上基于 **GT mask** 训练的表格模型（17,774 例）进行推断；部署模型为加权集成（见 `leaderboard.csv`）。**未在测试集上重训或调参**。完整参数表见 `docs/reproducibility_radiomics.md`。

## R2.20（连通域）

感谢审稿人指出后处理描述不清。我们已 **更正 Methods**：**报告的分割 Dice/HD95 与放射组学输入均使用同一 `selected mask`**，**不在 radiomics 前施加额外的连通域精修**（与返修代码一致）。在 **DINO-UNet 专家内部**，概率图以 **0.5** 二值化后保留 **面积 ≥50 像素** 的连通域并做 **5×5** 椭圆闭运算；若使用 **概率集成 mask**，多连通域时 **仅保留面积最大者**。系统按 **单图单 ROI** 处理，**不对同一图像内多个结节逐灶分离**。

关于审稿人 **&lt;5 mm** 举例：公开外测**无可靠逐图 pixel spacing**，回复信表 R11 以 **GT 等价径 &lt;50 px** 为主口径（与 DINO 专家 **≥50 px** 连通域规则同尺度），**不声称**跨队列临床毫米径。（说明性换算：0.1 mm/px 时 50 px ≈ 5 mm。）在 **七队列** 测试集上，**selected mask** 相对 GT 的失败定义为 **空 mask 或 Dice&lt;0.1**（见 `tables/R2_20_SUMMARY.md`）。**外测 ZJH-8K**（*n*=7958）：**N=1001**，**M=44**，子集 mean Dice **0.818**；**TN3K**：N=68，M=2，mean Dice 0.771；**TN5K**：N=103，M=12，mean Dice 0.696；另见 rjh7k、ddti_seg、pktn 等同表（**ThyroidXL** 该子集 N=0）。因 **未对 radiomics 单独做 CCA**，**M** 反映 **分割与路由整体**，而非 radiomics 前连通域删除。

## R2.7 / R2.1（均值）

我们统一规定：正文与摘要中跨 **五个分类测试队列**（Table S4）的「平均」为 **等权宏平均**（不对队列按图像数加权）。核对 Table S4 后，ThyroidXAgent 的更正宏平均为 **AUROC 0.9001**、**AUPRC 0.8705**（原摘要 0.9466 / 0.8361 为笔误）。补充材料同时给出 **按测试图像数加权** 的平均（AUROC **0.9228**、AUPRC **0.9533**）。所有含「mean」的图注已注明定义。

## R1.4（数据流，与 S9 合并）

我们补充了数据流图（Supp. Fig. S[X]）：对分割/分类专家池、AutoGluon radiomics、路由器与（若适用）LLM 裁决，标明 **堆叠训练数据**、**850 张验证集**（专家选择、学习型路由、拒答阈值）与各 **独立测试队列** 的用途；ZJH-8K 在通用测试与 LNM/FTC 任务上的数据复用单独标注。每个操作阈值在图中标明 **验证集拟合** 或 **固定开发超参**。
