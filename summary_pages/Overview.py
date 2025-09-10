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
new_seg = pd.read_excel('./data/2508차급외형연료.xlsx',sheet_name='신규')
new_seg['EXTRACT_DE'] = new_seg['EXTRACT_DE'].astype('str')
used_seg = pd.read_excel('./data/2508차급외형연료.xlsx',sheet_name='이전')
er_seg = pd.read_excel('./data/2508차급외형연료.xlsx',sheet_name='말소')
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
sz_order = ['소형', '경형', '준중형','중형','준대형','대형']
bt_order = ['SUV','세단','RV','해치백','픽업트럭','컨버터블','쿠페','왜건']
fu_order = ['휘발유','경유','LPG','하이브리드','전기','수소']
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

    seg = ['차급','외형','연료']
    # use.sort()
    segment = st.selectbox("세부 구분", seg)
    seg_dict = {'차급':['CAR_SZ',sz_order],
                '외형':['CAR_BT',bt_order],
                '연료':['USE_FUEL_NM',fu_order]}
    new_col1, new_col2 = st.columns([2, 2], gap="large")
    with new_col1:
        st.subheader(f"{month}월 {segment}별 신차등록 점유율")
        df_sz = new_seg[new_seg['EXTRACT_DE'] == '202508'].groupby([seg_dict[segment][0]])[['CNT']].sum().reset_index()
        new_sz = px.pie(df_sz, values="CNT", names=seg_dict[segment][0], hole=.3, category_orders={seg_dict[segment][0]: seg_dict[segment][1]})
        st.plotly_chart(new_sz, use_container_width=True)
    with new_col2:
        st.subheader(f"{year}년 {segment}별 누적 영역 그래프")
        stacked_area = new_seg.groupby(['EXTRACT_DE', seg_dict[segment][0]])[['CNT']].sum().reset_index()
        stacked_area["EXTRACT_DE"] = pd.to_datetime(
            stacked_area["EXTRACT_DE"].astype(str), format="%Y%m"
        )
        area_sz = px.area(stacked_area, x="EXTRACT_DE", y="CNT", color=seg_dict[segment][0],
                      pattern_shape=seg_dict[segment][0],
                      category_orders={seg_dict[segment][0]: seg_dict[segment][1]})
        area_sz.update_xaxes(dtick="M1", tickformat="%Y-%m")
        area_sz.update_xaxes(title_text="날짜")
        st.plotly_chart(area_sz, use_container_width=True)
    new_col3, new_col4 = st.columns([2, 2], gap="large")
    # with new_col3:
    #     st.subheader(f"{month}월 외형별 신차등록 점유율")
    #     df_bt = new_seg[new_seg['EXTRACT_DE'] == '202508'].groupby(['CAR_BT'])[['CNT']].sum().reset_index()
    #     new_bt = px.pie(df_bt, values="CNT", names="CAR_BT", hole=.3, category_orders={'CAR_BT': bt_order})
    #     st.plotly_chart(new_bt, use_container_width=True)
    # with new_col4:
    #     st.subheader(f"{year}년 월별 외형별 누적 영역 그래프")
    #     stacked_area = new_seg.groupby(['EXTRACT_DE', 'CAR_BT'])[['CNT']].sum().reset_index()
    #     stacked_area["EXTRACT_DE"] = pd.to_datetime(
    #         stacked_area["EXTRACT_DE"].astype(str), format="%Y%m"
    #     )
    #     area_bt = px.area(stacked_area, x="EXTRACT_DE", y="CNT", color="CAR_BT",
    #                       pattern_shape="CAR_BT",
    #                       category_orders={"CAR_BT": bt_order})
    #     area_bt.update_xaxes(dtick="M1", tickformat="%Y-%m")
    #     area_bt.update_xaxes(title_text="날짜")
    #     st.plotly_chart(area_bt, use_container_width=True)
    # new_col5, new_col6 = st.columns([2, 2], gap="large")
    # with new_col5:
    #     st.subheader(f"{month}월 연료별 신차등록 점유율")
    #     df_fu = new_seg[new_seg['EXTRACT_DE'] == '202508'].groupby(['USE_FUEL_NM'])[['CNT']].sum().reset_index()
    #     new_fu = px.pie(df_fu, values="CNT", names="USE_FUEL_NM", hole=.3, category_orders={'USE_FUEL_NM': fu_order})
    #     st.plotly_chart(new_fu, use_container_width=True)
    # with new_col6:
    #     st.subheader(f"{year}년 월별 연료별 누적 영역 그래프")
    #     stacked_area = new_seg.groupby(['EXTRACT_DE', 'USE_FUEL_NM'])[['CNT']].sum().reset_index()
    #     stacked_area["EXTRACT_DE"] = pd.to_datetime(
    #         stacked_area["EXTRACT_DE"].astype(str), format="%Y%m"
    #     )
    #     area_fu = px.area(stacked_area, x="EXTRACT_DE", y="CNT", color="USE_FUEL_NM",
    #                       pattern_shape="USE_FUEL_NM",
    #                       category_orders={"USE_FUEL_NM": fu_order})
    #     area_fu.update_xaxes(dtick="M1", tickformat="%Y-%m")
    #     area_fu.update_xaxes(title_text="날짜")
    #     st.plotly_chart(area_fu, use_container_width=True)


with tab2:
    st.subheader('이전등록 실거래 추이 및 전년 비교')
    st.markdown("- 실거래(매도, 알선, 개인거래) 대상 집계")
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

    used_col1, used_col2 = st.columns([2, 2], gap="large")
    with used_col1:
        st.subheader("2025년 8월 차급별 이전등록 점유율")
    with used_col2:
        st.subheader("2025년 월별 차급 누적 영역 그래프")

    used_col3, used_col4 = st.columns([2, 2], gap="large")
    with used_col3:
        st.subheader("2025년 8월 외형별 이전등록 점유율")
    with used_col4:
        st.subheader("2025년 월별 외형급 누적 영역 그래프")
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

    er_col1, er_col2 = st.columns([2, 2], gap="large")
    with er_col1:
        st.subheader("2025년 8월 차급별 말소등록 점유율")
    with er_col2:
        st.subheader("2025년 월별 차급 누적 영역 그래프")

    er_col3, er_col4 = st.columns([2, 2], gap="large")
    with er_col3:
        st.subheader("2025년 8월 외형별 말소등록 점유율")
    with er_col4:
        st.subheader("2025년 월별 외형급 누적 영역 그래프")





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