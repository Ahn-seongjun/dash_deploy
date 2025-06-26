import altair as alt
import pandas as pd
import streamlit as st


# 페이지 제목이랑 설명
st.set_page_config(page_title="[카이즈유] 최초등록연도 집계")#, page_icon="🎬")
with st.sidebar:
    st.write("CARISYOU DATALAB")
    st.link_button("CarCharts Free","https://carcharts-free.carisyou.net/")

st.title("말소데이터 최초등록연도별 단순집계")
st.write(
    """
    This app visualizes data from [The Movie Database (TMDB)](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata).
    It shows which movie genre performed best at the box office over the years. Just 
    click on the widgets below to explore!
    """
)



@st.cache_data
def load_data():
    df = pd.read_csv("data/CL 전처리 데이터.csv")
    return df


df = load_data()

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