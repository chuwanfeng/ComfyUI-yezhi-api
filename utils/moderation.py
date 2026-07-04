"""
内容审核 — 图片 & 文本审核
SELF_HOSTED_MODE=true 时直接放行
"""
import config


def check_image_safety(image_data: bytes) -> tuple[bool, str]:
    """
    检查图片安全性
    返回 (pass, reason)
    - SELF_HOSTED_MODE: 直接放行
    """
    if config.SELF_HOSTED_MODE:
        return True, "self_hosted_bypass"

    # TODO: 接入审核 API
    return True, "moderation_disabled"


def check_text_safety(text: str) -> tuple[bool, str]:
    """
    检查文本安全性（提示词/昵称/签名等）
    SELF_HOSTED_MODE: 直接放行
    """
    if config.SELF_HOSTED_MODE:
        return True, "self_hosted_bypass"

    # TODO: 接入敏感词过滤
    return True, "moderation_disabled"
