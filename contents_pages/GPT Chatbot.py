from openai import OpenAI
import streamlit as st
import pandas as pd
import os

# 페이지 설정
st.set_page_config(
    page_title="Chat Bot",
    initial_sidebar_state="expanded",
    layout="wide"
)

# 사이드바 - API 키 입력
with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    "[OpenAI API key 발급](https://platform.openai.com/account/api-keys)"

# 데이터 로딩
data_path = "./data/2024년 누적 데이터.csv"
if not os.path.exists(data_path):
    st.error("🚫 데이터 파일을 찾을 수 없습니다. 경로를 확인해주세요.")
    st.stop()

df_new = pd.read_csv(data_path, index_col=0)

# 연료별 통계 요약 함수
def summarize_fuel_by_keyword(fuel_type: str, user_input: str):
    if fuel_type == None :
        fuel_df = df_new
    else:
        fuel_df = df_new[df_new["FUEL"] == fuel_type]

    result = {}

    # 연령
    if "연령" in user_input or "나이" in user_input:
        result["연령별 집계"] = fuel_df.groupby("AGE")["CNT"].sum().sort_values(ascending=False).to_string()

    # 국산/수입
    if "국산" in user_input or "수입" in user_input or "세그먼트" in user_input:
        result["국산/수입 세그먼트별 집계"] = fuel_df.groupby("CL_HMMD_IMP_SE_NM")["CNT"].sum().sort_values(
            ascending=False).to_string()

    # 브랜드
    if "브랜드" in user_input:
        result["브랜드별 집계"] = fuel_df.groupby("ORG_CAR_MAKER_KOR")["CNT"].sum().sort_values(ascending=False).to_string()

    # 모델
    if "모델" in user_input:
        result["모델별 집계"] = fuel_df.groupby("CAR_MOEL_DT")["CNT"].sum().sort_values(ascending=False).to_string()

    # 디폴트: 아무 키워드 없으면 전부 보여줌
    if not result:
        result["연령별 집계"] = fuel_df.groupby("AGE")["CNT"].sum().to_string()
        result["국산/수입 세그먼트별 집계"] = fuel_df.groupby("CL_HMMD_IMP_SE_NM")["CNT"].sum().to_string()
        result["브랜드별 집계"] = fuel_df.groupby("ORG_CAR_MAKER_KOR")["CNT"].sum().sort_values(ascending=False).to_string()
        result["모델별 집계"] = fuel_df.groupby("CAR_MOEL_DT")["CNT"].sum().sort_values(ascending=False).to_string()

    return result


# 키워드 탐지 및 통계 추출
def detect_keyword_and_summarize(user_input):
    fuel_keywords = {
        "휘발유": "휘발유", "경유": "경유", "전기": "전기",
        "하이브리드": "하이브리드", "엘피지": "엘피지", "LPG": "엘피지"
    }
    category_keywords = {
        "연령": "AGE",
        "연령대": "AGE",
        "국산": "CL_HMMD_IMP_SE_NM",
        "수입": "CL_HMMD_IMP_SE_NM",
        "브랜드": "ORG_CAR_MAKER_KOR",
        "제조사": "ORG_CAR_MAKER_KOR",
        "모델": "CAR_MOEL_DT",
        "차종": "CAR_MOEL_DT"
    }

    fuel = None
    for key, val in fuel_keywords.items():
        if key in user_input:
            fuel = val
            break

    category = None
    for key, val in category_keywords.items():
        if key in user_input:
            category = val
            break

    if fuel and category:
        filtered = df_new[df_new["FUEL"] == fuel]
        summary = filtered.groupby(category)["CNT"].sum().sort_values(ascending=False).to_string()
        return summary

    return None


# 초기 메시지
st.title("💬 Chatbot")
st.caption("chatbot powered by OpenAI")
st.caption("해당 서비스는 GPT API 토큰 보유 시 사용 가능합니다.")

# 채팅 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "안녕하세요. 자동차 전문가 페페에요! 2024년 국내 자동차 시장에 대해 물어보시면 답변드릴게요!"}
    ]

for msg in st.session_state["messages"]:
    st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "🙋‍♂️").write(msg["content"])

if prompt := st.chat_input("궁금한 내용을 입력하세요! 예: '전기차 연령별 신차 등록 수'"):
    if not openai_api_key:
        st.warning("❗ OpenAI API 키를 입력해주세요.")
        st.stop()

    client = OpenAI(api_key=openai_api_key)

    summary = detect_keyword_and_summarize(prompt)
    if summary:
        system_prompt = f"""너는 자동차 등록 통계를 설명하는 데이터 전문가야.
    다음 통계 요약을 기반으로 사용자 질문에 대해 친절하게 설명해줘:\n\n{summary}"""
    else:
        system_prompt = """너는 자동차 등록 통계를 설명하는 데이터 전문가야.
    사용자가 제공한 질문에서 핵심 키워드를 찾지 못했어.
    자동차 통계와 관련된 일반적인 정보를 설명해주고, 아래 사이트도 함께 참고하라고 안내해줘:
    - [카차트 통계 시각화 플랫폼](https://carcharts-free.carisyou.net/?utm_source=Carisyou&utm_medium=Banner&utm_campaign=P03_PC_Free&)
    - 또는 [CARISYOU 자동차 사이트](https://www.carisyou.com/)
    """

    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user", avatar="🙋‍♂️").write(prompt)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
    )

    reply = response.choices[0].message.content
    st.session_state["messages"].append({"role": "assistant", "content": reply})
    st.chat_message("assistant", avatar="🤖").write(reply)