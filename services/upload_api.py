"""
文件上传 API
POST /api/upload — 接收图片/文件，返回访问路径
"""
from flask import Blueprint, request, jsonify
from utils.storage import save_upload

upload_bp = Blueprint("upload", __name__, url_prefix="/api/upload")


@upload_bp.route("", methods=["POST"])
def upload():
    """接收文件上传，返回文件 URL"""
    if "file" not in request.files:
        return jsonify({"error": "未找到文件字段 'file'"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "请选择文件"}), 400

    subdir = request.form.get("subdir", "images")
    data = file.read()

    # 简单文件大小限制（50MB）
    if len(data) > 50 * 1024 * 1024:
        return jsonify({"error": "文件大小不能超过 50MB"}), 413

    url = save_upload(data, file.filename, subdir=subdir)
    return jsonify({"url": url, "filename": file.filename})
