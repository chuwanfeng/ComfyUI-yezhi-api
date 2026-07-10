"""
模型列表 API — 从 workflow 表动态读取
仅返回 is_builtin=True 的内置工作流
"""
from flask import Blueprint, jsonify
from services.db import get_db_session
from models.workflow import Workflow
from services.workflow_api import _workflow_to_dict
import config

model_bp = Blueprint("models", __name__, url_prefix="/api/models")


def _workflow_to_model(wf: Workflow, db) -> dict:
    """将 Workflow 记录转为前端 model 格式（复用 _workflow_to_dict）"""
    base = _workflow_to_dict(wf, include_json=False)
    # 前端 model 列表/详情需要的额外字段
    base["isRecommended"] = False
    base["isAvailable"] = True
    base["isText2Image"] = not base["isVideo"] and not base.get("isImageEdit", False)
    base["requiresLogin"] = False
    base["normalSteps"] = 20
    base["maxSteps"] = 40
    base["allowedRatios"] = []
    base["ratioSizes"] = {}
    base["_type"] = "workflow"
    # cover 字段兼容
    if not base.get("cover"):
        base["cover"] = f"/static/models/{wf.id}.svg"
    return base


@model_bp.route("", methods=["GET"])
def list_models():
    db = get_db_session()
    try:
        wfs = db.query(Workflow).filter(
            Workflow.is_builtin == True
        ).order_by(Workflow.name).all()

        models = [_workflow_to_model(wf, db) for wf in wfs]
        return jsonify({"models": models})
    finally:
        db.close()


@model_bp.route("/<model_id>", methods=["GET"])
def get_model(model_id: str):
    db = get_db_session()
    try:
        wf = db.query(Workflow).filter(Workflow.id == model_id).first()
        if not wf:
            return jsonify({"error": "模型/工作流不存在"}), 404
        return jsonify(_workflow_to_model(wf, db))
    finally:
        db.close()
