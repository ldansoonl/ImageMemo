# 📌 ImageMemo (바탕화면 이미지 메모)

> **Windows 바탕화면에 감각적인 맞춤형 메모를 실시간으로 합성·배치하는 GUI 프로그램**  
> Unsplash의 고화질 이미지 배경과 Google Fonts의 다양한 글씨체를 연동하여 나만의 메모 위젯을 바탕화면에 직접 렌더링합니다.

---

## 📑 목차
1. [프로젝트 개요 & 주요 기능](#1-프로젝트-개요--주요-기능)
2. [프로젝트 아키텍처 및 모듈별 코드 설명](#2-프로젝트-아키텍처-및-모듈별-코드-설명)
3. [API Key 발급 및 설정 가이드](#3-api-key-발급-및-설정-가이드)
4. [설치 및 실행 방법](#4-설치-및-실행-방법)
5. [데이터 영속성 및 캐시 동작 방식](#5-데이터-영속성-및-캐시-동작-방식)

---

## 1. 프로젝트 개요 & 주요 기능

ImageMemo는 복잡한 상용 위젯 프로그램 없이, Python과 기본 윈도우 API(`user32`)만을 활용해 **Windows 바탕화면 배경 이미지 자체에 메모를 합성하여 띄워주는 경량 애플리케이션**입니다.

- **직관적인 메모 관리**: 메모 추가, 수정, 삭제를 간편한 GUI로 조작
- **크기 및 위치 자유 배치**:
  - 메모 가로/세로 슬라이더 크기 조절
  - 미니 캔버스를 통한 마우스 드래그 앤 드롭 화면 배치
- **외부 API 연동**:
  - **Unsplash API**: 키워드 입력(예: `sky`, `coffee`, `paper`)으로 감성적인 배경 텍스처 자동 다운로드 및 적용
  - **Google Fonts API**: 인기 웹폰트 목록 실시간 조회 및 TTF 다운로드 적용
- **지능형 가독성 처리**:
  - 배경 밝기(Luminance)를 자동 감지하여 어두운 배경에는 밝은 텍스트, 밝은 배경에는 어두운 텍스트와 섀도우를 자동 적용
- **무중단 Fallback 지원**:
  - API 키가 없거나 인터넷이 끊겨도 기본 포스트잇 스타일 및 대체 이미지/기본 폰트로 정상 동작

---

## 2. 프로젝트 아키텍처 및 모듈별 코드 설명

```
wi/
├── image_memo.py       # [UI/Controller] Tkinter 기반 대화형 GUI
├── wallpaper.py        # [Rendering/OS] Pillow 메모 합성 & 윈도우 배경화면 반영
├── api_service.py      # [Network/Cache] Unsplash & Google Fonts API 통신
├── .env.example        # 환경변수(API Key) 설정 템플릿
├── .gitignore          # 민감정보(.env) 및 캐시/임시 파일 제외
├── memos.json          # 메모 위치, 크기, 스타일 데이터 영구 저장 (자동 생성)
└── cache/              # 다운로드된 폰트 및 배경 이미지 로컬 캐시 (자동 생성)
    ├── backgrounds/
    └── fonts/
```

### 1) `image_memo.py` (사용자 인터페이스 & 컨트롤러)
- **역할**: 사용자 입력을 처리하고 프로그램의 상태를 제어하는 진입점입니다.
- **주요 클래스 & 메서드**:
  - `MemoApp`: 메인 Tkinter 윈도우 및 메모 목록(`Listbox`) 구성
  - `open_memo_window()`: 메모 내용 작성, Unsplash 키워드 및 Google Fonts 선택 팝업
  - `open_resize_window()`: 가로(150~600px), 세로(100~500px) 슬라이더를 통한 크기 제어
  - `open_arrange_window()`: 모니터 화면 비율을 축소한 캔버스에서 마우스 드래그로 메모 위치(`x`, `y`)를 재배치
  - `apply_wallpaper()`: 변경된 메모 데이터를 저장하고 바탕화면 갱신 호출

### 2) `wallpaper.py` (이미지 렌더링 & 윈도우 OS 연동)
- **역할**: 메모 데이터를 바탕으로 모니터 해상도에 맞춘 전체 배경 이미지를 생성하고 윈도우 바탕화면으로 등록합니다.
- **주요 함수**:
  - `get_screen_size()`: `ctypes.windll.user32` DPI 인식을 활성화하여 모니터의 실제 가로/세로 해상도를 픽셀 단위로 정확히 추출
  - `create_rounded_mask()`: 메모지 모서리를 부드러운 라운드(기본 반경 14px) 형태로 마스킹
  - `render_wallpaper_pil()`:
    - 개별 메모의 배경 이미지 리사이즈 및 합성 (이미지가 없을 시 클래식 옐로우 포스트잇 색상 칠하기)
    - `ImageStat.Stat`으로 배경 명암을 분석하여 글자색 및 그림자 대비 자동 보정
    - 줄바꿈(`\n`) 처리 및 텍스트 렌더링
  - `update_wallpaper()`: 완성된 이미지를 PNG로 저장 후 `SystemParametersInfoW(20, 0, path, 3)` Windows API를 호출해 바탕화면 즉각 적용
  - `clean_old_wallpapers()`: 바탕화면 갱신 시 누적되는 이전 타임스탬프 임시 이미지 자동 삭제

### 3) `api_service.py` (API 연동 & 로컬 캐싱)
- **역할**: Unsplash 및 Google Fonts와 HTTP 통신을 수행하며, 트래픽 절약 및 속도 향상을 위해 로컬 파일 캐시를 관리합니다.
- **주요 기능**:
  - `python-dotenv`를 통한 `.env` 파일의 API Key 로드
  - MD5 해시(`_hash_key`) 기반 캐싱: 키워드나 폰트명을 해시화하여 `cache/` 디렉터리에 보관, 중복 요청 방지
  - `get_available_fonts()` / `fetch_font_file()`:
    - 내장 기본 폰트(맑은 고딕, Gaegu, Nanum Pen Script, Single Day, Roboto) 기본 탑재
    - Google Fonts API 키 등록 시 인기 폰트 15종을 실시간으로 가져와 TTF 파일 로드
  - `fetch_unsplash_background()`:
    - Unsplash Search API(`https://api.unsplash.com/search/photos`) 호출
    - **Fallback 기능**: API 키 미설정 또는 할당량 초과 시 `Picsum Photos` 시드 이미지를 대신 활용해 끊김 없는 사용자 경험 제공

---

## 3. API Key 발급 및 설정 가이드

API Key를 등록하면 고해상도 Unsplash 이미지 검색과 실시간 Google Fonts 카탈로그를 온전히 활용할 수 있습니다. (미등록 시에도 기본 내장 기능으로 작동합니다.)

### 1단계: API Key 발급

#### A. Unsplash Access Key 발급
1. [Unsplash Developers](https://unsplash.com/developers)에 접속하여 로그인합니다.
2. 상단 메뉴의 **Your Apps** → **New Application**을 클릭합니다.
3. 약관에 동의한 후 애플리케이션 이름(예: `ImageMemo`)을 입력하고 앱을 생성합니다.
4. 생성된 앱 상세 페이지의 **Keys** 섹션에서 **Access Key** 값을 복사합니다.

#### B. Google Fonts Developer API Key 발급
1. [Google Cloud Console](https://console.cloud.google.com/)에 접속하여 로그인합니다.
2. 새 프로젝트를 생성하거나 기존 프로젝트를 선택합니다.
3. **API 및 서비스** → **라이브러리**로 이동하여 **"Web Fonts Developer API"**를 검색한 뒤 **사용(Enable)**을 클릭합니다.
4. **API 및 서비스** → **사용자 인증 정보**로 이동하여 **사용자 인증 정보 만들기** → **API 키**를 선택합니다.
5. 생성된 API 키 문자열을 복사합니다.

---

### 2단계: 프로젝트에 `.env` 파일 생성 및 키 등록

1. 프로젝트 루트 폴더에 위치한 `.env.example` 파일을 복사하여 이름을 `.env`로 변경합니다.
   ```powershell
   # Windows PowerShell 기준
   Copy-Item .env.example .env
   ```
2. 텍스트 편집기(VS Code, 메모장 등)로 `.env` 파일을 열고 복사한 키 값을 입력합니다.

```env
# Unsplash API Access Key (https://unsplash.com/developers)
UNSPLASH_ACCESS_KEY=your_unsplash_access_key_here

# Google Fonts Developer API Key (https://developers.google.com/fonts/docs/developer_api)
GOOGLE_FONTS_API_KEY=your_google_fonts_api_key_here
```

> ⚠️ **주의사항 (보안)**:  
> `.env` 파일에는 개인 인증 정보가 포함되어 있으므로 Git 저장소에 커밋되지 않도록 `.gitignore`에 이미 등록되어 있습니다. 외부로 유출되지 않도록 주의하세요.

---

## 4. 설치 및 실행 방법

### 요구 환경
- **운영체제**: Windows 10 / 11 (Windows API 사용)
- **Python 버전**: Python 3.9 이상 권장

### 1) 의존 패키지 설치
터미널에서 아래 명령어를 실행하여 필요한 라이브러리를 설치합니다.
```powershell
pip install pillow requests python-dotenv
```

### 2) 프로그램 실행
```powershell
python image_memo.py
```

---

## 5. 데이터 영속성 및 캐시 동작 방식

- **메모 데이터 저장 (`memos.json`)**:
  - 작성한 모든 메모(내용, 위치 X/Y, 크기 W/H, 지정 배경 키워드, 폰트 종류)는 프로그램 종료 후에도 `memos.json`에 저장되어 유지됩니다.
- **캐시 정책 (`cache/`)**:
  - 한 번 다운로드된 배경 이미지와 폰트는 해시 파일명으로 로컬에 영구 캐시되어, 다음 실행 시 네트워크 요청 없이 즉각 렌더링됩니다.
  - 캐시를 비우고 새로 받고 싶다면 `cache/` 폴더 내부 파일들을 삭제하시면 됩니다.
