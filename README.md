# 🗺️ 대한민국 관광·축제 인터랙티브 지도 웹앱 (Korea Tour Map)

대한민국 전국 17개 시·도 및 8도 광역 지역의 대표 축제와 문화행사를 실시간으로 조회하고 나만의 여행 코스를 계획할 수 있는 네이버·구글 지도 스타일의 고성능 반응형 PWA(Progressive Web App) 웹 애플리케이션입니다.

---

## 🌟 주요 기능

### 1. 실시간 축제 일정 및 라이브 상태 자동 판별
- **오늘 진행중 (LIVE)**: 현재 한국 표준시(KST) 날짜 기준으로 현장에서 열리고 있는 축제·행사 실시간 자동 필터링
- **개최 예정 (D-Day)**: 개막 D-Day 카운트다운 자동 계산
- **상시 운영 / 지난 축제(종료)**: 사계절 상시 명소 및 이미 종료된 축제 상태 자동 분류 및 스마트 필터링

### 2. 스마트 검색 및 접이식 필터 (Collapsible Filter UI)
- **사이드바 기본 접힘(Collapsed by Default)**: 초기 진입 시 화면 85% 이상을 행사 카드 목록으로 시원하게 확보
- **상세 필터 원클릭 토글**: `[상세 필터 펼치기 ▼]` 버튼을 통해 기간, 8도 지역, 동행자 큐레이션, 카테고리, 반경 필터를 자유롭게 제어
- **키워드 실시간 검색**: 축제명, 행사장소, 해시태그 기반 즉시 검색

### 3. 네이버 지도 & 카카오맵 공식 길찾기 100% 정상 연동
- 축제명이 아닌 **공식 홈페이지 "오시는 길" 기준 정제 도로명/지번 주소** 및 **실제 육지 진입로 좌표**를 목적지로 전달
- 네이버 지도 서비스 오류 및 카카오맵 수면(강물 위) 마커 이탈 현상을 원천 해결하여 클릭 즉시 대중교통·자가용 경로 안내

### 4. 실효성 검증 공식 홈페이지 및 예약 딥링크 매핑
- 단순 기관 메인 홈이 아닌, **실제 행사 포스터 및 세부 프로그램이 확인되는 공식 전용 홈페이지, 예약 페이지, 공식 SNS**를 1순위로 우선 연동
- 공식 전용 사이트가 없는 경우 지자체 공식 공고 및 서울문화포털 상세 페이지로 자동 매핑

### 5. 내 여행 코스 담기 & 최단 동선 최적화 (Smart Planner)
- 마음에 드는 축제를 '내 코스'에 저장하고, 카드를 길게 눌러 이동(드래그 앤 드롭)하거나 **[⚡ 최단 동선 정렬]** 버튼으로 최적 방문 순서 자동 계산
- 실제 도로망(OSRM) 기반 주행 곡선 표출 및 당일 현장 스마트 네비게이션 모드 탑재

### 6. PWA (Progressive Web App) 모바일 전체화면 앱 지원
- PC 및 모바일(iOS/Android) 브라우저에서 '홈 화면에 추가'를 통해 앱스토어 설치 없이 네이티브 앱처럼 전체화면으로 사용 가능

---

## ⚙️ 하이 레벨 무인 자동화 아키텍처 (Google Sheets ➔ GitHub Actions ➔ Vercel)

불안정한 외부 웹 크롤링이나 복잡한 API 키 관리 없이, **"AI & 사용자 검증 ➔ 구글 시트 허브 ➔ 깃허브 봇 초고속 배포"**로 이어지는 견고한 무장애 파이프라인으로 운영됩니다.

```
[1. AI 정기 조사 & 사용자 직접 입력]
├─ 실시간 팩트체크 및 주소/일정/공식링크 정밀 교차 검증
└─ '취소'된 축제 및 신규 개막 축제를 구글 시트에 실시간 반영
         │
         ▼
[2. 구글 스프레드시트 실시간 데이터 허브]
└─ URL: https://docs.google.com/spreadsheets/d/1tC4MDTWus7mt3AWD1m3DNIhGwTYjAMV7EZSpsrNAiYA/edit
         │
         ▼
[3. GitHub Actions 무인 봇: scripts/update_festivals.py]
├─ 매일 4회 자동 실행 (한국 시간 07:23, 13:23, 19:23, 01:23 KST / 6시간 간격)
├─ 구글 시트 CSV 피드를 실시간 호출하여 취소 축제 즉시 제외 및 신규 축제 자동 병합
├─ 오늘(KST) 날짜 기준 진행중/종료/예정 상태 및 D-Day 자동 재계산
├─ 육지 진입로 좌표 및 공식 딥링크 자동 교정(Auto-Calibrate)
└─ 브라우저 로컬스토리지 캐시 버전(vXX) 자동 판올림 및 index.html 커밋
         │
         ▼
[4. Vercel 프로덕션 자동 배포]
└─ 깃허브 커밋 발생 즉시 5초 만에 감지하여 글로벌 Edge CDN 웹앱 실시간 배포
```

---

## 🔑 환경 설정 (선택 사항)

GitHub 저장소 `Settings > Secrets and variables > Actions`에 아래 환경변수를 등록할 수 있으며, 미등록 시에도 기본 연동 시트 ID가 안전하게 적용됩니다.

| Secret 이름 | 설명 | 기본값 |
| :--- | :--- | :--- |
| `FESTIVAL_SHEET_URL` | 연동할 구글 스프레드시트의 공유 URL 또는 시트 ID | 기본 시트 자동 매핑 |

---

## 📱 기술 스택 (Tech Stack)

- **Frontend**: HTML5, Vanilla JavaScript (ES6+), CSS3 (Flexbox/Grid), Leaflet.js
- **Data Hub**: Google Sheets (Real-time CSV Feed)
- **Automation Engine**: Python 3.11 (Standard Library, Zero-dependency), GitHub Actions (Scheduled Cron)
- **Deployment**: Vercel (Global Edge CDN), PWA (Service Worker & Web App Manifest)
