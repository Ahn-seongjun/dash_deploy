import warnings
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from app_core import charts as od
from app_core import data_loader as dl
from app_core import footer
from app_core import ui
from app_core.nav import render_sidebar_nav

warnings.filterwarnings("ignore")

st.set_page_config(page_title="Overview", layout="wide", initial_sidebar_state="auto")
render_sidebar_nav()


PALETTE = {
    "primary": "#1d4ed8",
    "secondary": "#0f766e",
    "accent": "#f97316",
    "positive": "#16a34a",
    "negative": "#dc2626",
    "ink": "#0f172a",
    "muted": "#64748b",
    "line_1": "#1d4ed8",
    "line_2": "#06b6d4",
    "surface": "#f8fafc",
    "grid": "#e2e8f0",
}

SEGMENT_OPTIONS = ["차급", "외형", "연료"]
SEGMENT_DICT = {
    "차급": ["CAR_SZ", ["소형", "경형", "준중형", "중형", "준대형", "대형"]],
    "외형": ["CAR_BT", ["SUV", "세단", "RV", "해치백", "픽업트럭", "컨버터블", "쿠페", "왜건"]],
    "연료": ["USE_FUEL_NM", ["휘발유", "경유", "LPG", "하이브리드", "전기", "수소"]],
}
FEATURE_DICT = {
    "브랜드": "ORG_CAR_MAKER_KOR",
    "모델": "CAR_MOEL_DT",
    "차급": "CAR_SZ",
    "외형": "CAR_BT",
    "연료": "USE_FUEL_NM",
}
FEATURE_OPTIONS = list(FEATURE_DICT.keys())
KIND_META = {
    "신규": {"label": "신규등록", "help": "이삿짐, 부활차 제외"},
    "이전": {"label": "이전등록", "help": "실거래(매도, 알선, 개인거래) 대상 집계"},
    "말소": {"label": "말소등록", "help": "폐차, 수출예정 대상 집계"},
}


def inject_page_style() -> None:
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


def delta_percent(current: float, previous: float) -> str | None:
    if previous in (None, 0) or pd.isna(previous):
        return None
    return f"{((current - previous) / previous) * 100:+.1f}%"


def build_monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    out = df.groupby(["YEA", "MON"], as_index=False)["CNT"].sum().sort_values(["YEA", "MON"])
    out["month_date"] = pd.to_datetime(
        out["YEA"].astype(str) + out["MON"].astype(str).str.zfill(2),
        format="%Y%m",
    )
    out["month_label"] = out["month_date"].dt.strftime("%Y-%m")
    return out


def latest_values(monthly: pd.DataFrame) -> tuple[int, int, float, float | None]:
    latest = monthly.iloc[-1]
    previous_value = float(monthly.iloc[-2]["CNT"]) if len(monthly) > 1 else None
    return int(latest["YEA"]), int(latest["MON"]), float(latest["CNT"]), previous_value


def style_figure(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        height=height,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color=PALETTE["ink"]),
        margin=dict(l=18, r=18, t=86, b=24),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor=PALETTE["grid"], zeroline=False)
    return fig


def build_trend_figure(monthly: pd.DataFrame, title: str) -> go.Figure:
    pivot = monthly.pivot_table(index="MON", columns="YEA", values="CNT", aggfunc="sum")
    latest_year = pivot.columns.max()
    prev_year = latest_year - 1
    yoy = ((pivot[latest_year] - pivot[prev_year]) / pivot[prev_year].replace({0: pd.NA}) * 100).fillna(0)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=yoy.index,
            y=yoy.values,
            name=f"{latest_year} YoY",
            marker=dict(color=[PALETTE["positive"] if v >= 0 else PALETTE["negative"] for v in yoy.values]),
            opacity=0.28,
            text=[f"{v:.1f}%" for v in yoy.values],
            textposition="outside",
        ),
        secondary_y=True,
    )
    line_colors = [PALETTE["line_1"], PALETTE["line_2"], PALETTE["accent"]]
    for idx, year in enumerate(sorted(monthly["YEA"].unique())):
        sub = monthly[monthly["YEA"] == year]
        fig.add_trace(
            go.Scatter(
                x=sub["MON"],
                y=sub["CNT"],
                mode="lines+markers",
                name=f"{year} 등록대수",
                line=dict(width=3, color=line_colors[idx % len(line_colors)]),
                marker=dict(size=7, color=line_colors[idx % len(line_colors)]),
            ),
            secondary_y=False,
        )
    fig.update_layout(
        title=title,
        hovermode="x unified",
        bargap=0.35,
    )
    fig.update_xaxes(title_text="월")
    fig.update_yaxes(title_text="등록대수", secondary_y=False)
    fig.update_yaxes(title_text="전년 대비(%)", secondary_y=True, showgrid=False)
    return style_figure(fig, height=430)


def build_treemap_figure(df: pd.DataFrame, path1: str, path2: str, title: str) -> go.Figure:
    fig = px.treemap(
        df,
        path=[px.Constant("전체"), path1, path2],
        values="CNT",
        color=path1,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_traces(
        root_color="#f8fafc",
        textinfo="label+value",
        hovertemplate="%{label}<br>등록대수 %{value:,.0f}대<extra></extra>",
    )
    fig.update_layout(title=title)
    return style_figure(fig, height=460)


def build_donut_figure(df: pd.DataFrame, label_col: str, title: str, category_order: list[str]) -> go.Figure:
    fig = px.pie(
        df,
        values="CNT",
        names=label_col,
        hole=0.62,
        category_orders={label_col: category_order},
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
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.08,
            x=0,
            font=dict(size=11),
        ),
    )
    return style_figure(fig, height=400)


def build_area_figure(df: pd.DataFrame, label_col: str, title: str, category_order: list[str]) -> go.Figure:
    area_df = df.groupby(["EXTRACT_DE", label_col], as_index=False)["CNT"].sum()
    area_df["EXTRACT_DE"] = pd.to_datetime(area_df["EXTRACT_DE"].astype(str), format="%Y%m")
    fig = px.area(
        area_df,
        x="EXTRACT_DE",
        y="CNT",
        color=label_col,
        category_orders={label_col: category_order},
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(title=title, hovermode="x unified")
    fig.update_xaxes(dtick="M1", tickformat="%Y-%m", title_text="날짜")
    fig.update_yaxes(title_text="등록대수")
    return style_figure(fig, height=400)


def build_change_bar_figure(
    tbl: pd.DataFrame,
    dim_col: str,
    title: str,
    direction: str,
    topn: int = 5,
) -> go.Figure:
    filtered = tbl[(tbl["CNT_BASE"] >= 20) & (tbl["CNT_COMP"] >= 20)].copy()
    filtered["CHANGE_PCT"] = pd.to_numeric(filtered["CHANGE_PCT"], errors="coerce")
    filtered = filtered.dropna(subset=["CHANGE_PCT"])

    if filtered.empty:
        fig = go.Figure()
        fig.update_layout(
            title=title,
            xaxis_title="증감률(%)",
            yaxis_title=dim_col,
            annotations=[
                dict(
                    text="표시할 변동 데이터가 없습니다.",
                    x=0.5,
                    y=0.5,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=14, color=PALETTE["muted"]),
                )
            ],
        )
        return style_figure(fig, height=380)

    if direction == "상위 TOP":
        plot_df = filtered.nlargest(topn, "CHANGE_PCT").sort_values("CHANGE_PCT", ascending=True)
    else:
        plot_df = filtered.nsmallest(topn, "CHANGE_PCT").sort_values("CHANGE_PCT", ascending=True)

    fig = go.Figure(
        go.Bar(
            x=plot_df["CHANGE_PCT"],
            y=plot_df[dim_col],
            orientation="h",
            text=plot_df["CHANGE_PCT"].round(1).astype(str) + "%",
            textposition="outside",
            marker=dict(
                color=[
                    PALETTE["positive"] if value >= 0 else PALETTE["negative"]
                    for value in plot_df["CHANGE_PCT"]
                ]
            ),
            hovertemplate="%{y}<br>증감률 %{x:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(title=title, xaxis_title="증감률(%)", yaxis_title=dim_col, showlegend=False)
    fig.update_xaxes(zeroline=True, zerolinecolor=PALETTE["grid"])
    return style_figure(fig, height=380)


def render_top_tables(df: pd.DataFrame, title_prefix: str, show_detail_model: bool = False) -> None:
    left, right = st.columns(2)
    columns = ["RN", "ORG_CAR_MAKER_KOR", "CAR_MOEL_DT", "CNT"]
    rename_map = {"RN": "순위", "ORG_CAR_MAKER_KOR": "브랜드", "CAR_MOEL_DT": "모델", "CNT": "대수"}
    if show_detail_model and "CAR_MODEL_KOR" in df.columns:
        columns = ["RN", "ORG_CAR_MAKER_KOR", "CAR_MOEL_DT", "CAR_MODEL_KOR", "CNT"]
        rename_map["CAR_MODEL_KOR"] = "상세모델"
    with left:
        st.subheader(f"국산 {title_prefix} TOP 10")
        local_df = df[df["CL_HMMD_IMP_SE_NM"] == "국산"][columns].copy()
        local_df = local_df.rename(columns=rename_map).set_index("순위")
        local_df["대수"] = local_df["대수"].map("{:,}".format)
        st.dataframe(local_df, use_container_width=True)
    with right:
        st.subheader(f"수입 {title_prefix} TOP 10")
        import_df = df[df["CL_HMMD_IMP_SE_NM"] == "수입"][columns].copy()
        import_df = import_df.rename(columns=rename_map).set_index("순위")
        import_df["대수"] = import_df["대수"].map("{:,}".format)
        st.dataframe(import_df, use_container_width=True)


def render_kind_tab(
    kind_key: str,
    top_df: pd.DataFrame,
    monthly_summary_df: pd.DataFrame,
    monthly_detail_df: pd.DataFrame,
    segment_df: pd.DataFrame,
    latest_year: int,
    latest_month: int,
) -> None:
    meta = KIND_META[kind_key]
    render_top_tables(top_df, "모델", show_detail_model=(kind_key == "이전"))

    st.subheader(f"{meta['label']} 추이 및 전년 비교")
    st.caption(meta["help"])
    trend_fig = build_trend_figure(monthly_summary_df, title=f"{meta['label']} 월별 추이")
    st.plotly_chart(trend_fig, use_container_width=True)

    st.subheader(f"{meta['label']} 구조 탐색")
    st.caption("브랜드/모델, 차급, 외형, 연료 기준으로 구조를 빠르게 확인할 수 있습니다.")
    feat_clean = FEATURE_OPTIONS[:]
    key_prefix = {"신규": "new", "이전": "used", "말소": "ersr"}[kind_key]

    if f"{key_prefix}_seg1" not in st.session_state or st.session_state[f"{key_prefix}_seg1"] not in feat_clean:
        st.session_state[f"{key_prefix}_seg1"] = feat_clean[0]

    seg2_options = [item for item in feat_clean if item != st.session_state[f"{key_prefix}_seg1"]]
    if f"{key_prefix}_seg2" not in st.session_state or st.session_state[f"{key_prefix}_seg2"] not in seg2_options:
        st.session_state[f"{key_prefix}_seg2"] = seg2_options[0]

    t1, t2 = st.columns(2)
    with t1:
        st.selectbox("분류 1", feat_clean, key=f"{key_prefix}_seg1")
    with t2:
        seg2_options = [item for item in feat_clean if item != st.session_state[f"{key_prefix}_seg1"]]
        if st.session_state[f"{key_prefix}_seg2"] not in seg2_options:
            st.session_state[f"{key_prefix}_seg2"] = seg2_options[0]
        st.selectbox("분류 2", seg2_options, key=f"{key_prefix}_seg2")

    tree_col1 = FEATURE_DICT[st.session_state[f"{key_prefix}_seg1"]]
    tree_col2 = FEATURE_DICT[st.session_state[f"{key_prefix}_seg2"]]
    treemap_fig = build_treemap_figure(
        monthly_detail_df,
        tree_col1,
        tree_col2,
        title=f"{meta['label']} 트리맵",
    )
    st.plotly_chart(treemap_fig, use_container_width=True, key=f"{key_prefix}_treemap")

    segment_choice = st.selectbox("세부 구분", SEGMENT_OPTIONS, key=f"{key_prefix}_segment_choice")
    segment_col, segment_order = SEGMENT_DICT[segment_choice]
    latest_segment_df = (
        segment_df[segment_df["EXTRACT_DE"] == segment_df["EXTRACT_DE"].max()]
        .groupby(segment_col, as_index=False)["CNT"]
        .sum()
    )
    donut_col, area_col = st.columns(2)
    with donut_col:
        donut_fig = build_donut_figure(
            latest_segment_df,
            label_col=segment_col,
            title=f"{latest_month}월 {segment_choice}별 점유율",
            category_order=segment_order,
        )
        st.plotly_chart(donut_fig, use_container_width=True, key=f"{key_prefix}_donut")
    with area_col:
        area_fig = build_area_figure(
            segment_df,
            label_col=segment_col,
            title=f"{latest_year}년 {segment_choice}별 누적 흐름",
            category_order=segment_order,
        )
        st.plotly_chart(area_fig, use_container_width=True, key=f"{key_prefix}_area")


inject_page_style()

data = dl.get_overview_data()
new_top = data["new_top"]
use_top = data["use_top"]
ersr_top = data["ersr_top"]
new_mon_cnt = data["new_mon_cnt"]
used_mon_cnt = data["used_mon_cnt"]
er_mon_cnt = data["er_mon_cnt"]
new_seg = data["new_seg"].copy()
used_seg = data["used_seg"].copy()
er_seg = data["er_seg"].copy()

for frame in (new_seg, used_seg, er_seg):
    frame["EXTRACT_DE"] = frame["EXTRACT_DE"].astype(str)

mon_new = build_monthly_summary(new_mon_cnt)
mon_used = build_monthly_summary(used_mon_cnt)
mon_er = build_monthly_summary(er_mon_cnt)

latest_year, latest_month, latest_new, prev_new = latest_values(mon_new)
_, _, latest_used, prev_used = latest_values(mon_used)
_, _, latest_er, prev_er = latest_values(mon_er)

operating_total = 26643463
operating_prev = 26633482
hero_text = f"{latest_year}년 {latest_month}월 기준 자동차 등록 핵심 흐름"

with st.sidebar:
    ui.sidebar_links()

st.title(":material/stacked_line_chart: Mobility Overview")
st.markdown(
    f"**{hero_text}**를 기준으로 신규, 이전, 말소 등록 현황을 한 화면에서 비교할 수 있게 정리했습니다.  \n"
    "탭별로 시장 규모와 구성 변화를 빠르게 살펴보고, 하단에서는 월간·연간 변동 포인트를 확인할 수 있습니다."
)

spark_new = mon_new["CNT"].tolist()
spark_used = mon_used["CNT"].tolist()
spark_er = mon_er["CNT"].tolist()

metric_cols = st.columns(4)
with metric_cols[0]:
    st.metric(
        "신규 등록",
        format_count(latest_new),
        delta_percent(latest_new, prev_new),
        border=True,
        chart_data=spark_new,
        chart_type="area",
    )
with metric_cols[1]:
    st.metric(
        "이전 등록",
        format_count(latest_used),
        delta_percent(latest_used, prev_used),
        border=True,
        chart_data=spark_used,
        chart_type="line",
    )
with metric_cols[2]:
    st.metric(
        "말소 등록",
        format_count(latest_er),
        delta_percent(latest_er, prev_er),
        border=True,
        chart_data=spark_er,
        chart_type="bar",
    )
with metric_cols[3]:
    st.metric(
        "운행 등록",
        format_count(operating_total),
        delta_percent(operating_total, operating_prev),
        border=True,
    )

st.caption("상단 지표는 최근월 기준이며, 우측 수치일수록 현재 시장 체감 흐름을 빠르게 보여주도록 구성했습니다.")

ui.apply_tab_style()
tab1, tab2, tab3 = st.tabs(["신규", "이전", "말소"])

with tab1:
    render_kind_tab("신규", new_top, mon_new, new_mon_cnt, new_seg, latest_year, latest_month)
with tab2:
    render_kind_tab("이전", use_top, mon_used, used_mon_cnt, used_seg, latest_year, latest_month)
with tab3:
    render_kind_tab("말소", ersr_top, mon_er, er_mon_cnt, er_seg, latest_year, latest_month)

st.subheader(":material/query_stats: 변동 포인트 비교")
st.caption("선택한 기준으로 전월 대비와 전년 동월 대비 상·하위 변화를 확인합니다.")

control_col, summary_col = st.columns([2.4, 1.2])
with control_col:
    reg_kind = st.selectbox("데이터 선택", list(KIND_META.keys()), key="overview_reg_kind")
    dim_col = st.selectbox("비교 기준 선택", FEATURE_OPTIONS, key="overview_feat")
with summary_col:
    st.markdown(
        f"""
        <div style="padding:14px 16px; border:1px solid #e2e8f0; border-radius:16px; background:#f8fafc; margin-top:28px;">
        <div style="font-weight:700; color:{PALETTE['ink']}; margin-bottom:6px;">현재 선택</div>
        <div style="color:{PALETTE['muted']};">{KIND_META[reg_kind]['label']} / {dim_col}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    top_bottom_choice = st.radio(
        "비교 방향",
        ["상위 TOP", "하위 TOP"],
        horizontal=True,
        key="overview_top_bottom_choice",
    )

detail_map = {"신규": new_mon_cnt.copy(), "이전": used_mon_cnt.copy(), "말소": er_mon_cnt.copy()}
df_detail = detail_map[reg_kind]
base_month = pd.to_datetime(new_seg["EXTRACT_DE"].max(), format="%Y%m").strftime("%Y-%m")

tbl_mom = od.compute_change_table(df_detail, FEATURE_DICT[dim_col], base_month, mode="MoM")
mom_comp = tbl_mom["COMP_MONTH"].iloc[0] if not tbl_mom.empty else "-"
mom_base = tbl_mom["BASE_MONTH"].iloc[0] if not tbl_mom.empty else "-"
fig_mom = build_change_bar_figure(
    tbl_mom,
    FEATURE_DICT[dim_col],
    title=f"MoM · {top_bottom_choice} ({mom_base} vs {mom_comp})",
    direction=top_bottom_choice,
)

tbl_yoy = od.compute_change_table(df_detail, FEATURE_DICT[dim_col], base_month, mode="YoY")
yoy_comp = tbl_yoy["COMP_MONTH"].iloc[0] if not tbl_yoy.empty else "-"
yoy_base = tbl_yoy["BASE_MONTH"].iloc[0] if not tbl_yoy.empty else "-"
fig_yoy = build_change_bar_figure(
    tbl_yoy,
    FEATURE_DICT[dim_col],
    title=f"YoY · {top_bottom_choice} ({yoy_base} vs {yoy_comp})",
    direction=top_bottom_choice,
)

st.plotly_chart(fig_mom, use_container_width=True)
st.plotly_chart(fig_yoy, use_container_width=True)

footer.render()
