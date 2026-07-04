"""
JWT 认证工具
"""
from datetime import datetime, timedelta, timezone
import jwt
from functools import wraps

from flask import request, jsonify, g
from services.db import get_db_session
from models.user import User
import config


def create_token(user_id: str, extra: dict = None) -> str:
    """签发 JWT"""
    payload = {
        "sub": user_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=config.JWT_EXPIRE_HOURS),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """验证并解码 JWT，返回 payload"""
    return jwt.decode(token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM])


def get_user_id_from_request(request) -> str | None:
    """从 Flask request 中提取 user_id"""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    try:
        payload = decode_token(auth[7:])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(f):
    """需要登录装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = get_user_id_from_request(request)
        if not user_id:
            return jsonify({"error": "请先登录"}), 401
        db = get_db_session()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({"error": "用户不存在"}), 401
            if user.banned:
                return jsonify({"error": f"账号已封禁: {user.ban_reason or '未知'}"}), 403
            g.current_user = user
            return f(*args, **kwargs)
        finally:
            db.close()
    return decorated


def optional_auth(f):
    """可选登录装饰器（不强制登录）"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = get_user_id_from_request(request)
        if user_id:
            db = get_db_session()
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if user and not user.banned:
                    g.current_user = user
            except:
                pass
            finally:
                db.close()
        return f(*args, **kwargs)
    return decorated
