import streamlit as st
import pandas as pd
import plotly.express as px
import warnings
warnings.filterwarnings('ignore')
import base64
import plotly.graph_objects as go
from plotly.subplots import make_subplots


st.set_page_config(page_title= "[카이즈유] 자동차 등록데이터", layout="wide", initial_sidebar_state="auto")

df = pd.read_csv('./data/2024년 말소데이터.csv')
df['val'] = '1'
df['val'] = df['val'].astype('int')
df['EXTRACT_DE'] = df['EXTRACT_DE'].astype('str')
df['EXTRACT_DE'] = pd.to_datetime(df['EXTRACT_DE'])
# 단순 대수 전처리
reg = format(len(df), ',d')


# 사이드바 메뉴 설정
with st.sidebar:
    st.write("CARISYOU DATALAB")
    st.link_button("CarCharts Free", "https://carcharts-free.carisyou.net/")


st.markdown("## 2024 Yearly Summary")
st.markdown(f"### 2024년 자진말소(폐차) 등록대수 : {reg}")
st.markdown("- 승용차 대상 집계")
st.markdown('- 말소 등록 : 자진말소(폐차)')


fuel = st.selectbox("연료", df['연료'].unique().tolist())
# 월별 등록대수 및 증감률 전처리 및 그래프
er_pivo = pd.pivot_table(df,
              index = 'EXTRACT_DE',
              columns = '연료',
              values = 'val',
              aggfunc = 'sum')

er_pivo[f'{fuel}-1년'] = er_pivo[fuel].shift(1)
er_pivo[f'{fuel}_증감'] = ((er_pivo[fuel]-er_pivo[f'{fuel}-1년'])/er_pivo[f'{fuel}-1년'])*100


# 이중 Y축 그래프 만들기
mon_reg = make_subplots(specs=[[{"secondary_y": True}]])

# 첫 번째 Y축: 바 차트 (말소대수)
# Bar: 말소대수
mon_reg.add_trace(
    go.Bar(
        x=er_pivo.index,
        y=er_pivo[fuel],
        name=f'{fuel} 말소대수',
        marker_color='lightblue',
        hovertemplate='%{x}<extra></extra><br>%{y:,.0f}대'
    ),
    secondary_y=False,
)

# 두 번째 Y축: 선 그래프 (전년대비 증감률)
mon_reg.add_trace(
    go.Scatter(
        x=er_pivo.index,
        y=er_pivo[f'{fuel}_증감'],
        name='전월대비 증감률(%)',
        mode='lines+markers',
        line=dict(dash='dash', color='red'),
        marker=dict(size=10),
        hovertemplate='%{x}<extra></extra><br>%{y}%'
    ),
    secondary_y=True,
)

# 레이아웃 설정
mon_reg.update_layout(
    title=f'{fuel} 차량 말소 대수 및 증감률',
    xaxis_title='2024년',
    yaxis_title='말소대수',
    legend=dict(x=0.01, y=0.99),
    template='plotly_white'

)

mon_reg.update_yaxes(title_text='말소대수', secondary_y=False)
mon_reg.update_yaxes(title_text='증감률(%)', secondary_y=True)

st.plotly_chart(mon_reg, use_container_width=True)

tab1, tab2 = st.tabs(['bar','line'])

midleft_column, midright_column = st.columns([2,2], gap="large")
botleft_column, botright_column = st.columns(2, gap="large")
bot2left, bot2right = st.columns(2, gap="large")
bot3le,bot3ri = st.columns(2, gap="large")

# with tab1:
#
# with tab2:
#
#
# with midleft_column:
#
#
# with midright_column:
#
# with botleft_column:
#
# with botright_column:
#
# with bot3le:
#
# with bot3ri:







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
# https://data-science-at-swast-handover-poc-handover-yfa2kz.streamlit.app/
# 위에 이거 함 드가서 코드 훔쳐오자