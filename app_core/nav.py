# nav.py
import streamlit as st

def render_sidebar_nav():
    # 세션 키 안전 초기화
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    with st.sidebar:
        st.caption("APP MENU")

        # HOME
        st.subheader("HOME")
        st.page_link("pages/1_Overview.py", label="Overview", icon="📊")
        st.page_link("pages/2_New_Regist_summary.py", label="New Regist summary", icon="🚗")
        st.page_link("pages/3_Erase_Regist_summary.py", label="Erase Regist summary", icon="🗑️")

        # Contents (로그인 여부와 무관하게 노출하고 싶다면 여기 둠)
        st.subheader("Contents")
        st.page_link("pages/4_GPT_Chatbot.py", label="Chat Bot", icon="💬")
        st.page_link("pages/5_ab_test_platform.py", label="A/B Test", icon="🆎")

        # Durability Project (로그인한 경우에만 노출)
        if st.session_state.get("logged_in", False):
            st.subheader("Durability Project")
            st.page_link("pages/6_PV_ANALYSIS.py", label="PV ANALYSIS", icon="📈")
            st.page_link("pages/7_PV_FRST_YEAR_DATASET.py", label="PV FRST YEAR DATASET", icon="🗂️")
            st.page_link("pages/8_PV_MA_GRAPH.py", label="PV MA GRAPH", icon="📊")
            st.page_link("pages/9_CV_ANALYSIS.py", label="CV ANALYSIS", icon="🧮")
        # else:  # 아예 숨김. 힌트를 주고 싶으면 이쪽에 캡션으로 "로그인 후 이용 가능" 정도 표시해도 OK

        # Account
        st.subheader("Account")
        if st.session_state.get("logged_in", False):
            st.page_link("pages/11_log_out.py", label="Log out", icon="🚪")
        else:
            st.page_link("pages/10_log_in.py", label="Log in", icon="🔐")
