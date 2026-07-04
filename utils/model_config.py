"""
模型配置 — 15+ AI 图像/视频模型定义
完全复刻 Dreamifly 的 modelConfig.ts
"""
from typing import Optional
import config


class ModelConfig:
    """单个模型配置"""

    def __init__(
        self,
        id: str,
        name: str,
        image: str,
        description: str = "",
        use_i2i: bool = False,
        use_t2i: bool = True,
        max_images: int = 0,
        tags: list[str] = None,
        is_recommended: bool = False,
        requires_login: bool = False,
        homepage_cover: str = "/static/models/homepage/demo.jpg",
        normal_steps: int = None,
        high_steps: int = None,
        normal_res: int = None,
        high_res: int = None,
        allowed_ratios: list[str] = None,
        ratio_sizes: dict = None,
    ):
        self.id = id
        self.name = name
        self.image = image
        self.description = description
        self.use_i2i = use_i2i
        self.use_t2i = use_t2i
        self.max_images = max_images
        self.tags = tags or []
        self.is_recommended = is_recommended
        self.requires_login = requires_login
        self.homepage_cover = homepage_cover
        self.normal_steps = normal_steps
        self.high_steps = high_steps
        self.normal_res = normal_res
        self.high_res = high_res
        self.allowed_ratios = allowed_ratios or []
        self.ratio_sizes = ratio_sizes or {}
        self.is_available = False  # 运行时填充

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "image": self.image,
            "homepageCover": self.homepage_cover,
            "description": self.description,
            "useI2i": self.use_i2i,
            "useT2i": self.use_t2i,
            "maxImages": self.max_images,
            "tags": self.tags,
            "isRecommended": self.is_recommended,
            "isAvailable": self.is_available,
            "requiresLogin": self.requires_login,
            "normalSteps": self.normal_steps,
            "highSteps": self.high_steps,
            "normalRes": self.normal_res,
            "highRes": self.high_res,
            "allowedRatios": self.allowed_ratios,
            "ratioSizes": self.ratio_sizes,
        }


# ── 全部模型定义（仅厂商 API 模型）──────────
ALL_MODELS: list[ModelConfig] = [
    ModelConfig(
        id="Qwen-Image",
        name="Qwen-Image",
        image="/static/models/Qwen-Image.jpg",
        description="通义千问图像生成基础模型，基于MMDiT架构，20B参数。",
        use_t2i=True,
        tags=["chineseSupport"],
        is_recommended=True,
        normal_steps=10, high_steps=20,
        normal_res=1024 * 1024, high_res=1416 * 1416,
    ),
    ModelConfig(
        id="nano-banana-2",
        name="Nano Banana 2",
        image="/static/models/nano-banana-2.jpg",
        description="Google Gemini Flash 高效图像生成与编辑模型，支持文生图+图生图。",
        use_i2i=True,
        use_t2i=True,
        max_images=3,
        tags=["chineseSupport"],
        requires_login=True,
        allowed_ratios=["1:1", "4:3", "3:4", "16:9", "9:16"],
        ratio_sizes={
            "1:1": {"width": 1024, "height": 1024},
            "4:3": {"width": 1024, "height": 768},
            "3:4": {"width": 768, "height": 1024},
            "16:9": {"width": 1368, "height": 768},
            "9:16": {"width": 768, "height": 1368},
        },
    ),
]


def get_available_models() -> list[ModelConfig]:
    """获取可用模型列表
    自用模式: 返回全部模型
    正常模式: 仅返回已配置 ComfyUI 端点的模型
    """
    if config.SELF_HOSTED_MODE:
        for m in ALL_MODELS:
            m.is_available = True
        return list(ALL_MODELS)

    available = []
    for m in ALL_MODELS:
        url = config.COMIFY_MODEL_URLS.get(m.id, "")
        if url:
            m.is_available = True
            available.append(m)
    return available


def get_model_by_id(model_id: str) -> Optional[ModelConfig]:
    """按 ID 查找模型"""
    for m in ALL_MODELS:
        if m.id == model_id:
            return m
    return None
