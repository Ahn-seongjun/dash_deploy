import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')
import base64
from datetime import datetime, timedelta
import calendar

st.set_page_config(page_title= "[카이즈유] 상용차 말소분석", layout="wide", initial_sidebar_state="auto")
with st.sidebar:
    st.write("CARISYOU DATALAB")
    st.link_button("CarCharts Free","https://carcharts-free.carisyou.net/")

ersr_df = pd.read_csv('./data/상용차 말소분석.csv')
cnt = ersr_df['CAR_MOEL_DT'].value_counts()
st.markdown("## 상용차 말소 사용연한 기준 내구성 분석")
st.markdown(f"- 집계 기간 : 2015년 7월 ~ 2024년 6월(9개년)")
st.markdown(f"- 집계 대상 : 상용(자가용, 영업용), 말소등록데이터 자진말소(폐차)")
st.markdown(f"- 제외 대상 : 트레일러")

col_config = {"UY": "사용연수 기술통계량"}
st.dataframe(ersr_df.describe().iloc[0:3,1],column_config=col_config)
truck, bus, special = st.columns(3)
truck.metric(":truck: 트럭", format(cnt[0],','))
bus.metric(":oncoming_bus: 버스", format(cnt[1],','))
special.metric(":articulated_lorry: 특장차", format(cnt[2],','))

df_tr = ersr_df[ersr_df['CAR_MOEL_DT'] =='트럭']
df_bus = ersr_df[ersr_df['CAR_MOEL_DT'] =='버스']
df_spe = ersr_df[ersr_df['CAR_MOEL_DT'] =='특장차']

st.header(" 상용차 분류")
tab1, tab2, tab3 = st.tabs(['트럭','버스','특장차'])
with tab1:
    left1, right1 = st.columns([2, 2], gap="large")
    with left1:
        fig_hist = px.histogram(df_tr, x='UY', color_discrete_sequence = ['#00dac4'])
        st.plotly_chart(fig_hist, use_container_width=True)
    with right1:
        fig_tr = go.Figure()
        fig_tr.add_trace(go.Box(

            y=df_tr['UY'],
            name='사용연수 Boxplot',
            marker_color='#00dac4',
            boxmean=True  # represent mean
        ))

        st.plotly_chart(fig_tr, use_container_width=True)
    left2, right2 = st.columns([2,2], gap="large")
    with right2:
        Q1 = df_tr["UY"].quantile(0.25)
        Q3 = df_tr["UY"].quantile(0.75)
        iqr = Q3 - Q1
        upper_fence = Q3 + 1.5 * iqr
        df_tr['BIN'] = ''
        df_tr['BIN'] = df_tr['UY'].apply(lambda x: x // 10)
        tmp = df_tr[df_tr["UY"] >= upper_fence]
        col_config2 = {"CL_HMMD_IMP_SE_NM": "국산/수입",
                       "ORG_CAR_MAKER_KOR": "브랜드",
                       "CAR_MODEL_KOR": "상세모델",
                       "3": "30's",
                       "4": "40's",
                       "5": "50's",
                       "All": "총계"}
        pivot = tmp.pivot_table('UY', index=['CL_HMMD_IMP_SE_NM', 'ORG_CAR_MAKER_KOR','CAR_MODEL_KOR'], columns = "BIN",aggfunc='count', margins=True)
        st.markdown(f"- Upper Outlier(사용연수 {upper_fence} 이상)")
        st.dataframe(pivot, column_config=col_config2, width= 700)
with tab2:
    prpos = ['전체', '자가용', '영업용']
    name = st.selectbox("등록용도", prpos)
    df_bus['1YperD'] = round(df_bus['TRVL_DSTNC']/df_bus['UY'],-3)
    if name == '전체':
        tmp_bus = df_bus.copy()
    else:
        tmp_bus = df_bus[df_bus['PRPOS_SE_NM'] == name]
    fig_hist_bus = px.histogram(tmp_bus, x='UY', color_discrete_sequence=['#00dac4'])
    st.plotly_chart(fig_hist_bus, use_container_width=True)


    left3, right3 = st.columns([2, 2], gap="large")
    with left3:
        fig_box_bus = go.Figure()
        fig_box_bus.add_trace(go.Box(

            y=tmp_bus['UY'],
            name='사용연수 Boxplot',
            marker_color='#00dac4',
            boxmean=True  # represent mean
        ))
        st.plotly_chart(fig_box_bus, use_container_width=True)
    with right3:
        fig_trvl_bus = go.Figure()
        fig_trvl_bus.add_trace(go.Box(

            y=tmp_bus[tmp_bus['1YperD']<= 400000]['TRVL_DSTNC'],
            name='주행거리 Boxplot',
            marker_color='#00dac4',
            boxmean=True  # represent mean
        ))
        st.plotly_chart(fig_trvl_bus, use_container_width=True)
        st.markdown("- 1년 환산 주행거리 40만km 이하를 대상으로 집계함")
        st.markdown("- 1년 환산 주행거리 산출근거 : 주행거리/사용연수")
with tab3:
    st.dataframe(df_spe)
left1, right1 = st.columns([2,2], gap="large")







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
<center> Copyright &copy; All rights reserved |  <a href="https://carcharts.carisyou.net/" target=_blank><img src="data:image/png;base64,{base64.b64encode(data).decode()}" class='img-fluid' style = "width:75px; height:25px;"> </center>
</div>

"""

st.markdown(footer,unsafe_allow_html=True)