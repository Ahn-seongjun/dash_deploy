import warnings

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app_core import data_loader as dl
from app_core import footer
from app_core import ui
from app_core.nav import render_sidebar_nav

warnings.filterwarnings("ignore")

st.set_page_config(page_title="Overview", layout="wide", initial_sidebar_state="auto")
render_sidebar_nav()


PALETTE = {
    "blue": "#2563eb",
    "cyan": "#06b6d4",
    "green": "#16a34a",
    "orange": "#f97316",
    "red": "#dc2626",
    "ink": "#0f172a",
    "muted": "#64748b",
    "grid": "#e2e8f0",
}

KIND_META = {
    "new": {"label": "신규 등록", "color": PALETTE["blue"]},
    "used": {"label": "이전 등록", "color": PALETTE["cyan"]},
    "erase": {"label": "말소 등록", "color": PALETTE["orange"]},
}

SEGMENT_META = {
    "CAR_SZ": {"label": "차급", "order": ["경형", "소형", "준중형", "중형", "준대형", "대형"]},
    "CAR_BT": {"label": "차형", "order": ["세단", "SUV", "RV", "해치백", "왜건", "쿠페", "픽업트럭", "컨버터블"]},
    "USE_FUEL_NM": {"label": "연료", "order": ["휘발유", "경유", "LPG", "하이브리드", "전기", "수소"]},
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


def delta_percent(current: float, previous: float | None) -> str | None:
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
        margin=dict(l=18, r=18, t=70, b=24),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor=PALETTE["grid"], zeroline=False)
    return fig


def build_trend_figure(monthly: pd.DataFrame, title: str, color: str) -> go.Figure:
    fig = go.Figure(
        go.Scatter(
            x=monthly["month_date"],
            y=monthly["CNT"],
            mode="lines+markers",
            line=dict(color=color, width=3),
            marker=dict(size=7, color=color),
            fill="tozeroy",
            fillcolor="rgba(37, 99, 235, 0.10)" if color == PALETTE["blue"] else None,
            hovertemplate="%{x|%Y-%m}<br>%{y:,.0f}대<extra></extra>",
        )
    )
    fig.update_layout(title=title, hovermode="x unified", showlegend=False)
    fig.update_xaxes(title_text="월", tickformat="%Y-%m")
    fig.update_yaxes(title_text="등록대수")
    return style_figure(fig, height=390)


def build_segment_bar_figure(df: pd.DataFrame, col: str, title: str) -> go.Figure:
    segment = df.groupby(col, as_index=False)["CNT"].sum().sort_values("CNT", ascending=True)
    fig = px.bar(
        segment,
        x="CNT",
        y=col,
        orientation="h",
        text_auto=".2s",
        color_discrete_sequence=[PALETTE["blue"]],
    )
    fig.update_layout(title=title, showlegend=False)
    return style_figure(fig, height=390)


def build_top_model_figure(df: pd.DataFrame, title: str) -> go.Figure:
    top_df = df.sort_values("CNT", ascending=True).tail(10)
    label_col = "MODEL_LABEL"
    top_df = top_df.copy()
    top_df[label_col] = top_df["ORG_CAR_MAKER_KOR"].astype(str) + " / " + top_df["CAR_MOEL_DT"].astype(str)
    fig = px.bar(
        top_df,
        x="CNT",
        y=label_col,
        orientation="h",
        text_auto=".2s",
        color_discrete_sequence=[PALETTE["cyan"]],
    )
    fig.update_layout(title=title, showlegend=False)
    return style_figure(fig, height=390)


def render_top_tables(df: pd.DataFrame, title_prefix: str) -> None:
    left, right = st.columns(2)
    columns = ["RN", "ORG_CAR_MAKER_KOR", "CAR_MOEL_DT", "CNT"]
    rename_map = {
        "RN": "순위",
        "ORG_CAR_MAKER_KOR": "브랜드",
        "CAR_MOEL_DT": "모델",
        "CNT": "대수",
    }

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
    title_key: str,
    top_df: pd.DataFrame,
    monthly_detail_df: pd.DataFrame,
    segment_df: pd.DataFrame,
) -> None:
    meta = KIND_META[title_key]
    monthly = build_monthly_summary(monthly_detail_df)
    latest_year, latest_month, latest_value, previous_value = latest_values(monthly)

    st.subheader(meta["label"])
    metric_cols = st.columns(3)
    with metric_cols[0]:
        st.metric("최신월 대수", format_count(latest_value), delta_percent(latest_value, previous_value), border=True)
    with metric_cols[1]:
        st.metric("누적 대수", format_count(monthly["CNT"].sum()), border=True)
    with metric_cols[2]:
        st.metric("기준월", f"{latest_year}-{str(latest_month).zfill(2)}", border=True)

    trend_col, top_col = st.columns(2, gap="large")
    with trend_col:
        st.plotly_chart(
            build_trend_figure(monthly, f"{meta['label']} 월별 추이", meta["color"]),
            use_container_width=True,
        )
    with top_col:
        st.plotly_chart(
            build_top_model_figure(top_df, f"{meta['label']} 상위 모델"),
            use_container_width=True,
        )

    seg_choice = st.selectbox(
        "구조 기준",
        list(SEGMENT_META.keys()),
        format_func=lambda x: SEGMENT_META[x]["label"],
        key=f"{title_key}_segment_choice",
    )
    seg_col = seg_choice
    seg_filtered = segment_df.copy()
    if seg_col not in seg_filtered.columns:
        st.info("구조 데이터를 표시할 수 없습니다.")
    else:
        latest_seg_df = seg_filtered[seg_filtered["EXTRACT_DE"] == seg_filtered["EXTRACT_DE"].max()].copy()
        chart_col1, chart_col2 = st.columns(2, gap="large")
        with chart_col1:
            st.plotly_chart(
                build_segment_bar_figure(
                    latest_seg_df,
                    seg_col,
                    f"{latest_year}-{str(latest_month).zfill(2)} {SEGMENT_META[seg_col]['label']} 구성",
                ),
                use_container_width=True,
            )
        with chart_col2:
            render_top_tables(top_df, "모델")


inject_page_style()

data = dl.get_overview_data(base_dir="data")
new_top = data["new_top"].copy()
use_top = data["use_top"].copy()
ersr_top = data["ersr_top"].copy()
new_mon_cnt = data["new_mon_cnt"].copy()
used_mon_cnt = data["used_mon_cnt"].copy()
er_mon_cnt = data["er_mon_cnt"].copy()
new_seg = data["new_seg"].copy()
used_seg = data["used_seg"].copy()
er_seg = data["er_seg"].copy()

for frame in (new_seg, used_seg, er_seg):
    if "EXTRACT_DE" in frame.columns:
        frame["EXTRACT_DE"] = pd.to_numeric(frame["EXTRACT_DE"], errors="coerce").fillna(0).astype(int)

mon_new = build_monthly_summary(new_mon_cnt)
mon_used = build_monthly_summary(used_mon_cnt)
mon_er = build_monthly_summary(er_mon_cnt)

latest_year, latest_month, latest_new, prev_new = latest_values(mon_new)
_, _, latest_used, prev_used = latest_values(mon_used)
_, _, latest_er, prev_er = latest_values(mon_er)

with st.sidebar:
    ui.sidebar_links()

st.title(":material/stacked_line_chart: Mobility Overview")
st.markdown(
    f"기준월은 **{latest_year}-{str(latest_month).zfill(2)}**이며, 신규·이전·말소 등록의 최신 흐름과 주요 구성, 상위 모델을 한 화면에서 확인할 수 있게 정리했습니다."
)

metric_cols = st.columns(3)
with metric_cols[0]:
    st.metric("신규 등록", format_count(latest_new), delta_percent(latest_new, prev_new), border=True)
with metric_cols[1]:
    st.metric("이전 등록", format_count(latest_used), delta_percent(latest_used, prev_used), border=True)
with metric_cols[2]:
    st.metric("말소 등록", format_count(latest_er), delta_percent(latest_er, prev_er), border=True)

ui.apply_tab_style()
tab1, tab2, tab3 = st.tabs(["신규", "이전", "말소"])

with tab1:
    render_kind_tab("new", new_top, new_mon_cnt, new_seg)
with tab2:
    render_kind_tab("used", use_top, used_mon_cnt, used_seg)
with tab3:
    render_kind_tab("erase", ersr_top, er_mon_cnt, er_seg)

footer.render()
