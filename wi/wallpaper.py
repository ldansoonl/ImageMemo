"""
wallpaper.py - 바탕화면 이미지 생성 및 설정 모듈
- 검은 배경화면에 노란 메모지 이미지 렌더링
- Windows 바탕화면 즉시 적용 및 이전 생성 이미지 삭제
- 메모 데이터(JSON) 영구 저장 및 관리
"""
import os
import json
import time
import glob
import struct
import ctypes
from ctypes import wintypes

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memos.json")

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]

def get_screen_size():
    u32 = ctypes.windll.user32
    try:
        u32.SetProcessDPIAware()
    except Exception:
        pass
    w, h = u32.GetSystemMetrics(0), u32.GetSystemMetrics(1)
    return (w if w > 0 else 1920, h if h > 0 else 1080)

def load_memos():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return [{
        "id": 1,
        "text": "📌 환영합니다!\n새로운 메모를 추가하고\n원하는 위치로 드래그해보세요.",
        "x": 120, "y": 120, "width": 260, "height": 180
    }]

def save_memos(memos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(memos, f, ensure_ascii=False, indent=2)

def clean_old_wallpapers(current_file):
    base_dir = os.path.dirname(os.path.abspath(current_file))
    patterns = [os.path.join(base_dir, "wallpaper_memo_*.bmp"), os.path.join(base_dir, "wallpaper_memo_*.png")]
    for p in patterns:
        for f in glob.glob(p):
            if os.path.abspath(f) != os.path.abspath(current_file):
                try:
                    os.remove(f)
                except Exception:
                    pass

def render_wallpaper_pil(memos, width, height, out_path):
    img = Image.new("RGB", (width, height), (18, 18, 18))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("malgun.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
    for m in memos:
        x, y, w, h = int(m["x"]), int(m["y"]), int(m["width"]), int(m["height"])
        draw.rounded_rectangle([x, y, x + w, y + h], radius=12, fill=(255, 238, 115), outline=(225, 205, 80), width=2)
        lines = m["text"].split("\n")
        cur_y = y + 14
        for line in lines:
            draw.text((x + 14, cur_y), line, fill=(25, 25, 25), font=font)
            cur_y += 22
            if cur_y > y + h - 20:
                break
    img.save(out_path)

def render_wallpaper_gdi(memos, width, height, out_path):
    u32, g32 = ctypes.windll.user32, ctypes.windll.gdi32
    hdc_screen = u32.GetDC(0)
    hdc = g32.CreateCompatibleDC(hdc_screen)
    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth, bmi.biHeight, bmi.biPlanes, bmi.biBitCount = width, -height, 1, 32
    p_bits = ctypes.c_void_p()
    h_bmp = g32.CreateDIBSection(hdc, ctypes.byref(bmi), 0, ctypes.byref(p_bits), None, 0)
    old_bmp = g32.SelectObject(hdc, h_bmp)
    g32.PatBlt(hdc, 0, 0, width, height, 0x00000042)
    for m in memos:
        x, y, w, h = int(m["x"]), int(m["y"]), int(m["width"]), int(m["height"])
        brush = g32.CreateSolidBrush(0x73EEFF)
        pen = g32.CreatePen(0, 2, 0x50CDE1)
        o_br, o_pn = g32.SelectObject(hdc, brush), g32.SelectObject(hdc, pen)
        g32.RoundRect(hdc, x, y, x + w, y + h, 14, 14)
        g32.SelectObject(hdc, o_br)
        g32.SelectObject(hdc, o_pn)
        g32.DeleteObject(brush)
        g32.DeleteObject(pen)
        font = g32.CreateFontW(18, 0, 0, 0, 600, 0, 0, 0, 1, 0, 0, 4, 0, "맑은 고딕")
        o_fn = g32.SelectObject(hdc, font)
        g32.SetTextColor(hdc, 0x191919)
        g32.SetBkMode(hdc, 1)
        rect = wintypes.RECT(x + 14, y + 14, x + w - 14, y + h - 14)
        u32.DrawTextW(hdc, m["text"], -1, ctypes.byref(rect), 0x0010 | 0x0000)
        g32.SelectObject(hdc, o_fn)
        g32.DeleteObject(font)
    size = width * height * 4
    with open(out_path, "wb") as f:
        f.write(b"BM" + struct.pack("<IHHI", 54 + size, 0, 0, 54))
        f.write(bytes(bmi))
        f.write(ctypes.string_at(p_bits.value, size))
    g32.SelectObject(hdc, old_bmp)
    g32.DeleteObject(h_bmp)
    g32.DeleteDC(hdc)
    u32.ReleaseDC(0, hdc_screen)

def update_wallpaper(memos):
    w, h = get_screen_size()
    ext = "png" if HAS_PIL else "bmp"
    dir_path = os.path.dirname(os.path.abspath(__file__))
    new_file = os.path.join(dir_path, f"wallpaper_memo_{int(time.time() * 1000)}.{ext}")
    if HAS_PIL:
        render_wallpaper_pil(memos, w, h, new_file)
    else:
        render_wallpaper_gdi(memos, w, h, new_file)
    ctypes.windll.user32.SystemParametersInfoW(20, 0, new_file, 3)
    clean_old_wallpapers(new_file)
    return new_file
