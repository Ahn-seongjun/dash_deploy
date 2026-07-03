import streamlit as st

from app_core.constants import APP_TITLE
from app_core.nav import render_sidebar_nav

st.set_page_config(page_title=APP_TITLE, layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

render_sidebar_nav()

st.title(APP_TITLE)
st.markdown(
    "사이드바 또는 아래 링크를 통해 대시보드로 이동할 수 있습니다."
)

col1, col2, col3 = st.columns(3)
with col1:
    st.page_link("pages/1_Overview.py", label="Overview 열기", icon="📊")
with col2:
    st.page_link("pages/2_New_Regist_summary.py", label="New Regist summary", icon="🚗")
with col3:
    st.page_link("pages/3_Erase_Regist_summary.py", label="Erase Regist summary", icon="🗑️")
