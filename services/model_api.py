"""
模型列表 API — 从 workflow 表动态读取
仅返回 is_builtin=True 的内置工作流
"""
from flask import Blueprint, jsonify
from services.db import get_db_session
from models.workflow import Workflow
import config

model_bp = Blueprint("models", __name__, url_prefix="/api/models")


def _analyze_workflow(wf: Workflow) -> dict:
    """分析 workflow JSON，返回媒体类型、标签、所需参数"""
    import json, os
    from flask import current_app

    is_video = False
    load_image_count = 0
    has_audio = False
    image_edit = False

    try:
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
            audio_types = {"VHS_LoadAudioUpload"}
            edit_types = {"TextEncodeQwenImageEditPlus", "QwenImageEditProcessor"}

            for node in data.values():
                ct = node.get("class_type", "")
                if ct in video_types:
                    is_video = True
                if ct == "LoadImage":
                    load_image_count += 1
                if ct in audio_types:
                    has_audio = True
                if ct in edit_types:
                    image_edit = True
    except Exception:
        pass

    # 确定标签
    if is_video:
        if has_audio:
            tag = "音频驱动视频"
        elif load_image_count >= 2:
            tag = "图生视频"
        elif load_image_count >= 1:
            tag = "图生视频"
        else:
            tag = "文生视频"
    else:
        if image_edit or (load_image_count > 0 and not is_video):
            tag = "图像编辑"
        else:
            tag = "文生图"

    return {
        "is_video": is_video,
        "tag": tag,
        "requires_image": load_image_count > 0,
        "requires_audio": has_audio,
        "min_images": 2 if load_image_count >= 2 else (1 if load_image_count >= 1 else 0),
        "is_image_edit": image_edit,
    }


def _workflow_to_model(wf: Workflow, db) -> dict:
    """将 Workflow 记录转为前端 model 格式"""
    info = _analyze_workflow(wf)

    return {
        "id": wf.id,
        "name": wf.name,
        "cover": wf.cover_url or f"/static/models/{wf.id}.svg",
        "description": wf.description or "",
        "isRecommended": False,
        "isAvailable": True,
        "isText2Image": not info["is_video"] and not info["is_image_edit"],
        "isImageEdit": info["is_image_edit"],
        "isVideo": info["is_video"],
        "tag": info["tag"],
        "requiresImage": info["requires_image"],
        "requiresAudio": info["requires_audio"],
        "minImages": info["min_images"],
        "requiresLogin": False,
        "normalSteps": 20,
        "maxSteps": 40,
        "tags": [info["tag"]],
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
