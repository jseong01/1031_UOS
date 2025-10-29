import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

# ---------------- 기본 설정 ----------------
st.set_page_config(page_title="행정 우선 개선 진단", page_icon="🛠️", layout="wide")

# 헤더
st.title("🛠️ 행정 우선 개선 진단")
st.caption("자치구별로 만족도에 부정적 영향을 주는 주요 요인을 확인합니다.")

# ---------------- 데이터 불러오기 ----------------
# BASE_DIR = 현재 파일(pages/행정진단.py)의 상위 폴더 (streamlit/)
BASE_DIR = Path(__file__).resolve().parent.parent
C_FILE = BASE_DIR / "중요도 정규화.csv"

VARS = [
    "교통이용만족도_평균","보행환경만족도_주거지역","녹지현황(개소)","상수도요금평단",
    "구별 의료기관 수","노인여가복지시설 개수","도시 위험도","구별 지방세 징수액",
    "구별 주택매매지수","보육시설이용률",
    "구별 초등학교 교원 1인당 학생 수","구별 중학교 교원 1인당 학생 수",
    "구별 고등학교 교원 1인당 학생수","구별 유치원 교원 1인당 학생 수",
]

@st.cache_data(show_spinner=False)
def load_influence(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, index_col=0)
    for v in VARS:
        if v not in df.columns:
            raise ValueError(f"⚠️ 영향지수 파일에 '{v}' 변수가 없습니다.")
    return df[VARS].astype(float)

if not C_FILE.exists():
    st.error(f"⚠️ 영향지수 파일을 찾을 수 없습니다: {C_FILE}")
    st.stop()

C_norm = load_influence(C_FILE)

# ---------------- 옵션 ----------------
st.sidebar.header("⚙️ 옵션")
top_k = st.sidebar.slider("상위 음수 변수 개수", 1, 10, 5)

# ---------------- 음수 기여 상위 K ----------------
neg_long = (
    C_norm.reset_index(names="구")
    .melt(id_vars="구", var_name="변수", value_name="기여도")
)
neg_long = neg_long[neg_long["기여도"] < 0].copy()
neg_long["절댓값"] = neg_long["기여도"].abs()

top_neg = (
    neg_long.sort_values(["구","절댓값"], ascending=[True, False])
             .groupby("구", as_index=False)
             .head(top_k)
)

# ---------------- 자치구 선택 & TopK 변수명만 보기 ----------------
gu_list = sorted(C_norm.index.astype(str).tolist())
selected_gu = st.sidebar.selectbox("자치구 선택", gu_list)

sel_topk = (
    neg_long.loc[neg_long["구"] == selected_gu]
            .sort_values("절댓값", ascending=False)
            .head(top_k)[["변수"]]
    .reset_index(drop=True)
)
sel_topk.index = sel_topk.index + 1

# ---------------- 결과 출력 ----------------
st.markdown("---")
st.subheader(f"🔎 {selected_gu} 개선 우선 변수 Top {top_k}")
st.caption("자치구별 만족도에 부정적 영향을 준 요인들의 순위를 표시합니다.")
st.table(sel_topk)
