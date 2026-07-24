import pandas as pd
import streamlit as st
from streamlit_echarts import JsCode, st_echarts

from app_core import ui
from app_core.data_loader import get_usedreg_data
from app_core.nav import render_sidebar_nav


st.set_page_config(page_title="Used Regist Summary", layout="wide", initial_sidebar_state="auto")
render_sidebar_nav()

ECO_FUELS = ["전기", "하이브리드", "수소"]


def count(value: float) -> str:
    return f"{int(round(value)):,}"


def pct(value: float) -> str:
    return f"{value:.1f}%"


def ratio(numerator: float, denominator: float) -> float:
    return 0.0 if denominator == 0 else numerator / denominator * 100


def change(current: float, previous: float | None) -> float | None:
    if previous in (None, 0) or pd.isna(previous):
        return None
    return (current - previous) / previous * 100


def top_value(frame: pd.DataFrame, column: str) -> tuple[str, float]:
    grouped = frame.groupby(column, dropna=False)["CNT"].sum().sort_values(ascending=False)
    if grouped.empty:
        return "-", 0.0
    return str(grouped.index[0]), ratio(float(grouped.iloc[0]), float(grouped.sum()))


def top_growth(frame: pd.DataFrame, column: str) -> tuple[str, float]:
    grouped = frame.groupby(["month", column], as_index=False)["CNT"].sum()
    months = sorted(grouped["month"].unique())
    if len(months) < 2:
        return "-", 0.0
    current = grouped[grouped["month"] == months[-1]][[column, "CNT"]].rename(columns={"CNT": "current"})
    previous = grouped[grouped["month"] == months[-2]][[column, "CNT"]].rename(columns={"CNT": "previous"})
    delta = current.merge(previous, on=column, how="outer").fillna(0)
    delta["value"] = delta["current"] - delta["previous"]
    row = delta.sort_values("value", ascending=False).iloc[0]
    return str(row[column]), float(row["value"])


data = get_usedreg_data(base_dir="data/")
df = data["dim"].copy()
df["EXTRACT_DE"] = pd.to_datetime(df["EXTRACT_DE"].astype(str), format="%Y%m", errors="coerce")
df = df.dropna(subset=["EXTRACT_DE"]).copy()
df["month"] = df["EXTRACT_DE"].dt.to_period("M").dt.to_timestamp()
df["CNT"] = pd.to_numeric(df["CNT"], errors="coerce").fillna(0)

dimension_labels = {
    "CL_HMMD_IMP_SE_NM": "국산/수입",
    "ORG_CAR_MAKER_KOR": "브랜드",
    "CAR_BT": "차종",
    "USE_FUEL_NM": "연료",
    "CAR_SZ": "차급",
}
for column in [*dimension_labels, "CAR_MOEL_DT", "CAR_MODEL_KOR"]:
    if column in df.columns:
        df[column] = df[column].fillna("미상").astype(str)

st.title(":material/sync_alt: Used Regist Summary")
st.caption(f"데이터 기간: {df['EXTRACT_DE'].min():%Y-%m} ~ {df['EXTRACT_DE'].max():%Y-%m}")
st.info("집계 기준: 이전등록 데이터는 **실거래 기준**이며, **매도·알선·개인거래**를 기준으로 집계했습니다.")

with st.sidebar:
    st.title(":material/filter_alt: 필터")
    period_label = st.selectbox("조회 기간", ["최근 3개월", "최근 6개월", "최근 12개월", "전체"], index=1)
    period_map = {"최근 3개월": 3, "최근 6개월": 6, "최근 12개월": 12, "전체": None}
    base_df = df.copy()
    for column, label in dimension_labels.items():
        options = sorted(base_df[column].unique().tolist())
        selected = st.multiselect(label, options)
        if selected:
            base_df = base_df[base_df[column].isin(selected)]
    ui.sidebar_links()

if period_map[period_label] is None:
    filtered_df = base_df.copy()
else:
    start = base_df["month"].max() - pd.DateOffset(months=period_map[period_label] - 1)
    filtered_df = base_df[base_df["month"] >= start].copy()
if filtered_df.empty:
    st.warning("선택한 조건에 해당하는 이전등록 데이터가 없습니다. 필터를 조정해 주세요.")
    st.stop()

monthly = filtered_df.groupby("month", as_index=False)["CNT"].sum().sort_values("month")
monthly["mom_pct"] = monthly["CNT"].pct_change() * 100
latest_month = monthly["month"].max()
latest_count = float(monthly.loc[monthly["month"] == latest_month, "CNT"].iloc[0])
previous_count = float(monthly.iloc[-2]["CNT"]) if len(monthly) > 1 else None
total_count = float(filtered_df["CNT"].sum())
eco_by_fuel = filtered_df.groupby("USE_FUEL_NM")["CNT"].sum().reindex(ECO_FUELS, fill_value=0)
eco_count = float(eco_by_fuel.sum())
eco_share = ratio(eco_count, total_count)
electric_share = ratio(float(eco_by_fuel["전기"]), total_count)
hybrid_share = ratio(float(eco_by_fuel["하이브리드"]), total_count)
hydrogen_share = ratio(float(eco_by_fuel["수소"]), total_count)
brand, brand_share = top_value(filtered_df, "ORG_CAR_MAKER_KOR")
model, model_share = top_value(filtered_df, "CAR_MODEL_KOR")
body, body_share = top_value(filtered_df, "CAR_BT")
rising_brand, rising_count = top_growth(filtered_df, "ORG_CAR_MAKER_KOR")

metric_cols = st.columns(4)
metric_cols[0].metric("선택 기간 이전등록", count(total_count), border=True)
metric_cols[1].metric("최신월 이전등록", count(latest_count), None if change(latest_count, previous_count) is None else pct(change(latest_count, previous_count)), border=True)
metric_cols[2].metric("친환경차 거래 비중", pct(eco_share), f"친환경 {count(eco_count)}대", border=True)
metric_cols[3].metric("1위 브랜드 점유율", pct(brand_share), brand, border=True)

st.markdown(f"""
<div style="padding:16px 18px; border:1px solid #dbeafe; border-radius:16px; background:#f8fbff; margin:12px 0 18px;">
  <div style="font-size:15px; font-weight:700; margin-bottom:6px;">{period_label} 이전등록 핵심 요약</div>
  <div style="color:#334155; line-height:1.7;">선택 기간 실거래 이전등록은 <b>{count(total_count)}대</b>입니다. 가장 많이 거래된 브랜드는 <b>{brand}</b> ({pct(brand_share)}), 대표 모델은 <b>{model}</b> ({pct(model_share)}), 주요 차종은 <b>{body}</b> ({pct(body_share)})입니다.</div>
</div>""", unsafe_allow_html=True)

insight_left, insight_right = st.columns(2)
insight_left.info(f"최신월 기준 거래 증가 폭이 가장 큰 브랜드는 **{rising_brand}** ({count(rising_count)}대)입니다.")
insight_right.info(f"친환경 연료 비중은 전기 **{pct(electric_share)}**, 하이브리드 **{pct(hybrid_share)}**, 수소 **{pct(hydrogen_share)}** 입니다.")

st.subheader(":material/trending_up: 거래 추이")
trend_col, growth_col = st.columns([3, 2])
with trend_col:
    st_echarts(options={
        "tooltip": {"trigger": "axis", "valueFormatter": JsCode("function(v){return Math.round(v).toLocaleString()+'대'}")},
        "xAxis": {"type": "category", "data": monthly["month"].dt.strftime("%Y-%m").tolist()},
        "yAxis": {"type": "value", "name": "대수"}, "grid": {"left": "6%", "right": "4%", "bottom": "12%", "containLabel": True},
        "series": [{"name": "이전등록", "type": "line", "smooth": True, "areaStyle": {"opacity": 0.12}, "data": monthly["CNT"].round().astype(int).tolist(), "lineStyle": {"width": 3, "color": "#2563eb"}, "itemStyle": {"color": "#2563eb"}}],
    }, height="360px", key="usedreg_trend")
with growth_col:
    growth = monthly.dropna(subset=["mom_pct"])
    if growth.empty:
        st.info("증감률은 두 달 이상의 데이터가 있을 때 표시됩니다.")
    else:
        st_echarts(options={
            "tooltip": {"trigger": "axis", "formatter": "{b}<br/>{c}%"},
            "xAxis": {"type": "category", "data": growth["month"].dt.strftime("%Y-%m").tolist(), "axisLabel": {"rotate": 35}},
            "yAxis": {"type": "value", "axisLabel": {"formatter": "{value}%"}}, "grid": {"left": "8%", "right": "4%", "bottom": "16%", "containLabel": True},
            "series": [{"type": "bar", "data": [{"value": round(value, 1), "itemStyle": {"color": "#16a34a" if value >= 0 else "#dc2626"}} for value in growth["mom_pct"]]}],
        }, height="360px", key="usedreg_growth")

st.subheader(":material/insights: 시장 구성")
brand_col, body_col = st.columns(2)
with brand_col:
    st.markdown("#### 국산/수입별 브랜드 거래")
    brand_totals = filtered_df.groupby("ORG_CAR_MAKER_KOR", as_index=False)["CNT"].sum().nlargest(10, "CNT")
    brands = brand_totals.sort_values("CNT")["ORG_CAR_MAKER_KOR"].tolist()
    origin_brand = filtered_df.groupby(["ORG_CAR_MAKER_KOR", "CL_HMMD_IMP_SE_NM"], as_index=False)["CNT"].sum()
    origins = filtered_df.groupby("CL_HMMD_IMP_SE_NM")["CNT"].sum().sort_values(ascending=False).index.tolist()
    origin_colors = ["#2563eb", "#f97316", "#64748b", "#a855f7"]
    brand_series = []
    for index, origin in enumerate(origins):
        values = [
            int(origin_brand.loc[(origin_brand["ORG_CAR_MAKER_KOR"] == brand) & (origin_brand["CL_HMMD_IMP_SE_NM"] == origin), "CNT"].sum())
            for brand in brands
        ]
        brand_series.append({"name": origin, "type": "bar", "stack": "total", "data": values, "itemStyle": {"color": origin_colors[index % len(origin_colors)]}})
    st_echarts(options={
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}}, "legend": {"bottom": 0},
        "grid": {"left": "8%", "right": "8%", "bottom": "14%", "containLabel": True},
        "xAxis": {"type": "value"}, "yAxis": {"type": "category", "data": brands}, "series": brand_series,
    }, height="400px", key="usedreg_brand")
with body_col:
    st.markdown("#### 외형별 거래 구성")
    bodies = filtered_df.groupby("CAR_BT", as_index=False)["CNT"].sum().nlargest(8, "CNT")
    st_echarts(options={
        "tooltip": {"trigger": "item", "formatter": "{b}<br/>{c}대 ({d}%)"},
        "legend": {"bottom": 0, "type": "scroll"},
        "series": [{"type": "pie", "radius": ["38%", "70%"], "center": ["50%", "44%"], "label": {"formatter": "{b}\n{d}%"}, "data": [{"name": row["CAR_BT"], "value": int(row["CNT"])} for _, row in bodies.iterrows()]}],
    }, height="400px", key="usedreg_body_pie")

size_col, fuel_col = st.columns(2)
with size_col:
    st.markdown("#### 차급별 거래 구성")
    sizes = filtered_df.groupby("CAR_SZ", as_index=False)["CNT"].sum().nlargest(10, "CNT").sort_values("CNT")
    st_echarts(options={
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "grid": {"left": "10%", "right": "8%", "bottom": "6%", "containLabel": True},
        "xAxis": {"type": "value"}, "yAxis": {"type": "category", "data": sizes["CAR_SZ"].tolist()},
        "series": [{"type": "bar", "data": sizes["CNT"].round().astype(int).tolist(), "itemStyle": {"color": "#14b8a6", "borderRadius": [0, 8, 8, 0]}, "label": {"show": True, "position": "right"}}],
    }, height="400px", key="usedreg_size")
with fuel_col:
    st.markdown("#### 연료별 거래 구성")
    fuels = filtered_df.groupby("USE_FUEL_NM", as_index=False)["CNT"].sum().nlargest(8, "CNT")
    st_echarts(options={
        "tooltip": {"trigger": "item", "formatter": "{b}<br/>{c}대 ({d}%)"},
        "legend": {"bottom": 0, "type": "scroll"},
        "series": [{"type": "pie", "radius": ["38%", "70%"], "center": ["50%", "44%"], "label": {"formatter": "{b}\n{d}%"}, "data": [{"name": row["USE_FUEL_NM"], "value": int(row["CNT"])} for _, row in fuels.iterrows()]}],
    }, height="400px", key="usedreg_fuel_pie")

st.subheader(":material/format_list_numbered: 세부 모델 거래")
model_chart_col, model_table_col = st.columns([3, 2])
models = (
    filtered_df.groupby(["ORG_CAR_MAKER_KOR", "CAR_MODEL_KOR"], as_index=False)["CNT"]
    .sum()
    .nlargest(20, "CNT")
)
with model_chart_col:
    top_models = models.head(15).copy()
    top_models["label"] = top_models["ORG_CAR_MAKER_KOR"] + " | " + top_models["CAR_MODEL_KOR"]
    top_models = top_models.sort_values("CNT")
    st_echarts(options={
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "grid": {"left": "12%", "right": "8%", "bottom": "6%", "containLabel": True},
        "xAxis": {"type": "value"},
        "yAxis": {"type": "category", "data": top_models["label"].tolist()},
        "series": [{"type": "bar", "data": top_models["CNT"].round().astype(int).tolist(), "itemStyle": {"color": "#6366f1", "borderRadius": [0, 8, 8, 0]}, "label": {"show": True, "position": "right"}}],
    }, height="520px", key="usedreg_detail_model")
with model_table_col:
    models.index = range(1, len(models) + 1)
    st.dataframe(
        models.rename(columns={"ORG_CAR_MAKER_KOR": "브랜드", "CAR_MODEL_KOR": "세부 모델", "CNT": "이전등록 대수"}),
        width="stretch",
        height=520,
    )
