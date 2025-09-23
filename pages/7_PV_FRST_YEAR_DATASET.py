import altair as alt
import pandas as pd
import streamlit as st
from app_core import footer
from app_core import ui
from nav import render_sidebar_nav
st.set_page_config(page_title="승용말소 데이터셋", layout="wide")
render_sidebar_nav()
# 로그인 안하면 바로 로그인페이지로
if not st.session_state.get("logged_in", False):
    st.switch_page("pages/10_Log_in.py")
# 사이드바
with st.sidebar:
    ui.sidebar_links()

st.title("최초등록연도별 브랜드 말소대수")

@st.cache_data
def load_data():
    df = pd.read_csv("data/CL 전처리 데이터.csv")
    df1 = pd.read_csv("data/CI 전처리 데이터.csv")
    return df, df1

tab1, tab2 = st.tabs(['CL','CI'])
df, df1 = load_data()

with tab1:
    # 브랜드 선택 멀티셀렉트
    Brand = st.multiselect(
        "Brand",
        df.ORG_CAR_MAKER_KOR.unique(),
        ["랜드로버", "렉서스", "BMW", "벤츠", "폭스바겐"],
    )

    # 연도조절 슬라이더
    years = st.slider("Years", 1985, 2014, (2000, 2010))

    # 필터링
    df_filtered = df[(df["ORG_CAR_MAKER_KOR"].isin(Brand)) & (df["FRST_YYYY"].between(years[0], years[1]))]
    df_reshaped = df_filtered.pivot_table(
        index="FRST_YYYY", columns="ORG_CAR_MAKER_KOR", values="CAR_BT", aggfunc="count", fill_value=0
    )
    df_reshaped = df_reshaped.sort_values(by="FRST_YYYY", ascending=False)


    # 데이터프레임
    st.dataframe(
        df_reshaped,
        use_container_width=True,
        column_config={"FRST_YYYY": st.column_config.TextColumn("Year")},
    )

    # altair 차트
    df_chart = pd.melt(
        df_reshaped.reset_index(), id_vars="FRST_YYYY", var_name="Brand", value_name="CNT"
    )
    chart = (
        alt.Chart(df_chart)
        .mark_line()
        .encode(
            x=alt.X("FRST_YYYY:N", title="Year"),
            y=alt.Y("CNT:Q", title="말소 대수"),
            color="Brand:N",
        )
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)

with tab2:
    # 브랜드 선택 멀티셀렉트
    Brand = st.multiselect(
        "Brand",
        df1.ORG_CAR_MAKER_KOR.unique(),
        ["랜드로버", "BMW", "볼보", "현대", "폭스바겐"],
    )

    # 연도조절 슬라이더
    years = st.slider("Years", 2010, 2014, (2010, 2014))

    # 필터링
    df_filtered1 = df1[(df1["ORG_CAR_MAKER_KOR"].isin(Brand)) & (df1["FRST_YYYY"].between(years[0], years[1]))]
    df_reshaped1 = df_filtered1.pivot_table(
        index="FRST_YYYY", columns="ORG_CAR_MAKER_KOR", values="CAR_BT", aggfunc="count", fill_value=0
    )
    df_reshaped1 = df_reshaped1.sort_values(by="FRST_YYYY", ascending=False)


    # 데이터프레임
    st.dataframe(
        df_reshaped1,
        use_container_width=True,
        column_config={"FRST_YYYY": st.column_config.TextColumn("Year")},
    )

    # altair 차트
    df_chart1 = pd.melt(
        df_reshaped1.reset_index(), id_vars="FRST_YYYY", var_name="Brand", value_name="CNT"
    )
    chart1 = (
        alt.Chart(df_chart1)
        .mark_line()
        .encode(
            x=alt.X("FRST_YYYY:N", title="최초등록연도"),
            y=alt.Y("CNT:Q", title="말소 대수"),
            color="Brand:N",
        )
        .properties(height=320)
    )
    st.altair_chart(chart1, use_container_width=True)

footer.render()