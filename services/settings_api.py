"""
设置/配置 API — 前端动态配置 (除 env 外)
支持: 全局设置, 用户个性化设置
"""
import json
from flask import Blueprint, request, jsonify, g
from services.db import get_db
from models import Setting, UserSetting
from utils.auth import require_auth, optional_auth

settings_bp = Blueprint("settings", __name__, url_prefix="/api/settings")


# ═══════════════════════════════════════════════════
# 全局设置 (管理员可写, 所有人可读 public 的)
# ═══════════════════════════════════════════════════

@settings_bp.route("/public", methods=["GET"])
def get_public_settings():
    """获取公开的前端配置"""
    db = get_db()
    settings = db.query(Setting).filter(Setting.is_public == True).all()
    
    result = {}
    for s in settings:
        result[s.key] = _parse_value(s.value, s.value_type)
    
    return jsonify({"settings": result})


@settings_bp.route("/admin", methods=["GET"])
@require_auth
def get_all_settings():
    """获取所有设置 (仅管理员)"""
    if not g.current_user.is_admin:
        return jsonify({"error": "无权访问"}), 403
    
    db = get_db()
    settings = db.query(Setting).all()
    
    return jsonify({
        "settings": [_setting_to_dict(s) for s in settings],
    })


@settings_bp.route("/admin", methods=["POST"])
@require_auth
def create_or_update_setting():
    """创建或更新设置 (仅管理员)"""
    if not g.current_user.is_admin:
        return jsonify({"error": "无权访问"}), 403
    
    data = request.get_json() or {}
    key = data.get("key", "").strip()
    
    if not key:
        return jsonify({"error": "key 不能为空"}), 400
    
    db = get_db()
    setting = db.query(Setting).filter(Setting.key == key).first()
    
    value = data.get("value")
    value_type = data.get("value_type", "string")
    
    # 根据类型序列化
    if value_type == "json" and isinstance(value, (dict, list)):
        value = json.dumps(value)
    elif value_type == "bool":
        value = "true" if value else "false"
    else:
        value = str(value) if value is not None else ""
    
    if setting:
        setting.value = value
        setting.value_type = value_type
        setting.description = data.get("description", setting.description)
        setting.category = data.get("category", setting.category)
        setting.is_public = data.get("is_public", setting.is_public)
    else:
        setting = Setting(
            key=key,
            value=value,
            value_type=value_type,
            description=data.get("description", ""),
            category=data.get("category"),
            is_public=data.get("is_public", True),
        )
        db.add(setting)
    
    db.commit()
    
    return jsonify({
        "message": "设置已保存",
        "setting": _setting_to_dict(setting),
    })


@settings_bp.route("/admin/<key>", methods=["DELETE"])
@require_auth
def delete_setting(key: str):
    """删除设置 (仅管理员)"""
    if not g.current_user.is_admin:
        return jsonify({"error": "无权访问"}), 403
    
    db = get_db()
    setting = db.query(Setting).filter(Setting.key == key).first()
    
    if not setting:
        return jsonify({"error": "设置不存在"}), 404
    
    db.delete(setting)
    db.commit()
    
    return jsonify({"message": "设置已删除"})


# ═══════════════════════════════════════════════════
# 用户个性化设置
# ═══════════════════════════════════════════════════

@settings_bp.route("/user", methods=["GET"])
@require_auth
def get_user_settings():
    """获取当前用户的所有设置"""
    db = get_db()
    settings = db.query(UserSetting).filter(
        UserSetting.user_id == g.current_user.id
    ).all()
    
    result = {}
    for s in settings:
        result[s.key] = _parse_value(s.value, "string")
    
    return jsonify({"settings": result})


@settings_bp.route("/user/<key>", methods=["GET"])
@require_auth
def get_user_setting(key: str):
    """获取单个用户设置"""
    db = get_db()
    setting = db.query(UserSetting).filter(
        UserSetting.user_id == g.current_user.id,
        UserSetting.key == key,
    ).first()
    
    if not setting:
        return jsonify({"value": None})
    
    return jsonify({
        "key": key,
        "value": _parse_value(setting.value, "string"),
    })


@settings_bp.route("/user/<key>", methods=["PUT"])
@require_auth
def set_user_setting(key: str):
    """设置用户个性化配置"""
    data = request.get_json() or {}
    value = data.get("value")
    
    if value is not None and not isinstance(value, str):
        value = json.dumps(value)
    
    db = get_db()
    setting = db.query(UserSetting).filter(
        UserSetting.user_id == g.current_user.id,
        UserSetting.key == key,
    ).first()
    
    if setting:
        setting.value = value
    else:
        setting = UserSetting(
            user_id=g.current_user.id,
            key=key,
            value=value,
        )
        db.add(setting)
    
    db.commit()
    
    return jsonify({
        "message": "设置已保存",
        "key": key,
        "value": _parse_value(value, "string"),
    })


@settings_bp.route("/user/<key>", methods=["DELETE"])
@require_auth
def delete_user_setting(key: str):
    """删除用户设置"""
    db = get_db()
    setting = db.query(UserSetting).filter(
        UserSetting.user_id == g.current_user.id,
        UserSetting.key == key,
    ).first()
    
    if setting:
        db.delete(setting)
        db.commit()
    
    return jsonify({"message": "设置已删除"})


# ═══════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════

def _setting_to_dict(s: Setting) -> dict:
    """设置转字典"""
    return {
        "id": s.id,
        "key": s.key,
        "value": _parse_value(s.value, s.value_type),
        "value_type": s.value_type,
        "description": s.description,
        "category": s.category,
        "is_public": s.is_public,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def _parse_value(value: str, value_type: str):
    """根据类型解析值"""
    if value is None:
        return None
    
    if value_type == "int":
        try:
            return int(value)
        except:
            return 0
    elif value_type == "float":
        try:
            return float(value)
        except:
            return 0.0
    elif value_type == "bool":
        return value.lower() in ("true", "1", "yes", "on")
    elif value_type == "json":
        try:
            return json.loads(value)
        except:
            return {}
    else:
        return value


# ═══════════════════════════════════════════════════
# 初始化默认设置
# ═══════════════════════════════════════════════════

def init_default_settings():
    """初始化默认前端配置"""
    from services.db import get_db_session
    
    defaults = [
        # UI 设置
        {"key": "site.name", "value": "ComfyUI-Yezhi-API", "value_type": "string", "category": "ui", "is_public": True, "description": "站点名称"},
        {"key": "site.logo", "value": "/static/images/dreamifly-logo.jpg", "value_type": "string", "category": "ui", "is_public": True, "description": "站点 Logo"},
        {"key": "site.hero_title", "value": "通过AI释放你的无限想象力", "value_type": "string", "category": "ui", "is_public": True, "description": "首页主标题"},
        {"key": "site.hero_subtitle", "value": "只需一键！", "value_type": "string", "category": "ui", "is_public": True, "description": "首页副标题"},
        
        # 生成设置
        {"key": "generation.default_steps", "value": "28", "value_type": "int", "category": "generation", "is_public": True, "description": "默认生成步数"},
        {"key": "generation.max_steps", "value": "50", "value_type": "int", "category": "generation", "is_public": True, "description": "最大生成步数"},
        {"key": "generation.default_width", "value": "1024", "value_type": "int", "category": "generation", "is_public": True, "description": "默认宽度"},
        {"key": "generation.default_height", "value": "1024", "value_type": "int", "category": "generation", "is_public": True, "description": "默认高度"},
        {"key": "generation.allow_negative_prompt", "value": "true", "value_type": "bool", "category": "generation", "is_public": True, "description": "允许负面提示词"},
        {"key": "generation.enable_prompt_optimization", "value": "true", "value_type": "bool", "category": "generation", "is_public": True, "description": "启用提示词优化"},
        
        # 功能开关
        {"key": "features.community_enabled", "value": "true", "value_type": "bool", "category": "feature", "is_public": True, "description": "社区功能开关"},
        {"key": "features.user_workflows_enabled", "value": "true", "value_type": "bool", "category": "feature", "is_public": True, "description": "用户自定义工作流开关"},
        {"key": "features.public_gallery", "value": "true", "value_type": "bool", "category": "feature", "is_public": True, "description": "公开画廊"},
        
        # 限制设置
        {"key": "limits.guest_daily_quota", "value": "10", "value_type": "int", "category": "limit", "is_public": True, "description": "游客每日配额"},
        {"key": "limits.user_daily_quota", "value": "50", "value_type": "int", "category": "limit", "is_public": True, "description": "注册用户每日配额"},
        {"key": "limits.max_batch_size", "value": "4", "value_type": "int", "category": "limit", "is_public": True, "description": "最大批量生成数量"},
    ]
    
    with get_db_session() as db:
        for d in defaults:
            existing = db.query(Setting).filter(Setting.key == d["key"]).first()
            if not existing:
                setting = Setting(**d)
                db.add(setting)
        db.commit()
