"""
社区 API — 动态流 / 点赞 / 举报 / 标签
"""
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from services.db import get_db_session
from models.user import User
from models.generation import UserGeneratedImage
from models.community import CommunityLike, CommunityTag, ImageReport
from models.workflow import Workflow
from utils.auth import get_user_id_from_request

community_bp = Blueprint("community", __name__, url_prefix="/api/community")


def _now():
    return datetime.now(timezone.utc)


# ── 社区动态 ─────────────────────────────────
@community_bp.route("/feed", methods=["GET"])
def get_feed():
    """获取社区动态（瀑布流）"""
    db = get_db_session()
    try:
        limit = request.args.get("limit", 20, type=int)
        offset = request.args.get("offset", 0, type=int)
        tag = request.args.get("tag")

        query = (
            db.query(UserGeneratedImage)
            .filter(
                UserGeneratedImage.is_public == True,
                UserGeneratedImage.is_nsfw == False,
            )
            .order_by(UserGeneratedImage.created_at.desc())
        )

        if tag:
            # 同名工作流可能有多个（公用+私有），需匹配所有
            wfs = db.query(Workflow).filter(Workflow.name == tag).all()
            wf_ids = [w.id for w in wfs]
            if wf_ids:
                from sqlalchemy import or_
                query = query.filter(or_(
                    UserGeneratedImage.model_name.in_(wf_ids),
                    UserGeneratedImage.model_name == tag  # 兼容直接存名称的旧数据
                ))
            else:
                query = query.filter(UserGeneratedImage.model_name == tag)

        # 全量模型标签（不受分页影响）
        raw_tags = [
            r[0] for r in
            db.query(UserGeneratedImage.model_name)
            .filter(
                UserGeneratedImage.is_public == True,
                UserGeneratedImage.is_nsfw == False,
                UserGeneratedImage.model_name != None,
                UserGeneratedImage.model_name != "",
            )
            .distinct()
            .all()
        ]
        wf_map_tags = {}
        if raw_tags:
            for wf in db.query(Workflow).filter(Workflow.id.in_(raw_tags)).all():
                wf_map_tags[wf.id] = wf.name
        model_tags_list = sorted({wf_map_tags.get(t, t) for t in raw_tags})

        total = query.count()
        images = query.offset(offset).limit(limit).all()

        # 获取当前用户ID（可能未登录）
        current_user_id = get_user_id_from_request(request)

        # 预加载工作流名称映射
        wf_ids = {img.model_name for img in images if img.model_name}
        wf_map = {}
        if wf_ids:
            for wf in db.query(Workflow).filter(Workflow.id.in_(wf_ids)).all():
                wf_map[wf.id] = wf.name

        result = []
        for img in images:
            user = db.query(User).filter(User.id == img.user_id).first()
            like_count = (
                db.query(CommunityLike)
                .filter(CommunityLike.image_id == img.id)
                .count()
            )
            liked = False
            if current_user_id:
                liked = (
                    db.query(CommunityLike)
                    .filter(
                        CommunityLike.image_id == img.id,
                        CommunityLike.user_id == current_user_id,
                    )
                    .first()
                    is not None
                )
            tags = (
                db.query(CommunityTag)
                .filter(CommunityTag.image_id == img.id)
                .all()
            )

            result.append({
                "id": img.id,
                "userId": img.user_id,
                "userName": user.nickname or user.name if user else "匿名",
                "userAvatar": user.avatar if user else "/static/images/default-avatar.svg",
                "prompt": img.prompt,
                "imageUrl": img.image_url,
                "thumbnailUrl": (img.thumbnail_url if img.thumbnail_url and img.thumbnail_url != img.image_url else (None if (img.media_type or 'image') == 'video' else img.image_url)),
                "width": img.width,
                "height": img.height,
                "modelName": wf_map.get(img.model_name, img.model_name),
                "likeCount": like_count,
                "liked": liked,
                "reportCount": img.report_count or 0,
                "tags": [t.tag for t in tags],
                "createdAt": img.created_at.isoformat() if img.created_at else None,
                "mediaType": img.media_type or "image",
                "audioStartTime": img.audio_start_time,
                "audioDuration": img.audio_duration,
                "durationSeconds": img.duration_seconds,
                "fps": img.fps,
            })

        return jsonify({"images": result, "total": total, "modelTags": model_tags_list})
    finally:
        db.close()


# ── 点赞 / 取消点赞 ──────────────────────────
@community_bp.route("/likes/<image_id>", methods=["POST"])
def toggle_like(image_id: str):
    user_id = get_user_id_from_request(request)
    if not user_id:
        return jsonify({"error": "未登录"}), 401

    db = get_db_session()
    try:
        existing = (
            db.query(CommunityLike)
            .filter(
                CommunityLike.image_id == image_id,
                CommunityLike.user_id == user_id,
            )
            .first()
        )

        if existing:
            db.delete(existing)
            db.commit()
            return jsonify({"liked": False})
        else:
            like = CommunityLike(image_id=image_id, user_id=user_id)
            db.add(like)
            db.commit()
            return jsonify({"liked": True})
    finally:
        db.close()


# ── 举报 ────────────────────────────────────
@community_bp.route("/report", methods=["POST"])
def report_image():
    user_id = get_user_id_from_request(request)
    if not user_id:
        return jsonify({"error": "未登录"}), 401

    data = request.get_json() or {}
    image_id = data.get("image_id")
    reason = data.get("reason", "")

    if not image_id:
        return jsonify({"error": "image_id 不能为空"}), 400

    db = get_db_session()
    try:
        report = ImageReport(
            image_id=image_id,
            reporter_id=user_id,
            reason=reason,
        )
        db.add(report)

        # 更新举报计数
        img = db.query(UserGeneratedImage).filter(UserGeneratedImage.id == image_id).first()
        if img:
            img.report_count = (img.report_count or 0) + 1
        db.commit()

        return jsonify({"message": "举报已提交"})
    finally:
        db.close()
