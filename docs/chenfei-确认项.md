R2.4：
[英文原文]:
ZJH-8K and TN3K were both collected at Zhujiang Hospital, Southern Medical University. Unless they are demonstrably independent in patient population, collection period, cohort composition, and clinical workflow, ZJH-8K should not be described as an external-centre cohort.

[中文翻译]:
ZJH-8K 与 TN3K 都采集自南方医科大学珠江医院。除非能证明它们在患者人群、采集时段、队列构成与临床流程上确实独立，否则 ZJH-8K 不应被描述为外部中心队列。

[大概解释]:
审稿人认为：**TN3K（公开训练集之一）和 ZJH-8K（稿里外测）都在珠江医院采的**，若实际上是同一批病人、同一时段、同一套流程，就不该把 ZJH-8K 写成「独立外部中心」验证。

需要陈飞老师（或熟悉两库立项的同事）用**临床/队列事实**写进 Methods 的，是「两库到底有多独立」——请尽量按下面回答（可简短）：

**1. 患者是否重叠？** TN3K 与 ZJH-8K 的 patient ID / 住院号 / 检查号能否对账？是否已知**同一患者同时出现在 TN3K 与 ZJH**（哪怕图像文件名不同）？若从未系统对账，请说明「未做 ID 级去重，仅做了图像级 dHash 去重」是否可写进稿。

**2. 采集时段是否分开？** 两库大致的**入组年月范围**（如 TN3K 201x–201y，ZJH-8K 201a–201b）是否重叠、ZJH 是否主要是**更晚**的一轮专病收集或回顾性库？

**3. 队列构成有何不同？** 除 TN3K 偏结节检测公开 benchmark、ZJH 规模更大/含更多恶性等稿面已有描述外，是否有**明确的纳入排除差**（如 ZJH 只要手术病理确认、TN3K 含细胞学不确定例等）可写一句？

**4. 临床/成像流程是否同一？** 同一时期珠江医院甲状腺超声**是否同一套设备与扫查规范**；两库是否来自**同一 PACS/同一科室项目**，还是不同子课题、不同标注项目？

R2.5：
[英文原文]:
The Methods should specify the reference standards for nodule segmentation and benign-malignant classification, annotation procedures, annotator qualifications and adjudication of disagreements, patient-level deduplication, and handling of missing data.

[大概解释]:

解释 **ZJH-8K数据集**（即此前 excel 里的珠江医院恶性/良性图库，稿里作分割与良恶性**外测**的那批）。请尽量按下面条目给可写进 Methods 的表述（可简短 bullet + 示例即可）：

**1. 良恶性分类——金标准是什么？** 每张图的良性/恶性标签最终依据什么定：**术后病理**、**FNA 细胞学**，还是影像报告 + 病理复核？标签对应的是**整张图上的目标结节**，还是**患者级**一次手术结论再赋给该患者所有图？

**2. 结节分割 mask——谁、怎么勾？** 参考 mask 勾画的是**结节区域**还是其它结构？**几位**超声/放射科医师参与、是否有**年资/职称**可写；是否**双人独立勾画 + 第三人裁决**或 senior 复核；用的是什么工具（如 ITK-SNAP、科室 PACS 自带等）。若只有单人勾画，也请说明。

**3. 标注不一致时怎么处理？** 两人 mask 或良恶性不一致时，最终标签按什么规则定（取 senior、取并集、开会共识等）。


R2.10
[英文原文]:
For FTC/PTC classification, the training cohort comprised classic PTC and follicular-variant PTC, whereas the external test set comprised FTC and PTC. Because follicular-variant PTC is not equivalent to FTC, the target definition differs between training and testing. Unless this is justified as a clinically valid domain-transfer task, the reported performance may not be valid.

[中文翻译]:
对 FTC/PTC 分类，训练队列由经典型 PTC 与滤泡变异型 PTC 组成，而外部测试集由 FTC 与 PTC 组成。由于滤泡变异型 PTC 并不等同于 FTC，训练与测试的目标定义不同。除非将其论证为临床有效的域迁移任务，否则所报告的性能可能无效。

[大概解释]:
审稿人指出：原稿写 ZJH 上按 **「经典型 PTC vs 滤泡变异型（FVPTC）」** 训练，却在 Dai 外测上按 **「PTC vs FTC」** 评估，**FVPTC 不等于 FTC**，标签不一致。

需要确认的是 **ZJH-8K 恶性子集里「FTC/PTC 亚型」字段在数据与病历里真实含义**，避免 Methods 与数据库不一致：

**1. 当前标签到底是哪两类？** 是 **classic PTC vs follicular variant（FVPTC）**，还是病理确认的 **PTC（含各亚型）vs 真正的 FTC**？若 excel/库里有 `FTCPTC` 或类似字段，请说明 **0/1 或类别名各代表什么**。

**2. 纳入规则（病理/病历）。** 一例判为 FTC 或 PTC 时，依据的是**术后病理报告哪一句/哪一版 WHO 或院内规范**？FVPTC、包膜型 PTC 等是否曾计入某一类、有无**重新归类**过？

R2.12
[英文原文]:
For lymph-node metastasis prediction, the manuscript inconsistently refers to overall LNM, lateral LNM, and CN0/CN1 labels. The authors should clarify whether CN denotes central-compartment nodal status, whether the target is central, lateral, or any cervical LNM, whether the inputs include primary thyroid lesions, lymph nodes, or both, and how image-level predictions are aggregated at the patient level.

[中文翻译]:
对淋巴结转移预测，稿件不一致地使用总体 LNM、侧颈 LNM 与 CN0/CN1 标签。作者应澄清 CN 是否指中央区淋巴结状态、目标是中央/侧颈/任意颈部 LNM、输入是否包含原发甲状腺病灶与/或淋巴结图像，以及图像层面预测如何在患者层面聚合。

[大概解释]:
审稿人认为稿里 **LNM、侧颈 LNM、CN0/CN1** 混用，且没写清**输入是原发灶还是淋巴结图**、**多图怎么合成患者结论**。

需要确认的是 **ZJH-8K 上 LNM（CN0/CN1）标签与图像类型的临床定义**：

**1. CN0 / CN1 各表示什么？** 是否对应 **中央区淋巴结转移**（如 pN0 vs pN1a）、**侧颈转移**，还是**任意区域淋巴结转移**的汇总？请给**院内或病理报告上的可操作定义**（可引用一句话模板）。

**2. 「CN」是否仅指中央区？** 若病历里还有侧颈清扫/侧颈转移描述，ZJH 的 CN0/CN1 是否**包含侧颈信息**，还是**只看中央区**？原稿「侧颈 LNM」表述是否应一律删除或改成什么用语？

**3. ZJH-8K 用于 LNM 模型的图像是哪种？** 请确认：是否为**甲状腺原发灶超声**（不是单独拍的颈部淋巴结图）？若同一患者有多张原发灶图，是否**共用同一 LNM 标签**（病例级病理结论）？

**4. （可选）与字段对应。** excel/库中 LNM 相关列（如 `LNM_CN01`）与上述定义的对应关系。