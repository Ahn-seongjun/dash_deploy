import warnings

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app_core import data_loader as dl
from app_core import ui
from app_core.nav import render_sidebar_nav

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="말소등록 Summary",
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
    "red": "#dc2626",
}

DOMESTIC_LABELS = {"국산", "국내", "국산차"}


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


def format_signed_count(value: float) -> str:
    rounded = int(round(value))
    sign = "+" if rounded > 0 else ""
    return f"{sign}{rounded:,}대"


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def pct_change(current: float, previous: float | None) -> float | None:
    if previous in (None, 0) or pd.isna(previous):
        return None
    return (current - previous) / previous * 100


def first_existing(columns: list[str], candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def resolve_columns(df: pd.DataFrame) -> dict[str, str | None]:
    columns = df.columns.tolist()
    return {
        "date": first_existing(columns, ["EXTRACT_DE"]),
        "count": first_existing(columns, ["CNT", "count"]),
        "origin": first_existing(columns, ["CL_HMMD_IMP_SE_NM"]),
        "brand": first_existing(columns, ["ORG_CAR_MAKER_KOR"]),
        "model": first_existing(columns, ["CAR_MOEL_DT"]),
        "fuel": first_existing(columns, ["FUEL", "USE_FUEL_NM"]),
        "user_age": first_existing(columns, ["AGE", "SOU_AGE"]),
        "f_year": first_existing(columns, ["F_YEAR"]),
    }


def parse_date_series(series: pd.Series) -> pd.Series:
    raw = series.astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    lengths = raw.str.len()
    parsed = pd.Series(pd.NaT, index=raw.index, dtype="datetime64[ns]")

    mask_ym = lengths == 6
    if mask_ym.any():
        parsed.loc[mask_ym] = pd.to_datetime(raw.loc[mask_ym], format="%Y%m", errors="coerce")

    mask_ymd = lengths == 8
    if mask_ymd.any():
        parsed.loc[mask_ymd] = pd.to_datetime(raw.loc[mask_ymd], format="%Y%m%d", errors="coerce")

    fallback = parsed.isna()
    if fallback.any():
        parsed.loc[fallback] = pd.to_datetime(raw.loc[fallback], errors="coerce")

    return parsed


def prepare_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str | None]]:
    cols = resolve_columns(df)
    prepared = df.copy()

    count_col = cols["count"] or "CNT"
    if count_col not in prepared.columns:
        prepared[count_col] = 1
    prepared[count_col] = pd.to_numeric(prepared[count_col], errors="coerce").fillna(0)

    if cols["date"] is None:
        raise ValueError("말소 데이터에서 날짜 컬럼을 찾지 못했습니다.")

    prepared["DATE"] = parse_date_series(prepared[cols["date"]])
    prepared = prepared.dropna(subset=["DATE"]).copy()
    prepared["month"] = prepared["DATE"].dt.to_period("M").dt.to_timestamp()
    prepared["CNT"] = prepared[count_col]

    if cols["f_year"] is not None:
        prepared[cols["f_year"]] = pd.to_numeric(prepared[cols["f_year"]], errors="coerce")
        prepared["VEHICLE_AGE_YEARS"] = (prepared["DATE"].dt.year - prepared[cols["f_year"]]).clip(lower=0)
        prepared["VEHICLE_AGE_BAND"] = pd.cut(
            prepared["VEHICLE_AGE_YEARS"],
            bins=[-1, 2, 5, 9, 14, 100],
            labels=["0~2년", "3~5년", "6~9년", "10~14년", "15년+"],
        ).astype(str).replace("nan", "미상")

    for col in [cols["origin"], cols["brand"], cols["model"], cols["fuel"], cols["user_age"]]:
        if col and col in prepared.columns:
            prepared[col] = prepared[col].fillna("미상").astype(str)

    return prepared, cols


def summarize_monthly(df: pd.DataFrame) -> pd.DataFrame:
    monthly = df.groupby("month", as_index=False)["CNT"].sum().sort_values("month")
    monthly["mom_pct"] = monthly["CNT"].pct_change() * 100
    return monthly


def style_figure(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        height=height,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color=PALETTE["ink"]),
        margin=dict(l=20, r=20, t=72, b=28),
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


def build_donut(df: pd.DataFrame, label_col: str, title: str) -> go.Figure:
    fig = px.pie(
        df,
        values="CNT",
        names=label_col,
        hole=0.64,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        marker=dict(line=dict(color="#ffffff", width=3)),
        hovertemplate="%{label}<br>%{value:,.0f}대 (%{percent})<extra></extra>",
        pull=[0.01] * len(df),
    )
    fig.update_layout(title=title)
    return style_figure(fig, height=400)


def build_monthly_trend(monthly: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=monthly["month"],
            y=monthly["CNT"],
            mode="lines+markers",
            line=dict(color=PALETTE["blue"], width=3),
            marker=dict(size=7, color=PALETTE["blue"]),
            fill="tozeroy",
            fillcolor="rgba(37, 99, 235, 0.10)",
            hovertemplate="%{x|%Y-%m}<br>%{y:,.0f}대<extra></extra>",
            name="말소대수",
        )
    )
    fig.update_layout(title=title, hovermode="x unified", showlegend=False)
    fig.update_xaxes(title_text="월", tickformat="%Y-%m")
    fig.update_yaxes(title_text="말소대수")
    return style_figure(fig, height=420)


def build_growth_bar(monthly: pd.DataFrame, title: str) -> go.Figure:
    growth = monthly.dropna(subset=["mom_pct"]).copy()
    fig = go.Figure(
        go.Bar(
            x=growth["month"],
            y=growth["mom_pct"],
            marker=dict(color=[PALETTE["green"] if value >= 0 else PALETTE["red"] for value in growth["mom_pct"]]),
            text=growth["mom_pct"].round(1).astype(str) + "%",
            textposition="outside",
            hovertemplate="%{x|%Y-%m}<br>%{y:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(title=title, showlegend=False)
    fig.update_xaxes(title_text="월", tickformat="%Y-%m")
    fig.update_yaxes(title_text="전월 대비 증감률(%)")
    return style_figure(fig, height=420)


def build_bar(df: pd.DataFrame, x: str, y: str, title: str, orientation: str | None = None) -> go.Figure:
    fig = px.bar(
        df,
        x=x,
        y=y,
        color=y if orientation == "h" else x,
        orientation=orientation,
        text_auto=".2s",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_layout(title=title, showlegend=False)
    return style_figure(fig, height=420)


def build_stacked_monthly(df: pd.DataFrame, month_col: str, group_col: str, title: str) -> go.Figure:
    fig = px.area(
        df,
        x=month_col,
        y="CNT",
        color=group_col,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(title=title, hovermode="x unified")
    fig.update_xaxes(title_text="월", tickformat="%Y-%m")
    fig.update_yaxes(title_text="말소대수")
    return style_figure(fig, height=420)


def build_heatmap(df: pd.DataFrame, x_col: str, y_col: str, title: str) -> go.Figure:
    pivot = df.pivot_table(index=y_col, columns=x_col, values="CNT", aggfunc="sum", fill_value=0)
    fig = px.imshow(
        pivot,
        text_auto=True,
        aspect="auto",
        color_continuous_scale=["#e0f2fe", "#7dd3fc", "#2563eb"],
    )
    fig.update_layout(title=title, coloraxis_showscale=False)
    fig.update_xaxes(title_text=x_col)
    fig.update_yaxes(title_text=y_col)
    return style_figure(fig, height=430)


def top_share(df: pd.DataFrame, group_col: str) -> tuple[str, float]:
    grouped = df.groupby(group_col)["CNT"].sum().sort_values(ascending=False)
    if grouped.empty:
        return "-", 0.0
    return str(grouped.index[0]), safe_ratio(float(grouped.iloc[0]), float(grouped.sum())) * 100


def biggest_change(df: pd.DataFrame, group_col: str) -> tuple[str, float]:
    monthly_group = df.groupby(["month", group_col], as_index=False)["CNT"].sum().sort_values(["month", group_col])
    if monthly_group["month"].nunique() < 2:
        return "-", 0.0

    latest_month = monthly_group["month"].max()
    prev_month = sorted(monthly_group["month"].unique())[-2]
    latest_df = monthly_group[monthly_group["month"] == latest_month][[group_col, "CNT"]].rename(columns={"CNT": "latest_cnt"})
    prev_df = monthly_group[monthly_group["month"] == prev_month][[group_col, "CNT"]].rename(columns={"CNT": "prev_cnt"})
    merged = latest_df.merge(prev_df, on=group_col, how="outer").fillna(0)
    merged["delta"] = merged["latest_cnt"] - merged["prev_cnt"]
    row = merged.sort_values("delta", ascending=False).iloc[0]
    return str(row[group_col]), float(row["delta"])


def compute_period_comparison(base_df: pd.DataFrame, filtered_df: pd.DataFrame, months: int | None) -> tuple[float | None, str | None]:
    if months is None or filtered_df.empty:
        return None, None

    latest_month = filtered_df["month"].max()
    current_start = latest_month - pd.DateOffset(months=months - 1)
    previous_end = current_start - pd.DateOffset(months=1)
    previous_start = previous_end - pd.DateOffset(months=months - 1)

    current_total = float(filtered_df.loc[(filtered_df["month"] >= current_start) & (filtered_df["month"] <= latest_month), "CNT"].sum())
    previous_total = float(base_df.loc[(base_df["month"] >= previous_start) & (base_df["month"] <= previous_end), "CNT"].sum())

    if previous_total == 0 and current_total == 0:
        return None, f"직전 {months}개월 대비"

    return current_total - previous_total, f"직전 {months}개월 대비"


def build_summary_title(period_label: str, min_month: pd.Timestamp, max_month: pd.Timestamp) -> str:
    if period_label == "전체":
        return f"{min_month.year}년 {min_month.month}월 - {max_month.year}년 {max_month.month}월 한줄 요약"
    return f"{period_label} 한줄 요약"


inject_style()

raw = dl.get_ersr_data(base_dir="data")["monthly"].copy()
df, cols = prepare_frame(raw)

with st.sidebar:
    period_label = st.selectbox(
        "조회 기간",
        ["최근 3개월", "최근 6개월", "최근 12개월", "전체"],
        index=3,
    )
    period_map = {"최근 3개월": 3, "최근 6개월": 6, "최근 12개월": 12, "전체": None}

    selected_origin = []
    selected_brand = []
    selected_fuel = []
    selected_user_age = []

    if cols["origin"]:
        selected_origin = st.multiselect("국산/수입", sorted(df[cols["origin"]].dropna().astype(str).unique().tolist()))
    if cols["brand"]:
        selected_brand = st.multiselect("브랜드", sorted(df[cols["brand"]].dropna().astype(str).unique().tolist()))
    if cols["fuel"]:
        selected_fuel = st.multiselect("연료", sorted(df[cols["fuel"]].dropna().astype(str).unique().tolist()))
    if cols["user_age"]:
        selected_user_age = st.multiselect("사용자 연령대", sorted(df[cols["user_age"]].dropna().astype(str).unique().tolist()))
    ui.sidebar_links()

filtered_df = df.copy()
months = period_map[period_label]
if months is not None:
    latest_date = filtered_df["month"].max()
    start_date = latest_date - pd.DateOffset(months=months - 1)
    filtered_df = filtered_df[filtered_df["month"] >= start_date]

if selected_origin and cols["origin"]:
    filtered_df = filtered_df[filtered_df[cols["origin"]].astype(str).isin(selected_origin)]
if selected_brand and cols["brand"]:
    filtered_df = filtered_df[filtered_df[cols["brand"]].astype(str).isin(selected_brand)]
if selected_fuel and cols["fuel"]:
    filtered_df = filtered_df[filtered_df[cols["fuel"]].astype(str).isin(selected_fuel)]
if selected_user_age and cols["user_age"]:
    filtered_df = filtered_df[filtered_df[cols["user_age"]].astype(str).isin(selected_user_age)]

if filtered_df.empty:
    st.warning("선택한 조건에 해당하는 말소 데이터가 없습니다. 필터를 조정해 주세요.")
    st.stop()

monthly_summary = summarize_monthly(filtered_df)
latest_month = monthly_summary["month"].max()
latest_value = float(monthly_summary.loc[monthly_summary["month"] == latest_month, "CNT"].iloc[0])
previous_value = float(monthly_summary.iloc[-2]["CNT"]) if len(monthly_summary) > 1 else None
mom_value = pct_change(latest_value, previous_value)

total_cnt = float(filtered_df["CNT"].sum())
period_delta_value, period_delta_label = compute_period_comparison(df, filtered_df, months)
summary_title = build_summary_title(period_label, monthly_summary["month"].min(), latest_month)
top_brand_name, top_brand_share = top_share(filtered_df, cols["brand"]) if cols["brand"] else ("-", 0.0)
top_fuel_name, top_fuel_share = top_share(filtered_df, cols["fuel"]) if cols["fuel"] else ("-", 0.0)
top_user_age_name, top_user_age_share = top_share(filtered_df, cols["user_age"]) if cols["user_age"] else ("-", 0.0)

domestic_share = 0.0
if cols["origin"]:
    domestic_cnt = float(filtered_df.loc[filtered_df[cols["origin"]].astype(str).isin(DOMESTIC_LABELS), "CNT"].sum())
    domestic_share = safe_ratio(domestic_cnt, total_cnt) * 100

st.title(":material/delete_sweep: 말소등록 상세 분석")
st.markdown(
    f"데이터 기준 기간은 **{df['DATE'].min().strftime('%Y-%m')} ~ {df['DATE'].max().strftime('%Y-%m')}**이며, "
    "말소 규모와 최근 흐름, 연료·원산지·브랜드 구성, 사용자 연령대와 차량 사용연수를 한 화면에서 확인할 수 있도록 정리했습니다."
)

metric_cols = st.columns(4)
with metric_cols[0]:
    st.metric("선택 기간 총 말소", format_count(total_cnt), None if period_delta_value is None else format_signed_count(period_delta_value), border=True)
    if period_delta_label:
        st.caption(period_delta_label)
with metric_cols[1]:
    st.metric("최신월 말소", format_count(latest_value), None if mom_value is None else format_pct(mom_value), border=True)
with metric_cols[2]:
    label = "국산 비중" if cols["origin"] else "대표 연료 비중"
    value = format_pct(domestic_share) if cols["origin"] else format_pct(top_fuel_share)
    delta = f"수입 {format_pct(100 - domestic_share)}" if cols["origin"] else top_fuel_name
    st.metric(label, value, delta, border=True)
with metric_cols[3]:
    label = "대표 연령대" if cols["user_age"] else "1위 브랜드 점유율"
    value = format_pct(top_user_age_share) if cols["user_age"] else format_pct(top_brand_share)
    delta = top_user_age_name if cols["user_age"] else top_brand_name
    st.metric(label, value, delta, border=True)

st.markdown(
    f"""
    <div style="padding:16px 18px; border:1px solid #dbeafe; border-radius:18px; background:linear-gradient(180deg, #ffffff 0%, #f8fbff 100%); margin:10px 0 18px 0;">
      <div style="font-size:15px; color:#0f172a; font-weight:700; margin-bottom:6px;">{summary_title}</div>
      <div style="font-size:14px; color:#334155; line-height:1.6;">
        선택 기간 누적 말소는 <b>{format_count(total_cnt)}대</b>이며,
        대표 연료는 <b>{top_fuel_name}</b> ({format_pct(top_fuel_share)}),
        비중이 가장 높은 사용자 연령대는 <b>{top_user_age_name}</b> ({format_pct(top_user_age_share)})입니다.
        브랜드 기준으로는 <b>{top_brand_name}</b>가 가장 큰 비중을 차지합니다.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader(":material/trending_up: 월별 말소 추이")
trend_col, growth_col = st.columns(2, gap="large")
with trend_col:
    st.plotly_chart(build_monthly_trend(monthly_summary, "월별 말소대수 추이"), width="stretch")
with growth_col:
    if monthly_summary["mom_pct"].dropna().empty:
        st.info("증감률을 계산하려면 최소 2개월 이상의 데이터가 필요합니다.")
    else:
        st.plotly_chart(build_growth_bar(monthly_summary, "전월 대비 증감률"), width="stretch")

st.subheader(":material/widgets: 구조 분석")
row1_col1, row1_col2 = st.columns(2, gap="large")
with row1_col1:
    if cols["fuel"]:
        fuel_df = filtered_df.groupby(cols["fuel"], as_index=False)["CNT"].sum().sort_values("CNT", ascending=False)
        st.plotly_chart(build_donut(fuel_df, cols["fuel"], "연료별 말소 구성"), width="stretch")
    else:
        st.info("연료 컬럼이 없어 연료 분포를 표시할 수 없습니다.")
with row1_col2:
    if cols["user_age"]:
        user_age_df = filtered_df.groupby(cols["user_age"], as_index=False)["CNT"].sum().sort_values("CNT", ascending=True)
        st.plotly_chart(build_bar(user_age_df, "CNT", cols["user_age"], "연령대별 말소대수", orientation="h"), width="stretch")
    else:
        st.info("연령대 컬럼이 없어 연령대 분포를 표시할 수 없습니다.")

if cols["origin"]:
    origin_monthly = filtered_df.groupby(["month", cols["origin"]], as_index=False)["CNT"].sum().sort_values("month")
    st.plotly_chart(build_stacked_monthly(origin_monthly, "month", cols["origin"], "국산/수입 월별 구조"), width="stretch")
else:
    st.info("국산/수입 컬럼이 없어 원산지 구조를 표시할 수 없습니다.")

row3_col1, row3_col2 = st.columns(2, gap="large")
with row3_col1:
    if "VEHICLE_AGE_BAND" in filtered_df.columns and cols["fuel"]:
        heat_df = filtered_df.groupby(["VEHICLE_AGE_BAND", cols["fuel"]], as_index=False)["CNT"].sum()
        st.plotly_chart(build_heatmap(heat_df, cols["fuel"], "VEHICLE_AGE_BAND", "사용연수 구간 x 연료 Heatmap"), width="stretch")
    else:
        st.info("F_YEAR와 연료 컬럼이 모두 있을 때 사용연수 x 연료 구성을 볼 수 있습니다.")
with row3_col2:
    if "VEHICLE_AGE_BAND" in filtered_df.columns:
        age_band_df = filtered_df.groupby("VEHICLE_AGE_BAND", as_index=False)["CNT"].sum().sort_values("CNT", ascending=True)
        st.plotly_chart(build_bar(age_band_df, "CNT", "VEHICLE_AGE_BAND", "사용연수 구간별 말소대수", orientation="h"), width="stretch")
    else:
        st.info("F_YEAR가 있어야 사용연수 구간별 말소대수를 계산할 수 있습니다.")

st.subheader(":material/account_tree: 브랜드 및 모델")
detail_col1, detail_col2 = st.columns(2, gap="large")
with detail_col1:
    if cols["brand"]:
        brand_df = filtered_df.groupby(cols["brand"], as_index=False)["CNT"].sum().sort_values("CNT", ascending=True).tail(15)
        st.plotly_chart(build_bar(brand_df, "CNT", cols["brand"], "브랜드별 말소대수 Top 15", orientation="h"), width="stretch")
    else:
        st.info("브랜드 컬럼이 없어 브랜드별 현황을 표시할 수 없습니다.")
with detail_col2:
    if cols["brand"] and cols["model"]:
        brand_options = filtered_df.groupby(cols["brand"])["CNT"].sum().sort_values(ascending=False).index.astype(str).tolist()
        selected_brand = st.selectbox("브랜드 선택", brand_options)
        model_df = (
            filtered_df[filtered_df[cols["brand"]].astype(str) == selected_brand]
            .groupby(cols["model"], as_index=False)["CNT"]
            .sum()
            .sort_values("CNT", ascending=False)
            .head(15)
        )
        st.plotly_chart(build_bar(model_df, cols["model"], "CNT", f"{selected_brand} 모델별 말소대수 Top 15"), width="stretch")
    else:
        st.info("브랜드와 모델 컬럼이 모두 있어야 모델별 현황을 표시할 수 있습니다.")

