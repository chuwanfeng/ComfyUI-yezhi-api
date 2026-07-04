"""
站点统计 API
GET /api/stats
"""
from flask import Blueprint, jsonify
from services.db import get_db_session
from models.generation import SiteStats

stats_bp = Blueprint("stats", __name__, url_prefix="/api/stats")


@stats_bp.route("", methods=["GET"])
def get_stats():
    """获取站点统计"""
    db = get_db_session()
    try:
        stats = db.query(SiteStats).filter(SiteStats.id == 1).first()
        if not stats:
            return jsonify({
                "totalGenerations": 0,
                "dailyGenerations": 0,
            })
        return jsonify({
            "totalGenerations": stats.total_generations,
            "dailyGenerations": stats.daily_generations,
        })
    finally:
        db.close()
