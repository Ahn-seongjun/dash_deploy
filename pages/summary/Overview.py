# pages/summary/Overview.py
import warnings
warnings.filterwarnings('ignore')

import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

# overview_def: 사용자 원본 그대로 사용
from app_core import overview_def as od

# 공통 모듈
from app_core import data_loader as dl
from app_core import footer

# ── 1) 데이터 로딩 (번들러에서 스피너 1회) ─────────────────────────────
data = dl.get_overview_data(base_dir="data")  # ./data 내 파일명은 data_loader에서 지정
new_top     = data["new_top"]
use_top     = data["use_top"]
ersr_top    = data["ersr_top"]
new_mon_cnt = data["new_mon_cnt"]
used_mon_cnt= data["used_mon_cnt"]
er_mon_cnt  = data["er_mon_cnt"]
new_seg     = data["new_seg"]
used_seg    = data["used_seg"]
er_seg      = data["er_seg"]

# ── 2) 기존 전처리/지표/차트 로직 그대로 ──────────────────────────────
for df in (new_seg, used_seg, er_seg):
    df["EXTRACT_DE"] = df["EXTRACT_DE"].astype(str)

mon_new  = new_mon_cnt.groupby(['YEA','MON'])["CNT"].sum().reset_index()
mon_used = used_mon_cnt.groupby(['YEA','MON'])["CNT"].sum().reset_index()
mon_er   = er_mon_cnt.groupby(['YEA','MON'])["CNT"].sum().reset_index()

this_new  = mon_new[(mon_new['YEA']==2025) & (mon_new['MON']==8)]['CNT'].values[0]
this_used = mon_used[(mon_used['YEA']==2025) & (mon_used['MON']==8)]['CNT'].values[0]
this_er   = mon_er[(mon_er['YEA']==2025) & (mon_er['MON']==8)]['CNT'].values[0]
last_new  = mon_new[(mon_new['YEA']==2025) & (mon_new['MON']==7)]['CNT'].values[0]
last_used = mon_used[(mon_used['YEA']==2025) & (mon_used['MON']==7)]['CNT'].values[0]
last_er   = mon_er[(mon_er['YEA']==2025) & (mon_er['MON']==7)]['CNT'].values[0]

def cal(x,y): return round((x-y)/y, 2)

today = datetime.today()
month_ago = datetime(today.year, today.month, today.day) + relativedelta(months=-1)
year = today.year
month = "{}".format(month_ago.strftime('%m'))

with st.sidebar:
    st.write("CARISYOU DATALAB")
    st.link_button("CarCharts Free", "https://carcharts-free.carisyou.net/")

st.header("Summary")
st.markdown(f"## {year}년 {month}월 기준 자동차 등록 요약")
st.markdown("### 월간 승용차 등록 집계", help="전월대비 증감")

new, used, ersr, op = st.columns(4)
new.metric("신규 등록", format(this_new,','),  f"{cal(this_new, last_new)}%",  border=True)
used.metric("이전 등록", format(this_used,','), f"{cal(this_used, last_used)}%", border=True)
ersr.metric("말소 등록", format(this_er,','),   f"{cal(this_er, last_er)}%",    border=True)
op.metric("운행 등록",   format(int(26434579),','), f"{cal(26434579, 26425398)}%", border=True)

# 탭 스타일 (원본 유지)
st.markdown("""
<style>
.stTabs [role="tablist"] { gap: 6px; }
.stTabs [data-baseweb="tab"], .stTabs [data-baseweb="tab"] > div,
.stTabs [data-baseweb="tab"] p, .stTabs button[role="tab"] {
    font-size: 18px !important; font-weight: 700 !important;
    font-family: 'Arial', sans-serif !important; color: #333333 !important;
    padding: 8px 14px !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"],
.stTabs button[role="tab"][aria-selected="true"] {
    color: #ffffff !important; background-color: #00dac4 !important;
    border-radius: 8px 8px 0 0 !important;
}
.stTabs [data-baseweb="tab"]:hover, .stTabs button[role="tab"]:hover {
    background-color: #e9f2fb !important;
}
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(['신규', '이전', '말소'])

sz_order = ['소형','경형','준중형','중형','준대형','대형']
bt_order = ['SUV','세단','RV','해치백','픽업트럭','컨버터블','쿠페','왜건']
fu_order = ['휘발유','경유','LPG','하이브리드','전기','수소']
seg = ['차급','외형','연료']
seg_dict = {
    '차급': ['CAR_SZ', sz_order],
    '외형': ['CAR_BT', bt_order],
    '연료': ['USE_FUEL_NM', fu_order],
}

# ── (이하 그래프/표는 원본 그대로 유지) ───────────────────────────────
with tab1:
    col1, col2 = st.columns([2,2], gap="large")
    with col1:
        st.subheader('국산 모델 TOP 10')
        na_top = new_top[new_top['CL_HMMD_IMP_SE_NM']=='국산'].iloc[:, :4]
        na_top = na_top.rename(columns={'RN':'순위','ORG_CAR_MAKER_KOR':'브랜드','CAR_MOEL_DT':'모델','CNT':'대수'}).set_index("순위")
        na_top["대수"] = na_top["대수"].map("{:,}".format)
        st.dataframe(na_top, use_container_width=True)
    with col2:
        st.subheader('수입 모델 TOP 10')
        im_top = new_top[new_top['CL_HMMD_IMP_SE_NM']=='수입'].iloc[:, :4]
        im_top = im_top.rename(columns={'RN':'순위','ORG_CAR_MAKER_KOR':'브랜드','CAR_MOEL_DT':'모델','CNT':'대수'}).set_index("순위")
        im_top["대수"] = im_top["대수"].map("{:,}".format)
        st.dataframe(im_top, use_container_width=True)

    st.subheader('신규등록 추이 및 전년 비교')
    st.markdown("- 이삿짐, 부활차 제외")
    pvt_new = mon_new.pivot_table(index='MON', columns='YEA', values='CNT', aggfunc='sum')
    latest_year = pvt_new.columns.max()
    prev_year = latest_year - 1
    yoy_new = (pvt_new[latest_year] - pvt_new[prev_year]) / pvt_new[prev_year] * 100
    colors = ["lightcoral" if v >= 0 else "lightskyblue" for v in yoy_new.values]
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    fig1.add_trace(go.Bar(x=yoy_new.index, y=yoy_new.values, name=f"{latest_year} 전년대비 증감률(%)",
                          marker=dict(color=colors),
                          text=[f"{v:.1f}%" for v in yoy_new.values],
                          textposition="inside", insidetextanchor="middle", opacity=0.6),
                   secondary_y=True)
    line_colors = ["#1e3a8a","#00dac4"]
    for i, yr in enumerate(sorted(mon_new['YEA'].unique())):
        sub = mon_new[mon_new['YEA']==yr]
        fig1.add_trace(go.Scatter(x=sub['MON'], y=sub['CNT'], mode='lines+markers',
                                  name=f"{yr} 등록대수",
                                  line=dict(width=3, color=line_colors[i % len(line_colors)]),
                                  marker=dict(size=7, color=line_colors[i % len(line_colors)])),
                       secondary_y=False)
    fig1.update_layout(hovermode="x unified", barmode="overlay")
    fig1.update_yaxes(title_text="등록대수", secondary_y=False)
    fig1.update_yaxes(title_text="전년대비 증감률 (%)", secondary_y=True)
    fig1.update_xaxes(title_text="월")
    st.plotly_chart(fig1, use_container_width=True)

    segment = st.selectbox("세부 구분", seg, key="new")
    new_col1, new_col2 = st.columns([2, 2], gap="large")
    with new_col1:
        st.subheader(f"{month}월 {segment}별 신차등록 점유율")
        df_sz = new_seg[new_seg['EXTRACT_DE']=='202508'].groupby([seg_dict[segment][0]])[['CNT']].sum().reset_index()
        new_sz = px.pie(df_sz, values="CNT", names=seg_dict[segment][0], hole=.3,
                        category_orders={seg_dict[segment][0]: seg_dict[segment][1]})
        st.plotly_chart(new_sz, use_container_width=True)
    with new_col2:
        st.subheader(f"{year}년 {segment}별 누적 영역 그래프")
        stacked_area = new_seg.groupby(['EXTRACT_DE', seg_dict[segment][0]])[['CNT']].sum().reset_index()
        stacked_area["EXTRACT_DE"] = pd.to_datetime(stacked_area["EXTRACT_DE"].astype(str), format="%Y%m")
        area_sz = px.area(stacked_area, x="EXTRACT_DE", y="CNT", color=seg_dict[segment][0],
                          pattern_shape=seg_dict[segment][0],
                          category_orders={seg_dict[segment][0]: seg_dict[segment][1]})
        area_sz.update_xaxes(dtick="M1", tickformat="%Y-%m", title_text="날짜")
        st.plotly_chart(area_sz, use_container_width=True)

with tab2:
    # (원본 코드 동일하게 유지)
    col1, col2 = st.columns([2,2], gap="large")
    with col1:
        st.subheader('국산 모델 TOP 10')
        na_top = use_top[use_top['CL_HMMD_IMP_SE_NM']=='국산'].iloc[:, :5]
        na_top = na_top.rename(columns={'RN':'순위','ORG_CAR_MAKER_KOR':'브랜드','CAR_MOEL_DT':'모델','CAR_MODEL_KOR':'상세모델','CNT':'대수'}).set_index("순위")
        na_top["대수"] = na_top["대수"].map("{:,}".format)
        st.dataframe(na_top, use_container_width=True)
    with col2:
        st.subheader('수입 모델 TOP 10')
        im_top = use_top[use_top['CL_HMMD_IMP_SE_NM']=='수입'].iloc[:, :5]
        im_top = im_top.rename(columns={'RN':'순위','ORG_CAR_MAKER_KOR':'브랜드','CAR_MOEL_DT':'모델','CAR_MODEL_KOR':'상세모델','CNT':'대수'}).set_index("순위")
        im_top["대수"] = im_top["대수"].map("{:,}".format)
        st.dataframe(im_top, use_container_width=True)

    st.subheader('이전등록 실거래 추이 및 전년 비교')
    st.markdown("- 실거래(매도, 알선, 개인거래) 대상 집계")
    pvt_used = mon_used.pivot_table(index='MON', columns='YEA', values='CNT', aggfunc='sum')
    latest_year = pvt_used.columns.max()
    prev_year = latest_year - 1
    yoy_used = (pvt_used[latest_year] - pvt_used[prev_year]) / pvt_used[prev_year] * 100
    colors = ["lightcoral" if v >= 0 else "lightskyblue" for v in yoy_used.values]
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    fig2.add_trace(go.Bar(x=yoy_used.index, y=yoy_used.values, name=f"{latest_year} 전년대비 증감률(%)",
                          marker=dict(color=colors),
                          text=[f"{v:.1f}%" for v in yoy_used.values],
                          textposition="inside", insidetextanchor="middle", opacity=0.6),
                   secondary_y=True)
    line_colors = ["#1e3a8a","#00dac4"]
    for i, yr in enumerate(sorted(mon_used['YEA'].unique())):
        sub = mon_used[mon_used['YEA']==yr]
        fig2.add_trace(go.Scatter(x=sub['MON'], y=sub['CNT'], mode='lines+markers',
                                  name=f"{yr} 등록대수",
                                  line=dict(width=3, color=line_colors[i % len(line_colors)]),
                                  marker=dict(size=7, color=line_colors[i % len(line_colors)])),
                       secondary_y=False)
    fig2.update_layout(hovermode="x unified", barmode="overlay")
    fig2.update_yaxes(title_text="등록대수", secondary_y=False)
    fig2.update_yaxes(title_text="전년대비 증감률 (%)", secondary_y=True)
    fig2.update_xaxes(title_text="월")
    st.plotly_chart(fig2, use_container_width=True)

    segment = st.selectbox("세부 구분", seg, key="used")
    used_col1, used_col2 = st.columns([2,2], gap="large")
    with used_col1:
        st.subheader(f"{month}월 {segment}별 이전등록 점유율")
        df_us = used_seg[used_seg['EXTRACT_DE']=='202508'].groupby([seg_dict[segment][0]])[['CNT']].sum().reset_index()
        us_plot = px.pie(df_us, values="CNT", names=seg_dict[segment][0], hole=.3,
                         category_orders={seg_dict[segment][0]: seg_dict[segment][1]})
        st.plotly_chart(us_plot, use_container_width=True)
    with used_col2:
        st.subheader(f"{year}년 {segment}별 누적 영역 그래프")
        stacked_area = used_seg.groupby(['EXTRACT_DE', seg_dict[segment][0]])[['CNT']].sum().reset_index()
        stacked_area["EXTRACT_DE"] = pd.to_datetime(stacked_area["EXTRACT_DE"].astype(str), format="%Y%m")
        area_sz = px.area(stacked_area, x="EXTRACT_DE", y="CNT", color=seg_dict[segment][0],
                          pattern_shape=seg_dict[segment][0],
                          category_orders={seg_dict[segment][0]: seg_dict[segment][1]})
        area_sz.update_xaxes(dtick="M1", tickformat="%Y-%m", title_text="날짜")
        st.plotly_chart(area_sz, use_container_width=True)

with tab3:
    # (원본 코드 동일하게 유지)
    col1, col2 = st.columns([2,2], gap="large")
    with col1:
        st.subheader('국산 모델 TOP 10')
        na_top = ersr_top[ersr_top['CL_HMMD_IMP_SE_NM']=='국산'].iloc[:, :4]
        na_top = na_top.rename(columns={'RN':'순위','ORG_CAR_MAKER_KOR':'브랜드','CAR_MOEL_DT':'모델','CNT':'대수'}).set_index("순위")
        na_top["대수"] = na_top["대수"].map("{:,}".format)
        st.dataframe(na_top, use_container_width=True)
    with col2:
        st.subheader('수입 모델 TOP 10')
        im_top = ersr_top[ersr_top['CL_HMMD_IMP_SE_NM']=='수입'].iloc[:, :4]
        im_top = im_top.rename(columns={'RN':'순위','ORG_CAR_MAKER_KOR':'브랜드','CAR_MOEL_DT':'모델','CNT':'대수'}).set_index("순위")
        im_top["대수"] = im_top["대수"].map("{:,}".format)
        st.dataframe(im_top, use_container_width=True)

    st.subheader('말소등록 추이 및 전년 비교')
    st.markdown("- 폐차, 수출예정 대상 집계")
    pvt_er = mon_er.pivot_table(index='MON', columns='YEA', values='CNT', aggfunc='sum')
    latest_year = pvt_er.columns.max()
    prev_year = latest_year - 1
    yoy_er = (pvt_er[latest_year] - pvt_er[prev_year]) / pvt_er[prev_year] * 100
    colors = ["lightcoral" if v >= 0 else "lightskyblue" for v in yoy_er.values]
    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    fig3.add_trace(go.Bar(x=yoy_er.index, y=yoy_er.values, name=f"{latest_year} 전년대비 증감률(%)",
                          marker=dict(color=colors),
                          text=[f"{v:.1f}%" for v in yoy_er.values],
                          textposition="inside", insidetextanchor="middle", opacity=0.6),
                   secondary_y=True)
    line_colors = ["#1e3a8a","#00dac4"]
    for i, yr in enumerate(sorted(mon_er['YEA'].unique())):
        sub = mon_er[mon_er['YEA']==yr]
        fig3.add_trace(go.Scatter(x=sub['MON'], y=sub['CNT'], mode='lines+markers',
                                  name=f"{yr} 등록대수",
                                  line=dict(width=3, color=line_colors[i % len(line_colors)]),
                                  marker=dict(size=7, color=line_colors[i % len(line_colors)])),
                       secondary_y=False)
    fig3.update_layout(hovermode="x unified", barmode="overlay")
    fig3.update_yaxes(title_text="등록대수", secondary_y=False)
    fig3.update_yaxes(title_text="전년대비 증감률 (%)", secondary_y=True)
    fig3.update_xaxes(title_text="월")
    st.plotly_chart(fig3, use_container_width=True)

    segment = st.selectbox("세부 구분", seg, key="ersr")
    er_col1, er_col2 = st.columns([2,2], gap="large")
    with er_col1:
        st.subheader(f"{month}월 {segment}별 말소등록 점유율")
        df_er = er_seg[er_seg['EXTRACT_DE']=='202508'].groupby([seg_dict[segment][0]])[['CNT']].sum().reset_index()
        er_plot = px.pie(df_er, values="CNT", names=seg_dict[segment][0], hole=.3,
                         category_orders={seg_dict[segment][0]: seg_dict[segment][1]})
        st.plotly_chart(er_plot, use_container_width=True)
    with er_col2:
        st.subheader(f"{year}년 {segment}별 누적 영역 그래프")
        stacked_area = er_seg.groupby(['EXTRACT_DE', seg_dict[segment][0]])[['CNT']].sum().reset_index()
        stacked_area["EXTRACT_DE"] = pd.to_datetime(stacked_area["EXTRACT_DE"].astype(str), format="%Y%m")
        area_sz = px.area(stacked_area, x="EXTRACT_DE", y="CNT", color=seg_dict[segment][0],
                          pattern_shape=seg_dict[segment][0],
                          category_orders={seg_dict[segment][0]: seg_dict[segment][1]})
        area_sz.update_xaxes(dtick="M1", tickformat="%Y-%m", title_text="날짜")
        st.plotly_chart(area_sz, use_container_width=True)

# ── 3) 공통 푸터 ──────────────────────────────────────────────────────
footer.render()
