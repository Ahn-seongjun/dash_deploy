import streamlit as st
import pandas as pd
import plotly.express as px
from app_core import footer
from app_core import ui
from app_core.nav import render_sidebar_nav
st.set_page_config(page_title="승용 이동평균", layout="wide")
render_sidebar_nav()
# 로그인 안하면 바로 로그인페이지로
if not st.session_state.get("logged_in", False):
    st.switch_page("pages/10_Log_in.py")
df = pd.read_csv('./data/이평선용.csv')

# 사이드바
with st.sidebar:
    ui.sidebar_links()

st.markdown("## 2024년 결산 기준 최초등록월별 생존률")
st.markdown(f"- 데이터 값 산출 근거 : $생존률 = \\frac{{운행대수}}{{말소대수 + 운행대수}}$")
st.markdown("#### 이동평균 그래프 사용 방법")
st.markdown(f"- 차수 기준으로 이동평균선 조정 가능합니다.")
st.markdown(f"- 하단의 브랜드 콤보박스를 통해 브랜드 설정 가능합니다.")

number = st.slider('MA',1,36,1,1)

df['EXTRACT_DE'] = pd.to_datetime(df['EXTRACT_DE'])
st.subheader('최초등록월별 생존률 시계열 그래프')
brand1 = st.selectbox("브랜드", df.ORG_CAR_MAKER_KOR.unique().tolist())
ma_fig_na = px.scatter(df[df['ORG_CAR_MAKER_KOR'] == brand1], x="EXTRACT_DE", y='sur_rate', trendline="rolling",
                       trendline_options=dict(window=number),
                       title=f"{number}-point moving average")
st.plotly_chart(ma_fig_na, use_container_width=True)

footer.render()