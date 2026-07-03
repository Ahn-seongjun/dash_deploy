# streamlit_app.py
import streamlit as st

from app_core.constants import APP_TITLE
from app_core.nav import render_sidebar_nav

st.set_page_config(page_title=APP_TITLE, layout="wide")

try:
    st.switch_page("pages/1_Overview.py")
except Exception:
    st.write("사이드바에서 Overview를 선택해 주세요.")

render_sidebar_nav()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
