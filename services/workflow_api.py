"""
工作流管理 API
Workflow JSON 存储在文件系统（WORKFLOWS_DIR），数据库只存元数据
"""
import json
import os
from flask import Blueprint, request, jsonify, send_from_directory, g, current_app
from services.db import get_db_session
from models.workflow import Workflow, WorkflowTemplate
from models.user import User
from utils.auth import require_auth, optional_auth, get_user_id_from_request
import config

workflow_bp = Blueprint("workflows", __name__, url_prefix="/api/workflows")

# 工作流 JSON 存储目录
WORKFLOWS_DIR = os.path.join(os.path.dirname(__file__), "..", "workflows")
os.makedirs(WORKFLOWS_DIR, exist_ok=True)


# ── 节点类型常量（与 model_api._analyze_workflow 保持一致） ──
VIDEO_NODE_TYPES = {
    "CreateVideo", "SaveVideo", "EmptyLTXVLatentVideo",
    "LTXVPreprocess", "LTXVConditioning", "LTXVEmptyLatentVideo",
    "VideoLinearCFGGuidance", "VideoCombine", "VHS_VideoCombine",
}
AUDIO_NODE_TYPES = {"VHS_LoadAudioUpload"}
EDIT_NODE_TYPES = {"TextEncodeQwenImageEditPlus", "QwenImageEditProcessor"}


def _analyze_workflow_json(workflow_json: dict) -> dict:
    """分析工作流 JSON，返回 is_video / requires_image / requires_audio / tags 等"""
    is_video = False
    load_image_count = 0
    has_audio = False
    image_edit = False
    has_cfg = False
    has_denoise = False
    has_fps = False

    if isinstance(workflow_json, dict):
        for nid, node in workflow_json.items():
            if not isinstance(node, dict):
                continue
            ct = node.get("class_type", "")
            inputs = node.get("inputs", {})
            if ct in VIDEO_NODE_TYPES:
                is_video = True
            if ct == "LoadImage":
                load_image_count += 1
            if ct in AUDIO_NODE_TYPES:
                has_audio = True
            if ct in EDIT_NODE_TYPES:
                image_edit = True
            if ct in ("KSampler", "KSamplerAdvanced"):
                if "cfg" in inputs:
                    has_cfg = True
                if "denoise" in inputs:
                    has_denoise = True
            if "fps" in inputs or "frame_rate" in inputs:
                has_fps = True

    # 确定标签
    tags = []
    if is_video:
        if has_audio:
            tags.append("音频驱动视频")
        elif load_image_count >= 2:
            tags.append("图生视频")
        elif load_image_count >= 1:
            tags.append("图生视频")
        else:
            tags.append("文生视频")
    elif image_edit or (load_image_count > 0 and not is_video):
        tags.append("图像编辑")
    else:
        tags.append("文生图")

    return {
        "is_video": is_video,
        "requires_image": load_image_count > 0,
        "requires_audio": has_audio,
        "min_images": 2 if load_image_count >= 2 else (1 if load_image_count >= 1 else 0),
        "is_image_edit": image_edit,
        "has_cfg": has_cfg,
        "has_denoise": has_denoise,
        "has_fps": has_fps,
        "tags": tags,
    }


def _get_workflow_path(json_path: str) -> str:
    """获取 workflow JSON 文件的完整路径"""
    return os.path.join(WORKFLOWS_DIR, json_path)


def _save_workflow_json(workflow_id: str, workflow_json: dict, name: str = "") -> str:
    """保存 workflow JSON 到文件，返回相对路径。文件名 = 名称（sanitized）或 ID 兜底。"""
    if name:
        safe = "".join(c for c in name if c.isalnum() or c in " ()+-._")
        safe = safe.strip()[:60] or name[:60]
        filename = f"{safe}.json"
    else:
        filename = f"{workflow_id}.json"
    # 同名文件覆盖
    filepath = os.path.join(WORKFLOWS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(workflow_json, f, ensure_ascii=False, indent=2)
    return filename


def _load_workflow_json(json_path: str) -> dict:
    """从文件加载 workflow JSON"""
    filepath = _get_workflow_path(json_path)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Workflow file not found: {json_path}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def _delete_workflow_files(wf_id: str, json_path: str):
    """删除工作流关联文件：JSON + SVG 封面"""
    # 删 JSON 文件
    filepath = _get_workflow_path(json_path)
    if os.path.exists(filepath):
        os.remove(filepath)

    # 删 SVG 封面（由 _workflow_to_model 同步生成）
    svg_dir = os.path.join(
        current_app.root_path if current_app else '.',
        'static', 'models'
    )
    svg_path = os.path.join(svg_dir, f"{wf_id}.svg")
    if os.path.exists(svg_path):
        os.remove(svg_path)


def _auto_param_mapping(workflow_json: dict) -> str:
    """Auto-generate param_mapping from workflow JSON nodes
    
    覆盖常见节点类型，生成参数映射表：
    - prompt / negative_prompt : CLIPTextEncode
    - referenceImage_* : LoadImage
    - audio : VHS_LoadAudioUpload
    - width / height / duration : EmptyLatentImage / LTXVEmptyLatentVideo / EmptySD3LatentImage
    - steps / batch_size / cfg / denoise : KSampler / KSamplerAdvanced
    - fps : CreateVideo / SaveVideo / VideoCombine 等
    - seed : 由 generation_api._inject_user_params 自动注入，无需映射
    """
    if not isinstance(workflow_json, dict):
        return None
    mapping = {}
    prompt_count = 0
    for nid, node in workflow_json.items():
        if not isinstance(node, dict):
            continue
        ct = node.get("class_type", "")
        inputs = node.get("inputs", {})

        # ── Prompt / Negative Prompt ──
        if ct == "CLIPTextEncode" and "text" in inputs:
            if prompt_count == 0 and "prompt" not in mapping:
                mapping["prompt"] = {"node_id": nid, "field": "text"}
            elif prompt_count >= 1 and "negative_prompt" not in mapping:
                mapping["negative_prompt"] = {"node_id": nid, "field": "text"}
            prompt_count += 1

        # ── Reference Images ──
        elif ct == "LoadImage":
            existing = [k for k in mapping if k.startswith("referenceImage_")]
            key = f"referenceImage_{len(existing)}"
            mapping[key] = {"node_id": nid, "field": "image"}

        # ── Audio ──
        elif ct in AUDIO_NODE_TYPES:
            mapping["audio"] = {"node_id": nid, "field": "audio"}

        # ── Width / Height / Duration (Empty Latent nodes) ──
        elif ct in ("EmptyLatentImage", "LTXVEmptyLatentVideo", "EmptySD3LatentImage"):
            if "width" in inputs and "width" not in mapping:
                mapping["width"] = {"node_id": nid, "field": "width"}
                mapping["height"] = {"node_id": nid, "field": "height"}
            if "frames_number" in inputs and "duration" not in mapping:
                mapping["duration"] = {"node_id": nid, "field": "frames_number"}
            if "length" in inputs and "duration" not in mapping:
                mapping["duration"] = {"node_id": nid, "field": "length"}

        # ── KSampler: steps / batch_size / cfg / denoise ──
        elif ct in ("KSampler", "KSamplerAdvanced"):
            if "steps" in inputs and "steps" not in mapping:
                mapping["steps"] = {"node_id": nid, "field": "steps"}
            if "batch_size" in inputs and "batch_size" not in mapping:
                mapping["batch_size"] = {"node_id": nid, "field": "batch_size"}
            if "cfg" in inputs and "cfg" not in mapping:
                mapping["cfg_scale"] = {"node_id": nid, "field": "cfg"}
            if "denoise" in inputs and "denoise" not in mapping:
                mapping["denoise"] = {"node_id": nid, "field": "denoise"}

        # ── FPS (CreateVideo / SaveVideo / VideoCombine) ──
        elif ct in ("CreateVideo", "SaveVideo", "VideoCombine", "VHS_VideoCombine") and "fps" not in mapping:
            if "fps" in inputs:
                mapping["fps"] = {"node_id": nid, "field": "fps"}
            elif "frame_rate" in inputs:
                mapping["fps"] = {"node_id": nid, "field": "frame_rate"}

        # ── LTXV 系列 FPS 字段 ──
        elif "frame_rate" in inputs and "fps" not in mapping:
            mapping["fps"] = {"node_id": nid, "field": "frame_rate"}

        # ── Seed (KSampler noise_seed → 自动注入，但预设 entry 有助于引擎匹配) ──
        # 不显式添加，留给 _inject_user_params 自动扫描

    return json.dumps(mapping, ensure_ascii=False) if mapping else None


def _workflow_to_dict(wf: Workflow, include_json: bool = False) -> dict:
    """Workflow 转为 API 响应字典（含自动分析字段）"""
    # 加载并分析 JSON
    analysis = {"is_video": False, "requires_image": False, "requires_audio": False,
                "min_images": 0, "is_image_edit": False, "tags": []}
    try:
        wf_json = _load_workflow_json(wf.json_path)
        analysis = _analyze_workflow_json(wf_json)
    except Exception:
        pass

    result = {
        "id": wf.id,
        "user_id": wf.user_id,
        "name": wf.name,
        "description": wf.description,
        "cover_url": wf.cover_url,
        "cover": wf.cover_url,
        "json_path": wf.json_path,
        "comfyui_url": wf.comfyui_url,
        "param_mapping": json.loads(wf.param_mapping) if wf.param_mapping else {},
        "is_public": wf.is_public,
        "is_builtin": wf.is_builtin,
        "use_count": wf.use_count or 0,
        "created_at": wf.created_at.isoformat() if wf.created_at else None,
        "updated_at": wf.updated_at.isoformat() if wf.updated_at else None,
        # ── 分析字段（用于前端参数显隐）──
        "isVideo": analysis["is_video"],
        "requiresImage": analysis["requires_image"],
        "requiresAudio": analysis["requires_audio"],
        "minImages": analysis["min_images"],
        "isImageEdit": analysis["is_image_edit"],
        "tags": analysis["tags"],
        "tag": analysis["tags"][0] if analysis["tags"] else "",
    }
    if include_json:
        try:
            result["workflow_json"] = _load_workflow_json(wf.json_path)
        except FileNotFoundError:
            result["workflow_json"] = {}
    return result


# ── 公开列表（含当前用户私有）─────────────────────────
@workflow_bp.route("", methods=["GET"])
def list_workflows():
    """获取工作流列表（内置 + 公开 + 当前用户私有）"""
    db = get_db_session()
    try:
        user_id = get_user_id_from_request(request)

        if user_id:
            # 登录用户：看公开 + 内置 + 自己的
            query = db.query(Workflow).filter(
                (Workflow.is_public == True) |
                (Workflow.is_builtin == True) |
                (Workflow.user_id == user_id)
            )
        else:
            # 未登录：只看公开 + 内置
            query = db.query(Workflow).filter(
                (Workflow.is_public == True) | (Workflow.is_builtin == True)
            )

        # 过滤内置
        builtin_only = request.args.get("builtin") == "1"
        if builtin_only:
            query = query.filter(Workflow.is_builtin == True)

        workflows = query.order_by(Workflow.use_count.desc(), Workflow.created_at.desc()).limit(100).all()
        return jsonify({"workflows": [_workflow_to_dict(w) for w in workflows]})
    finally:
        db.close()


# ── 我的工作流（需登录）───────────────────────
@workflow_bp.route("/my", methods=["GET"])
@require_auth
def list_my_workflows():
    """获取当前用户的所有工作流"""
    db = get_db_session()
    try:
        workflows = db.query(Workflow).filter(
            Workflow.user_id == g.current_user.id
        ).order_by(Workflow.updated_at.desc()).all()
        return jsonify({"workflows": [_workflow_to_dict(w) for w in workflows]})
    finally:
        db.close()


# ── 详情 ───────────────────────────────
@workflow_bp.route("/<workflow_id>", methods=["GET"])
def get_workflow(workflow_id: str):
    """获取工作流详情（含 workflow_json）"""
    db = get_db_session()
    try:
        wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not wf:
            return jsonify({"error": "工作流不存在"}), 404

        # 非内置/非公开需验证所有权
        if not wf.is_public and not wf.is_builtin:
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"error": "无权访问"}), 403
            try:
                from utils.auth import decode_token
                payload = decode_token(auth[7:])
                if payload.get("sub") != wf.user_id:
                    return jsonify({"error": "无权访问"}), 403
            except:
                return jsonify({"error": "无权访问"}), 403

        return jsonify(_workflow_to_dict(wf, include_json=True))
    finally:
        db.close()


# ── 创建 ───────────────────────────────
@workflow_bp.route("", methods=["POST"])
@require_auth
def create_workflow():
    """创建新工作流"""
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    workflow_json = data.get("workflow_json")

    if not name or not workflow_json:
        return jsonify({"error": "名称和 workflow_json 不能为空"}), 400

    # 验证 JSON
    if isinstance(workflow_json, str):
        try:
            workflow_json = json.loads(workflow_json)
        except json.JSONDecodeError:
            return jsonify({"error": "workflow_json 格式错误"}), 400

    db = get_db_session()
    try:
        import uuid
        wf_id = uuid.uuid4().hex[:16]
        json_path = _save_workflow_json(wf_id, workflow_json, name)
        auto_mapping = _auto_param_mapping(workflow_json)

        wf = Workflow(
            id=wf_id,
            user_id=g.current_user.id,
            name=name,
            description=data.get("description", ""),
            cover_url=data.get("cover_url", ""),
            json_path=json_path,
            comfyui_url=data.get("comfyui_url", ""),
            param_mapping=data.get("param_mapping") or auto_mapping,
            is_public=data.get("is_public", False),
        )
        db.add(wf)
        db.commit()
        return jsonify({"workflow": _workflow_to_dict(wf, include_json=True), "message": "创建成功"}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# ── 导入（从 ComfyUI 导出 JSON）───────────────
@workflow_bp.route("/import", methods=["POST"])
@require_auth
def import_workflow():
    """从 ComfyUI 导出的 JSON 导入工作流"""
    data = request.get_json() or {}
    name = (data.get("name") or "").strip() or "导入的工作流"
    workflow_json = data.get("workflow_json")

    if not workflow_json:
        return jsonify({"error": "workflow_json 不能为空"}), 400

    if isinstance(workflow_json, str):
        try:
            workflow_json = json.loads(workflow_json)
        except json.JSONDecodeError:
            return jsonify({"error": "workflow_json 格式错误"}), 400

    db = get_db_session()
    try:
        import uuid
        wf_id = uuid.uuid4().hex[:16]
        json_path = _save_workflow_json(wf_id, workflow_json, name)
        auto_mapping = _auto_param_mapping(workflow_json)

        wf = Workflow(
            id=wf_id,
            user_id=g.current_user.id,
            name=name,
            description=data.get("description", ""),
            cover_url=data.get("cover_url", ""),
            json_path=json_path,
            comfyui_url=data.get("comfyui_url", ""),
            param_mapping=auto_mapping,
        )
        db.add(wf)
        db.commit()
        return jsonify({"workflow": _workflow_to_dict(wf, include_json=True), "message": "导入成功"}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# ── 更新 ───────────────────────────────
@workflow_bp.route("/<workflow_id>", methods=["PUT"])
@require_auth
def update_workflow(workflow_id: str):
    """更新工作流（仅所有者）"""
    db = get_db_session()
    try:
        wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not wf:
            return jsonify({"error": "工作流不存在"}), 404
        if wf.user_id != g.current_user.id and not g.current_user.is_admin:
            return jsonify({"error": "无权修改"}), 403

        data = request.get_json() or {}

        if "name" in data and data["name"]:
            wf.name = data["name"].strip()
        if "description" in data:
            wf.description = data["description"]
        if "cover_url" in data:
            wf.cover_url = data["cover_url"]
        if "comfyui_url" in data:
            wf.comfyui_url = data["comfyui_url"]
        if "param_mapping" in data:
            wf.param_mapping = data["param_mapping"]
        if "is_public" in data:
            wf.is_public = data["is_public"]

        # 更新 workflow JSON 文件（仅当有实际内容时）
        if "workflow_json" in data and data["workflow_json"]:
            wf_json = data["workflow_json"]
            if isinstance(wf_json, str):
                try:
                    wf_json = json.loads(wf_json)
                except json.JSONDecodeError:
                    return jsonify({"error": "workflow_json 格式错误"}), 400
            _save_workflow_json(wf.id, wf_json, wf.name)
            # 自动重新生成参数映射（除非前端显式传入）
            if "param_mapping" not in data:
                wf.param_mapping = _auto_param_mapping(wf_json)

        db.commit()
        return jsonify({"workflow": _workflow_to_dict(wf, include_json=True), "message": "保存成功"})
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# ── 删除 ───────────────────────────────
@workflow_bp.route("/<workflow_id>", methods=["DELETE"])
@require_auth
def delete_workflow(workflow_id: str):
    """删除工作流（仅所有者）"""
    db = get_db_session()
    try:
        wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not wf:
            return jsonify({"error": "工作流不存在"}), 404
        if wf.user_id != g.current_user.id and not g.current_user.is_admin:
            return jsonify({"error": "无权删除"}), 403

        # 删除工作流关联文件
        _delete_workflow_files(wf.id, wf.json_path)

        db.delete(wf)
        db.commit()
        return jsonify({"message": "已删除"})
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# ── 工作流 JSON 内容（供前端编辑用）──────
@workflow_bp.route("/<workflow_id>/json", methods=["GET"])
def get_workflow_json(workflow_id: str):
    """仅获取工作流的 JSON 内容"""
    db = get_db_session()
    try:
        wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not wf:
            return jsonify({"error": "工作流不存在"}), 404
        try:
            return jsonify({"workflow_json": _load_workflow_json(wf.json_path)})
        except FileNotFoundError:
            return jsonify({"error": "工作流文件丢失"}), 404
    finally:
        db.close()


# ── 下载 JSON 文件 ──────────────────────
@workflow_bp.route("/<workflow_id>/download", methods=["GET"])
def download_workflow(workflow_id: str):
    """下载工作流 JSON 文件（供 ComfyUI 导入）"""
    db = get_db_session()
    try:
        wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not wf:
            return jsonify({"error": "工作流不存在"}), 404

        try:
            wf_json = _load_workflow_json(wf.json_path)
        except FileNotFoundError:
            return jsonify({"error": "工作流文件丢失"}), 404

        return jsonify(wf_json)
    finally:
        db.close()
