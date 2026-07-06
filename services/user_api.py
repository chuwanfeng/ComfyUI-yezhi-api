"""
用户作品 & 配额 API
"""
from flask import Blueprint, request, jsonify
from services.db import get_db_session
from models.user import User
from models.generation import UserGeneratedImage
from utils.auth import get_user_id_from_request

user_bp = Blueprint("user", __name__, url_prefix="/api/user")


@user_bp.route("/quota", methods=["GET"])
def get_quota():
    """获取用户配额（自用模式返回无限制）"""
    from config import SELF_HOSTED_MODE
    if SELF_HOSTED_MODE:
        return jsonify({
            "selfHosted": True,
            "dailyRemaining": -1,  # 无限制
            "dailyLimit": -1,
            "storageRemaining": -1,
        })

    user_id = get_user_id_from_request(request)
    if not user_id:
        return jsonify({
            "dailyRemaining": 0,
            "dailyLimit": 10,
        })

    db = get_db_session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "用户不存在"}), 404

        return jsonify({
            "selfHosted": False,
            "dailyRemaining": max(0, 50 - (user.daily_request_count or 0)),
            "dailyLimit": 50,
            "isSubscribed": user.is_subscribed,
        })
    finally:
        db.close()


@user_bp.route("/images", methods=["GET"])
def list_images():
    """获取用户自己的作品列表"""
    user_id = get_user_id_from_request(request)
    if not user_id:
        return jsonify({"images": [], "total": 0})

    db = get_db_session()
    try:
        limit = request.args.get("limit", 20, type=int)
        offset = request.args.get("offset", 0, type=int)

        query = (
            db.query(UserGeneratedImage)
            .filter(UserGeneratedImage.user_id == user_id)
            .order_by(UserGeneratedImage.created_at.desc())
        )
        total = query.count()

        # 全量模型标签（不受分页影响）
        model_tags = [
            r[0] for r in
            db.query(UserGeneratedImage.model_name)
            .filter(
                UserGeneratedImage.user_id == user_id,
                UserGeneratedImage.model_name != None,
                UserGeneratedImage.model_name != "",
            )
            .distinct()
            .all()
        ]
        model_tags.sort()

        images = query.offset(offset).limit(limit).all()

        return jsonify({
            "images": [_image_dict(img) for img in images],
            "total": total,
            "modelTags": model_tags,
        })
    finally:
        db.close()


@user_bp.route("/images/<image_id>", methods=["DELETE"])
def delete_image(image_id: str):
    """删除自己的作品（同时删除本地文件）"""
    user_id = get_user_id_from_request(request)
    if not user_id:
        return jsonify({"error": "未登录"}), 401

    db = get_db_session()
    try:
        img = (
            db.query(UserGeneratedImage)
            .filter(
                UserGeneratedImage.id == image_id,
                UserGeneratedImage.user_id == user_id,
            )
            .first()
        )
        if not img:
            return jsonify({"error": "作品不存在"}), 404

        # 删除本地文件
        _delete_image_file(img.image_url)
        if img.thumbnail_url and img.thumbnail_url != img.image_url:
            _delete_image_file(img.thumbnail_url)

        db.delete(img)
        db.commit()
        return jsonify({"message": "已删除"})
    finally:
        db.close()


@user_bp.route("/images/<image_id>/publish", methods=["POST"])
def publish_image(image_id: str):
    """将作品发布到社区"""
    user_id = get_user_id_from_request(request)
    if not user_id:
        return jsonify({"error": "未登录"}), 401

    db = get_db_session()
    try:
        img = (
            db.query(UserGeneratedImage)
            .filter(
                UserGeneratedImage.id == image_id,
                UserGeneratedImage.user_id == user_id,
            )
            .first()
        )
        if not img:
            return jsonify({"error": "作品不存在"}), 404

        img.is_public = not img.is_public
        db.commit()
        msg = "已取消发布" if not img.is_public else "已发布到社区"
        return jsonify({"message": msg, "isPublic": img.is_public})
    finally:
        db.close()


@user_bp.route("/images/<image_id>/thumbnail", methods=["POST"])
def update_thumbnail(image_id: str):
    """更新视频缩略图（前端截取当前帧上传）"""
    user_id = get_user_id_from_request(request)
    if not user_id:
        return jsonify({"error": "未登录"}), 401

    db = get_db_session()
    try:
        img = (
            db.query(UserGeneratedImage)
            .filter(
                UserGeneratedImage.id == image_id,
                UserGeneratedImage.user_id == user_id,
            )
            .first()
        )
        if not img:
            return jsonify({"error": "作品不存在"}), 404

        file = request.files.get("frame")
        if not file:
            return jsonify({"error": "缺少帧图片"}), 400

        frame_data = file.read()
        if len(frame_data) > 5 * 1024 * 1024:
            return jsonify({"error": "图片太大"}), 400

        # 删除旧缩略图（如果不等于 image_url）
        if img.thumbnail_url and img.thumbnail_url != img.image_url:
            _delete_image_file(img.thumbnail_url)

        from utils.storage import save_upload
        thumb_url = save_upload(frame_data, f"{image_id}_thumb.jpg", subdir="generations")
        img.thumbnail_url = thumb_url
        db.commit()

        return jsonify({"message": "封面已更新", "thumbnailUrl": thumb_url})
    finally:
        db.close()


def _image_dict(img: UserGeneratedImage) -> dict:
    # 根据宽高推断比例
    w, h = img.width or 1024, img.height or 1024
    from math import gcd
    g = gcd(w, h)
    ratio = f"{w//g}:{h//g}" if g else "1:1"

    return {
        "id": img.id,
        "userId": img.user_id,
        "modelName": img.model_name,
        "prompt": img.prompt,
        "negativePrompt": img.negative_prompt or "",
        "imageUrl": img.image_url,
        "thumbnailUrl": (img.thumbnail_url if img.thumbnail_url and img.thumbnail_url != img.image_url else (None if (img.media_type or 'image') == 'video' else img.image_url)),
        "width": img.width,
        "height": img.height,
        "ratio": ratio,
        "steps": img.steps or 28,
        "workflowId": img.workflow_id or "",
        "isPublic": img.is_public,
        "isNsfw": img.is_nsfw,
        "likes": img.report_count or 0,  # 实际应该 count likes
        "createdAt": img.created_at.isoformat() if img.created_at else None,
        "durationSeconds": img.duration_seconds,
        "fps": img.fps,
        "mediaType": img.media_type or "image",
        "audioStartTime": img.audio_start_time,
        "audioDuration": img.audio_duration,
    }


# ── 辅助: 删除本地图片文件 ────────────────
import os
import config

def _delete_image_file(url: str):
    """根据 URL (/uploads/...) 删除对应本地文件"""
    if not url or not url.startswith("/uploads/"):
        return
    filepath = os.path.join(config.BASE_DIR, url.lstrip("/"))
    try:
        if os.path.isfile(filepath):
            os.remove(filepath)
    except OSError:
        pass
