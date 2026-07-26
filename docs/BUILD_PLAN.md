# ThyroidCascadeAgent 构建流程文档

> **执行方式：** 本文档按 Phase 0 → Phase 8 顺序执行，每个 Phase 产出可独立验证的代码。Phase 1-3 为基础层（可独立跑通），Phase 4-5 为待做文档要求的新功能层，Phase 6-8 为集成层。

**目标：** 从零构建一个甲状腺超声级联推理仓库，包含分割筛选 Agent 和分类筛选 Agent，并以 GT-trained radiomics 模型作为分割质量裁判，实现"分割筛选 → 分类筛选"的串联 pipeline。

**架构：** 三层结构——共享层（IO/LLM/数据集信息/模型架构）、分割层（多模型预测 + 形态学/分歧评估 + radiomics 裁判 + LLM 选择）、分类层（多模型预测 + 校准 + soft voting + LLM 选择）。上层 pipeline 串联两阶段：分割 Agent 筛选出的 mask 喂给分类 Agent。

**技术栈：** Python 3.10+、PyTorch、OpenCV、PIL、SimpleITK/pyradiomics、AutoGluon、scipy、OpenAI 兼容 LLM API（Qwen）、PyYAML

**关联仓库：** `git@github.com:ordinary7Zz/ThyroidCascadeAgent.git`

**参考来源：**
- 分割层逻辑：`/Users/wangbd/sysu/Segmentation_Agent/`（完整版，含分歧度量/ensemble/performance_stats）
- 分类层逻辑：`/Users/wangbd/sysu/Classification_Agent/`（完整版，含 calibration/soft_voting/bootstrap CI95）
- radiomics 特征提取：`/Users/wangbd/sysu/pyradiomics_train/extract_radiomics_2d.py`
- radiomics 推理包装器：`/Users/wangbd/sysu/Classification_Agent/models/autogluon_radiomics_model.py`
- 待做需求：`/Users/wangbd/sysu/my_Thyroid_infer/待做.md`

---

## 一、完整文件清单与职责

```
ThyroidCascadeAgent/
├── docs/
│   └── BUILD_PLAN.md              # 本文档
├── requirements.txt
├── README.md
├── run_seg.py                     # 入口：单独跑分割筛选
├── run_cls.py                     # 入口：单独跑分类筛选
├── run_pipeline.py                # 入口：串联分割→分类
├── config/
│   └── config.yaml                # 统一配置
├── shared/                        # 共享层
│   ├── __init__.py
│   ├── image_io.py                # 图像/mask IO（加载/保存），不含模型预处理
│   ├── base_datasets_info.py      # 数据集设备/中心信息 + 设备匹配逻辑（单一来源）
│   ├── llm_client.py              # OpenAI 兼容 LLM 客户端
│   └── model_architectures/       # DINOv3 网络定义
│       ├── __init__.py
│       ├── dino_unet.py           # DINOv3_S_UNet（纯分割）
│       └── dino_unet_multitask.py # DINOv3_S_UNet_MULTITASK（分割+分类多任务）
├── segmentation/                  # 分割层
│   ├── __init__.py
│   ├── base_model.py              # BaseSegmentationModel + SegModelOutput
│   ├── model_registry.py          # SegModelRegistry
│   ├── dino_unet_model.py         # DINOUNetSegmentationModel
│   ├── metrics.py                 # dice/hd95/iou/ece + pairwise_iou + 分歧度量
│   ├── quality_evaluator.py       # 形态学评估（circularity/solidity/smoothness...）
│   ├── performance_stats.py       # 批次 Dice/HD95/ECE 聚合 + bootstrap CI95
│   └── agent.py                   # SegmentationAgent + SegAgentDecision
├── classification/                # 分类层
│   ├── __init__.py
│   ├── base_model.py              # BaseClassificationModel + ClsModelOutput
│   ├── model_registry.py          # ClsModelRegistry（含 calibration）
│   ├── dino_unet_model.py         # DINOUNetModel（多任务分类头）
│   ├── autogluon_radiomics_model.py  # AutoGluonRadiomicsModel
│   ├── soft_voting.py             # top_k soft voting 融合
│   ├── evaluation.py              # ROC/AUC/accuracy + bootstrap CI95
│   ├── calibration/
│   │   ├── __init__.py
│   │   ├── runtime.py             # maybe_apply_calibration_map
│   │   └── artifacts/             # 离线校准 JSON（占位）
│   └── agent.py                   # LLMClassificationAgent + ClsAgentDecision
├── radiomics_judge/               # 【新增】GT-trained radiomics 裁判
│   ├── __init__.py
│   ├── feature_extractor.py       # pyradiomics 2D 特征提取
│   ├── judge.py                   # RadiomicsJudge：对 pred mask 输出分类置信度+特征摘要
│   └── feature_summary.py         # SHAP top-K 特征 + 马氏距离
└── pipeline/                      # 【新增】串联编排
    ├── __init__.py
    └── cascade.py                 # CascadePipeline
```

### 顺手修复的明显问题

| 问题 | 来源 | 修复 |
|---|---|---|
| `Classification_Agent/agent/__init__.py` 导出废弃的 `GeminiAgent` 而非 `LLMClassificationAgent` | 旧代码残留 | 新仓库 `classification/__init__.py` 正确导出 `LLMClassificationAgent` |
| 两个仓库 `base_datasets_info` 重复定义且需手动同步 | 两份 config | 合并到 `shared/base_datasets_info.py`，单一来源 |
| 两个 `ImageProcessor` 一个 cv2 一个 PIL、范围/二值化逻辑不一致 | 历史原因 | `shared/image_io.py` 统一用 cv2 做 IO，模型特定预处理放各自 model 类 |
| `Segmentation_Agent/model_architectures/__init__.py` 为空 | 未配置 | `shared/model_architectures/__init__.py` 正确导出两个架构 |
| API key 硬编码在 config.yaml | 安全隐患 | config 只读环境变量 `DASHSCOPE_API_KEY`，不写明文 key |

---

## 二、关键接口契约

### 2.1 数据结构

```python
# segmentation/base_model.py
@dataclass
class SegModelOutput:
    model_name: str
    mask: np.ndarray              # (H, W) uint8, 0/1
    confidence_map: np.ndarray    # (H, W) float32, [0,1]
    metadata: dict                # input_size, threshold, base_dataset_performance, dataset_info, ece(可选)

@dataclass
class SegAgentDecision:
    selected_model: str
    confidence: float
    reasoning: str
    method: str                   # "single" | "ensemble"
    ensemble_weights: dict | None # {model_name: weight}，method="ensemble" 时非空
    judge_scores: dict | None     # 【新增】{model_name: radiomics_judge_result}，裁判信号

# classification/base_model.py
@dataclass
class ClsModelOutput:
    model_name: str
    predictions: np.ndarray       # (num_classes,) float32
    top_class: int
    top_confidence: float
    requires_mask: bool
    metadata: dict

@dataclass
class ClsAgentDecision:
    selected_model: str
    final_prediction: int
    confidence: float
    reasoning: str
    method: str                   # "single" | "soft_voting"
    voting_models: list[str] | None
```

### 2.2 共享层接口

```python
# shared/image_io.py
class ImageIO:
    """纯 IO，不做模型预处理"""
    @staticmethod
    def load_image(path) -> np.ndarray:          # (H,W,3) RGB, uint8 [0,255]
    @staticmethod
    def load_mask(path) -> np.ndarray:           # (H,W) uint8 [0,255]，不二值化
    @staticmethod
    def save_mask(mask: np.ndarray, path):       # 二值 mask → 0/255 保存
    @staticmethod
    def save_image(image: np.ndarray, path):
    @staticmethod
    def binarize_mask(mask: np.ndarray, threshold=127) -> np.ndarray  # → 0/1
    @staticmethod
    def resize_image(image, target_hw) -> np.ndarray
    @staticmethod
    def resize_mask(mask, target_hw) -> np.ndarray  # INTER_NEAREST

# shared/base_datasets_info.py
BASE_DATASETS_INFO: dict  # TN3K/ThyroidXL/TN5K/DDTI/PKTN/CineClip 的 main_devices/centers/years

def infer_device_match(input_devices: list[str], model_base_datasets: list[str]) -> dict:
    """返回 {matched: bool, matched_datasets: list, reason: str}"""

# shared/llm_client.py
class LLMClient:
    def __init__(self, api_key, base_url, model_name, temperature, max_tokens): ...
    def chat(self, system_prompt: str, user_prompt: str, max_retries=3) -> str:
        """返回 LLM 文本响应；失败重试 max_retries 次"""
```

### 2.3 分割层接口

```python
# segmentation/base_model.py
class BaseSegmentationModel(ABC):
    def __init__(self, model_name, model_path, input_size, threshold,
                 base_dataset_performance: dict, dataset_info: dict): ...
    @abstractmethod
    def load_model(self): ...
    @abstractmethod
    def predict(self, image: np.ndarray) -> SegModelOutput:  # image: (H,W,3) RGB uint8
    def get_metadata(self) -> dict: ...

# segmentation/model_registry.py
class SegModelRegistry:
    def register_model(self, model: BaseSegmentationModel): ...
    def predict_all(self, image: np.ndarray) -> list[SegModelOutput]: ...

# segmentation/quality_evaluator.py
class SegmentationQualityEvaluator:
    def evaluate_single_mask(self, mask: np.ndarray) -> dict:
        # area, num_components, circularity, compactness, solidity, smoothness, aspect_ratio, extent...
    def evaluate_model_agreement(self, masks: list[np.ndarray]) -> dict:
        # pairwise_iou_matrix, average_agreement, overall_agreement, volume_cv, pairwise_hd95_*

# segmentation/agent.py
class SegmentationAgent:
    def __init__(self, llm_client: LLMClient, quality_evaluator: SegmentationQualityEvaluator,
                 performance_stats=None, radiomics_judge=None, config: dict = None): ...
    def select_best_mask(self, image: np.ndarray, predictions: list[SegModelOutput]) -> SegAgentDecision:
        """构造 prompt（形态学+分歧+【新增】radiomics 裁判）→ LLM 选择 → 解析返回"""
    def format_predictions_for_agent(self, image, predictions, quality_results, judge_results=None) -> str:
        """构造给 LLM 的 JSON prompt"""
```

### 2.4 分类层接口

```python
# classification/base_model.py
class BaseClassificationModel(ABC):
    def __init__(self, model_name, model_path, use_tirads: bool,
                 base_dataset_performance: dict, dataset_info: dict): ...
    @abstractmethod
    def load_model(self): ...
    @abstractmethod
    def predict(self, image: np.ndarray, mask: np.ndarray | None) -> ClsModelOutput: ...
    @abstractmethod
    def validate_inputs(self, image, mask): ...
    @property
    @abstractmethod
    def requires_mask(self) -> bool: ...

# classification/model_registry.py
class ClsModelRegistry:
    def __init__(self, calibration_map: dict | None = None): ...
    def register_model(self, model: BaseClassificationModel): ...
    def load_all_models(self): ...
    def predict_all(self, image: np.ndarray, mask: np.ndarray | None) -> list[ClsModelOutput]: ...

# classification/agent.py
class LLMClassificationAgent:
    def __init__(self, llm_client: LLMClient, config: dict = None): ...
    def select_best_model(self, image, mask, predictions: list[ClsModelOutput]) -> ClsAgentDecision: ...
```

### 2.5 Radiomics 裁判接口（新增）

```python
# radiomics_judge/judge.py
class RadiomicsJudge:
    """用 GT-trained AutoGluon radiomics 模型评估 pred mask 的可信度"""
    def __init__(self, model_dir: str, top_k_features: int = 5,
                 shap_reference: str | None = None): ...
    def judge(self, image: np.ndarray, mask: np.ndarray) -> dict:
        """
        输入: image (H,W,3) RGB uint8, mask (H,W) binary 0/1
        输出: {
            'predicted_class': int,       # 0=benign, 1=malignant
            'malignant_prob': float,      # 恶性概率
            'confidence': float,          # max(prob)
            'top_features': [             # SHAP top-K
                {'name': str, 'value': float, 'shap': float, 'direction': str}
            ],
            'mahalanobis_distance': float # 与训练集均值的距离
        }
    """
    def judge_batch(self, image: np.ndarray, masks: list[np.ndarray]) -> list[dict]:
        """对同一张图的多个 pred mask 批量裁判"""
```

### 2.6 Pipeline 接口（新增）

```python
# pipeline/cascade.py
class CascadePipeline:
    """串联分割筛选 → 分类筛选"""
    def __init__(self, seg_agent: SegmentationAgent,
                 cls_agent: LLMClassificationAgent,
                 seg_registry: SegModelRegistry,
                 cls_registry: ClsModelRegistry,
                 image_io: ImageIO,
                 config: dict): ...
    def run_single(self, image: np.ndarray) -> dict:
        """
        1. seg_registry.predict_all(image) → 多个分割预测
        2. seg_agent.select_best_mask(image, seg_predictions) → 筛选 + 裁判
        3. 取筛后 mask → cls_registry.predict_all(image, selected_mask) → 多个分类预测
        4. cls_agent.select_best_model(image, selected_mask, cls_predictions) → 最终分类
        返回: {seg_decision, selected_mask, cls_decision, final_label}
        """
    def run_batch(self, image_dir: str, output_dir: str): ...
```

---

## 三、分阶段构建计划

### Phase 0: 仓库骨架

**文件：**
- 创建: `requirements.txt`, `README.md`, `.gitignore`, 所有 `__init__.py`

- [ ] **Step 0.1: 创建目录结构与 `.gitignore`**

`.gitignore` 内容：`__pycache__/`, `*.pyc`, `output/`, `weights/`, `*.pth`, `.env`, `venv/`, `.venv/`

- [ ] **Step 0.2: 创建 `requirements.txt`**

```
torch>=2.0
torchvision
opencv-python
Pillow
numpy
scipy
pyyaml
openai>=1.0
SimpleITK
pyradiomics
autogluon.tabular
scikit-learn
pandas
```

- [ ] **Step 0.3: 创建所有 `__init__.py`（空占位）**

- [ ] **Step 0.4: 提交骨架**

```bash
git add -A && git commit -m "chore: init repo skeleton"
```

---

### Phase 1: 共享层 `shared/`

**目标：** 两个 agent 都依赖的 IO、数据集信息、LLM 客户端、网络架构，从零编写，消除原两仓库的重复。

- [ ] **Step 1.1: `shared/image_io.py`**

职责：纯图像/mask IO，不含任何模型预处理（归一化/resize-to-model-size 由各 model 类自行处理）。

关键点：
- 统一用 `cv2.imread` 加载（BGR→RGB）
- `load_image` 返回 `(H,W,3) uint8 [0,255]`（不归一化，归一化由模型做）
- `load_mask` 返回 `(H,W) uint8 [0,255]`（不二值化，二值化由调用方按需 `binarize_mask`）
- `save_mask` 接收 0/1 二值 mask，存为 0/255 PNG
- `resize_image` 用 `cv2.INTER_LINEAR`，`resize_mask` 用 `cv2.INTER_NEAREST`

与原代码差异：原 Seg 的 ImageProcessor 返回 [0,1] float 且内置归一化，原 Cls 的用 PIL 返回 [0,255]。新代码统一为 uint8 [0,255] IO 层 + 模型内部预处理，避免混淆。

**为什么不会改变模型推理输出（正确性证明）：**

两个原模型的 `preprocess` 方法内部都有 dtype 防御检查，无论输入 `[0,1] float` 还是 `uint8 [0,255]`，最终都归到同一条数值流：

```python
# 分割侧 Segmentation_Agent/models/dino_unet_model.py:177 与
# 分类侧 Classification_Agent/models/dino_unet_model.py:131 的 preprocess 逻辑一致：
if image.dtype == np.float32 or image.dtype == np.float64:
    image = (image * 255).astype(np.uint8)   # float[0,1] → uint8[0,255]
pil_image = Image.fromarray(image)            # uint8 → PIL
tensor = self.transform(pil_image)            # PIL → ToTensor(/255) → [0,1] → ImageNet Normalize
```

| 模型 | 原流程 | 新流程（image_io） | 进网络值 |
|---|---|---|---|
| 分割 DINOUNet | load `[0,1]float` → preprocess `×255→uint8` → PIL → ToTensor `/255` → Normalize | load `uint8` → preprocess 跳过 if → PIL → ToTensor `/255` → Normalize | **一致**（省掉 `/255→×255` 往返） |
| 分类 DINOUNet | load `uint8` → preprocess 跳过 if → PIL → ToTensor `/255` → Normalize | 同左 | **完全一致** |
| AutoGluonRadiomics | load `uint8` + mask `[0,255]` → 内部 `(mask>0)` 二值化 → SimpleITK | 同左 | **完全一致** |

结论：新方案只是跳过了分割侧"load 时 `/255`、preprocess 又 `×255`"的多余往返，最终进网络的张量值与原实现完全相同。分类侧与 radiomics 侧则零变化。

- [ ] **Step 1.2: `shared/base_datasets_info.py`**

职责：单一来源的数据集元信息 + 设备匹配推断。

```python
BASE_DATASETS_INFO = {
    "TN3K": {"main_devices": [...], "centers": [...], "years": [...]},
    "ThyroidXL": {...},
    "TN5K": {...},
    "DDTI": {...},
    "PKTN": {...},
    "CineClip": {...},
}
```

`infer_device_match(input_devices, model_base_datasets)`：检查 `input_devices` 与模型训练数据集的 `main_devices` 是否有交集，返回 `{matched, matched_datasets, reason}`。

数据来源：合并两个原 config 的 `base_datasets_info` 段（内容一致，去重）。

- [ ] **Step 1.3: `shared/llm_client.py`**

职责：OpenAI 兼容 API 客户端，支持重试。

```python
class LLMClient:
    def __init__(self, api_key, base_url, model_name, temperature=0.3, max_tokens=1024): ...
    def chat(self, system_prompt, user_prompt, max_retries=3) -> str: ...
```

关键点：
- 用 `openai` 库（v1+），`OpenAI(api_key=..., base_url=...)`
- `chat` 内部重试：捕获 `openai.APIError` / 超时，最多 `max_retries` 次，指数退避
- 返回纯文本（choices[0].message.content）
- api_key 从环境变量 `DASHSCOPE_API_KEY` 读取，config 不写明文

- [ ] **Step 1.4: `shared/model_architectures/dino_unet.py`**

职责：`DINOv3_S_UNet` 纯分割网络定义。

来源：参照 `Segmentation_Agent/model_architectures/` 下的架构文件重写。关键：DINOv3 backbone + UNet decoder，输入 `(B,3,H,W)`，输出 `(B,1,H,W)` 概率图。

- [ ] **Step 1.5: `shared/model_architectures/dino_unet_multitask.py`**

职责：`DINOv3_S_UNet_MULTITASK` 多任务网络（分割头 + 分类头）。

来源：参照 `Classification_Agent/model_architectures/dino_unet_multitask.py` 重写。关键：共享 backbone，分割头输出 mask，分类头输出 `num_classes` 概率。

- [ ] **Step 1.6: `shared/model_architectures/__init__.py`**

```python
from .dino_unet import DINOv3_S_UNet
from .dino_unet_multitask import DINOv3_S_UNet_MULTITASK
__all__ = ['DINOv3_S_UNet', 'DINOv3_S_UNet_MULTITASK']
```

- [ ] **Step 1.7: 提交 Phase 1**

```bash
git add -A && git commit -m "feat: shared layer (image_io, base_datasets_info, llm_client, architectures)"
```

**验证：** `python -c "from shared.image_io import ImageIO; from shared.base_datasets_info import BASE_DATASETS_INFO, infer_device_match; from shared.llm_client import LLMClient; print('OK')"`

---

### Phase 2: 分割层 `segmentation/`

**目标：** 从零实现分割预测 + 形态学评估 + 分歧度量 + LLM 选择，功能对标 `Segmentation_Agent/` 完整版，并在 agent 中预留 `radiomics_judge` 接口（Phase 7 填充）。

- [ ] **Step 2.1: `segmentation/base_model.py`**

`SegModelOutput` dataclass + `BaseSegmentationModel` ABC。

关键：`predict(image)` 输入 `(H,W,3) RGB uint8`，模型内部自行 resize/normalize/to-tensor。`metadata` 含 `base_dataset_performance`、`dataset_info`。

- [ ] **Step 2.2: `segmentation/model_registry.py`**

`SegModelRegistry`：`register_model` / `predict_all(image)` / `list_models` / `get_model_info`。模型存 list。`predict_all` 对每个模型 try-except，失败跳过。

- [ ] **Step 2.3: `segmentation/dino_unet_model.py`**

`DINOUNetSegmentationModel(BaseSegmentationModel)`：
- `load_model`：加载 `DINOv3_S_UNet`，载入 `.pth` 权重
- `predict(image)`：resize→normalize(ImageNet)→to-tensor→forward→sigmoid→threshold→`SegModelOutput(mask, confidence_map, metadata)`
- 输入尺寸由 config `input_size` 决定（默认 224×224）

- [ ] **Step 2.4: `segmentation/metrics.py`**

函数：`compute_dice`, `compute_iou`, `compute_hd95`, `compute_pairwise_iou`, `compute_average_agreement`, `compute_ece`。

来源：重写 `Segmentation_Agent/utils/metrics.py`，逻辑一致。`compute_hd95` 用 scipy 或向量化实现（原代码用向量化，保留）。

- [ ] **Step 2.5: `segmentation/quality_evaluator.py`**

`SegmentationQualityEvaluator`：
- `evaluate_single_mask(mask)` → 形态学指标 dict（area, num_components, circularity, compactness, solidity, smoothness, aspect_ratio, extent, ...）
- `evaluate_model_agreement(masks)` → 跨模型一致性（pairwise_iou_matrix, average_agreement, overall_agreement, volume_cv, pairwise_hd95_mean/std）
- `evaluate_batch(masks, model_names)` → 综合评估
- `get_quality_summary(quality_metrics)` → 人类可读摘要

来源：重写 `Segmentation_Agent/utils/quality_evaluator.py`，逻辑一致。

- [ ] **Step 2.6: `segmentation/performance_stats.py`**

函数：`extract_ece_scores`, `bootstrap_mean_ci95`, `build_performance_stats`。

来源：重写 `Segmentation_Agent/utils/performance_stats.py`。用于批处理结束后聚合 Dice/HD95/ECE 的 mean/std/min/max/CI95。

- [ ] **Step 2.7: `segmentation/agent.py`**

`SegmentationAgent` + `SegAgentDecision`。核心方法：

```python
class SegmentationAgent:
    def __init__(self, llm_client, quality_evaluator, performance_stats=None,
                 radiomics_judge=None, config=None):
        # radiomics_judge 默认 None（Phase 2 不启用），Phase 7 注入

    def select_best_mask(self, image, predictions) -> SegAgentDecision:
        # 1. quality_evaluator.evaluate_batch(masks, model_names)
        # 2. 若 radiomics_judge 不为 None: judge.judge_batch(image, masks) → judge_results
        # 3. format_predictions_for_agent(...) → prompt
        # 4. llm_client.chat(system_prompt, user_prompt) → response
        # 5. parse_response(response) → SegAgentDecision
        # 6. 若 decision.method == "ensemble": 按 ensemble_weights 加权融合 confidence_map

    def format_predictions_for_agent(self, image, predictions, quality_results,
                                     judge_results=None) -> str:
        # 构造 JSON prompt：
        #   - 每个模型: name, 形态学指标(circularity/solidity/smoothness/area_ratio),
        #     base_dataset_performance, device_match, ece
        #   - 跨模型: overall_agreement, volume_cv, pairwise_hd95_mean
        #   - 【新增】若 judge_results: 每个模型的 radiomics 裁判 (malignant_prob, confidence,
        #     top_features, mahalanobis_distance)
        #   - reasoning_requirements: 要求 LLM 写出 area_cv / pairwise_hd95 / 裁判分歧的推理

    def _parse_llm_response(self, response) -> SegAgentDecision: ...
    def _ensemble_masks(self, predictions, weights) -> SegModelOutput: ...
```

LLM prompt 的 system message 要点：
- 你是甲状腺超声分割专家，要从多个模型的分割结果中选出最可信的
- 综合考虑：形态学合理性、跨模型一致性、设备匹配、验证集性能、**radiomics 裁判的分类合理性**
- 输出 JSON：`{selected_model, confidence, reasoning, method, ensemble_weights}`

- [ ] **Step 2.8: 提交 Phase 2**

```bash
git add -A && git commit -m "feat: segmentation layer (models, metrics, quality, agent)"
```

**验证：** 构造一个假 image + 假 mask，能跑通 `registry.predict_all` → `quality_evaluator.evaluate_batch` → `agent.select_best_mask`（不接 LLM 时返回 voting 结果）。

---

### Phase 3: 分类层 `classification/`

**目标：** 从零实现分类预测 + 校准 + soft voting + LLM 选择，功能对标 `Classification_Agent/` 完整版。

- [ ] **Step 3.1: `classification/base_model.py`**

`ClsModelOutput` dataclass + `BaseClassificationModel` ABC。

关键：`predict(image, mask)`，`requires_mask` 抽象属性，`validate_inputs(image, mask)` 检查 mask 是否为 None（当 requires_mask=True 时）。

- [ ] **Step 3.2: `classification/model_registry.py`**

`ClsModelRegistry`：
- 模型存 dict
- `calibration_map`：model_name → 校准 JSON
- `load_all_models()`：批量加载
- `predict_all(image, mask)`：对每个模型 validate → predict → `maybe_apply_calibration_map`

- [ ] **Step 3.3: `classification/dino_unet_model.py`**

`DINOUNetModel(BaseClassificationModel)`：
- `requires_mask = False`（多任务模型自己产生 mask 用于分类，或用 crop）
- `load_model`：加载 `DINOv3_S_UNet_MULTITASK`
- `predict(image, mask)`：forward → 取分类头 → softmax → `ClsModelOutput`
- `use_tirads`：控制是良恶性二分类还是 TI-RADS 多分类

- [ ] **Step 3.4: `classification/autogluon_radiomics_model.py`**

`AutoGluonRadiomicsModel(BaseClassificationModel)`：
- `requires_mask = True`
- `load_model`：加载 AutoGluon TabularPredictor
- `predict(image, mask)`：pyradiomics 提特征 → AutoGluon 推理 → `ClsModelOutput`
- 特征提取逻辑参照 `pyradiomics_train/extract_radiomics_2d.py`：用 SimpleITK 构造 image+mask，调 `radiomics.featureextractor.RadiomicsFeatureExtractor`

来源：重写 `Classification_Agent/models/autogluon_radiomics_model.py`。

- [ ] **Step 3.5: `classification/calibration/runtime.py`**

```python
def maybe_apply_calibration_map(output: ClsModelOutput, calibration_map: dict | None):
    """若 calibration_map 有该模型的校准 JSON，对 output.predictions 做温度缩放/等距校准"""
```

- [ ] **Step 3.6: `classification/soft_voting.py`**

```python
def soft_voting(predictions: list[ClsModelOutput], top_k: int = 5) -> ClsModelOutput:
    """取 top_confidence 最高的 top_k 个模型，对 predictions 做加权平均（权重=top_confidence）"""
```

- [ ] **Step 3.7: `classification/evaluation.py`**

```python
def compute_roc_auc(labels, probs) -> dict:     # {auc, fpr, tpr, thresholds}
def compute_accuracy(labels, preds) -> float:
def bootstrap_ci95(labels, probs, metric_fn, n_bootstrap=2000) -> tuple:
```

- [ ] **Step 3.8: `classification/agent.py`**

`LLMClassificationAgent` + `ClsAgentDecision`：

```python
class LLMClassificationAgent:
    def __init__(self, llm_client, config=None): ...

    def select_best_model(self, image, mask, predictions) -> ClsAgentDecision:
        # 1. 若 predictions 分歧小（top_confidence 最高者与其他一致）→ 直接 soft voting
        # 2. 若有分歧 → format → LLM → parse
        # 3. mask 来源信息加入 prompt（Phase 8: 标注 mask 是否经 radiomics 裁判验证）

    def format_predictions_for_agent(self, image, mask, predictions, mask_source=None) -> str:
        # JSON prompt: 每个模型的 top_class, top_confidence, requires_mask,
        #   base_dataset_performance, device_match, ece,
        #   mask_source（"segmentation_agent_filtered" | "external"）

    def _parse_llm_response(self, response) -> ClsAgentDecision: ...
```

- [ ] **Step 3.9: 提交 Phase 3**

```bash
git add -A && git commit -m "feat: classification layer (models, calibration, soft_voting, agent)"
```

**验证：** 假 image + 假 mask 能跑通 `registry.predict_all` → `agent.select_best_model`。

---

### Phase 4: Radiomics 裁判 `radiomics_judge/`（新增·待做文档核心）

**目标：** 实现 GT-trained AutoGluon radiomics 模型作为分割质量裁判。对每个 pred mask，输出"这个 mask 切出来的结节像良性还是恶性 + 关键特征 + 与训练集分布的偏离度"，作为 LLM 选择分割结果的独立信号。

- [ ] **Step 4.1: `radiomics_judge/feature_extractor.py`**

```python
class RadiomicsFeatureExtractor:
    """2D 超声 radiomics 特征提取，复用 pyradiomics"""
    def __init__(self, config: dict | None = None):
        # 配置 binWidth, image normalization 等，参照 pyradiomics_train/extract_radiomics_2d.py
        self._extractor = radiomics.featureextractor.RadiomicsFeatureExtractor(**config)

    def extract(self, image: np.ndarray, mask: np.ndarray) -> dict:
        """
        image: (H,W,3) RGB uint8 → 转 grayscale SimpleITK
        mask:  (H,W) binary 0/1 → SimpleITK
        返回: {feature_name: value}，约 100+ 维
        """
        # 1. RGB→gray
        # 2. np → SimpleITK.GetImageFromArray
        # 3. self._extractor.execute(sitk_image, sitk_mask)
        # 4. 过滤掉诊断性字段（只留 feature_ 开头的）
```

关键：mask 必须非空且有前景像素，否则 pyradiomics 报错。空 mask 返回空 dict + 标记 `valid=False`。

- [ ] **Step 4.2: `radiomics_judge/feature_summary.py`**

```python
class FeatureSummarizer:
    """把 100+ 维特征压缩成 LLM 可读的摘要"""
    def __init__(self, shap_top_k: int = 5, reference_stats: dict | None = None):
        # reference_stats: GT 训练集特征均值/协方差，用于马氏距离

    def summarize(self, features: dict) -> dict:
        return {
            'top_features': [...],          # SHAP top-K: {name, value, shap, direction}
            'mahalanobis_distance': float,  # 与训练集均值的马氏距离
            'feature_count': int,
        }

    def load_shap_reference(self, path: str):
        """加载 SHAP 特征重要性排序 + 训练集均值/协方差"""
```

关键：
- SHAP 特征重要性从 `pyradiomics_train/shap_analyze/` 的产出加载（离线算好的）
- 马氏距离需要训练集的均值向量和协方差矩阵（离线算好存 JSON）
- 若无 SHAP reference，降级为只返回前 K 个特征值（按名称排序）

- [ ] **Step 4.3: `radiomics_judge/judge.py`**

```python
class RadiomicsJudge:
    def __init__(self, model_dir: str, top_k_features: int = 5,
                 shap_reference_path: str | None = None):
        self._predictor = None  # AutoGluon TabularPredictor，lazy load
        self._extractor = RadiomicsFeatureExtractor()
        self._summarizer = FeatureSummarizer(top_k_features, ...)

    def _ensure_loaded(self):
        if self._predictor is None:
            from autogluon.tabular import TabularPredictor
            self._predictor = TabularPredictor.load(self.model_dir)

    def judge(self, image: np.ndarray, mask: np.ndarray) -> dict:
        self._ensure_loaded()
        features = self._extractor.extract(image, mask)
        if not features:
            return {'valid': False, 'reason': 'empty mask'}
        df = pd.DataFrame([features])
        pred = self._predictor.predict_proba(df)
        malignant_prob = float(pred.iloc[0].get(1, 0.5))
        summary = self._summarizer.summarize(features)
        return {
            'valid': True,
            'predicted_class': int(malignant_prob > 0.5),
            'malignant_prob': malignant_prob,
            'confidence': float(max(malignant_prob, 1 - malignant_prob)),
            **summary,
        }

    def judge_batch(self, image: np.ndarray, masks: list[np.ndarray]) -> list[dict]:
        return [self.judge(image, m) for m in masks]
```

关键：`model_dir` 指向 GT-trained AutoGluon 模型（来自 `pyradiomics_train` 训练产物，如 `autogluon_model/gt/TN5K`）。模型 lazy load，首次调用才加载。

- [ ] **Step 4.4: 提交 Phase 4**

```bash
git add -A && git commit -m "feat: radiomics judge (GT-trained AutoGluon as segmentation quality arbiter)"
```

**验证：** 用一张真实超声图 + 一个 mask，`RadiomicsJudge.judge(image, mask)` 返回含 `malignant_prob` 和 `top_features` 的 dict。

---

### Phase 5: 串联 Pipeline `pipeline/`（新增·待做文档核心）

**目标：** 实现"分割筛选 → 分类筛选"的闭环。分割 Agent 筛选出的 mask 直接喂给分类 Agent。

- [ ] **Step 5.1: `pipeline/cascade.py`**

```python
class CascadePipeline:
    def __init__(self, seg_agent, cls_agent, seg_registry, cls_registry,
                 image_io, config):
        self.seg_agent = seg_agent
        self.cls_agent = cls_agent
        self.seg_registry = seg_registry
        self.cls_registry = cls_registry
        self.image_io = image_io
        self.config = config

    def run_single(self, image: np.ndarray) -> dict:
        # Phase A: 分割筛选
        seg_predictions = self.seg_registry.predict_all(image)
        seg_decision = self.seg_agent.select_best_mask(image, seg_predictions)

        # 取筛后 mask
        if seg_decision.method == "ensemble":
            selected_mask = self._get_ensemble_mask(seg_predictions, seg_decision)
        else:
            selected_mask = next(
                p.mask for p in seg_predictions if p.model_name == seg_decision.selected_model
            )

        # Phase B: 分类筛选（mask 来源标注为 "segmentation_agent_filtered"）
        cls_predictions = self.cls_registry.predict_all(image, selected_mask)
        cls_decision = self.cls_agent.select_best_model(
            image, selected_mask, cls_predictions
        )

        return {
            'seg_decision': seg_decision.__dict__,
            'selected_mask_shape': selected_mask.shape,
            'cls_decision': cls_decision.__dict__,
            'final_label': cls_decision.final_prediction,
            'final_confidence': cls_decision.confidence,
        }

    def run_batch(self, image_dir: str, output_dir: str):
        """遍历目录，run_single 每张图，聚合结果 + performance_stats"""
        # 1. list 图片
        # 2. for each: load → run_single → save mask + json
        # 3. 批次结束: build_performance_stats / compute_roc_auc（若有 label）

    def _get_ensemble_mask(self, predictions, decision) -> np.ndarray:
        """按 ensemble_weights 加权融合 confidence_map → threshold"""
```

关键设计：
- `run_single` 是核心：分割筛选产出 mask → 分类筛选消费 mask
- 分类 Agent 的 `mask_source` 标注为 `"segmentation_agent_filtered"`，LLM 知道 mask 已经过裁判验证
- `run_batch` 支持断点续跑（`start_index`）、max_images 限制、输出 JSON + mask

- [ ] **Step 5.2: 提交 Phase 5**

```bash
git add -A && git commit -m "feat: cascade pipeline (seg filter → cls filter)"
```

**验证：** mock 两个 registry + agent，`CascadePipeline.run_single` 返回含 `seg_decision` 和 `cls_decision` 的 dict。

---

### Phase 6: 入口与配置

**目标：** 统一 config，三个入口脚本。

- [ ] **Step 6.1: `config/config.yaml`**

```yaml
# 共享段
shared:
  base_datasets_info: ...        # 引用 shared/base_datasets_info.py 的内置数据，此处可覆盖
  agent_llm:
    api_key_env: "DASHSCOPE_API_KEY"   # 从环境变量读，不写明文
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model_name: "qwen2.5-32b-instruct"
    temperature: 0.3
    max_tokens: 1024

# 分割段
segmentation:
  dino_unet:
    models:
      - name: "all_datasets"
        model_path: "weights/seg/all_datasets.pth"
        input_size: [224, 224]
        threshold: 0.5
        base_dataset_performance: {TN5K: {dice: 0.83, hd95: 8.5, ece: 0.01}, ...}
        dataset_info: {base_datasets: [...], dataset_size: 39604}
      # ... 更多模型
  agent:
    use_agent_selection: true
    include_disagreement_metrics_in_prompt: true
    ensemble:
      enabled: true
      top_k: 1
      method: "weighted_average"
      threshold: 0.5

# 分类段
classification:
  dino_unet:
    models:
      - name: "all_datasets"
        model_path: "weights/cls/all_datasets.pth"
        use_tirads: false
        base_dataset_performance: {...}
        dataset_info: {...}
  autogluon:
    models:
      - name: "autogluon_radiomics"
        model_dir: "weights/cls/autogluon_model"
        base_dataset_performance: {...}
        dataset_info: {...}
  calibration:
    enabled: false
    artifacts_dir: "classification/calibration/artifacts"
  agent:
    enable_agent: true
    top_k: 5

# Radiomics 裁判段（新增）
radiomics_judge:
  enabled: true
  model_dir: "weights/judge/autogluon_gt_trained"   # GT-trained AutoGluon 模型
  top_k_features: 5
  shap_reference_path: "weights/judge/shap_reference.json"
  # 触发阈值：跨模型分歧大时才启用裁判（省时间）；null 表示总是启用
  trigger_volume_cv: null

# Pipeline 段（新增）
pipeline:
  seg_output_to_cls_mask: true    # 分割筛选结果直接喂分类
  data:
    image_input: "/path/to/images"
    label_file: "/path/to/labels.json"
    device_info: ["GE Logiq E9", "GE S7"]
    start_index: 0
    max_images: null
  output:
    output_dir: "output/pipeline_run"
    save_masks: true
    save_json: true
```

- [ ] **Step 6.2: `run_seg.py`**

职责：单独跑分割筛选（对标 `Segmentation_Agent/main.py`）。

流程：
1. 加载 config → 构建 `LLMClient`
2. 构建 `SegModelRegistry`，从 config 注册所有 dino_unet 分割模型
3. 构建 `SegmentationQualityEvaluator`
4. 构建 `SegmentationAgent`（`radiomics_judge=None`，或按 config 启用）
5. 遍历 image_dir → `registry.predict_all` → `agent.select_best_mask` → 保存 mask + JSON
6. 批次结束：`build_performance_stats`

- [ ] **Step 6.3: `run_cls.py`**

职责：单独跑分类筛选（对标 `Classification_Agent/main.py`）。

流程：
1. 加载 config → 构建 `LLMClient`
2. 构建 `ClsModelRegistry`，注册 dino_unet 多任务 + autogluon radiomics
3. 构建 `LLMClassificationAgent`
4. mask 来源：config 的 `data.mask_input`（外部 mask）
5. 遍历 → `registry.predict_all(image, mask)` → `agent.select_best_model` → 保存 JSON
6. 批次结束：`compute_roc_auc` + `bootstrap_ci95`

- [ ] **Step 6.4: `run_pipeline.py`**

职责：串联入口。

流程：
1. 加载 config
2. 构建所有组件：`LLMClient`、`SegModelRegistry`、`ClsModelRegistry`、`SegmentationQualityEvaluator`、`RadiomicsJudge`（若 enabled）、`SegmentationAgent`（注入 judge）、`LLMClassificationAgent`
3. 构建 `CascadePipeline`
4. `pipeline.run_batch(image_dir, output_dir)`

- [ ] **Step 6.5: 提交 Phase 6**

```bash
git add -A && git commit -m "feat: unified config and entry points (run_seg, run_cls, run_pipeline)"
```

---

### Phase 7: 集成 Radiomics 裁判到分割 Agent（待做文档任务1）

**目标：** 让分割 Agent 的 LLM 在选择 mask 时，能看到每个 pred mask 的 radiomics 裁判结果（分类置信度 + 特征摘要），作为"分割质量"的独立信号。

- [ ] **Step 7.1: 修改 `segmentation/agent.py` 的 `select_best_mask`**

在 `quality_evaluator.evaluate_batch` 之后、`format_predictions_for_agent` 之前，插入：

```python
judge_results = None
if self.radiomics_judge is not None:
    masks = [p.mask for p in predictions]
    judge_results = self.radiomics_judge.judge_batch(image, masks)
    # judge_results: [{malignant_prob, confidence, top_features, ...}, ...]
```

- [ ] **Step 7.2: 修改 `format_predictions_for_agent`**

在 prompt JSON 的每个模型条目中增加 `radiomics_judge` 字段（仅当 judge_results 非空）：

```json
{
  "model_name": "all_datasets",
  "morphology": {"circularity": 0.82, "solidity": 0.91, "smoothness": 0.75, "area_ratio": 0.15},
  "base_dataset_performance": {"TN5K": {"dice": 0.83}},
  "device_match": {"matched": true},
  "ece": 0.01,
  "radiomics_judge": {
    "malignant_prob": 0.72,
    "confidence": 0.72,
    "top_features": [
      {"name": "original_glcm_Contrast", "value": 45.3, "direction": "malignant"},
      {"name": "log_sigma_3_mm_3D_GLRLM_RunEntropy", "value": 4.2, "direction": "benign"}
    ],
    "mahalanobis_distance": 2.1
  }
}
```

在 reasoning_requirements 中增加：
- "若多个模型的 radiomics_judge 分类结果出现分歧，说明分割质量差异大，需重点分析哪个 mask 让裁判给出更合理的分类"
- "mahalanobis_distance 过大（>3）的 mask 可能分割异常"

- [ ] **Step 7.3: 修改 system prompt**

增加一句：
> "你还将看到每个分割结果经 GT-trained radiomics 模型的分类判断。这个裁判模型用金标准 mask 训练，其分类置信度可作为分割质量的间接信号：分割越准确，radiomics 特征越接近训练分布，分类置信度越合理。"

- [ ] **Step 7.4: 提交 Phase 7**

```bash
git add -A && git commit -m "feat: integrate radiomics judge into segmentation agent LLM prompt"
```

**验证：** 构造 2 个不同的 mask（一个好的一个差的），`select_best_mask` 的 prompt 中能看到 judge 结果，LLM 倾向选 judge 置信度更合理的 mask。

---

### Phase 8: 集成串联到分类 Agent（待做文档任务2）

**目标：** 分类 Agent 消费分割 Agent 筛选后的 mask，并在 LLM prompt 中标注 mask 来源。

- [ ] **Step 8.1: 修改 `classification/agent.py` 的 `select_best_model`**

增加 `mask_source` 参数：

```python
def select_best_model(self, image, mask, predictions, mask_source="external") -> ClsAgentDecision:
    # mask_source: "segmentation_agent_filtered" | "external"
```

- [ ] **Step 8.2: 修改 `format_predictions_for_agent`**

在 prompt JSON 顶部增加：

```json
{
  "mask_source": "segmentation_agent_filtered",
  "mask_validation": "此 mask 已经过分割 Agent 的 radiomics 裁判验证，可信度较高",
  "models": [...]
}
```

当 `mask_source="external"` 时标注"mask 来自外部，未经验证"。

- [ ] **Step 8.3: 确保 `pipeline/cascade.py` 正确传递 mask_source**

`CascadePipeline.run_single` 调用 `cls_agent.select_best_model(image, selected_mask, cls_predictions, mask_source="segmentation_agent_filtered")`。

- [ ] **Step 8.4: 提交 Phase 8**

```bash
git add -A && git commit -m "feat: integrate cascade mask source into classification agent"
```

**验证：** `run_pipeline.py` 端到端跑通一张图，输出 JSON 含 seg_decision + cls_decision + final_label。

---

## 四、验证策略

| Phase | 验证方式 |
|---|---|
| 0-1 | import 检查，无报错 |
| 2 | 假数据跑通 `predict_all → evaluate_batch → select_best_mask`（voting 模式） |
| 3 | 假数据跑通 `predict_all → select_best_model` |
| 4 | 真实超声图 + mask 跑通 `judge.judge`，返回含 `malignant_prob` |
| 5 | mock 组件跑通 `CascadePipeline.run_single` |
| 6 | `run_seg.py --config config/config.yaml` 能加载模型并处理 1 张图 |
| 7 | 分割 agent prompt 中可见 radiomics_judge 字段 |
| 8 | `run_pipeline.py` 端到端，输出含两阶段 decision |

**回归对比：** Phase 2 完成后，用同一数据集跑 `run_seg.py`，与原 `Segmentation_Agent/main.py` 的输出对比 Dice/HD95（应一致，因为模型权重和推理逻辑相同）。Phase 3 同理对比分类指标。

---

## 五、风险与注意事项

1. **AutoGluon 版本兼容**：`autogluon.tabular` 的 `predict_proba` 接口在不同版本有差异。`RadiomicsJudge` 和 `AutoGluonRadiomicsModel` 都依赖它，需 pin 版本。建议 `autogluon.tabular>=1.0`。

2. **pyradiomics 空 mask 崩溃**：pyradiomics 对空 mask 或面积过小的 mask 会抛异常。`RadiomicsFeatureExtractor.extract` 必须捕获并返回 `{'valid': False}`，`RadiomicsJudge.judge` 据此返回无效标记，不中断流程。

3. **特征列对齐**：AutoGluon 推理时，pred mask 提取的特征列必须与 GT 训练时的特征列完全一致（顺序、名称）。`RadiomicsFeatureExtractor` 的配置必须与 `pyradiomics_train/extract_radiomics_2d.py` 完全相同。建议把训练时的 pyradiomics 配置 YAML 复制到 `weights/judge/` 下，加载时读取。

4. **LLM prompt token 预算**：每个模型条目含形态学(~10字段) + 性能(~6数据集) + 裁判(top5特征+摘要) ≈ 300 token/模型。6 个模型约 1800 token，加上 system prompt 和 reasoning_requirements，总输入约 2500 token。Qwen2.5-32b 的 32k 上下文足够，但需控制 `top_k_features` 不超过 5。

5. **DINOv3 权重路径**：分割和分类的 DINO-UNet 权重文件不同（纯分割 vs 多任务），config 里的 `model_path` 不能混用。多任务权重含分类头参数，纯分割权重没有。

6. **device 推断**：`infer_device_match` 的设备列表要从 config 的 `data.device_info` 传入，与 `BASE_DATASETS_INFO` 比对。原代码这段逻辑分散在两处，合并后统一到 `shared/base_datasets_info.py`。

7. **image_io 不二值化 mask 的影响（不影响推理，影响指标计算）**：原分割侧 `load_mask` 自动 `>127→0/1` 二值化，新 `image_io.load_mask` 返回 `[0,255]` 不二值化。这不影响任何模型推理（分割模型 `predict(image)` 不接收 mask；分类 radiomics 模型内部自己 `(mask>0)` 二值化）。但算分割指标（Dice/HD95）时调用方必须显式二值化 GT mask：`gt = image_io.binarize_mask(image_io.load_mask(path))`。原分割侧 `load_mask` 偷偷二值化的行为被移除，二值化职责回归调用方。

---

## 六、自检：待做文档需求覆盖

| 待做文档要求 | 实现位置 |
|---|---|
| 用 GT 分割结果训练一个 radiomics 模型 | 复用 `pyradiomics_train` 已训练的 GT 模型，路径在 `config.yaml → radiomics_judge.model_dir` |
| 把各分割模型输出作为 radiomics 输入 | `radiomics_judge/judge.py` 的 `judge_batch` |
| 用分类置信度+特征评估分割可信度 | `Phase 7`：judge 结果加入 `segmentation/agent.py` 的 LLM prompt |
| 差异大时挑更可信的分割 | `Phase 7`：LLM 综合形态学+分歧+裁判信号选择 |
| 根据筛选完的分割结果跑分类 | `Phase 5+8`：`pipeline/cascade.py` 串联，分类 agent 消费筛后 mask |
| agent 再次评估 radiomics 和其他分类模型输出 | `Phase 3+8`：`classification/agent.py` 的 `select_best_model` 综合所有分类模型 |

---

## 七、执行交接

计划已完成并保存到 `docs/BUILD_PLAN.md`。两种执行方式：

1. **Subagent 驱动（推荐）**：每个 Phase 派一个 subagent 实现，Phase 间 review，快速迭代
2. **内联执行**：在当前会话按 Phase 顺序执行，批量推进 + checkpoint review

**选择哪种方式开始？**
