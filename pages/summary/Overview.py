import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')
import base64
import time
from datetime import datetime
from dateutil.relativedelta import *
import overview_def as od

st.set_page_config(page_title= "[카이즈유] 자동차 등록데이터", layout="wide", initial_sidebar_state="auto")

@st.cache_data(ttl=3600, show_spinner=False)
def load_workbook(path: str, sheets: list[str] | None = None) -> dict[str, pd.DataFrame]:
    dfs = pd.read_excel(path, sheet_name=sheets, engine="openpyxl")
    if isinstance(dfs, pd.DataFrame):
        dfs = {sheets if isinstance(sheets, str) else "Sheet1": dfs}
    return dfs

with st.spinner("🚗 데이터 엔진 예열 중…"):
    top_wb = load_workbook("./data/2508_top.xlsx", sheets=["신규","이전","말소"])
    new_top   = top_wb["신규"]
    use_top   = top_wb["이전"]
    ersr_top  = top_wb["말소"]

    mon_wb = load_workbook("./data/24_25_moncnt.xlsx", sheets=["신규","이전","말소"])
    new_mon_cnt  = mon_wb["신규"]
    used_mon_cnt = mon_wb["이전"]
    er_mon_cnt   = mon_wb["말소"]

    seg_wb = load_workbook("./data/2508차급외형연료.xlsx", sheets=["신규","이전","말소"])
    new_seg  = seg_wb["신규"].copy()
    used_seg = seg_wb["이전"].copy()
    er_seg   = seg_wb["말소"].copy()

for df in (new_seg, used_seg, er_seg):
    # EXTRACT_DE: YYYYMM → 문자열/날짜 중 하나로 통일
    df["EXTRACT_DE"] = df["EXTRACT_DE"].astype(str)
    # 시각화 축 표시를 YYYY-MM로 쓰려면:
    #df["YYYYMM"] = df["EXTRACT_DE"].dt.strftime("%Y-%m")

# 슬라이싱
mon_new = new_mon_cnt.groupby(['YEA', 'MON'])["CNT"].sum().reset_index()
mon_used = used_mon_cnt.groupby(['YEA', 'MON'])["CNT"].sum().reset_index()
mon_er = er_mon_cnt.groupby(['YEA', 'MON'])["CNT"].sum().reset_index()
this_new = mon_new[(mon_new['YEA']==2025) & (mon_new['MON'] ==8)]['CNT'].values[0]
this_used = mon_used[(mon_used['YEA']==2025) & (mon_used['MON'] ==8)]['CNT'].values[0]
this_er = mon_er[(mon_er['YEA']==2025) & (mon_er['MON'] ==8)]['CNT'].values[0]
last_new = mon_new[(mon_new['YEA']==2025) & (mon_new['MON'] ==7)]['CNT'].values[0]
last_used = mon_used[(mon_used['YEA']==2025) & (mon_used['MON'] ==7)]['CNT'].values[0]
last_er = mon_er[(mon_er['YEA']==2025) & (mon_er['MON'] ==7)]['CNT'].values[0]

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
st.markdown('### 월간 승용차 등록 집계',help = '전월대비 증감')



new, used, ersr, op = st.columns(4)
new.metric("신규 등록", format(this_new,','),f"{cal(this_new, last_new)}%",border = True)
used.metric("이전 등록", format(this_used,','),f"{cal(this_used, last_used)}%",border = True)
ersr.metric("말소 등록", format(this_er,','),f"{cal(this_er, last_er)}%",border = True)
op.metric("운행 등록", format(int(26434579),','),f"{cal(26434579, 26425398)}%",border = True)

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
tab1, tab2, tab3 = st.tabs(['신규', '이전', '말소'])

sz_order = ['소형', '경형', '준중형','중형','준대형','대형']
bt_order = ['SUV','세단','RV','해치백','픽업트럭','컨버터블','쿠페','왜건']
fu_order = ['휘발유','경유','LPG','하이브리드','전기','수소']
seg = ['차급','외형','연료']
seg_dict = {'차급':['CAR_SZ',sz_order],
            '외형':['CAR_BT',bt_order],
            '연료':['USE_FUEL_NM',fu_order]}
with tab1:
    col1, col2 = st.columns([2, 2], gap="large")
    with col1:
        st.subheader('국산 모델 TOP 10')
        na_top = new_top[new_top['CL_HMMD_IMP_SE_NM'] == '국산'].iloc[:, :4]
        na_top.rename(columns={'RN': '순위', 'ORG_CAR_MAKER_KOR': '브랜드', 'CAR_MOEL_DT': '모델', 'CNT': '대수'}, inplace=True)
        na_top = na_top.set_index("순위")
        na_top["대수"] = na_top["대수"].map("{:,}".format)
        st.dataframe(na_top, use_container_width=True)

    with col2:
        st.subheader('수입 모델 TOP 10')
        im_top = new_top[new_top['CL_HMMD_IMP_SE_NM'] == '수입'].iloc[:, :4]
        im_top.rename(columns={'RN': '순위', 'ORG_CAR_MAKER_KOR': '브랜드', 'CAR_MOEL_DT': '모델', 'CNT': '대수'}, inplace=True)
        im_top = im_top.set_index("순위")
        im_top["대수"] = im_top["대수"].map("{:,}".format)
        st.dataframe(im_top, use_container_width=True)

    st.subheader('신규등록 추이 및 전년 비교')
    st.markdown("- 이삿짐, 부활차 제외")
    # 전년대비 산출

    pvt_new = mon_new.pivot_table(index='MON', columns='YEA', values='CNT', aggfunc='sum')
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
    for i, year in enumerate(sorted(mon_new['YEA'].unique())):
        df_year = mon_new[mon_new['YEA'] == year]
        fig1.add_trace(
            go.Scatter(
                x=df_year['MON'],
                y=df_year['CNT'],
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


    segment = st.selectbox("세부 구분", seg, key= "new")
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

with tab2:
    col1, col2 = st.columns([2, 2], gap="large")
    with col1:
        st.subheader('국산 모델 TOP 10')
        na_top = use_top[use_top['CL_HMMD_IMP_SE_NM'] == '국산'].iloc[:, :5]
        na_top.rename(columns={'RN': '순위', 'ORG_CAR_MAKER_KOR': '브랜드', 'CAR_MOEL_DT': '모델','CAR_MODEL_KOR':'상세모델', 'CNT': '대수'}, inplace=True)
        na_top = na_top.set_index("순위")
        na_top["대수"] = na_top["대수"].map("{:,}".format)
        st.dataframe(na_top, use_container_width=True)

    with col2:
        st.subheader('수입 모델 TOP 10')
        im_top = use_top[use_top['CL_HMMD_IMP_SE_NM'] == '수입'].iloc[:, :5]
        im_top.rename(columns={'RN': '순위', 'ORG_CAR_MAKER_KOR': '브랜드', 'CAR_MOEL_DT': '모델','CAR_MODEL_KOR':'상세모델', 'CNT': '대수'}, inplace=True)
        im_top = im_top.set_index("순위")
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
    for i, year in enumerate(sorted(mon_used['YEA'].unique())):
        df_year = mon_used[mon_used['YEA'] == year]
        fig2.add_trace(
            go.Scatter(
                x=df_year['MON'],
                y=df_year['CNT'],
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

    segment = st.selectbox("세부 구분", seg, key= "used")
    used_col1, used_col2 = st.columns([2, 2], gap="large")
    with used_col1:
        st.subheader(f"{month}월 {segment}별 이전등록 점유율")
        df_us = used_seg[used_seg['EXTRACT_DE'] == '202508'].groupby([seg_dict[segment][0]])[['CNT']].sum().reset_index()
        us_plot = px.pie(df_us, values="CNT", names=seg_dict[segment][0], hole=.3, category_orders={seg_dict[segment][0]: seg_dict[segment][1]})
        st.plotly_chart(us_plot, use_container_width=True)
    with used_col2:
        st.subheader(f"{year}년 {segment}별 누적 영역 그래프")
        stacked_area = used_seg.groupby(['EXTRACT_DE', seg_dict[segment][0]])[['CNT']].sum().reset_index()
        stacked_area["EXTRACT_DE"] = pd.to_datetime(
            stacked_area["EXTRACT_DE"].astype(str), format="%Y%m"
        )
        area_sz = px.area(stacked_area, x="EXTRACT_DE", y="CNT", color=seg_dict[segment][0],
                      pattern_shape=seg_dict[segment][0],
                      category_orders={seg_dict[segment][0]: seg_dict[segment][1]})
        area_sz.update_xaxes(dtick="M1", tickformat="%Y-%m")
        area_sz.update_xaxes(title_text="날짜")
        st.plotly_chart(area_sz, use_container_width=True)


with tab3:
    col1, col2 = st.columns([2, 2], gap="large")
    with col1:
        st.subheader('국산 모델 TOP 10')
        na_top = ersr_top[ersr_top['CL_HMMD_IMP_SE_NM'] == '국산'].iloc[:, :4]
        na_top.rename(
            columns={'RN': '순위', 'ORG_CAR_MAKER_KOR': '브랜드', 'CAR_MOEL_DT': '모델', 'CNT': '대수'},
            inplace=True)
        na_top = na_top.set_index("순위")
        na_top["대수"] = na_top["대수"].map("{:,}".format)
        st.dataframe(na_top, use_container_width=True)

    with col2:
        st.subheader('수입 모델 TOP 10')
        im_top = ersr_top[ersr_top['CL_HMMD_IMP_SE_NM'] == '수입'].iloc[:, :4]
        im_top.rename(
            columns={'RN': '순위', 'ORG_CAR_MAKER_KOR': '브랜드', 'CAR_MOEL_DT': '모델', 'CNT': '대수'},
            inplace=True)
        im_top = im_top.set_index("순위")
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
    for i, year in enumerate(sorted(mon_er['YEA'].unique())):
        df_year = mon_er[mon_er['YEA'] == year]
        fig3.add_trace(
            go.Scatter(
                x=df_year['MON'],
                y=df_year['CNT'],
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

    segment = st.selectbox("세부 구분", seg, key="ersr")
    er_col1, er_col2 = st.columns([2, 2], gap="large")
    with er_col1:
        st.subheader(f"{month}월 {segment}별 말소등록 점유율")
        df_er = er_seg[er_seg['EXTRACT_DE'] == '202508'].groupby([seg_dict[segment][0]])[
            ['CNT']].sum().reset_index()
        er_plot = px.pie(df_er, values="CNT", names=seg_dict[segment][0], hole=.3,
                         category_orders={seg_dict[segment][0]: seg_dict[segment][1]})
        st.plotly_chart(er_plot, use_container_width=True)
    with er_col2:
        st.subheader(f"{year}년 {segment}별 누적 영역 그래프")
        stacked_area = er_seg.groupby(['EXTRACT_DE', seg_dict[segment][0]])[['CNT']].sum().reset_index()
        stacked_area["EXTRACT_DE"] = pd.to_datetime(
            stacked_area["EXTRACT_DE"].astype(str), format="%Y%m"
        )
        area_sz = px.area(stacked_area, x="EXTRACT_DE", y="CNT", color=seg_dict[segment][0],
                          pattern_shape=seg_dict[segment][0],
                          category_orders={seg_dict[segment][0]: seg_dict[segment][1]})
        area_sz.update_xaxes(dtick="M1", tickformat="%Y-%m")
        area_sz.update_xaxes(title_text="날짜")
        st.plotly_chart(area_sz, use_container_width=True)

st.markdown("### 분석 대상 컬럼 선택")
reg = ['신규','이전','말소']
feat = ['브랜드', '모델', '차급', '외형', '연료']
feat_dict = {'브랜드':'ORG_CAR_MAKER_KOR',
             '모델':'CAR_MOEL_DT',
             '차급':'CAR_SZ',
             '외형':'CAR_BT',
             '연료':'USE_FUEL_NM'}
with st.form(key="my_form"):
    reg_kind = st.selectbox("데이터 선택",reg,key = "reg_kind")
    dim_col = st.selectbox("비교 기준 선택", feat, key="feat")
    submit_button = st.form_submit_button(label="Submit")
if reg_kind == '신규':
    df_detail = new_mon_cnt.copy()
elif reg_kind == '이전':
    df_detail = used_mon_cnt.copy()
else :
    df_detail = er_mon_cnt.copy()
base_month = month_ago.strftime('%Y-%m')

tbl_mom = od.compute_change_table(df_detail, feat_dict[dim_col], base_month, mode="MoM")

fig_up_mom, fig_dn_mom = od.plot_top_bottom(tbl_mom, feat_dict[dim_col], topn=5, title_prefix="MoM")
fig_up_mom.update_yaxes(title_text=dim_col)
fig_dn_mom.update_yaxes(title_text=dim_col)
st.plotly_chart(fig_up_mom, use_container_width=True)
st.plotly_chart(fig_dn_mom, use_container_width=True)

tbl_yoy = od.compute_change_table(df_detail, feat_dict[dim_col], base_month, mode="YoY")
fig_up_yoy, fig_dn_yoy = od.plot_top_bottom(tbl_yoy, feat_dict[dim_col], topn=5, title_prefix="YoY")
fig_up_yoy.update_yaxes(title_text=dim_col)
fig_dn_yoy.update_yaxes(title_text=dim_col)
st.plotly_chart(fig_up_yoy, use_container_width=True)
st.plotly_chart(fig_dn_yoy, use_container_width=True)

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