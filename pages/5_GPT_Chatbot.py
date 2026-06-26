import streamlit as st
st.set_page_config(page_title="Chatbot", layout="wide", initial_sidebar_state="auto")

from app_core.nav import render_sidebar_nav
render_sidebar_nav()

# 사이드바: API 키만
with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key (선택)", key="chatbot_api_key", type="password")
    st.caption("키가 없어도 로컬 집계로 답합니다. 키가 있으면 설명 문장만 LLM이 작성합니다.")

from app_core import chatbot_engine as eng

# 1) 컨텍스트 로드
ctx = eng.load_context()
frames, colmaps = ctx["frames"], ctx["colmaps"]
has_er_detail, catalog = ctx["has_er_detail"], ctx["catalog"]

# 2) UI
st.title("💬 데이터 기반 Chatbot")
st.caption("자연어 질의를 내부 데이터로 해석해 집계/상세 정보를 제공합니다.")

# 채팅 로그
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role":"assistant","content":"예) '2025년 7월 신규 대수', '신규 전기차 SUV 차급별 상위 5', '기아 카니발 알려줘'"},
    ]
for m in st.session_state["messages"]:
    st.chat_message(m["role"], avatar="🤖" if m["role"]=="assistant" else "🙋‍♂️").write(m["content"])

# 3) 입력 처리
if q := st.chat_input("무엇이 궁금하세요?"):
    st.chat_message("user", avatar="🙋‍♂️").write(q)
    st.session_state["messages"].append({"role":"user","content":q})

    # ✅ 스펙 의도 감지
    is_spec, b_like, m_like = eng.detect_spec_intent(q, catalog)
    if is_spec:
        # ⬇️ 누적 상세 + 신규(세그) 합집합으로 스펙 생성
        spec_df = eng.vehicle_specs_from_sources(
            frames=frames,
            colmaps=colmaps,
            brand_like=b_like,
            model_like=m_like,
            include=("누적 상세", "신규(세그)")   # 원하면 모든 세그로 확장 가능
        )
        st.chat_message("assistant", avatar="📙").write("차종 스펙 정보")
        st.dataframe(spec_df, use_container_width=True)
        st.session_state["messages"].append({"role":"assistant","content":"차종 스펙 정보를 표시했습니다."})
        raise st.stop()

    # 1) (스펙이 아니면) 기존처럼 소스 결정 → 플랜 생성 → 집계/표시
    source0 = eng.detect_source(q, has_er_detail)
    plan    = eng.parse_query(q, source0, catalog)
    source  = eng.route_source(q, source0, plan, colmaps, has_er_detail)

    try:
        df_out, meta = eng.execute(frames[source], plan, colmaps[source], source)

        st.subheader("📊 집계 결과")
        st.dataframe(df_out, use_container_width=True)
        fig = eng.make_chart(df_out)
        if fig is None and not df_out.empty:
            st.metric("합계(대수)", f"{int(df_out.iloc[0]['대수']):,}")
        elif fig is not None:
            st.plotly_chart(fig, use_container_width=True)

        if openai_api_key:
            answer = eng.llm_explain(plan, df_out, q, openai_api_key)
        else:
            if df_out.empty:
                answer = "요청 조건에 해당하는 결과가 없습니다."
            elif df_out.shape[0] == 1:
                answer = f"요청하신 조건의 합계는 {int(df_out.iloc[0]['대수']):,}대입니다."
            else:
                head = df_out.iloc[0]
                total = int(df_out['대수'].sum())
                share = 100.0 * int(head['대수']) / total if total else 0.0
                answer = f"가장 큰 항목은 '{head['구분']}'({int(head['대수']):,}대)로, 표 합계 대비 약 {share:.1f}%입니다."

        st.chat_message("assistant", avatar="🤖").write(answer)

        # 기존 요구사항대로 조건 요약만 노출(플랜/필터 원본 JSON은 비노출)
        st.chat_message("assistant", avatar="🧭").markdown(eng.render_condition_summary(meta))

        st.session_state["messages"] += [
            {"role":"assistant","content":answer},
            {"role":"assistant","content":eng.render_condition_summary(meta)},
        ]

        # (원하면 여기서 스펙도 추가로 보여줄 수 있지만,
        #  지금은 '스펙 의도'가 아니므로 기본 집계 흐름만 유지)

    except Exception as e:
        err = f"질의 처리 중 오류: {e}"
        st.chat_message("assistant", avatar="🤖").error(err)
        st.session_state["messages"].append({"role":"assistant","content":err})
