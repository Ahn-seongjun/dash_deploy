# pages/summary/ersr_reg_summary.py
import streamlit as st
st.set_page_config(page_title="말소등록 Summary", layout="wide", initial_sidebar_state="auto")
import pandas as pd
import warnings
warnings.filterwarnings('ignore')
from app_core.nav import render_sidebar_nav
render_sidebar_nav()
from app_core import footer
from app_core import data_loader as dl
from app_core import charts as ch
from app_core import ui

st.title("말소 등록 요약")

# 데이터 로딩 (ERSR 전용)
data = dl.get_ersr_data(base_dir="data")
df = data["monthly"]

# 원본 전처리 유지
df["val"] = 1
df["val"] = df["val"].astype(int)
df["EXTRACT_DE"] = pd.to_datetime(df["EXTRACT_DE"].astype("str"))
reg = format(len(df), ",d")

# 사이드바
with st.sidebar:
    ui.sidebar_links()

st.markdown("## 2024 Yearly Summary")
st.markdown(f"### 2024년 자진말소(폐차) 등록대수 : {reg}")
st.markdown("- 승용차 대상 집계")
st.markdown("- 말소 등록 : 자진말소(폐차)")
st.markdown("----")

# 연료 선택
fuel = st.selectbox("연료", sorted(df["연료"].dropna().unique().tolist()))

# 월별 집계 피벗 및 전월 대비 증감률 계산 (원본 로직 유지)
er_pivo = pd.pivot_table(
    df, index="EXTRACT_DE", columns="연료", values="val", aggfunc="sum"
).sort_index()
er_pivo[f"{fuel}-1개월"] = er_pivo[fuel].shift(1)
er_pivo[f"{fuel}_증감"] = ((er_pivo[fuel] - er_pivo[f"{fuel}-1개월"]) / er_pivo[f"{fuel}-1개월"]) * 100

# 이중축 그래프: 막대(말소대수) + 라인(전월 대비 증감률)
mon_reg = ch.dual_axis_bar_line(
    x=er_pivo.index,
    bar_y=er_pivo[fuel],
    line_y=er_pivo[f"{fuel}_증감"],
    bar_name=f"{fuel} 말소대수",
    line_name="전월대비 증감률(%)",
    bar_color="lightblue", line_color="red", line_dash="dash",
    x_title="2024년", y1_title="말소대수", y2_title="증감률(%)",
    template="plotly_white"
)
st.plotly_chart(mon_reg, use_container_width=True)

midleft_column, midright_column = st.columns([2, 2], gap="large")
botleft_column, botright_column = st.columns(2, gap="large")
bot2left, bot2right = st.columns(2, gap="large")
bot3le, bot3ri = st.columns(2, gap="large")

with midleft_column:
    st.subheader("국산 말소대수 TOP 10")
    brand_na = (
        df[df["CL_HMMD_IMP_SE_NM"] == "국산"]
        .groupby("ORG_CAR_MAKER_KOR")[["val"]].sum()
        .sort_values(by="val", ascending=False).head(10).reset_index()
    )
    br_na = ch.category_bar(brand_na, x="val", y="ORG_CAR_MAKER_KOR",
                            color="ORG_CAR_MAKER_KOR", orientation="h",
                            labels=dict(ORG_CAR_MAKER_KOR="브랜드", val="대수"))
    br_na.update_layout(height=600, template="plotly_white", legend_title_text="브랜드")
    st.plotly_chart(br_na, use_container_width=True)

    mo_na_cnt = (
        df[df["CL_HMMD_IMP_SE_NM"] == "국산"]
        .groupby("CAR_MOEL_DT")[["val"]].sum()
        .sort_values(by="val", ascending=False).head(10).reset_index()
    )
    mo_na = ch.category_bar(mo_na_cnt, x="val", y="CAR_MOEL_DT",
                            color="CAR_MOEL_DT", orientation="h",
                            labels=dict(CAR_MOEL_DT="모델", val="대수"))
    mo_na.update_layout(height=600, template="plotly_white", legend_title_text="모델")
    st.plotly_chart(mo_na, use_container_width=True)

with midright_column:
    st.subheader("수입 말소대수 TOP 10")
    brand_im = (
        df[df["CL_HMMD_IMP_SE_NM"] == "외산"]
        .groupby("ORG_CAR_MAKER_KOR")[["val"]].sum()
        .sort_values(by="val", ascending=False).head(10).reset_index()
    )
    br_im = ch.category_bar(brand_im, x="val", y="ORG_CAR_MAKER_KOR",
                            color="ORG_CAR_MAKER_KOR", orientation="h",
                            labels=dict(ORG_CAR_MAKER_KOR="브랜드", val="대수"))
    br_im.update_layout(height=600, template="plotly_white", legend_title_text="브랜드")
    st.plotly_chart(br_im, use_container_width=True)

    mo_im_cnt = (
        df[df["CL_HMMD_IMP_SE_NM"] == "외산"]
        .groupby("CAR_MOEL_DT")[["val"]].sum()
        .sort_values(by="val", ascending=False).head(10).reset_index()
    )
    mo_im = ch.category_bar(mo_im_cnt, x="val", y="CAR_MOEL_DT",
                            color="CAR_MOEL_DT", orientation="h",
                            labels=dict(CAR_MOEL_DT="모델", val="대수"))
    mo_im.update_layout(height=600, template="plotly_white", legend_title_text="모델")
    st.plotly_chart(mo_im, use_container_width=True)

with botleft_column:
    sou_gb = ch.sunburst_simple(df, path=["소유자유형", "성별", "연령"], values="val",
                                color="성별", title="소유자 유형별 분포")
    st.plotly_chart(sou_gb, use_container_width=True)

with botright_column:
    df1 = df.groupby("연령")["val"].sum().reset_index()
    sou_age = ch.pie_simple(df1, values="val", names="연령", hole=.3, title="소유자 연령별 분포")
    st.plotly_chart(sou_age, use_container_width=True)

# (bot3 섹션은 원본이 주석이므로 유지하지 않음)

footer.render()
