"""
模型列表 API — 从 workflow 表动态读取
仅返回 is_builtin=True 的内置工作流
"""
from flask import Blueprint, jsonify
from services.db import get_db_session
from models.workflow import Workflow
import config

model_bp = Blueprint("models", __name__, url_prefix="/api/models")


def _workflow_to_model(wf: Workflow, db) -> dict:
    """将 Workflow 记录转为前端 model 格式"""
    # 判断媒体类型：有 CreateVideo/SaveVideo 节点 → 视频
    is_video = False
    try:
        from flask import current_app
        import json, os
        json_path = os.path.join(
            current_app.root_path, 'workflows', wf.json_path
        ) if current_app else os.path.join('workflows', wf.json_path)
        if os.path.exists(json_path):
            with open(json_path, encoding='utf-8') as f:
                data = json.load(f)
            video_types = {
                "CreateVideo", "SaveVideo", "EmptyLTXVLatentVideo",
                "LTXVPreprocess", "LTXVConditioning"
            }
            for node in data.values():
                if node.get("class_type") in video_types:
                    is_video = True
                    break
    except Exception:
        pass

    return {
        "id": wf.id,
        "name": wf.name,
        "cover": wf.cover_url or "/static/models/homepage/demo.jpg",
        "description": wf.description or "",
        "isRecommended": False,
        "isAvailable": True,
        "isText2Image": not is_video,
        "isImageEdit": False,
        "isVideo": is_video,
        "requiresLogin": False,
        "normalSteps": 20,
        "maxSteps": 40,
        "tags": [],
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
