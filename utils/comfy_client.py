"""
ComfyUI API 客户端
发送 prompt → 轮询结果 → 返回图像 base64
"""
import uuid
import time
import json
import base64
import requests
from typing import Optional


class ComfyUIClient:
    """ComfyUI /prompt API 封装"""

    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip("/")
        self.ws_url = self.server_url.replace("http://", "ws://").replace("https://", "wss://")

    def _call(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self.server_url}{path}"
        resp = requests.request(method, url, timeout=30, **kwargs)
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
        图片/音频均走 POST /upload/image（ComfyUI 的 upload 端点对类型不严格校验）。
        自动去重：用文件内容 MD5 做文件名 + 上传前检查服务端是否已存在。
        """
        import io, hashlib
        md5 = hashlib.md5(file_data).hexdigest()[:12]
        if filename is None:
            filename = f"yezhi_{md5}.bin"
        else:
            base, ext = filename.rsplit(".", 1) if "." in filename else (filename, "bin")
            filename = f"{base}_{md5}.{ext}"

        # 去重：检查 ComfyUI 服务端是否已有同名文件
        if self._input_file_exists(filename):
            return filename

        # 根据扩展名推断 MIME
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
        mime_map = {
            "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "webp": "image/webp", "gif": "image/gif", "bmp": "image/bmp",
            "mp3": "audio/mpeg", "wav": "audio/wav", "m4a": "audio/mp4",
            "aac": "audio/aac", "ogg": "audio/ogg", "flac": "audio/flac",
            "mp4": "video/mp4", "webm": "video/webm",
        }
        mime = mime_map.get(ext, "application/octet-stream")

        url = f"{self.server_url}/upload/image"
        resp = requests.post(
            url,
            files={"image": (filename, io.BytesIO(file_data), mime)},
            data={"overwrite": "true"},
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()
        return result.get("name", filename)

    def _input_file_exists(self, filename: str) -> bool:
        """检查 ComfyUI input/ 目录是否已有该文件"""
        try:
            url = f"{self.server_url}/view"
            resp = requests.get(
                url,
                params={"filename": filename, "type": "input", "subfolder": ""},
                timeout=10,
            )
            return resp.status_code == 200 and len(resp.content) > 0
        except Exception:
            return False

    def get_history(self, prompt_id: str) -> dict:
        """获取历史记录"""
        return self._call("GET", f"/history/{prompt_id}")

    def wait_for_result(
        self,
        prompt_id: str,
        timeout: int = 300,
        poll_interval: float = 1.0,
    ) -> list[bytes]:
        """
        轮询等待 ComfyUI 完成生成，返回图像字节列表
        """
        start = time.time()
        while time.time() - start < timeout:
            history = self.get_history(prompt_id)
            if prompt_id in history and "outputs" in history[prompt_id]:
                outputs = history[prompt_id]["outputs"]
                return self._extract_images(outputs)
            time.sleep(poll_interval)
        raise TimeoutError(f"ComfyUI generation timeout after {timeout}s")

    def _extract_media(self, outputs: dict) -> list[dict]:
        """从 outputs 中提取所有媒体（图片 + 视频/GIF），返回 [{type:'image'|'video', data:bytes, ext:str}]"""
        results = []
        for node_id, node_output in outputs.items():
            # 普通图片 / 视频 (SaveVideo 也走 images key)
            if "images" in node_output:
                for img in node_output["images"]:
                    data = self._get_media_data(img)
                    if data:
                        filename = img.get("filename", "")
                        ext = filename.rsplit(".", 1)[-1] if "." in filename else "png"
                        is_video = ext.lower() in ("mp4", "webm", "avi", "mov")
                        results.append({"type": "video" if is_video else "image", "data": data, "ext": ext})
            # 视频/GIF (SaveVideo / CreateVideo / VHS_VideoCombine → 输出 key="gifs")
            if "gifs" in node_output:
                for vid in node_output["gifs"]:
                    data = self._get_media_data(vid)
                    if data:
                        filename = vid.get("filename", "")
                        ext = filename.rsplit(".", 1)[-1] if "." in filename else "mp4"
                        results.append({"type": "video", "data": data, "ext": ext})
        return results

    def _get_media_data(self, item: dict) -> Optional[bytes]:
        """获取单个媒体文件数据（图片/视频通用）"""
        filename = item.get("filename")
        subfolder = item.get("subfolder", "")
        media_type = item.get("type", "output")

        if filename:
            params = {"filename": filename, "subfolder": subfolder, "type": media_type}
            url = f"{self.server_url}/view"
            resp = requests.get(url, params=params, timeout=120)
            resp.raise_for_status()
            return resp.content
        return None

    def generate(
        self,
        workflow: dict,
        timeout: int = 300,
    ) -> list[bytes]:
        """
        一键生成：提交 workflow → 等待 → 返回图像字节
        """
        prompt_id = self.queue_prompt(workflow)
        result = self.wait_for_result(prompt_id, timeout=timeout)
        return [m["data"] for m in result if m["type"] == "image"]

    def generate_media(
        self,
        workflow: dict,
        timeout: int = 300,
    ) -> list[dict]:
        """
        一键生成：提交 workflow → 等待 → 返回 [{type, data, ext}]
        """
        prompt_id = self.queue_prompt(workflow)
        return self.wait_for_result(prompt_id, timeout=timeout)

    def wait_for_result(
        self,
        prompt_id: str,
        timeout: int = 300,
        poll_interval: float = 1.0,
    ) -> list[dict]:
        """
        轮询等待 ComfyUI 完成生成，返回 [{type:'image'|'video', data:bytes, ext:str}]
        """
        start = time.time()
        while time.time() - start < timeout:
            history = self.get_history(prompt_id)
            if prompt_id in history and "outputs" in history[prompt_id]:
                outputs = history[prompt_id]["outputs"]
                return self._extract_media(outputs)
            time.sleep(poll_interval)
        raise TimeoutError(f"ComfyUI generation timeout after {timeout}s")
