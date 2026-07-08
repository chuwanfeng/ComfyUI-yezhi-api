"""
模型列表 API — 从 workflow 表动态读取
仅返回 is_builtin=True 的内置工作流
"""
from flask import Blueprint, jsonify
from services.db import get_db_session
from models.workflow import Workflow
from services.workflow_api import _analyze_workflow_json
import config

model_bp = Blueprint("models", __name__, url_prefix="/api/models")


def _workflow_to_model(wf: Workflow, db) -> dict:
    """将 Workflow 记录转为前端 model 格式"""
    import json, os
    from flask import current_app
    from services.workflow_api import _load_workflow_json

    # 加载并分析 JSON（复用 workflow_api 共享方法）
    analysis = {"is_video": False, "requires_image": False, "requires_audio": False,
                "min_images": 0, "is_image_edit": False, "tags": []}
    try:
        wf_json = _load_workflow_json(wf.json_path)
        analysis = _analyze_workflow_json(wf_json)
    except Exception:
        pass

    tag = analysis["tags"][0] if analysis["tags"] else ""

    return {
        "id": wf.id,
        "name": wf.name,
        "cover": wf.cover_url or f"/static/models/{wf.id}.svg",
        "description": wf.description or "",
        "isRecommended": False,
        "isAvailable": True,
        "isText2Image": not analysis["is_video"] and not analysis["is_image_edit"],
        "isImageEdit": analysis["is_image_edit"],
        "isVideo": analysis["is_video"],
        "tag": tag,
        "requiresImage": analysis["requires_image"],
        "requiresAudio": analysis["requires_audio"],
        "minImages": analysis["min_images"],
        "requiresLogin": False,
        "normalSteps": 20,
        "maxSteps": 40,
        "tags": [tag],
        "allowedRatios": [],
        "ratioSizes": {},
        "_type": "workflow",
    }


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
