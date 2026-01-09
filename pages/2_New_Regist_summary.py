# pages/summary/new_reg_summary.py
import streamlit as st
st.set_page_config(page_title="신규등록 Summary", layout="wide", initial_sidebar_state="auto")
import pandas as pd
import warnings
warnings.filterwarnings('ignore')
from app_core.nav import render_sidebar_nav
render_sidebar_nav()
from app_core import footer
from app_core import data_loader as dl
from app_core import charts as ch
from app_core import ui

st.title("신규 등록 요약")

# 데이터 로딩
data = dl.get_newreg_data(base_dir="data/")
df_bar = data["monthly"]
df_use = data["cum"]
df = data["dim"]
# 원본 전처리 유지
df_bar = df_bar.reset_index()
df_bar["date"] = pd.to_datetime(df_bar["date"], format='%Y%m').astype("str")
df["EXTRACT_DE"] = df["EXTRACT_DE"].astype("str")
reg = format(df["CNT"].sum(), ",d")

# 사이드바
with st.sidebar:
    select_multi_brand = st.multiselect(
        "브랜드 선택(다중 선택 가능)",
        df["ORG_CAR_MAKER_KOR"].unique().tolist()
    )
    start_button = st.button("filter apply")
    df2 = df if not start_button or not select_multi_brand else df[df["ORG_CAR_MAKER_KOR"].isin(select_multi_brand)]
    if start_button:
        ui.sidebar_filters_applied()
    ui.sidebar_links()


st.markdown("## 2025 Yearly Summary")
st.markdown(f"#### 2025년 승용 신규등록대수 : {reg}")

st.header("월별 신규등록대수")
tab1, tab2 = st.tabs(["bar", "line"])

midleft_column, midright_column = st.columns([2, 2], gap="large")
botleft_column, botright_column = st.columns(2, gap="large")
bot2left, bot2right = st.columns(2, gap="large")
bot3le, bot3ri = st.columns(2, gap="large")

with tab1:
    fig1 = ch.bar_with_range_selector(
        df_bar, x="date", y="CNT",
        hover=["date", "CNT"], color="CNT",
        labels={"date": "등록날짜", "CNT": "등록대수"},
        height=400
    )
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    fig1_1 = ch.line_with_range_selector(df_bar, x="date", y="CNT")
    st.plotly_chart(fig1_1, use_container_width=True)

with midleft_column:
    st.subheader("외형별 신규등록대수")
    hist = df2.groupby(["CAR_BT"])["CNT"].sum().reset_index().sort_values(by="CNT", ascending=False)
    fig3 = ch.category_bar(hist, x="CAR_BT", y="CNT", color="CAR_BT", labels=dict(CAR_BT="외형", CNT="대수"))
    st.plotly_chart(fig3, use_container_width=True)

with midright_column:
    st.subheader("신규등록대수 연료비중")
    df3 = df2.groupby(["FUEL"])["CNT"].sum().reset_index()
    fig4 = ch.pie_simple(df3, values="CNT", names="FUEL", hole=.3)
    st.plotly_chart(fig4, use_container_width=True)

with botleft_column:
    st.subheader("국산/수입별 신규등록대수")
    df_tmp = df2.groupby(["CL_HMMD_IMP_SE_NM"])["CNT"].sum().reset_index()
    fig5 = ch.category_bar(df_tmp, x="CL_HMMD_IMP_SE_NM", y="CNT", color="CL_HMMD_IMP_SE_NM",
                           labels=dict(CL_HMMD_IMP_SE_NM="국산/수입", CNT="대수"))
    st.plotly_chart(fig5, use_container_width=True)

with botright_column:
    st.subheader("외형별 연료별 신규등록대수 버블차트")
    df4 = df2.groupby(["FUEL", "CAR_BT"])["CNT"].sum().reset_index()
    fig6 = ch.scatter_bubble(df4, x="CAR_BT", y="FUEL", size="CNT", hover_name="CNT",
                             size_max=60, labels=dict(CAR_BT="외형", FUEL="연료"))
    st.plotly_chart(fig6, use_container_width=True)

with bot2left:
    st.subheader("월별 소유자 유형별 신차등록대수")
    df_own = df2.groupby(["EXTRACT_DE", "OWNER_GB"])[["CNT"]].sum().reset_index()
    df_own["EXTRACT_DE"] = pd.to_datetime(df_own["EXTRACT_DE"].astype("str"))
    fig_own = ch.stacked_bar_time(df_own, x="EXTRACT_DE", y="CNT", color="OWNER_GB",
                                  labels=dict(EXTRACT_DE="2024년", CNT="대수"))
    st.plotly_chart(fig_own, use_container_width=True)

with bot2right:
    st.subheader("연령별 신차등록 비중")
    df_age = df.groupby(["AGE"])[["CNT"]].sum().reset_index()
    age_order = ["20대", "30대", "40대", "50대", "60대", "70대", "법인및사업자"]
    fig_age = ch.pie_simple(df_age, values="CNT", names="AGE", hole=.3,
                            category_orders={"AGE": age_order})
    st.plotly_chart(fig_age, use_container_width=True)
idx_lst = df_use.columns[2:].tolist()
idx_lst = ['20'+ x for x in idx_lst]
with bot3le:
    st.subheader("연도별 용도별 신규등록대수")
    use = df_use["CAR_USE"].unique().tolist()
    name = st.selectbox("용도", use)
    sele_use_df = df_use[df_use["CAR_USE"] == name]
    pre_use_df = sele_use_df.iloc[:, 1:].transpose()
    pre_use_df.rename(columns=pre_use_df.iloc[0], inplace=True)
    pre_use_df = pre_use_df.drop(pre_use_df.index[0])
    pre_use_df.index = idx_lst#[2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
    pre_use_df.reset_index(inplace=True)
    pre_use_df.rename(columns={"index": "연도"}, inplace=True)

    numeric_df = pre_use_df.set_index("연도")
    bump_fig, rank_df, sort_fields = ch.bump_from_wide(numeric_df)
    # 원본과 동일 hover 텍스트
    for trace in bump_fig.data:
        trace.hovertemplate = '%{x}<br>등록대수: ' + numeric_df[trace.name].astype(str)
    bump_fig.update_layout(
        xaxis_title="연도",
        yaxis_tickvals=list(range(1, len(sort_fields) + 1)),
        width=600, height=600
    )
    st.plotly_chart(bump_fig, use_container_width=True)

with bot3ri:
    st.subheader("브랜드 모델별 신규등록대수")
    brand = df["ORG_CAR_MAKER_KOR"].unique().tolist(); brand.sort()
    name = st.selectbox("브랜드", brand)
    date_mon = df["EXTRACT_DE"].unique().tolist(); date_mon.sort()
    mon = st.selectbox("등록 월", date_mon)
    df1 = df[(df["ORG_CAR_MAKER_KOR"] == name) & (df["EXTRACT_DE"] == mon)]
    df1 = df1.groupby(["CAR_MOEL_DT"])["CNT"].sum().reset_index().sort_values(by="CNT", ascending=False)
    fig2 = ch.category_bar(df1, x="CAR_MOEL_DT", y="CNT", color="CAR_MOEL_DT",
                           labels=dict(CAR_MOEL_DT="모델", CNT="대수"))
    st.plotly_chart(fig2, use_container_width=True)

footer.render()
