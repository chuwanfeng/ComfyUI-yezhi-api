"""
ComfyUI-Yezhi-API — Flask 应用入口
轻量级 ComfyUI 前端 + REST API
"""
from flask import Flask
from flask_cors import CORS
import config


def create_app() -> Flask:
    app = Flask(__name__,
                template_folder="templates",
                static_folder="static",
                static_url_path="/static")

    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["JSON_AS_ASCII"] = False

    CORS(app, supports_credentials=True)

    # ── 数据库初始化 ──────────────────────
    from services.db import init_db
    with app.app_context():
        init_db()
        
        # 初始化默认前端设置
        try:
            from services.settings_api import init_default_settings
            init_default_settings()
        except Exception as e:
            print(f"[WARN] Failed to init default settings: {e}")

    # ── 蓝图注册 ──────────────────────────
    from services.auth_api import auth_bp
    from services.generation_api import gen_bp
    from services.model_api import model_bp
    from services.upload_api import upload_bp
    from services.prompt_api import prompt_bp
    from services.stats_api import stats_bp
    from services.user_api import user_bp
    from services.points_api import points_bp
    from services.community_api import community_bp
    from services.admin_api import admin_bp
    from services.workflow_api import workflow_bp
    from services.settings_api import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(gen_bp)
    app.register_blueprint(model_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(prompt_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(points_bp)
    app.register_blueprint(community_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(workflow_bp)
    app.register_blueprint(settings_bp)

    # ── 前端入口 ──────────────────────────
    from flask import render_template

    @app.route("/")
    def index():
        return render_template("index.html")

    # ── 静态文件: 上传目录 ────────────────
    from flask import send_from_directory, request as flask_request, Response
    import os as _os

    @app.route("/uploads/<path:filename>")
    def serve_uploads(filename):
        filepath = _os.path.join(config.UPLOAD_DIR, filename)
        if not _os.path.isfile(filepath):
            return {"error": "file not found"}, 404
        # 视频文件显式设置 MIME + Accept-Ranges 以支持浏览器 seek
        ext = _os.path.splitext(filename)[1].lower()
        mime_map = {".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime", ".avi": "video/x-msvideo"}
        mimetype = mime_map.get(ext)
        if mimetype:
            range_header = flask_request.headers.get("Range")
            if range_header:
                import re as _re
                size = _os.path.getsize(filepath)
                match = _re.match(r"bytes=(\d+)-(\d*)", range_header)
                if match:
                    start = int(match.group(1))
                    end = int(match.group(2)) if match.group(2) else size - 1
                    end = min(end, size - 1)
                    length = end - start + 1
                    with open(filepath, "rb") as f:
                        f.seek(start)
                        data = f.read(length)
                    resp = Response(data, 206, mimetype=mimetype, direct_passthrough=True)
                    resp.headers["Content-Range"] = f"bytes {start}-{end}/{size}"
                    resp.headers["Accept-Ranges"] = "bytes"
                    resp.headers["Content-Length"] = str(length)
                    return resp
            return send_from_directory(config.UPLOAD_DIR, filename, mimetype=mimetype)
        return send_from_directory(config.UPLOAD_DIR, filename)

    # ── 健康检查 ──────────────────────────
    @app.route("/api/health")
    def health():
        return {"status": "ok", "self_hosted": config.SELF_HOSTED_MODE}

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
        threaded=True,
    )
