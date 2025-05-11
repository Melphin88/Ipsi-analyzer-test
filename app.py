import streamlit as st
import pandas as pd
import plotly.express as px

# 데이터 불러오기
data = pd.read_csv("sci_comp_data_with_level.csv")

st.title("🎓 이과 입시 지원 가능성 분석기")

# 📌 지원유형 선택
admission_type = st.radio("🗂️ 지원유형 선택", ["정시", "수시"])

# 🎯 과목 가중치 프리셋
preset_options = {
    "선택 안 함": None,
    "연세대학교": {"kor": 3.0, "math": 4.0, "sci": 3.0},
    "고려대학교": {"kor": 3.3, "math": 3.3, "sci": 3.3},
    "성균관대학교": {"kor": 2.5, "math": 4.0, "sci": 3.5}
}

preset_choice = st.selectbox("🏫 대학별 가중치 프리셋 선택", list(preset_options.keys()))

# ⚙️ 가중치 설정
default_kor = preset_options[preset_choice]["kor"] if preset_choice != "선택 안 함" else 3.5
default_math = preset_options[preset_choice]["math"] if preset_choice != "선택 안 함" else 3.8
default_sci = preset_options[preset_choice]["sci"] if preset_choice != "선택 안 함" else 3.5

with st.expander("⚙️ 과목별 가중치 조정"):
    kor_weight = st.slider("국어 가중치", 0.0, 5.0, default_kor, 0.1)
    math_weight = st.slider("수학 가중치", 0.0, 5.0, default_math, 0.1)
    sci_weight = st.slider("탐구 가중치", 0.0, 5.0, default_sci, 0.1)

# 점수 입력
with st.form("score_form"):
    st.subheader("📘 과목별 점수 입력")
    kor = st.number_input("국어 점수 (0~100)", 0, 100)
    math = st.number_input("수학 점수 (0~100)", 0, 100)
    sci = st.number_input("탐구 두 과목 합산 점수 (0~100)", 0, 100)
    eng_grade = st.selectbox("영어 등급 (1~9)", list(range(1, 10)))
    school_grade = st.selectbox("내신 등급 (1~9)", list(range(1, 10)))
    submitted = st.form_submit_button("지원 가능성 분석하기")

# 영어 감점 / 내신 보너스
ENG_PENALTY = {1: 0, 2: -1, 3: -2.5, 4: -4, 5: -6, 6: -8, 7: -10, 8: -12, 9: -15}
NAESIN_SCORE = {1: 20, 2: 18, 3: 16, 4: 14, 5: 12, 6: 10, 7: 8, 8: 6, 9: 4}

# 제출 저장
if submitted:
    st.session_state["submitted"] = True
    st.session_state["user_input"] = {
        "kor": kor, "math": math, "sci": sci,
        "eng_grade": eng_grade, "school_grade": school_grade,
        "kor_weight": kor_weight, "math_weight": math_weight,
        "sci_weight": sci_weight, "admission_type": admission_type
    }

# 분석 로직
if st.session_state.get("submitted", False):
    ui = st.session_state["user_input"]
    if ui["admission_type"] == "정시":
        total = (
            ui["kor"] * ui["kor_weight"]
            + ui["math"] * ui["math_weight"]
            + ui["sci"] * ui["sci_weight"]
            + ENG_PENALTY[ui["eng_grade"]]
            + NAESIN_SCORE[ui["school_grade"]]
        )
    else:
        total = (
            (ui["kor"] + ui["math"] + ui["sci"]) * 0.6
            + NAESIN_SCORE[ui["school_grade"]] * 2
        )

    st.markdown(f"### ✅ 계산된 환산 점수: **{round(total, 2)}점**")

    def classify(score, cutoff):
        diff = score - cutoff
        if pd.isna(score) or pd.isna(cutoff): return "데이터 부족"
        elif diff >= 10: return "안정"
        elif diff >= -10: return "적정"
        else: return "소신"

    def estimate_probability(score, cutoff):
        diff = score - cutoff
        if pd.isna(score) or pd.isna(cutoff): return None
        if diff >= 20: return 95
        elif diff >= 10: return 75
        elif diff >= -10: return 50
        elif diff >= -20: return 30
        else: return 10

    data["분석된 지원 가능성"] = data["적정점수"].apply(lambda c: classify(total, c))
    data["합격 확률(%)"] = data["적정점수"].apply(lambda c: estimate_probability(total, c))

    # 필터
    st.markdown("## 🎛️ 결과 필터")
    possibility_filter = st.multiselect("📌 지원 가능성 선택", ["소신", "적정", "안정"], default=["적정", "안정"])
    level_options = data["대학 수준"].unique().tolist()
    selected_levels = st.multiselect("🏫 대학 수준 선택", level_options, default=level_options)
    major_keyword = st.text_input("🔍 전공 키워드", "")
    univ_keyword = st.text_input("🏫 대학명 키워드", "")
    top10_only = st.checkbox("🔝 상위 10개만 보기")

    sort_column = st.selectbox("정렬 기준", ["적정점수", "합격 확률(%)", "대학교", "전공"])
    sort_asc = st.radio("정렬 방식", ["내림차순", "오름차순"]) == "오름차순"

    result = data.copy()
    if possibility_filter:
        result = result[result["분석된 지원 가능성"].isin(possibility_filter)]
    if selected_levels:
        result = result[result["대학 수준"].isin(selected_levels)]
    if major_keyword.strip():
        result = result[result["전공"].str.contains(major_keyword, case=False, na=False)]
    if univ_keyword.strip():
        result = result[result["대학교"].str.contains(univ_keyword, case=False, na=False)]

    result = result.sort_values(by=sort_column, ascending=sort_asc)
    if top10_only:
        result = result.head(10)

    st.markdown("### 🎯 분석 결과")
    st.dataframe(result[["대학교", "전공", "대학 수준", "적정점수", "분석된 지원 가능성", "합격 확률(%)"]])

    if result.empty:
        st.warning("조건에 맞는 학과가 없습니다.")
    else:
        st.markdown("### 📊 대학별 합격 확률")
        bar_fig = px.bar(result, x="대학교", y="합격 확률(%)", color="분석된 지원 가능성", hover_data=["전공"])
        st.plotly_chart(bar_fig, use_container_width=True)

        st.markdown("### 🥧 지원 가능성 분포")
        pie_data = result["분석된 지원 가능성"].value_counts().reset_index()
        pie_data.columns = ["지원 가능성", "학과 수"]
        pie_fig = px.pie(pie_data, names="지원 가능성", values="학과 수", title="지원 분포")
        st.plotly_chart(pie_fig, use_container_width=True)
