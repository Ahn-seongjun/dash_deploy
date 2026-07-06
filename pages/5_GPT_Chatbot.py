import streamlit as st

from app_core import chatbot_engine as eng
from app_core.nav import render_sidebar_nav


st.set_page_config(page_title="Chatbot", layout="wide", initial_sidebar_state="auto")
render_sidebar_nav()


with st.sidebar:
    st.subheader("LLM 설정")
    hf_api_token = st.text_input("Hugging Face Token", type="password", key="hf_api_token")
    model_name = st.text_input("모델명", value=eng.DEFAULT_HF_MODEL, key="hf_model_name")
    st.caption("배포 환경에서는 로컬 모델보다 Hugging Face Inference API 방식이 안정적입니다.")


st.title("데이터 기반 RAG Chatbot")
st.caption("`data/marts`에 저장된 parquet 집계데이터를 근거로 질문에 답변합니다.")

doc_df = eng.load_rag_documents()
dataset_choice = st.selectbox("조회 데이터", eng.dataset_options(doc_df), index=0)

with st.expander("현재 연결된 데이터 보기", expanded=False):
    summary_df = (
        doc_df.groupby(["source_label", "dimension_label"], as_index=False)
        .size()
        .rename(columns={"size": "문서수"})
        .sort_values(["source_label", "문서수"], ascending=[True, False])
    )
    st.dataframe(summary_df, width="stretch")


if "rag_messages" not in st.session_state:
    st.session_state["rag_messages"] = [
        {
            "role": "assistant",
            "content": "예시 질문: `2026-05 말소등록 상위 브랜드는?`, `2025-12 신규등록 하이브리드 비중은?`, `용도 데이터에서 2025년 상위 용도는?`",
        }
    ]


for message in st.session_state["rag_messages"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])


if question := st.chat_input("질문을 입력하세요"):
    st.session_state["rag_messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.spinner("관련 근거 문서를 찾는 중입니다..."):
        retrieved_df = eng.retrieve_documents(question, doc_df, source_label=dataset_choice, top_k=8)
        answer = eng.answer_with_huggingface(question, retrieved_df, hf_api_token, model_name=model_name)

    with st.chat_message("assistant"):
        st.write(answer)
        st.caption("검색된 근거")
        evidence_df = retrieved_df[["source_label", "month", "dimension_label", "label", "value"]].rename(
            columns={
                "source_label": "데이터",
                "month": "기준",
                "dimension_label": "구분축",
                "label": "항목",
                "value": "대수",
            }
        )
        st.dataframe(evidence_df, width="stretch")
        with st.expander("근거 문장 보기", expanded=False):
            for row in retrieved_df.itertuples(index=False):
                st.write(f"- {row.text}")

    st.session_state["rag_messages"].append({"role": "assistant", "content": answer})
