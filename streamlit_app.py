import streamlit as st

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


def login():
    if st.button("Log in"):
        st.session_state.logged_in = True
        st.rerun()


def logout():
    st.session_state.logged_in = False
    st.rerun()

#login_page = st.Page(login, title="Log in", icon=":material/login:")

# HOME
new_summary = st.Page(
    "summary_pages/new_reg_summary.py", title="New Regist summary", icon=":material/dashboard:", default=True)
ersr_summary = st.Page(
    "summary_pages/ersr_reg_summary.py", title="Erase Regist summary", icon=":material/dashboard:")

# TF ANALYSIS
pv_ana = st.Page(
    "dur_pages/PV_ANALYSIS.py", title="PV ANALYSIS", icon=":material/dashboard:")
pv_frst = st.Page("dur_pages/PV_FRST_YEAR_DATASET.py", title="PV FRST YEAR DATASET", icon=":material/dataset:")
pv_ma = st.Page(
    "dur_pages/PV_MA_GRAPH.py", title="PV MA GRAPH", icon=":material/ssid_chart:"
)
cv_ana = st.Page("dur_pages/CV_ANALYSIS.py", title="CV ANALYSIS", icon=":material/dashboard:")

# CONTENTS
ab_ana = st.Page("contents_pages/ab_test_platform.py", title="AB TEST", icon=":material/analytics:")
chatbot = st.Page("contents_pages/GPT Chatbot.py", title="Chat Bot", icon=":material/chat:")

# TEST
test = st.Page("test_pages/tab_testpage.py", title="Test Page", icon=":material/experiment:")

# ACCOUNT
login = st.Page("account_pages/login_page.py", title="Log in", icon=":material/login:")
#signup = st.Page("pages/signup_page.py", title="Sign up", icon=":material/add:")  # 임시 회원가입 페이지
logout = st.Page(logout, title="Log out", icon=":material/logout:")
# (icon search) https://fonts.google.com/icons?selected=Material+Symbols+Outlined:docs:FILL@0;wght@400;GRAD@0;opsz@24&icon.size=24&icon.color=%231f1f1f
# 로그인 여부에 따라 다른 네비게이션 구성
if st.session_state.logged_in:
    pg = st.navigation(
        {
            "HOME": [new_summary,ersr_summary],
            "Durability Project": [pv_ana, pv_frst, pv_ma, cv_ana],
            "Contents": [ab_ana,chatbot],
            "Test" : [test],
            "Account": [logout]
        }
    )
else:
    pg = st.navigation(
        {
            "HOME": [new_summary,ersr_summary],
            "Contents": [ab_ana,chatbot],
            "Test" : [test],
            "Account": [login]#, signup]
        }
    )

pg.run()