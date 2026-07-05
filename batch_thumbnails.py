"""批量生成视频缩略图 — 对 media_type='video' 且 thumbnail_url 为空的记录用 ffmpeg 抽帧"""
import os, subprocess, sqlite3, sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "yezhi.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT id, image_url FROM yezhi_user_generated_image
        WHERE media_type = 'video'
          AND (thumbnail_url IS NULL OR thumbnail_url = '' OR thumbnail_url = image_url)
    """).fetchall()
    print(f"找到 {len(rows)} 个视频需要生成缩略图")
    ok, fail = 0, 0
    for row in rows:
        img_id = row["id"]
        url = row["image_url"]
        # /uploads/generations/xxx.mp4 -> uploads/generations/xxx.mp4
        local_path = os.path.join(BASE_DIR, url.lstrip("/").replace("/", os.sep))
        if not os.path.exists(local_path):
            print(f"  [跳过] {img_id}: 文件不存在 {local_path}")
            fail += 1
            continue
        thumb_name = f"{img_id.replace('-', '')}_thumb.jpg"
        thumb_rel = f"/uploads/generations/{thumb_name}"
        thumb_path = os.path.join(UPLOAD_DIR, "generations", thumb_name)
        os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
        try:
            # 取第1秒画面，视频短于1秒则取最后帧
            r = subprocess.run(
                ["ffmpeg", "-y", "-i", local_path, "-ss", "00:00:01",
                 "-vframes", "1", "-q:v", "2", thumb_path],
                capture_output=True, timeout=15
            )
            if r.returncode != 0 or not os.path.exists(thumb_path):
                # 重试：取 0.5 秒
                r2 = subprocess.run(
                    ["ffmpeg", "-y", "-i", local_path, "-ss", "00:00:00.5",
                     "-vframes", "1", "-q:v", "2", thumb_path],
                    capture_output=True, timeout=15
                )
            if os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0:
                conn.execute(
                    "UPDATE yezhi_user_generated_image SET thumbnail_url = ? WHERE id = ?",
                    (thumb_rel, img_id)
                )
                conn.commit()
                ok += 1
                print(f"  [完成] {img_id} -> {thumb_rel}")
            else:
                fail += 1
                print(f"  [失败] {img_id}: ffmpeg 未生成文件")
        except Exception as e:
            fail += 1
            print(f"  [错误] {img_id}: {e}")
    conn.close()
    print(f"\n完成: {ok} 成功, {fail} 失败")

if __name__ == "__main__":
    main()
