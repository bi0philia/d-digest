"""
고요한 연구살롱 데이터 정제 및 리팩토링 스크립트
1. latest_digest.json의 논문 제목 및 초록 요약 100% 개별 정밀화 (중복 캔드 타이틀 완전 제거)
2. archive.json 내의 과거 캔드 타이틀 전수 교정
3. researcher_engine을 통한 '핫한 연구자' & '올타임 레전드' 동적 갱신
4. trends.json 동기화
"""
import json
import os
import re
from curator import translate_academic_title, generate_deep_heuristic_summary, synthesize_daily_summary
from researcher_engine import update_gurus_file
from exporter import compute_trends

WEB_DATA_DIR = os.path.join(r"h:\내 드라이브\lgh\curation-digest-app\web\data")
LATEST_FILE = os.path.join(WEB_DATA_DIR, "latest_digest.json")
ARCHIVE_FILE = os.path.join(WEB_DATA_DIR, "archive.json")
TRENDS_FILE = os.path.join(WEB_DATA_DIR, "trends.json")

CANNED_TITLES = {
    "도시 공간의 탈상품화와 자율적 시민 공간권 연구",
    "농생태학적 대지 윤리와 다종 공생의 회복탄력성",
    "취약계층 포용 인터페이스와 참여형 시빅 서비스 설계",
    "자치적 커먼즈 프로토콜과 호혜적 공유 거버넌스",
    "사회기술시스템과 기술 민주화에 관한 비판적 고찰",
    "위기 환경 속 최소 개입형 공공안전망과 상호부조 인프라"
}

def clean_item(it):
    orig_title = it.get("original_title") or it.get("title", "")
    abstract = it.get("abstract", "")
    source = it.get("source", "")
    text = f"{orig_title} {abstract}".lower()
    
    # 1. Category inference
    cat = it.get("category", "커먼즈·공유재")
    if "mining" in text or "mountain" in text:
        cat = "공간사회·도시커먼즈"
    elif "respect" in text or "health" in text or "practitioner" in text:
        cat = "돌봄·상호부조"
    elif "solar" in text or "solarities" in text or "interspecies" in text or "nature" in text or "oromo" in text or "agroecology" in text or "peasant" in text:
        cat = "농생태·식량주권"
    elif "algorithm" in text or "journalism" in text or "ai" in text or "socio-technical" in text or "finance" in text:
        cat = "과학기술학·STS"
    elif "urban" in text or "spatial" in text or "city" in text:
        cat = "공간사회·도시커먼즈"
    elif "disaster" in text or "safety" in text or "emergency" in text or "informatics" in text:
        cat = "재난안전·공공인프라"
    elif "commons" in text or "commoning" in text or "cooperation" in text or "p2p" in text:
        cat = "커먼즈·공유재"

    # 2. Unique accurate title
    new_title_kr = translate_academic_title(orig_title, cat)
    
    # 3. Rich unique abstract summary
    new_summary = generate_deep_heuristic_summary(it, cat, new_title_kr)
    
    # 4. Canonical URL fix
    url = it.get("url", "")
    if "10.17613/jchtw-w2z97" in url:
        url = "https://works.hcommons.org/records/d0ee4-h2e12"
    elif "10.17613/sb76m-v2e23" in url:
        url = "https://works.hcommons.org/records/9jeb4-f7a34"
        
    # 5. Keywords
    keywords = [f"#{cat.split('·')[0]}"]
    if "algorithm" in text: keywords.append("#알고리즘정의")
    if "ai" in text: keywords.append("#책임있는AI")
    if "respect" in text or "health" in text: keywords.append("#존중의수사학")
    if "solar" in text: keywords.append("#태양성에너지")
    if "mining" in text: keywords.append("#자원추출주의")
    if "nature" in text or "oromo" in text: keywords.append("#대지윤리")
    if "commons" in text: keywords.append("#커머닝")
    if "farmer" in text: keywords.append("#농민협동")
    if len(keywords) < 3: keywords.append("#동시대학술")

    it["title_kr"] = new_title_kr
    it["category"] = cat
    it["url"] = url
    it["summary_points"] = new_summary
    it["keywords"] = list(dict.fromkeys(keywords))[:4]
    return it


def main():
    print("=== 고요한 연구살롱 데이터 정제 시작 ===")
    
    # 1. latest_digest.json 정제
    if os.path.exists(LATEST_FILE):
        with open(LATEST_FILE, "r", encoding="utf-8") as f:
            latest = json.load(f)
            
        print(f"Latest digest {latest.get('id')} 정제 중... (논문 {len(latest.get('items', []))}편)")
        cleaned_items = []
        seen_titles = set()
        for it in latest.get("items", []):
            cit = clean_item(it)
            t_kr = cit["title_kr"]
            if t_kr in seen_titles:
                t_kr = f"{t_kr} ({cit.get('source', '')})"
                cit["title_kr"] = t_kr
            seen_titles.add(t_kr)
            cleaned_items.append(cit)
            print(f"  -> {cit['title_kr']} [{cit['category']}]")
            
        latest["items"] = cleaned_items
        latest["daily_summary"] = synthesize_daily_summary(cleaned_items)
        
        with open(LATEST_FILE, "w", encoding="utf-8") as f:
            json.dump(latest, f, ensure_ascii=False, indent=2)
        print("Latest digest 저장 완료.")

    # 2. archive.json 정제
    if os.path.exists(ARCHIVE_FILE):
        with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
            archive = json.load(f)
            
        print(f"아카이브 {len(archive)}회차 정제 중...")
        repaired_count = 0
        for d in archive:
            # If this is today's digest, update with latest
            if d.get("id") == latest.get("id"):
                d["items"] = latest["items"]
                d["daily_summary"] = latest["daily_summary"]
                continue
                
            seen_d_titles = set()
            for it in d.get("items", []):
                curr_t = it.get("title_kr", "")
                if curr_t in CANNED_TITLES or "비판적 분석 및 실천 담론" in curr_t:
                    repaired_count += 1
                    clean_item(it)
                if it.get("title_kr") in seen_d_titles:
                    it["title_kr"] = f"{it['title_kr']} ({it.get('source', '')})"
                seen_d_titles.add(it.get("title_kr"))
                
        with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
            json.dump(archive, f, ensure_ascii=False, indent=2)
        print(f"아카이브 {repaired_count}건의 캔드 타이틀 정제 완료.")

    # 3. 연구자 인덱스 갱신 (핫한 연구자 + 올타임 레전드)
    print("연구자 인덱스(gurus.json) 동적 갱신 중...")
    with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
        clean_archive = json.load(f)
    gurus_data = update_gurus_file(clean_archive)
    print(f"  -> 핫한 연구자 {gurus_data['total_trending']}명, 올타임 레전드 {gurus_data['total_legends']}명 갱신 완료.")

    # 4. trends.json 갱신
    print("연구 동향(trends.json) 갱신 중...")
    trends = compute_trends(clean_archive)
    with open(TRENDS_FILE, "w", encoding="utf-8") as f:
        json.dump(trends, f, ensure_ascii=False, indent=2)
    print("trends.json 갱신 완료.")

    print("=== 모든 데이터 정제 및 동기화 완료! ===")

if __name__ == "__main__":
    main()
