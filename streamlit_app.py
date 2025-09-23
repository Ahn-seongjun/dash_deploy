# streamlit_app.py
import streamlit as st
from app_core.constants import APP_TITLE
from app_core.nav import render_sidebar_nav
st.set_page_config(page_title=APP_TITLE, layout="wide")

try:
    st.switch_page("pages/1_Overview.py")  # 지원되는 버전에서만 동작
except Exception:
    st.write("사이드바에서 Overview를 선택하세요.")
render_sidebar_nav()
# 세션 상태 초기화
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# 로그인 상태 표시(선택)
#status = "✅ Logged In" if st.session_state.logged_in else "🔒 Logged Out"
#st.caption(f"Status: {status}")
#st.page_link("pages/1_Overview.py", label="Overview", icon="📊")
