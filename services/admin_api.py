"""
管理员 API — 后台管理接口
"""
from flask import Blueprint, request, jsonify
from services.db import get_db_session
from models.user import User
from models.generation import UserGeneratedImage, SiteStats
from models.admin import ProfanityWord, IPBlacklist, UserLimitConfig
from utils.auth import get_user_id_from_request

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def _require_admin(request):
    """检查是否为管理员"""
    user_id = get_user_id_from_request(request)
    if not user_id:
        return None
    db = get_db_session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_admin:
            return None
        return user
    finally:
        db.close()


# ── 用户列表 ─────────────────────────────────
@admin_bp.route("/users", methods=["GET"])
def list_users():
    admin = _require_admin(request)
    if not admin:
        return jsonify({"error": "无权限"}), 403

    db = get_db_session()
    try:
        limit = request.args.get("limit", 50, type=int)
        offset = request.args.get("offset", 0, type=int)
        search = request.args.get("search", "")

        query = db.query(User).order_by(User.created_at.desc())
        if search:
            query = query.filter(
                (User.email.contains(search)) |
                (User.nickname.contains(search))
            )

        total = query.count()
        users = query.offset(offset).limit(limit).all()

        return jsonify({
            "users": [
                {
                    "id": u.id,
                    "uid": u.uid,
                    "email": u.email,
                    "nickname": u.nickname,
                    "banned": u.banned,
                    "banReason": u.ban_reason,
                    "isAdmin": u.is_admin,
                    "createdAt": u.created_at.isoformat() if u.created_at else None,
                }
                for u in users
            ],
            "total": total,
        })
    finally:
        db.close()


# ── 封禁/解封用户 ───────────────────────────
@admin_bp.route("/users/<user_id>/ban", methods=["POST"])
def toggle_ban(user_id: str):
    admin = _require_admin(request)
    if not admin:
        return jsonify({"error": "无权限"}), 403

    data = request.get_json() or {}
    reason = data.get("reason", "")

    db = get_db_session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "用户不存在"}), 404

        user.banned = not user.banned
        user.ban_reason = reason if reason else None
        db.commit()

        return jsonify({
            "banned": user.banned,
            "banReason": user.ban_reason,
        })
    finally:
        db.close()


# ── 敏感词管理 ───────────────────────────────
@admin_bp.route("/profanity-words", methods=["GET"])
def list_profanity():
    admin = _require_admin(request)
    if not admin:
        return jsonify({"error": "无权限"}), 403

    db = get_db_session()
    try:
        words = db.query(ProfanityWord).order_by(ProfanityWord.created_at.desc()).all()
        return jsonify({
            "words": [
                {"id": w.id, "word": w.word, "category": w.category, "isActive": w.is_active}
                for w in words
            ]
        })
    finally:
        db.close()


@admin_bp.route("/profanity-words", methods=["POST"])
def add_profanity():
    admin = _require_admin(request)
    if not admin:
        return jsonify({"error": "无权限"}), 403

    data = request.get_json() or {}
    word = (data.get("word") or "").strip()
    category = data.get("category", "general")

    if not word:
        return jsonify({"error": "敏感词不能为空"}), 400

    db = get_db_session()
    try:
        existing = db.query(ProfanityWord).filter(ProfanityWord.word == word).first()
        if existing:
            return jsonify({"error": "该词已存在"}), 409

        pw = ProfanityWord(word=word, category=category)
        db.add(pw)
        db.commit()
        return jsonify({"id": pw.id, "word": pw.word, "category": pw.category}), 201
    finally:
        db.close()


# ── IP 黑名单 ────────────────────────────────
@admin_bp.route("/blacklist/ip", methods=["GET"])
def list_ip_blacklist():
    admin = _require_admin(request)
    if not admin:
        return jsonify({"error": "无权限"}), 403

    db = get_db_session()
    try:
        entries = db.query(IPBlacklist).order_by(IPBlacklist.created_at.desc()).all()
        return jsonify({
            "entries": [
                {
                    "id": e.id,
                    "ipAddress": e.ip_address,
                    "reason": e.reason,
                    "createdAt": e.created_at.isoformat() if e.created_at else None,
                }
                for e in entries
            ]
        })
    finally:
        db.close()


# ── 内容审核（审核单张图片） ─────────────────
@admin_bp.route("/images/<image_id>/moderate", methods=["POST"])
def moderate_image(image_id: str):
    admin = _require_admin(request)
    if not admin:
        return jsonify({"error": "无权限"}), 403

    data = request.get_json() or {}
    action = data.get("action")  # approve, reject, mark_nsfw

    db = get_db_session()
    try:
        img = db.query(UserGeneratedImage).filter(UserGeneratedImage.id == image_id).first()
        if not img:
            return jsonify({"error": "作品不存在"}), 404

        if action == "reject":
            img.is_public = False
        elif action == "mark_nsfw":
            img.is_nsfw = True
        elif action == "approve":
            img.is_nsfw = False
            img.report_count = 0

        db.commit()
        return jsonify({"message": f"已执行: {action}"})
    finally:
        db.close()
