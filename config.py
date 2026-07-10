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

# ── ComfyUI 端点 ─────────────────────────────
# 全局兜底：内置工作流未单独配置 + 用户工作流未配置时使用
COMFYUI_BASE_URL = os.getenv("COMFYUI_BASE_URL", "")

# 内置工作流各自 ComfyUI URL（按 json_path 映射 -> 环境变量名）
# 为空则 fallback 到 COMFYUI_BASE_URL
_BUILTIN_WORKFLOW_URL_MAP = {
    "Ltx2.3-ia2v":               "COMFYUI_LTX23_IA2V_URL",
    "Ltx2.3-ia2v-原clip":        "COMFYUI_LTX23_IA2V_CLIP_URL",
    "Ltx2.3图生视频":            "COMFYUI_LTX23_I2V_URL",
    "Qwen-Rapid-AIO":            "COMFYUI_QWEN_RAPID_URL",
    "Z+Image双模型双采样手动提示词极致人体文生图": "COMFYUI_ZIMAGE_URL",
    "ltx2_3_flf2v_首尾帧":       "COMFYUI_LTX23_FLF2V_URL",
    "ltx2_3_flf2v_首尾帧_VBVR":  "COMFYUI_LTX23_FLF2V_VBVR_URL",
    "my_image_z_image_turbo":    "COMFYUI_ZIMAGE_TURBO_URL",
}

def get_builtin_workflow_url(json_path: str) -> str:
    """内置工作流：按 json_path 查对应 env var，为空 fallback 到 COMFYUI_BASE_URL"""
    env_key = _BUILTIN_WORKFLOW_URL_MAP.get(json_path, "")
    url = os.getenv(env_key, "") if env_key else ""
    return url or COMFYUI_BASE_URL

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
