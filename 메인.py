# ============================================
# 서울 이사 만족도 추천 (집값 티어 미리 정의 + 설문 14문항)
# ============================================
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import os

# ============================================
# 페이지 설정
# ============================================
st.set_page_config(
    page_title="서울시 맞춤형 동네 추천 — 당신의 라이프스타일을 반영합니다",
    page_icon="🌆",
    layout="wide"
)

# ============================================
# 상대경로 설정 (Streamlit Cloud 호환)
# ============================================
BASE_DIR = Path(__file__).resolve().parent
LOGO_DIR = BASE_DIR / "logos"
DATA_DIR = BASE_DIR
C_FILE = DATA_DIR / "중요도 정규화.csv"

# ============================================
# 상단 로고 + 제목
# ============================================
logo_seoul = LOGO_DIR / "서울시.jpeg"
logo_uos = LOGO_DIR / "서울시립대.png"

cols = st.columns([1, 3, 1])

with cols[0]:
    if logo_seoul.exists():
        st.image(str(logo_seoul), width=200)
    else:
        st.markdown("🏙️")

with cols[1]:
    st.markdown(
        """
        <div style='text-align:center; line-height:1.4;'>
            <h1 style='margin-bottom:0;'> 서울시 맞춤형 동네 추천</h1>
            <h4 style='color:#5a5a5a; margin-top:0.3em; font-weight:400;'>
                <em>Seoul Lifestyle Matching System</em>
            </h4>
            <p style='color:gray; margin-top:0.4em; font-size:16px;'>
                데이터 기반으로 <b>당신의 생활환경 선호도</b>에 꼭 맞는 동네를 찾아드립니다.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

with cols[2]:
    if logo_uos.exists():
        st.image(str(logo_uos), width=200)
    else:
        st.markdown("🎓")

st.markdown("---")

# ============================================
# 데이터 정의
# ============================================
tier_data = {
    "강남구": "상", "강동구": "중", "강북구": "하", "강서구": "하", "관악구": "하",
    "광진구": "상", "구로구": "하", "금천구": "하", "노원구": "하", "도봉구": "하",
    "동대문구": "중", "동작구": "상", "마포구": "중", "서대문구": "중", "서초구": "상",
    "성동구": "중", "성북구": "하", "송파구": "상", "양천구": "상", "영등포구": "중",
    "용산구": "상", "은평구": "중", "종로구": "상", "중구": "중", "중랑구": "중"
}

VARS = [
    "교통이용만족도_평균","보행환경만족도_주거지역","녹지현황(개소)","상수도요금평단",
    "구별 의료기관 수","노인여가복지시설 개수","도시 위험도","구별 지방세 징수액",
    "구별 주택매매지수","보육시설이용률",
    "구별 초등학교 교원 1인당 학생 수","구별 중학교 교원 1인당 학생 수",
    "구별 고등학교 교원 1인당 학생수","구별 유치원 교원 1인당 학생 수",
]

QUESTIONS = {
    "교통이용만족도_평균": "교통 이용 편의성(대중교통 접근/정시성)",
    "보행환경만족도_주거지역": "보행환경(보도 안전/쾌적성)",
    "녹지현황(개소)": "공원/녹지 접근성",
    "상수도요금평단": "상수도 요금 부담",
    "구별 의료기관 수": "의료 접근성(병원/의원 수)",
    "노인여가복지시설 개수": "노인 여가/복지 인프라",
    "도시 위험도": "도시 안전(위험 낮음)",
    "구별 지방세 징수액": "재정 여력(세수/서비스)",
    "구별 주택매매지수": "주택시장 안정성(가격 수준/변동)",
    "보육시설이용률": "보육 인프라 충족도",
    "구별 초등학교 교원 1인당 학생 수": "초등학교 학급 밀도",
    "구별 중학교 교원 1인당 학생 수": "중학교 학급 밀도",
    "구별 고등학교 교원 1인당 학생수": "고등학교 학급 밀도",
    "구별 유치원 교원 1인당 학생 수": "유치원 학급 밀도",
}

# ============================================
# 영향지수 로드
# ============================================
@st.cache_data(show_spinner=False)
def load_influence(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, index_col=0)
    for v in VARS:
        if v not in df.columns:
            raise ValueError(f"영향지수 파일에 누락된 변수: {v}")
    return df[VARS].astype(float)

if not C_FILE.exists():
    st.error(f"⚠️ 영향지수 파일이 없습니다: {C_FILE}")
    st.stop()

C_norm = load_influence(C_FILE)

# ============================================
# 집값 티어 선택
# ============================================
st.sidebar.header("🏠 집값 수준 선택")
selected_tier = st.sidebar.selectbox("집값 수준 선택", ["상", "중", "하"], index=1)
allowed = [gu for gu, tier in tier_data.items() if tier == selected_tier]
C_sub = C_norm.loc[C_norm.index.intersection(allowed)]

# ============================================
# 사용자 입력 (14문항)
# ============================================
st.markdown("생활환경 요소에 대해 중요도를 입력하세요 (1️⃣: 전혀 중요하지 않음  ~ 5️⃣ : 매우 중요)")

cols = st.columns(2)
w_user = {}
for i, var in enumerate(VARS):
    col = cols[i % 2]
    val = col.slider(f"{i+1}. {QUESTIONS[var]}", 1, 5, 3, 1)
    w_user[var] = (val - 1.0) / 4.0  # 0~1로 변환

w = pd.Series(w_user, index=VARS)
if w.sum() > 0:
    w = w / w.sum()

# ============================================
# 점수 계산 (정규화 영향지수 × 중요도)
# ============================================
score = (C_sub * w).sum(axis=1)
rank = score.sort_values(ascending=False).to_frame("예상 만족도 점수")

# ============================================
# 결과 표시 (TOP3 카드)
# ============================================
gu_info = {
    "강남구": ("https://www.gangnam.go.kr", "서울의 경제·문화 중심, 높은 생활 인프라"),
    "강동구": ("https://www.gangdong.go.kr", "쾌적한 주거환경과 한강변 녹지 조성"),
    "강북구": ("https://www.gangbuk.go.kr", "북한산 자락의 자연 친화적 도시"),
    "강서구": ("https://www.gangseo.seoul.kr", "김포공항 인접, 서남권 관문도시"),
    "관악구": ("https://www.gwanak.go.kr", "대학가 중심의 젊은 분위기와 문화"),
    "광진구": ("https://www.gwangjin.go.kr", "건대입구 중심의 상권·문화 중심지"),
    "구로구": ("https://www.guro.go.kr", "IT산업단지와 남부 생활거점"),
    "금천구": ("https://www.geumcheon.go.kr", "첨단산업 중심의 도심형 자족도시"),
    "노원구": ("https://www.nowon.kr", "북부 주거 중심지, 교육환경 우수"),
    "도봉구": ("https://www.dobong.go.kr", "자연과 조화된 조용한 주거지역"),
    "동대문구": ("https://www.ddm.go.kr", "패션과 상업 중심, 교통 접근성 우수"),
    "동작구": ("https://www.dongjak.go.kr", "한강변 주거·교육 환경 우수"),
    "마포구": ("https://www.mapo.go.kr", "홍대·상수 중심의 젊은 문화 중심지"),
    "서대문구": ("https://www.sdm.go.kr", "연세대·이화여대 등 학문 중심지"),
    "서초구": ("https://www.seocho.go.kr", "예술의전당·교육 중심의 고급 주거지"),
    "성동구": ("https://www.sd.go.kr", "성수·왕십리 개발로 급부상한 지역"),
    "성북구": ("https://www.sb.go.kr", "고려대·성신여대 등 교육·문화 중심"),
    "송파구": ("https://www.songpa.go.kr", "잠실 중심의 주거·상업 복합지역, 편리한 교통망"),
    "양천구": ("https://www.yangcheon.go.kr", "목동 중심의 교육특화·쾌적 주거지"),
    "영등포구": ("https://www.ydp.go.kr", "여의도 금융·비즈니스 중심지"),
    "용산구": ("https://www.yongsan.go.kr", "한강변 국제업무지구로 발전 중"),
    "은평구": ("https://www.ep.go.kr", "북서부 교통 요충지, 자연 친화적"),
    "종로구": ("https://www.jongno.go.kr", "서울의 역사·행정 중심지"),
    "중구": ("https://www.junggu.seoul.kr", "도심 상업 중심, 접근성 최상"),
    "중랑구": ("https://www.jungnang.seoul.kr", "동북권 주거지, 서울 외곽 접근 용이")
}

st.subheader("🏆 추천 TOP 3 자치구")

top3 = rank.head(3).index

for i, gu in enumerate(top3, start=1):
    url, desc = gu_info.get(gu, ("#", "정보 없음"))
    logo_path = LOGO_DIR / f"{gu}.png"

    cols = st.columns([1, 5])
    with cols[0]:
        if logo_path.exists():
            st.image(str(logo_path), width=80)
        else:
            st.markdown("🗺️")
    with cols[1]:
        st.markdown(f"""
        <div style="margin-top:-10px">
        <h4>🏅 {i}위 : {gu}</h4>
        <p><a href="{url}" target="_blank">🔗 {url}</a></p>
        <p style="color:gray;">{desc}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
