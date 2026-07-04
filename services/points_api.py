"""
积分 API — 余额 / 签到 / CDK / 套餐
"""
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from sqlalchemy import select
from services.db import get_db_session
from models.user import User
from models.points import UserPoints, UserPointsRecord, CDK, CDKRedemption, PointsPackage
from utils.auth import get_user_id_from_request

points_bp = Blueprint("points", __name__, url_prefix="/api/points")


def _now():
    return datetime.now(timezone.utc)


# ── 余额 ─────────────────────────────────────
@points_bp.route("/balance", methods=["GET"])
def get_balance():
    user_id = get_user_id_from_request(request)
    if not user_id:
        return jsonify({"balance": 0, "selfHosted": True})

    db = get_db_session()
    try:
        pts = db.query(UserPoints).filter(UserPoints.user_id == user_id).first()
        if not pts:
            return jsonify({"balance": 0})
        return jsonify({"balance": pts.balance})
    finally:
        db.close()


# ── 每日签到 ─────────────────────────────────
@points_bp.route("/award-daily", methods=["POST"])
def award_daily():
    user_id = get_user_id_from_request(request)
    if not user_id:
        return jsonify({"error": "未登录"}), 401

    db = get_db_session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "用户不存在"}), 404

        # 检查是否今天已签到
        today = _now().replace(hour=0, minute=0, second=0, microsecond=0)
        if user.last_daily_award_date and user.last_daily_award_date >= today:
            return jsonify({"error": "今日已签到", "retryAfter": "tomorrow"}), 400

        # 签到奖励 10 积分
        award = 10
        _add_points(db, user_id, award, source_type="daily_award", description="每日签到")

        user.last_daily_award_date = _now()
        db.commit()

        pts = db.query(UserPoints).filter(UserPoints.user_id == user_id).first()
        return jsonify({
            "awarded": award,
            "balance": pts.balance if pts else award,
        })
    finally:
        db.close()


# ── CDK 兑换 ─────────────────────────────────
@points_bp.route("/cdk/redeem", methods=["POST"])
def redeem_cdk():
    user_id = get_user_id_from_request(request)
    if not user_id:
        return jsonify({"error": "未登录"}), 401

    data = request.get_json() or {}
    code = (data.get("code") or "").strip().upper()

    if not code:
        return jsonify({"error": "CDK 不能为空"}), 400

    db = get_db_session()
    try:
        cdk = db.query(CDK).filter(CDK.code == code).first()
        if not cdk:
            return jsonify({"error": "无效的 CDK"}), 404
        if not cdk.is_active:
            return jsonify({"error": "CDK 已失效"}), 400
        if cdk.expires_at and cdk.expires_at < _now():
            return jsonify({"error": "CDK 已过期"}), 400
        if cdk.used_count >= cdk.max_uses:
            return jsonify({"error": "CDK 已达使用上限"}), 400

        # 检查是否已经兑换过
        existing = db.query(CDKRedemption).filter(
            CDKRedemption.cdk_id == cdk.id,
            CDKRedemption.user_id == user_id,
        ).first()
        if existing:
            return jsonify({"error": "你已经兑换过此 CDK"}), 400

        # 添加积分
        _add_points(db, user_id, cdk.points, source_type="cdk", source_id=cdk.id, description=f"CDK兑换: {cdk.code}")

        # 记录兑换
        redemption = CDKRedemption(
            cdk_id=cdk.id,
            user_id=user_id,
            points_awarded=cdk.points,
        )
        db.add(redemption)
        cdk.used_count += 1
        db.commit()

        pts = db.query(UserPoints).filter(UserPoints.user_id == user_id).first()
        return jsonify({
            "awarded": cdk.points,
            "balance": pts.balance if pts else cdk.points,
        })
    finally:
        db.close()


# ── 套餐列表 ─────────────────────────────────
@points_bp.route("/packages", methods=["GET"])
def list_packages():
    db = get_db_session()
    try:
        packages = (
            db.query(PointsPackage)
            .filter(PointsPackage.is_active == True, PointsPackage.show_on_frontend == True)
            .order_by(PointsPackage.sort_order)
            .all()
        )
        return jsonify({
            "packages": [
                {
                    "id": p.id,
                    "name": p.name,
                    "nameTag": p.name_tag,
                    "points": p.points,
                    "priceCents": p.price_cents,
                }
                for p in packages
            ]
        })
    finally:
        db.close()


def _add_points(db, user_id: str, amount: int, source_type: str, source_id: str = None, description: str = ""):
    """添加积分并记录"""
    pts = db.query(UserPoints).filter(UserPoints.user_id == user_id).first()
    if not pts:
        pts = UserPoints(user_id=user_id, balance=0, total_earned=0, total_spent=0)
        db.add(pts)
        db.flush()

    balance_before = pts.balance
    pts.balance += amount
    pts.total_earned += amount

    record = UserPointsRecord(
        user_id=user_id,
        amount=amount,
        balance_before=balance_before,
        balance_after=pts.balance,
        source_type=source_type,
        source_id=source_id,
        description=description,
    )
    db.add(record)
