import warnings

import pandas as pd
import streamlit as st
from streamlit_echarts import JsCode, st_echarts

from app_core import charts as ch
from app_core import footer
from app_core import ui
from app_core.data_loader import get_newreg_data
from app_core.nav import render_sidebar_nav

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="신규등록 상세 분석",
    layout="wide",
    initial_sidebar_state="auto",
)
render_sidebar_nav()


DOMESTIC_LABELS = {"국산", "국내", "국산차"}
ECO_FUELS = {"전기", "하이브리드", "수소"}


def format_count(value: float) -> str:
    return f"{int(round(value)):,}"


def format_pct(value: float) -> str:
    return f"{value:.1f}%"


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def pct_change(current: float, previous: float | None) -> float | None:
    if previous in (None, 0) or pd.isna(previous):
        return None
    return (current - previous) / previous * 100


def build_period_mask(series: pd.Series, months: int | None) -> pd.Series:
    if months is None:
        return pd.Series(True, index=series.index)
    latest = series.max()
    start = latest - pd.DateOffset(months=months - 1)
    return series >= start


def build_summary_title(period_label: str, min_month: pd.Timestamp, max_month: pd.Timestamp) -> str:
    if period_label == "전체":
        return f"{min_month.year}년 {min_month.month}월 - {max_month.year}년 {max_month.month}월 한줄 요약"
    return f"{period_label} 한줄 요약"


def summarize_monthly(df: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        df.assign(month=df["EXTRACT_DE"].dt.to_period("M").dt.to_timestamp())
        .groupby("month", as_index=False)["CNT"]
        .sum()
        .sort_values("month")
    )
    monthly["mom_pct"] = monthly["CNT"].pct_change() * 100
    return monthly


def compute_period_comparison(
    base_df: pd.DataFrame,
    selected_df: pd.DataFrame,
    months: int | None,
) -> tuple[float | None, str | None]:
    if months is None:
        return None, None

    selected_monthly = summarize_monthly(selected_df)
    if selected_monthly.empty:
        return None, None

    latest_month = selected_monthly["month"].max()
    current_start = latest_month - pd.DateOffset(months=months - 1)
    previous_end = current_start - pd.DateOffset(months=1)
    previous_start = previous_end - pd.DateOffset(months=months - 1)

    previous_mask = (base_df["month"] >= previous_start) & (base_df["month"] <= previous_end)
    previous_total = float(base_df.loc[previous_mask, "CNT"].sum())
    current_total = float(selected_df["CNT"].sum())
    delta_pct = pct_change(current_total, previous_total)

    label = f"직전 {months}개월 대비"
    return delta_pct, label


def top_share(df: pd.DataFrame, group_col: str) -> tuple[str, float]:
    grouped = df.groupby(group_col, dropna=False)["CNT"].sum().sort_values(ascending=False)
    if grouped.empty:
        return "-", 0.0
    return str(grouped.index[0]), safe_ratio(float(grouped.iloc[0]), float(grouped.sum())) * 100


def top_change_summary(df: pd.DataFrame, group_col: str) -> tuple[str, float, str, float]:
    monthly_group = (
        df.groupby(["month", group_col], as_index=False)["CNT"]
        .sum()
        .sort_values(["month", group_col])
    )
    if monthly_group.empty:
        return "-", 0.0, "-", 0.0

    months = monthly_group["month"].drop_duplicates().sort_values().tolist()
    if len(months) < 2:
        return "-", 0.0, "-", 0.0

    latest = months[-1]
    prev = months[-2]
    latest_df = monthly_group[monthly_group["month"] == latest][[group_col, "CNT"]].rename(
        columns={"CNT": "latest_cnt"}
    )
    prev_df = monthly_group[monthly_group["month"] == prev][[group_col, "CNT"]].rename(
        columns={"CNT": "prev_cnt"}
    )
    change_df = latest_df.merge(prev_df, on=group_col, how="outer").fillna(0)
    change_df["delta"] = change_df["latest_cnt"] - change_df["prev_cnt"]
    inc_row = change_df.sort_values("delta", ascending=False).iloc[0]
    dec_row = change_df.sort_values("delta", ascending=True).iloc[0]
    return str(inc_row[group_col]), float(inc_row["delta"]), str(dec_row[group_col]), float(dec_row["delta"])


def normalize_frame(frame: pd.DataFrame, metric_cols: list[str]) -> pd.DataFrame:
    normalized = frame.copy()
    for col in metric_cols:
        max_value = normalized[col].max()
        normalized[col] = 0 if max_value == 0 else normalized[col] / max_value * 100
    return normalized


def detect_region_column(df: pd.DataFrame) -> str | None:
    for candidate in ["JUSO_SIDO", "REGION", "AREA"]:
        if candidate in df.columns:
            return candidate
    return None


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


inject_style()

data = get_newreg_data(base_dir="data/")
df = data["dim"].copy()
df_use = data["cum"].copy()

df["EXTRACT_DE"] = pd.to_datetime(df["EXTRACT_DE"].astype(str), format="%Y%m", errors="coerce")
df = df.dropna(subset=["EXTRACT_DE"]).copy()
df["month"] = df["EXTRACT_DE"].dt.to_period("M").dt.to_timestamp()
df["CNT"] = pd.to_numeric(df["CNT"], errors="coerce").fillna(0)

for col in [
    "CL_HMMD_IMP_SE_NM",
    "ORG_CAR_MAKER_KOR",
    "CAR_MOEL_DT",
    "CAR_BT",
    "FUEL",
    "OWNER_GB",
    "AGE",
    "JUSO_SIDO",
    "CAR_USE",
    "CAR_USE_DETAL",
]:
    if col in df.columns:
        df[col] = df[col].fillna("미상").astype(str)

analysis_year = int(df["EXTRACT_DE"].dt.year.max())

st.title(":material/dashboard: 신규등록 상세 분석")
st.markdown(
    f"데이터 기간: **{df['EXTRACT_DE'].min().strftime('%Y-%m')} ~ {df['EXTRACT_DE'].max().strftime('%Y-%m')}**"
)

with st.sidebar:
    st.title(":material/filter_alt: 필터")
    period_label = st.selectbox(
        "조회 기간",
        ["최근 3개월", "최근 6개월", "최근 12개월", "전체"],
        index=1,
    )
    period_map = {"최근 3개월": 3, "최근 6개월": 6, "최근 12개월": 12, "전체": None}

    selected_origin = st.multiselect(
        "국산/수입",
        sorted(df["CL_HMMD_IMP_SE_NM"].dropna().astype(str).unique().tolist()),
    )
    selected_brand_filter = st.multiselect(
        "브랜드",
        sorted(df["ORG_CAR_MAKER_KOR"].dropna().astype(str).unique().tolist()),
    )
    selected_body = st.multiselect(
        "차형",
        sorted(df["CAR_BT"].dropna().astype(str).unique().tolist()),
    )
    selected_fuel = st.multiselect(
        "연료",
        sorted(df["FUEL"].dropna().astype(str).unique().tolist()),
    )
    selected_owner = st.multiselect(
        "소유구분",
        sorted(df["OWNER_GB"].dropna().astype(str).unique().tolist()),
    )
    selected_age = st.multiselect(
        "연령대",
        sorted(df["AGE"].dropna().astype(str).unique().tolist()),
    )
    ui.sidebar_links()

base_filtered_df = df.copy()

if selected_origin:
    base_filtered_df = base_filtered_df[base_filtered_df["CL_HMMD_IMP_SE_NM"].isin(selected_origin)]
if selected_brand_filter:
    base_filtered_df = base_filtered_df[base_filtered_df["ORG_CAR_MAKER_KOR"].isin(selected_brand_filter)]
if selected_body:
    base_filtered_df = base_filtered_df[base_filtered_df["CAR_BT"].isin(selected_body)]
if selected_fuel:
    base_filtered_df = base_filtered_df[base_filtered_df["FUEL"].isin(selected_fuel)]
if selected_owner:
    base_filtered_df = base_filtered_df[base_filtered_df["OWNER_GB"].isin(selected_owner)]
if selected_age:
    base_filtered_df = base_filtered_df[base_filtered_df["AGE"].isin(selected_age)]

mask = build_period_mask(base_filtered_df["month"], period_map[period_label])
filtered_df = base_filtered_df.loc[mask].copy()

if filtered_df.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다. 필터를 조정해 주세요.")
    footer.render()
    st.stop()

monthly_summary = summarize_monthly(filtered_df)
latest_month = monthly_summary["month"].max()
latest_month_value = float(monthly_summary.loc[monthly_summary["month"] == latest_month, "CNT"].iloc[0])
previous_month_value = float(monthly_summary.iloc[-2]["CNT"]) if len(monthly_summary) > 1 else None
latest_delta = pct_change(latest_month_value, previous_month_value)

total_cnt = float(filtered_df["CNT"].sum())
period_delta, period_delta_label = compute_period_comparison(
    base_filtered_df,
    filtered_df,
    period_map[period_label],
)
domestic_cnt = float(
    filtered_df.loc[filtered_df["CL_HMMD_IMP_SE_NM"].astype(str).isin(DOMESTIC_LABELS), "CNT"].sum()
)
domestic_share = safe_ratio(domestic_cnt, total_cnt) * 100

top_brand_name, top_brand_share = top_share(filtered_df, "ORG_CAR_MAKER_KOR")
top_body_name, top_body_share = top_share(filtered_df, "CAR_BT")
top_fuel_name, top_fuel_share = top_share(filtered_df, "FUEL")
inc_fuel_name, inc_fuel_delta, _, _ = top_change_summary(filtered_df, "FUEL")
_, _, dec_body_name, dec_body_delta = top_change_summary(filtered_df, "CAR_BT")

brand_share_df = (
    filtered_df.groupby("ORG_CAR_MAKER_KOR", as_index=False)["CNT"]
    .sum()
    .sort_values("CNT", ascending=False)
)
top3_brand_share = safe_ratio(brand_share_df.head(3)["CNT"].sum(), brand_share_df["CNT"].sum()) * 100
summary_title = build_summary_title(period_label, monthly_summary["month"].min(), latest_month)
sparkline = monthly_summary["CNT"].round(0).astype(int).tolist()

metric_cols = st.columns(4)
with metric_cols[0]:
    total_delta_text = None if period_delta is None else format_pct(period_delta)
    st.metric(
        "선택 기간 총 등록",
        format_count(total_cnt),
        total_delta_text,
        border=True,
        chart_data=sparkline,
        chart_type="area",
    )
    if period_delta_label is not None:
        st.caption(period_delta_label)
with metric_cols[1]:
    st.metric(
        "최신월 등록",
        format_count(latest_month_value),
        None if latest_delta is None else format_pct(latest_delta),
        border=True,
        chart_data=sparkline,
        chart_type="bar",
    )
with metric_cols[2]:
    st.metric(
        "국산 비중",
        format_pct(domestic_share),
        f"수입 {format_pct(100 - domestic_share)}",
        border=True,
        chart_data=sparkline,
        chart_type="line",
    )
with metric_cols[3]:
    st.metric(
        "1위 브랜드 점유율",
        format_pct(top_brand_share),
        top_brand_name,
        border=True,
        chart_data=sparkline,
        chart_type="area",
    )

st.markdown(
    f"""
    <div style="padding:16px 18px; border:1px solid #dbeafe; border-radius:18px; background:linear-gradient(180deg, #ffffff 0%, #f8fbff 100%); margin:10px 0 18px 0;">
      <div style="font-size:15px; color:#0f172a; font-weight:700; margin-bottom:6px;">{summary_title}</div>
      <div style="font-size:14px; color:#334155; line-height:1.7;">
        선택 기간 누적 등록은 <b>{format_count(total_cnt)}대</b>이며,
        1위 브랜드는 <b>{top_brand_name}</b> ({format_pct(top_brand_share)}),
        대표 차형은 <b>{top_body_name}</b> ({format_pct(top_body_share)}),
        대표 연료는 <b>{top_fuel_name}</b> ({format_pct(top_fuel_share)})입니다.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

insight_cols = st.columns(2)
with insight_cols[0]:
    st.info(f"상위 3개 브랜드가 전체 등록의 **{format_pct(top3_brand_share)}** 를 차지해 브랜드 집중도가 비교적 높게 나타납니다.")
with insight_cols[1]:
    st.info(
        f"최신월 기준 가장 늘어난 연료는 **{inc_fuel_name}** ({format_count(inc_fuel_delta)}대), "
        f"가장 줄어든 차형은 **{dec_body_name}** ({format_count(abs(dec_body_delta))}대)입니다."
    )

st.subheader(":material/trending_up: 등록 추이")
trend_col, growth_col = st.columns([3, 2], gap="small")

with trend_col:
    trend_options = {
        "title": {"text": "월별 신규등록 추이", "left": "center", "top": 5},
        "tooltip": {
            "trigger": "axis",
            "valueFormatter": JsCode("function(v){return Math.round(v).toLocaleString()+'대'}"),
        },
        "legend": {"bottom": "0"},
        "xAxis": {"type": "category", "data": monthly_summary["month"].dt.strftime("%Y-%m").tolist()},
        "yAxis": {"type": "value", "name": "등록대수"},
        "grid": {"bottom": "18%"},
        "dataZoom": [
            {"type": "inside", "start": 0, "end": 100},
            {"type": "slider", "start": 0, "end": 100, "height": 18, "bottom": 28},
        ],
        "series": [
            {
                "name": "등록대수",
                "type": "line",
                "smooth": True,
                "areaStyle": {"opacity": 0.12},
                "lineStyle": {"width": 3, "color": "#1d4ed8"},
                "itemStyle": {"color": "#1d4ed8"},
                "data": monthly_summary["CNT"].round(0).astype(int).tolist(),
            }
        ],
    }
    st_echarts(options=trend_options, height="400px", key="newreg_trend")

with growth_col:
    growth_df = monthly_summary.dropna(subset=["mom_pct"]).copy()
    if growth_df.empty:
        st.info("증감률을 보려면 2개월 이상의 데이터가 필요합니다.")
    else:
        growth_options = {
            "title": {"text": "전월 대비 증감률", "left": "center", "top": 5},
            "tooltip": {"trigger": "axis", "formatter": "{b}<br/>{c}%"},
            "xAxis": {
                "type": "category",
                "data": growth_df["month"].dt.strftime("%Y-%m").tolist(),
                "axisLabel": {"rotate": 35},
            },
            "yAxis": {"type": "value", "axisLabel": {"formatter": "{value}%"}},
            "grid": {"bottom": "18%", "containLabel": True},
            "series": [
                {
                    "type": "bar",
                    "data": [
                        {
                            "value": round(value, 1),
                            "itemStyle": {"color": "#16a34a" if value >= 0 else "#dc2626"},
                        }
                        for value in growth_df["mom_pct"].tolist()
                    ],
                }
            ],
        }
        st_echarts(options=growth_options, height="400px", key="newreg_growth")

st.subheader(":material/insights: 시장 구성")
mix_col1, mix_col2 = st.columns(2)

with mix_col1:
    top_brand_chart = brand_share_df.head(5).sort_values("CNT", ascending=True)
    top_brand_options = {
        "title": {"text": "상위 브랜드 집중도", "left": "center"},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "grid": {"left": "4%", "right": "4%", "bottom": "8%", "containLabel": True},
        "xAxis": {"type": "value"},
        "yAxis": {"type": "category", "data": top_brand_chart["ORG_CAR_MAKER_KOR"].astype(str).tolist()},
        "series": [
            {
                "type": "bar",
                "data": top_brand_chart["CNT"].round(0).astype(int).tolist(),
                "itemStyle": {"color": "#3b82f6", "borderRadius": [0, 12, 12, 0]},
                "label": {"show": True, "position": "right"},
            }
        ],
    }
    st_echarts(options=top_brand_options, height="340px", key="newreg_brand_focus")

with mix_col2:
    origin_fuel_mix = filtered_df.groupby(["CL_HMMD_IMP_SE_NM", "FUEL"], as_index=False)["CNT"].sum()
    origin_order = (
        origin_fuel_mix.groupby("CL_HMMD_IMP_SE_NM")["CNT"].sum().sort_values(ascending=False).index.tolist()
    )
    fuel_order = origin_fuel_mix.groupby("FUEL")["CNT"].sum().sort_values(ascending=False).index.tolist()
    origin_fuel_series = []
    for fuel in fuel_order:
        values = []
        for origin in origin_order[::-1]:
            subset = origin_fuel_mix[
                (origin_fuel_mix["CL_HMMD_IMP_SE_NM"] == origin) & (origin_fuel_mix["FUEL"] == fuel)
            ]["CNT"]
            values.append(int(subset.iloc[0]) if not subset.empty else 0)
        origin_fuel_series.append(
            {"name": str(fuel), "type": "bar", "stack": "total", "emphasis": {"focus": "series"}, "data": values}
        )

    origin_fuel_options = {
        "title": {"text": "국산/수입 x 연료 구성", "left": "center"},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {"bottom": "0", "type": "scroll"},
        "grid": {"left": "4%", "right": "4%", "bottom": "14%", "containLabel": True},
        "xAxis": {"type": "value"},
        "yAxis": {"type": "category", "data": origin_order[::-1]},
        "series": origin_fuel_series,
    }
    st_echarts(options=origin_fuel_options, height="340px", key="newreg_origin_fuel")

st.subheader(":material/explore: 구조 분석")
row3_1, row3_2, row3_3 = st.columns(3)

with row3_1:
    brand_model = (
        filtered_df.groupby(["ORG_CAR_MAKER_KOR", "CAR_MOEL_DT"], as_index=False)["CNT"]
        .sum()
        .sort_values("CNT", ascending=False)
    )
    tree_data = []
    for brand, group in brand_model.groupby("ORG_CAR_MAKER_KOR"):
        children = [{"name": str(row["CAR_MOEL_DT"]), "value": int(row["CNT"])} for _, row in group.head(12).iterrows()]
        tree_data.append({"name": str(brand), "children": children})

    treemap_options = {
        "title": {"text": "브랜드-모델 Treemap", "left": "center"},
        "tooltip": {
            "formatter": JsCode(
                "function(p){return p.name + '<br/>등록대수 ' + Math.round(p.value || 0).toLocaleString() + '대';}"
            )
        },
        "series": [
            {
                "type": "treemap",
                "data": tree_data,
                "visibleMin": 50,
                "roam": False,
                "label": {"show": True, "formatter": "{b}"},
                "upperLabel": {"show": True},
                "breadcrumb": {"show": False},
                "levels": [
                    {"itemStyle": {"borderColor": "#ffffff", "borderWidth": 3, "gapWidth": 3}},
                    {"itemStyle": {"borderColor": "#f3f4f6", "borderWidth": 1, "gapWidth": 1}},
                ],
            }
        ],
    }
    st_echarts(options=treemap_options, height="450px", key="newreg_treemap")

with row3_2:
    body_profile = (
        filtered_df.groupby("CAR_BT")
        .apply(
            lambda g: pd.Series(
                {
                    "total_cnt": g["CNT"].sum(),
                    "brand_diversity": g["ORG_CAR_MAKER_KOR"].nunique(),
                    "model_diversity": g["CAR_MOEL_DT"].nunique(),
                    "import_share": safe_ratio(
                        g.loc[~g["CL_HMMD_IMP_SE_NM"].astype(str).isin(DOMESTIC_LABELS), "CNT"].sum(),
                        g["CNT"].sum(),
                    )
                    * 100,
                    "private_share": safe_ratio(
                        g.loc[g["OWNER_GB"].astype(str) == "개인", "CNT"].sum(),
                        g["CNT"].sum(),
                    )
                    * 100,
                }
            )
        )
        .reset_index()
        .sort_values("total_cnt", ascending=False)
        .head(5)
    )

    radar_metrics = ["total_cnt", "brand_diversity", "model_diversity", "import_share", "private_share"]
    radar_labels = ["등록규모", "브랜드수", "모델수", "수입비중", "개인비중"]
    radar_norm = normalize_frame(body_profile, radar_metrics)
    radar_series = [
        {"name": str(row["CAR_BT"]), "value": [round(float(row[col]), 1) for col in radar_metrics]}
        for _, row in radar_norm.iterrows()
    ]

    radar_options = {
        "title": {"text": "상위 차형 프로파일", "left": "center"},
        "tooltip": {"trigger": "item"},
        "legend": {"bottom": "0", "type": "scroll"},
        "radar": {
            "indicator": [{"name": label, "max": 100} for label in radar_labels],
            "center": ["50%", "50%"],
            "radius": "60%",
        },
        "series": [{"type": "radar", "data": radar_series, "areaStyle": {"opacity": 0.08}}],
    }
    st_echarts(options=radar_options, height="450px", key="newreg_radar")

with row3_3:
    top_brands = (
        filtered_df.groupby("ORG_CAR_MAKER_KOR", as_index=False)["CNT"]
        .sum()
        .sort_values("CNT", ascending=False)
        .head(5)["ORG_CAR_MAKER_KOR"]
        .tolist()
    )
    fuel_mix = (
        filtered_df[filtered_df["ORG_CAR_MAKER_KOR"].isin(top_brands)]
        .groupby(["ORG_CAR_MAKER_KOR", "FUEL"], as_index=False)["CNT"]
        .sum()
    )
    fuel_order = fuel_mix.groupby("FUEL")["CNT"].sum().sort_values(ascending=False).index.tolist()
    stacked_series = []
    for fuel in fuel_order:
        values = []
        for brand in top_brands[::-1]:
            subset = fuel_mix[(fuel_mix["ORG_CAR_MAKER_KOR"] == brand) & (fuel_mix["FUEL"] == fuel)]["CNT"]
            values.append(int(subset.iloc[0]) if not subset.empty else 0)
        stacked_series.append(
            {"name": str(fuel), "type": "bar", "stack": "total", "emphasis": {"focus": "series"}, "data": values}
        )

    top5_options = {
        "title": {"text": "Top 5 브랜드 연료 구성", "left": "center"},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {"bottom": "0", "type": "scroll"},
        "grid": {"left": "3%", "right": "4%", "bottom": "14%", "containLabel": True},
        "xAxis": {"type": "value"},
        "yAxis": {"type": "category", "data": top_brands[::-1]},
        "series": stacked_series,
    }
    st_echarts(options=top5_options, height="450px", key="newreg_top5")

st.subheader(":material/touch_app: 브랜드 드릴다운")
left, right = st.columns(2)

brand_scatter = (
    filtered_df.groupby("ORG_CAR_MAKER_KOR")
    .apply(
        lambda g: pd.Series(
            {
                "total_cnt": g["CNT"].sum(),
                "model_count": g["CAR_MOEL_DT"].nunique(),
                "latest_cnt": g.loc[g["month"] == latest_month, "CNT"].sum(),
            }
        )
    )
    .reset_index()
    .sort_values("total_cnt", ascending=False)
)

scatter_data = [
    [int(row["model_count"]), int(row["total_cnt"]), int(max(row["latest_cnt"], 1)), str(row["ORG_CAR_MAKER_KOR"])]
    for _, row in brand_scatter.iterrows()
]

with left:
    scatter_options = {
        "animation": False,
        "title": {"text": "브랜드 포트폴리오", "left": "center"},
        "tooltip": {
            "trigger": "item",
            "formatter": JsCode(
                "function(p){var v=p.value; return v[3] + '<br/>모델 수 ' + v[0] + '<br/>누적 등록 ' + Math.round(v[1]).toLocaleString() + '대<br/>최신월 ' + Math.round(v[2]).toLocaleString() + '대';}"
            ),
        },
        "xAxis": {"name": "모델 수", "type": "value"},
        "yAxis": {"name": "누적 등록대수", "type": "value"},
        "visualMap": {
            "show": False,
            "dimension": 2,
            "min": 1,
            "max": max(item[2] for item in scatter_data) if scatter_data else 1,
            "inRange": {"symbolSize": [12, 48]},
        },
        "series": [{"type": "scatter", "data": scatter_data, "itemStyle": {"opacity": 0.78, "color": "#2563eb"}}],
    }
    st_echarts(options=scatter_options, height="450px", key="newreg_scatter")

with right:
    selected_brand_name = st.selectbox(
        "브랜드 선택",
        brand_scatter["ORG_CAR_MAKER_KOR"].astype(str).tolist(),
        index=0,
    )
    brand_df = filtered_df[filtered_df["ORG_CAR_MAKER_KOR"] == selected_brand_name].copy()
    brand_monthly = summarize_monthly(brand_df)
    top_models = (
        brand_df.groupby("CAR_MOEL_DT", as_index=False)["CNT"]
        .sum()
        .sort_values("CNT", ascending=False)
        .head(5)
    )
    detail_options = {
        "title": {"text": f"{selected_brand_name} 월별 추이", "left": "center"},
        "tooltip": {
            "trigger": "axis",
            "valueFormatter": JsCode("function(v){return Math.round(v).toLocaleString()+'대'}"),
        },
        "legend": {"bottom": "0"},
        "grid": {"bottom": "16%"},
        "xAxis": {"type": "category", "data": brand_monthly["month"].dt.strftime("%Y-%m").tolist()},
        "yAxis": [{"type": "value", "name": "등록대수"}, {"type": "value", "name": "증감률"}],
        "series": [
            {
                "name": "등록대수",
                "type": "bar",
                "data": brand_monthly["CNT"].round(0).astype(int).tolist(),
                "itemStyle": {"color": "#60a5fa"},
            },
            {
                "name": "전월 대비",
                "type": "line",
                "yAxisIndex": 1,
                "smooth": True,
                "data": brand_monthly["mom_pct"].round(1).fillna(0).tolist(),
                "itemStyle": {"color": "#f97316"},
                "lineStyle": {"width": 3},
            },
        ],
    }
    st_echarts(options=detail_options, height="300px", key="newreg_brand_detail")
    st.dataframe(
        top_models.rename(columns={"CAR_MOEL_DT": "모델", "CNT": "등록대수"}).reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )

st.subheader(":material/settings: 상세 분포")
row5_1, row5_2, row5_3, row5_4 = st.columns(4)

with row5_1:
    age_body = filtered_df.groupby(["AGE", "CAR_BT"], as_index=False)["CNT"].sum().sort_values("CNT", ascending=False)
    age_order = age_body.groupby("AGE")["CNT"].sum().sort_values(ascending=False).index.tolist()
    body_order = age_body.groupby("CAR_BT")["CNT"].sum().sort_values(ascending=False).head(6).index.tolist()
    heatmap_data = []
    for _, row in age_body.iterrows():
        if row["CAR_BT"] in body_order:
            heatmap_data.append([body_order.index(row["CAR_BT"]), age_order.index(row["AGE"]), int(row["CNT"])])

    heatmap_options = {
        "title": {"text": "연령대-차형 Heatmap", "left": "center"},
        "tooltip": {"position": "top"},
        "grid": {"height": "55%", "top": "14%", "bottom": "24%"},
        "xAxis": {"type": "category", "data": body_order, "axisLabel": {"rotate": 35}},
        "yAxis": {"type": "category", "data": age_order},
        "visualMap": {
            "min": 0,
            "max": max((item[2] for item in heatmap_data), default=0),
            "calculable": True,
            "orient": "horizontal",
            "left": "center",
            "bottom": "0%",
            "inRange": {"color": ["#dbeafe", "#60a5fa", "#1d4ed8"]},
        },
        "series": [{"type": "heatmap", "data": heatmap_data, "label": {"show": True}}],
    }
    st_echarts(options=heatmap_options, height="450px", key="newreg_heatmap")

with row5_2:
    owner_profile = (
        filtered_df.groupby("OWNER_GB")
        .apply(
            lambda g: pd.Series(
                {
                    "total_cnt": g["CNT"].sum(),
                    "avg_per_model": safe_ratio(g["CNT"].sum(), g["CAR_MOEL_DT"].nunique()),
                }
            )
        )
        .reset_index()
        .sort_values("total_cnt", ascending=True)
    )
    owner_options = {
        "title": {"text": "소유구분 규모", "left": "center"},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {"bottom": "0"},
        "grid": {"left": "4%", "right": "4%", "bottom": "14%", "containLabel": True},
        "yAxis": {"type": "category", "data": owner_profile["OWNER_GB"].astype(str).tolist()},
        "xAxis": {"type": "value"},
        "series": [
            {
                "name": "총 등록대수",
                "type": "bar",
                "data": owner_profile["total_cnt"].round(0).astype(int).tolist(),
                "itemStyle": {"color": "#2563eb"},
            },
            {
                "name": "모델당 평균 등록",
                "type": "bar",
                "data": owner_profile["avg_per_model"].round(1).tolist(),
                "itemStyle": {"color": "#93c5fd"},
            },
        ],
    }
    st_echarts(options=owner_options, height="450px", key="newreg_owner_bar")

with row5_3:
    monthly_origin = filtered_df.groupby(["month", "CL_HMMD_IMP_SE_NM"], as_index=False)["CNT"].sum().sort_values("month")
    origin_labels = monthly_origin.groupby("CL_HMMD_IMP_SE_NM")["CNT"].sum().sort_values(ascending=False).index.tolist()
    month_labels = sorted(monthly_origin["month"].dt.strftime("%Y-%m").unique().tolist())
    monthly_series = []
    for label in origin_labels:
        values = []
        for month_label in month_labels:
            subset = monthly_origin[
                (monthly_origin["CL_HMMD_IMP_SE_NM"] == label)
                & (monthly_origin["month"].dt.strftime("%Y-%m") == month_label)
            ]["CNT"]
            values.append(int(subset.iloc[0]) if not subset.empty else 0)
        monthly_series.append({"name": str(label), "type": "bar", "stack": "total", "data": values})

    monthly_mix_options = {
        "title": {"text": "월별 국산/수입 구성", "left": "center"},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {"bottom": "0"},
        "xAxis": {"type": "category", "data": month_labels, "axisLabel": {"rotate": 35}},
        "yAxis": {"type": "value"},
        "grid": {"bottom": "16%", "containLabel": True},
        "series": monthly_series,
    }
    st_echarts(options=monthly_mix_options, height="450px", key="newreg_origin_mix")

with row5_4:
    fuel_dist = filtered_df.groupby("FUEL", as_index=False)["CNT"].sum().sort_values("CNT", ascending=False)
    fuel_options = {
        "title": {"text": "연료 비중", "left": "center"},
        "tooltip": {"trigger": "item", "formatter": "{b}: {c}대 ({d}%)"},
        "series": [
            {
                "type": "pie",
                "radius": ["42%", "72%"],
                "avoidLabelOverlap": True,
                "itemStyle": {"borderRadius": 14, "borderColor": "#ffffff", "borderWidth": 3},
                "label": {"show": True, "formatter": "{b}\n{d}%"},
                "data": [{"name": str(row["FUEL"]), "value": int(row["CNT"])} for _, row in fuel_dist.iterrows()],
            }
        ],
    }
    st_echarts(options=fuel_options, height="450px", key="newreg_fuel_donut")

region_col = detect_region_column(filtered_df)
if region_col:
    st.subheader(":material/speed: 지역별 친환경 전환률")
    st.caption(f"`{period_label}` 기준으로 지역별 친환경차(전기·하이브리드·수소) 등록 비중을 게이지와 순위로 확인합니다.")

    region_summary = (
        filtered_df.groupby(region_col, as_index=False)
        .agg(total_cnt=("CNT", "sum"))
        .sort_values("total_cnt", ascending=False)
    )
    eco_summary = (
        filtered_df[filtered_df["FUEL"].astype(str).isin(ECO_FUELS)]
        .groupby(region_col, as_index=False)["CNT"]
        .sum()
        .rename(columns={"CNT": "eco_cnt"})
    )
    region_summary = region_summary.merge(eco_summary, on=region_col, how="left").fillna({"eco_cnt": 0})
    region_summary["eco_rate"] = (region_summary["eco_cnt"] / region_summary["total_cnt"] * 100).fillna(0)
    region_summary = region_summary.sort_values("eco_rate", ascending=False)

    national_total = float(region_summary["total_cnt"].sum())
    national_eco = float(region_summary["eco_cnt"].sum())
    national_rate = safe_ratio(national_eco, national_total) * 100

    gauge_col, rank_col = st.columns([1.6, 1], gap="large")
    with gauge_col:
        region_options = ["전체"] + region_summary[region_col].astype(str).tolist()
        selected_region = st.selectbox("지역 선택", region_options, key="newreg_region")
        if selected_region == "전체":
            region_name = "전국"
            total_value = national_total
            eco_value = national_eco
            eco_rate = national_rate
        else:
            selected_row = region_summary[region_summary[region_col].astype(str) == selected_region].iloc[0]
            region_name = selected_region
            total_value = float(selected_row["total_cnt"])
            eco_value = float(selected_row["eco_cnt"])
            eco_rate = float(selected_row["eco_rate"])

        diff_vs_national = eco_rate - national_rate
        gauge_options = {
            "tooltip": {
                "trigger": "item",
                "backgroundColor": "rgba(15, 23, 42, 0.92)",
                "borderWidth": 0,
                "textStyle": {"color": "#f8fafc", "fontSize": 12},
                "formatter": (
                    f"{region_name} 친환경 전환률<br/>"
                    f"전환률: {eco_rate:.1f}%<br/>"
                    f"친환경 등록: {format_count(eco_value)}대<br/>"
                    f"전체 등록: {format_count(total_value)}대<br/>"
                    f"전국 평균 대비 {diff_vs_national:+.1f}%p"
                ),
            },
            "series": [
                {
                    "type": "gauge",
                    "startAngle": 180,
                    "endAngle": 0,
                    "min": 0,
                    "max": 100,
                    "center": ["50%", "72%"],
                    "radius": "115%",
                    "splitNumber": 5,
                    "axisLine": {
                        "lineStyle": {
                            "width": 26,
                            "color": [
                                [0.1, "#ef4444"],
                                [0.2, "#f97316"],
                                [0.3, "#facc15"],
                                [0.5, "#84cc16"],
                                [1, "#16a34a"],
                            ],
                        }
                    },
                    "progress": {
                        "show": True,
                        "roundCap": True,
                        "width": 26,
                        "itemStyle": {"color": "rgba(15, 23, 42, 0.42)"},
                    },
                    "pointer": {
                        "show": True,
                        "length": "42%",
                        "width": 8,
                        "offsetCenter": [0, "-2%"],
                        "itemStyle": {"color": "#0f172a"},
                    },
                    "anchor": {
                        "show": True,
                        "showAbove": True,
                        "size": 18,
                        "itemStyle": {"color": "#ffffff", "borderColor": "#0f172a", "borderWidth": 4},
                    },
                    "axisTick": {"distance": -30, "splitNumber": 4, "lineStyle": {"color": "#fff", "width": 2}},
                    "splitLine": {"distance": -34, "length": 14, "lineStyle": {"color": "#fff", "width": 3}},
                    "axisLabel": {"distance": 4, "color": "#64748b", "fontSize": 11},
                    "detail": {
                        "valueAnimation": True,
                        "formatter": f"{eco_rate:.1f}%",
                        "color": "#0f172a",
                        "fontSize": 30,
                        "fontWeight": 700,
                        "offsetCenter": [0, "10%"],
                    },
                    "title": {
                        "offsetCenter": [0, "-48%"],
                        "fontSize": 17,
                        "fontWeight": 700,
                        "color": "#0f172a",
                    },
                    "data": [{"value": round(eco_rate, 1), "name": f"{region_name} 친환경 전환률"}],
                }
            ],
            "graphic": [
                {
                    "type": "text",
                    "left": "center",
                    "top": "80%",
                    "style": {
                        "text": f"친환경 {format_count(eco_value)}대 / 전체 {format_count(total_value)}대",
                        "fill": "#475569",
                        "fontSize": 13,
                    },
                },
                {
                    "type": "text",
                    "left": "center",
                    "top": "88%",
                    "style": {
                        "text": f"전국 평균 대비 {diff_vs_national:+.1f}%p",
                        "fill": "#1d4ed8" if diff_vs_national >= 0 else "#dc2626",
                        "fontSize": 13,
                        "fontWeight": 700,
                    },
                },
            ],
        }
        st_echarts(options=gauge_options, height="420px", key="newreg_eco_gauge")

    with rank_col:
        rank_df = region_summary.head(8).sort_values("eco_rate", ascending=True)
        rank_options = {
            "title": {"text": "지역별 전환률 순위", "left": "center"},
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}, "formatter": "{b}<br/>{c}%"},
            "grid": {"left": "8%", "right": "6%", "bottom": "6%", "containLabel": True},
            "xAxis": {"type": "value", "axisLabel": {"formatter": "{value}%"}},
            "yAxis": {"type": "category", "data": rank_df[region_col].astype(str).tolist()},
            "series": [
                {
                    "type": "bar",
                    "data": rank_df["eco_rate"].round(1).tolist(),
                    "itemStyle": {"color": "#22c55e", "borderRadius": [0, 10, 10, 0]},
                    "label": {"show": True, "position": "right", "formatter": "{c}%"},
                }
            ],
        }
        st_echarts(options=rank_options, height="420px", key="newreg_eco_rank")

st.subheader(":material/account_tree: 용도 및 모델 상세")
detail_col1, detail_col2 = st.columns(2, gap="large")

with detail_col1:
    use_options = df_use["CAR_USE"].dropna().astype(str).unique().tolist()
    selected_use = st.selectbox("용도 선택", use_options)
    selected_use_df = df_use[df_use["CAR_USE"].astype(str) == selected_use].copy()
    year_cols = [col for col in selected_use_df.columns if str(col).isdigit()]
    detail_key = "CAR_USE_DETAL" if "CAR_USE_DETAL" in selected_use_df.columns else "CAR_USE"
    numeric_df = selected_use_df[[detail_key, *year_cols]].copy()
    numeric_df[detail_key] = numeric_df[detail_key].fillna("Unknown").astype(str)
    numeric_df = numeric_df.set_index(detail_key).transpose()
    numeric_df.index = [
        str(idx) if len(str(idx)) == 4 else f"20{str(idx).zfill(2)}"
        for idx in numeric_df.index
    ]
    bump_fig, _, sort_fields = ch.bump_from_wide(numeric_df)
    for trace in bump_fig.data:
        series_name = trace.name
        if series_name in numeric_df.columns:
            trace.hovertemplate = "%{x}<br>" + series_name + ": %{customdata:,}대<extra></extra>"
            trace.customdata = numeric_df[series_name].tolist()
    bump_fig.update_layout(
        title="용도 세부 순위 변화",
        xaxis_title="연도",
        yaxis_title="순위",
        yaxis_tickvals=list(range(1, len(sort_fields) + 1)),
        yaxis_autorange="reversed",
    )
    st.plotly_chart(bump_fig, use_container_width=True)

with detail_col2:
    brand_options = sorted(filtered_df["ORG_CAR_MAKER_KOR"].dropna().astype(str).unique().tolist())
    selected_brand_detail = st.selectbox("브랜드 선택", brand_options, key="newreg_detail_brand")
    month_options = sorted(filtered_df["EXTRACT_DE"].dt.strftime("%Y-%m").unique().tolist())
    selected_month_detail = st.selectbox("등록월 선택", month_options, key="newreg_detail_month")
    detail_df = filtered_df[
        (filtered_df["ORG_CAR_MAKER_KOR"].astype(str) == selected_brand_detail)
        & (filtered_df["EXTRACT_DE"].dt.strftime("%Y-%m") == selected_month_detail)
    ]
    detail_df = (
        detail_df.groupby("CAR_MOEL_DT", as_index=False)["CNT"]
        .sum()
        .sort_values("CNT", ascending=False)
        .head(20)
    )
    model_options = {
        "title": {"text": f"{selected_brand_detail} 모델별 신규등록 Top 20", "left": "center"},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "grid": {"left": "4%", "right": "4%", "bottom": "20%", "containLabel": True},
        "xAxis": {"type": "category", "data": detail_df["CAR_MOEL_DT"].astype(str).tolist(), "axisLabel": {"rotate": 35}},
        "yAxis": {"type": "value"},
        "series": [
            {
                "type": "bar",
                "data": detail_df["CNT"].round(0).astype(int).tolist(),
                "itemStyle": {"color": "#60a5fa", "borderRadius": [8, 8, 0, 0]},
                "label": {"show": True, "position": "top"},
            }
        ],
    }
    st_echarts(options=model_options, height="520px", key="newreg_top20")

footer.render()
