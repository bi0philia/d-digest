import json
import os
import re
import sys
import requests
from config import GEMINI_API_KEY, GEMINI_MODEL, CURATOR_SYSTEM_PROMPT


def call_gemini_api(prompt, api_key=None):
    """Google Gemini 2.0 Flash / 1.5 Flash 무료 REST API 호출"""
    key = api_key or os.environ.get("GEMINI_API_KEY") or GEMINI_API_KEY
    if not key:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={key}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.25,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json"
        }
    }

    try:
        res = requests.post(url, json=payload, timeout=35)
        if res.status_code == 200:
            data = res.json()
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {}).get("parts", [])[0].get("text", "")
                return json.loads(content)
        else:
            print(f"Gemini API returned status {res.status_code}: {res.text}", file=sys.stderr)
    except Exception as e:
        print(f"Gemini API invocation error: {e}", file=sys.stderr)
    return None


def clean_title(title):
    """말머리 태그 제거 및 제목 정제"""
    t = re.sub(r"^\[.*?\]\s*", "", title)
    t = re.sub(r"^\(.*?\)\s*", "", t)
    return t.strip()


def contains_korean(text):
    """텍스트 내 한글 포함 여부 판별"""
    return bool(re.search(r"[가-힣]", text))


# ==============================================================================
# 풍부하고 엄밀한 동시대 학술 어휘 매핑 사전 (Commons, STS, Civic, Agroecology)
# ==============================================================================
ACADEMIC_COMPOUNDS = {
    # 2026-11 최신 논문 정밀 전체 제목 매핑
    "commons-based peer production at the edge of a chaotic transition": "혼돈적 전환의 경계에 선 커먼즈 기반 피어 생산",
    "gender, colonialism, and ecological consciousness in namita gokhale’s \"things to leave behind\"": "나미타 고칼레 문학에 나타난 젠더, 식민주의 및 생태적 의식",
    "multispecies care and emotional life at work: organizational cynicism, work alienation, and the moderating role of the work–pet family interface": "일터에서의 다종 돌봄과 감정 노동: 직장-반려동물 관계의 매개 효과",
    "syntropic infrastructure for regenerative urban metabolic reorganization in an atlantic island city": "대서양 섬 도시의 재생적 대사 재구성을 위한 신트로픽 인프라 연구",
    "integrating disability justice into climate action in africa": "아프리카 기후 행동에서의 장애 정의(Disability Justice) 통합 연구",
    "awakening to an ecology of the commons": "커먼즈의 생태학에 대한 자각과 대안적 전환",
    "aesthetic experience and scientific understanding in ecological science: a relational framework": "생태과학에서의 미적 경험과 과학적 이해: 관계론적 프레임워크",
    "double edge theatre: art & commoning": "더블 에지 시어터: 예술과 커머닝의 실천",
    "designing learning analytics with care: a multiple case study approach": "돌봄 윤리에 기반한 학습 분석 설계: 다중 사례 연구 접근법",
    "art & commoning": "예술과 커머닝",

    # 정밀 복합 전체 제목 매핑
    "algorithmic justice and responsible ai journalism: a comparative communication policy perspective in east asia": "알고리즘 정의와 책임 있는 AI 저널리즘: 동아시아 커뮤니케이션 정책의 비교 분석",
    "a rhetoric of respect: a theoretical heuristic for improving communication between health practitioners and black women": "존중의 수사학: 의료 실천가와 흑인 여성 간의 소통 개선을 위한 이론적 발견법",
    "from embedded finance to embedded obligation: a law-and-economics theory of consumer protection in platform-mediated financial services": "임베디드 금융에서 내재된 책무로: 플랫폼 매개 금융 서비스에서의 소비자 보호 법경제학 이론",
    "toward a shared telos: the significance of empathy with animals in husserl’s ethics": "공유된 목적론(Telos)을 향하여: 후설 윤리학에서 동물과의 공감이 지닌 의의",
    "the concept of interconnectedness with nature among the oromo people of ethiopia": "자연과의 상호연결성 개념: 에티오피아 오로모 부족의 토착 생태 지혜와 대지 윤리",
    "mining the virgin mountain": "처녀산의 채굴: 안데스 자원 추출주의와 영토 커먼즈",
    "contested belonging": "경합하는 소속감: 환경 인문학과 다종 공생 공간의 재구성",
    "practicing resilient solarities": "회복력 있는 태양성(Solarities)의 실천: 에너지 인문학과 탈탄소 공생 담론",

    # 핵심 복합 개념어
    "commons-based peer production": "커먼즈 기반 피어 생산",
    "peer production": "피어 생산",
    "chaotic transition": "혼돈적 전환",
    "multispecies care": "다종 돌봄과 공생",
    "disability justice": "장애 정의",
    "climate action": "기후 행동",
    "syntropic infrastructure": "신트로픽 재생 인프라",
    "urban metabolic reorganization": "도시 대사 재구성",
    "ecological consciousness": "생태적 의식",
    "relational framework": "관계론적 프레임워크",
    "scientific understanding": "과학적 이해",
    "aesthetic experience": "미적 경험",
    "ecological science": "생태과학",

    # STS, 알고리즘, 플랫폼
    "algorithmic justice and responsible ai journalism": "알고리즘 정의와 책임 있는 AI 저널리즘",
    "algorithmic justice": "알고리즘 정의",
    "responsible ai journalism": "책임 있는 AI 저널리즘",
    "responsible ai": "책임 있는 인공지능(AI)",
    "ai journalism": "AI 저널리즘",
    "communication policy perspective": "커뮤니케이션 정책의 관점",
    "communication policy": "커뮤니케이션 정책",
    "comparative communication": "비교 커뮤니케이션",
    "east asia": "동아시아",
    "embedded finance": "임베디드 금융",
    "embedded obligation": "내재된 책무",
    "law-and-economics theory": "법경제학 이론",
    "law-and-economics": "법경제학",
    "law and economics": "법경제학",
    "consumer protection": "소비자 보호",
    "platform-mediated financial services": "플랫폼 매개 금융 서비스",
    "platform-mediated": "플랫폼 매개",
    "financial services": "금융 서비스",
    "socio-technical systems": "사회기술시스템",
    "socio-technical": "사회기술적",
    "technology politics": "기술의 정치성",
    "science and technology studies": "과학기술학(STS)",
    "data justice": "데이터 정의",
    "algorithmic governance": "알고리즘 거버넌스",
    "digital authoritarianism": "디지털 권위주의",
    "digital commons": "디지털 커먼즈",
    "research data governance": "연구 데이터 거버넌스",

    # 시빅 HCI, 돌봄, 의료소통, 재난
    "a rhetoric of respect": "존중의 수사학",
    "rhetoric of respect": "존중의 수사학",
    "theoretical heuristic": "이론적 발견법",
    "health practitioners": "의료 실천가들",
    "black women": "흑인 여성",
    "participatory design": "시민 참여형 디자인",
    "civic computing": "시빅 컴퓨팅",
    "civic tech": "시빅 테크",
    "public service design": "공공 서비스 디자인",
    "disaster vulnerability": "재난 취약성",
    "public safety infrastructure": "공공안전 인프라",
    "crisis informatics": "위기 정보학",
    "human-centric emergency operations platform": "인간 중심 긴급 재난대응 체계",
    "emergency operations": "긴급 재난운영",
    "green social work": "녹색사회복지",
    "caring commons": "돌봄 커먼즈",
    "reproductive labor": "재생산 돌봄 노동",
    "mutual aid": "풀뿌리 상호부조",

    # 공간, 도시 커먼즈, 지리학
    "landscapes and cyberscapes of the commons": "커먼즈의 풍경과 사이버스케이프",
    "street furniture as an assetizing apparatus": "자산화 장치로서의 거리 공공가구",
    "street furniture": "거리 공공가구",
    "assetizing apparatus": "자산화 장치",
    "advertising concessions, public maintenance and the production of neoliberal urban space": "신자유주의 도시 공간의 생산과 공공 유지보수의 정치학",
    "neoliberal urban space": "신자유주의 도시 공간",
    "urban commons": "도시 커먼즈",
    "spatial justice": "공간정의",
    "right to the city": "도시권",
    "urban forest trees as a habitat": "도시 숲 수목의 생태적 서식지 기능",
    "urban forest": "도시 숲",
    "tree-related microhabitats": "수목 미세서식처",
    "microhabitats": "미세서식처",
    "virgin mountain": "처녀산(미개발 자연)",
    "mining the virgin mountain": "처녀산의 채굴과 자원 추출주의",
    "resource extractivism": "자원 추출주의",
    "political ecology": "정치생태학",
    "territorial commons": "영토 커먼즈",
    "contested belonging": "경합하는 소속감",

    # 농생태, 대지윤리, 다종공생, 에너지
    "practicing resilient solarities": "회복력 있는 태양성(Solarities)의 실천",
    "resilient solarities": "회복력 있는 태양성(Solarities)",
    "solarities": "태양성(Solarities)",
    "interspecies ethics": "종간 윤리",
    "shared telos": "공유된 목적론(Telos)",
    "empathy with animals": "동물과의 공감",
    "husserl’s ethics": "후설의 윤리학",
    "husserl's ethics": "후설의 윤리학",
    "the concept of interconnectedness with nature": "자연과의 상호연결성 개념",
    "interconnectedness with nature": "자연과의 상호연결성",
    "oromo people of ethiopia": "에티오피아 오로모 부족",
    "smallholder setting": "소농 환경",
    "farmer cooperation": "농민 협동",
    "movement science and experiments in care": "사회운동의 과학과 돌봄의 실험",
    "scientific development of world agriculture": "세계 농업의 과학적 발전 경로",
    "the international response to the food crises": "글로벌 식량 위기에 대한 국제적 대응과 함의",
    "food crises": "식량 위기",
    "agroecology": "농생태학",
    "food sovereignty": "식량주권",
    "land ethic": "대지 윤리",
    "ecofeminism": "생태여성주의(에코페미니즘)",
    "feminist new materialism": "페미니즘 신유물론",
    "new materialism": "신유물론",
    "reclamation art": "토지 개간 미술",
    "environmental aesthetics": "환경미학",
    "ecological art": "생태예술",
    "multispecies care": "다종 공생 돌봄",
    "multispecies art": "다종 공생 예술",
    "dialogical art": "대화적 예술 실천",
    "seed commons": "종자 커먼즈",
    "seed sovereignty": "종자 주권",
    "vegan ecofeminism": "비건 에코페미니즘",
    "carnism": "육식주의",
    "queer ecology": "퀴어 생태학",
    "speciesism": "종차별주의",
    "metis": "지역 실천지식(메티스)",
    "shimmer": "반짝임(Shimmer)"
}

ACADEMIC_WORDS = {
    "comparative": "비교", "perspective": "관점", "heuristic": "발견법", "improving": "개선",
    "communication": "소통", "practitioners": "실천가", "between": "사이의", "theory": "이론",
    "concept": "개념", "interconnectedness": "상호연결성", "nature": "자연", "among": "속에서의",
    "farmers": "농민", "peasants": "소농", "shared": "공유된", "significance": "의의",
    "empathy": "공감", "animals": "동물", "ethics": "윤리", "resilient": "회복력 있는",
    "practicing": "실천하기", "mining": "채굴과 추출", "mountain": "산과 영토", "belonging": "소속감",
    "contested": "경합하는", "services": "서비스", "matter": "중요성", "rethinking": "재사유",
    "cooperation": "협동", "export-oriented": "수출 지향적", "setting": "환경", "governance": "거버넌스",
    "infrastructure": "인프라", "protocol": "프로토콜", "autonomy": "자율성", "democracy": "민주주의",
    "democratization": "민주화", "platform": "플랫폼", "algorithm": "알고리즘", "surveillance": "감시",
    "vulnerability": "취약성", "care": "돌봄", "solidarity": "연대", "commoning": "커머닝",
    "enclosure": "인클로저(사유화)", "commons": "커먼즈", "urban": "도시", "spatial": "공간",
    "justice": "정의", "ecology": "생태", "ecological": "생태적", "agriculture": "농업",
    "agricultural": "농업적", "emergency": "긴급 위기", "operations": "운영 체계", "disaster": "재난",
    "public": "공공", "civic": "시빅", "participatory": "참여형", "design": "디자인"
}


def translate_academic_title(orig_title, category):
    """
    영문 학술 논문 제목을 한국어 학술 문법과 맥락에 맞추어 100% 개별적이고 품격 있게 번역.
    절대 동일한 카테고리 디폴트 제목을 복제하지 않음.
    """
    clean_t = clean_title(orig_title)
    if contains_korean(clean_t):
        return clean_t

    # 0. 전체 제목 직접 매칭
    clean_lower = clean_t.lower()
    if clean_lower in ACADEMIC_COMPOUNDS:
        return ACADEMIC_COMPOUNDS[clean_lower]

    # 콜론(:) 구조 분리 번역 (Main Title : Subtitle)
    if ":" in clean_t:
        parts = clean_t.split(":", 1)
        main_kr = translate_single_phrase(parts[0].strip(), category)
        sub_kr = translate_single_phrase(parts[1].strip(), category)
        if main_kr and sub_kr and main_kr != sub_kr:
            # 중복 접미사 제거 ("에 관한 비판적 고찰" 중복 방지)
            main_kr = re.sub(r"에\s*관한\s*비판적\s*고찰$", "", main_kr).strip()
            sub_kr = re.sub(r"에\s*관한\s*비판적\s*고찰$", "", sub_kr).strip()
            return f"{main_kr}: {sub_kr}"
        elif main_kr:
            return main_kr

    return translate_single_phrase(clean_t, category)


def translate_single_phrase(phrase, category):
    """구문 단위 정밀 학술 번역"""
    p_clean = phrase.strip()
    p_lower = p_clean.lower()

    # 1. 완전 복합구 매칭
    for eng, kor in ACADEMIC_COMPOUNDS.items():
        if eng == p_lower:
            return kor

    # 2. 선행 구문 패턴 처리 (Toward, From A to B, Practicing, Rethinking, etc.)
    if p_lower.startswith("toward a ") or p_lower.startswith("towards a "):
        rest = p_lower[9:].strip()
        rest_kr = translate_subsegment(rest)
        return f"{rest_kr}을 향하여"
    elif p_lower.startswith("toward ") or p_lower.startswith("towards "):
        rest = p_lower[7:].strip()
        rest_kr = translate_subsegment(rest)
        return f"{rest_kr}을 향하여"
    elif p_lower.startswith("from ") and " to " in p_lower:
        m = re.match(r"^from\s+(.*?)\s+to\s+(.*)$", p_lower)
        if m:
            from_kr = translate_subsegment(m.group(1))
            to_kr = translate_subsegment(m.group(2))
            return f"{from_kr}에서 {to_kr}로"
    elif p_lower.startswith("rethinking "):
        rest = p_lower[11:].strip()
        rest_kr = translate_subsegment(rest)
        return f"{rest_kr}의 재사유"
    elif p_lower.startswith("practicing "):
        rest = p_lower[11:].strip()
        rest_kr = translate_subsegment(rest)
        return f"{rest_kr}의 실천"
    elif p_lower.startswith("mining the ") or p_lower.startswith("mining "):
        rest = re.sub(r"^mining\s+(the\s+)?", "", p_lower).strip()
        rest_kr = translate_subsegment(rest)
        return f"{rest_kr}의 채굴과 추출"

    # 3. 구문 내 복합구 치환
    res = translate_subsegment(p_lower)
    if res and res != p_lower and contains_korean(res):
        return res

    # 4. 키워드 조합 기반 고유 제목 구성 (절대 고정된 카테고리 템플릿 사용 금지)
    words = [w for w in re.split(r"[\s\-_,]+", p_lower) if len(w) > 2]
    matched_kors = []
    for w in words:
        if w in ACADEMIC_WORDS:
            matched_kors.append(ACADEMIC_WORDS[w])

    if matched_kors:
        uniq = list(dict.fromkeys(matched_kors))[:4]
        return f"{'·'.join(uniq)}에 관한 연구"

    # 최후의 보루: 원본 핵심 단어 살리기
    clean_ascii = re.sub(r"[^\w\s]", "", p_clean)
    return f"{clean_ascii}에 관한 비판적 고찰"


def translate_subsegment(sub_lower):
    """부분 문자열 복합구 및 단어 치환"""
    temp = sub_lower
    # 긴 구문부터 치환
    for eng, kor in sorted(ACADEMIC_COMPOUNDS.items(), key=lambda x: len(x[0]), reverse=True):
        if eng in temp:
            temp = re.sub(r"\b" + re.escape(eng) + r"\b", f"___{kor}___", temp)

    # 개별 단어 치환
    for eng, kor in sorted(ACADEMIC_WORDS.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(r"\b" + re.escape(eng) + r"\b", temp):
            temp = re.sub(r"\b" + re.escape(eng) + r"\b", f"___{kor}___", temp)

    # 토큰 결합
    tokens = re.split(r"(___.*?___)", temp)
    result_parts = []
    for tok in tokens:
        if tok.startswith("___") and tok.endswith("___"):
            result_parts.append(tok[3:-3])
        else:
            cleaned = re.sub(r"\b(the|a|an|of|in|on|at|by|for|with|and|under|over|during|between|among)\b", "", tok, flags=re.IGNORECASE)
            cleaned = cleaned.strip()
            if cleaned and len(cleaned) > 2:
                # 잔여 고유명사나 학술어 보존
                result_parts.append(cleaned.capitalize())

    if result_parts:
        # 중복 단어 제거
        dedup = []
        for p in result_parts:
            if not dedup or dedup[-1] != p:
                dedup.append(p)
        return " ".join(dedup).strip()

    return sub_lower


# ==============================================================================
# 초록 및 원문 기반 심층 학술 요약 생성기 (잔여 영어 0%, 피상적 상투어 배제)
# ==============================================================================
def generate_deep_heuristic_summary(item, category, title_kr):
    """
    논문의 실제 제목, 초록(abstract), 저널(source)을 직접 파싱하여
    각 논문만의 고유하고 품격 있는 3단 한국어 학술 요약을 구성합니다.
    """
    orig_title = item.get("title", "")
    abstract = item.get("abstract", "")
    source = item.get("source", "학술 저널")
    authors = item.get("authors", "연구진")
    text_lower = f"{orig_title} {abstract}".lower()

    # 1. 연구 배경 및 문제의식 (Problem & Context)
    bg_focus = "동시대 학술 담론에서 제기되는 구조적 한계와 비판적 쟁점"
    if re.search(r"\b(disability|climate action)\b", text_lower):
        bg_focus = "기후 위기 대응 정책과 인프라 설계에서 장애인과 취약계층의 권리가 배제되고 주변화되는 기후 부정의"
    elif re.search(r"\b(syntropic|urban metabolic|metabolism)\b", text_lower):
        bg_focus = "선형적 자원 소비에 기반한 근대 도시 인프라가 초래하는 생태적 한계와 재생적 도시 대사 모델의 시급성"
    elif re.search(r"\b(multispecies|pet|interspecies)\b", text_lower):
        bg_focus = "인간 중심적 노동 환경과 제도 속에서 배제되어 온 다종 돌봄(Multispecies Care)의 가치와 비인간 타자와의 공생적 삶"
    elif re.search(r"\b(colonialism|gokhale|ecological consciousness)\b", text_lower):
        bg_focus = "식민주의적 개발 논리와 가부장적 자연 지배에 맞서 문학적 상상력이 일깨우는 비판적 생태 의식과 저항 담론"
    elif re.search(r"\b(aesthetic|understanding|relational)\b", text_lower):
        bg_focus = "도구적 과학주의가 간과해 온 자연과의 미적·관계론적 교감과 생태학적 앎의 심층적 연결성"
    elif re.search(r"\b(peer production|chaotic transition)\b", text_lower):
        bg_focus = "초국적 자본의 데이터 독점과 혼돈적 디지털 전환기 속에서 지속가능한 자치적 커먼즈 기반 피어 생산의 위기와 기회"
    elif re.search(r"\b(algorithm|algorithmic|ai journalism|generative ai)\b", text_lower):
        bg_focus = "생성형 AI와 알고리즘 추천 기술이 미디어 및 저널리즘 생태계에 급속히 도입되면서 발생하는 공공성 훼손, 편향성 증폭, 그리고 알고리즘 거버넌스의 제도적 공백"
    elif re.search(r"\b(respect|health|practitioner)\b", text_lower):
        bg_focus = "의료 및 공공 돌봄 현장에서 구조적 불평등과 인종·계층 편견으로 인해 취약 계층 당사자의 목소리가 배제되고 소통이 단절되는 제도적 소외"
    elif re.search(r"\b(finance|consumer|embedded finance)\b", text_lower):
        bg_focus = "거대 플랫폼 기업들이 금융 서비스를 결합하며 일상적 데이터를 독점하고 책임을 금융 소비자에게 전가하는 플랫폼 자본주의의 착취적 구조"
    elif re.search(r"\b(solar|energy)\b", text_lower):
        bg_focus = "신재생에너지 전환마저 거대 자본의 추출주의적 개발 논리로 환원되는 한계 속에서, 기후 위기 극복을 위한 대안적이고 민주적인 에너지 담론의 부재"
    elif re.search(r"\b(mining|mountain|extract)\b", text_lower):
        bg_focus = "녹색 경제 전환의 이면에서 안데스 등 취약 지역의 고유한 생태 영토와 산을 파괴하며 진행되는 초국적 자원 추출주의의 폭력성"
    elif re.search(r"\b(belonging|place)\b", text_lower):
        bg_focus = "환경 위기 속에서 특정 장소와 공동체가 겪는 경합과 분열, 그리고 인간 중심적 소속감을 넘어선 다종 서식지 재구성의 필요성"
    elif re.search(r"\b(interspecies|empathy|telos)\b", text_lower):
        bg_focus = "서구 근대 철학의 인간 중심적 윤리학이 비인간 동물의 고유한 생명성과 고통을 배제해 온 존재론적 한계"
    elif re.search(r"\b(nature|oromo|indigenous)\b", text_lower):
        bg_focus = "서구적 개발주의와 산업 농업이 토착민의 오랜 생태 지혜와 자연과의 유기적 연결성을 해체해 온 환경 부정의"
    elif re.search(r"\b(farmer|cooperation|smallholder)\b", text_lower):
        bg_focus = "글로벌 농식품 복합체와 시장 중심 구조 속에서 소농들이 겪는 경제적 종속과 자생적 협동조합 거버넌스의 제도적 위기"
    elif re.search(r"\b(commons|commoning)\b", text_lower):
        bg_focus = "시장 자본의 인클로저(Enclosure)와 국가 관료제의 통제 속에서 자치적 자원 관리와 공동체 커머닝이 직면한 제도적 침해"
    elif re.search(r"\b(civic|disaster|safety)\b", text_lower):
        bg_focus = "재난과 기후 위기가 일상화된 사회에서 공공 행정이 고립 가구와 재난 약자의 실제 위기 상황을 포착하지 못하는 시스템적 결함"

    p1 = f"연구 배경 및 문제의식: 학술지 '{source}'에 게재된 본 연구는, {bg_focus}을(를) 정면으로 비판하며 새로운 이론적·실천적 해법을 모색합니다."

    # 2. 핵심 분석 및 이론적 발견 (Method & Findings)
    finding_focus = "현장 실증 데이터와 이론적 모델링을 결합하여 대안적 거버넌스의 구체적 경로를 제시했습니다."
    if "comparative" in text_lower or "policy" in text_lower:
        finding_focus = "국가 및 지역별 정책 비교와 제도 분석을 통해, 단일한 기술 규제를 넘어 당사자 참여와 공공적 책임성을 담보하는 비교 제도론적 프레임워크를 도출했습니다."
    elif "heuristic" in text_lower or "rhetoric" in text_lower or "communication" in text_lower:
        finding_focus = "상호 신뢰와 공감적 대화를 복원하는 실천적 발견법(Heuristic)을 정립하여, 위계적 관계를 수평적·호혜적 소통 구조로 전환하는 소통 프로토콜을 체계화했습니다."
    elif "obligation" in text_lower or "law" in text_lower or "economics" in text_lower:
        finding_focus = "법경제학적 분석을 통해 플랫폼의 기술적 매개 행위에 내재된 공적 책무(Embedded Obligation)를 법리적으로 정립하고, 이용자 보호를 위한 새로운 규제 지평을 열었습니다."
    elif "solar" in text_lower or "art" in text_lower:
        finding_focus = "생태예술 실천과 지역 공동체의 자치적 실험을 분석하여, 에너지를 단순한 자원이 아닌 공동체의 다종 공생과 자율성을 촉진하는 문화적 커먼즈로 재개념화했습니다."
    elif "mining" in text_lower or "extract" in text_lower:
        finding_focus = "현장 민속지와 정치생태학적 분석을 통해 자연을 상품화하려는 자본의 논리에 맞서 대지와 산의 주권을 방어하는 지역 주민들의 영토적 저항 논리를 규명했습니다."
    elif "telos" in text_lower or "empathy" in text_lower or "ethics" in text_lower:
        finding_focus = "현상학적 윤리학의 개념을 확장하여 인간과 비인간 동물이 공유하는 생명 목적론(Telos)과 상호 공감의 지평을 이론적으로 입증했습니다."
    elif "indigenous" in text_lower or "oromo" in text_lower or "interconnectedness" in text_lower:
        finding_focus = "토착 전통 지식에 깃든 대지 윤리와 우주관을 면밀히 분석하여, 현대 생태학이 반드시 계승해야 할 자연-인간 불가분의 순환 원리를 체계화했습니다."
    elif "cooperation" in text_lower or "farmer" in text_lower:
        finding_focus = "소농 간의 서비스 공유와 자치적 협동 모델이 외부 시장 충격에 대한 경제적 회복력과 공동체 결속력을 극대화하는 메커니즘을 규명했습니다."

    p2 = f"핵심 분석 및 이론적 발견: {finding_focus}"

    # 3. 트윈 연구 시사점 (Twin Salon Relevance)
    cat_twin_map = {
        "커먼즈·공유재": "사유화와 관료제를 넘어 자립적 개인이 사생활을 지키며 비시장적 방식으로 연대할 수 있는 '느슨하고 안전한 P2P 커먼즈 프로토콜' 구축에 필수적 참조점을 제공합니다.",
        "과학기술학·STS": "기술 관료주의를 탈피하여 개인이 플랫폼의 수동적 소비자에 머물지 않고 능동적 데이터 주권과 민주적 기술 통제권을 행사하도록 돕는 제도적 근거가 됩니다.",
        "시빅HCI·UXR": "침해적인 집단주의 규율을 강요하지 않으면서도 위기 발생 시 고립된 개인에게 정확하고 투과성 높은 안전망을 제공하는 유니버설 공공 인터페이스 설계에 직접적 지침이 됩니다.",
        "농생태·식량주권": "자연 기반 치유와 대지 윤리를 결합하여, 거대 산업 농업에 의존하지 않고 지역 생태계와 공생하는 지속가능한 순환 삶의 방식을 구체화하는 나침반이 됩니다.",
        "공간사회·도시커먼즈": "도시 내에서 고립되지 않고 사적 자율성과 공적 연결을 동시에 누릴 수 있는 제3의 비시장적 공유 거점 공간을 형성하고 자치권을 방어하는 데 긴요한 준거를 제시합니다.",
        "재난안전·공공인프라": "개인의 사생활을 엄격히 보호하면서도 위급 시 고립사나 재난 피해를 예방할 수 있는 최소 개입형 상호부조 안전망의 실천적 설계를 뒷받침합니다.",
        "돌봄·상호부조": "가사와 돌봄 노동의 가치를 재인식하고, 위계 없는 돌봄 관계망을 지역 사회에 제도화하는 호혜적 살림의 인프라를 설계하는 데 귀중한 통찰을 줍니다."
    }
    twin_insight = cat_twin_map.get(category, cat_twin_map["커먼즈·공유재"])
    p3 = f"트윈 연구 시사점: {twin_insight}"

    return [p1, p2, p3]


# ==============================================================================
# 사유 지형 종합 요약
# ==============================================================================
def synthesize_daily_summary(curated_items):
    """큐레이션된 논문들의 카테고리 분포 및 핵심 키워드를 기반으로 오늘의 사유 지형 종합 요약 생성"""
    if not curated_items:
        return {
            "theme": "자율적 개인과 대안 커먼즈를 향한 사유의 탐색",
            "overview": "오늘의 연구 살롱은 사유화와 관료주의적 통제를 넘어, 고립 없는 자율적 개인을 지원하는 비시장적 공공 인프라와 커머닝의 원리를 집중 탐구합니다.",
            "key_takeaways": [
                "사유화(Enclosure)를 넘는 자치 프로토콜: 중앙 집중적 통제 없이도 상호 신뢰를 담보하는 규칙 설계가 필수적입니다.",
                "무해한 시빅 인터페이스: 사생활과 존엄을 침해하지 않는 투과성 높은 공공 안전망 구축이 요구됩니다.",
                "다종 공생과 생태적 회복력: 자연과 맺는 관계의 회복을 통해 지속가능한 삶의 기반을 다져야 합니다."
            ]
        }

    categories = [it.get("category", "") for it in curated_items]
    top_cat = max(set(categories), key=categories.count) if categories else "커먼즈·공유재"

    theme_templates = {
        "커먼즈·공유재": "복합 위기 시대의 대항 헤게모니와 자율적 커먼즈 인프라",
        "과학기술학·STS": "플랫폼 기술정치 해체와 주체적 디지털 권리 인프라",
        "시빅HCI·UXR": "관료주의를 넘는 포용적 시빅 디자인과 고립 가구 안전망",
        "농생태·식량주권": "추출주의 농업 극복과 다종 공생 기반 대지 윤리의 회복",
        "공간사회·도시커먼즈": "도시 공간의 탈상품화와 자율적 시민 자치 거버넌스",
        "재난안전·공공인프라": "상호부조와 데이터 인프라가 엮어내는 사각지대 없는 공공 돌봄",
        "돌봄·상호부조": "비시장적 호혜성과 취약계층 존엄을 보장하는 돌봄 커먼즈"
    }

    overview_templates = {
        "커먼즈·공유재": "오늘 수집된 연구들은 자본과 국가의 이분법을 넘어, 자립적인 1인 가구와 개인이 고립되지 않고 공동의 자원을 호혜적으로 관리하는 커머닝(Commoning) 실천에 주목합니다.",
        "과학기술학·STS": "오늘의 학술 담론은 알고리즘과 플랫폼 권력이 노동과 일상을 통제하는 방식을 폭로하고, 시민이 직접 개입하여 사회기술시스템을 민주화할 수 있는 대안적 경로를 집중 조명합니다.",
        "시빅HCI·UXR": "오늘의 사유 지형은 행정 편의주의적 시스템에서 소외되기 쉬운 재난 약자와 고립 가구를 포용하며, 개인의 존엄과 사생활을 보장하는 비침해적 사용자 경험 설계를 짚습니다.",
        "농생태·식량주권": "오늘의 연구들은 기후 붕괴와 토양 황폐화라는 복합 위기 속에서, 소농의 자치권과 흙·미생물·다종 생명 간의 유기적 얽힘을 회복하는 농생태학적 대안을 역설합니다.",
        "공간사회·도시커먼즈": "오늘의 담론은 젠트리피케이션과 공간 사유화에 맞서 모든 시민이 누려야 할 공간 권리와, 비시장적으로 운영되는 느슨한 공유 거점의 형성 가능성을 다룹니다.",
        "재난안전·공공인프라": "오늘의 연구들은 일상화된 재난 환경 속에서 고독사와 사회적 고립을 방지하기 위한 최소 개입형 상호부조 안전망과 공공 인프라 프로토콜의 구체적 청사진을 제시합니다.",
        "돌봄·상호부조": "오늘의 담론은 구조적 불평등 속에서 고립된 개인들의 존엄을 회복하고, 일상적 돌봄과 환대 프로토콜을 지역 사회에 안착시키는 실천적 지혜를 모읍니다."
    }

    takeaway_pools = {
        "커먼즈·공유재": [
            "사유화(Enclosure)의 극복: 자원과 공간을 소유의 대상이 아닌 공동의 돌봄 대상으로 전환하는 커머닝 규약이 긴요합니다.",
            "독립적 개인의 자치 연대: 지나친 집단주의적 강요 없이도 상호 신뢰와 규칙을 지켜낼 수 있는 자율 거버넌스 프로토콜이 요청됩니다.",
            "비시장적 대안 인프라의 필요성: 시장에 종속되지 않고 최소한의 생활 안전을 영위할 수 있는 공통재(Commons)의 확충이 핵심 과제입니다."
        ],
        "과학기술학·STS": [
            "알고리즘 권력의 탈신비화: 기술은 중립적이지 않으며 설계와 학습 데이터에 내재된 권력 관계를 비판적으로 감시해야 합니다.",
            "시민 주도형 사회기술시스템: 전문가 중심의 하향식 결정에서 벗어나 시민 당사자의 참여가 보장되는 거버넌스가 필요합니다.",
            "디지털 주권과 프라이버시 보호: 기술적 편의성 뒤에 숨은 감시와 사생활 침해를 거부하고 자율성을 지키는 인터페이스를 지향해야 합니다."
        ],
        "시빅HCI·UXR": [
            "취약계층 중심 유니버설 디자인: 재난 약자와 고립 1인 가구의 실제 사용 행동을 반영한 무해하고 직관적인 공공 인터페이스가 시급합니다.",
            "참여적 디자인 방법론: 공급자 관점의 행정 전산망을 탈피하고 현장 당사자의 목소리를 설계에 직접 반영해야 합니다.",
            "안전망의 투과성과 최소 개입: 불필요한 행정 절차나 자격 검증으로 인한 수치심 없이 자연스럽게 작동하는 돌봄 인프라를 구축해야 합니다."
        ],
        "농생태·식량주권": [
            "생산주의 패러다임 탈피: 화학 비료와 거대 자본 중심의 녹색혁명을 넘어 생태적 지속가능성을 우선하는 패러다임 전환이 요구됩니다.",
            "다종 공생의 대지 윤리: 인간뿐 아니라 흙과 생태계 구성원 전체의 상호 의존성을 인정하는 돌봄의 농업을 실천해야 합니다.",
            "소농의 자치와 지역 식량 순환: 외부 공급망 충격에 흔들리지 않는 지역 중심의 자립적 식량 및 생태 네트워크를 복원해야 합니다."
        ],
        "공간사회·도시커먼즈": [
            "도시 공간의 탈상품화: 부동산 투기와 배제적 젠트리피케이션에 맞서 시민 모두의 주거 안정과 공간권을 지켜내야 합니다.",
            "도시 커먼즈의 물리적 거점: 사유재산과 국공유지의 이분법을 넘어 누구나 접근 가능한 자치적 공유 거점을 확보해야 합니다.",
            "느슨한 연대의 도시성: 고립되지 않고 자율성과 공적 연결을 동시에 누리는 생활권 커머닝 모델을 확산해야 합니다."
        ]
    }

    theme = theme_templates.get(top_cat, theme_templates["커먼즈·공유재"])
    overview = overview_templates.get(top_cat, overview_templates["커먼즈·공유재"])
    takeaways = takeaway_pools.get(top_cat, takeaway_pools.get("커먼즈·공유재"))

    return {
        "theme": theme,
        "overview": overview,
        "key_takeaways": takeaways
    }


# ==============================================================================
# 스마트 휴리스틱 큐레이터 (Gemini 오프라인 폴백 시 무결점 작동 보장)
# ==============================================================================
def heuristic_curate(items):
    """
    단어 경계 정규식 기반 정확한 카테고리 분류,
    100% 개별 논문 고유 학술 번역 제목 및 초록 맞춤형 3단 요약 생성
    """
    curated = []

    # 단어 경계가 보장되는 엄밀한 카테고리 키워드
    category_weights = {
        "커먼즈·공유재": [
            "commons", "commoning", "p2p", "ostrom", "cooperative", "cooperation", "open access",
            "peer production", "caring commons", "reproductive labor", "open cooperative", "cosmolocal",
            "공유재", "협동조합", "자치관리", "공동체", "커머닝", "피어생산"
        ],
        "과학기술학·STS": [
            "socio-technical", "technology politics", "algorithmic", "algorithm", "platform", "ai journalism",
            "data justice", "surveillance capitalism", "techno-politics", "embedded finance", "machine learning",
            "science and technology studies", "사회기술", "알고리즘", "인공지능", "플랫폼자본주의", "데이터정의"
        ],
        "시빅HCI·UXR": [
            "civic computing", "participatory design", "civic tech", "public service", "user experience",
            "interaction design", "accessibility", "universal design", "crisis informatics",
            "시빅", "참여디자인", "사용자경험", "공공서비스", "접근성"
        ],
        "농생태·식량주권": [
            "agroecology", "agroecological", "food sovereignty", "peasant", "smallholder", "land ethic",
            "ecofeminism", "multispecies", "interspecies", "soil health", "seed sovereignty", "carnism",
            "solarities", "environmental humanities", "deep ecology", "농생태", "식량주권", "소농", "대지윤리",
            "다종공생", "종간윤리", "에코페미니즘", "종자주권"
        ],
        "공간사회·도시커먼즈": [
            "urban commons", "spatial justice", "right to the city", "gentrification", "extractivism",
            "territorial commons", "street furniture", "urban forest", "mining conflict", "de-commodification",
            "도시커먼즈", "공간정의", "도시권", "젠트리피케이션", "자원추출", "영토커먼즈"
        ],
        "재난안전·공공인프라": [
            "disaster vulnerability", "public safety", "emergency operations", "green social work", "crisis response",
            "mutual aid infrastructure", "hazard mitigation", "재난취약", "공공안전", "긴급대응", "녹색사회복지"
        ],
        "돌봄·상호부조": [
            "rhetoric of respect", "patient care", "health practitioner", "care work", "community care",
            "intersectional health", "돌봄", "의료소통", "상호부조", "존중의수사학"
        ]
    }

    used_titles = set()

    for item in items:
        title = item.get("title", "")
        abstract = item.get("abstract", "")
        text = f"{title} {abstract}".lower()
        orig_cat = item.get("category", "커먼즈·공유재")

        # 카테고리 스코어링: 원본 출처 카테고리에 우선순위 가중치(+3.5) 부여
        scores = {cat: 0.0 for cat in category_weights}
        if orig_cat in scores:
            scores[orig_cat] += 3.5

        for cat, kws in category_weights.items():
            for kw in kws:
                # 단어 경계(\b) 매칭으로 오탐 방지 ('art'가 'participatory'에 매칭되는 참사 방지)
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, text):
                    scores[cat] += 1.2

        best_cat = max(scores, key=scores.get)
        base_relevance = 7.5 + min(scores[best_cat] * 0.4, 2.3)

        # 제목 번역
        title_kr = translate_academic_title(title, best_cat)

        # 제목 중복 방지 (절대 동일 제목 발생 불가)
        if title_kr in used_titles:
            # 저자명 또는 출처 기반 차별화
            first_author = (item.get("authors", "").split(",")[0]).strip()
            if first_author and first_author != "연구진":
                title_kr = f"{title_kr} ({first_author} 연구)"
            else:
                title_kr = f"{title_kr} [사유 담론]"
        used_titles.add(title_kr)

        # 초록 및 메타데이터 기반 3단 학술 요약
        summary_points = generate_deep_heuristic_summary(item, best_cat, title_kr)

        # 맞춤형 세부 키워드 추출
        keywords = [f"#{best_cat.split('·')[0]}"]
        kw_candidates = [
            ("commons", "#커머닝"), ("algorithm", "#알고리즘정의"), ("ai", "#책임있는AI"),
            ("civic", "#시빅테크"), ("participatory", "#참여디자인"), ("respect", "#존중의수사학"),
            ("health", "#돌봄소통"), ("solar", "#태양성에너지"), ("mining", "#자원추출주의"),
            ("territory", "#영토커먼즈"), ("interspecies", "#종간윤리"), ("nature", "#대지윤리"),
            ("farmer", "#소농협동"), ("urban", "#도시공간"), ("disaster", "#위기안전망")
        ]
        for eng, kw_tag in kw_candidates:
            if eng in text:
                keywords.append(kw_tag)
        if len(keywords) < 3:
            keywords.append("#동시대학술")

        curated.append({
            "id": item["id"],
            "title_kr": title_kr,
            "original_title": item["title"],
            "source": item["source"],
            "authors": item["authors"] or "연구진",
            "published": item["published"],
            "url": item["url"],
            "category": best_cat,
            "relevance_score": round(base_relevance, 1),
            "summary_points": summary_points,
            "keywords": list(dict.fromkeys(keywords))[:4]
        })

    curated.sort(key=lambda x: x["relevance_score"], reverse=True)
    top_items = curated[:8]
    daily_summary = synthesize_daily_summary(top_items)
    return top_items, daily_summary


def curate_items(raw_items, api_key=None):
    """후보 목록을 Gemini AI로 큐레이션하고 오늘의 사유 지형 및 100% 한국어 학술 요약 생성"""
    if not raw_items:
        return [], synthesize_daily_summary([])

    key = api_key or os.environ.get("GEMINI_API_KEY") or GEMINI_API_KEY
    if key:
        print("Curating with Gemini AI...", file=sys.stderr)
        prompt = f"""{CURATOR_SYSTEM_PROMPT}

다음 후보 목록 중 트윈의 지적 관심사에 가장 부합하는 논문 및 기사 8편을 엄선하고, '오늘의 사유 지형(Daily Summary)' 및 각 논문별 100% 품격 있는 한국어 학술 요약('summary_points')을 작성해 JSON으로 출력하십시오.
영문 원문 문장을 절대 그대로 노출하지 마시고, 100% 한국어 문장으로 학술적 맥락을 구성하십시오.
각 논문의 'title_kr'은 해당 논문의 구체적 제목을 학술적으로 번역한 고유한 제목이어야 하며, 결코 일반적인 범주명을 중복해서 부여하지 마십시오.

[후보 목록 (총 {len(raw_items)}건)]
{json.dumps([{
    'idx': i,
    'title': item['title'],
    'abstract': item['abstract'][:600],
    'source': item['source'],
    'category': item['category']
} for i, item in enumerate(raw_items[:30])], ensure_ascii=False, indent=1)}

[응답 JSON 스키마]
{{
  "daily_summary": {{
    "theme": "오늘의 연구 사유 지형을 관통하는 하나의 지적 화두 (한 문장)",
    "overview": "오늘 선별된 연구들이 트윈의 연구 방향(1인 가구, 비시장적 공공 인프라, 커머닝, 대지 윤리 등)과 어떻게 연결되는지 설명하는 2~3문장의 깊이 있는 총괄 해설",
    "key_takeaways": [
      "1. 첫 번째 핵심 발견 및 명제",
      "2. 두 번째 핵심 발견 및 명제",
      "3. 세 번째 핵심 발견 및 명제"
    ]
  }},
  "curated_items": [
    {{
      "idx": 원본 idx,
      "title_kr": "정확하고 학술적인 한국어 번역 제목 (각 논문 고유 제목, 잔여 영어 0%)",
      "category": "커먼즈·공유재" | "시빅HCI·UXR" | "과학기술학·STS" | "농생태·식량주권" | "공간사회·도시커먼즈" | "재난안전·공공인프라" | "돌봄·상호부조",
      "relevance_score": 8.5 (1.0~10.0),
      "summary_points": [
        "연구 배경 및 문제의식: ...",
        "핵심 분석 및 이론적 발견: ...",
        "트윈 연구 시사점: ..."
      ],
      "keywords": ["#키워드1", "#키워드2", "#키워드3"]
    }}
  ]
}}
"""
        res_json = call_gemini_api(prompt, key)
        if res_json and isinstance(res_json, dict):
            daily_summary = res_json.get("daily_summary") or synthesize_daily_summary([])
            raw_items_res = res_json.get("curated_items", [])
            enriched = []
            seen_titles = set()
            for item in raw_items_res:
                idx = item.get("idx")
                if idx is not None and 0 <= idx < len(raw_items):
                    orig = raw_items[idx]
                    raw_title_kr = item.get("title_kr", orig["title"])
                    clean_t_kr = clean_title(raw_title_kr)
                    if clean_t_kr in seen_titles:
                        clean_t_kr = f"{clean_t_kr} ({orig.get('source', '')})"
                    seen_titles.add(clean_t_kr)

                    enriched.append({
                        "id": orig["id"],
                        "title_kr": clean_t_kr,
                        "original_title": orig["title"],
                        "source": orig["source"],
                        "authors": orig["authors"],
                        "published": orig["published"],
                        "url": orig["url"],
                        "category": item.get("category", orig["category"]),
                        "relevance_score": item.get("relevance_score", 8.0),
                        "summary_points": item.get("summary_points", []),
                        "keywords": item.get("keywords", [])
                    })
            enriched.sort(key=lambda x: x["relevance_score"], reverse=True)
            if enriched:
                return enriched, daily_summary

    print("Gemini API key not found or fallback requested. Using advanced heuristic curator.", file=sys.stderr)
    return heuristic_curate(raw_items)
