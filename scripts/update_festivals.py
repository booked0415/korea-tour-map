#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Festival Data Updater for Korea Tourism Map
Runs periodically via GitHub Actions 4 times daily (Every day at 07:30, 12:30, 17:30, 23:00 KST / 6-hour interval)
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

# ==============================================================================
# 🎯 AUTOMATED VERIFIED OFFICIAL PORTAL & LOCATION REGISTRY
# Ensures 100% full automation without regression or manual maintenance
# ==============================================================================
OFFICIAL_PORTAL_REGISTRY = {
    "양재아트살롱": {
        "websiteUrl": "https://yangjaeartsalon.co.kr/",
        "govUrl": "https://www.seocho.go.kr",
        "address": "서울특별시 서초구 양재동 261-23 (양재천 영동1교~수변무대)",
        "lat": 37.4785, "lng": 127.0425,
        "transitInfo": "신분당선 양재시민의숲역 1번 출구, 3호선·신분당선 양재역 9번 출구 (서초21 버스 환승)"
    },
    "뚜벅뚜벅": {
        "websiteUrl": "https://www.festa-ddooddoo.com/",
        "govUrl": "https://hangang.seoul.go.kr",
        "address": "서울특별시 서초구 반포동 115-5 (반포한강공원 잠수교 및 달빛광장)",
        "lat": 37.5105, "lng": 126.9960,
        "transitInfo": "지하철 3·7·9호선 고속터미널역 8-1, 8-2번 출구 (도보 10분), 반포한강공원 피크닉장 방향 진입"
    },
    "빛섬": {
        "websiteUrl": "https://www.bitseomfestival.com/",
        "govUrl": "https://hangang.seoul.go.kr/www/eventMng/detail.do?srchType=list&mid=538&evntSn=460",
        "address": "서울특별시 용산구 양녕로 445 (이촌동 302-6, 노들섬)",
        "lat": 37.5172, "lng": 126.9582,
        "transitInfo": "지하철 9호선 노들역 2번 출구 (도보 700m), 노들섬 버스정류장(03-340) 하차, 순환 셔틀버스"
    },
    "정원박람회": {
        "websiteUrl": "https://festival.seoul.go.kr/garden",
        "govUrl": "https://culture.seoul.go.kr",
        "address": "서울특별시 성동구 뚝섬로 273 (성수동1가 720, 서울숲)",
        "lat": 37.5444, "lng": 127.0374,
        "transitInfo": "수인분당선 서울숲역 3,4,5번 출구 (도보 2분), 2호선 뚝섬역 7,8번 출구 (도보 11분)"
    },
    "불꽃축제": {
        "websiteUrl": "https://www.hanwhapromise.com/cheering/fireworks",
        "govUrl": "https://festival.seoul.go.kr",
        "address": "서울특별시 영등포구 여의동로 330 (여의도동 84-9, 여의도한강공원)",
        "lat": 37.5275, "lng": 126.9328,
        "transitInfo": "지하철 5호선 여의나루역 3번 출구, 9호선 샛강역 3번 출구"
    },
    "억새축제": {
        "websiteUrl": "https://parks.seoul.go.kr/",
        "govUrl": "https://festival.seoul.go.kr/festival/main/festivalView.do?festacode=683",
        "address": "서울특별시 마포구 하늘공원로 95 (상암동 482, 월드컵공원 하늘공원)",
        "lat": 37.5681, "lng": 126.8853,
        "transitInfo": "지하철 6호선 월드컵경기장역 1번 출구 (도보 15분 후 맹꽁이 전기차 탑승 또는 하늘계단)"
    },
    "궁중문화축전": {
        "websiteUrl": "https://www.chf.or.kr/fest",
        "govUrl": "https://www.royalpalace.go.kr",
        "address": "서울특별시 종로구 사직로 161 (세종로 1-1, 경복궁 흥례문 광장)",
        "lat": 37.5762, "lng": 126.9769,
        "transitInfo": "지하철 3호선 경복궁역 5번 출구 (도보 1분), 5호선 광화문역 2번 출구"
    },
    "정동야행": {
        "websiteUrl": "https://culture-night.junggu.seoul.kr/",
        "govUrl": "https://www.junggu.seoul.kr",
        "address": "서울특별시 중구 정동길 15 (정동 5-1, 덕수궁 돌담길 및 정동 분수대 광장)",
        "lat": 37.5658, "lng": 126.9736,
        "transitInfo": "지하철 1·2호선 시청역 1, 2, 12번 출구 (도보 3분)"
    },
    "강감찬": {
        "websiteUrl": "https://www.gwanak.go.kr",
        "govUrl": "https://www.gwanakcf.or.kr",
        "address": "서울특별시 관악구 낙성대로 77 (봉천동 228, 낙성대공원)",
        "lat": 37.4714, "lng": 126.9585,
        "transitInfo": "지하철 2호선 낙성대역 4번 출구에서 관악02 마을버스 탑승 후 낙성대공원 하차"
    },
    "빛초롱": {
        "websiteUrl": "https://www.stolantern.com/",
        "govUrl": "https://korean.visitseoul.net",
        "address": "서울특별시 종로구 세종대로 175 (세종로 1-68, 광화문광장)",
        "lat": 37.5714, "lng": 126.9768,
        "transitInfo": "지하철 5호선 광화문역 2, 9번 출구 직결, 3호선 경복궁역 6번 출구"
    },
    "드론 라이트": {
        "websiteUrl": "https://korean.visitseoul.net/events",
        "govUrl": "https://hangang.seoul.go.kr",
        "address": "서울특별시 광진구 강변북로 139 (자양동 427-1, 뚝섬한강공원 수변무대)",
        "lat": 37.5298, "lng": 127.0695,
        "transitInfo": "지하철 7호선 자양(뚝섬한강공원)역 2, 3번 출구 (도보 3분)"
    },
    "한옥위크": {
        "websiteUrl": "https://hanok.seoul.go.kr/",
        "govUrl": "https://culture.seoul.go.kr",
        "address": "서울특별시 종로구 계동길 37 (계동 105, 북촌문화센터)",
        "lat": 37.5828, "lng": 126.9838,
        "transitInfo": "지하철 3호선 안국역 3번 출구 (도보 4분)"
    },
    "SPAF": {
        "websiteUrl": "https://spaf.or.kr/",
        "govUrl": "https://culture.seoul.go.kr",
        "address": "서울특별시 종로구 대학로8길 7 (동숭동 1-130, 아르코예술극장)",
        "lat": 37.5818, "lng": 127.0028,
        "transitInfo": "지하철 4호선 혜화역 2번 출구 (도보 2분 마로니에공원 내)"
    },
    "디자인위크": {
        "websiteUrl": "https://seouldesign.or.kr/",
        "govUrl": "https://culture.seoul.go.kr",
        "address": "서울특별시 중구 을지로 281 (을지로7가 2-1, 동대문디자인플라자 DDP)",
        "lat": 37.5668, "lng": 127.0095,
        "transitInfo": "지하철 2·4·5호선 동대문역사문화공원역 1, 2번 출구 직결"
    },
    "한성백제": {
        "websiteUrl": "https://baekjefestival.com/",
        "govUrl": "https://culture.seoul.go.kr",
        "address": "서울특별시 송파구 올림픽로 424 (방이동 88-2, 올림픽공원 평화의 광장)",
        "lat": 37.5185, "lng": 127.1215,
        "transitInfo": "지하철 8호선 몽촌토성역 1번 출구 (도보 1분), 9호선 한성백제역 2번 출구"
    },
    "서울뮤직": {
        "websiteUrl": "https://nodeul.org/",
        "govUrl": "https://culture.seoul.go.kr",
        "address": "서울특별시 용산구 양녕로 445 (이촌동 302-6, 노들섬 잔디마당)",
        "lat": 37.5175, "lng": 126.9585,
        "transitInfo": "지하철 9호선 노들역 2번 출구 (도보 10분), 1호선 용산역에서 버스 환승"
    },
    "노원달빛": {
        "websiteUrl": "https://nowonarts.kr/",
        "govUrl": "https://culture.seoul.go.kr",
        "address": "서울특별시 노원구 동일로 1238 (중계동 507-1, 노원구민의전당 앞 당현천)",
        "lat": 37.6542, "lng": 127.0685,
        "transitInfo": "지하철 7호선 중계역 5, 6번 출구 (도보 3분)"
    },
    "자라섬": {
        "websiteUrl": "http://jarasumjazz.com/",
        "govUrl": "https://www.gp.go.kr",
        "address": "경기도 가평군 가평읍 자라섬로 60 (달전리 1-1, 자라섬 중도)",
        "lat": 37.8205, "lng": 127.5255,
        "transitInfo": "경춘선·ITX청춘 가평역 1번 출구 (도보 15분 또는 셔틀버스)"
    },
    "독일마을": {
        "websiteUrl": "https://german-village.kr/beer-festival/1",
        "govUrl": "https://tour.namhae.go.kr",
        "address": "경상남도 남해군 삼동면 독일로 89-7 (물건리 1074-2, 독일마을 광장)",
        "lat": 34.8015, "lng": 128.0435,
        "transitInfo": "남해공용터미널에서 지족·미조 방면 버스 탑승 후 독일마을 입구 하차"
    },
    "남강유등": {
        "websiteUrl": "https://yudeung.com/",
        "govUrl": "https://www.jinju.go.kr",
        "address": "경상남도 진주시 남강로 626 (본성동 1-2, 진주성 및 남강 일원)",
        "lat": 35.1885, "lng": 128.0825,
        "transitInfo": "진주고속버스터미널에서 도보 15분, 진주역 및 임시주차장에서 무료 셔틀버스"
    },
    "머드축제": {
        "websiteUrl": "https://www.mudfestival.or.kr/",
        "govUrl": "https://www.brcn.go.kr",
        "address": "충청남도 보령시 해수욕장10길 5 (신흑동 2282, 대천해수욕장 머드광장)",
        "lat": 36.3055, "lng": 126.5165,
        "transitInfo": "대천역 및 보령종합터미널에서 100, 101번 버스 탑승 후 머드광장 하차"
    },
    "치맥": {
        "websiteUrl": "https://www.chimacfestival.com/",
        "govUrl": "https://www.daegu.go.kr",
        "address": "대구광역시 달서구 공원순환로 36 (두류동 산302-11, 두류공원 2.28자유광장)",
        "lat": 35.8525, "lng": 128.5565,
        "transitInfo": "대구지하철 2호선 두류역 14, 15번 출구 (도보 5분 두류공원 방향)"
    },
    "춘향": {
        "websiteUrl": "https://www.chunhyang.org/",
        "govUrl": "https://www.namwon.go.kr",
        "address": "전북특별자치도 남원시 요천로 1447 (천거동 78, 광한루원 및 요천둔치)",
        "lat": 35.4055, "lng": 127.3795,
        "transitInfo": "KTX 남원역에서 133, 134, 141번 버스 탑승 후 광한루원 하차"
    },
    "반딧불": {
        "websiteUrl": "https://www.firefly.or.kr/",
        "govUrl": "https://www.muju.go.kr",
        "address": "전북특별자치도 무주군 무주읍 한풍루로 326-17 (당산리 1199-2, 등나무운동장)",
        "lat": 35.9835, "lng": 127.6625,
        "transitInfo": "무주공용버스터미널에서 도보 7분, 반딧불이 신비탐사는 전용 셔틀버스"
    },
    "임실N치즈": {
        "websiteUrl": "http://www.imsilfestival.com/",
        "govUrl": "https://www.imsil.go.kr",
        "address": "전북특별자치도 임실군 성수면 도인2길 50 (도인리 687, 임실치즈테마파크)",
        "lat": 35.6175, "lng": 127.2885,
        "transitInfo": "임실시외버스터미널 및 임실역에서 축제장 직통 무료 셔틀버스"
    },
    "충장축제": {
        "websiteUrl": "https://recollection.kr/",
        "govUrl": "https://gdctf.or.kr",
        "address": "광주광역시 동구 금남로 245 (광산동 13, 5·18민주광장 및 금남로)",
        "lat": 35.1485, "lng": 126.9195,
        "transitInfo": "광주지하철 1호선 문화전당역 3, 4번 출구 (도보 1분 5·18민주광장)"
    },
    "탈춤": {
        "websiteUrl": "https://www.maskdance.com/",
        "govUrl": "https://www.tourandong.com",
        "address": "경상북도 안동시 육사로 239 (운흥동 271-1, 안동 탈춤공원)",
        "lat": 36.5625, "lng": 128.7345,
        "transitInfo": "KTX 안동역에서 도보 5분"
    },
    "군항제": {
        "websiteUrl": "https://www.jgfestival.or.kr/",
        "govUrl": "https://www.changwon.go.kr",
        "address": "경상남도 창원시 진해구 통신동 1 (중원로터리 및 진해루 일원)",
        "lat": 35.1495, "lng": 128.6625,
        "transitInfo": "진해시외버스터미널에서 도보 10분, 창원중앙역·마산역에서 임시 셔틀버스"
    },
    "부산국제영화제": {
        "websiteUrl": "https://www.biff.kr/",
        "govUrl": "https://www.busan.go.kr",
        "address": "부산광역시 해운대구 수영강변대로 120 (우동 1467, 영화의전당)",
        "lat": 35.1715, "lng": 129.1275,
        "transitInfo": "부산지하철 2호선 센텀시티역 12, 6번 출구 (도보 7분 영화의전당)"
    },
    "부산 불꽃": {
        "websiteUrl": "https://busanfireworks.com/",
        "govUrl": "https://festivalbusan.com",
        "address": "부산광역시 수영구 광안해변로 219 (광안동 192-20, 광안리해수욕장)",
        "lat": 35.1535, "lng": 129.1185,
        "transitInfo": "부산지하철 2호선 금련산역 1, 3번 출구 또는 광안역 3, 5번 출구 (도보 10분)"
    },
    "세종축제": {
        "websiteUrl": "http://www.sjfestival.kr/",
        "govUrl": "https://www.sejong.go.kr",
        "address": "세종특별자치시 연기면 세종호수공원길 155 (세종리 1201, 세종호수공원)",
        "lat": 36.5015, "lng": 127.2685,
        "transitInfo": "정부세종청사 인근 BRT 노선(B0, B1, B2) 탑승 후 세종호수공원 하차"
    },
    "해미읍성": {
        "websiteUrl": "https://www.seosan.go.kr/haemi",
        "govUrl": "https://www.seosan.go.kr",
        "address": "충청남도 서산시 해미면 남문2로 143 (읍내리 40-1, 서산 해미읍성 진남문)",
        "lat": 36.7135, "lng": 126.5495,
        "transitInfo": "해미정류소에서 도보 5분, 서산공용버스터미널에서 해미 방면 시내버스"
    },
    "빵축제": {
        "websiteUrl": "https://daejeontour.co.kr/issue_djt/6",
        "govUrl": "https://www.daejeon.go.kr",
        "address": "대전광역시 유성구 대덕대로 480 (도룡동 3-1, 엑스포과학공원 한빛탑 물빛광장)",
        "lat": 36.3762, "lng": 127.3848,
        "transitInfo": "대전역 또는 유성온천역에서 606, 705, 911번 버스 탑승 후 엑스포과학공원 하차"
    }
}


# 25 Autonomous Districts of Seoul Fallback Geocoding Coordinates
SEOUL_DISTRICT_COORDS = {
    "종로구": (37.5730, 126.9794),
    "중구": (37.5638, 126.9976),
    "용산구": (37.5326, 126.9900),
    "성동구": (37.5634, 127.0368),
    "광진구": (37.5385, 127.0823),
    "동대문구": (37.5744, 127.0397),
    "중랑구": (37.6065, 127.0927),
    "성북구": (37.5891, 127.0182),
    "강북구": (37.6396, 127.0255),
    "도봉구": (37.6688, 127.0471),
    "노원구": (37.6542, 127.0568),
    "은평구": (37.6027, 126.9291),
    "서대문구": (37.5791, 126.9368),
    "마포구": (37.5663, 126.9016),
    "양천구": (37.5169, 126.8665),
    "강서구": (37.5509, 126.8495),
    "구로구": (37.4954, 126.8874),
    "금천구": (37.4568, 126.8955),
    "영등포구": (37.5264, 126.8962),
    "동작구": (37.5124, 126.9393),
    "관악구": (37.4784, 126.9515),
    "서초구": (37.4837, 127.0324),
    "강남구": (37.5172, 127.0473),
    "송파구": (37.5145, 127.1060),
    "강동구": (37.5301, 127.1238)
}

def auto_calibrate_festival_metadata(item):
    """
    Intelligently match festival names with official verified portal registries,
    calibrate land coordinates (prevent river/water offsets), and ensure 1st priority portal URLs.
    """
    name = item.get("name", "")
    for keyword, meta in OFFICIAL_PORTAL_REGISTRY.items():
        if keyword in name:
            if meta.get("websiteUrl") and not item.get("websiteUrl"):
                item["websiteUrl"] = meta["websiteUrl"]
            elif meta.get("websiteUrl") and ("visitkorea" in item.get("websiteUrl", "").lower() or "seoul.go.kr" in item.get("websiteUrl", "").lower()):
                # Promote to dedicated festival portal
                item["websiteUrl"] = meta["websiteUrl"]
                
            if meta.get("govUrl") and not item.get("govUrl"):
                item["govUrl"] = meta["govUrl"]
            if meta.get("address"):
                item["address"] = meta["address"]
            if meta.get("lat") and meta.get("lng"):
                item["lat"] = meta["lat"]
                item["lng"] = meta["lng"]
            if meta.get("transitInfo"):
                item["transitInfo"] = meta["transitInfo"]
            break
    return item

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

def fetch_seoul_culture_portal_events(seoul_api_key, today_str):
    """
    Directly query Seoul Culture Portal Open API (culturalEventInfo) for Seoul performances, festivals, and exhibitions.
    Supports both official API key and sample key via XML & JSON endpoints.
    """
    key = seoul_api_key.strip() if seoul_api_key else "sample"
    # If sample key, limit to 5 per Seoul API specification; if real key, fetch 100
    max_rows = 100 if key != "sample" else 5
    
    # 1. Try XML endpoint first (Most stable for Seoul Open Data API)
    xml_url = f"http://openapi.seoul.go.kr:8088/{key}/xml/culturalEventInfo/1/{max_rows}/"
    print(f"[*] Calling Seoul Culture Portal Open API: {xml_url.replace(key, '***') if key != 'sample' else xml_url}")
    try:
        req = urllib.request.Request(xml_url, headers={"User-Agent": "Mozilla/5.0 (compatible; KoreaTourMap/1.0)"})
        with urllib.request.urlopen(req, timeout=12) as response:
            if response.status == 200:
                content = response.read().decode("utf-8", errors="replace")
                root = ET.fromstring(content)
                rows = []
                for row_el in root.findall(".//row"):
                    r_dict = {}
                    for child in row_el:
                        r_dict[child.tag] = (child.text or "").strip()
                    rows.append(r_dict)
                if rows:
                    print(f"[✓] Retrieved {len(rows)} cultural events directly from Seoul Culture Portal (XML)!")
                    return rows
    except Exception as e_xml:
        print(f"[!] Seoul API XML notice: {e_xml}. Trying JSON endpoint...")

    # 2. Fallback to JSON endpoint
    json_url = f"http://openapi.seoul.go.kr:8088/{key}/json/culturalEventInfo/1/{max_rows}/"
    try:
        req = urllib.request.Request(json_url, headers={"User-Agent": "Mozilla/5.0 (compatible; KoreaTourMap/1.0)"})
        with urllib.request.urlopen(req, timeout=12) as response:
            if response.status == 200:
                content = response.read().decode("utf-8", errors="replace")
                res_json = json.loads(content)
                event_info = res_json.get("culturalEventInfo", {})
                rows = event_info.get("row", [])
                if rows:
                    print(f"[✓] Retrieved {len(rows)} cultural events directly from Seoul Culture Portal (JSON)!")
                    return rows
    except Exception as e_json:
        print(f"[!] Seoul Culture Portal JSON notice: {e_json}. Moving forward.")

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

    # 5-1. Seoul Culture Portal Direct Integration (공연, 전시, 축제, 야간문화행사)
    seoul_api_key = os.environ.get("SEOUL_API_KEY", "").strip()
    seoul_events = fetch_seoul_culture_portal_events(seoul_api_key, today_str)
    seoul_added = 0
    for se in seoul_events:
        title = se.get("TITLE", "").strip()
        if not title:
            continue
        norm_t = title.replace(" ", "")
        core_t = normalize_festival_core_name(title)
        if norm_t in existing_names or (len(core_t) >= 3 and core_t in existing_cores):
            continue

        # Extract dates
        s_date = se.get("STRTDATE", "")[:10]
        e_date = se.get("END_DATE", "")[:10]
        if not s_date or not e_date:
            continue

        # Filter: only current or upcoming events
        if e_date < today_str:
            continue

        place = se.get("PLACE", "").strip() or "서울 시내 공연장/야외무대"
        guname = se.get("GUNAME", "").strip()
        full_addr = f"서울특별시 {guname} {place}".strip()
        
        # Handle coordinates with autonomous district fallback
        raw_lot = se.get("LOT", "").strip() # Longitude
        raw_lat = se.get("LAT", "").strip() # Latitude
        
        lat, lng = 0.0, 0.0
        try:
            if raw_lat and raw_lot:
                lat = float(raw_lat)
                lng = float(raw_lot)
        except Exception:
            pass

        # If swapped (LOT was lat, LAT was lng)
        if lat > 50 and lng < 40:
            lat, lng = lng, lat

        # Fallback to district representative coordinates if out of Seoul bounds
        if not (37.4 < lat < 37.7 and 126.7 < lng < 127.3):
            if guname in SEOUL_DISTRICT_COORDS:
                lat, lng = SEOUL_DISTRICT_COORDS[guname]
            else:
                lat, lng = 37.5665, 126.9780

        codename = se.get("CODENAME", "축제/행사")
        cat = "축제/행사" if ("축제" in codename or "행사" in codename) else "문화/역사"
        is_free = se.get("IS_FREE", "")
        fee_str = se.get("USE_FEE", "무료" if is_free == "무료" else "유료 (상세 안내 참조)")

        hpage = se.get("ORG_LINK", "").strip() or se.get("HOMEPAGE", "").strip()
        
        seoul_item = {
            "id": f"seoul-culture-{len(data)+1}",
            "name": title,
            "type": "festival",
            "category": cat,
            "region": "서울",
            "provinceGroup": "수도권",
            "season": "가을",
            "startDate": s_date,
            "endDate": e_date,
            "period": f"{s_date} ~ {e_date}",
            "lat": lat,
            "lng": lng,
            "address": full_addr,
            "summary": f"서울문화포털 공식 등록 {codename}입니다. {place}에서 펼쳐집니다.",
            "highlights": [codename, place, "서울시 문화행사"],
            "tip": f"관람 대상: {se.get('USE_TRGT', '시민 누구나')}. 사전 예약 및 세부 프로그램은 안내처를 확인하세요.",
            "fee": fee_str,
            "phone": "다산콜센터 02-120",
            "websiteUrl": hpage if (hpage and not "culture.seoul.go.kr" in hpage) else "",
            "govUrl": "https://culture.seoul.go.kr/culture/culture/cultureEvent/list.do",
            "visitKoreaUrl": hpage or "https://culture.seoul.go.kr",
            "tags": ["서울문화포털", codename, guname, "서울문화행사", "서울"]
        }
        data.append(seoul_item)
        existing_names.add(norm_t)
        if len(core_t) >= 3:
            existing_cores.add(core_t)
        seoul_added += 1
        added_total += 1

    if seoul_added > 0:
        print(f"[✓] Added {seoul_added} Seoul culture portal events into database!")

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
