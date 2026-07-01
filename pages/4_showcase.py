import warnings

import pandas as pd
import streamlit as st
from streamlit_echarts import JsCode, st_echarts

from app_core import footer
from app_core import ui
from app_core.data_loader import get_newreg_data
from app_core.nav import render_sidebar_nav

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="신차등록 쇼케이스",
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


def pct_change(current: float, previous: float) -> float | None:
    if previous in (None, 0) or pd.isna(previous):
        return None
    return (current - previous) / previous * 100


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def build_period_mask(series: pd.Series, months: int | None) -> pd.Series:
    if months is None:
        return pd.Series(True, index=series.index)
    latest = series.max()
    start = latest - pd.DateOffset(months=months - 1)
    return series >= start


def summarize_monthly(df: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        df.assign(month=df["EXTRACT_DE"].dt.to_period("M").dt.to_timestamp())
        .groupby("month", as_index=False)["CNT"]
        .sum()
        .sort_values("month")
    )
    monthly["mom_pct"] = monthly["CNT"].pct_change() * 100
    return monthly


def top_share(df: pd.DataFrame, group_col: str) -> tuple[str, float]:
    grouped = (
        df.groupby(group_col, dropna=False)["CNT"]
        .sum()
        .sort_values(ascending=False)
    )
    if grouped.empty:
        return "-", 0.0
    name = str(grouped.index[0])
    share = safe_ratio(float(grouped.iloc[0]), float(grouped.sum())) * 100
    return name, share


def normalize_frame(frame: pd.DataFrame, metric_cols: list[str]) -> pd.DataFrame:
    normalized = frame.copy()
    for col in metric_cols:
        max_value = normalized[col].max()
        normalized[col] = 0 if max_value == 0 else normalized[col] / max_value * 100
    return normalized


def top_change_summary(df: pd.DataFrame, group_col: str) -> tuple[str, float, str, float]:
    monthly_group = (
        df.groupby(["month", group_col], as_index=False)["CNT"]
        .sum()
        .sort_values(["month", group_col])
    )
    latest = monthly_group["month"].max()
    prev = monthly_group["month"].sort_values().unique()
    if len(prev) < 2:
        return "-", 0.0, "-", 0.0
    prev_month = prev[-2]
    latest_df = monthly_group[monthly_group["month"] == latest][[group_col, "CNT"]].rename(
        columns={"CNT": "latest_cnt"}
    )
    prev_df = monthly_group[monthly_group["month"] == prev_month][[group_col, "CNT"]].rename(
        columns={"CNT": "prev_cnt"}
    )
    change_df = latest_df.merge(prev_df, on=group_col, how="outer").fillna(0)
    change_df["delta"] = change_df["latest_cnt"] - change_df["prev_cnt"]
    inc_row = change_df.sort_values("delta", ascending=False).iloc[0]
    dec_row = change_df.sort_values("delta", ascending=True).iloc[0]
    return str(inc_row[group_col]), float(inc_row["delta"]), str(dec_row[group_col]), float(dec_row["delta"])


def detect_region_column(df: pd.DataFrame) -> str | None:
    candidates = ["지역", "REGION", "AREA"]
    for name in candidates:
        if name in df.columns:
            return name
    for col in df.columns:
        if "지역" in str(col):
            return col
    return None


data = get_newreg_data(base_dir="data/")
df = data["dim"].copy()
df["EXTRACT_DE"] = pd.to_datetime(df["EXTRACT_DE"].astype(str), format="%Y%m%d")
df["month"] = df["EXTRACT_DE"].dt.to_period("M").dt.to_timestamp()
df["CNT"] = pd.to_numeric(df["CNT"], errors="coerce").fillna(0)
analysis_year = int(df["EXTRACT_DE"].dt.year.max())
analysis_period_label = f"{analysis_year}-12"

st.title(":material/dashboard: 신차등록현황 쇼케이스")
st.markdown(
    "신차등록 데이터를 기준으로 **등록 규모, 최근 흐름, 구성 변화**를 한눈에 볼 수 있게 정리한 요약형 대시보드입니다.  \n"
    f"분석 기준년: **{analysis_year}**"
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
        "국산/외산",
        sorted(df["CL_HMMD_IMP_SE_NM"].dropna().astype(str).unique().tolist()),
    )
    selected_brand = st.multiselect(
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
        "소유자구분",
        sorted(df["OWNER_GB"].dropna().astype(str).unique().tolist()),
    )
    selected_age = st.multiselect(
        "연령대",
        sorted(df["AGE"].dropna().astype(str).unique().tolist()),
    )
    ui.sidebar_links()

mask = build_period_mask(df["month"], period_map[period_label])
filtered_df = df.loc[mask].copy()

if selected_origin:
    filtered_df = filtered_df[filtered_df["CL_HMMD_IMP_SE_NM"].isin(selected_origin)]
if selected_brand:
    filtered_df = filtered_df[filtered_df["ORG_CAR_MAKER_KOR"].isin(selected_brand)]
if selected_body:
    filtered_df = filtered_df[filtered_df["CAR_BT"].isin(selected_body)]
if selected_fuel:
    filtered_df = filtered_df[filtered_df["FUEL"].isin(selected_fuel)]
if selected_owner:
    filtered_df = filtered_df[filtered_df["OWNER_GB"].isin(selected_owner)]
if selected_age:
    filtered_df = filtered_df[filtered_df["AGE"].isin(selected_age)]

if filtered_df.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다. 필터를 조정해 주세요.")
    footer.render()
    st.stop()

monthly_summary = summarize_monthly(filtered_df)
latest_month = monthly_summary["month"].max()
latest_month_value = float(
    monthly_summary.loc[monthly_summary["month"] == latest_month, "CNT"].iloc[0]
)
previous_month_value = (
    float(monthly_summary.iloc[-2]["CNT"]) if len(monthly_summary) > 1 else None
)
latest_delta = pct_change(latest_month_value, previous_month_value)

total_cnt = float(filtered_df["CNT"].sum())
domestic_cnt = float(
    filtered_df.loc[
        filtered_df["CL_HMMD_IMP_SE_NM"].astype(str).isin(DOMESTIC_LABELS), "CNT"
    ].sum()
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

sparkline = monthly_summary["CNT"].tolist()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(
        "선택 기간 총 등록대수",
        format_count(total_cnt),
        border=True,
        chart_data=sparkline,
        chart_type="area",
    )
with col2:
    st.metric(
        "최근월 등록대수",
        format_count(latest_month_value),
        None if latest_delta is None else format_pct(latest_delta),
        border=True,
        chart_data=sparkline,
        chart_type="bar",
    )
with col3:
    st.metric(
        "국산 비중",
        format_pct(domestic_share),
        f"외산 {format_pct(100 - domestic_share)}",
        border=True,
        chart_data=sparkline,
        chart_type="line",
    )
with col4:
    st.metric(
        "1위 브랜드 점유율",
        format_pct(top_brand_share),
        top_brand_name,
        border=True,
        chart_data=sparkline,
        chart_type="area",
    )

# st.caption(
#     f"최근월 기준 최다 차형은 **{top_body_name}**이며, 비중은 **{format_pct(top_body_share)}**입니다."
# )

st.markdown(
    f"""
    <div style="padding:16px 18px; border:1px solid #dbeafe; border-radius:18px; background:linear-gradient(180deg, #ffffff 0%, #f8fbff 100%); margin:10px 0 18px 0;">
      <div style="font-size:15px; color:#0f172a; font-weight:700; margin-bottom:6px;">{analysis_year}년 한줄 요약</div>
      <div style="font-size:14px; color:#334155; line-height:1.6;">
        {analysis_year}년 누적 등록은 <b>{format_count(total_cnt)}대</b>이며,
        시장 점유율 1위 브랜드는 <b>{top_brand_name}</b> ({format_pct(top_brand_share)}), 최다 차형은 <b>{top_body_name}</b>,
        최다 연료는 <b>{top_fuel_name}</b> ({format_pct(top_fuel_share)})입니다.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

insight_col1, insight_col2 = st.columns(2)
with insight_col1:
    st.info(
        f"상위 3개 브랜드가 전체 등록의 **{format_pct(top3_brand_share)}**를 차지합니다. 시장 집중도를 빠르게 볼 수 있는 지표입니다."
    )
with insight_col2:
    st.info(
        f"최근월 기준 증가폭 1위 연료는 **{inc_fuel_name}** ({format_count(inc_fuel_delta)}대), 감소폭이 큰 차형은 **{dec_body_name}** ({format_count(abs(dec_body_delta))}대)입니다."
    )

st.subheader(":material/trending_up: 등록 추이")
#st.caption("최근 신차등록 흐름과 전월 대비 증감률을 함께 확인합니다.")
row2_1, row2_2 = st.columns([3, 2], gap="small")

with row2_1:
    trend_options = {
        "title": {"text": "월별 등록대수 추이", "left": "center", "top": 5},
        "tooltip": {
            "trigger": "axis",
            "valueFormatter": JsCode(
                "function(v){return Math.round(v).toLocaleString()+'대'}"
            ),
        },
        "toolbox": {
            "feature": {
                "saveAsImage": {},
                "dataView": {"readOnly": True},
                "restore": {},
                "magicType": {"type": ["line", "bar"]},
            }
        },
        "legend": {"bottom": "0"},
        "xAxis": {
            "type": "category",
            "data": monthly_summary["month"].dt.strftime("%Y-%m").tolist(),
        },
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
    st_echarts(options=trend_options, height="400px", key="showcase_trend")

with row2_2:
    growth_df = monthly_summary.dropna(subset=["mom_pct"]).copy()
    if growth_df.empty:
        st.info("증감률을 표시하려면 2개월 이상 데이터가 필요합니다.")
    else:
        growth_series = []
        for value in growth_df["mom_pct"].tolist():
            growth_series.append(
                {
                    "value": round(value, 1),
                    "itemStyle": {"color": "#16a34a" if value >= 0 else "#dc2626"},
                }
            )

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
            "series": [{"type": "bar", "data": growth_series}],
        }
        st_echarts(options=growth_options, height="400px", key="showcase_growth")

st.subheader(":material/insights: 추가 인사이트")
#st.caption("신차등록 요약 페이지를 보완할 수 있는 핵심 포인트만 가볍게 추가했습니다.")
extra_1, extra_2 = st.columns(2)

with extra_1:
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
                "itemStyle": {"color": "#3b82f6", "borderRadius": [0, 10, 10, 0]},
                "label": {"show": True, "position": "right"},
            }
        ],
    }
    st_echarts(options=top_brand_options, height="340px", key="showcase_brand_focus")

with extra_2:
    origin_fuel_mix = (
        filtered_df.groupby(["CL_HMMD_IMP_SE_NM", "FUEL"], as_index=False)["CNT"]
        .sum()
    )
    origin_order = (
        origin_fuel_mix.groupby("CL_HMMD_IMP_SE_NM")["CNT"].sum().sort_values(ascending=False).index.tolist()
    )
    fuel_order = (
        origin_fuel_mix.groupby("FUEL")["CNT"].sum().sort_values(ascending=False).index.tolist()
    )
    origin_fuel_series = []
    for fuel in fuel_order:
        values = []
        for origin in origin_order[::-1]:
            subset = origin_fuel_mix[
                (origin_fuel_mix["CL_HMMD_IMP_SE_NM"] == origin)
                & (origin_fuel_mix["FUEL"] == fuel)
            ]["CNT"]
            values.append(int(subset.iloc[0]) if not subset.empty else 0)
        origin_fuel_series.append(
            {
                "name": str(fuel),
                "type": "bar",
                "stack": "total",
                "emphasis": {"focus": "series"},
                "data": values,
            }
        )

    origin_fuel_options = {
        "title": {"text": "국산/외산별 연료 구성", "left": "center"},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {"bottom": "0", "type": "scroll"},
        "grid": {"left": "4%", "right": "4%", "bottom": "14%", "containLabel": True},
        "xAxis": {"type": "value"},
        "yAxis": {"type": "category", "data": origin_order[::-1]},
        "series": origin_fuel_series,
    }
    st_echarts(options=origin_fuel_options, height="340px", key="showcase_origin_fuel")

st.subheader(":material/explore: 구성 분석")
#st.caption("브랜드, 모델, 차형, 연료 기준으로 신차등록 구성을 요약합니다.")
row3_1, row3_2, row3_3 = st.columns(3)

with row3_1:
    brand_model = (
        filtered_df.groupby(["ORG_CAR_MAKER_KOR", "CAR_MOEL_DT"], as_index=False)["CNT"]
        .sum()
        .sort_values("CNT", ascending=False)
    )
    tree_data = []
    for brand, group in brand_model.groupby("ORG_CAR_MAKER_KOR"):
        children = [
            {"name": str(row["CAR_MOEL_DT"]), "value": int(row["CNT"])}
            for _, row in group.head(12).iterrows()
        ]
        tree_data.append({"name": str(brand), "children": children})

    treemap_options = {
        "title": {"text": "브랜드-모델 Treemap", "left": "center"},
        "tooltip": {
            "formatter": JsCode(
                "function(p){return p.name + '<br/>등록대수: ' + Math.round(p.value || 0).toLocaleString() + '대';}"
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
                    {
                        "itemStyle": {
                            "borderColor": "#ffffff",
                            "borderWidth": 3,
                            "gapWidth": 3,
                        }
                    },
                    {
                        "itemStyle": {
                            "borderColor": "#f3f4f6",
                            "borderWidth": 1,
                            "gapWidth": 1,
                        }
                    },
                ],
            }
        ],
    }
    st_echarts(options=treemap_options, height="450px", key="showcase_treemap")

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
                        g.loc[
                            ~g["CL_HMMD_IMP_SE_NM"].astype(str).isin(DOMESTIC_LABELS),
                            "CNT",
                        ].sum(),
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

    radar_metrics = [
        "total_cnt",
        "brand_diversity",
        "model_diversity",
        "import_share",
        "private_share",
    ]
    radar_labels = ["등록규모", "브랜드수", "모델수", "외산비중", "개인비중"]
    radar_norm = normalize_frame(body_profile, radar_metrics)
    radar_series = []
    for _, row in radar_norm.iterrows():
        radar_series.append(
            {
                "name": str(row["CAR_BT"]),
                "value": [round(float(row[col]), 1) for col in radar_metrics],
            }
        )

    radar_options = {
        "title": {"text": "상위 차형 프로파일", "left": "center"},
        "tooltip": {"trigger": "item"},
        "legend": {
            "bottom": "0",
            "type": "scroll",
            "data": [item["name"] for item in radar_series],
        },
        "radar": {
            "indicator": [{"name": label, "max": 100} for label in radar_labels],
            "center": ["50%", "50%"],
            "radius": "60%",
        },
        "series": [{"type": "radar", "data": radar_series, "areaStyle": {"opacity": 0.08}}],
    }
    st_echarts(options=radar_options, height="450px", key="showcase_radar")

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
    fuel_order = (
        fuel_mix.groupby("FUEL")["CNT"].sum().sort_values(ascending=False).index.tolist()
    )
    stacked_series = []
    for fuel in fuel_order:
        values = []
        for brand in top_brands[::-1]:
            subset = fuel_mix[
                (fuel_mix["ORG_CAR_MAKER_KOR"] == brand) & (fuel_mix["FUEL"] == fuel)
            ]["CNT"]
            values.append(int(subset.iloc[0]) if not subset.empty else 0)
        stacked_series.append(
            {
                "name": str(fuel),
                "type": "bar",
                "stack": "total",
                "emphasis": {"focus": "series"},
                "data": values,
            }
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
    st_echarts(options=top5_options, height="450px", key="showcase_top5")

st.subheader(":material/touch_app: 브랜드 드릴다운")
#st.caption("브랜드별 등록 규모를 비교하고, 선택 브랜드의 월별 추이와 대표 모델을 확인합니다.")
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

scatter_data = []
for _, row in brand_scatter.iterrows():
    scatter_data.append(
        [
            int(row["model_count"]),
            int(row["total_cnt"]),
            int(max(row["latest_cnt"], 1)),
            str(row["ORG_CAR_MAKER_KOR"]),
        ]
    )

with left:
    scatter_options = {
        "animation": False,
        "title": {"text": "브랜드 포트폴리오", "left": "center"},
        "tooltip": {
            "trigger": "item",
            "formatter": JsCode(
                "function(p){var v=p.value; return v[3] + '<br/>모델 수: ' + v[0] + '<br/>등록대수: ' + Math.round(v[1]).toLocaleString() + '대<br/>최근월: ' + Math.round(v[2]).toLocaleString() + '대';}"
            ),
        },
        "xAxis": {"name": "모델 수", "type": "value"},
        "yAxis": {"name": "총 등록대수", "type": "value"},
        "visualMap": {
            "show": False,
            "dimension": 2,
            "min": 1,
            "max": max(item[2] for item in scatter_data) if scatter_data else 1,
            "inRange": {"symbolSize": [12, 48]},
        },
        "series": [
            {
                "type": "scatter",
                "data": scatter_data,
                "itemStyle": {"opacity": 0.78, "color": "#2563eb"},
            }
        ],
    }
    st_echarts(options=scatter_options, height="450px", key="showcase_scatter")

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
            "valueFormatter": JsCode(
                "function(v){return Math.round(v).toLocaleString()+'대'}"
            ),
        },
        "legend": {"bottom": "0"},
        "grid": {"bottom": "16%"},
        "xAxis": {
            "type": "category",
            "data": brand_monthly["month"].dt.strftime("%Y-%m").tolist(),
        },
        "yAxis": [
            {"type": "value", "name": "등록대수"},
            {"type": "value", "name": "증감률"},
        ],
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
    st_echarts(options=detail_options, height="300px", key="showcase_brand_detail")
    st.dataframe(
        top_models.rename(columns={"CAR_MOEL_DT": "모델", "CNT": "등록대수"}).reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )

st.subheader(":material/settings: 세부 분포")
#st.caption("연령, 소유자, 월별 구성, 연료 분포로 하단 인사이트를 보완합니다.")
row5_1, row5_2, row5_3, row5_4 = st.columns(4)

with row5_1:
    age_body = (
        filtered_df.groupby(["AGE", "CAR_BT"], as_index=False)["CNT"]
        .sum()
        .sort_values("CNT", ascending=False)
    )
    age_order = (
        age_body.groupby("AGE")["CNT"].sum().sort_values(ascending=False).index.tolist()
    )
    body_order = (
        age_body.groupby("CAR_BT")["CNT"].sum().sort_values(ascending=False).head(6).index.tolist()
    )
    heatmap_data = []
    for _, row in age_body.iterrows():
        if row["CAR_BT"] in body_order:
            heatmap_data.append(
                [
                    body_order.index(row["CAR_BT"]),
                    age_order.index(row["AGE"]),
                    int(row["CNT"]),
                ]
            )

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
    st_echarts(options=heatmap_options, height="450px", key="showcase_heatmap")

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
        "title": {"text": "소유자구분별 규모", "left": "center"},
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
    st_echarts(options=owner_options, height="450px", key="showcase_owner_bar")

with row5_3:
    monthly_origin = (
        filtered_df.groupby(["month", "CL_HMMD_IMP_SE_NM"], as_index=False)["CNT"]
        .sum()
        .sort_values("month")
    )
    origin_labels = (
        monthly_origin.groupby("CL_HMMD_IMP_SE_NM")["CNT"]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )
    monthly_series = []
    month_labels = sorted(monthly_origin["month"].dt.strftime("%Y-%m").unique().tolist())
    for label in origin_labels:
        values = []
        for month_label in month_labels:
            subset = monthly_origin[
                (monthly_origin["CL_HMMD_IMP_SE_NM"] == label)
                & (monthly_origin["month"].dt.strftime("%Y-%m") == month_label)
            ]["CNT"]
            values.append(int(subset.iloc[0]) if not subset.empty else 0)
        monthly_series.append(
            {
                "name": str(label),
                "type": "bar",
                "stack": "total",
                "data": values,
            }
        )

    monthly_mix_options = {
        "title": {"text": "월별 국산/외산 구성", "left": "center"},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {"bottom": "0"},
        "xAxis": {"type": "category", "data": month_labels, "axisLabel": {"rotate": 35}},
        "yAxis": {"type": "value"},
        "grid": {"bottom": "16%", "containLabel": True},
        "series": monthly_series,
    }
    st_echarts(options=monthly_mix_options, height="450px", key="showcase_origin_mix")

with row5_4:
    fuel_dist = (
        filtered_df.groupby("FUEL", as_index=False)["CNT"]
        .sum()
        .sort_values("CNT", ascending=False)
    )
    fuel_options = {
        "title": {"text": "연료 비중", "left": "center"},
        "tooltip": {"trigger": "item", "formatter": "{b}: {c}대 ({d}%)"},
        "series": [
            {
                "type": "pie",
                "radius": ["40%", "70%"],
                "avoidLabelOverlap": True,
                "itemStyle": {
                    "borderRadius": 8,
                    "borderColor": "#fff",
                    "borderWidth": 2,
                },
                "label": {"show": True, "formatter": "{b}\n{d}%"},
                "data": [
                    {"name": str(row["FUEL"]), "value": int(row["CNT"])}
                    for _, row in fuel_dist.iterrows()
                ],
            }
        ],
    }
    st_echarts(options=fuel_options, height="450px", key="showcase_fuel_donut")

region_col = detect_region_column(filtered_df)
if region_col:
    st.subheader(":material/speed: 지역별 친환경 전환률")
    st.caption(f"`{period_label}` 누적 기준으로 지역별 친환경차(전기·하이브리드·수소) 등록 비중을 자동차 계기판 형태로 확인합니다.")

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
        selected_region = st.selectbox("지역 선택", region_options, key="showcase_region")
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
                    f"전국 평균 대비: {diff_vs_national:+.1f}%p"
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
                        "itemStyle": {
                            "color": "rgba(15, 23, 42, 0.42)"
                        },
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
        st_echarts(options=gauge_options, height="420px", key="showcase_eco_gauge")

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
        st_echarts(options=rank_options, height="420px", key="showcase_eco_rank")

# with st.expander("원본 데이터 미리보기", icon=":material/table_view:"):
#     preview_cols = [
#         "EXTRACT_DE",
#         "ORG_CAR_MAKER_KOR",
#         "CAR_MOEL_DT",
#         "CAR_BT",
#         "FUEL",
#         "OWNER_GB",
#         "CL_HMMD_IMP_SE_NM",
#         "CNT",
#     ]
#     st.dataframe(filtered_df[preview_cols].head(100), use_container_width=True, hide_index=True)

footer.render()
