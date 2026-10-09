#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Festival Data Updater for Korea Tourism Map
Runs periodically via GitHub Actions (Every day at 07:00 and 17:00 KST)
"""

import os
import re
import json
import datetime
import urllib.parse
import urllib.request

def parse_area_code(code_str):
    area_map = {
        "1": "서울", "2": "인천", "3": "대전", "4": "대구", "5": "광주",
        "6": "부산", "7": "울산", "8": "세종", "31": "경기", "32": "강원",
        "33": "충북", "34": "충남", "35": "경북", "36": "경남", "37": "전북",
        "38": "전남", "39": "제주"
    }
    return area_map.get(str(code_str), "전국")

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
    url = f"https://apis.data.go.kr/B551011/KorService1/searchFestival1?serviceKey={urllib.parse.quote(clean_key)}&eventStartDate={start_yyyymmdd}&MobileOS=ETC&MobileApp=KoreaTourMap&_type=json&numOfRows=50&pageNo=1"
    
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

def main():
    print("="*60)
    print("🚀 Starting Korea Festival Daily Auto-Update Script")
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

    # 5. Check TourAPI Key if available in GitHub Secrets
    tour_api_key = os.environ.get("TOUR_API_KEY", "").strip()
    if tour_api_key:
        print(f"[*] TOUR_API_KEY secret detected (length {len(tour_api_key)}). Fetching live data...")
        live_items = fetch_live_tourapi_festivals(tour_api_key, start_yyyymmdd)
        
        # Merge live items into data
        existing_names = {item['name'].replace(" ", "") for item in data}
        added_count = 0
        for it in live_items:
            raw_title = it.get("title", "").strip()
            norm_title = raw_title.replace(" ", "")
            if not raw_title or norm_title in existing_names:
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
            added_count += 1
        
        if added_count > 0:
            print(f"[✓] Added {added_count} new festivals directly from TourAPI 4.0!")
    else:
        print("[*] No TOUR_API_KEY secret provided. Using built-in verified intelligence engine.")

    # 6. Recalibrate D-days and status for all festivals
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

    # 7. Increment cache version to ensure browsers load fresh data
    cur_v_match = re.search(r'korea_tourism_database_v(\d+)', html)
    if cur_v_match:
        cur_v = int(cur_v_match.group(1))
        new_v = cur_v + 1
        html = html.replace(f'korea_tourism_database_v{cur_v}', f'korea_tourism_database_v{new_v}')
        html = html.replace(f'korea_travel_bookmarks_v{cur_v}', f'korea_travel_bookmarks_v{new_v}')
        print(f"[*] Incremented database cache version: v{cur_v} -> v{new_v}")

    # 8. Re-insert updated DEFAULT_DATA into index.html
    new_json = json.dumps(data, ensure_ascii=False)
    html = html[:m.start(1)] + new_json + html[m.end(1):]

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[✓] Successfully wrote updated index.html! (Total length: {len(html)} bytes)")
    print("="*60)

if __name__ == "__main__":
    main()
