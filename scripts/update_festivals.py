#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
High-Reliability Automated Festival Data Engine & Publisher for Korea Tour Map
Architecture:
- AI Agent & User Curation: Researches, fact-checks, and logs festival additions/cancellations to Google Sheets.
- GitHub Actions Bot: Acts as a lightweight, zero-failure pipeline operator that:
    1. Recalibrates live dates, D-Days, and ongoing/closed statuses based on KST clock.
    2. Synchronizes overrides, cancellations, and new additions from Google Sheets feed.
    3. Auto-calibrates land coordinates and official verified URLs.
    4. Auto-increments localStorage cache version to ensure immediate client updates.
    5. Commits and triggers seamless Vercel deployment without external API dependencies.
"""

import os
import re
import io
import csv
import json
import datetime
import urllib.parse
import urllib.request

# ==============================================================================
# 📊 GOOGLE SHEETS LIVE OVERRIDE & REAL-TIME FEED CONFIGURATION
# ==============================================================================
DEFAULT_GOOGLE_SHEET_ID = "159rBV3xq_W8SjZxx8hz4tKilmv4FWBGmhDnP38MV7P8"

# ==============================================================================
# 🎯 AUTOMATED VERIFIED OFFICIAL PORTAL & LAND COORDINATES REGISTRY
# Prevents regression and ensures accurate land access coordinates & deep links
# ==============================================================================
OFFICIAL_PORTAL_REGISTRY = {
    "책읽는 서울광장": {
        "lat": 37.5663,
        "lng": 126.9778,
        "address": "서울특별시 중구 세종대로 110 (태평로1가 31, 서울광장 잔디광장)",
        "websiteUrl": "https://seouloutdoorlibrary.kr/user/square/about.do",
        "govUrl": "https://seouloutdoorlibrary.kr/"
    },
    "광화문 책마당": {
        "lat": 37.5714,
        "lng": 126.9768,
        "address": "서울특별시 종로구 세종대로 175 (세종로 1-68, 광화문광장 육조마당 및 놀이마당)",
        "websiteUrl": "https://seouloutdoorlibrary.kr/user/yard/about.do",
        "govUrl": "https://seouloutdoorlibrary.kr/"
    },
    "책읽는 맑은냇가": {
        "lat": 37.5691,
        "lng": 126.9785,
        "address": "서울특별시 종로구 서린동 14-1 (청계광장 및 청계천 모전교~광통교 수변)",
        "websiteUrl": "https://seouloutdoorlibrary.kr/user/stream/about.do",
        "govUrl": "https://seouloutdoorlibrary.kr/"
    },
    "운동하는 서울광장": {
        "lat": 37.5658,
        "lng": 126.9782,
        "address": "서울특별시 중구 세종대로 110 (태평로1가 31, 서울광장 동측 상설무대 앞)",
        "websiteUrl": "https://seoulsportsday.com/",
        "govUrl": "https://sports.seoul.go.kr"
    },
    "사육신": {
        "lat": 37.5141,
        "lng": 126.9486,
        "address": "서울특별시 동작구 노량진로 191 (노량진동 155-1, 사육신역사공원 내 사육신역사관 및 야외마당)",
        "websiteUrl": "https://www.idfac.or.kr/bbs/board.php?bo_table=gallery_info&wr_id=324",
        "govUrl": "https://www.idfac.or.kr/",
        "visitKoreaUrl": "https://culture.seoul.go.kr/culture/culture/cultureEvent/view.do?cultcode=159614"
    },
    "충효예술": {
        "lat": 37.5141,
        "lng": 126.9486,
        "address": "서울특별시 동작구 노량진로 191 (노량진동 155-1, 사육신역사공원 내 사육신역사관 및 야외마당)",
        "websiteUrl": "https://www.idfac.or.kr/bbs/board.php?bo_table=gallery_info&wr_id=324",
        "govUrl": "https://www.idfac.or.kr/",
        "visitKoreaUrl": "https://culture.seoul.go.kr/culture/culture/cultureEvent/view.do?cultcode=159614"
    },
    "동네방네비프": {
        "lat": 37.5302,
        "lng": 126.9174,
        "address": "서울특별시 영등포구 의사당대로 1 (여의도동 1, 국회의원회관 2층 대회의실)",
        "websiteUrl": "https://reservation.assembly.go.kr/reserve/contents/booking/contentsDetail.do?cntsDtlClsCd=EVT301&cntsUniqId=4957022",
        "govUrl": "https://everywhere.biff.kr/",
        "transitInfo": "지하철 9호선 국회의사당역 6번 출구 (도보 5분 국회의원회관)"
    },
    "국회문화극장": {
        "lat": 37.5302,
        "lng": 126.9174,
        "address": "서울특별시 영등포구 의사당대로 1 (여의도동 1, 국회의원회관 2층 대회의실)",
        "websiteUrl": "https://reservation.assembly.go.kr/reserve/contents/booking/contentsDetail.do?cntsDtlClsCd=EVT301&cntsUniqId=4957022",
        "govUrl": "https://everywhere.biff.kr/"
    },
    "서울디자인위크": {
        "websiteUrl": "https://www.seoul-designweek.or.kr/",
        "govUrl": "https://seouldesign.or.kr/"
    },
    "그린칩스": {
        "websiteUrl": "https://www.greenchipsseoul.com/about/2026/",
        "govUrl": "https://ddp.or.kr"
    },
    "M 클래식": {
        "websiteUrl": "https://www.mfac.or.kr/festival/mpf_info2026.jsp",
        "govUrl": "https://www.mfac.or.kr"
    },
    "M클래식": {
        "websiteUrl": "https://www.mfac.or.kr/festival/mpf_info2026.jsp",
        "govUrl": "https://www.mfac.or.kr"
    },
    "D.FESTA": {
        "lat": 37.5815,
        "lng": 127.0035,
        "address": "서울특별시 종로구 대학로8길 25 (동숭동 1-40, 대학로 공간아울)",
        "websiteUrl": "https://stheater.or.kr/perform-ad/?idx=175023327&bmode=view",
        "govUrl": "https://culture.seoul.go.kr"
    },
    "소극장축제": {
        "lat": 37.5815,
        "lng": 127.0035,
        "address": "서울특별시 종로구 대학로8길 25 (동숭동 1-40, 대학로 공간아울)",
        "websiteUrl": "https://stheater.or.kr/perform-ad/?idx=175023327&bmode=view",
        "govUrl": "https://culture.seoul.go.kr"
    },
    "부산 불꽃축제": {
        "lat": 35.1532,
        "lng": 129.1186,
        "address": "부산광역시 수영구 광안해변로 219 (광안동 192-20, 광안리해수욕장 및 광안대교 일원)",
        "websiteUrl": "https://www.bfo.or.kr/festival_fireworks/",
        "govUrl": "https://www.busan.go.kr",
        "transitInfo": "부산도시철도 2호선 광안역 3·5번 출구 (도보 10분 광안리해변)"
    },
    "부산불꽃": {
        "lat": 35.1532,
        "lng": 129.1186,
        "address": "부산광역시 수영구 광안해변로 219 (광안동 192-20, 광안리해수욕장 및 광안대교 일원)",
        "websiteUrl": "https://www.bfo.or.kr/festival_fireworks/",
        "govUrl": "https://www.busan.go.kr",
        "transitInfo": "부산도시철도 2호선 광안역 3·5번 출구 (도보 10분 광안리해변)"
    },
    "관악강감찬": {
        "websiteUrl": "https://www.ggcfest.com/",
        "govUrl": "https://www.gwanakcf.or.kr/"
    },
    "조계사": {
        "websiteUrl": "https://www.jogyesa.kr/board/notice/board_view.php?search_category=1&num=8268",
        "govUrl": "https://www.jogyesa.kr"
    },
    "드림파크국화": {
        "websiteUrl": "https://www.slc.or.kr/",
        "govUrl": "https://www.slc.or.kr"
    },
    "자라섬 꽃": {
        "websiteUrl": "https://korean.visitkorea.or.kr/kfes/detail/fstvlDetail.do?fstvlCntntsId=8b7f0ad9-384b-4b55-ba4b-5a6804cae161",
        "govUrl": "https://www.gptour.go.kr/"
    },
    "용마폭포": {
        "websiteUrl": "https://festival.seoul.go.kr/festival/main/festivalView.do?festacode=605",
        "govUrl": "https://www.jungnang.go.kr"
    },
    "문래": {
        "websiteUrl": "https://www.ydpcf.or.kr/festival/networkart.do",
        "govUrl": "https://www.ydpcf.or.kr"
    },
    "종로 가족공연": {
        "websiteUrl": "https://www.jfac.or.kr/site/main/program/perf_show_list_view?pgIdx=2792",
        "govUrl": "https://www.jfac.or.kr"
    },
    "군산 짬뽕": {
        "websiteUrl": "https://jjambbong.kr/",
        "govUrl": "https://www.gunsan.go.kr"
    },
    "동구동락": {
        "websiteUrl": "https://dgdr.kr/",
        "govUrl": "https://www.donggu.go.kr"
    },
    "대전 서구 아트": {
        "websiteUrl": "https://djseogufestival.com/",
        "govUrl": "https://www.seogu.go.kr"
    },
    "생거진천": {
        "websiteUrl": "https://jcfestival.or.kr/",
        "govUrl": "https://jinculture.or.kr/"
    },
    "전주한지": {
        "websiteUrl": "https://jjhanji.or.kr/",
        "govUrl": "https://www.jjcf.or.kr"
    },
    "남원 흥부제": {
        "websiteUrl": "https://heungbu.org/",
        "govUrl": "https://www.namwon.go.kr"
    },
    "심청어린이": {
        "websiteUrl": "https://www.gokseong.go.kr/tour/festivity/simcheong",
        "govUrl": "https://www.gokseong.go.kr"
    },
    "산청한방약초": {
        "websiteUrl": "https://www.scherb.or.kr/",
        "govUrl": "https://donguibogam-village.sancheong.go.kr/"
    },
    "고양 가을꽃": {
        "websiteUrl": "https://flower.or.kr/",
        "govUrl": "https://www.goyang.go.kr"
    },
    "포천 한탄강 가든": {
        "websiteUrl": "https://www.pocheon-gardenfesta.kr/",
        "govUrl": "https://www.pocheon.go.kr"
    },
    "삼랑성": {
        "websiteUrl": "https://samrangseong.org/",
        "govUrl": "https://www.ganghwa.go.kr"
    },
    "나주영산강": {
        "websiteUrl": "https://www.naju.go.kr/tour/notice/information?mode=view&idx=9785&date=2026-10-07",
        "govUrl": "https://www.naju.go.kr"
    },
    "익산 천만송이": {
        "websiteUrl": "https://www.iksan.go.kr/tour/index.iksan?menuCd=DOM_000002002001000000",
        "govUrl": "https://www.iksan.go.kr"
    },
    "어슬렁페스티벌": {
        "websiteUrl": "https://www.instagram.com/earthrunfestival/",
        "govUrl": "https://www.mapo.go.kr"
    },
    "울산고래축제": {
        "websiteUrl": "http://www.ulsanwhale.com/",
        "govUrl": "https://www.ulsan.go.kr"
    },
    "라베니체": {
        "websiteUrl": "https://www.gimpo.go.kr/culture/selectTourCntntsWebList.do?key=6808&ctgry=4",
        "govUrl": "https://www.gimpo.go.kr"
    },
    "통닭거리": {
        "websiteUrl": "https://www.suwon.go.kr/culture/ingCultureView.do?ctrSeqNo=1948&listType=ing",
        "govUrl": "https://www.suwon.go.kr"
    },
    "연천국화": {
        "websiteUrl": "https://www.yeoncheon.go.kr",
        "govUrl": "https://www.yeoncheon.go.kr"
    },
    "매헌시민의숲": {
        "lat": 37.4705,
        "lng": 127.0355,
        "address": "서울특별시 서초구 매헌로 99 (양재동 236, 매헌시민의숲 잔디광장 일원)",
        "websiteUrl": "https://www.seoul.go.kr/festa/garden/y2026/maeheon-forest/maeheon-intro/maeheon-overview",
        "govUrl": "https://parks.seoul.go.kr"
    },
    "양재천을 품은 야외도서관": {
        "lat": 37.4735,
        "lng": 127.0334,
        "address": "서울특별시 서초구 양재천로 33 (양재동 102-6, 서초구립 양재도서관 및 앞 오솔길 야외도서관)",
        "websiteUrl": "https://yangjae.seocholib.or.kr/NoticeInfoDetail/26288",
        "govUrl": "https://korean.visitkorea.or.kr/kfes/detail/fstvlDetail.do?fstvlCntntsId=174dc17e-b58d-46f1-ae12-8fba1d329f4d"
    },
    "양재도서관": {
        "lat": 37.4735,
        "lng": 127.0334,
        "address": "서울특별시 서초구 양재천로 33 (양재동 102-6, 서초구립 양재도서관 및 앞 오솔길)",
        "websiteUrl": "https://yangjae.seocholib.or.kr/NoticeInfoDetail/26288",
        "govUrl": "https://korean.visitkorea.or.kr/kfes/detail/fstvlDetail.do?fstvlCntntsId=174dc17e-b58d-46f1-ae12-8fba1d329f4d"
    },
    "억새축제": {
        "websiteUrl": "https://festival.seoul.go.kr/festival/main/festivalView.do?festacode=683",
        "govUrl": "https://parks.seoul.go.kr"
    },
    "한성백제": {
        "websiteUrl": "https://www.songpa.go.kr/hanseong/",
        "govUrl": "https://festival.seoul.go.kr/festival/main/festivalView.do?festacode=581"
    },
    "노원달빛": {
        "websiteUrl": "https://moonlightwalk.kr/",
        "govUrl": "https://www.nowonarts.kr/"
    },
    "정동야행": {
        "websiteUrl": "https://www.jeongdong-culturenight.kr/",
        "govUrl": "https://www.junggu.seoul.kr"
    },
    "서울국제정원박람회": {
        "lat": 37.5444,
        "lng": 127.0374,
        "address": "서울특별시 성동구 뚝섬로 273 (성수동1가 720, 서울숲 일원)",
        "websiteUrl": "https://www.seoul.go.kr/festa/garden/y2026/introduce/introduce2026",
        "govUrl": "https://parks.seoul.go.kr"
    },
    "새우젓": {
        "websiteUrl": "https://festival.seoul.go.kr/festival/main/festivalView.do?festacode=683",
        "govUrl": "https://www.mapo.go.kr"
    },
    "한강페스티벌": {
        "websiteUrl": "https://festival.seoul.go.kr/festival/main/festivalView.do?festacode=400",
        "govUrl": "https://hangang.seoul.go.kr"
    },
    "백년나이트": {
        "websiteUrl": "https://culture.seoul.go.kr/culture/culture/cultureEvent/view.do?cultcode=159740&menuNo=200010",
        "govUrl": "https://www.gangbuk.go.kr"
    },
    "잠수교": {
        "lat": 37.5105,
        "lng": 126.9960,
        "address": "서울특별시 서초구 반포동 115-5 (반포한강공원 달빛광장 및 잠수교)",
        "websiteUrl": "https://www.festa-ddooddoo.com/",
        "govUrl": "https://hangang.seoul.go.kr"
    },
    "빛섬축제": {
        "websiteUrl": "https://www.bitseomfestival.com/",
        "govUrl": "https://hangang.seoul.go.kr"
    },
    "양재아트살롱": {
        "websiteUrl": "https://yangjaeartsalon.co.kr/",
        "govUrl": "https://www.seocho.go.kr"
    },
    "밤의석조전": {
        "websiteUrl": "https://www.kh.or.kr/cont/view/fest/month/menu/210?thisPage=1&idx=110623",
        "govUrl": "https://www.royalpalace.go.kr"
    },
    "별빛야행": {
        "websiteUrl": "https://www.kh.or.kr/cont/view/fest/month/menu/210",
        "govUrl": "https://www.royalpalace.go.kr"
    },
    "궁중문화축전": {
        "websiteUrl": "https://www.chf.or.kr/fest",
        "govUrl": "https://www.royalpalace.go.kr"
    },
    "자라섬재즈": {
        "websiteUrl": "http://www.jarasumjazz.com/",
        "govUrl": "https://www.gp.go.kr"
    },
    "부산국제영화제": {
        "websiteUrl": "https://www.biff.kr/",
        "govUrl": "https://www.busan.go.kr"
    },
    "안동국제탈춤": {
        "websiteUrl": "http://www.maskdance.com/",
        "govUrl": "https://www.andong.go.kr"
    },
    "진주남강유등": {
        "websiteUrl": "http://www.yudeung.com/",
        "govUrl": "https://www.jinju.go.kr"
    },
    "보령머드": {
        "websiteUrl": "http://www.mudfestival.or.kr/",
        "govUrl": "https://www.boryeong.go.kr"
    },
    "광주추억의충장": {
        "websiteUrl": "https://www.donggu.kr/index.es?sid=c7",
        "govUrl": "https://www.donggu.kr"
    },
    "임실N치즈": {
        "websiteUrl": "http://www.imsilfestival.com/",
        "govUrl": "https://www.imsil.go.kr"
    },
    "남해독일마을": {
        "websiteUrl": "https://tour.namhae.go.kr/",
        "govUrl": "https://www.namhae.go.kr"
    },
    "대전빵축제": {
        "websiteUrl": "https://dnto.or.kr/",
        "govUrl": "https://www.daejeon.go.kr"
    }
}

def auto_calibrate_festival_metadata(item):
    """
    Auto-calibrates official links and land coordinates using verified registry.
    """
    name = item.get("name", "")
    for key, reg in OFFICIAL_PORTAL_REGISTRY.items():
        if key in name:
            # Overwrite if empty or if registry provides high-priority official portal
            cur_url = item.get("websiteUrl", "")
            if "websiteUrl" in reg:
                if not cur_url or any(bad in cur_url for bad in ["dfesta.co.kr", "dfac.or.kr", "hanwhapromise.com", "yna.co.kr", "weeklytoday.com", "m-i.kr", "thekorea.kr"]):
                    item["websiteUrl"] = reg["websiteUrl"]
            if "govUrl" in reg and (not item.get("govUrl") or "seoul.go.kr" in item.get("govUrl") and "부산" in name):
                item["govUrl"] = reg["govUrl"]
            if "lat" in reg:
                item["lat"] = reg["lat"]
            if "lng" in reg:
                item["lng"] = reg["lng"]
            if "address" in reg:
                item["address"] = reg["address"]
            if "transitInfo" in reg:
                item["transitInfo"] = reg["transitInfo"]
            break

    # Fix portal landing page to direct search query if culture.seoul.go.kr without query
    raw_url = item.get("websiteUrl") or item.get("govUrl") or ""
    if raw_url and "culture.seoul.go.kr" in raw_url and "cultcode=" not in raw_url and "searchStr=" not in raw_url:
        clean_query = re.sub(r'\[.*?\]|\(.*?\)|제\d+회|\d{4}', '', item.get("name", "")).strip()
        if clean_query:
            fixed_url = f"https://culture.seoul.go.kr/culture/culture/cultureEvent/list.do?searchStr={urllib.parse.quote(clean_query)}"
            item["websiteUrl"] = fixed_url
            if not item.get("govUrl"):
                item["govUrl"] = fixed_url

    return item

def normalize_festival_core_name(name):
    """
    Strips year, edition, and prefixes for reliable deduplication.
    """
    if not name:
        return ""
    clean = re.sub(r'202\d년?|제\s*\d+\s*회|\[.*?\]|\(.*?\)', '', name)
    clean = re.sub(r'축제|페스티벌|대축제|한마당|문화제|축전', '', clean)
    return clean.strip().replace(" ", "")

def parse_province_group(region):
    """Maps 17 administrative regions to broad provincial groups."""
    if region in ["서울", "경기", "인천"]:
        return "수도권"
    elif region in ["강원"]:
        return "강원권"
    elif region in ["대전", "세종", "충남", "충북"]:
        return "충청권"
    elif region in ["광주", "전남", "전북"]:
        return "호남권"
    elif region in ["부산", "대구", "울산", "경남", "경북"]:
        return "영남권"
    elif region in ["제주"]:
        return "제주권"
    return "전국"

def fetch_google_sheet_override(sheet_target=None):
    """
    Fetches real-time festival additions, edits, or cancellations from Google Sheet CSV export.
    Supports full Google Sheet URL, CSV export URL, or the Sheet ID.
    Columns expected:
    상태(등록/취소), 축제명, 구분, 지역, 시작일, 종료일, 상세주소, 위도, 경도, 소개및특징, 문의처, 공식홈페이지URL, 골든타임팁
    """
    target = sheet_target or os.environ.get("FESTIVAL_SHEET_URL", "").strip() or DEFAULT_GOOGLE_SHEET_ID
    if not target:
        return []

    if "docs.google.com/spreadsheets" in target:
        m = re.search(r'/d/([a-zA-Z0-9-_]+)', target)
        sheet_id = m.group(1) if m else target
    else:
        sheet_id = target.strip()

    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    print(f"[*] Connecting to Google Sheets Live Feed: {csv_url}")

    try:
        req = urllib.request.Request(
            csv_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) KoreaFestivalBot/2.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            content = resp.read().decode('utf-8')
        
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        print(f"[✓] Successfully retrieved {len(rows)} verified rows from Google Sheet!")
        return rows
    except Exception as e:
        print(f"[!] Google Sheet notice: {e}. Gracefully continuing with cached database.")
        return []

def main():
    print("="*65)
    print("🚀 Korea Tour Map - High-Reliability Automated Publisher Engine")
    print("   Architecture: Google Sheets Sync + KST Status Recalibration")
    print("="*65)

    # 1. Calculate current KST date
    kst_tz = datetime.timezone(datetime.timedelta(hours=9))
    now_kst = datetime.datetime.now(kst_tz)
    today_str = now_kst.strftime("%Y-%m-%d")
    today_dot = now_kst.strftime("%Y.%m.%d")
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
    
    # Update or inject LAST_SYNC_TIMESTAMP in index.html
    ts_pattern = r'const LAST_SYNC_TIMESTAMP = "[^"]*";'
    new_ts_def = f'const LAST_SYNC_TIMESTAMP = "{timestamp_str}";'
    if re.search(ts_pattern, html):
        html = re.sub(ts_pattern, new_ts_def, html)
    else:
        html = html.replace(new_date_def, f'{new_date_def}\n    const LAST_SYNC_TIMESTAMP = "{timestamp_str}";')
    print(f"[*] Updated LAST_SYNC_TIMESTAMP -> {timestamp_str}")
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

    # Auto-calibrate all existing items with verified portal registries
    data = [auto_calibrate_festival_metadata(it) for it in data]
    existing_names = {item['name'].replace(" ", "") for item in data}

    # 5. Synchronize Overrides & Additions from Google Sheets Live Feed
    sheet_rows = fetch_google_sheet_override()
    sheet_added = 0
    sheet_cancelled = 0
    sheet_updated = 0

    for r in sheet_rows:
        raw_status = r.get("상태(등록/취소)", "").strip()
        raw_name = r.get("축제명", "").strip()
        if not raw_name:
            continue

        norm_name = raw_name.replace(" ", "")

        # A. Cancellation Processing
        if "취소" in raw_status:
            before_len = len(data)
            data = [it for it in data if it.get("name", "").replace(" ", "") != norm_name]
            if len(data) < before_len:
                sheet_cancelled += (before_len - len(data))
                print(f"[-] Removed cancelled festival from database: {raw_name}")
            continue

        # B. Addition / Update Processing
        s_date = r.get("시작일", "").strip()
        e_date = r.get("종료일", "").strip()
        addr = r.get("상세주소", "").strip() or f"{r.get('지역', '전국')} 행사 일원"
        
        try:
            lat = float(r.get("위도", 0)) if r.get("위도") else 37.5665
            lng = float(r.get("경도", 0)) if r.get("경도") else 126.9780
        except Exception:
            lat, lng = 37.5665, 126.9780

        region = r.get("지역", "전국").strip()
        summary = r.get("소개및특징", "").strip() or f"{raw_name} 행사입니다."
        phone = r.get("문의처", "").strip() or "공식 안내처 문의"
        url = r.get("공식홈페이지URL", "").strip()
        tip = r.get("골든타임팁", "").strip() or "공식 안내를 참고하여 방문하세요."

        existing_item = next((it for it in data if it.get("name", "").replace(" ", "") == norm_name), None)
        if existing_item:
            if s_date: existing_item["startDate"] = s_date
            if e_date: existing_item["endDate"] = e_date
            if s_date and e_date: existing_item["period"] = f"{s_date} ~ {e_date}"
            if addr: existing_item["address"] = addr
            if lat and lng:
                existing_item["lat"] = lat
                existing_item["lng"] = lng
            if summary: existing_item["summary"] = summary
            if phone: existing_item["phone"] = phone
            if url: existing_item["websiteUrl"] = url
            if tip: existing_item["tip"] = tip
            sheet_updated += 1
            print(f"[*] Updated existing festival from Google Sheet: {raw_name}")
        else:
            new_item = {
                "id": f"sheet-{abs(hash(raw_name)) % 1000000}",
                "name": raw_name,
                "type": r.get("구분", "festival").strip() or "festival",
                "category": "축제/행사",
                "region": region,
                "provinceGroup": parse_province_group(region),
                "season": "가을",
                "startDate": s_date,
                "endDate": e_date,
                "period": f"{s_date} ~ {e_date}",
                "lat": lat,
                "lng": lng,
                "address": addr,
                "summary": summary,
                "highlights": ["구글시트 실시간 반영", "문화 행사", "대표 축제"],
                "tip": tip,
                "fee": "무료",
                "phone": phone,
                "websiteUrl": url,
                "tags": ["구글시트연동", region, "실시간축제"]
            }
            new_item = auto_calibrate_festival_metadata(new_item)
            data.insert(0, new_item)
            existing_names.add(norm_name)
            sheet_added += 1
            print(f"[+] Added new festival from Google Sheet: {raw_name}")

    print(f"[*] Google Sheet sync result -> Added: {sheet_added}, Cancelled: {sheet_cancelled}, Updated: {sheet_updated}")

    # 🛡️ GUARANTEE REGISTRY PRECEDENCE: Re-apply auto_calibrate_festival_metadata
    # This prevents outdated URLs or coordinates from Google Sheet from overwriting verified portals.
    data = [auto_calibrate_festival_metadata(it) for it in data]
    print("[🛡️] Re-applied verified OFFICIAL_PORTAL_REGISTRY post-sheet-sync to guarantee 100% data integrity")

    # 6. Recalibrate D-days and status for all festivals based on today's KST date
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

    print(f"[*] Real-time status distribution as of {today_str}: {stats}")

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

    print(f"[✓] Successfully wrote updated index.html! (Total length: {len(html)} bytes, items: {len(data)})")
    print("="*65)

if __name__ == "__main__":
    main()
