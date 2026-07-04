"""
图像生成 API — SSE 流式推送
POST /api/generate — 提交生成任务，返回 SSE 流
POST /api/generate-video — 视频生成（TODO）
支持: quick 模式, direct 模式, workflow 模式
"""
import json
import time
import threading
import logging
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, Response, stream_with_context
from services.db import get_db_session
from services.workflow_api import _load_workflow_json as _load_workflow_json_from_file
from models.generation import UserGeneratedImage, SiteStats, ModelUsageStats
from models.workflow import Workflow
from models.user import User
from utils.comfy_client import ComfyUIClient
from utils.model_config import get_model_by_id
from utils.moderation import check_text_safety
from utils.storage import save_upload
from utils.auth import get_user_id_from_request
from utils import profanity_filter
import config
import os
import json

gen_bp = Blueprint("generation", __name__, url_prefix="/api")


def _now():
    return datetime.now(timezone.utc)


def _to_compare(dt):
    """SQLite 兼容：naive dt 按 UTC 补齐 tzinfo"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _check_quota(db, user_id: str) -> tuple[bool, str]:
    """检查用户配额，返回 (allowed, reason)"""
    if config.SELF_HOSTED_MODE:
        return True, "self_hosted"

    if not user_id:
        # 未登录用户从 IP 检查
        return True, "no_limit"  # TODO: IP 配额检查

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False, "用户不存在"
    if user.banned:
        return False, f"账号已封禁: {user.ban_reason or '未知'}"

    # 简单每日限额
    daily_limit = 50
    if user.daily_request_count and user.daily_request_count >= daily_limit:
        return False, f"已超出每日生成次数 ({daily_limit})"

    return True, "ok"


def _increment_stats(db, user_id: str = None, ip_address: str = None):
    """更新站点统计和用户配额"""
    stats = db.query(SiteStats).filter(SiteStats.id == 1).first()
    if not stats:
        stats = SiteStats(id=1)
        db.add(stats)
        db.flush()
    stats.total_generations = (stats.total_generations or 0) + 1
    stats.daily_generations = (stats.daily_generations or 0) + 1

    # 重置每日计数（兼容 SQLite naive/aware）
    today = _now().replace(hour=0, minute=0, second=0, microsecond=0)
    if stats.last_reset_date and _to_compare(stats.last_reset_date) < today:
        stats.daily_generations = 1
        stats.last_reset_date = _now()

    if user_id and not config.SELF_HOSTED_MODE:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.daily_request_count = (user.daily_request_count or 0) + 1
            # 重置每日请求计数
            if user.last_request_reset_date and _to_compare(user.last_request_reset_date) < today:
                user.daily_request_count = 1
                user.last_request_reset_date = _now()

    db.commit()


# ── 图像生成 (SSE) ───────────────────────────
@gen_bp.route("/generate", methods=["POST"])
def generate():
    """
    图像生成接口
    支持两种模式：
    1. 直接生成（direct）: 提交 workflow JSON
    2. 快捷生成（quick）: 传入 prompt + model_id，自动构建 workflow
    返回 SSE 流
    """
    data = request.get_json() or {}
    mode = data.get("mode", "quick")
    user_id = get_user_id_from_request(request)
    ip_address = request.remote_addr

    # 额度检查
    db = get_db_session()
    try:
        allowed, reason = _check_quota(db, user_id)
        if not allowed:
            return jsonify({"error": reason}), 429

        if mode == "quick":
            return _generate_quick(db, data, user_id, ip_address)
        else:
            return _generate_direct(db, data, user_id, ip_address)
    finally:
        db.close()


def _generate_quick(db, data: dict, user_id: str, ip_address: str) -> Response:
    """快捷模式：prompt + model/workflow → ComfyUI"""
    prompt = (data.get("prompt") or "").strip()
    negative_prompt = (data.get("negative_prompt") or "").strip()
    model_id = data.get("model_id", "")
    workflow_id = data.get("workflow_id")  # 新增: 使用自定义工作流
    width = data.get("width", 1024)
    height = data.get("height", 1024)
    steps = data.get("steps", 20)
    batch_size = data.get("batch_size", 1)
    seed = data.get("seed", -1)
    duration_seconds = data.get("duration")  # 视频时长
    fps = data.get("fps")                    # 视频帧率
    audio_start_time = data.get("audio_start_time")  # 音频开始帧
    audio_duration = data.get("audio_duration")      # 音频长度（秒）
    reference_images = data.get("reference_images") or []  # base64 图生图（多图）
    audio_files = data.get("audio") or []  # base64 音频文件
    # 向后兼容单图
    if not reference_images:
        single = data.get("reference_image")
        if single:
            reference_images = [single]

    if not prompt:
        return jsonify({"error": "提示词不能为空"}), 400

    # 文本安全审核（自用模式放行）
    safe, reason = check_text_safety(prompt)
    if not safe:
        return jsonify({"error": f"提示词包含违规内容: {reason}"}), 400

    # 确定使用的工作流
    workflow = None
    comfy_url = None
    workflow_record = None
    
    if workflow_id:
        # 使用用户自定义工作流（从文件加载 JSON）
        workflow_record = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow_record:
            return jsonify({"error": f"工作流不存在: {workflow_id}"}), 404
        
        workflow = _load_workflow_json_from_file(workflow_record.json_path)
        comfy_url = workflow_record.comfyui_url or getattr(config, 'COMFY_URL', '')
        if not comfy_url:
            comfy_url = config.COMFYUI_URL
        
        # ── 参考图：上传到 ComfyUI input/ 目录（MD5 命名，自动去重）──
        input_image_names = []  # 所有图的上传后文件名
        if reference_images:
            for idx, ref_img in enumerate(reference_images):
                if not ref_img:
                    continue
                try:
                    import base64 as b64
                    img_bytes = b64.b64decode(ref_img.split(",")[-1]) if "," in ref_img else b64.b64decode(ref_img)
                    client_pre = ComfyUIClient(comfy_url)
                    fname = client_pre.upload_file(img_bytes, f"ref_{idx}.png")
                    input_image_names.append(fname)
                    logging.getLogger('generation').info(f'  [upload] Reference image #{idx+1} → ComfyUI input/{fname}')
                except Exception as e:
                    logging.getLogger('generation').error(f'  [upload] Failed to upload reference image #{idx+1}: {e}')
        
        # ── 音频：上传到 ComfyUI input/ 目录 ──
        input_audio_names = []
        if audio_files:
            for idx, audio in enumerate(audio_files):
                if not audio:
                    continue
                try:
                    import base64 as b64
                    # 解析 data:audio/mpeg;base64,xxx 格式
                    if "," in audio:
                        header, data_b64 = audio.split(",", 1)
                        ext = header.split("/")[-1].split(";")[0] if "/" in header else "mp3"
                    else:
                        data_b64 = audio
                        ext = "mp3"
                    audio_bytes = b64.b64decode(data_b64)
                    client_pre = ComfyUIClient(comfy_url)
                    fname = client_pre.upload_file(audio_bytes, f"audio_{idx}.{ext}")
                    input_audio_names.append(fname)
                    logging.getLogger('generation').info(f'  [upload] Audio #{idx+1} → ComfyUI input/{fname}')
                except Exception as e:
                    logging.getLogger('generation').error(f'  [upload] Failed to upload audio #{idx+1}: {e}')
        
        # 应用参数映射
        param_mapping = json.loads(workflow_record.param_mapping) if workflow_record.param_mapping else {}
        workflow = _inject_user_params(workflow, param_mapping, {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "batch_size": batch_size,
            "seed": seed,
            "duration": duration_seconds,
            "fps": fps,
            "reference_images": reference_images,
            "input_image_names": input_image_names,
            "input_audio_names": input_audio_names,
            "audio_start_time": audio_start_time,
            "audio_duration": audio_duration,
        })
    else:
        # 使用模型预设
        model = get_model_by_id(model_id)
        if not model:
            return jsonify({"error": f"未知模型: {model_id}"}), 400

        comfy_url = config.COMIFY_MODEL_URLS.get(model_id, "")
        if not comfy_url:
            return jsonify({"error": f"模型 {model_id} 未配置 ComfyUI 端点"}), 400

        # 构建基础 t2i workflow
        workflow = _build_t2i_workflow(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            steps=steps,
            batch_size=batch_size,
            seed=seed,
        )
    
    if not comfy_url:
        comfy_url = config.COMFYUI_URL
    
    client = ComfyUIClient(comfy_url)

    def generate_events():
        start_time = time.time()
        # queue.Queue 解耦：bg_thread 跑 ComfyUI+保存，generator 只读 queue 发 SSE
        # 客户端断开 → GeneratorExit → bg_thread 不受影响，继续保存到 DB
        import queue as pyqueue
        from services.db import get_db_session as _get_db_session
        result_queue = pyqueue.Queue()

        try:
            prompt_id = client.queue_prompt(workflow)
            yield f"data: {json.dumps({'type': 'queued', 'prompt_id': prompt_id, 'model': model_id}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'提交失败: {e}'}, ensure_ascii=False)}\n\n"
            return

        def _bg_generate():
            try:
                media_list = client.wait_for_result(prompt_id, timeout=300)
                elapsed = time.time() - start_time
                s = _get_db_session()
                try:
                    for i, media in enumerate(media_list):
                        is_video = media.get("type") == "video" or media.get("ext", "png").lower() in ("mp4", "webm", "avi", "mov", "gif")
                        ext = media.get("ext", "png")
                        url = save_upload(media["data"], f"generated_{prompt_id}_{i}.{ext}", subdir="generations")
                        generated = UserGeneratedImage(
                            user_id=user_id if user_id else "anonymous",
                            model_name=model_id or (workflow_record.name if workflow_record else "custom"),
                            workflow_id=workflow_id,
                            prompt=prompt,
                            negative_prompt=negative_prompt,
                            image_url=url,
                            width=width,
                            height=height,
                            steps=steps,
                            batch_index=i,
                            media_type="video" if is_video else "image",
                            duration_seconds=duration_seconds,
                            fps=fps,
                        )
                        s.add(generated)
                        s.flush()
                        if workflow_record:
                            wr = s.query(Workflow).filter(Workflow.id == workflow_record.id).first()
                            if wr:
                                wr.use_count = (wr.use_count or 0) + 1
                        result_queue.put({'type': 'image' if not is_video else 'video', 'index': i, 'url': url, 'id': generated.id, 'media_type': 'video' if is_video else 'image'})
                    usage = ModelUsageStats(
                        model_name=model_id, user_id=user_id, response_time=elapsed,
                        is_authenticated=bool(user_id), ip_address=ip_address,
                    )
                    s.add(usage)
                    _increment_stats(s, user_id=user_id, ip_address=ip_address)
                    s.commit()
                    result_queue.put({'type': 'done', 'total': len(media_list), 'elapsed': round(elapsed, 2)})
                    # 自动清理已禁用 — 见 _cleanup_old_generation_files
                finally:
                    s.close()
            except Exception as e:
                result_queue.put({'type': 'error', 'message': str(e)})

        bg_thread = threading.Thread(target=_bg_generate, daemon=True)
        bg_thread.start()

        while bg_thread.is_alive():
            try:
                item = result_queue.get(timeout=1)
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
                if item.get('type') in ('done', 'error'):
                    break  # 收到 done 后继续排空队列，避免遗漏残余事件
            except pyqueue.Empty:
                yield ":\n\n"
                continue

        # 排空残余事件（防止 bg_thread 在 done 之后还 push 了 image）
        while True:
            try:
                item = result_queue.get_nowait()
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
                if item.get('type') in ('done', 'error'):
                    continue  # 已处理过，跳过重复 done/error
            except pyqueue.Empty:
                break

    return Response(
        stream_with_context(generate_events()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _generate_direct(db, data: dict, user_id: str, ip_address: str) -> Response:
    """直接模式：前端传入完整 ComfyUI workflow JSON"""
    workflow = data.get("workflow")
    if not workflow:
        return jsonify({"error": "workflow 不能为空"}), 400

    comfy_url = data.get("comfy_url")
    if not comfy_url:
        return jsonify({"error": "comfy_url 不能为空"}), 400

    client = ComfyUIClient(comfy_url)

    def generate_events():
        try:
            prompt_id = client.queue_prompt(workflow)
            yield f"data: {json.dumps({'type': 'queued', 'prompt_id': prompt_id}, ensure_ascii=False)}\n\n"

            images = client.wait_for_result(prompt_id, timeout=300)

            saved_urls = []
            for i, img_bytes in enumerate(images):
                url = save_upload(img_bytes, f"direct_{prompt_id}_{i}.png", subdir="generations")
                saved_urls.append(url)
                yield f"data: {json.dumps({'type': 'image', 'index': i, 'url': url}, ensure_ascii=False)}\n\n"

            _increment_stats(db, user_id=user_id, ip_address=ip_address)
            yield f"data: {json.dumps({'type': 'done', 'total': len(images)}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate_events()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── 视频生成 (占位) ───────────────────────────
@gen_bp.route("/generate-video", methods=["POST"])
def generate_video():
    data = request.get_json() or {}
    return jsonify({
        "error": "请使用 /api/generate 端点，指定 workflow_id 为视频工作流即可",
        "note": "视频工作流和图片工作流统一通过 /api/generate 提交",
    }), 400


# ── 工作流构建器 ──────────────────────────────
def _build_t2i_workflow(
    prompt: str,
    negative_prompt: str = "",
    width: int = 1024,
    height: int = 1024,
    steps: int = 20,
    batch_size: int = 1,
    seed: int = -1,
    cfg: float = 7.0,
) -> dict:
    """
    构建标准 t2i (text-to-image) workflow
    这是一个最小化的 ComfyUI API JSON 格式
    节点 ID 和连接按 ComfyUI 标准 API 格式排列
    """
    import random
    if seed == -1:
        seed = random.randint(0, 2**31 - 1)

    return {
        "3": {
            "inputs": {
                "seed": seed, "steps": steps, "cfg": cfg,
                "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
            "class_type": "KSampler",
        },
        "4": {
            "inputs": {"ckpt_name": "model.safetensors"},
            "class_type": "CheckpointLoaderSimple",
        },
        "5": {
            "inputs": {"width": width, "height": height, "batch_size": batch_size},
            "class_type": "EmptyLatentImage",
        },
        "6": {
            "inputs": {"text": prompt, "clip": ["4", 1]},
            "class_type": "CLIPTextEncode",
        },
        "7": {
            "inputs": {"text": negative_prompt, "clip": ["4", 1]},
            "class_type": "CLIPTextEncode",
        },
        "8": {
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
            "class_type": "VAEDecode",
        },
        "9": {
            "inputs": {"filename_prefix": "yezhi", "images": ["8", 0]},
            "class_type": "SaveImage",
        },
    }


def _inject_user_params(workflow: dict, param_mapping: dict, values: dict) -> dict:
    """
    将用户输入注入到自定义工作流节点。
    同时使用 param_mapping（精确指定）+ auto_inject（自动探测常见节点）。
    """
    import random, copy
    import logging
    log = logging.getLogger('generation')

    # 重置 LoadImage 计数器
    _inject_user_params._loadimage_idx = 0
    _inject_user_params._loadaudio_idx = 0

    result = {}
    for nid, node in workflow.items():
        result[nid] = {"inputs": dict(node.get("inputs", {})), "class_type": node.get("class_type", "")}
        if "_meta" in node:
            result[nid]["_meta"] = node["_meta"]

    # ── 第1步：param_mapping 精确注入 ──
    for param_name, mapping in param_mapping.items():
        node_id = mapping.get("node_id")
        field = mapping.get("field")
        if not node_id or not field or node_id not in result:
            continue
        value = values.get(param_name)
        if value is not None:
            result[node_id]["inputs"][field] = value
            log.info(f'  [param_map] Node {node_id}.{field} = {value}')

    # ── 第2步：自动注入 prompt / negative_prompt / seed / 尺寸 ──
    for nid, node in result.items():
        cls = (node.get("class_type") or "").lower()
        inp = node["inputs"]

        # ── 提示词注入：CLIPTextEncode / TextEncode* 等节点 ──
        # 自动匹配所有文本编码节点（标准 CLIPTextEncode + Qwen TextEncodeQwenImageEditPlus 等）
        cls_name = node.get("class_type", "")
        if any(kw in cls_name for kw in ["CLIPTextEncode", "TextEncode"]):
            has_explicit = bool(param_mapping)
            # 兼容不同字段名：CLIPTextEncode 用 text，TextEncodeQwenImageEditPlus 用 prompt
            text_field = "text" if "text" in inp else "prompt"
            current_text = (inp.get(text_field, "") or "").strip()
            # 判断正/负：内容含负面词 → 负面节点
            is_negative = any(kw in current_text[:200].lower() for kw in [
                "worst quality", "low quality", "normal quality", "deformed", "bad anatomy",
                "ugly", "blurry", "nsfw", "nude", "naked",
            ])
            # 也检查 _meta.title
            node_title = (node.get("_meta", {}).get("title", "") or "").lower()
            is_negative = is_negative or ("negative" in node_title or "neg" in node_title)
            # 负向空 prompt 也视为负面节点（Qwen Image Edit Plus 负向默认空）
            is_negative = is_negative or (not current_text and "qwen" in cls_name.lower() and any(kw in node_title for kw in ["negative", "neg"]))

            if not has_explicit:
                if is_negative:
                    # 负向节点：保留原始 + 追加用户输入
                    if values.get("negative_prompt"):
                        new_text = (current_text + ", " + values["negative_prompt"]) if current_text else values["negative_prompt"]
                        inp[text_field] = new_text
                        log.info(f'  [auto] Node {nid} ({cls_name}) negative: append user input')
                else:
                    # 正向节点：替换为用户 prompt
                    if values.get("prompt"):
                        inp[text_field] = values["prompt"]
                        log.info(f'  [auto] Node {nid} ({cls_name}) positive = user prompt')

        # ── 负向提示词节点（title/name 含 "negative" 的）──
        node_title = (node.get("_meta", {}).get("title", "") or "").lower()
        if "negative" in node_title or "neg" in node_title:
            if any(kw in node.get("class_type", "") for kw in ["CLIPTextEncode", "CR Prompt Text"]):
                text_val = inp.get("text", "")
                if not text_val or text_val in ("low quality, blurry", "worst quality", ""):
                    if values.get("negative_prompt"):
                        inp["text"] = values["negative_prompt"]
                        log.info(f'  [auto] Node {nid} ({node["class_type"]}) text = negative_prompt')

        # ── KSampler seed / steps / cfg ──
        if "ksampler" in cls or "sampler" in cls:
            if "seed" in inp and (values.get("seed") is None or values.get("seed") == -1):
                inp["seed"] = random.randint(0, 2**31 - 1)
                log.info(f'  [auto] Node {nid} {cls} seed randomized')
            if "steps" in inp and values.get("steps"):
                inp["steps"] = values["steps"]
                log.info(f'  [auto] Node {nid} steps = {values["steps"]}')
            if "cfg" in inp and values.get("cfg"):
                inp["cfg"] = values["cfg"]

        # ── RandomNoise / Noise 节点（视频工作流常用）──
        if "noise" in cls and cls != "SamplerCustomAdvanced":
            if "noise_seed" in inp and (values.get("seed") is None or values.get("seed") == -1):
                inp["noise_seed"] = random.randint(0, 2**63 - 1)
                log.info(f'  [auto] Node {nid} {cls} noise_seed randomized')

        # ── 空潜空间尺寸 + INTConstant 上游尺寸注入 ──
        if any(kw in cls for kw in ["emptylatent", "empty latent", "emptysd3", "emptyltxlatent"]):
            if values.get("width") and not isinstance(inp.get("width"), list):
                inp["width"] = values["width"]
                log.info(f'  [auto] Node {nid} width = {values["width"]}')
            elif values.get("width") and isinstance(inp.get("width"), list):
                # 宽高是连线（如 EmptyLTXVLatentVideo）→ 往上游 INTConstant 注入
                for k, src_id in [("width", inp["width"]), ("height", inp["height"])]:
                    if isinstance(src_id, list) and len(src_id) == 2:
                        src_nid = str(src_id[0])
                        src_node = result.get(src_nid)
                        if src_node and "intconstant" in (src_node.get("class_type") or "").lower():
                            if values.get(k) and not isinstance(src_node["inputs"].get("value"), list):
                                src_node["inputs"]["value"] = values[k]
                                log.info(f'  [auto] INTConstant {src_nid}.value = {values[k]} (for {k})')
            if values.get("height") and not isinstance(inp.get("height"), list):
                inp["height"] = values["height"]
                log.info(f'  [auto] Node {nid} height = {values["height"]}')
            if values.get("batch_size") and "batch_size" in inp and not isinstance(inp.get("batch_size"), list):
                inp["batch_size"] = values["batch_size"]

        # ── LoadImage：注入上传后的文件名；超出数量的节点填第1张图+禁用（mode=4 靠填入而非跳过，ComfyUI 校验先于 mute）──
        if cls_name == "LoadImage":
            names = values.get("input_image_names") or []
            _ld_idx = getattr(_inject_user_params, '_loadimage_idx', 0)
            if _ld_idx < len(names):
                inp["image"] = names[_ld_idx]
                log.info(f'  [auto] Node {nid} LoadImage = {names[_ld_idx]}')
            elif names:
                # 超出数量：填入第1张图（校验通过）+ 禁用节点
                inp["image"] = names[0]
                result[nid]["mode"] = 4
                log.info(f'  [auto] Node {nid} LoadImage disabled (fallback={names[0]})')
            else:
                # 无图且无预设：清空
                inp["image"] = ""
            _inject_user_params._loadimage_idx = _ld_idx + 1

        # ── VHS_LoadAudioUpload / LoadAudio：注入音频文件名 + duration/start_time ──
        if "loadaudio" in cls or "loadaudioupload" in cls:
            names = values.get("input_audio_names") or []
            _a_idx = getattr(_inject_user_params, '_loadaudio_idx', 0)
            if _a_idx < len(names):
                inp["audio"] = names[_a_idx]
                log.info(f'  [auto] Node {nid} ({cls}) audio = {names[_a_idx]}')
            elif names:
                inp["audio"] = names[0]
                result[nid]["mode"] = 4
                log.info(f'  [auto] Node {nid} ({cls}) audio disabled (fallback={names[0]})')
            # audio_start_time → start_time
            if values.get("audio_start_time") is not None:
                inp["start_time"] = values["audio_start_time"]
                log.info(f'  [auto] Node {nid} ({cls}) start_time = {values["audio_start_time"]}')
            # audio_duration → duration
            if values.get("audio_duration") is not None:
                inp["duration"] = values["audio_duration"]
                log.info(f'  [auto] Node {nid} ({cls}) duration = {values["audio_duration"]}')
            _inject_user_params._loadaudio_idx = _a_idx + 1

    return result


def _apply_param_mapping(workflow: dict, param_mapping: dict, values: dict) -> dict:
    """
    将前端参数应用到工作流节点（已被 _inject_user_params 取代，保留向后兼容）
    param_mapping: {"prompt": {"node_id": "6", "field": "text"}, ...}
    values: {"prompt": "...", "negative_prompt": "...", ...}
    """
    return _inject_user_params(workflow, param_mapping, values)


def _optimize_prompt(prompt: str) -> str:
    """提示词优化（留空即使用 LLM 优化）"""
    # TODO: 接入 LLM 提示词优化服务
    return prompt


# ── 生成后文件清理 ──────────────────────────
def _cleanup_old_generation_files(db, user_id: str):
    """清除 30 分钟前的生成图片本地文件（保留 DB 记录）"""
    from datetime import datetime, timezone, timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
    old_images = (
        db.query(UserGeneratedImage)
        .filter(
            UserGeneratedImage.user_id == user_id,
            UserGeneratedImage.created_at < cutoff,
        )
        .all()
    )
    for img in old_images:
        _delete_image_file(img.image_url)
        if img.thumbnail_url and img.thumbnail_url != img.image_url:
            _delete_image_file(img.thumbnail_url)


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
