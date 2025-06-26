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
st.dataframe(ersr_df.describe().iloc[0:3,1],column_config=col_config, width= 400)
st.markdown(
    """
    <style>
    [data-testid="stMetricLabel"] p {
        font-size: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
truck, bus, special = st.columns(3)
truck.metric(":truck: 트럭", format(cnt[0],','),border = True)
bus.metric(":bus: 버스", format(cnt[1],','),border = True)
special.metric(":articulated_lorry: 특장차", format(cnt[2],','),border = True)
# https://emojiterra.com/bus/ 이모지 사이트
df_tr = ersr_df[ersr_df['CAR_MOEL_DT'] =='트럭']
df_bus = ersr_df[ersr_df['CAR_MOEL_DT'] =='버스']
df_spe = ersr_df[ersr_df['CAR_MOEL_DT'] =='특장차']

# 데이터프레임 강조 색 채우기
def draw_color_at_value(x, color):
    color = f'background-color:{color}'
    is_val = x > 0
    return [color if b else '' for b in is_val]

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
        pivot = pivot.fillna("0").astype('int')
        pivot = pivot.style.apply(draw_color_at_value, color='#00dac4', axis=0)
        st.markdown(f"- Upper Outlier(사용연수 {upper_fence} 이상)")
        st.dataframe(pivot, column_config=col_config2, width= 700)
    fig_scat_tr = px.scatter(df_tr, x='UY', y='TRVL_DSTNC', color='ORG_CAR_MAKER_KOR', trendline="ols",
                              title='주행거리 / 사용연수 산점도')
    st.plotly_chart(fig_scat_tr, use_container_width=True)
    st.markdown("- 트럭의 내구성 분석에 주행거리는 연관이 없음을 확인 할 수 있음")
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
    #left4, right4 = st.columns([2, 2], gap="large")
    tmp_bus2 = tmp_bus[tmp_bus['1YperD'] <= 400000]
    fig_scat_bus = px.scatter(tmp_bus2, x='1YperD', y='TRVL_DSTNC', color='ORG_CAR_MAKER_KOR', trendline="ols",title='주행거리 / 1년 환산 주행거리(40만km 이하) 산점도')
    st.plotly_chart(fig_scat_bus, use_container_width=True)

    fig_scat_bus2 = px.scatter(tmp_bus2, x='UY', y='TRVL_DSTNC', color='ORG_CAR_MAKER_KOR', trendline="ols",title='주행거리 / 사용연수 산점도')
    st.plotly_chart(fig_scat_bus2, use_container_width=True)
    st.markdown("- 버스의 내구성 분석에 주행거리는 연관이 없음을 확인 할 수 있음")
with tab3:
    use = df_spe['CAR_USE'].unique().tolist()
    use.insert(0,'전체')
    name = st.selectbox("용도", use)
    if name == '전체':
        tmp_spe = df_spe.copy()
    else:
        tmp_spe = df_spe[df_spe['CAR_USE'] == name]
    fig_hist_spe = px.histogram(tmp_spe, x='UY', color_discrete_sequence=['#00dac4'])
    st.plotly_chart(fig_hist_spe, use_container_width=True)
    #spe_pivo = pd.pivot_table(tmp_spe, index=['CL_HMMD_IMP_SE_NM','ORG_CAR_MAKER_KOR','CAR_USE_DETAL'],values='UY',aggfunc='count').sort_values(by='UY',ascending = False)
    spe_pivo = pd.pivot_table(tmp_spe, index=['ORG_CAR_MAKER_KOR'],columns='UY',aggfunc='count')['CAR_MOEL_DT']
    col_config3 = {"ORG_CAR_MAKER_KOR": "브랜드"
                   }
    spe_pivo = spe_pivo.fillna("0").astype('int')
    spe_pivo = spe_pivo.style.apply(draw_color_at_value, color='#00dac4', axis=0)
    st.dataframe(spe_pivo, column_config=col_config3, width= 1400)
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
<center> &copy; 2023. SJAhn. All rights reserved. |  <a href="https://carcharts.carisyou.net/" target=_blank><img src="data:image/png;base64,{base64.b64encode(data).decode()}" class='img-fluid' style = "width:75px; height:25px;"> </center>
</div>

"""

st.markdown(footer,unsafe_allow_html=True)