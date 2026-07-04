"""
认证 API — 注册 / 登录 / 邮箱验证 / 重置密码
"""
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from sqlalchemy import select

from services.db import get_db_session
from models.user import User, Account, Verification
from utils.auth import create_token, decode_token, get_user_id_from_request
from utils.profanity_filter import contains_profanity, filter_profanity
import bcrypt

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _now():
    return datetime.now(timezone.utc)


# ── 注册 ─────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")
    nickname = (data.get("nickname") or "").strip()

    if not email or not password:
        return jsonify({"error": "邮箱和密码不能为空"}), 400
    if len(password) < 6:
        return jsonify({"error": "密码至少6位"}), 400

    db = get_db_session()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return jsonify({"error": "该邮箱已注册"}), 409

        # 敏感词检查（自用模式自动放行）
        if nickname and contains_profanity(nickname):
            return jsonify({"error": "昵称包含违规内容"}), 400

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        user = User(
            email=email,
            name=nickname or email.split("@")[0],
            nickname=filter_profanity(nickname) if nickname else None,
            last_login_at=_now(),
        )
        db.add(user)
        db.flush()  # 触发 gen_id，填充 user.id
        acc = Account(
            account_id=email,
            provider_id="credential",
            user_id=user.id,
            password_hash=hashed.decode(),
        )
        db.commit()

        token = create_token(user.id, {"email": email})
        return jsonify({
            "token": token,
            "user": _user_dict(user),
        }), 201
    finally:
        db.close()


# ── 登录 ─────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "邮箱和密码不能为空"}), 400

    db = get_db_session()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return jsonify({"error": "邮箱或密码错误"}), 401
        if user.banned:
            return jsonify({"error": f"账号已被封禁: {user.ban_reason or '无原因'}"}), 403

        acc = db.query(Account).filter(
            Account.user_id == user.id,
            Account.provider_id == "credential",
        ).first()
        if not acc or not acc.password_hash:
            return jsonify({"error": "该账号未设置密码"}), 401

        if not bcrypt.checkpw(password.encode(), acc.password_hash.encode()):
            return jsonify({"error": "邮箱或密码错误"}), 401

        user.last_login_at = _now()
        db.commit()

        token = create_token(user.id, {"email": email})
        return jsonify({
            "token": token,
            "user": _user_dict(user),
        })
    finally:
        db.close()


# ── 获取当前用户 ─────────────────────────────
@auth_bp.route("/me", methods=["GET"])
def me():
    user_id = get_user_id_from_request(request)
    if not user_id:
        return jsonify({"error": "未登录"}), 401

    db = get_db_session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "用户不存在"}), 404
        if user.banned:
            return jsonify({"error": f"账号已被封禁"}), 403
        return jsonify({"user": _user_dict(user)})
    finally:
        db.close()


# ── 修改密码 ─────────────────────────────────
@auth_bp.route("/change-password", methods=["POST"])
def change_password():
    user_id = get_user_id_from_request(request)
    if not user_id:
        return jsonify({"error": "未登录"}), 401

    data = request.get_json() or {}
    old_pw = data.get("old_password", "")
    new_pw = data.get("new_password", "")

    if len(new_pw) < 6:
        return jsonify({"error": "新密码至少6位"}), 400

    db = get_db_session()
    try:
        acc = db.query(Account).filter(
            Account.user_id == user_id,
            Account.provider_id == "credential",
        ).first()
        if not acc:
            return jsonify({"error": "该账号没有密码"}), 400

        if not bcrypt.checkpw(old_pw.encode(), acc.password_hash.encode()):
            return jsonify({"error": "原密码错误"}), 400

        acc.password_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
        db.commit()
        return jsonify({"message": "密码修改成功"})
    finally:
        db.close()


# ── 更新资料 ─────────────────────────────────
@auth_bp.route("/profile", methods=["PUT"])
def update_profile():
    user_id = get_user_id_from_request(request)
    if not user_id:
        return jsonify({"error": "未登录"}), 401

    data = request.get_json() or {}
    db = get_db_session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "用户不存在"}), 404

        if "nickname" in data:
            nick = data["nickname"].strip()
            if contains_profanity(nick):
                return jsonify({"error": "昵称包含违规内容"}), 400
            user.nickname = filter_profanity(nick)
        if "signature" in data:
            sig = data["signature"].strip()
            if contains_profanity(sig):
                return jsonify({"error": "签名包含违规内容"}), 400
            user.signature = filter_profanity(sig)
        if "avatar" in data:
            user.avatar = data["avatar"]

        db.commit()
        return jsonify({"user": _user_dict(user)})
    finally:
        db.close()


def _user_dict(user: User) -> dict:
    return {
        "id": user.id,
        "uid": user.uid,
        "email": user.email,
        "name": user.name,
        "nickname": user.nickname,
        "avatar": user.avatar,
        "signature": user.signature,
        "isAdmin": user.is_admin,
        "isPremium": user.is_premium,
        "isSubscribed": user.is_subscribed,
        "subscriptionExpiresAt": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
        "emailVerified": user.email_verified,
        "banned": user.banned,
        "banReason": user.ban_reason,
        "createdAt": user.created_at.isoformat() if user.created_at else None,
    }
