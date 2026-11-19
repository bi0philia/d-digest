"""
고요한 연구 살롱 · 연구자 인덱스 엔진 (Researcher & Guru Engine)
- 학계에서 핫한(Trending/Rising) 동시대 연구자 실시간 자동 추출 & 갱신
- 올타임 레전드(All-time Legends) 불멸의 사상가 아카이브 관리
"""
import json
import os
import re
from datetime import datetime
from collections import Counter, defaultdict

# 파일 경로
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Fallback to web/data if run from project root
WEB_DATA_DIR = os.path.join(CURRENT_DIR, "web", "data") if os.path.exists(os.path.join(CURRENT_DIR, "web")) else CURRENT_DIR
GURUS_FILE = os.path.join(WEB_DATA_DIR, "gurus.json")

# 🏛️ 올타임 레전드 (All-time Legends) 마스터 데이터
ALL_TIME_LEGENDS = [
    {
        "id": "elinor-ostrom",
        "name_kr": "엘리너 오스트롬",
        "name_en": "Elinor Ostrom",
        "field": "커먼즈 자치 거버넌스·제도 분석",
        "category": "커먼즈·공유재",
        "affiliation": "인디애나 대학교 정치학 석좌교수 / 2009 노벨 경제학상 수상",
        "tier": "legend",
        "badge": "🏛️ 올타임 레전드",
        "avatar": "🏆",
        "core_philosophy": "'공유재의 비극'은 불가피한 운명이 아니다. 국가의 강제나 시장의 사유화 없이도, 자원을 직접 이용하는 당사자 공동체가 스스로 명확한 경계, 참여적 규칙 개정, 점진적 제재 등 '커먼즈 8대 원칙'을 수립할 때 자원은 수백 년간 지속가능하게 유지된다.",
        "key_concepts": ["커먼즈 8대 원칙", "다중심 거버넌스(Polycentricity)", "공동 풀 자원(CPR)", "사회생태시스템(SES)", "제도 분석 개발(IAD)"],
        "key_works": ["『공유의 비극을 넘어(Governing the Commons)』 (1990)", "『제도적 다양성의 이해(Understanding Institutional Diversity)』 (2005)"],
        "representative_work": "『공유의 비극을 넘어(Governing the Commons)』",
        "recent_activities": "오스트롬 워크숍(Ostrom Workshop)을 통해 전 세계 다중심 기후 거버넌스 및 디지털 커먼즈 연구에 불멸의 이론적 기틀 제공.",
        "links": [
            {"title": "Ostrom Workshop", "url": "https://ostromworkshop.indiana.edu/"},
            {"title": "노벨상 공식 사이트", "url": "https://www.nobelprize.org/prizes/economic-sciences/2009/ostrom/facts/"}
        ]
    },
    {
        "id": "david-harvey",
        "name_kr": "데이비드 하비",
        "name_en": "David Harvey",
        "field": "마르크스주의 지리학·도시공간론",
        "category": "공간사회·도시커먼즈",
        "affiliation": "뉴욕시립대학교(CUNY) 대학원 인류학·지리학 특훈교수",
        "tier": "legend",
        "badge": "🏛️ 올타임 레전드",
        "avatar": "🏙️",
        "core_philosophy": "자본주의는 주기적 위기를 넘기기 위해 도시 공간을 금융화하고 부동산 투기를 통해 잉여 자본을 흡수하는 '공간적 조정(Spatial Fix)'을 감행한다. 이 과정에서 공공 인프라와 주거가 박탈당하므로, 시민은 도시를 집단적으로 재창조할 '도시권(Right to the City)'을 쟁취해야 한다.",
        "key_concepts": ["도시권(Right to the City)", "수탈에 의한 축적", "공간적 조정(Spatial Fix)", "반란의 도시", "도시 커먼즈의 정치학"],
        "key_works": ["『반란의 도시(Rebel Cities)』 (2012)", "『포스트모더니티의 조건』 (1989)", "『신자유주의 간략한 역사』 (2005)", "『자본의 한계』 (1982)"],
        "representative_work": "『반란의 도시(Rebel Cities)』",
        "recent_activities": "팟캐스트 'The Anti-Capitalist Chronicles' 운영, 도시 커먼즈의 탈상품화와 신자유주의 도시 공간 수탈 비판 강연 지속.",
        "links": [
            {"title": "공식 웹사이트", "url": "http://davidharvey.org/"},
            {"title": "CUNY 교수진 소개", "url": "https://www.gc.cuny.edu/people/david-harvey"}
        ]
    },
    {
        "id": "donna-haraway",
        "name_kr": "도나 해러웨이",
        "name_en": "Donna Haraway",
        "field": "에코페미니즘·과학기술학·다종공생",
        "category": "농생태·식량주권",
        "affiliation": "캘리포니아 대학교 산타크루즈(UCSC) 의식사학과 명예교수",
        "tier": "legend",
        "badge": "🏛️ 올타임 레전드",
        "avatar": "🐙",
        "core_philosophy": "인간 중심주의와 이분법적 자연관을 거부하고, 생명과 비생명, 인간과 비인간, 기계와 유기체가 상호 침투하는 '반려종(Companion Species)'과 '얽힘의 존재론'을 주창한다. 인간세(Anthropocene)를 넘어 복합적 위기 속에서 '트러블과 함께 머물며(Staying with the Trouble)' 친족을 만들어야 한다.",
        "key_concepts": ["사이보그 선언", "상황적 지식(Situated Knowledges)", "반려종(Companion Species)", "트러블과 함께 머물기", "툴루세(Chthulucene)"],
        "key_works": ["『트러블과 함께 머물기(Staying with the Trouble)』 (2016)", "『사이보그 선언(A Cyborg Manifesto)』 (1985)", "『반려종 선언』 (2003)"],
        "representative_work": "『트러블과 함께 머물기(Staying with the Trouble)』",
        "recent_activities": "인류세 생태 예술가들과 협업, 다종 공생 스토리텔링 및 공생적(Sympoietic) 생태윤리 강연 활발.",
        "links": [
            {"title": "UCSC 교수 페이지", "url": "https://historyofconsciousness.ucsc.edu/faculty/index.php?uid=haraway"}
        ]
    },
    {
        "id": "henri-lefebvre",
        "name_kr": "앙리 르페브르",
        "name_en": "Henri Lefebvre",
        "field": "공간사회학·도시권·일상생활 비판",
        "category": "공간사회·도시커먼즈",
        "affiliation": "스트라스부르 대학교·낭테르 대학교 교수 (프랑스 철학자)",
        "tier": "legend",
        "badge": "🏛️ 올타임 레전드",
        "avatar": "🗺️",
        "core_philosophy": "공간은 단순한 물리적 용기가 아니라 사회적 관계가 투영되고 재생산되는 '사회적 생산물'이다. 자본에 의해 교환가치로 환원된 도시 공간을 일상생활의 '사용가치'로 탈환해야 하며, 소외된 모든 시민은 도시 공간을 전유하고 형성할 권리인 '도시권(Le droit à la ville)'을 갖는다.",
        "key_concepts": ["공간의 생산(The Production of Space)", "도시권(Le droit à la ville)", "공간적 삼원성(지각·구상·체현)", "일상생활의 비판", "리듬분석"],
        "key_works": ["『공간의 생산(The Production of Space)』 (1974)", "『도시로의 권리(Le Droit à la ville)』 (1968)", "『일상생활의 비판』 (1947~1981)"],
        "representative_work": "『공간의 생산(The Production of Space)』",
        "recent_activities": "동시대 도시 커먼즈 운동 및 급진 지리학의 영구적 사유 원천으로 계승.",
        "links": [
            {"title": "스탠포드 철학 백과사전", "url": "https://plato.stanford.edu/entries/lefebvre/"}
        ]
    },
    {
        "id": "bruno-latour",
        "name_kr": "브뤼노 라투르",
        "name_en": "Bruno Latour",
        "field": "과학기술학(STS)·행위자연결망이론",
        "category": "과학기술학·STS",
        "affiliation": "파리 정치대학(Sciences Po) 명예교수",
        "tier": "legend",
        "badge": "🏛️ 올타임 레전드",
        "avatar": "🌐",
        "core_philosophy": "자연과 사회, 인간과 비인간의 이분법을 해체하고 모든 사물, 미생물, 기후, 제도가 동등하게 행위성(Agency)을 지닌 행위자-연결망(Actor-Network Theory)을 형성한다고 본다. 신자유주의적 세계화의 환상을 벗어나 우리가 발 딛고 있는 구체적인 가이아(Gaia) 지구로 '착지(Down to Earth)'해야 한다.",
        "key_concepts": ["행위자-연결망 이론(ANT)", "우리는 결코 근대인이었던 적이 없다", "비인간 행위자(Actant)", "지구에 착지하기(Down to Earth)", "사물의 국회"],
        "key_works": ["『우리는 결코 근대인이었던 적이 없다』 (1991)", "『지구와 착지(Down to Earth)』 (2017)", "『실험실 생활』 (1979)"],
        "representative_work": "『우리는 결코 근대인이었던 적이 없다』",
        "recent_activities": "기후 변동 시대 정치생태학의 새로운 문법 제시 및 사물 국회 전시 프로젝트 총괄.",
        "links": [
            {"title": "Bruno Latour 공식 사이트", "url": "http://www.bruno-latour.fr/"}
        ]
    },
    {
        "id": "silvia-federici",
        "name_kr": "실비아 페데리치",
        "name_en": "Silvia Federici",
        "field": "페미니즘·돌봄 커먼즈·재생산 노동",
        "category": "돌봄·상호부조",
        "affiliation": "호프스트라 대학교(Hofstra University) 명예교수",
        "tier": "legend",
        "badge": "🏛️ 올타임 레전드",
        "avatar": "🫂",
        "core_philosophy": "자본주의적 원시 축적은 여성의 가사·돌봄(재생산) 노동을 비가시화하고 자연을 인클로저하는 과정이었다. 따라서 진정한 커머닝은 거실과 부엌, 돌봄과 살림의 영역을 재전유하고 집단화하는 데서 출발해야 한다.",
        "key_concepts": ["재생산 노동의 가치화", "가사의 공동체화", "신체와 대지의 커먼즈", "마녀사냥과 원시축적"],
        "key_works": ["『캘리번과 마녀(Caliban and the Witch)』 (2004)", "『혁명의 영점(Revolution at Point Zero)』 (2012)", "『세계를 재마법화하기』 (2018)"],
        "representative_work": "『캘리번과 마녀(Caliban and the Witch)』",
        "recent_activities": "글로벌 여성·소농 연대 운동 참여, 라틴아메리카 토착민 여성들의 공동체 방어 투쟁 기록 및 글로벌 에코페미니즘 강연.",
        "links": [
            {"title": "위키피디아", "url": "https://en.wikipedia.org/wiki/Silvia_Federici"},
            {"title": "PM Press 저자 페이지", "url": "https://pmpress.org/index.php?l=product_list&c=137"}
        ]
    },
    {
        "id": "arturo-escobar",
        "name_kr": "아르투로 에스코바르",
        "name_en": "Arturo Escobar",
        "field": "정치생태학·다원우주 디자인·탈개발",
        "category": "농생태·식량주권",
        "affiliation": "노스캐롤라이나 대학교 채플힐 명예교수 (콜롬비아 인류학자)",
        "tier": "legend",
        "badge": "🏛️ 올타임 레전드",
        "avatar": "🌱",
        "core_philosophy": "서구 중심의 단일 세계(One-World) 개발 패러다임을 비판하고, 다종다양한 토착민과 지역 공동체의 존재론적 삶의 방식이 공존하는 '다원우주(Pluriverse)'를 옹호한다. 자연과 인간이 분리되지 않는 '영토 커먼즈'를 방어하고 자율적 삶을 위한 자치 디자인(Autonomous Design)을 실천해야 한다.",
        "key_concepts": ["다원우주(Pluriverse)", "관계적 존재론(Relational Ontology)", "탈개발(Post-development)", "자치 디자인(Autonomous Design)", "영토 방어"],
        "key_works": ["『Designs for the Pluriverse(다원우주를 위한 디자인)』 (2018)", "『Encountering Development(개발과의 조우)』 (1995)", "『Sentipensar con la tierra(대지와 함께 사유하기)』"],
        "representative_work": "『Designs for the Pluriverse』",
        "recent_activities": "라틴아메리카 풀뿌리 커뮤니티와 자치 디자인 워크숍 주도, 기후 위기 극복을 위한 탈추출주의 대안 모색.",
        "links": [
            {"title": "공식 웹사이트", "url": "http://arturoescobar.net/"}
        ]
    },
    {
        "id": "joan-martinez-alier",
        "name_kr": "호안 마르티네스 알리에르",
        "name_en": "Joan Martinez-Alier",
        "field": "생태경제학·환경정의·생태갈등",
        "category": "공간사회·도시커먼즈",
        "affiliation": "바르셀로나 자치대학교(UAB) ICTA 석좌교수 / 2023 홀베르그상 수상",
        "tier": "legend",
        "badge": "🏛️ 올타임 레전드",
        "avatar": "⚖️",
        "core_philosophy": "부유한 국가들의 경제 성장은 남반구와 소외 계층의 자원을 헐값에 수탈하고 생태적 부채를 전가하는 '물질적 추출주의'에 기반한다. 생존과 생계의 터전을 지키기 위해 광산과 댐에 맞서는 전 세계 빈민들의 저항은 지구 환경을 지키는 가장 강력한 '가난한 사람들의 환경주의'다.",
        "key_concepts": ["가난한 사람들의 환경주의", "생태 부채(Ecological Debt)", "생태적 분배 갈등", "EJAtlas(환경정의지도)", "탈성장(Degrowth)"],
        "key_works": ["『가난한 사람들의 환경주의(The Environmentalism of the Poor)』 (2002)", "『생태적 갈등의 땅(Land, Water, Air and Freedom)』 (2023)"],
        "representative_work": "『가난한 사람들의 환경주의』",
        "recent_activities": "전 세계 4,000여 개 환경 갈등을 기록하는 글로벌 데이터베이스 EJAtlas(Environmental Justice Atlas) 디렉터.",
        "links": [
            {"title": "EJAtlas 공식 플랫폼", "url": "https://ejatlas.org/"},
            {"title": "UAB ICTA 프로필", "url": "https://ictaweb.uab.cat/personal_detail.php?id=38"}
        ]
    },
    {
        "id": "anna-tsing",
        "name_kr": "애나 로웬하웁트 칭",
        "name_en": "Anna Lowenhaupt Tsing",
        "field": "인류학·다종민속지학·포스트휴먼",
        "category": "농생태·식량주권",
        "affiliation": "캘리포니아 대학교 산타크루즈(UCSC) 인류학과 교수",
        "tier": "legend",
        "badge": "🏛️ 올타임 레전드",
        "avatar": "🍄",
        "core_philosophy": "자본주의는 통제 불가능한 자연을 상품화하며 지구를 황폐화했지만, 인간이 파괴한 잔해 속에서도 송이버섯과 미생물, 인간 노동은 뜻밖의 협력과 공생을 엮어낸다. 진보라는 일직선적 신화를 넘어 예측 불가능한 불안정성(Precarity) 속에서 살아남는 다종 공생의 기술을 배워야 한다.",
        "key_concepts": ["말미암음의 버섯", "오염된 다양성(Contaminated Diversity)", "마찰(Friction)", "자본주의의 잔해 속 공생", "원산지 얽힘"],
        "key_works": ["『말미암음의 버섯(The Mushroom at the End of the World)』 (2015)", "『마찰(Friction)』 (2005)", "『Arts of Living on a Damaged Planet』 (공저, 2017)"],
        "representative_work": "『말미암음의 버섯(The Mushroom at the End of the World)』",
        "recent_activities": "Feral Atlas(야생 지도) 디지털 프로젝트를 통해 인간세 생태적 파괴의 비의도적 결과들을 매핑.",
        "links": [
            {"title": "Feral Atlas 프로젝트", "url": "https://feralatlas.org/"}
        ]
    },
    {
        "id": "vandana-shiva",
        "name_kr": "반다나 시바",
        "name_en": "Vandana Shiva",
        "field": "생태페미니즘·종자주권·소농자치",
        "category": "농생태·식량주권",
        "affiliation": "나브다냐(Navdanya) 재단 설립자 / 물리학자·생태철학자",
        "tier": "legend",
        "badge": "🏛️ 올타임 레전드",
        "avatar": "🌾",
        "core_philosophy": "다국적 생명공학 기업의 종자 특허와 화학비료 기반 녹색혁명은 소농의 종자 주권을 빼앗고 대지를 죽이는 '생명해적질(Biopiracy)'이다. 종자는 사유재산이 아니라 대지 어머니와 소농 공동체가 수천 년간 보존해 온 거룩한 커먼즈이며, 대지 민주주의(Earth Democracy)의 근간이다.",
        "key_concepts": ["종자 주권(Seed Sovereignty)", "대지 민주주의(Earth Democracy)", "생명해적질(Biopiracy) 비판", "살아있는 지구 커먼즈"],
        "key_works": ["『자연과 여성의 치유(Staying Alive)』 (1988)", "『토종 씨앗의 역습(Seed Sovereignty)』", "『만물의 민주주의(Earth Democracy)』 (2005)"],
        "representative_work": "『만물의 민주주의(Earth Democracy)』",
        "recent_activities": "인도 나브다냐 유기농 종자 은행 운영 및 전 세계 GMO 반대, 유기농 농생태학 보급 운동 전개.",
        "links": [
            {"title": "Navdanya 공식 웹사이트", "url": "https://www.navdanya.org/"}
        ]
    },
    {
        "id": "david-bollier",
        "name_kr": "데이비드 볼리어",
        "name_en": "David Bollier",
        "field": "커먼즈·공유재 거버넌스",
        "category": "커먼즈·공유재",
        "affiliation": "Schumacher Center for a New Economics / Commons Strategies Group",
        "tier": "legend",
        "badge": "🏛️ 올타임 레전드",
        "avatar": "🏛️",
        "core_philosophy": "커먼즈는 단순한 '자원'이 아니라 사람과 자원, 규범이 상호작용하는 살아있는 사회적 실천인 '커머닝(Commoning)'이다. 국가와 시장이라는 낡은 이분법을 넘어 자치와 협력에 기반한 새로운 존재론적 패러다임(Ontoshift)을 제안한다.",
        "key_concepts": ["커머닝(Commoning)", "온토시프트(Ontoshift)", "관계적 존재론", "커먼즈 법", "코스모로컬리즘"],
        "key_works": ["『공유인으로 살아가기(Think Like a Commoner)』", "『자유, 공정, 번영(Free, Fair, and Alive)』 (질케 헬프리히 공저)", "『The Commoner's Catalog for Changemaking』"],
        "representative_work": "『공유인으로 살아가기』",
        "recent_activities": "글로벌 커먼즈 패턴 랭귀지 보급, 팟캐스트 'Frontiers of Commoning' 진행.",
        "links": [
            {"title": "공식 웹사이트", "url": "https://www.bollier.org/"},
            {"title": "Frontiers of Commoning", "url": "https://frontiersofcommoning.podbean.com/"}
        ]
    },
    {
        "id": "michel-bauwens",
        "name_kr": "미셸 바우언스",
        "name_en": "Michel Bauwens",
        "field": "P2P 피어생산·코스모로컬 커먼즈",
        "category": "커먼즈·공유재",
        "affiliation": "P2P Foundation 설립자 / P2P 이론가",
        "tier": "legend",
        "badge": "🏛️ 올타임 레전드",
        "avatar": "💻",
        "core_philosophy": "정보 통신 기술의 발전은 중앙집권적 기업 없이도 동료들이 수평적으로 가치를 공동 생산하는 P2P(Peer-to-Peer) 생산 양식을 가능하게 했다. 지식은 글로벌 디지털 커먼즈로 공유하고 물리적 생산은 지역에서 자치적으로 순환하는 '코스모로컬(Cosmo-local)' 생산 체제를 구축해야 한다.",
        "key_concepts": ["P2P 협동 생산", "코스모로컬리즘(Cosmo-localism)", "개방형 협동조합", "파트너 국가(Partner State)", "커먼즈 기반 동료 생산"],
        "key_works": ["『Peer to Peer: The Commons Manifesto』 (2019)", "『네트워크 사회와 P2P 혁명』"],
        "representative_work": "『Peer to Peer: The Commons Manifesto』",
        "recent_activities": "P2P Foundation 위키 운영, 부탄 및 에콰도르 정부의 커먼즈 전환 정책 자문.",
        "links": [
            {"title": "P2P Foundation", "url": "https://p2pfoundation.net/"}
        ]
    },
    {
        "id": "karl-polanyi",
        "name_kr": "칼 폴라니",
        "name_en": "Karl Polanyi",
        "field": "정치경제학·탈상품화·사회적 배태성",
        "category": "커먼즈·공유재",
        "affiliation": "컬럼비아 대학교 교수 (오스트리아-헝가리 정치경제학자)",
        "tier": "legend",
        "badge": "🏛️ 올타임 레전드",
        "avatar": "🔄",
        "core_philosophy": "토지, 노동, 화폐는 시장에서 판매하기 위해 만들어진 상품이 아닌 '허구적 상품(Fictitious Commodities)'이다. 시장이 사회로부터 분리되어 인간과 자연을 파괴할 때, 사회는 스스로를 방어하기 위해 '이중 운동(Double Movement)'을 일으킨다. 진정한 인간적 삶은 토지와 돌봄의 '탈상품화(Decommodification)'를 통해 가능하다.",
        "key_concepts": ["허구적 상품(토지·노동·화폐)", "사회적 배태성(Embeddedness)", "이중 운동(Double Movement)", "탈상품화(Decommodification)", "호혜성과 재분배"],
        "key_works": ["『거대한 전환(The Great Transformation)』 (1944)", "『인간의 경제(The Livelihood of Man)』 (1977)"],
        "representative_work": "『거대한 전환(The Great Transformation)』",
        "recent_activities": "동시대 신자유주의 금융화와 기후 위기를 넘어서는 대안 경제학의 기본 토대로 전 세계적 재조명.",
        "links": [
            {"title": "Karl Polanyi Institute", "url": "https://www.concordia.ca/research/polanyi.html"}
        ]
    },
    {
        "id": "lena-dominelli",
        "name_kr": "레나 도미넬리",
        "name_en": "Lena Dominelli",
        "field": "녹색사회복지·기후재난 취약성",
        "category": "재난안전·공공인프라",
        "affiliation": "스털링 대학교(University of Stirling) 사회복지학과 교수",
        "tier": "legend",
        "badge": "🏛️ 올타임 레전드",
        "avatar": "🛡️",
        "core_philosophy": "기후 재난과 환경 파괴는 모든 사람에게 평등하게 다가오지 않으며, 빈곤층, 노인, 1인 가구, 장애인 등 사회적 약자에게 가장 가혹한 고통을 전가한다. '녹색사회복지(Green Social Work)'는 환경 정의와 사회적 돌봄을 결합하여 최소 개입형이자 상호부조적인 회복력 인프라를 구축하는 실천이다.",
        "key_concepts": ["녹색사회복지(Green Social Work)", "재난 취약성(Disaster Vulnerability)", "환경 정의(Environmental Justice)", "기후 돌봄(Climate Care)", "풀뿌리 상호부조"],
        "key_works": ["『녹색사회복지(Green Social Work)』 (2012)", "『기후변화와 사회복지』 (2014)"],
        "representative_work": "『녹색사회복지(Green Social Work)』",
        "recent_activities": "국제사회복지사연맹(IASSW) 재난구호위원회 위원장, 기후 난민 및 취약계층 재난 안전망 구축 프로젝트 리딩.",
        "links": [
            {"title": "University of Stirling 프로필", "url": "https://www.stir.ac.uk/people/256950"}
        ]
    },
    {
        "id": "sasha-costanza-chock",
        "name_kr": "사샤 코스탄자-촉",
        "name_en": "Sasha Costanza-Chock",
        "field": "디자인 정의·시빅 미디어·포용HCI",
        "category": "시빅HCI·UXR",
        "affiliation": "메사추세츠 공과대학교(MIT) 객원교수 / Design Justice Network",
        "tier": "legend",
        "badge": "🏛️ 올타임 레전드",
        "avatar": "📐",
        "core_philosophy": "디자인은 가치중립적이지 않으며 대다수의 기술 인터페이스는 비장애인·백인·남성을 기본값으로 상정하여 사회적 약자를 배제한다. '디자인 정의(Design Justice)'는 시스템에 의해 가장 큰 불이익을 받는 당사자가 설계의 주도권을 갖도록 인터페이스 권력 관계를 전복하는 실천이다.",
        "key_concepts": ["디자인 정의(Design Justice)", "매트릭스 지배(Matrix of Domination)", "시빅 미디어", "참여형 사용자경험(UXR)", "기술 민주화"],
        "key_works": ["『디자인 정의(Design Justice: Community-Led Practices to Build the Worlds We Need)』 (2020)"],
        "representative_work": "『디자인 정의(Design Justice)』",
        "recent_activities": "Design Justice Network 코디네이터, 인공지능 윤리 가이드라인 및 공공 포용 디자인 실천.",
        "links": [
            {"title": "Design Justice Network", "url": "https://designjustice.org/"},
            {"title": "개인 포트폴리오", "url": "https://schock.cc/"}
        ]
    },
    {
        "id": "yuk-hui",
        "name_kr": "육 후이",
        "name_en": "Yuk Hui",
        "field": "기술철학·다원기술론·디지털 존재론",
        "category": "과학기술학·STS",
        "affiliation": "에라스무스 로테르담 대학교 교수 / 철학자",
        "tier": "legend",
        "badge": "🏛️ 올타임 레전드",
        "avatar": "⚙️",
        "core_philosophy": "서구 중심의 단일한 보편 기술관을 해체하고 각 문화권과 지역의 철학적 우주론에 뿌리내린 다원적 기술인 '코스모테크닉스(Cosmotechnics)'를 복원해야 한다. 디지털 객체와 알고리즘의 본질을 인간과 자연과의 도덕적 관계 속에서 재정의할 것을 촉구한다.",
        "key_concepts": ["코스모테크닉스(Cosmotechnics)", "디지털 객체의 존재론", "재귀성과 우발성", "기계와 유기체"],
        "key_works": ["『중국에서의 기술에 관한 물음』 (2016)", "『디지털 객체의 존재에 대하여』 (2016)", "『예술과 코스모테크닉스』 (2021)"],
        "representative_work": "『중국에서의 기술에 관한 물음』",
        "recent_activities": "Research Network for Philosophy and Technology 설립 및 유럽-아시아 철학 콜로키움 주재.",
        "links": [
            {"title": "공식 웹사이트", "url": "http://digitalmilieu.net/"}
        ]
    },
    {
        "id": "lee-kwang-suk",
        "name_kr": "이광석",
        "name_en": "Lee Kwang-suk",
        "field": "디지털 문화·플랫폼 비판·기술생태론",
        "category": "과학기술학·STS",
        "affiliation": "서울과학기술대학교 IT정책전문대학원 교수 / 『문화/과학』 편집위원",
        "tier": "legend",
        "badge": "🏛️ 올타임 레전드",
        "avatar": "🇰🇷",
        "core_philosophy": "자본주의 플랫폼이 일상과 감정, 데이터를 추출하고 독점하는 기술봉건주의(Techno-feudalism)를 비판한다. 디지털 테크놀로지를 생태적 파괴의 도구가 아닌 탈성장과 생태적 커머닝, 그리고 시민 자율성을 북돋우는 '기술생태(Techno-ecology)'로 전환해야 한다.",
        "key_concepts": ["기술생태학", "데이터 정의", "플랫폼 자본주의 비판", "디지털 커먼즈", "포스트휴먼 감수성"],
        "key_works": ["『피드백 커먼즈』 (2023)", "『디지털의 배반』 (2017)", "『데이터 사회 미학』 (2020)"],
        "representative_work": "『피드백 커먼즈』",
        "recent_activities": "계간 『문화/과학』을 중심으로 기술비판 담론 선도 및 디지털 커먼즈 연구 프로젝트 진행.",
        "links": [
            {"title": "서울과기대 교수 소개", "url": "https://itpp.seoultech.ac.kr/"}
        ]
    },
    {
        "id": "jung-young-shin",
        "name_kr": "정영신",
        "name_en": "Jung Young-shin",
        "field": "마을 커먼즈·농촌사회학·지역자치",
        "category": "커먼즈·공유재",
        "affiliation": "가톨릭대학교 사회학과 교수 / 커먼즈 연구자",
        "tier": "legend",
        "badge": "🏛️ 올타임 레전드",
        "avatar": "🏡",
        "core_philosophy": "한국 전통 사회의 송계, 두레, 마을 숲 등 자치적 커먼즈의 역사를 발굴하고, 현대 농촌 및 지역 사회에서 숲과 바람, 물을 공동 관리하는 커머닝 실천을 현장 민속지로 분석한다. 중앙 정부 중심의 농정 대신 지역 주민들의 자립적 커먼즈 거버넌스를 역설한다.",
        "key_concepts": ["한국형 마을 커먼즈", "송계와 두레", "지역 자치 거버넌스", "대안적 농촌사회학", "생태적 공유지"],
        "key_works": ["『커먼즈란 무엇인가』 (공저)", "『마을의 귀환』 (공저)", "『공동자원론』"],
        "representative_work": "『커먼즈란 무엇인가』",
        "recent_activities": "제주 풍력·지하수 커먼즈 및 농촌 지역사회 회복탄력성 현장 조사.",
        "links": [
            {"title": "가톨릭대학교 교수 소개", "url": "https://www.catholic.ac.kr/"}
        ]
    }
]


def extract_trending_scholars_from_archive(archive, limit=25):
    """
    아카이브 전체를 스캔하여 동시대 학술 담론을 이끄는 핫한 실시간 연구자 추출 및 프로필 자동 생성
    """
    author_counts = Counter()
    author_papers = defaultdict(list)
    author_categories = defaultdict(Counter)
    author_latest_date = {}

    ignored_names = {
        "연구진", "p2p foundation", "p2p foundation blog", "기타", "et al.", "admin", "editorial",
        "anonymous", "editor", "author", "authors"
    }

    for digest in archive:
        d_date = digest.get("date", "")
        for it in digest.get("items", []):
            raw_authors = it.get("authors", "")
            if not raw_authors:
                continue
            
            # Split comma and 'and'
            parts = [p.strip() for p in re.split(r",|\sand\s", raw_authors) if p.strip()]
            for a in parts:
                a_clean = re.sub(r"\(.*?\)", "", a).strip()
                if len(a_clean) < 3 or a_clean.lower() in ignored_names:
                    continue
                
                author_counts[a_clean] += 1
                cat = it.get("category", "커먼즈·공유재")
                author_categories[a_clean][cat] += 1
                
                # Check latest date
                if a_clean not in author_latest_date or d_date > author_latest_date[a_clean]:
                    author_latest_date[a_clean] = d_date

                # Deduplicate paper by URL
                existing_urls = [p["url"] for p in author_papers[a_clean]]
                if it.get("url") not in existing_urls:
                    author_papers[a_clean].append({
                        "title": it.get("title_kr") or it.get("original_title"),
                        "orig_title": it.get("original_title"),
                        "source": it.get("source"),
                        "url": it.get("url"),
                        "date": it.get("published") or d_date,
                        "category": cat
                    })

    # Top authors sorted by paper count and recency
    ranked_authors = []
    for a, cnt in author_counts.most_common():
        papers = author_papers[a]
        latest_d = author_latest_date.get(a, "")
        ranked_authors.append({
            "name": a,
            "count": cnt,
            "latest_date": latest_d,
            "papers": papers,
            "top_category": author_categories[a].most_common(1)[0][0] if author_categories[a] else "커먼즈·공유재"
        })

    # Sort by recency (2026 먼저) then count
    ranked_authors.sort(key=lambda x: (x["latest_date"], x["count"]), reverse=True)

    trending_list = []
    category_emojis = {
        "커먼즈·공유재": "🤝",
        "과학기술학·STS": "🔬",
        "시빅HCI·UXR": "💻",
        "농생태·식량주권": "🌱",
        "공간사회·도시커먼즈": "🏙️",
        "재난안전·공공인프라": "🛡️",
        "돌봄·상호부조": "🫂"
    }

    for i, ra in enumerate(ranked_authors[:limit], 1):
        name = ra["name"]
        cat = ra["top_category"]
        count = ra["count"]
        latest_date = ra["latest_date"]
        papers = ra["papers"]

        # Badges
        if latest_date >= "2026-11":
            badge = "🔥 이번 주 살롱 수록"
        elif count >= 3:
            badge = f"⭐ {count}회 다수 수록"
        else:
            badge = "⚡ 핫 토픽 연구자"

        # Extract topics from paper titles
        topics = set()
        for p in papers:
            txt = f"{p['title']} {p.get('orig_title', '')}".lower()
            if "solar" in txt or "태양" in txt: topics.add("태양성·에너지전환")
            if "algorithm" in txt or "ai" in txt or "알고리즘" in txt: topics.add("알고리즘정의·AI윤리")
            if "respect" in txt or "health" in txt or "소통" in txt or "돌봄" in txt: topics.add("존중의수사학·돌봄소통")
            if "mining" in txt or "extract" in txt or "채굴" in txt: topics.add("자원추출주의·영토커먼즈")
            if "finance" in txt or "platform" in txt or "금융" in txt: topics.add("플랫폼책무·임베디드금융")
            if "farmer" in txt or "cooperation" in txt or "농민" in txt: topics.add("농민협동·소농경제")
            if "urban" in txt or "city" in txt or "도시" in txt: topics.add("도시커먼즈·공간정의")
            if "resilience" in txt or "회복" in txt: topics.add("사회생태적회복탄력성")
            if "disaster" in txt or "safety" in txt or "재난" in txt: topics.add("위기정보학·공공안전망")
            if "interspecies" in txt or "nature" in txt or "생태" in txt: topics.add("다종공생·대지윤리")
        
        if not topics:
            topics.add(cat.split("·")[0])
            topics.add("동시대학술연구")

        # Affiliation & bio inference
        latest_p = papers[0]
        recent_src = latest_p.get("source", "학술 저널")
        bio = f"학술지 '{recent_src}'에 연구를 게재하며, {cat} 분야에서 활발히 논문을 발표하고 있는 동시대 주목 연구자입니다."

        slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.lower()).strip("-") or f"scholar-{i}"

        links = [
            {"title": "OpenAlex 프로필", "url": f"https://openalex.org/authors?search={name.replace(' ', '+')}"},
            {"title": "Google Scholar", "url": f"https://scholar.google.com/scholar?q={name.replace(' ', '+')}"}
        ]
        if papers and papers[0].get("url"):
            links.insert(0, {"title": "최신 논문 보기", "url": papers[0]["url"]})

        trending_list.append({
            "id": slug,
            "name_kr": name,
            "name_en": name,
            "field": f"{cat} · 동시대 연구",
            "category": cat,
            "affiliation": f"{recent_src} 게재 연구진",
            "tier": "trending",
            "badge": badge,
            "avatar": category_emojis.get(cat, "📝"),
            "paper_count": count,
            "latest_active": latest_date,
            "core_philosophy": f"최근 논문 <{latest_p['title']}> 등을 통해 {', '.join(list(topics)[:3])}의 문제를 실증적이고 비판적으로 규명하고 있습니다.",
            "key_concepts": list(topics)[:5],
            "key_works": [p["title"] for p in papers[:3]],
            "recent_papers": papers[:4],
            "representative_work": papers[0]["title"],
            "recent_activities": f"살롱 최근 수록일({latest_date}): '{recent_src}'에 <{latest_p['title']}> 발표.",
            "links": links
        })

    return trending_list


def generate_unified_gurus(archive):
    """
    올타임 레전드와 동시대 핫한 연구자를 결합한 통합 데이터셋 생성
    """
    trending = extract_trending_scholars_from_archive(archive, limit=20)
    legends = ALL_TIME_LEGENDS

    return {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_trending": len(trending),
        "total_legends": len(legends),
        "total_all": len(trending) + len(legends),
        "trending_scholars": trending,
        "all_time_legends": legends,
        # Flat list for backwards compatibility
        "all_scholars": trending + legends
    }


def update_gurus_file(archive=None):
    """
    gurus.json 파일 자동 갱신 및 저장:
    ScholarGPS, Google Scholar, AD Scientific Index & OpenAlex 기반 전 분야 고영향력 석학 39인 유지
    """
    try:
        from update_gurus_scholars import generate_gurus_json
        generate_gurus_json()
    except Exception as e:
        print(f"Notice: Failed to run generate_gurus_json: {e}")


if __name__ == "__main__":
    archive_path = os.path.join(WEB_DATA_DIR, "archive.json")
    if os.path.exists(archive_path):
        with open(archive_path, "r", encoding="utf-8") as f:
            archive = json.load(f)
        ds = update_gurus_file(archive)
        print("Sample trending scholar:", ds["trending_scholars"][0]["name_kr"])
        print("Sample legend:", ds["all_time_legends"][0]["name_kr"])
