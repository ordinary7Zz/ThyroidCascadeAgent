# ThyroidCascadeAgent 多模型适配方案

> **背景：** `BUILD_PLAN.md` 只把 `DINOv3_S_UNet`（分割）和 `DINOv3_S_UNet_MULTITASK` + AutoGluon（分类）纳入架构。实际 `my_Thyroid_infer/` 下已有 9 个独立推理包，覆盖 5 个分割模型和 4 个分类模型。本文档分析这些模型的接口异质性，给出在现有 ThyroidCascadeAgent 三层架构下最小侵入的适配方案。
>
> **本文档不实现代码，只做接口调研与方案选型。**

---

## 一、当前架构的扩展点与约束

### 1.1 分割层契约（已实现）

```python
# segmentation/base_model.py
class BaseSegmentationModel(ABC):
    def __init__(self, model_name, model_path, input_size=(224,224), threshold=0.5,
                 base_dataset_performance=None, dataset_info=None, device="cuda", **kwargs): ...
    @abstractmethod
    def load_model(self) -> None: ...
    @abstractmethod
    def predict(self, image: np.ndarray) -> SegModelOutput:  # image: (H,W,3) RGB uint8 [0,255]
        ...

@dataclass
class SegModelOutput:
    model_name: str
    mask: np.ndarray              # (H,W) uint8, 0/1
    confidence_map: np.ndarray   # (H,W) float32 [0,1]
    metadata: dict
```

### 1.2 分类层契约（BUILD_PLAN Phase 3 待实现）

```python
class BaseClassificationModel(ABC):
    def __init__(self, model_name, model_path, use_tirads, base_dataset_performance, dataset_info): ...
    @abstractmethod
    def load_model(self): ...
    @abstractmethod
    def predict(self, image: np.ndarray, mask: np.ndarray | None) -> ClsModelOutput: ...
    @property
    @abstractmethod
    def requires_mask(self) -> bool: ...
```

### 1.3 不变的扩展点

| 扩展点 | 是否需要改动 |
|---|---|
| `BaseSegmentationModel.predict(image)` 契约 | ❌ 保持 |
| `BaseClassificationModel.predict(image, mask)` 契约 | ❌ 保持 |
| `SegModelRegistry.predict_all` / `register_model` | ❌ 保持 |
| `ClsModelRegistry.predict_all` / `register_model` | ❌ 保持 |
| `SegmentationAgent.select_best_mask` | ❌ 保持（agent 只消费 `SegModelOutput`） |
| `LLMClassificationAgent.select_best_model` | ❌ 保持（agent 只消费 `ClsModelOutput`） |
| `config.yaml` 结构 | ✅ **需要扩展**（见第五章） |
| `shared/model_architectures/` | ✅ **需要补充**（轻量架构）或改用 adapter（见第三章） |

**核心结论**：当前架构的抽象边界已经够用，适配工作集中在「为每个外部模型写一个 `BaseSegmentationModel` / `BaseClassificationModel` 子类」，把异质性封装在子类内部。

---

## 二、9 个模型的接口调研

### 2.1 分割模型

| 模型 | 来源目录 | 网络架构 | 输入预处理 | 权重格式 | confidence_map 可获得性 | 特殊依赖 |
|---|---|---|---|---|---|---|
| **DINOv3-UNet** | `infer_dinov3_unet` | DINOv3 ViT-S + UNet decoder | PIL RGB → Resize(224) → ToTensor → ImageNet Norm | `.pth` state_dict（含 `state_dict`/`model_state_dict` key） | ✓ sigmoid 概率图 | DINOv3 backbone（已在 `shared/model_architectures/`） |
| **TransUNet** | `infer_transunet` | R50-ViT-B_16 + ResNet skip | **灰度单通道** → scipy zoom order=3 到 224 → unsqueeze | `.pth` state_dict（含 `model`/`state_dict` key） | ⚠ 多类 softmax logits（2 类，取前景类概率） | `networks/vit_seg_modeling`（自包含） |
| **MedSegX** | `infer_medsegx` | SAM ViT-B + 模态/器官 embedding | RGB float → Resize(1024) → `sam.preprocess` | `.pth`，用 `model.load_parameters(ckpt["model"])` | ✓ `torch.sigmoid(mask_pred)` 选中 mask 的概率 | `segment_anything` 包；**需 `task_name`**（`US_GlndThyroid`/`US_ThyroidNodule`）和 **box prompt** |
| **MedSAM2** | `infer_medsam2` | SAM2 video predictor | RGB → [3,H,W] → Resize(512) → ImageNet Norm | `.pt`，`build_sam2_video_predictor_npz(config, ckpt)` | ✓ logits → sigmoid | `sam2` 包；单帧"视频"推理；全图 box prompt |
| **UltraFedFM** | `infer_ultrafedfm/segment.py` | SMP UNet + MAE encoder | cv2 RGB → albumentations Resize+Norm(224) | `.pth` 直接 state_dict | ✓ sigmoid 输出 | `segmentation_models_pytorch`、`albumentations`、MAE encoder 权重 |

### 2.2 分类模型

| 模型 | 来源目录 | 网络架构 | 输入预处理 | 是否需要 mask | 权重格式 | 特殊依赖 |
|---|---|---|---|---|---|---|
| **DINOv3-UNet Multitask** | `infer_dinov3_unet_multitask` | DINOv3 + 分割头 + 分类头 | PIL RGB → Resize(224) → ImageNet Norm | ❌（模型自己产生 mask/crop） | `.pth` state_dict（`weights_only=True`） | DINOv3 backbone |
| **MedSigLIP** | `infer_medsiglip` | SigLIP ViT + 分类头 | 灰度→三通道 → Resize(448) → mean/std=[0.5,0.5,0.5] | ❌ | `.pt` checkpoint（含 `model_state_dict` + `config` + `class_names`） | `timm`、HuggingFace `medsiglip-448` 预训练目录 |
| **BiomedCLIP** | `infer_biomedclip` | open_clip visual tower + 分类头 | PIL RGB → Resize(224) → CLIP 标准化 mean=(0.481,...) std=(0.268,...) | ❌ | `.pth` state_dict + 预训练骨干目录（`open_clip_config.json` + `.bin`/`.safetensors`） | `open_clip`、`safetensors` |
| **AutoGluon Radiomics** | `infer_autogluon` | AutoGluon TabularPredictor | (image, mask) → pyradiomics 特征向量 | ✅ **必须** | 目录形式（`predictor.pkl` + `radiomics_2d.yaml`） | `autogluon.tabular`、`pyradiomics`、`SimpleITK` |

### 2.3 异质性维度汇总

| 维度 | 分割侧差异 | 分类侧差异 |
|---|---|---|
| **输入通道** | TransUNet 灰度，其他 RGB | MedSigLIP 灰度复制三通道，其他 RGB；AutoGluon 用灰度提特征 |
| **输入尺寸** | 224 / 512 / 1024 | 224 / 448 |
| **归一化常数** | 大多 ImageNet；MedSegX 用 `sam.preprocess` | ImageNet / [0.5,0.5,0.5] / CLIP 标准 / 无（AutoGluon） |
| **输出类型** | sigmoid 单通道（DINO/UltraFedFM）/ softmax 多类（TransUNet）/ SAM mask decoder logits | sigmoid 二分类 / softmax 多分类 / AutoGluon predict_proba |
| **是否需 prompt** | MedSegX 需 box + task_name；MedSAM2 需 box | 都不需要 |
| **是否需 mask** | 都不需要 | 仅 AutoGluon 需要 |
| **权重格式** | `.pth` state_dict / `.pt` / 目录 | `.pth` / `.pt` checkpoint / 预训练骨干目录 + 分类头 |
| **额外配置** | MedSegX 的 `task_name`、`vit_name` | num_classes、class_names、预训练路径 |

---

## 三、适配方案对比

### 方案 A：全部在 `shared/model_architectures/` 重写网络定义

- **做法**：把 9 个模型的 `model.py` / `networks/` 全部复制到 `shared/model_architectures/`，每个写一个 `BaseSegmentationModel` 子类。
- **优点**：代码自包含，无外部路径依赖。
- **缺点**：
  - `segment_anything`、`sam2`、`open_clip`、`timm`、`albumentations`、`autogluon` 等重依赖全部进入主环境
  - 9 个网络定义重复维护，独立推理包升级后需同步
  - TransUNet 的 `networks/` 4 个文件、MedSegX 的 `segment_anything/` 29 个文件都要搬进来

### 方案 B：纯 Adapter 包装独立推理包

- **做法**：ThyroidCascadeAgent 内不重写网络，每个模型写一个 ThinAdapter，通过 `sys.path` 引用 `my_Thyroid_infer/infer_xxx/` 下的 `model.py` 和 `infer.py` 逻辑。
- **优点**：零代码重复，独立包可独立迭代。
- **缺点**：
  - 跨仓库路径耦合（`my_Thyroid_infer/` 必须存在）
  - 9 个独立包的 `sys.path` 注入易冲突
  - 依赖仍会污染主环境

### 方案 C（推荐）：Hybrid — 按依赖重量分级

按"依赖是否纯净"分两级处理：

| 级别 | 模型 | 处理方式 |
|---|---|---|
| **L1：轻量重写** | DINOv3-UNet（分割）、TransUNet（分割）、UltraFedFM-segment（分割）、DINOv3-UNet Multitask（分类） | 网络定义搬到 `shared/model_architectures/`，子类放 `segmentation/` 或 `classification/` 下 |
| **L2：Adapter 包装** | MedSegX、MedSAM2、MedSigLIP、BiomedCLIP、AutoGluon | 子类内 lazy import + 调用独立包的 `model.py`，输入输出转契约格式 |

**L1 判定标准**：依赖只有 `torch` / `torchvision` / `PIL` / `cv2` / `numpy` / `scipy`，无大包。
**L2 判定标准**：依赖 `segment_anything` / `sam2` / `open_clip` / `timm` / `autogluon` / `pyradiomics` 等重型包。

**优点**：
- L1 模型零外部路径依赖，部署简单
- L2 模型按需 lazy import，不启用就不装依赖
- 独立推理包的升级可通过 adapter 快速同步（改 adapter 的转换逻辑即可）
- 主环境只装实际启用的模型依赖

---

## 四、推荐方案的具体适配映射

### 4.1 分割模型适配映射

| 模型 | 子类名 | 文件位置 | 依赖级别 | 输入转换 | 输出转换 |
|---|---|---|---|---|---|
| DINOv3-UNet | `DINOUNetSegmentationModel` | `segmentation/dino_unet_model.py`（**已实现**） | L1 | 无（直接接收 RGB uint8） | sigmoid → (H,W) float32 + 二值化 |
| TransUNet | `TransUNetSegmentationModel` | `segmentation/transunet_model.py`（新增） | L1 | RGB→灰度（`cv2.cvtColor`）→ zoom(224) | softmax 多类 → 取前景类概率作为 confidence_map |
| UltraFedFM | `UltraFedFMSegmentationModel` | `segmentation/ultrafedfm_model.py`（新增） | L1 | RGB → albumentations Resize+Norm | sigmoid → (H,W) float32 |
| MedSegX | `MedSegXSegmentationModel` | `segmentation/medsegx_model.py`（新增） | L2 | RGB float → Resize(1024) → `sam.preprocess` | mask_pred sigmoid → (H,W) float32 |
| MedSAM2 | `MedSAM2SegmentationModel` | `segmentation/medsam2_model.py`（新增） | L2 | RGB→[3,H,W]→Resize(512)→ImageNet Norm | logits → sigmoid → (H,W) float32 |

### 4.2 分类模型适配映射

| 模型 | 子类名 | 文件位置 | 依赖级别 | requires_mask | 输入转换 | 输出转换 |
|---|---|---|---|---|---|---|
| DINOv3-UNet Multitask | `DINOUNetClassificationModel` | `classification/dino_unet_model.py`（BUILD_PLAN 已规划） | L1 | False | RGB → Resize(224) → ImageNet Norm | 取 `benign_malignant` 头（二分类）或 `tirads` 头（五分类）→ softmax |
| MedSigLIP | `MedSigLIPClassificationModel` | `classification/medsiglip_model.py`（新增） | L2 | False | 灰度→三通道 → Resize(448) → [0.5,0.5,0.5] Norm | logits → softmax |
| BiomedCLIP | `BiomedCLIPClassificationModel` | `classification/biomedclip_model.py`（新增） | L2 | False | RGB → Resize(224) → CLIP Norm | logits → softmax |
| AutoGluon Radiomics | `AutoGluonRadiomicsModel` | `classification/autogluon_radiomics_model.py`（BUILD_PLAN 已规划） | L2 | **True** | (image, mask) → pyradiomics 特征 → DataFrame | `predict_proba` → (num_classes,) float32 |

### 4.3 通用适配规则

每个子类必须遵守：

1. **输入契约**：`predict(image: np.ndarray (H,W,3) RGB uint8)` —— 不修改 image 原数组
2. **输出契约**：
   - 分割：`SegModelOutput(mask=(H,W) uint8 0/1, confidence_map=(H,W) float32 [0,1], metadata=...)`
   - 分类：`ClsModelOutput(predictions=(num_classes,) float32, top_class=int, top_confidence=float, ...)`
3. **内部自行 resize/归一化**：不依赖 `shared/image_io` 的预处理（IO 层只做加载/保存）
4. **lazy import**：L2 模型在 `load_model()` 内才 import 重依赖，`predict()` 不重复 import
5. **失败安全**：`predict` 异常时返回 `SegModelOutput(mask=zeros, confidence_map=zeros, metadata={'error': ...})`，或抛异常由 `SegModelRegistry.predict_all` 的 try-except 兜底

---

## 五、config.yaml 扩展设计

BUILD_PLAN 的 `segmentation.dino_unet.models[]` 结构需要泛化为多架构：

```yaml
segmentation:
  models:
    - type: "dinov3_unet"            # 对应子类名前缀
      name: "dinov3_unet_all_datasets"
      model_path: "weights/seg/dinov3_unet/all_datasets.pth"
      input_size: [224, 224]
      threshold: 0.5
      use_dilation: false
      base_dataset_performance: {TN5K: {dice: 0.83, hd95: 8.5, ece: 0.01}}
      dataset_info: {base_datasets: [TN3K, TN5K, ThyroidXL, DDTI, PKTN, CineClip]}

    - type: "transunet"
      name: "transunet_all_datasets"
      model_path: "weights/seg/transunet/all_datasets.pth"
      input_size: 224
      num_classes: 2                 # TransUNet 是多类 softmax
      vit_name: "R50-ViT-B_16"
      n_skip: 3
      base_dataset_performance: {...}
      dataset_info: {...}

    - type: "ultrafedfm"
      name: "ultrafedfm_seg_all_datasets"
      model_path: "weights/seg/ultrafedfm/all_datasets.pth"
      input_size: 224
      threshold: 0.5
      base_dataset_performance: {...}
      dataset_info: {...}

    - type: "medsegx"
      name: "medsegx_nodule"
      model_path: "weights/seg/medsegx/nodule.pth"      # --model_weight
      sam_checkpoint_dir: "weights/seg/medsegx/sam/"   # --checkpoint（SAM 目录）
      model_type: "vit_b"
      task_name: "US_ThyroidNodule"                    # 必填
      method: "medsegx"
      box_mode: "full"                                  # agent 场景固定 full（无 GT）
      bottleneck_dim: 16
      embedding_dim: 16
      expert_num: 4
      base_dataset_performance: {...}
      dataset_info: {...}

    - type: "medsam2"
      name: "medsam2_nodule"
      model_path: "weights/seg/medsam2/nodule.pt"
      config: "sam2.1_hiera_t512.yaml"
      base_dataset_performance: {...}
      dataset_info: {...}

  agent: { ... }  # 不变

classification:
  models:
    - type: "dinov3_unet_multitask"
      name: "dinov3_cls_all_datasets"
      model_path: "weights/cls/dinov3_multitask/all_datasets.pth"
      use_tirads: false
      num_classes: 2
      img_size: 224
      base_dataset_performance: {...}
      dataset_info: {...}

    - type: "medsiglip"
      name: "medsiglip_binary"
      model_path: "weights/cls/medsiglip/binary.pt"            # checkpoint
      pretrained_model_path: "weights/pretrained/medsiglip-448" # 预训练骨干目录
      num_classes: 2
      img_size: 448
      base_dataset_performance: {...}
      dataset_info: {...}

    - type: "biomedclip"
      name: "biomedclip_binary"
      model_path: "weights/cls/biomedclip/binary.pth"            # 分类头权重
      pretrained_model_dir: "weights/pretrained/biomedclip/"    # open_clip_config.json + .bin
      num_classes: 2
      img_size: 224
      base_dataset_performance: {...}
      dataset_info: {...}

    - type: "autogluon_radiomics"
      name: "autogluon_radiomics_binary"
      model_dir: "weights/cls/autogluon/binary/"                  # predictor.pkl 所在目录
      radiomics_params: "weights/cls/autogluon/radiomics_2d.yaml"
      num_classes: 2
      class_names: ["benign", "malignant"]
      mask_threshold: 0
      spacing: [1.0, 1.0]
      base_dataset_performance: {...}
      dataset_info: {...}

  calibration: { ... }  # 不变
  agent: { ... }        # 不变

radiomics_judge: { ... }  # 不变
pipeline: { ... }         # 不变
```

**关键设计**：
- 用 `type` 字段驱动模型工厂（`type → 子类` 映射），替代 BUILD_PLAN 中按 `dino_unet`/`autogluon` 分段写死的结构
- 每个模型的"特有参数"（如 MedSegX 的 `task_name`、MedSigLIP 的 `pretrained_model_path`）平铺在该模型条目下，子类自行读取
- `base_dataset_performance` 和 `dataset_info` 仍是必填，作为 LLM prompt 的统一信号

---

## 六、模型工厂设计

为了把 config 的 `type` 字段映射到子类，需要一个工厂：

```python
# segmentation/model_factory.py（新增）
SEG_MODEL_REGISTRY: dict[str, type[BaseSegmentationModel]] = {}

def register_seg_model(type_name: str):
    def deco(cls):
        SEG_MODEL_REGISTRY[type_name] = cls
        return cls
    return deco

@register_seg_model("dinov3_unet")
class DINOUNetSegmentationModel(BaseSegmentationModel): ...

@register_seg_model("transunet")
class TransUNetSegmentationModel(BaseSegmentationModel): ...

# ... 其他

def build_seg_model(cfg: dict) -> BaseSegmentationModel:
    type_name = cfg["type"]
    cls = SEG_MODEL_REGISTRY[type_name]
    return cls(**{k: v for k, v in cfg.items() if k != "type"})
```

分类侧同理（`classification/model_factory.py`）。

**入口脚本改造**：`run_seg.py` / `run_cls.py` / `run_pipeline.py` 不再硬编码 `DINOUNetSegmentationModel`，改为：

```python
for model_cfg in config["segmentation"]["models"]:
    model = build_seg_model(model_cfg)
    model.load_model()
    seg_registry.register_model(model)
```

---

## 七、依赖管理与工程问题

### 7.1 依赖分组

把 `requirements.txt` 拆分为核心 + 可选：

```
# requirements.txt（核心，必装）
torch>=2.0
torchvision
opencv-python
Pillow
numpy
scipy
pyyaml
openai>=1.0

# requirements-optional.txt（按启用的模型按需装）
# TransUNet: 无额外依赖
# UltraFedFM: albumentations, segmentation_models_pytorch
# MedSegX: 见 infer_medsegx/requirements.txt
# MedSAM2: 见 infer_medsam2/requirements.txt
# MedSigLIP: timm, transformers
# BiomedCLIP: open_clip_torch, safetensors
# AutoGluon (分类或裁判): autogluon.tabular>=1.0, pyradiomics, SimpleITK, scikit-learn, pandas
```

### 7.2 L2 模型的路径管理

L2 模型需要访问 `my_Thyroid_infer/infer_xxx/` 下的 `model.py` / `networks/`。两种策略：

**策略 1（推荐）：把独立包作为子模块**
- 把 `my_Thyroid_infer/` 作为 git submodule 或软链接到 `ThyroidCascadeAgent/external/infer_xxx/`
- adapter 通过相对路径 import

**策略 2：环境变量配置路径**
```yaml
segmentation:
  external_infer_root: "/Users/wangbd/sysu/my_Thyroid_infer"  # L2 模型查找根
```
adapter 在 `load_model()` 内 `sys.path.insert(0, external_infer_root + "/infer_medsegx")`。

### 7.3 MedSegX 的特殊问题

MedSegX 需要 `task_name`（`US_GlndThyroid` 或 `US_ThyroidNodule`）来解析模态/器官 embedding。在 cascade pipeline 中：
- 分割结节 → `task_name="US_ThyroidNodule"`
- 分割腺体 → `task_name="US_GlndThyroid"`
- 这个字段必须在 config 中为每个 MedSegX 模型显式配置

### 7.4 AutoGluon 的双重角色

同一个 AutoGluon radiomics 模型在 pipeline 中扮演两个角色：
- **分割阶段**：`RadiomicsJudge`（GT-trained，评估 pred mask 可信度）
- **分类阶段**：`AutoGluonRadiomicsModel`（作为分类模型之一）

两者的 pyradiomics 配置必须完全一致（特征列对齐）。建议：
- `radiomics_judge.radiomics_params` 和 `classification.models[type=autogluon_radiomics].radiomics_params` 指向同一个 YAML
- 或在 `shared/radiomics_config.py` 中统一管理

### 7.5 confidence_map 的统一性

- TransUNet 输出多类 softmax，需在 adapter 中取前景类（`pred_resized[..., 1]`）作为 confidence_map
- MedSegX 的 mask_pred 是 `[num_obj, 1, H, W]`，需取 `iou_pred.argmax` 选中的那个 mask 的 sigmoid 概率
- MedSAM2 的 logits 直接 sigmoid
- 所有 confidence_map 最终 resize 回原图尺寸（`cv2.INTER_LINEAR`）

### 7.6 输入图像通道转换

- TransUNet 需灰度：`gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)`
- MedSigLIP 输入虽是三通道，但来自灰度复制：`rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)` —— 若输入已是 RGB，可直接用
- 所有转换在子类 `preprocess` 内完成，对外契约不变

---

## 八、实施步骤建议

### Phase A：补充分类层基础（前置依赖）
完成 BUILD_PLAN 的 Phase 3：`classification/base_model.py`、`model_registry.py`、`agent.py`、`soft_voting.py`、`calibration/runtime.py`。

### Phase B：L1 模型适配（4 个）
1. `segmentation/transunet_model.py` —— 复制 `infer_transunet/networks/` 到 `shared/model_architectures/transunet/`
2. `segmentation/ultrafedfm_model.py` —— 复制 `segmentation_models_pytorch` 到 `shared/` 或作为依赖
3. `classification/dino_unet_model.py` —— BUILD_PLAN 已规划
4. 每个写单元测试：假 image → predict → 验证 `SegModelOutput` / `ClsModelOutput` 字段

### Phase C：L2 模型适配（5 个）
1. 建 `external/` 目录或配置 `external_infer_root` 路径
2. `segmentation/medsegx_model.py`、`medsam2_model.py`
3. `classification/medsiglip_model.py`、`biomedclip_model.py`、`autogluon_radiomics_model.py`
4. 每个 adapter 内 lazy import + 调用独立包的 model 类

### Phase D：模型工厂与入口改造
1. `segmentation/model_factory.py`、`classification/model_factory.py`
2. 改造 `run_seg.py` / `run_cls.py` / `run_pipeline.py` 用工厂构建模型
3. 扩展 `config.yaml` 到多模型结构

### Phase E：LLM Prompt 扩展（可选）
- 当前 `format_predictions_for_agent` 假设所有模型条目字段一致
- 多模型场景下，不同模型的 `metadata` 字段不同（如 MedSegX 有 `task_name`）
- 需在 prompt 中只暴露对 LLM 决策有用的统一字段（`base_dataset_performance` / `device_match` / `ece` / `morphology` / `judge_scores`），特有字段藏到 `metadata` 不进 prompt

---

## 九、自检：需求覆盖

| 需求 | 覆盖位置 |
|---|---|
| 分割层接收 5 个模型输出 | 第四章 4.1 表 + `SegModelRegistry.predict_all` 不变 |
| 分类层接收 4 个模型输出 | 第四章 4.2 表 + `ClsModelRegistry.predict_all` 不变 |
| 不破坏现有架构契约 | 第一章 1.3 表 |
| 依赖按需启用 | 第七章 7.1 |
| 配置统一管理 | 第五章 |
| 可扩展新模型 | 第六章工厂模式 |
