import streamlit as st
import pandas as pd
import plotly.express as px
import base64



# ersr_over = pd.read_csv('./data/해외말소1507_2406.csv')
# ersr_over['EXTRACT_DE'] = ersr_over['EXTRACT_DE'].astype('str')
# ersr_over['EXTRACT_DE'] = pd.to_datetime(ersr_over['EXTRACT_DE'])
# ersr_over['MAX_AVG_TRVL'] = round(ersr_over['TRVL'] * ersr_over['USE_YEAR'], -3)
# trvl_over = ersr_over.pivot(index='EXTRACT_DE', columns='ORG_CAR_MAKER_KOR', values='MAX_AVG_TRVL')
# trvl_over = trvl_over.reset_index()
# trvl_over.dropna(axis=1, inplace=True)

# ersr_na = pd.read_csv('./data/국내말소1507_2406.csv')
# ersr_na['EXTRACT_DE'] = ersr_na['EXTRACT_DE'].astype('str')
# ersr_na['EXTRACT_DE'] = pd.to_datetime(ersr_na['EXTRACT_DE'])
# ersr_na['MAX_AVG_TRVL'] = round(ersr_na['TRVL'] * ersr_na['USE_YEAR'], -3)
# trvl_na = ersr_na.pivot(index='EXTRACT_DE', columns='ORG_CAR_MAKER_KOR', values='MAX_AVG_TRVL')
# trvl_na = trvl_na.reset_index()
# trvl_na.dropna(axis=1, inplace=True)

df = pd.read_csv('./data/이평선용.csv')

st.set_page_config(page_title= "[카이즈유] 승용차 이동평균 그래프", layout="wide", initial_sidebar_state="auto")

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