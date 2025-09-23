import streamlit as st
from app_core.nav import render_sidebar_nav

st.set_page_config(page_title="Log in", layout="wide")
st.title("Log in")
render_sidebar_nav()
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

with st.form("login_form"):
    user = st.text_input("ID")
    pw = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Log in")

if submitted:
    # TODO: 실제 인증 로직으로 교체
    if user and pw:
        st.session_state.logged_in = True
        st.success("로그인되었습니다.")
        st.switch_page("pages/1_Overview.py")
    else:
        st.error("ID/Password를 입력하세요.")
