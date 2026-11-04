"""
api_service.py - Unsplash API 및 Google Fonts API 연동 서비스
- Unsplash: 키워드 기반 배경 이미지 검색 및 로컬 캐싱
- Google Fonts: 웹폰트 메타데이터 수집 및 TTF 다운로드
- .env 환경변수(API 키) 안전 관리
"""
import os
import hashlib
import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

BG_CACHE_DIR = os.path.join(BASE_DIR, "cache", "backgrounds")
FONT_CACHE_DIR = os.path.join(BASE_DIR, "cache", "fonts")
os.makedirs(BG_CACHE_DIR, exist_ok=True)
os.makedirs(FONT_CACHE_DIR, exist_ok=True)

BUILTIN_FONTS = {
    "기본 (맑은 고딕)": None,
    "Gaegu (손글씨)": "https://raw.githubusercontent.com/google/fonts/main/ofl/gaegu/Gaegu-Regular.ttf",
    "Nanum Pen Script (나눔펜)": "https://raw.githubusercontent.com/google/fonts/main/ofl/nanumpenscript/NanumPenScript-Regular.ttf",
    "Single Day (싱글데이)": "https://raw.githubusercontent.com/google/fonts/main/ofl/singleday/SingleDay-Regular.ttf",
    "Roboto": "https://raw.githubusercontent.com/google/fonts/main/ofl/roboto/static/Roboto-Regular.ttf",
}

def _hash_key(val: str) -> str:
    return hashlib.md5(val.strip().encode("utf-8")).hexdigest()[:12]

def get_available_fonts() -> list[str]:
    """선택 가능한 폰트 목록 반환 (Google Fonts API 연동 및 기본 폰트 지원)"""
    font_list = list(BUILTIN_FONTS.keys())
    api_key = os.getenv("GOOGLE_FONTS_API_KEY", "").strip()
    if api_key:
        try:
            url = f"https://www.googleapis.com/webfonts/v1/webfonts?key={api_key}&sort=popularity"
            res = requests.get(url, timeout=4)
            if res.status_code == 200:
                data = res.json()
                for item in data.get("items", [])[:15]:
                    family = item.get("family")
                    if family and family not in font_list:
                        font_list.append(family)
        except Exception:
            pass
    return font_list

def fetch_font_file(font_family: str) -> str | None:
    """선택한 폰트의 TTF 파일을 다운로드하여 로컬 경로 반환"""
    if not font_family or font_family == "기본 (맑은 고딕)":
        return None
    out_path = os.path.join(FONT_CACHE_DIR, f"{_hash_key(font_family)}.ttf")
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1024:
        return out_path

    url = BUILTIN_FONTS.get(font_family)
    if not url:
        api_key = os.getenv("GOOGLE_FONTS_API_KEY", "").strip()
        if api_key:
            try:
                r = requests.get(f"https://www.googleapis.com/webfonts/v1/webfonts?key={api_key}", timeout=4)
                if r.status_code == 200:
                    for item in r.json().get("items", []):
                        if item.get("family") == font_family:
                            url = item.get("files", {}).get("regular")
                            break
            except Exception:
                pass
    if url:
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                with open(out_path, "wb") as f:
                    f.write(res.content)
                return out_path
        except Exception:
            pass
    return None

def fetch_unsplash_background(keyword: str, width: int = 400, height: int = 300) -> str | None:
    """Unsplash API를 통해 키워드 기반 배경 이미지를 다운로드하여 로컬 경로 반환"""
    keyword = keyword.strip()
    if not keyword:
        return None
    out_path = os.path.join(BG_CACHE_DIR, f"{_hash_key(keyword)}.jpg")
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1024:
        return out_path

    img_url = None
    access_key = os.getenv("UNSPLASH_ACCESS_KEY", "").strip()
    if access_key:
        try:
            api_url = "https://api.unsplash.com/search/photos"
            params = {"query": keyword, "per_page": 1, "orientation": "landscape"}
            headers = {"Authorization": f"Client-ID {access_key}"}
            res = requests.get(api_url, params=params, headers=headers, timeout=8)
            if res.status_code == 200:
                results = res.json().get("results", [])
                if results:
                    img_url = results[0]["urls"].get("regular") or results[0]["urls"].get("small")
        except Exception:
            pass

    # Fallback: API 키 미설정 또는 네트워크 오류 시 Picsum 시드 이미지로 대체 지원
    if not img_url:
        safe_seed = _hash_key(keyword)
        img_url = f"https://picsum.photos/seed/{safe_seed}/{width}/{height}"

    try:
        res = requests.get(img_url, timeout=10)
        if res.status_code == 200:
            with open(out_path, "wb") as f:
                f.write(res.content)
            return out_path
    except Exception:
        pass
    return None
