# streamlit_app.py
import streamlit as st
from app_core.constants import APP_TITLE

# ── (1) 반드시 최상단 첫 Streamlit 명령 ───────────────────────────────
st.set_page_config(page_title=APP_TITLE, layout="wide")

# ── (2) 세션 상태 초기화 ──────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def logout_action():
    st.session_state.logged_in = False
    st.rerun()

try:
    # 최신 API 체크 (없으면 AttributeError)
    _ = st.Page

    # ── (3) 페이지 등록 ───────────────────────────────────────────────
    # HOME
    overview     = st.Page("pages/summary/Overview.py",        title="Overview",            icon="📊", default=True)
    new_summary  = st.Page("pages/summary/new_reg_summary.py", title="New Regist summary",  icon="🚗")
    ersr_summary = st.Page("pages/summary/ersr_reg_summary.py",title="Erase Regist summary",icon="🗑️")

    # Durability
    pv_ana  = st.Page("pages/durability/PV_ANALYSIS.py",          title="PV ANALYSIS",          icon=":material/dashboard:")
    pv_frst = st.Page("pages/durability/PV_FRST_YEAR_DATASET.py", title="PV FRST YEAR DATASET", icon=":material/dataset:")
    pv_ma   = st.Page("pages/durability/PV_MA_GRAPH.py",          title="PV MA GRAPH",          icon=":material/ssid_chart:")
    cv_ana  = st.Page("pages/durability/CV_ANALYSIS.py",          title="CV ANALYSIS",          icon=":material/dashboard:")

    # Contents
    ab_ana  = st.Page("pages/contents/ab_test_platform.py", title="AB TEST",  icon=":material/analytics:")
    chatbot = st.Page("pages/contents/GPT Chatbot.py",      title="Chat Bot", icon=":material/chat:")

    # Account
    login_pg    = st.Page("pages/account/login_page.py", title="Log in",  icon=":material/login:")
    logout_page = st.Page(logout_action,                 title="Log out", icon=":material/logout:")

    # ── (4) 네비게이션(로그인 여부에 따라 그룹 구성) ──────────────────
    if st.session_state.logged_in:
        pg = st.navigation({
            "HOME": [overview, new_summary, ersr_summary],
            "Durability Project": [pv_ana, pv_frst, pv_ma, cv_ana],
            "Contents": [ab_ana, chatbot],
            "Account": [logout_page],
        })
    else:
        pg = st.navigation({
            "HOME": [overview, new_summary, ersr_summary],
            "Contents": [ab_ana, chatbot],
            "Account": [login_pg],
        })

    pg.run()

except AttributeError:
    st.error(
        "이 앱은 Streamlit의 `st.Page`/`st.navigation` API에 의존합니다. "
        "현재 환경에서 해당 API를 찾지 못했습니다. Streamlit 버전을 확인해 주세요."
    )
except Exception as e:
    # 조용히 삼키지 말고 화면에 예외 표시 (초기 진입 UX 착시 방지)
    st.exception(e)
