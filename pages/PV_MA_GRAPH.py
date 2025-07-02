import streamlit as st
import pandas as pd
import plotly.express as px
import base64


df = pd.read_csv('./data/이평선용.csv')

st.set_page_config(page_title= "[카이즈유] 승용차 이동평균 그래프", layout="wide", initial_sidebar_state="auto")

# summary = st.Page(
#     "summary.py", title="New Regist summary", icon=":material/dashboard:")
# pv_ana = st.Page(
#     "pages/PV_ANALYSIS.py", title="PV ANALYSIS", icon=":material/dashboard:")
# pv_frst = st.Page("pages/PV_FRST_YEAR_DATASET.py", title="PV FRST YEAR DATASET", icon=":material/dataset:")
# pv_ma = st.Page(
#     "pages/PV_MA_GRAPH.py", title="PV MA GRAPH", icon=":material/ssid_chart:", default=True
# )
# cv_ana = st.Page("pages/CV_ANALYSIS.py", title="CV ANALYSIS", icon=":material/dashboard:")
# # (icon search) https://fonts.google.com/icons?selected=Material+Symbols+Outlined:docs:FILL@0;wght@400;GRAD@0;opsz@24&icon.size=24&icon.color=%231f1f1f
# pg = st.navigation(
#         {
#             "pages": [summary],
#             "ERSR Analysis": [pv_ana,pv_frst,pv_ma,cv_ana]
#         }
#     )
# pg.run()
with st.sidebar:
    st.write("CARISYOU DATALAB")
    st.link_button("CarCharts Free","https://carcharts-free.carisyou.net/")

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



with open('./assets/carcharts.png', "rb") as f:
    data = f.read()


footer=f"""<style>
.footer {{
position: fixed;
left: 0;
bottom: 0;
width: 100%;
height : 30px;
background-color: white;
color: black;
border-width : 5px;
border-color : gray white white white;
border-style:double none none none;
text-align: center;

}}
</style>

<div class="footer">
<center> &copy; 2023. SJAhn. All rights reserved. |  <a href="https://carcharts.carisyou.net/" target=_blank><img src="data:image/png;base64,{base64.b64encode(data).decode()}" class='img-fluid' style = "width:75px; height:25px;"> </center>
</div>

"""


st.markdown(footer,unsafe_allow_html=True)

# streamlit run summary.py