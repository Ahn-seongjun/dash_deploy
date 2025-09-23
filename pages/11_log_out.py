import streamlit as st
from app_core.nav import render_sidebar_nav

st.set_page_config(page_title="Log out", layout="wide")
render_sidebar_nav()
# 세션키 보정
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# 로그아웃 처리
st.session_state.logged_in = False

# # (선택) 세션 키/캐시 정리
# for k in ("new_seg1","new_seg2","used_seg1","used_seg2","ersr_seg1","ersr_seg2"):
#     st.session_state.pop(k, None)
# try:
#     st.cache_data.clear()
#     st.cache_resource.clear()
# except Exception:
#     pass

# 바로 Overview로 이동
st.switch_page("pages/1_Overview.py")