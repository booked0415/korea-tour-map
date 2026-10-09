#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Festival Data Updater for Korea Tourism Map
Runs periodically via GitHub Actions (Every day at 07:00 and 17:00 KST)
Features:
- Date recalibration and live D-day status updating
- TourAPI 4.0 official public data synchronization
- Google News RSS & Regional Festival Web search (including Incheon, Seoul, Gyeonggi, Busan, etc.)
- Gemini AI (Gemini 2.5/1.5) LLM-powered festival intelligence extraction and JSON structuring
"""

import os
import re
import json
import datetime
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

def parse_area_code(code_str):
    area_map = {
        "1": "서울", "2": "인천", "3": "대전", "4": "대구", "5": "광주",
        "6": "부산", "7": "울산", "8": "세종", "31": "경기", "32": "강원",
        "33": "충북", "34": "충남", "35": "경북", "36": "경남", "37": "전북",
        "38": "전남", "39": "제주"
    }
    return area_map.get(str(code_str), "전국")

def normalize_festival_core_name(name):
    """
    Extracts the core festival title to prevent duplicate entries with different edition numbers
    (e.g., '제12회 남해 독일마을 맥주축제' vs '제14회 남해 독일마을 맥주축제').
    """
    s = re.sub(r'[\d회제\(\)·\-\s]', '', name)
    s = s.replace('축제', '').replace('페스티벌', '').replace('문화', '').replace('오크토버페스트', '')
    return s

def parse_province_group(region):
    if region in ["서울", "경기", "인천"]:
        return "수도권"
    elif region in ["강원"]:
        return "강원권"
    elif region in ["충남", "충북", "대전", "세종"]:
        return "충청권"
    elif region in ["전남", "전북", "광주"]:
        return "호남권"
    elif region in ["경남", "경북", "부산", "대구", "울산"]:
        return "영남권"
    elif region in ["제주"]:
        return "제주권"
    return "전국"

def format_date_str(raw):
    raw = str(raw).strip()
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    return raw

def fetch_live_tourapi_festivals(service_key, start_yyyymmdd):
    if not service_key:
        return []
    
    clean_key = urllib.parse.unquote(service_key.strip())
    url = f"https://apis.data.go.kr/B551011/KorService1/searchFestival1?serviceKey={urllib.parse.quote(clean_key)}&eventStartDate={start_yyyymmdd}&MobileOS=ETC&MobileApp=KoreaTourMap&_type=json&numOfRows=100&pageNo=1"
    
    print(f"[*] Calling TourAPI 4.0: start date {start_yyyymmdd}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; KoreaTourMap/1.0)"})
        with urllib.request.urlopen(req, timeout=12) as response:
            if response.status != 200:
                print(f"[!] TourAPI returned status {response.status}")
                return []
            content = response.read().decode("utf-8")
            res_json = json.loads(content)
            
            body = res_json.get("response", {}).get("body", {})
            items_obj = body.get("items", {})
            if not items_obj:
                return []
            item_list = items_obj.get("item", [])
            if isinstance(item_list, dict):
                item_list = [item_list]
            
            print(f"[✓] Successfully retrieved {len(item_list)} festival items from TourAPI 4.0!")
            return item_list
    except Exception as e:
        print(f"[!] TourAPI live sync warning: {e}. Falling back to intelligence database.")
        return []

def fetch_google_news_festival_articles():
    """
    Search Google News RSS for Korean festival announcements and news across all major regions.
    """
    queries = [
        # 서울문화포털 & 서울관광정보 (VisitSeoul) 우선순위 및 공공 축제/쇼
        "site:culture.seoul.go.kr 축제 행사",
        "site:korean.visitseoul.net 행사 축제",
        "서울 축제 드론쇼 불꽃축제 한강 빛축제 야간공연",
        "서울문화포털 축제 행사 개막",
        "인천 축제 일정 개막 야행",
        "경기 축제 개막 가을 드론 불꽃",
        "부산 대구 광주 축제 문화행사",
        "가을 축제 드론라이트쇼 불꽃축제 미디어아트 야간공연"
    ]
    collected_articles = []
    seen_links = set()

    for q in queries:
        try:
            url = f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}&hl=ko&gl=KR&ceid=KR:ko"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read()
                root = ET.fromstring(content)
                for item in root.findall('./channel/item')[:8]:
                    title = item.find('title').text if item.find('title') is not None else ""
                    desc = item.find('description').text if item.find('description') is not None else ""
                    link = item.find('link').text if item.find('link') is not None else ""
                    pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                    
                    desc_clean = re.sub(r'<[^>]+>', ' ', desc).strip()
                    
                    if link and link not in seen_links and title:
                        seen_links.add(link)
                        collected_articles.append({
                            "title": title,
                            "snippet": desc_clean[:300],
                            "date": pub_date,
                            "source_url": link
                        })
        except Exception as e:
            print(f"[!] Warning fetching RSS for query '{q}': {e}")
            continue

    print(f"[*] Collected {len(collected_articles)} relevant news articles from web search.")
    return collected_articles

def extract_festivals_with_gemini(api_key, articles, today_str):
    """
    Use Gemini AI API to extract structured festival information from unstructured articles.
    """
    if not api_key or not articles:
        return []

    print(f"[*] Calling Gemini AI to analyze {len(articles)} web search articles...")
    
    # Take up to 25 most recent articles
    articles_sample = articles[:25]
    text_corpus = "\n\n".join([
        f"기사 제목: {a['title']}\n내용 요약: {a['snippet']}\n링크: {a['source_url']}"
        for a in articles_sample
    ])

    prompt = f"""당신은 대한민국 문화 관광 축제 및 공개 문화공연 전문 데이터 큐레이터입니다.
기준일(오늘): {today_str}

아래는 최근 인터넷 뉴스, 서울문화포털, 서울관광정보(VisitSeoul), 지자체 소식 등에서 수집한 최신 문화/축제/공개 공연·쇼 관련 기사들입니다.
이 기사들을 정밀하게 분석하여, 시민과 관광객을 대상으로 열리는 '축제, 문화행사, 드론 라이트 쇼, 불꽃축제, 미디어아트, 야간 불빛공연' 정보만을 추출하여 아래 JSON 형식 배열로 응답해주세요.

[추출 규칙]
1. 이미 과거에 종료된 행사는 제외하고, 현재 진행 중이거나 앞으로 개최될 축제 및 공개 쇼(드론쇼, 불꽃쇼, 야간 미디어공연 등)를 적극 추출하세요.
2. 서울문화포털 및 서울관광정보(VisitSeoul) 관련 행사와 한강 드론라이트쇼 등 시민 참여형 공개 쇼를 최우선 순위로 반영하세요.
2. 기사에 명시된 지역(인천, 서울, 수원, 부산 등)을 정확한 광역 행정구역(region: '서울', '경기', '인천', '강원', '충남', '충북', '대전', '세종', '전남', '전북', '광주', '경남', '경북', '부산', '대구', '울산', '제주' 중 하나)으로 지정하세요.
3. 장소(도시, 주소), 대략적인 위도(lat)와 경도(lng)를 대한민국 좌표계(위도 33~38.5, 경도 126~129.5) 내에서 정확히 매핑하세요.
4. 반드시 순수 JSON 배열만 출력하세요. 마크다운 코드 블록(```json ... ```) 없이 대괄호 [] 로 시작하고 끝나야 합니다.

[JSON 객체 스키마 예시 (링크 우선순위 철저 준수)]
[
  {{
    "name": "축제명 (예: 2026 인천개항장 국가유산야행)",
    "region": "인천",
    "startDate": "YYYY-MM-DD",
    "endDate": "YYYY-MM-DD",
    "address": "상세 주소 또는 개최 장소 (예: 인천 중구 신포로27번길 80)",
    "lat": 37.4745,
    "lng": 126.6214,
    "summary": "축제에 대한 핵심 소개 (1~2문장)",
    "highlights": ["핵심 볼거리1", "볼거리2", "볼거리3"],
    "tip": "방문객을 위한 꿀팁 (주차, 추천 시간대 등)",
    "fee": "무료 또는 입장료 정보",
    "websiteUrl": "1순위: 해당 축제 전용 공식 웹사이트 URL (없으면 빈 문자열)",
    "govUrl": "2순위: 지자체(시·군·구청) 또는 문화재단 등 공공기관 공식 안내 페이지 URL (없으면 빈 문자열)",
    "visitKoreaUrl": "3순위: 대한민국 구석구석, 서울문화포털, VisitSeoul 또는 관련 언론 기사 링크 URL"
  }}
]

[수집된 기사 본문]
{text_corpus}
"""

    # Dynamic model discovery from API key
    discovered_models = []
    for ver in ["v1beta", "v1"]:
        try:
            list_url = f"https://generativelanguage.googleapis.com/{ver}/models?key={api_key}"
            req = urllib.request.Request(list_url, headers={"User-Agent": "KoreaTourMap/1.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200:
                    models_data = json.loads(resp.read().decode("utf-8"))
                    for m in models_data.get("models", []):
                        m_name = m.get("name", "")
                        methods = m.get("supportedGenerationMethods", [])
                        if "generateContent" in methods:
                            clean_name = m_name.replace("models/", "")
                            discovered_models.append((ver, clean_name))
            if discovered_models:
                # Prioritize flash-lite and flash models over preview/experimental/tts
                def model_priority(item):
                    v, m = item
                    score = 100
                    if "lite" in m:
                        score -= 50
                    elif "flash" in m:
                        score -= 40
                    elif "pro" in m:
                        score -= 20
                    if "preview" in m or "tts" in m or "gemma" in m:
                        score += 50
                    return score

                discovered_models.sort(key=model_priority)
                print(f"[*] Discovered {len(discovered_models)} supported Gemini models via {ver} API! (Top choice: {discovered_models[0][1]})")
                break
        except Exception:
            continue

    if not discovered_models:
        discovered_models = [
            ("v1beta", "gemini-1.5-flash-latest"),
            ("v1", "gemini-1.5-flash"),
            ("v1beta", "gemini-1.5-flash"),
            ("v1beta", "gemini-1.5-pro"),
            ("v1beta", "gemini-2.0-flash-exp"),
            ("v1beta", "gemini-2.5-flash")
        ]

    for api_ver, model in discovered_models:
        api_url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 8192,
                "responseMimeType": "application/json"
            }
        }
        
        try:
            req = urllib.request.Request(
                api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 200:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    text = resp_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    
                    # Clean markdown code block fences if present
                    if text.startswith("```"):
                        text = re.sub(r"^```(?:json)?", "", text)
                        text = re.sub(r"```$", "", text).strip()
                    
                    festivals = json.loads(text)
                    if isinstance(festivals, list) and len(festivals) > 0:
                        print(f"[✓] Gemini ({model}) successfully extracted {len(festivals)} festivals from web search!")
                        return festivals
        except Exception as e:
            print(f"[!] Model {model} attempt error: {e}. Trying fallback...")
            continue

    print("[!] Could not extract festivals via Gemini API. Moving forward.")
    return []

def main():
    print("="*60)
    print("🚀 Starting Korea Festival Daily Auto-Update Script (AI Enhanced)")
    print("="*60)

    # 1. Calculate current KST date
    kst_tz = datetime.timezone(datetime.timedelta(hours=9))
    now_kst = datetime.datetime.now(kst_tz)
    today_str = now_kst.strftime("%Y-%m-%d")
    today_dot = now_kst.strftime("%Y.%m.%d")
    start_yyyymmdd = now_kst.strftime("%Y%m01") # first day of current month
    timestamp_str = now_kst.strftime("%Y-%m-%d %H:%M:%S KST")
    print(f"[*] Current KST Time: {timestamp_str} (Reference: {today_str})")

    index_path = "index.html"
    if not os.path.exists(index_path):
        print(f"[!] Error: {index_path} not found.")
        return

    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    # 2. Update CURRENT_DATE_STR in index.html
    date_pattern = r'const CURRENT_DATE_STR = "[^"]+";'
    new_date_def = f'const CURRENT_DATE_STR = "{today_str}";'
    html, n_sub = re.subn(date_pattern, new_date_def, html)
    print(f"[*] Updated CURRENT_DATE_STR -> {today_str} ({n_sub} replacements)")

    # 3. Update quick filter label
    chip_label_pattern = r'행사 일정 빠른 선택 \([^)]+ 기준\)'
    new_chip_label = f'행사 일정 빠른 선택 ({today_dot} 기준)'
    html, n_chip = re.subn(chip_label_pattern, new_chip_label, html)
    print(f"[*] Updated Chip Label -> {new_chip_label} ({n_chip} replacements)")

    # 4. Parse DEFAULT_DATA
    m = re.search(r'const DEFAULT_DATA = (\[.*?\]);', html)
    if not m:
        print("[!] Error: DEFAULT_DATA array not found in index.html")
        return

    data = json.loads(m.group(1))
    print(f"[*] Successfully loaded {len(data)} items from database")

    existing_names = {item['name'].replace(" ", "") for item in data}
    existing_cores = {normalize_festival_core_name(item['name']) for item in data if len(normalize_festival_core_name(item['name'])) >= 3}
    added_total = 0

    # 5. Check TourAPI Key if available in GitHub Secrets
    tour_api_key = os.environ.get("TOUR_API_KEY", "").strip()
    if tour_api_key:
        print(f"[*] TOUR_API_KEY secret detected (length {len(tour_api_key)}). Fetching live data...")
        live_items = fetch_live_tourapi_festivals(tour_api_key, start_yyyymmdd)
        
        for it in live_items:
            raw_title = it.get("title", "").strip()
            norm_title = raw_title.replace(" ", "")
            core_t = normalize_festival_core_name(raw_title)
            if not raw_title or norm_title in existing_names or (len(core_t) >= 3 and core_t in existing_cores):
                continue
            
            s_date = format_date_str(it.get("eventstartdate", ""))
            e_date = format_date_str(it.get("eventenddate", ""))
            if not s_date or not e_date:
                continue

            region = parse_area_code(it.get("areacode", ""))
            prov_group = parse_province_group(region)
            addr = it.get("addr1", "").strip() or f"{region} 행사 일원"
            
            lat = float(it["mapy"]) if it.get("mapy") else 37.5665
            lng = float(it["mapx"]) if it.get("mapx") else 126.9780

            new_item = {
                "id": f"tourapi-live-{it.get('contentid', len(data)+1)}",
                "name": raw_title,
                "type": "festival",
                "category": "축제/행사",
                "region": region,
                "provinceGroup": prov_group,
                "season": "가을",
                "startDate": s_date,
                "endDate": e_date,
                "period": f"{s_date} ~ {e_date}",
                "lat": lat,
                "lng": lng,
                "address": addr,
                "summary": f"한국관광공사 TourAPI 4.0 실시간 연동 축제입니다. {addr}에서 열립니다.",
                "highlights": ["공공데이터 실시간 축제", "현장 체험", "문화 행사"],
                "tip": "상세 프로그램 및 주차 정보는 공식 문의처를 통해 확인하시기 바랍니다.",
                "fee": "무료 (일부 체험 프로그램 별도)",
                "phone": it.get("tel", "공식 안내처 문의"),
                "visitKoreaUrl": f"https://korean.visitkorea.or.kr/detail/ms_detail.do?cotid={it.get('contentid', '')}",
                "tags": ["공공데이터연동", "TourAPI", region, "문화관광축제"]
            }
            data.append(new_item)
            existing_names.add(norm_title)
            if len(core_t) >= 3:
                existing_cores.add(core_t)
            added_total += 1

    # 6. Check GEMINI_API_KEY secret and run Web Search + AI Extraction
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if gemini_key:
        print(f"[*] GEMINI_API_KEY secret detected (length {len(gemini_key)}). Starting AI Web Search...")
        articles = fetch_google_news_festival_articles()
        ai_festivals = extract_festivals_with_gemini(gemini_key, articles, today_str)
        
        gemini_added = 0
        for f_item in ai_festivals:
            name = f_item.get("name", "").strip()
            norm = name.replace(" ", "")
            core_t = normalize_festival_core_name(name)
            if not name or norm in existing_names or (len(core_t) >= 3 and core_t in existing_cores):
                continue

            s_date = f_item.get("startDate", "")
            e_date = f_item.get("endDate", "")
            if not s_date or not e_date:
                continue

            region = f_item.get("region", "전국")
            prov_group = parse_province_group(region)
            addr = f_item.get("address", f"{region} 일원")
            lat = float(f_item.get("lat", 37.5665))
            lng = float(f_item.get("lng", 126.9780))

            ai_entry = {
                "id": f"gemini-ai-{len(data)+1}",
                "name": name,
                "type": "festival",
                "category": "축제/행사",
                "region": region,
                "provinceGroup": prov_group,
                "season": "가을",
                "startDate": s_date,
                "endDate": e_date,
                "period": f"{s_date} ~ {e_date}",
                "lat": lat,
                "lng": lng,
                "address": addr,
                "summary": f_item.get("summary", f"{name} 축제 정보입니다."),
                "highlights": f_item.get("highlights", ["웹서칭 AI 발굴", "문화 축제", "현장 체험"]),
                "tip": f_item.get("tip", "행사 세부 일정은 기상 및 주최측 사정에 따라 변동될 수 있습니다."),
                "fee": f_item.get("fee", "무료/유료 현장 문의"),
                "phone": "주최 측 문의",
                "websiteUrl": f_item.get("websiteUrl", ""),
                "govUrl": f_item.get("govUrl", ""),
                "visitKoreaUrl": f_item.get("visitKoreaUrl") or f_item.get("sourceUrl") or "https://korean.visitkorea.or.kr",
                "tags": ["AI자동수집", "웹서칭연동", region, "인기축제"]
            }
            data.append(ai_entry)
            existing_names.add(norm)
            if len(core_t) >= 3:
                existing_cores.add(core_t)
            gemini_added += 1
            added_total += 1

        if gemini_added > 0:
            print(f"[✓] Added {gemini_added} brand new festivals discovered via Gemini AI Web Search!")
    else:
        print("[*] No GEMINI_API_KEY provided. Web search AI extraction skipped.")

    if added_total > 0:
        print(f"[✓] Total new festival items added to database: {added_total}")
    else:
        print("[*] All latest items are up to date.")

    # 7. Recalibrate D-days and status for all festivals
    stats = {"ongoing": 0, "upcoming": 0, "closed": 0, "always": 0}
    for item in data:
        if item.get("type") == "attraction":
            stats["always"] += 1
            continue

        start = item.get("startDate", "")
        end = item.get("endDate", "")
        if not start or not end:
            stats["always"] += 1
            continue

        if today_str < start:
            stats["upcoming"] += 1
        elif today_str > end:
            stats["closed"] += 1
        else:
            stats["ongoing"] += 1

    print(f"[*] Status distribution as of {today_str}: {stats}")

    # 8. Increment cache version to ensure browsers load fresh data
    cur_v_match = re.search(r'korea_tourism_database_v(\d+)', html)
    if cur_v_match:
        cur_v = int(cur_v_match.group(1))
        new_v = cur_v + 1
        html = html.replace(f'korea_tourism_database_v{cur_v}', f'korea_tourism_database_v{new_v}')
        html = html.replace(f'korea_travel_bookmarks_v{cur_v}', f'korea_travel_bookmarks_v{new_v}')
        print(f"[*] Incremented database cache version: v{cur_v} -> v{new_v}")

    # 9. Re-insert updated DEFAULT_DATA into index.html
    new_json = json.dumps(data, ensure_ascii=False)
    html = html[:m.start(1)] + new_json + html[m.end(1):]

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[✓] Successfully wrote updated index.html! (Total length: {len(html)} bytes)")
    print("="*60)

if __name__ == "__main__":
    main()
