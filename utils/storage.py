"""
文件存储 — local / OSS
SELF_HOSTED_MODE 不影响存储，仅影响限额
"""
import os
import uuid
import config


def save_upload(file_data: bytes, filename: str, subdir: str = "images") -> str:
    """保存上传文件，返回访问路径"""
    ext = os.path.splitext(filename)[1] or ".png"
    new_name = f"{uuid.uuid4().hex}{ext}"

    if config.STORAGE_TYPE == "oss":
        return _save_oss(file_data, new_name, subdir)
    else:
        return _save_local(file_data, new_name, subdir)


def _save_local(file_data: bytes, filename: str, subdir: str) -> str:
    """保存到本地文件系统"""
    upload_dir = os.path.join(config.UPLOAD_DIR, subdir)
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    with open(filepath, "wb") as f:
        f.write(file_data)
    return f"/uploads/{subdir}/{filename}"


def _save_oss(file_data: bytes, filename: str, subdir: str) -> str:
    """保存到阿里云 OSS"""
    import oss2
    auth = oss2.Auth(config.OSS_AK, config.OSS_SK)
    bucket = oss2.Bucket(auth, config.OSS_ENDPOINT, config.OSS_BUCKET)
    key = f"{subdir}/{filename}"
    bucket.put_object(key, file_data)
    return f"https://{config.OSS_BUCKET}.{config.OSS_ENDPOINT}/{key}"
