import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')
import base64
from datetime import datetime,timedelta
from dateutil.relativedelta import *

st.set_page_config(page_title= "[카이즈유] 자동차 등록데이터", layout="wide", initial_sidebar_state="auto")
# df_bar = pd.read_csv('./data/simple_monthly_cnt.csv')
df = pd.read_csv('./data/202508monthly_cnt.csv', index_col=0)
top = pd.read_csv('./data/202508_top.csv', index_col=0)
mon_cnt = pd.read_csv('./data/24_25_moncnt.csv', index_col=0)
# df_use = pd.read_csv('./data/12-24누적 용도별 등록대수.csv')
# 전년, 전월대비 계산
def cal(x,y):
    result = round((x-y)/y,2)
    return result

today = datetime.today()
month_ago = datetime(today.year, today.month, today.day) + relativedelta(months= -1)
year =  today.year
month = "{}".format(month_ago.strftime('%m'))

# 사이드바 메뉴 설정
with st.sidebar:
    st.write("CARISYOU DATALAB")
    st.link_button("CarCharts Free", "https://carcharts-free.carisyou.net/")


st.header(f"Summary")
st.markdown(f"## {year}년 {month}월 기준 자동차 등록 요약")
cal(df['NEW_CNT'][202508],df['NEW_CNT'][202507])
st.markdown('### 월간 승용차 등록 집계',help = '전월대비 증감')

new, used, ersr, op = st.columns(4)
new.metric("신규 등록", format(df['NEW_CNT'][202508],','),f"{cal(df['NEW_CNT'][202508], df['NEW_CNT'][202507])}%",border = True)
used.metric("이전 등록", format(df['USED_CNT'][202508],','),f"{cal(df['USED_CNT'][202508], df['USED_CNT'][202507])}%",border = True)
ersr.metric("말소 등록", format(df['ERSR_CNT'][202508],','),f"{cal(df['ERSR_CNT'][202508], df['ERSR_CNT'][202507])}%",border = True)
op.metric("운행 등록", format(int(26434579),','),f"{cal(26434579, 26425398)}%",border = True)

col1, col2 = st.columns([2,2], gap="large")
with col1:
    st.subheader('국산 모델 TOP 10')
    na_top = top[top['CL_HMMD_IMP_SE_NM']=='국산'].iloc[:,:4]
    na_top.rename(columns={'RN': '순위', 'ORG_CAR_MAKER_KOR': '브랜드', 'CAR_MOEL_DT': '모델', 'CNT': '대수'}, inplace=True)
    na_top = na_top.set_index("순위")
    na_top["대수"] = na_top["대수"].map("{:,}".format)
    st.dataframe(na_top, use_container_width=True)


with col2:
    st.subheader('수입 모델 TOP 10')
    im_top = top[top['CL_HMMD_IMP_SE_NM'] == '수입'].iloc[:,:4]
    im_top.rename(columns={'RN': '순위', 'ORG_CAR_MAKER_KOR': '브랜드', 'CAR_MOEL_DT': '모델', 'CNT': '대수'}, inplace=True)
    im_top = im_top.set_index("순위")
    im_top["대수"] = im_top["대수"].map("{:,}".format)
    st.dataframe(im_top, use_container_width=True)

st.markdown(
    """
    <style>
    .stTabs [role="tablist"] {
        gap: 6px;
    }
    
    .stTabs [data-baseweb="tab"],
    .stTabs [data-baseweb="tab"] > div,
    .stTabs [data-baseweb="tab"] p,
    .stTabs button[role="tab"] {
        font-size: 18px !important;
        font-weight: 700 !important;
        font-family: 'Arial', sans-serif !important;
        color: #333333 !important;
        padding: 8px 14px !important;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"],
    .stTabs button[role="tab"][aria-selected="true"] {
        color: #ffffff !important;
        background-color: #00dac4 !important;
        border-radius: 8px 8px 0 0 !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover,
    .stTabs button[role="tab"]:hover {
        background-color: #e9f2fb !important;
    }
    </style>
    """, unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(['신규','이전','말소'])

with tab1:
    st.subheader('신규등록 추이 및 전년 비교')
    st.markdown("- 이삿짐, 부활차 제외")
    # 전년대비 산출
    mon_cnt['MON'] = mon_cnt['MON'].astype(int)
    mon_cnt['YEA'] = mon_cnt['YEA'].astype(int)
    pvt_new = mon_cnt.pivot_table(index='MON', columns='YEA', values='NEW_CNT', aggfunc='sum')
    latest_year = pvt_new.columns.max()
    prev_year = latest_year - 1
    yoy_new = (pvt_new[latest_year] - pvt_new[prev_year]) / pvt_new[prev_year] * 100
    colors = ["lightcoral" if v >= 0 else "lightskyblue" for v in yoy_new.values]
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])

    fig1.add_trace(
        go.Bar(
            x=yoy_new.index, y=yoy_new.values,
            name=f"{latest_year} 전년대비 증감률(%)",
            marker=dict(color=colors),
            text=[f"{v:.1f}%" for v in yoy_new.values],
            textposition="inside",  # <-- outside 대신 inside로 (라인 가림 최소화)
            insidetextanchor="middle",
            opacity=0.6
        ),
        secondary_y=True
    )
    line_colors = ["#1e3a8a","#00dac4"]
    for i, year in enumerate(sorted(mon_cnt['YEA'].unique())):
        df_year = mon_cnt[mon_cnt['YEA'] == year]
        fig1.add_trace(
            go.Scatter(
                x=df_year['MON'],
                y=df_year['NEW_CNT'],
                mode='lines+markers',
                name=f"{year} 등록대수",
                line=dict(width=3, color=line_colors[i % len(line_colors)]),
                marker=dict(size=7, color=line_colors[i % len(line_colors)])
            ),
            secondary_y=False
        )

    # 축 설정
    fig1.update_layout(
        hovermode="x unified",
        barmode="overlay"
    )
    fig1.update_yaxes(title_text="등록대수", secondary_y=False)
    fig1.update_yaxes(title_text="전년대비 증감률 (%)", secondary_y=True)
    fig1.update_xaxes(title_text="월")

    st.plotly_chart(fig1, use_container_width=True)
with tab2:
    st.subheader('이전등록 실거래 추이 및 전년 비교')
    st.markdown("- 매도, 알선, 개인거래 대상 집계")
    pvt_used = mon_cnt.pivot_table(index='MON', columns='YEA', values='USED_CNT', aggfunc='sum')
    latest_year = pvt_used.columns.max()
    prev_year = latest_year - 1
    yoy_used = (pvt_used[latest_year] - pvt_used[prev_year]) / pvt_used[prev_year] * 100
    colors = ["lightcoral" if v >= 0 else "lightskyblue" for v in yoy_used.values]
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])

    fig2.add_trace(
        go.Bar(
            x=yoy_used.index, y=yoy_used.values,
            name=f"{latest_year} 전년대비 증감률(%)",
            marker=dict(color=colors),
            text=[f"{v:.1f}%" for v in yoy_used.values],
            textposition="inside",  # <-- outside 대신 inside로 (라인 가림 최소화)
            insidetextanchor="middle",
            opacity=0.6
        ),
        secondary_y=True
    )
    line_colors = ["#1e3a8a", "#00dac4"]
    for i, year in enumerate(sorted(mon_cnt['YEA'].unique())):
        df_year = mon_cnt[mon_cnt['YEA'] == year]
        fig2.add_trace(
            go.Scatter(
                x=df_year['MON'],
                y=df_year['USED_CNT'],
                mode='lines+markers',
                name=f"{year} 등록대수",
                line=dict(width=3, color=line_colors[i % len(line_colors)]),
                marker=dict(size=7, color=line_colors[i % len(line_colors)])
            ),
            secondary_y=False
        )

    # 축 설정
    fig2.update_layout(
        hovermode="x unified",
        barmode="overlay"
    )
    fig2.update_yaxes(title_text="등록대수", secondary_y=False)
    fig2.update_yaxes(title_text="전년대비 증감률 (%)", secondary_y=True)
    fig2.update_xaxes(title_text="월")

    st.plotly_chart(fig2, use_container_width=True)
with tab3:
    st.subheader('말소등록 추이 및 전년 비교')
    st.markdown("- 폐차, 수출예정 대상 집계")
    pvt_er = mon_cnt.pivot_table(index='MON', columns='YEA', values='ER_CNT', aggfunc='sum')
    latest_year = pvt_er.columns.max()
    prev_year = latest_year - 1
    yoy_er = (pvt_er[latest_year] - pvt_er[prev_year]) / pvt_er[prev_year] * 100
    colors = ["lightcoral" if v >= 0 else "lightskyblue" for v in yoy_er.values]
    fig3 = make_subplots(specs=[[{"secondary_y": True}]])

    fig3.add_trace(
        go.Bar(
            x=yoy_er.index, y=yoy_er.values,
            name=f"{latest_year} 전년대비 증감률(%)",
            marker=dict(color=colors),
            text=[f"{v:.1f}%" for v in yoy_er.values],
            textposition="inside",  # <-- outside 대신 inside로 (라인 가림 최소화)
            insidetextanchor="middle",
            opacity=0.6
        ),
        secondary_y=True
    )
    line_colors = ["#1e3a8a", "#00dac4"]
    for i, year in enumerate(sorted(mon_cnt['YEA'].unique())):
        df_year = mon_cnt[mon_cnt['YEA'] == year]
        fig3.add_trace(
            go.Scatter(
                x=df_year['MON'],
                y=df_year['ER_CNT'],
                mode='lines+markers',
                name=f"{year} 등록대수",
                line=dict(width=3, color=line_colors[i % len(line_colors)]),
                marker=dict(size=7, color=line_colors[i % len(line_colors)])
            ),
            secondary_y=False
        )

    # 축 설정
    fig3.update_layout(
        hovermode="x unified",
        barmode="overlay"
    )
    fig3.update_yaxes(title_text="등록대수", secondary_y=False)
    fig3.update_yaxes(title_text="전년대비 증감률 (%)", secondary_y=True)
    fig3.update_xaxes(title_text="월")

    st.plotly_chart(fig3, use_container_width=True)





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