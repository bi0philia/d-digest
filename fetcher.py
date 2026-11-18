# -*- coding: utf-8 -*-
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
import requests
from config import TARGET_JOURNALS, SCHOLARLY_QUERIES, RSS_FEEDS, EXCLUDE_KEYWORDS

HEADERS = {"User-Agent": "ResearchDigestCurator/1.0 (mailto:twin@commons.org)"}
ARCHIVE_FILE = os.path.join(os.path.dirname(__file__), "web", "data", "archive.json")


def get_archived_identifiers():
    """기존 아카이브에 수집·발행된 논문의 DOI, URL, 원본 제목 목록 추출"""
    seen = set()
    if os.path.exists(ARCHIVE_FILE):
        try:
            with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
                archive = json.load(f)
                for digest in archive:
                    for it in digest.get("items", []):
                        if it.get("id"):
                            seen.add(str(it["id"]).strip().lower())
                        if it.get("url"):
                            seen.add(str(it["url"]).strip().lower())
                        if it.get("original_title"):
                            seen.add(str(it["original_title"]).strip().lower())
        except Exception as e:
            print(f"Notice: Failed to load archive for deduplication: {e}", file=sys.stderr)
    return seen


def reconstruct_abstract(inverted_index):
    """OpenAlex의 abstract_inverted_index를 일반 문장으로 복원"""
    if not inverted_index:
        return ""
    word_pos = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_pos.append((pos, word))
    word_pos.sort(key=lambda x: x[0])
    return " ".join(w[1] for w in word_pos)


def get_best_url(item):
    """안전하고 접근 가능한 최적의 학술 URL 도출 (DOI, 랜딩페이지, 오픈액세스 URL 검증)"""
    doi = item.get("doi")
    prim_loc = item.get("primary_location") or {}
    landing_url = prim_loc.get("landing_page_url")
    best_oa = item.get("best_oa_location") or {}
    oa_url = best_oa.get("landing_page_url") or item.get("open_access", {}).get("oa_url")

    # Humanities Commons / MLA Core(10.17613) 등 로그인 루프가 발생할 수 있는 DOI는 랜딩페이지 우선
    if doi and "10.17613" in doi and landing_url:
        return landing_url

    if doi:
        if not doi.startswith("http"):
            return f"https://doi.org/{doi}"
        return doi

    return landing_url or oa_url or item.get("id") or ""


# 도메인별 필수 긍정 키워드 (검색/arXiv 수집 시 최소 1개 이상 매칭 필수)
DOMAIN_REQUIRED_KEYWORDS = {
    "커먼즈·공유재": ["common", "ostrom", "p2p", "peer production", "cooperative", "open access", "caring", "solidarity"],
    "과학기술학·STS": ["socio-technical", "technology politics", "data justice", "algorithmic", "surveillance", "sts", "science and technology studies", "platform"],
    "시빅HCI·UXR": ["civic", "participatory", "public service", "citizen", "co-design", "crisis informatics", "disaster", "accessibility", "community"],
    "농생태·식량주권": ["agroecol", "food sovereignty", "peasant", "seed", "smallholder", "ecofeminism", "multispecies", "soil", "ecological", "earth"],
    "공간사회·도시커먼즈": ["urban", "spatial justice", "right to the city", "gentrification", "extractivism", "commons", "public space", "territor"],
    "재난안전·공공인프라": ["disaster", "vulnerab", "public safety", "green social work", "crisis response", "infrastructure", "hazard"],
    "돌봄·상호부조": ["care", "respect", "mutual aid", "reproductive labor", "patient", "community care", "nursing"]
}


def is_valid_candidate(title, abstract, category):
    """엄격한 관련성 검사: 언어 필터, 블랙리스트 배제 및 도메인 필수 키워드 검증"""
    if not title or len(title.strip()) < 12:
        return False

    full_text = f"{title} {abstract}".lower()

    # 1. 비영어/비한국어 외국어 논문 배제 (스페인어, 포르투갈어, 인도네시아어 등 잡음 차단)
    foreign_stops = [
        " de la ", " y ", " en el ", " en la ", " das ", " dos ", " uma ", " para ",
        " contracoloniais", " diálogos ", " turismo comunitario ", " hunian ", " warga ",
        " resistencia urbana", " periferia norte"
    ]
    padded_title = f" {title.lower()} "
    if any(stop in padded_title for stop in foreign_stops):
        return False

    # 2. 블랙리스트 검사
    for bad in EXCLUDE_KEYWORDS:
        if bad.lower() in full_text:
            return False

    # 3. 도메인 필수 키워드 검증 (저널 직접 발행 논문이 아닌 검색/arXiv/RSS인 경우)
    req_kws = DOMAIN_REQUIRED_KEYWORDS.get(category, [])
    if req_kws:
        has_domain_signal = any(kw in full_text for kw in req_kws)
        if not has_domain_signal:
            return False

    return True


def fetch_openalex_journal(journal_config, limit=6):
    """OpenAlex API를 통해 특정 핵심 저널의 최신 논문 수집"""
    results = []
    issn = journal_config["issn"]
    url = f"https://api.openalex.org/works?filter=primary_location.source.issn:{issn}&sort=publication_date:desc&per-page={limit}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            data = res.json().get("results", [])
            for item in data:
                title = item.get("title") or ""
                if not title:
                    continue
                abstract = reconstruct_abstract(item.get("abstract_inverted_index"))

                # 블랙리스트 제외 검사
                if not is_valid_candidate(title, abstract, journal_config["category"]):
                    continue

                authors = []
                for a in (item.get("authorships") or [])[:3]:
                    if a and isinstance(a, dict):
                        auth = a.get("author") or {}
                        name = auth.get("display_name", "")
                        if name:
                            authors.append(name)
                best_url = get_best_url(item)
                item_id = item.get("doi") or item.get("id") or best_url
                results.append({
                    "id": item_id,
                    "title": title,
                    "abstract": abstract[:1000] if abstract else "Abstract not available in metadata.",
                    "url": best_url,
                    "source": journal_config["name"],
                    "category": journal_config["category"],
                    "authors": ", ".join(filter(None, authors)) or "연구진",
                    "published": item.get("publication_date", ""),
                    "type": "scholarly_paper"
                })
    except Exception as e:
        print(f"Error fetching OpenAlex journal {journal_config['name']}: {e}", file=sys.stderr)
    return results


def fetch_openalex_search(query_config, limit=6):
    """OpenAlex 검색 쿼리를 통한 최신 주제 논문 수집 (엄격한 관련성 필터링 적용)"""
    results = []
    query = query_config["query"]
    url = f"https://api.openalex.org/works?search={requests.utils.quote(query)}&sort=publication_date:desc&per-page={limit*2}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            data = res.json().get("results", [])
            for item in data:
                title = item.get("title") or ""
                if not title:
                    continue
                abstract = reconstruct_abstract(item.get("abstract_inverted_index"))

                # 엄격한 관련성 검사 (블랙리스트 배제 + 도메인 시그널 검증)
                if not is_valid_candidate(title, abstract, query_config["category"]):
                    continue

                authors = []
                for a in (item.get("authorships") or [])[:3]:
                    if a and isinstance(a, dict):
                        auth = a.get("author") or {}
                        name = auth.get("display_name", "")
                        if name:
                            authors.append(name)

                best_url = get_best_url(item)
                item_id = item.get("doi") or item.get("id") or best_url
                prim_loc = item.get("primary_location") or {}
                source_obj = prim_loc.get("source") or {}
                source_name = source_obj.get("display_name") or "Scholarly Pre-print / Journal"
                results.append({
                    "id": item_id,
                    "title": title,
                    "abstract": abstract[:1000] if abstract else "",
                    "url": best_url,
                    "source": source_name,
                    "category": query_config["category"],
                    "authors": ", ".join(filter(None, authors)) or "연구진",
                    "published": item.get("publication_date", ""),
                    "type": "scholarly_paper"
                })
                if len(results) >= limit:
                    break
    except Exception as e:
        print(f"Error fetching OpenAlex search {query_config['name']}: {e}", file=sys.stderr)
    return results


def fetch_arxiv(arxiv_config, limit=5):
    """arXiv API를 통한 프리프린트 수집 (엄격한 필터링)"""
    results = []
    query = arxiv_config["query"]
    url = f"http://export.arxiv.org/api/query?search_query={requests.utils.quote(query)}&sortBy=submittedDate&sortOrder=descending&max_results={limit*2}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns):
                title = entry.find("atom:title", ns).text or ""
                title = re.sub(r"\s+", " ", title).strip()
                abstract = entry.find("atom:summary", ns).text or ""
                abstract = re.sub(r"\s+", " ", abstract).strip()

                # 엄격한 관련성 검사 (블랙리스트 배제 + 도메인 시그널 검증)
                if not is_valid_candidate(title, abstract, arxiv_config["category"]):
                    continue

                url_el = entry.find("atom:id", ns)
                paper_url = url_el.text.strip() if url_el is not None else ""
                authors = [
                    a.find("atom:name", ns).text
                    for a in entry.findall("atom:author", ns)
                    if a.find("atom:name", ns) is not None
                ]
                published = entry.find("atom:published", ns)
                pub_date = published.text[:10] if published is not None else ""

                results.append({
                    "id": paper_url,
                    "title": title,
                    "abstract": abstract[:1000],
                    "url": paper_url,
                    "source": "arXiv cs.HC / cs.CY",
                    "category": arxiv_config["category"],
                    "authors": ", ".join(authors[:3]) or "연구진",
                    "published": pub_date,
                    "type": "scholarly_paper"
                })
                if len(results) >= limit:
                    break
    except Exception as e:
        print(f"Error fetching arXiv {arxiv_config['name']}: {e}", file=sys.stderr)
    return results


def fetch_rss(feed_config, limit=4):
    """RSS 피드 수집 (블랙리스트 및 관련성 검증)"""
    results = []
    url = feed_config["url"]
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            channel = root.find("channel")
            if channel is not None:
                for item in channel.findall("item")[:limit*2]:
                    title = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else ""
                    desc = item.find("description").text if item.find("description") is not None else ""
                    desc = re.sub(r"<[^>]+>", "", desc)

                    if not is_valid_candidate(title, desc, feed_config["category"]):
                        continue

                    results.append({
                        "id": link,
                        "title": title.strip(),
                        "abstract": desc.strip()[:800],
                        "url": link.strip(),
                        "source": feed_config["name"],
                        "category": feed_config["category"],
                        "authors": feed_config["name"],
                        "published": datetime.now().strftime("%Y-%m-%d"),
                        "type": "news_article"
                    })
                    if len(results) >= limit:
                        break
    except Exception as e:
        print(f"Error fetching RSS {feed_config['name']}: {e}", file=sys.stderr)
    return results


def fetch_all(exclude_archived=True):
    """모든 소스에서 후보 수집, 기수집 아카이브 중복 제거 및 신선도 보장"""
    raw_candidates = []
    archived_seen = get_archived_identifiers() if exclude_archived else set()

    # 1. 핵심 학술 저널 (OpenAlex) - 최우선 순위
    for j in TARGET_JOURNALS:
        raw_candidates.extend(fetch_openalex_journal(j, limit=5))

    # 2. 학술 쿼리 (OpenAlex & arXiv)
    for q in SCHOLARLY_QUERIES:
        if q["type"] == "openalex_search":
            raw_candidates.extend(fetch_openalex_search(q, limit=4))
        elif q["type"] == "arxiv":
            raw_candidates.extend(fetch_arxiv(q, limit=4))

    # 3. 뉴스 및 비판 담론 RSS
    for r in RSS_FEEDS:
        raw_candidates.extend(fetch_rss(r, limit=3))

    # 중복 제거 (세션 내 중복 및 기존 아카이브 중복 제외)
    seen_urls = set()
    fresh_candidates = []
    archived_fallback = []

    for item in raw_candidates:
        url = (item.get("url") or "").strip().lower()
        doi = (item.get("id") or "").strip().lower()
        title = (item.get("title") or "").strip().lower()

        if not url or url in seen_urls:
            continue
        seen_urls.add(url)

        # 과거 아카이브에 이미 포함된 논문인지 검사
        is_archived = (url in archived_seen) or (doi in archived_seen) or (title in archived_seen)
        if not is_archived:
            fresh_candidates.append(item)
        else:
            archived_fallback.append(item)

    # 신선한 미수집 후보가 충분하면 신선한 후보만 반환, 부족하면 폴백 결합
    if len(fresh_candidates) >= 8:
        print(f"      [Fetcher] Fresh candidate pool: {len(fresh_candidates)} items (Filtered out {len(archived_fallback)} previously archived).")
        return fresh_candidates
    else:
        print(f"      [Fetcher] Fresh candidates: {len(fresh_candidates)}, supplementing with fallback.")
        return fresh_candidates + archived_fallback[:(12 - len(fresh_candidates))]


if __name__ == "__main__":
    items = fetch_all()
    print(f"Total candidate items fetched: {len(items)}")
    for i, it in enumerate(items[:6], 1):
        print(f"[{i}] ({it['category']}) {it['title']} - {it['source']}")
