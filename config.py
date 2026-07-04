"""
ComfyUI-Yezhi-API 配置管理
读取 .env + 环境变量，统一入口
"""
import os
from dotenv import load_dotenv

# 项目根目录（用于相对路径解析）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key, str(default)).lower()
    return val in ("true", "1", "yes", "on")


# ── 自用模式 ─────────────────────────────────
SELF_HOSTED_MODE = _bool("SELF_HOSTED_MODE", False)

# ── 核心 ─────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
_db_url = os.getenv("DATABASE_URL", "")
if not _db_url:
    _db_url = f"sqlite:///{os.path.join(BASE_DIR, 'yezhi.db').replace(chr(92), '/')}"
DATABASE_URL = _db_url
DEBUG = _bool("DEBUG", True)
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5090"))

# ── JWT ──────────────────────────────────────
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "72"))
JWT_ALGORITHM = "HS256"

# ── ComfyUI 模型端点 ─────────────────────────
COMIFY_MODEL_URLS = {
    "HiDream-full-fp8": os.getenv("HiDream_Fp8_URL", ""),
    "Flux-Dev": os.getenv("Flux_Dev_URL", ""),
    "Flux-Krea": os.getenv("Flux_Krea_URL", ""),
    "Flux-Kontext": os.getenv("Kontext_fp8_URL", ""),
    "Stable-Diffusion-3.5": os.getenv("Stable_Diffusion_3_5_URL", ""),
    "Qwen-Image": os.getenv("Qwen_Image_URL", ""),
    "Qwen-Image-Edit": os.getenv("Qwen_Image_Edit_URL", ""),
    "Wai-SDXL-V150": os.getenv("Wai_SDXL_V150_URL", ""),
    "Wai-SDXL-V170": os.getenv("Wai_SDXL_V170_URL", ""),
    "Z-Image": os.getenv("Z_IMAGE_URL", ""),
    "Z-Image-Turbo": os.getenv("Z_Image_Turbo_URL", ""),
    "Flux-2": os.getenv("Flux_2_URL", ""),
}

# ── LLM 提示词优化 ───────────────────────────
LLM_BASE_URL = os.getenv("PROMPT_OPTIMIZATION_BASE_URL", "")
LLM_API_KEY = os.getenv("PROMPT_OPTIMIZATION_API_KEY", "")
LLM_MODEL = os.getenv("PROMPT_OPTIMIZATION_MODEL", "Qwen/Qwen3-VL-8B-Instruct-FP8")
LLM_MAX_TOKENS = int(os.getenv("PROMPT_OPTIMIZATION_MAX_TOKENS", "2000"))

# ── 存储 ─────────────────────────────────────
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")  # local | oss
UPLOAD_DIR = os.path.join(BASE_DIR, os.getenv("UPLOAD_DIR", "uploads"))
OSS_AK = os.getenv("OSS_AK", "")
OSS_SK = os.getenv("OSS_SK", "")
OSS_BUCKET = os.getenv("OSS_BUCKET", "")
OSS_ENDPOINT = os.getenv("OSS_ENDPOINT", "")

# ── 支付宝 ───────────────────────────────────
ALIPAY_APP_ID = os.getenv("ALIPAY_APP_ID", "")
ALIPAY_PRIVATE_KEY = os.getenv("ALIPAY_PRIVATE_KEY", "")
ALIPAY_PUBLIC_KEY = os.getenv("ALIPAY_PUBLIC_KEY", "")
ALIPAY_NOTIFY_URL = os.getenv("ALIPAY_NOTIFY_URL", "")
ALIPAY_RETURN_URL = os.getenv("ALIPAY_RETURN_URL", "")

# ── 邮件 ─────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
