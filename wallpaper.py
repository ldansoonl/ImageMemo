"""
wallpaper.py - 바탕화면 이미지 생성 및 설정 모듈
- Pillow(PIL) 기반 메모 합성 (사용자 지정 폰트 및 Unsplash 배경 텍스처 지원)
- Windows 바탕화면 실시간 반영 및 이전 임시 파일 자동 정리
- 메모 데이터(JSON) 영구 저장 (기본 환영 메모 없이 빈 상태로 시작)
"""
import os
import glob
import json
import time
import ctypes
from PIL import Image, ImageDraw, ImageFont, ImageStat

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memos.json")

def get_screen_size() -> tuple[int, int]:
    u32 = ctypes.windll.user32
    try:
        u32.SetProcessDPIAware()
    except Exception:
        pass
    w, h = u32.GetSystemMetrics(0), u32.GetSystemMetrics(1)
    return (w if w > 0 else 1920, h if h > 0 else 1080)

def load_memos() -> list[dict]:
    """저장된 메모 목록 로드 (환영 메모 없이 빈 리스트 반환)"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            return []
    return []

def save_memos(memos: list[dict]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(memos, f, ensure_ascii=False, indent=2)

def clean_old_wallpapers(current_file: str) -> None:
    base_dir = os.path.dirname(os.path.abspath(current_file))
    patterns = [os.path.join(base_dir, "wallpaper_memo_*.png"), os.path.join(base_dir, "wallpaper_memo_*.bmp")]
    for p in patterns:
        for f in glob.glob(p):
            if os.path.abspath(f) != os.path.abspath(current_file):
                try:
                    os.remove(f)
                except Exception:
                    pass

def create_rounded_mask(width: int, height: int, radius: int = 14) -> Image.Image:
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, width, height], radius=radius, fill=255)
    return mask

def render_wallpaper_pil(memos: list[dict], width: int, height: int, out_path: str) -> None:
    img = Image.new("RGB", (width, height), (18, 18, 18))
    draw = ImageDraw.Draw(img)

    for m in memos:
        x, y, w, h = int(m["x"]), int(m["y"]), int(m["width"]), int(m["height"])
        if w <= 10 or h <= 10:
            continue

        bg_path = m.get("bg_image_path")
        is_dark = False
        if bg_path and os.path.exists(bg_path):
            try:
                bg_memo = Image.open(bg_path).convert("RGB").resize((w, h), Image.Resampling.LANCZOS)
                mask = create_rounded_mask(w, h, radius=14)
                img.paste(bg_memo, (x, y), mask)
                draw.rounded_rectangle([x, y, x + w, y + h], radius=14, outline=(220, 220, 220), width=2)
                stat = ImageStat.Stat(bg_memo.convert("L"))
                is_dark = stat.mean[0] < 128
            except Exception:
                draw.rounded_rectangle([x, y, x + w, y + h], radius=14, fill=(255, 238, 115), outline=(225, 205, 80), width=2)
        else:
            draw.rounded_rectangle([x, y, x + w, y + h], radius=14, fill=(255, 238, 115), outline=(225, 205, 80), width=2)

        font_path = m.get("font_path")
        font_size = 18
        font = None
        if font_path and os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, font_size)
            except Exception:
                pass
        if font is None:
            try:
                font = ImageFont.truetype("malgun.ttf", 16)
            except Exception:
                font = ImageFont.load_default()

        text_color = (245, 245, 245) if is_dark else (25, 25, 25)
        shadow_color = (15, 15, 15) if is_dark else (255, 255, 255)
        lines = m.get("text", "").split("\n")
        cur_y = y + 14
        for line in lines:
            draw.text((x + 15, cur_y + 1), line, fill=shadow_color, font=font)
            draw.text((x + 14, cur_y), line, fill=text_color, font=font)
            cur_y += 24
            if cur_y > y + h - 22:
                break

    img.save(out_path, format="PNG")

def update_wallpaper(memos: list[dict]) -> str:
    w, h = get_screen_size()
    dir_path = os.path.dirname(os.path.abspath(__file__))
    new_file = os.path.join(dir_path, f"wallpaper_memo_{int(time.time() * 1000)}.png")
    render_wallpaper_pil(memos, w, h, new_file)
    ctypes.windll.user32.SystemParametersInfoW(20, 0, new_file, 3)
    clean_old_wallpapers(new_file)
    return new_file
