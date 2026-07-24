import streamlit as st


def render_sidebar_nav():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    with st.sidebar:
        st.subheader("HOME")
        st.page_link("pages/1_Overview.py", label="Overview", icon="📊")
        st.page_link("pages/2_New_Regist_summary.py", label="New Regist summary", icon="🚗")
        st.page_link("pages/4_Used_Regist_summary.py", label="Used Regist summary", icon="🔄")
        st.page_link("pages/3_Erase_Regist_summary.py", label="Erase Regist summary", icon="🗑️")

        st.subheader("Contents")
        st.page_link("pages/5_GPT_Chatbot.py", label="Chat Bot", icon="🤖")
        st.page_link("pages/6_ab_test_platform.py", label="A/B Test", icon="🧪")
