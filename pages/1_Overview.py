import streamlit as st
st.set_page_config(page_title="Overview", layout="wide", initial_sidebar_state="auto")

import warnings
warnings.filterwarnings('ignore')
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')
import base64
from datetime import datetime
from dateutil.relativedelta import relativedelta
from app_core.nav import render_sidebar_nav
render_sidebar_nav()
# 🔹 공통 로더 사용 (번들러에서만 스피너 1회)
from app_core import data_loader as dl
from app_core import charts as od
from app_core import footer
from app_core import ui
# =============================
# 1) 데이터 로딩 (스피너는 번들러에서 한 번만)
# =============================
data = dl.get_overview_data()
new_top     = data["new_top"]
use_top     = data["use_top"]
ersr_top    = data["ersr_top"]
new_mon_cnt = data["new_mon_cnt"]
used_mon_cnt= data["used_mon_cnt"]
er_mon_cnt  = data["er_mon_cnt"]
new_seg     = data["new_seg"]
used_seg    = data["used_seg"]
er_seg      = data["er_seg"]
# =============================
# 2) 전처리
# =============================
for df in (new_seg, used_seg, er_seg):
    df["EXTRACT_DE"] = df["EXTRACT_DE"].astype(str)

today = datetime.today()
month_ago = datetime(today.year, today.month, today.day) + relativedelta(months=-1)
year = today.year
month = "{}".format(month_ago.strftime('%m'))
month_ago_2 = datetime(today.year, today.month, today.day) + relativedelta(months=-2)
year_2 = "{}".format(month_ago_2.strftime('%Y'))
month_2 = "{}".format(month_ago_2.strftime('%m'))
# 슬라이싱
mon_new  = new_mon_cnt.groupby(['YEA', 'MON'])["CNT"].sum().reset_index()
mon_used = used_mon_cnt.groupby(['YEA', 'MON'])["CNT"].sum().reset_index()
mon_er   = er_mon_cnt.groupby(['YEA', 'MON'])["CNT"].sum().reset_index()
pre_mon = mon_new['MON'][-1:].values[0]
pre_year = mon_new['YEA'][-1:].values[0]
#print(pre_mon, pre_year)
last_pre_mon = mon_new['MON'][-2:].values[0]
last_pre_year = mon_new['YEA'][-2:].values[0]
#print(last_pre_mon, last_pre_year)
this_new  = mon_new[(mon_new['YEA']==pre_year) & (mon_new['MON']==pre_mon)]['CNT'].values[0]
this_used = mon_used[(mon_used['YEA']==pre_year) & (mon_used['MON']==pre_mon)]['CNT'].values[0]
this_er   = mon_er[(mon_er['YEA']==pre_year) & (mon_er['MON']==pre_mon)]['CNT'].values[0]
last_new  = mon_new[(mon_new['YEA']==last_pre_year) & (mon_new['MON']==last_pre_mon)]['CNT'].values[0]
last_used = mon_used[(mon_used['YEA']==last_pre_year) & (mon_used['MON']==last_pre_mon)]['CNT'].values[0]
last_er   = mon_er[(mon_er['YEA']==last_pre_year) & (mon_er['MON']==last_pre_mon)]['CNT'].values[0]
def cal(x,y):
    return round((x-y)/y, 4)

# 사이드바
with st.sidebar:
    ui.sidebar_links()

# 헤더/KPI
st.header("Summary")
st.markdown(f"## {pre_year}년 {pre_mon}월 기준 자동차 등록 요약")
st.markdown('### 월간 승용차 등록 집계', help='전월대비 증감')

new, used, ersr, op = st.columns(4)
new.metric("신규 등록", format(this_new,','),  f"{cal(this_new, last_new)}%",  border=True)
used.metric("이전 등록", format(this_used,','), f"{cal(this_used, last_used)}%", border=True)
ersr.metric("말소 등록", format(this_er,','),   f"{cal(this_er, last_er)}%",    border=True)
op.metric("운행 등록",   format(int(26536795),','), f"{cal(26536795, 26514873)}%", border=True)

# 탭 스타일
ui.apply_tab_style()
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
feat_dict = {
        '브랜드': 'ORG_CAR_MAKER_KOR',
        '모델': 'CAR_MOEL_DT',
        '차급': 'CAR_SZ',
        '외형': 'CAR_BT',
        '연료': 'USE_FUEL_NM'
    }
feat = ['브랜드','모델','차급','외형','연료']

def on_seg1_change():
    if st.session_state.seg2 == st.session_state.seg1:
        # seg1과 겹치지 않는 첫 옵션으로 교체
        for f in feat:
            if f != st.session_state.seg1:
                st.session_state.seg2 = f
                break

with tab1:
    col1, col2 = st.columns([2, 2], gap="large")
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
                          textposition="inside", insidetextanchor="middle", opacity=0.6), secondary_y=True)
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

    st.subheader('신규등록 트리맵')
    feat_clean = list(dict.fromkeys(feat))
    if not feat_clean:
        st.error("feat가 비어 있습니다.")
    else:
        # 1) 세션 키 안전 초기화
        if "new_seg1" not in st.session_state or st.session_state["new_seg1"] not in feat_clean:
            st.session_state["new_seg1"] = feat_clean[0]

        seg2_options = [f for f in feat_clean if f != st.session_state["new_seg1"]] or feat_clean[:]
        if ("new_seg2" not in st.session_state) or (st.session_state["new_seg2"] not in seg2_options):
            st.session_state["new_seg2"] = seg2_options[0]

        # 2) 위젯 (항상 초기화 이후 렌더)
        tre1, tre2 = st.columns(2)
        with tre1:
            st.selectbox(
                "분류1",
                feat_clean,
                index=feat_clean.index(st.session_state["new_seg1"]),
                key="new_seg1"
            )
        with tre2:
            # seg1 변경 반영
            seg2_options = [f for f in feat_clean if f != st.session_state["new_seg1"]] or feat_clean[:]
            if st.session_state["new_seg2"] not in seg2_options:
                st.session_state["new_seg2"] = seg2_options[0]

            st.selectbox(
                "분류2",
                seg2_options,
                index=seg2_options.index(st.session_state["new_seg2"]),
                key="new_seg2"
            )

        # 3) Treemap
        seg_one = st.session_state["new_seg1"]
        seg_two = st.session_state["new_seg2"]
        col1 = feat_dict[seg_one]
        col2 = feat_dict[seg_two]

        missing = [c for c in (col1, col2, "CNT") if c not in new_mon_cnt.columns]
        if missing:
            st.error(f"필요 컬럼 누락: {missing}")
        else:
            tree1 = px.treemap(
                new_mon_cnt,
                path=[px.Constant("전체"), col1, col2],
                values="CNT",
                color=col1,
            )
            tree1.update_layout(margin=dict(t=25, l=25, r=25, b=25))
            st.plotly_chart(tree1, use_container_width=True, key="new_treemap_chart")


    segment = st.selectbox("세부 구분", seg, key="new")
    new_col1, new_col2 = st.columns([2, 2], gap="large")
    with new_col1:
        st.subheader(f"{month}월 {segment}별 신차등록 점유율")
        df_sz = new_seg[new_seg['EXTRACT_DE']==str(year)+str(month)].groupby([seg_dict[segment][0]])[['CNT']].sum().reset_index()
        new_sz = px.pie(df_sz, values="CNT", names=seg_dict[segment][0], hole=.3,
                        category_orders={seg_dict[segment][0]: seg_dict[segment][1]})
        st.plotly_chart(new_sz, use_container_width=True)
    with new_col2:
        st.subheader(f"{pre_year}년 {segment}별 누적 영역 그래프")
        stacked_area = new_seg.groupby(['EXTRACT_DE', seg_dict[segment][0]])[['CNT']].sum().reset_index()
        stacked_area["EXTRACT_DE"] = pd.to_datetime(stacked_area["EXTRACT_DE"].astype(str), format="%Y%m")
        area_sz = px.area(stacked_area, x="EXTRACT_DE", y="CNT", color=seg_dict[segment][0],
                          pattern_shape=seg_dict[segment][0],
                          category_orders={seg_dict[segment][0]: seg_dict[segment][1]})
        area_sz.update_xaxes(dtick="M1", tickformat="%Y-%m", title_text="날짜")
        st.plotly_chart(area_sz, use_container_width=True)

with tab2:
    col1, col2 = st.columns([2, 2], gap="large")
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

    st.subheader('이전등록 트리맵')
    feat_clean = list(dict.fromkeys(feat))
    if not feat_clean:
        st.error("feat가 비어 있습니다.")
    else:
        # 1) 세션 키 안전 초기화
        if "used_seg1" not in st.session_state or st.session_state["used_seg1"] not in feat_clean:
            st.session_state["used_seg1"] = feat_clean[0]

        seg2_options = [f for f in feat_clean if f != st.session_state["used_seg1"]] or feat_clean[:]
        if ("used_seg2" not in st.session_state) or (st.session_state["used_seg2"] not in seg2_options):
            st.session_state["used_seg2"] = seg2_options[0]

        # 2) 위젯 (항상 초기화 이후 렌더)
        tre1, tre2 = st.columns(2)
        with tre1:
            st.selectbox(
                "분류1",
                feat_clean,
                index=feat_clean.index(st.session_state["used_seg1"]),
                key="used_seg1"
            )
        with tre2:
            # seg1 변경 반영
            seg2_options = [f for f in feat_clean if f != st.session_state["used_seg1"]] or feat_clean[:]
            if st.session_state["used_seg2"] not in seg2_options:
                st.session_state["used_seg2"] = seg2_options[0]

            st.selectbox(
                "분류2",
                seg2_options,
                index=seg2_options.index(st.session_state["used_seg2"]),
                key="used_seg2"
            )

        # 3) Treemap
        seg_one = st.session_state["used_seg1"]
        seg_two = st.session_state["used_seg2"]
        col1 = feat_dict[seg_one]
        col2 = feat_dict[seg_two]

        missing = [c for c in (col1, col2, "CNT") if c not in used_mon_cnt.columns]
        if missing:
            st.error(f"필요 컬럼 누락: {missing}")
        else:
            tree2 = px.treemap(
                used_mon_cnt,
                path=[px.Constant("전체"), col1, col2],
                values="CNT",
                color=col1,
            )
            tree2.update_layout(margin=dict(t=25, l=25, r=25, b=25))
            st.plotly_chart(tree2, use_container_width=True, key="used_treemap_chart")

    segment = st.selectbox("세부 구분", seg, key="used")
    used_col1, used_col2 = st.columns([2, 2], gap="large")
    with used_col1:
        st.subheader(f"{month}월 {segment}별 이전등록 점유율")
        df_us = used_seg[used_seg['EXTRACT_DE']==str(year)+str(month)].groupby([seg_dict[segment][0]])[['CNT']].sum().reset_index()
        us_plot = px.pie(df_us, values="CNT", names=seg_dict[segment][0], hole=.3,
                         category_orders={seg_dict[segment][0]: seg_dict[segment][1]})
        st.plotly_chart(us_plot, use_container_width=True)
    with used_col2:
        st.subheader(f"{pre_year}년 {segment}별 누적 영역 그래프")
        stacked_area = used_seg.groupby(['EXTRACT_DE', seg_dict[segment][0]])[['CNT']].sum().reset_index()
        stacked_area["EXTRACT_DE"] = pd.to_datetime(stacked_area["EXTRACT_DE"].astype(str), format="%Y%m")
        area_sz = px.area(stacked_area, x="EXTRACT_DE", y="CNT", color=seg_dict[segment][0],
                          pattern_shape=seg_dict[segment][0],
                          category_orders={seg_dict[segment][0]: seg_dict[segment][1]})
        area_sz.update_xaxes(dtick="M1", tickformat="%Y-%m", title_text="날짜")
        st.plotly_chart(area_sz, use_container_width=True)

with tab3:
    col1, col2 = st.columns([2, 2], gap="large")
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

    st.subheader('말소등록 트리맵')
    feat_clean = list(dict.fromkeys(feat))
    if not feat_clean:
        st.error("feat가 비어 있습니다.")
    else:
        # 1) 세션 키 안전 초기화
        if "ersr_seg1" not in st.session_state or st.session_state["ersr_seg1"] not in feat_clean:
            st.session_state["ersr_seg1"] = feat_clean[0]

        seg2_options = [f for f in feat_clean if f != st.session_state["ersr_seg1"]] or feat_clean[:]
        if ("ersr_seg2" not in st.session_state) or (st.session_state["ersr_seg2"] not in seg2_options):
            st.session_state["ersr_seg2"] = seg2_options[0]

        # 2) 위젯 (항상 초기화 이후 렌더)
        tre1, tre2 = st.columns(2)
        with tre1:
            st.selectbox(
                "분류1",
                feat_clean,
                index=feat_clean.index(st.session_state["ersr_seg1"]),
                key="ersr_seg1"
            )
        with tre2:
            # seg1 변경 반영
            seg2_options = [f for f in feat_clean if f != st.session_state["ersr_seg1"]] or feat_clean[:]
            if st.session_state["ersr_seg2"] not in seg2_options:
                st.session_state["ersr_seg2"] = seg2_options[0]

            st.selectbox(
                "분류2",
                seg2_options,
                index=seg2_options.index(st.session_state["ersr_seg2"]),
                key="ersr_seg2"
            )

        # 3) Treemap
        seg_one = st.session_state["ersr_seg1"]
        seg_two = st.session_state["ersr_seg2"]
        col1 = feat_dict[seg_one]
        col2 = feat_dict[seg_two]

        missing = [c for c in (col1, col2, "CNT") if c not in er_mon_cnt.columns]
        if missing:
            st.error(f"필요 컬럼 누락: {missing}")
        else:
            tree3 = px.treemap(
                er_mon_cnt,
                path=[px.Constant("전체"), col1, col2],
                values="CNT",
                color=col1,
            )
            tree3.update_layout(margin=dict(t=25, l=25, r=25, b=25))
            st.plotly_chart(tree3, use_container_width=True, key="ersr_treemap_chart")

    segment = st.selectbox("세부 구분", seg, key="ersr")
    er_col1, er_col2 = st.columns([2, 2], gap="large")
    with er_col1:
        st.subheader(f"{month}월 {segment}별 말소등록 점유율")
        df_er = er_seg[er_seg['EXTRACT_DE']==str(year)+str(month)].groupby([seg_dict[segment][0]])[['CNT']].sum().reset_index()
        er_plot = px.pie(df_er, values="CNT", names=seg_dict[segment][0], hole=.3,
                         category_orders={seg_dict[segment][0]: seg_dict[segment][1]})
        st.plotly_chart(er_plot, use_container_width=True)
    with er_col2: # year
        st.subheader(f"{pre_year}년 {segment}별 누적 영역 그래프")
        stacked_area = er_seg.groupby(['EXTRACT_DE', seg_dict[segment][0]])[['CNT']].sum().reset_index()
        stacked_area["EXTRACT_DE"] = pd.to_datetime(stacked_area["EXTRACT_DE"].astype(str), format="%Y%m")
        area_sz = px.area(stacked_area, x="EXTRACT_DE", y="CNT", color=seg_dict[segment][0],
                          pattern_shape=seg_dict[segment][0],
                          category_orders={seg_dict[segment][0]: seg_dict[segment][1]})
        area_sz.update_xaxes(dtick="M1", tickformat="%Y-%m", title_text="날짜")
        st.plotly_chart(area_sz, use_container_width=True)
st.markdown("### 분석 대상 컬럼 선택")
reg = ['신규','이전','말소']
#feat = ['브랜드','모델','차급','외형','연료']
# feat_dict = {
#     '브랜드':'ORG_CAR_MAKER_KOR',
#     '모델':'CAR_MOEL_DT',
#     '차급':'CAR_SZ',
#     '외형':'CAR_BT',
#     '연료':'USE_FUEL_NM'
# }

with st.form(key="my_form"):
    reg_kind = st.selectbox("데이터 선택", reg, key="reg_kind")
    dim_col  = st.selectbox("비교 기준 선택", feat, key="feat")
    submitted = st.form_submit_button(label="Submit")

if reg_kind == '신규':
    df_detail = new_mon_cnt.copy()
elif reg_kind == '이전':
    df_detail = used_mon_cnt.copy()
else:
    df_detail = er_mon_cnt.copy()

base_month = month_ago.strftime('%Y-%m')

# ✅ overview_def 사용 복구

tbl_mom = od.compute_change_table(df_detail, feat_dict[dim_col], base_month, mode="MoM")
fig_mom = od.plot_top_bottom_toggle(tbl_mom, feat_dict[dim_col], topn=5, title_prefix="MoM", show_periods=False)
fig_mom.update_yaxes(title_text=dim_col)

st.plotly_chart(fig_mom, use_container_width=True)

tbl_yoy = od.compute_change_table(df_detail, feat_dict[dim_col], base_month, mode="YoY")
fig_yoy = od.plot_top_bottom_toggle(tbl_yoy, feat_dict[dim_col], topn=5, title_prefix="YoY", show_periods=False)
fig_yoy.update_yaxes(title_text=dim_col)
st.plotly_chart(fig_yoy, use_container_width=True)
footer.render()