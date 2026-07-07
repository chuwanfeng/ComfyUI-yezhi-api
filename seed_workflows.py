"""
一次性脚本：将 workflows/ 目录下所有 JSON 文件入库。
每个文件创建一条 Workflow(is_builtin=True) 记录。
根据节点类型自动判断 图片/视频。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.db import init_db, get_sessionmaker
from models.workflow import Workflow

WORKFLOWS_DIR = os.path.join(os.path.dirname(__file__), "workflows")

# ── 工作流配置：文件名 → (显示名称, 描述, 媒体类型)
WORKFLOW_CONFIG = {
    "0243009787194a80.json": ("音频驱动视频", "音频 + 参考图驱动 LTXV 视频生成，支持 LoRA", "video"),
    "2df2fc58911149bf.json": ("文生图", "AuraFlow/SD3 文生图基础工作流", "image"),
    "63c44237a3584646.json": ("图生图", "Qwen Image Edit 图像编辑（可选输入图）", "image"),
    "83f22069b5084d2e.json": ("首尾帧生视频", "LTXV 首帧 → 视频，支持音频驱动", "video"),
    "b30930013eb24533.json": ("图生视频+放大", "LTXV 图生视频，含 Upscaler 和 Prompt 控制", "video"),
    "d7ee74d9e2774e5f.json": ("音频驱动视频(LoRA)", "音频驱动 LTXV 视频 + IC LoRA，支持参考图", "video"),
    "d993f2505e224b0d.json": ("首尾帧生视频(变体)", "LTXV 首帧 → 视频变体，Euler 采样器", "video"),
    "e6027e3ae8684de0.json": ("双模型文生图", "双模型双采样文生图，SD3+AuraFlow", "image"),
}


def main():
    init_db()
    db = get_sessionmaker()()

    json_files = [f for f in os.listdir(WORKFLOWS_DIR) if f.endswith(".json")]

    count = 0
    for fname in sorted(json_files):
        fpath = os.path.join(WORKFLOWS_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            json.load(f)  # 验证格式

        cfg = WORKFLOW_CONFIG.get(fname)
        if not cfg:
            print(f"  [SKIP] {fname} — 未在配置中")
            continue

        name, desc, media_type = cfg
        wf_id = fname.replace(".json", "").replace("-", "")

        existing = db.query(Workflow).filter(Workflow.json_path == fname).first()
        if existing:
            existing.name = name
            existing.description = desc
            existing.is_builtin = True
            print(f"  [UPDATE] {fname} → {name} ({media_type})")
        else:
            wf = Workflow(
                id=wf_id,
                name=name,
                description=desc,
                json_path=fname,
                comfyui_url=None,
                is_builtin=True,
                is_public=False,
                user_id=None,
            )
            db.add(wf)
            print(f"  [CREATE] {fname} → {name} ({media_type})")

        count += 1

    db.commit()
    db.close()
    print(f"\nDone. {count} workflows seeded.")


if __name__ == "__main__":
    main()
