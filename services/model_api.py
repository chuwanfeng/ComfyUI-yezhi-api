"""
模型列表 API
GET /api/models — 返回已配置端点的可用模型
"""
from flask import Blueprint, jsonify
from utils.model_config import get_available_models

model_bp = Blueprint("models", __name__, url_prefix="/api/models")


@model_bp.route("", methods=["GET"])
def list_models():
    """返回所有已配置端点的模型"""
    models = get_available_models()
    return jsonify({
        "models": [m.to_dict() for m in models]
    })


@model_bp.route("/<model_id>", methods=["GET"])
def get_model(model_id: str):
    """返回指定模型配置"""
    from utils.model_config import get_model_by_id
    m = get_model_by_id(model_id)
    if not m:
        return jsonify({"error": "模型不存在"}), 404
    return jsonify(m.to_dict())
