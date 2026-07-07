"""
ComfyUI API 客户端
发送 prompt → 轮询结果 → 返回图像 base64
全局单例 requests.Session，避免连接泄漏
"""
import time
import json
from typing import Optional
import requests


# ── 全局连接池，进程生命周期内不复建 ──
_shared_session: Optional[requests.Session] = None


def _get_session() -> requests.Session:
    global _shared_session
    if _shared_session is None:
        _shared_session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=5,
            pool_maxsize=10,
            max_retries=1,
            pool_block=False,
        )
        _shared_session.mount("http://", adapter)
        _shared_session.mount("https://", adapter)
    return _shared_session


class ComfyUIClient:
    """ComfyUI /prompt API 封装 — 共享连接池"""

    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip("/")
        self._session = _get_session()

    def _call(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self.server_url}{path}"
        resp = self._session.request(method, url, timeout=30, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def queue_prompt(self, workflow: dict) -> str:
        """提交 workflow，返回 prompt_id"""
        result = self._call("POST", "/prompt", json={"prompt": workflow})
        return result["prompt_id"]

    def upload_image(self, image_data: bytes, filename: str = None) -> str:
        return self.upload_file(image_data, filename)

    def upload_file(self, file_data: bytes, filename: str = None) -> str:
        """
        通用文件上传到 ComfyUI input/ 目录，返回 ComfyUI 保存的文件名。
        自动去重：用文件内容 MD5 做文件名 + 上传前检查服务端是否已存在。
        """
        import io, hashlib
        md5 = hashlib.md5(file_data).hexdigest()[:12]
        if filename is None:
            filename = f"yezhi_{md5}.bin"
        else:
            base, ext = filename.rsplit(".", 1) if "." in filename else (filename, "bin")
            filename = f"{base}_{md5}.{ext}"

        if self._input_file_exists(filename):
            return filename

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
        mime_map = {
            "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "webp": "image/webp", "gif": "image/gif", "bmp": "image/bmp",
            "mp3": "audio/mpeg", "wav": "audio/wav", "m4a": "audio/mp4",
            "aac": "audio/aac", "ogg": "audio/ogg", "flac": "audio/flac",
            "mp4": "video/mp4", "webm": "video/webm",
        }
        mime = mime_map.get(ext, "application/octet-stream")

        resp = self._session.post(
            f"{self.server_url}/upload/image",
            files={"image": (filename, io.BytesIO(file_data), mime)},
            data={"overwrite": "true"},
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()
        return result.get("name", filename)

    def _input_file_exists(self, filename: str) -> bool:
        try:
            resp = self._session.get(
                f"{self.server_url}/view",
                params={"filename": filename, "type": "input", "subfolder": ""},
                timeout=10,
            )
            return resp.status_code == 200 and len(resp.content) > 0
        except Exception:
            return False

    def get_history(self, prompt_id: str) -> dict:
        return self._call("GET", f"/history/{prompt_id}")

    def _extract_media(self, outputs: dict) -> list[dict]:
        results = []
        for node_id, node_output in outputs.items():
            if "images" in node_output:
                for img in node_output["images"]:
                    data = self._get_media_data(img)
                    if data:
                        filename = img.get("filename", "")
                        ext = filename.rsplit(".", 1)[-1] if "." in filename else "png"
                        is_video = ext.lower() in ("mp4", "webm", "avi", "mov")
                        results.append({"type": "video" if is_video else "image", "data": data, "ext": ext})
            if "gifs" in node_output:
                for vid in node_output["gifs"]:
                    data = self._get_media_data(vid)
                    if data:
                        filename = vid.get("filename", "")
                        ext = filename.rsplit(".", 1)[-1] if "." in filename else "mp4"
                        results.append({"type": "video", "data": data, "ext": ext})
        return results

    def _get_media_data(self, item: dict) -> Optional[bytes]:
        filename = item.get("filename")
        subfolder = item.get("subfolder", "")
        media_type = item.get("type", "output")

        if filename:
            params = {"filename": filename, "subfolder": subfolder, "type": media_type}
            resp = self._session.get(
                f"{self.server_url}/view", params=params, timeout=120
            )
            resp.raise_for_status()
            return resp.content
        return None

    def generate_media(self, workflow: dict, timeout: int = 300) -> list[dict]:
        prompt_id = self.queue_prompt(workflow)
        return self.wait_for_result(prompt_id, timeout=timeout)

    def wait_for_result(
        self, prompt_id: str, timeout: int = 300, poll_interval: float = 1.0
    ) -> list[dict]:
        start = time.time()
        while time.time() - start < timeout:
            history = self.get_history(prompt_id)
            if prompt_id in history and "outputs" in history[prompt_id]:
                outputs = history[prompt_id]["outputs"]
                return self._extract_media(outputs)
            time.sleep(poll_interval)
        raise TimeoutError(f"ComfyUI generation timeout after {timeout}s")
