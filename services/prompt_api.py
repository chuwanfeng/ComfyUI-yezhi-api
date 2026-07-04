"""
提示词优化 API
POST /api/optimize-prompt
"""
from flask import Blueprint, request, jsonify
from utils.prompt_optimizer import optimize_prompt

prompt_bp = Blueprint("prompt", __name__, url_prefix="/api/optimize-prompt")


@prompt_bp.route("", methods=["POST"])
def optimize():
    """用 LLM 优化提示词"""
    data = request.get_json() or {}
    prompt = (data.get("prompt") or "").strip()
    model_id = data.get("model_id")

    if not prompt:
        return jsonify({"error": "提示词不能为空"}), 400

    result = optimize_prompt(prompt, model_id)
    return jsonify(result)
