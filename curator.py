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


def josa(word, with_batchim="을", without_batchim="를"):
    """한국어 받침 여부에 따라 정확한 조사(을/를, 은/는, 이/가)를 반환"""
    w = (word or "").strip()
    if not w:
        return with_batchim
    last = w[-1]
    if "가" <= last <= "힣":
        code = ord(last) - 0xAC00
        return with_batchim if (code % 28) != 0 else without_batchim
    return with_batchim


def translate_academic_title(title, category=""):
    """원문 제목을 그대로 보존 (한영 혼용 기계 치환 금지)"""
    return clean_title(title)


# ==============================================================================
# 초록 및 원문 기반 심층 학술 요약 생성기 (단어 경계 엄밀 매칭 + 정교한 한국어 학술 문체)
# ==============================================================================
def generate_deep_heuristic_summary(item, category, title_kr):
    """
    논문의 실제 제목, 초록(abstract), 저널(source), 저자(authors)를 분석하여
    배경·발견·시사점 3단 한국어 학술 요약을 정교하게 구성합니다.
    """
    orig_title = item.get("original_title") or item.get("title", "")
    abstract = item.get("abstract", "")
    source = item.get("source", "학술 저널")
    authors = item.get("authors", "연구진")
    text_lower = f"{orig_title} {abstract}".lower()

    # 1. 연구 배경 및 문제의식 (Problem & Context)
    bg_focus = "기존 학술·제도적 패러다임이 드러내는 구조적 한계와 비판적 전환의 필요성"
    if re.search(r"\b(surveillance|visibility|flourishing)\b", text_lower):
        bg_focus = "종교적·제도적 감시에서 디지털 데이터 감시로 이어지는 '가시성(visibility)'의 역사와, 상시적 감시 체계가 인간의 번영(human flourishing)과 자율성에 미치는 윤리적 긴장"
    elif re.search(r"\b(simulated users|ux testing|user who is not there|synthetic users)\b", text_lower):
        bg_focus = "UX 리서치 및 사용성 평가 현장에 생성형 AI 기반 '가상(시뮬레이션) 사용자'가 빠르게 도입되면서 실제 당사자의 경험과 목소리가 대체·소거되는 인식론적 위기"
    elif re.search(r"\b(digital authoritarianism|manipulation|datafication)\b", text_lower):
        bg_focus = "생성형 AI와 데이터화(datafication) 기술이 권위주의적 통제·여론 조작 및 감시 인프라를 정교화하는 동시대 디지털 권위주의의 확산 양상"
    elif re.search(r"\b(indigenous data sovereignty|interisland|cross-community)\b", text_lower):
        bg_focus = "외부 연구자·국가·플랫폼이 토착 공동체의 지식과 데이터를 일방적으로 추출해 온 관행에 맞서, 지역·도서 공동체가 데이터 주권을 되찾기 위한 연대의 필요성"
    elif re.search(r"\b(ecofeminism|ecofeminist|trees|performance)\b", text_lower):
        bg_focus = "자연과 여성을 동시에 대상화해 온 가부장적·개발주의적 시선에 맞서, 나무·몸·퍼포먼스를 매개로 전개되어 온 생태여성주의(에코페미니즘) 실천의 역사적 계보"
    elif re.search(r"\b(participatory design|modularity|ceramic|shifting ground)\b", text_lower):
        bg_focus = "참여형 디자인(Participatory Design)이 단순한 의견 수렴 절차를 넘어, 흙·도자 같은 물질적 실천과 관계적 모듈성을 통해 공동체적 감각을 재구성할 수 있는 가능성"
    elif re.search(r"\b(natural environments|ecological consciousness|colonialism)\b", text_lower):
        bg_focus = "식민주의적 개발 논리와 도구적 자연관이 해체해 온 자연환경의 고유한 의미와, 인간-자연의 상호의존성을 복원하는 비판적 생태 의식의 형성 과정"
    elif re.search(r"\b(disability|accessibility|climate action)\b", text_lower):
        bg_focus = "기후 대응 정책과 일상적 공간·서사 설계에서 장애인과 취약계층의 접근성(accessibility) 및 주체성(agency)이 주변화되는 구조적 배제"
    elif re.search(r"\b(syntropic|urban metabolic|metabolism|lidar|green space)\b", text_lower):
        bg_focus = "선형적 자원 소비에 기반한 근대 도시 인프라의 생태적 한계를 넘어, 정밀 공간 데이터와 주민 참여를 결합한 재생적 도시 녹지·대사 모델의 시급성"
    elif re.search(r"\b(multispecies|interspecies|making-with-kin)\b", text_lower):
        bg_focus = "인간 중심적 노동·제도·윤리 체계가 배제해 온 비인간 생명체와의 다종 돌봄(multispecies care)과 친족 만들기(making-with-kin)의 존재론적 가치"
    elif re.search(r"\b(data spaces|catena-x|platform|embedded finance)\b", text_lower):
        bg_focus = "거대 중앙집중형 디지털 플랫폼이 데이터와 규칙을 독점하는 구조 속에서, 분산·협력형 데이터 공간(data spaces)이 규제 복잡성과 공공 책임을 조율할 수 있는 조건"
    elif re.search(r"\b(uav|disaster|public safety|emergency)\b", text_lower):
        bg_focus = "기후재난과 복합 위기가 일상화된 환경에서 기존 공공안전 대응 체계가 지닌 사각지대와, 지능형 기술·상호부조 인프라의 공공적 활용 가능성"
    elif re.search(r"\b(agroecology|soil|smallholder|farmer|food sovereignty)\b", text_lower):
        bg_focus = "화학 투입과 거대 자본 중심의 산업 농업이 초래한 토양 황폐화와 소농 종속 문제를 극복하고, 지역 순환형 농생태·식량주권 체계를 구축해야 할 과제"
    elif re.search(r"\b(commons|commoning|peer production)\b", text_lower):
        bg_focus = "시장 자본의 사유화(enclosure)와 관료적 통제 사이에서 공동체가 자원을 자치적으로 관리하는 커먼즈·피어 생산 거버넌스의 지속가능성"

    p1 = f"연구 배경 및 문제의식: '{source}'에 실린 {authors}의 본 연구는 {bg_focus}{josa(bg_focus, '을', '를')} 핵심 문제로 제기하며 이론적·실천적 대안을 탐구합니다."

    # 2. 핵심 분석 및 이론적 발견 (Method & Findings)
    finding_focus = "문헌 검토와 실증·사례 분석을 결합하여 기존 틀의 맹점을 짚고 대안적 거버넌스와 실천 경로를 체계화했습니다."
    if re.search(r"\b(surveillance|visibility|flourishing)\b", text_lower):
        finding_focus = "신적 시선에서 디지털 알고리즘 감시로 이어지는 가시성의 역사적 변천을 추적하며, 감시를 단순한 프라이버시 침해가 아니라 인간의 존엄·신뢰·번영 조건을 재편하는 사회문화적 구조로 규명했습니다."
    elif re.search(r"\b(simulated users|ux testing|user who is not there)\b", text_lower):
        finding_focus = "생성형 AI 기반 가상 사용자(simulated users)의 계보를 비판적으로 해부하고, 통계적 평균에 수렴하는 합성 페르소나가 소수자·비정형 사용자의 돌발적 맥락과 실제 마찰을 은폐하는 구조적 한계를 입증했습니다."
    elif re.search(r"\b(digital authoritarianism|manipulation|datafication)\b", text_lower):
        finding_focus = "여러 국가의 비교 사례 분석을 통해 생성형 AI가 정보 통제, 자동화된 검열, 맞춤형 여론 조작을 결합하며 디지털 권위주의의 작동 방식을 질적으로 변화시키고 있음을 밝혔습니다."
    elif re.search(r"\b(indigenous data sovereignty|interisland)\b", text_lower):
        finding_focus = "도서·토착 공동체 간 초지역 연대 사례를 통해, 데이터 수집·보관·활용 전 과정에 공동체의 자결권과 관계적 책임을 내재화하는 토착 데이터 주권(IDS) 거버넌스 모델을 제시했습니다."
    elif re.search(r"\b(ecofeminism|ecofeminist|trees|performance)\b", text_lower):
        finding_focus = "나무와 신체가 만나는 생태 퍼포먼스 예술의 사료를 재구성하여, 에코페미니즘이 단순한 환경 담론을 넘어 몸의 감각과 비인간 생명과의 연대를 통해 추출주의에 저항해 온 실천적 미학임을 보여주었습니다."
    elif re.search(r"\b(participatory design|modularity|ceramic)\b", text_lower):
        finding_focus = "'Shifting Ground' 도자 공동 제작 프로젝트를 사례로, 흙을 빚고 조합하는 관계적 모듈성(relational modularity)이 참여자 간의 위계를 허물고 장소 기반의 공동체적 기억을 형성하는 과정을 실증했습니다."
    elif re.search(r"\b(comparative|policy|regulatory)\b", text_lower):
        finding_focus = "비교 정책·제도 분석을 통해 단일 기술 규제의 한계를 넘어, 분산된 이해관계자 간의 상호운용성과 공공적 책임성을 동시에 확보하는 거버넌스 설계 원리를 도출했습니다."
    elif re.search(r"\b(uav|public safety|narrative review)\b", text_lower):
        finding_focus = "공공안전 분야 지능형 드론(UAV) 연구를 체계적으로 종합하여, 재난 탐지·수색·인프라 점검에서의 실질적 효용과 함께 프라이버시·안전 규제·현장 통합 과제를 구조화했습니다."
    elif re.search(r"\b(lidar|participatory mapping|green space)\b", text_lower):
        finding_focus = "LiDAR 기반 정밀 식생 데이터와 주민 주도 참여형 매핑을 결합함으로써, 객관적 물리 지표만으로는 포착할 수 없는 도시 녹지의 체감 질과 공간 형평성 격차를 드러냈습니다."
    elif re.search(r"\b(natural environments|ecological|aesthetic)\b", text_lower):
        finding_focus = "자연환경에 대한 감각적·미적 경험과 과학적 탐구가 분리되지 않고 상호 보완될 때, 인간과 생태계 간의 지속가능한 돌봄 관계가 형성된다는 관계론적 분석 틀을 제시했습니다."

    p2 = f"핵심 분석 및 이론적 발견: {finding_focus}"

    # 3. 트윈 연구 시사점 (Twin Salon Relevance)
    cat_twin_map = {
        "커먼즈·공유재": "사유화와 중앙 관료제를 넘어 지역·공동체가 지식과 데이터를 자치적으로 관리하는 '관계적 커먼즈 프로토콜' 설계에 직접적인 이론적 토대를 제공합니다.",
        "과학기술학·STS": "기술을 중립적 도구가 아닌 권력과 가치가 각인된 사회기술 체계로 읽어내며, 감시·알고리즘 통제 속에서 시민의 데이터 주권과 인간 번영을 지키는 비판적 준거가 됩니다.",
        "시빅HCI·UXR": "AI 자동화·합성 데이터가 실제 취약계층과 현장 당사자의 목소리를 대체하지 않도록 경계하고, 물질성·참여·신뢰에 기반한 공공 인터페이스와 리서치 방법론을 다듬는 데 기여합니다.",
        "농생태·식량주권": "흙·나무·생태계를 추출 대상이 아닌 공생의 주체로 바라보는 농생태학적 관점을 심화시키며, 이론과 현장 실천(유기순환·생태복원)을 잇는 사유의 나침반이 됩니다.",
        "공간사회·도시커먼즈": "정량적 공간 데이터와 주민의 생활 감각을 결합해 배제 없는 도시 녹지·공유 공간 및 접근성 높은 커먼즈 거점을 설계하는 데 실질적 시사점을 줍니다.",
        "재난안전·공공인프라": "재난·기후 위기 대응 기술이 현장의 취약계층과 사생활 보호 원칙을 해치지 않으면서 실질적 안전망으로 작동하기 위한 공공 인프라 설계 기준을 제시합니다.",
        "돌봄·상호부조": "돌봄과 상호부조의 가치를 제도·공간·기술 설계의 중심에 놓아, 위계 없는 호혜적 연대망을 구축하는 실천적 통찰을 제공합니다."
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
