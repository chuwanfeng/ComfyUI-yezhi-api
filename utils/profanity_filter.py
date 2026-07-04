"""
敏感词过滤
SELF_HOSTED_MODE=true 时直接放行
"""
import config


def contains_profanity(text: str) -> bool:
    """检查文本是否包含敏感词"""
    if config.SELF_HOSTED_MODE:
        return False

    # TODO: 接入敏感词库/LLM审核
    return False


def filter_profanity(text: str) -> str:
    """过滤敏感词（替换为***）"""
    if config.SELF_HOSTED_MODE:
        return text

    # TODO: 实现敏感词替换
    return text
