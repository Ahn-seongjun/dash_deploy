import warnings

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app_core import charts as ch
from app_core import data_loader as dl
from app_core import footer
from app_core import ui
from app_core.nav import render_sidebar_nav

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="신규등록 Summary",
    layout="wide",
    initial_sidebar_state="auto",
)
render_sidebar_nav()


PALETTE = {
    "ink": "#0f172a",
    "muted": "#64748b",
    "grid": "#e2e8f0",
    "blue": "#2563eb",
    "cyan": "#06b6d4",
    "green": "#16a34a",
    "orange": "#f97316",
    "surface": "#f8fafc",
}

AGE_ORDER = ["20대", "30대", "40대", "50대", "60대", "70대", "법인및사업자"]


def inject_style() -> None:
    st.markdown(
        """
        <style>
        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            border: 1px solid #dbe7ff;
            border-radius: 18px;
            padding: 10px 12px;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
        }
        div[data-testid="stDataFrame"] {
            border-radius: 16px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_count(value: float) -> str:
    return f"{int(round(value)):,}"


def format_pct(value: float) -> str:
    return f"{value:.1f}%"


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def summarize_monthly(df: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        df.assign(month=pd.to_datetime(df["EXTRACT_DE"].astype(str), format="%Y%m%d").dt.to_period("M").dt.to_timestamp())
        .groupby("month", as_index=False)["CNT"]
        .sum()
        .sort_values("month")
    )
    monthly["mom_pct"] = monthly["CNT"].pct_change() * 100
    return monthly


def style_figure(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        height=height,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color=PALETTE["ink"]),
        margin=dict(l=20, r=20, t=70, b=28),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(255,255,255,0.85)",
            borderwidth=0,
        ),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor=PALETTE["grid"], zeroline=False)
    return fig


def build_donut(df: pd.DataFrame, label_col: str, title: str, category_orders: dict | None = None) -> go.Figure:
    fig = px.pie(
        df,
        values="CNT",
        names=label_col,
        hole=0.62,
        category_orders=category_orders,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        insidetextorientation="horizontal",
        marker=dict(line=dict(color="#ffffff", width=3)),
        hovertemplate="%{label}<br>%{value:,.0f}대 (%{percent})<extra></extra>",
        pull=[0.01] * len(df),
    )
    fig.update_layout(
        title=title,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            font=dict(size=11),
            bgcolor="rgba(255,255,255,0.85)",
            borderwidth=0,
        ),
    )
    return style_figure(fig, height=400)


def build_trend_tabs(df_bar: pd.DataFrame) -> tuple[go.Figure, go.Figure]:
    bar_fig = ch.bar_with_range_selector(
        df_bar,
        x="date",
        y="CNT",
        hover=["date", "CNT"],
        color="CNT",
        labels={"date": "등록날짜", "CNT": "등록대수"},
        height=420,
    )
    bar_fig.update_layout(showlegend=False, title="월별 등록대수 Bar View")
    style_figure(bar_fig, height=420)

    line_fig = ch.line_with_range_selector(df_bar, x="date", y="CNT")
    line_fig.update_layout(title="월별 등록대수 Line View")
    line_fig.update_traces(line=dict(width=3, color=PALETTE["blue"]))
    style_figure(line_fig, height=420)
    return bar_fig, line_fig


def build_bar(df: pd.DataFrame, x: str, y: str, title: str, color: str, orientation: str | None = None) -> go.Figure:
    fig = px.bar(
        df,
        x=x,
        y=y,
        color=color,
        orientation=orientation,
        text_auto=".2s",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_layout(title=title, showlegend=False)
    return style_figure(fig, height=420)


def build_scatter(df: pd.DataFrame, title: str) -> go.Figure:
    fig = px.scatter(
        df,
        x="CAR_BT",
        y="FUEL",
        size="CNT",
        color="CNT",
        hover_name="CNT",
        size_max=60,
        color_continuous_scale="Blues",
        labels={"CAR_BT": "외형", "FUEL": "연료", "CNT": "대수"},
    )
    fig.update_layout(title=title, coloraxis_showscale=False)
    return style_figure(fig, height=420)


inject_style()

data = dl.get_newreg_data(base_dir="data/")
df_bar = data["monthly"].copy().reset_index()
df_use = data["cum"].copy()
df = data["dim"].copy()

df_bar["date"] = pd.to_datetime(df_bar["date"], format="%Y%m").astype(str)
df["EXTRACT_DE"] = df["EXTRACT_DE"].astype(str)
df["CNT"] = pd.to_numeric(df["CNT"], errors="coerce").fillna(0)
year_label = pd.to_datetime(df["EXTRACT_DE"], format="%Y%m%d").dt.year.max()

with st.sidebar:
    select_multi_brand = st.multiselect(
        "브랜드",
        sorted(df["ORG_CAR_MAKER_KOR"].dropna().astype(str).unique().tolist()),
    )
    selected_body = st.multiselect(
        "외형",
        sorted(df["CAR_BT"].dropna().astype(str).unique().tolist()),
    )
    selected_fuel = st.multiselect(
        "연료",
        sorted(df["FUEL"].dropna().astype(str).unique().tolist()),
    )
    ui.sidebar_links()

filtered_df = df.copy()
if select_multi_brand:
    filtered_df = filtered_df[filtered_df["ORG_CAR_MAKER_KOR"].isin(select_multi_brand)]
if selected_body:
    filtered_df = filtered_df[filtered_df["CAR_BT"].isin(selected_body)]
if selected_fuel:
    filtered_df = filtered_df[filtered_df["FUEL"].isin(selected_fuel)]

if filtered_df.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다. 필터를 조정해 주세요.")
    footer.render()
    st.stop()

monthly_summary = summarize_monthly(filtered_df)
latest_month = monthly_summary["month"].max()
latest_value = float(monthly_summary.loc[monthly_summary["month"] == latest_month, "CNT"].iloc[0])
prev_value = float(monthly_summary.iloc[-2]["CNT"]) if len(monthly_summary) > 1 else 0.0
mom_pct = safe_ratio(latest_value - prev_value, prev_value) * 100 if prev_value else 0.0

total_cnt = float(filtered_df["CNT"].sum())
domestic_cnt = float(
    filtered_df.loc[filtered_df["CL_HMMD_IMP_SE_NM"].astype(str) == "국산", "CNT"].sum()
)
domestic_share = safe_ratio(domestic_cnt, total_cnt) * 100

top_brand = (
    filtered_df.groupby("ORG_CAR_MAKER_KOR")["CNT"].sum().sort_values(ascending=False)
)
top_brand_name = str(top_brand.index[0]) if not top_brand.empty else "-"
top_brand_share = safe_ratio(float(top_brand.iloc[0]), float(top_brand.sum())) * 100 if not top_brand.empty else 0.0

top_body = filtered_df.groupby("CAR_BT")["CNT"].sum().sort_values(ascending=False)
top_body_name = str(top_body.index[0]) if not top_body.empty else "-"

st.title(":material/analytics: 신규등록 상세 분석")
# st.markdown(
#     f"**{year_label}년 신규등록 데이터**를 기준으로 월별 흐름, 외형/연료/소유자 구조, 브랜드·모델 상세를 더 깊게 볼 수 있도록 구성한 상세 대시보드입니다.  \n"
#     "Showcase가 전체 구조를 빠르게 읽는 화면이라면, 이 페이지는 실제 분석용 세부 차트를 집중적으로 배치한 버전입니다."
# )

# metric_cols = st.columns(4)
# with metric_cols[0]:
#     st.metric("연간 신규등록", format_count(total_cnt), border=True)
# with metric_cols[1]:
#     st.metric("최근월 등록", format_count(latest_value), format_pct(mom_pct), border=True)
# with metric_cols[2]:
#     st.metric("국산 비중", format_pct(domestic_share), f"외산 {format_pct(100 - domestic_share)}", border=True)
# with metric_cols[3]:
#     st.metric("1위 브랜드 점유율", format_pct(top_brand_share), top_brand_name, border=True)

# st.markdown(
#     f"""
#     <div style="padding:16px 18px; border:1px solid #dbeafe; border-radius:18px; background:linear-gradient(180deg, #ffffff 0%, #f8fbff 100%); margin:10px 0 18px 0;">
#       <div style="font-size:15px; color:#0f172a; font-weight:700; margin-bottom:6px;">{year_label}년 상세 요약</div>
#       <div style="font-size:14px; color:#334155; line-height:1.6;">
#         누적 신규등록은 <b>{format_count(total_cnt)}대</b>이며, 최근월 등록은 <b>{format_count(latest_value)}대</b>입니다.
#         최다 브랜드는 <b>{top_brand_name}</b>, 가장 비중이 큰 외형은 <b>{top_body_name}</b>입니다.
#       </div>
#     </div>
#     """,
#     unsafe_allow_html=True,
# )

st.subheader(":material/trending_up: 월별 신규등록 추이")
#st.caption("세부 분석에 앞서 연간 월별 흐름을 bar/line 두 방식으로 확인합니다.")
tab1, tab2 = st.tabs(["Bar View", "Line View"])
bar_fig, line_fig = build_trend_tabs(df_bar)
with tab1:
    st.plotly_chart(bar_fig, use_container_width=True)
with tab2:
    st.plotly_chart(line_fig, use_container_width=True)

st.subheader(":material/widgets: 세부 구조 분석")
#st.caption("외형, 연료, 국산/수입, 소유자, 연령대 기준의 구조를 한 번에 비교합니다.")

row1_col1, row1_col2 = st.columns(2, gap="large")
row2_col1, row2_col2 = st.columns(2, gap="large")
row3_col1, row3_col2 = st.columns(2, gap="large")

with row1_col1:
    hist = filtered_df.groupby("CAR_BT", as_index=False)["CNT"].sum().sort_values("CNT", ascending=False)
    fig = build_bar(hist, x="CAR_BT", y="CNT", title="외형별 신규등록대수", color="CAR_BT")
    st.plotly_chart(fig, use_container_width=True)

with row1_col2:
    fuel_df = filtered_df.groupby("FUEL", as_index=False)["CNT"].sum()
    fig = build_donut(fuel_df, "FUEL", "신규등록대수 연료 비중")
    st.plotly_chart(fig, use_container_width=True)

with row2_col1:
    origin_df = filtered_df.groupby("CL_HMMD_IMP_SE_NM", as_index=False)["CNT"].sum()
    fig = build_bar(origin_df, x="CL_HMMD_IMP_SE_NM", y="CNT", title="국산/수입별 신규등록대수", color="CL_HMMD_IMP_SE_NM")
    st.plotly_chart(fig, use_container_width=True)

with row2_col2:
    bubble_df = filtered_df.groupby(["FUEL", "CAR_BT"], as_index=False)["CNT"].sum()
    fig = build_scatter(bubble_df, "외형별 · 연료별 신규등록 버블")
    st.plotly_chart(fig, use_container_width=True)

with row3_col1:
    own_df = filtered_df.groupby(["EXTRACT_DE", "OWNER_GB"], as_index=False)["CNT"].sum()
    own_df["EXTRACT_DE"] = pd.to_datetime(own_df["EXTRACT_DE"].astype(str))
    fig = px.bar(
        own_df,
        x="EXTRACT_DE",
        y="CNT",
        color="OWNER_GB",
        barmode="stack",
        color_discrete_sequence=px.colors.qualitative.Set2,
        title="월별 소유자 유형별 신규등록대수",
    )
    fig.update_xaxes(dtick="M1", tickformat="%Y-%m", title_text="월")
    fig.update_yaxes(title_text="등록대수")
    st.plotly_chart(style_figure(fig, height=420), use_container_width=True)

with row3_col2:
    age_df = filtered_df.groupby("AGE", as_index=False)["CNT"].sum()
    fig = build_donut(age_df, "AGE", "연령별 신규등록 비중", {"AGE": AGE_ORDER})
    st.plotly_chart(fig, use_container_width=True)

st.subheader(":material/account_tree: 용도 및 브랜드 상세")
#st.caption("기존 summary 페이지의 깊이 있는 분석 요소는 그대로 유지하면서 시각 톤만 정리했습니다.")

detail_col1, detail_col2 = st.columns(2, gap="large")

idx_lst = ["20" + x for x in df_use.columns[2:].tolist()]
with detail_col1:
    use_name = st.selectbox("용도 선택", df_use["CAR_USE"].unique().tolist())
    sele_use_df = df_use[df_use["CAR_USE"] == use_name]
    pre_use_df = sele_use_df.iloc[:, 1:].transpose()
    pre_use_df.rename(columns=pre_use_df.iloc[0], inplace=True)
    pre_use_df = pre_use_df.drop(pre_use_df.index[0])
    pre_use_df.index = idx_lst
    pre_use_df.reset_index(inplace=True)
    pre_use_df.rename(columns={"index": "연도"}, inplace=True)

    numeric_df = pre_use_df.set_index("연도")
    bump_fig, rank_df, sort_fields = ch.bump_from_wide(numeric_df)
    for trace in bump_fig.data:
        trace.hovertemplate = "%{x}<br>등록대수: " + numeric_df[trace.name].astype(str)
    bump_fig.update_layout(
        #title="연도별 용도별 신규등록대수",
        xaxis_title="연도",
        yaxis_tickvals=list(range(1, len(sort_fields) + 1)),
    )
    st.plotly_chart(style_figure(bump_fig, height=520), use_container_width=True)

with detail_col2:
    brand = sorted(filtered_df["ORG_CAR_MAKER_KOR"].dropna().astype(str).unique().tolist())
    selected_brand = st.selectbox("브랜드 선택", brand)
    date_mon = sorted(filtered_df["EXTRACT_DE"].dropna().astype(str).unique().tolist())
    selected_mon = st.selectbox("등록 월 선택", date_mon)
    df1 = filtered_df[
        (filtered_df["ORG_CAR_MAKER_KOR"].astype(str) == selected_brand)
        & (filtered_df["EXTRACT_DE"].astype(str) == selected_mon)
    ]
    df1 = (
        df1.groupby("CAR_MOEL_DT", as_index=False)["CNT"]
        .sum()
        .sort_values("CNT", ascending=False)
        .head(20)
    )
    fig = px.bar(
        df1,
        x="CAR_MOEL_DT",
        y="CNT",
        color="CAR_MOEL_DT",
        text_auto=".2s",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        title="브랜드 모델별 신규등록대수 Top 20",
    )
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title_text="모델")
    fig.update_yaxes(title_text="등록대수")
    st.plotly_chart(style_figure(fig, height=520), use_container_width=True)

footer.render()
