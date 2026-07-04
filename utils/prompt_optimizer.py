"""
提示词优化 — 用 LLM 将中文提示词优化为英文
"""
import json
import requests
import config


def optimize_prompt(prompt: str, model_id: str = None) -> dict:
    """
    用 LLM 优化提示词
    返回 {"optimized": str, "negative": str}
    SELF_HOSTED_MODE 且未配置 LLM: 直接返回原文
    """
    if not config.LLM_BASE_URL or not config.LLM_API_KEY:
        if config.SELF_HOSTED_MODE:
            return {"optimized": prompt, "negative": ""}
        return {"optimized": prompt, "negative": ""}

    system_prompt = (
        "You are a professional AI art prompt engineer. "
        "Convert the user's Chinese/English prompt into a high-quality English prompt "
        "suitable for AI image generation. Add detail about lighting, composition, style, "
        "and quality keywords. Also provide a negative prompt. "
        "Respond in JSON format: {\"optimized\": \"...\", \"negative\": \"...\"}"
    )

    try:
        resp = requests.post(
            f"{config.LLM_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {config.LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": config.LLM_MAX_TOKENS,
                "temperature": 0.7,
                "response_format": {"type": "json_object"},
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return {
            "optimized": parsed.get("optimized", prompt),
            "negative": parsed.get("negative", ""),
        }
    except Exception:
        return {"optimized": prompt, "negative": ""}
