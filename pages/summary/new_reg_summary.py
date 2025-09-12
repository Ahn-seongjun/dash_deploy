import streamlit as st
import pandas as pd
import plotly.express as px
import warnings
warnings.filterwarnings('ignore')
import base64
from pathlib import Path

# 파일 → DataFrame 캐시 (1시간)
@st.cache_data(ttl=3600, show_spinner="신규등록 데이터 불러오는 중...")
def load_csv(path: Path, dtype=None, parse_dates=None):
    return pd.read_csv(path, dtype=dtype, parse_dates=parse_dates)

@st.cache_data(ttl=3600)
def get_newreg_data(base_dir="data/new_reg"):
    base = Path(base_dir)
    df_monthly = load_csv(base / "simple_monthly_cnt.csv")
    df_cum     = load_csv(base / "12-24누적 용도별 등록대수.csv")
    df_dim     = load_csv(base / "2024년 누적 데이터.csv")

    return {
        "monthly": df_monthly,
        "cum": df_cum,
        "dim": df_dim,
    }

# --- 스트림릿 UI 시작 ---
st.set_page_config(page_title="신규 등록 요약", page_icon="🚗", layout="wide")
st.title("신규 등록 요약")
data = get_newreg_data(base_dir="data/")  # <- 프로젝트 구조에 맞게 경로 조정
df_bar = data["monthly"]
df_use     = data["cum"]
df     = data["dim"]
# st.set_page_config(page_title= "[카이즈유] 자동차 등록데이터", layout="wide", initial_sidebar_state="auto")
# df_bar = pd.read_csv('./data/simple_monthly_cnt.csv', index_col=0)
# df = pd.read_csv('./data/2024년 누적 데이터.csv', index_col=0)
# df_use = pd.read_csv('./data/12-24누적 용도별 등록대수.csv')
#print(df_bar)
# 단순 대수 전처리
df_bar = df_bar.reset_index()
df_bar['date'] = df_bar['date'].astype('str')
df_bar['date'] = pd.to_datetime(df_bar['date'])

df['EXTRACT_DE'] = df['EXTRACT_DE'].astype('str')
reg = format(df['CNT'].sum(), ',d')


# 사이드바 메뉴 설정
with st.sidebar:
    select_multi_brand = st.sidebar.multiselect(
        '브랜드 선택(다중 선택 가능)',
        df['ORG_CAR_MAKER_KOR'].unique().tolist()
    )

    start_button = st.sidebar.button(
        "filter apply"  # "버튼에 표시될 내용"
    )

    df2 = df
    if start_button:
        if not select_multi_brand:
            df2 = df
        else:
            df2 = df[df['ORG_CAR_MAKER_KOR'].isin(select_multi_brand)]


        st.sidebar.success("Filter Applied!")
        st.balloons()

    st.write("CARISYOU DATALAB")
    st.link_button("CarCharts Free", "https://carcharts-free.carisyou.net/")


st.markdown("## 2024 Yearly Summary")
st.markdown(f"#### 2024년 누적 신규등록대수 : {reg}")


st.header('월별 누적 신규등록대수')
tab1, tab2 = st.tabs(['bar','line'])

midleft_column, midright_column = st.columns([2,2], gap="large")
botleft_column, botright_column = st.columns(2, gap="large")
bot2left, bot2right = st.columns(2, gap="large")
bot3le,bot3ri = st.columns(2, gap="large")

#with left_column:
with tab1:
    fig1 = px.bar(df_bar, x='date', y='CNT',
             hover_data=['date', 'CNT'], color='CNT',
             labels={'date':'등록날짜', 'CNT':'등록대수'}, height=400).update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    fig1_1 = px.line(df_bar, x='date', y='CNT').update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )

    st.plotly_chart(fig1_1, use_container_width=True)
#with right_column:



with midleft_column:
    st.subheader('외형별 신규등록대수')

    hist = df2.groupby(['CAR_BT'])['CNT'].sum().reset_index().sort_values(by = 'CNT',ascending = False)
    fig3 = px.bar(hist, x='CAR_BT', y = 'CNT', color = 'CAR_BT',labels=dict(CAR_BT="외형", CNT="대수"))
    st.plotly_chart(fig3, use_container_width=True)


with midright_column:
    st.subheader('신규등록대수 연료비중')
    #df2 = df[df["EXTRACT_DE"] == '20231201']
    # if not select_multi_species:
    #     df3 = df[df["EXTRACT_DE"] == '20231201']
    # else:
    #     df3 = df[df["ORG_CAR_MAKER_KOR"].isin(select_multi_species)]
    df3 = df2.groupby(['FUEL'])['CNT'].sum().reset_index()
    fig4 = px.pie(df3, values = "CNT", names = "FUEL", hole=.3)
    st.plotly_chart(fig4, use_container_width=True)

with botleft_column:
    st.subheader('국산/수입별 신규등록대수')
    df_tmp = df2.groupby(['CL_HMMD_IMP_SE_NM'])['CNT'].sum().reset_index()
    fig5 = px.bar(df_tmp, x="CL_HMMD_IMP_SE_NM", y= 'CNT', color = "CL_HMMD_IMP_SE_NM",labels=dict(CL_HMMD_IMP_SE_NM="국산/수입", CNT="대수"))
    st.plotly_chart(fig5, use_container_width=True)

with botright_column:
    st.subheader('외형별 연료별 신규등록대수 버블차트')
    df4 = df2.groupby(["FUEL", "CAR_BT"])['CNT'].sum().reset_index()
    fig6 = px.scatter(df4, x="CAR_BT", y="FUEL", size="CNT", hover_name="CNT", size_max=60,labels=dict(CAR_BT="외형", FUEL="연료"))
    st.plotly_chart(fig6, use_container_width=True)

with bot2left:
    st.subheader('월별 소유자 유형별 신차등록대수')
    df_own=df2.groupby(['EXTRACT_DE', 'OWNER_GB'])[['CNT']].sum().reset_index()
    df_own['EXTRACT_DE'] = df_own['EXTRACT_DE'].astype('str')
    df_own['EXTRACT_DE'] = pd.to_datetime(df_own['EXTRACT_DE'])
    #st.dataframe(df_own.info())
    #print(df_own)
    fig_own = px.bar(df_own, x='EXTRACT_DE', y = 'CNT', color = 'OWNER_GB',labels=dict(EXTRACT_DE="2024년", CNT="대수"))
    st.plotly_chart(fig_own, use_container_width=True)

with bot2right:
    st.subheader('연령별 신차등록 비중')
    df_age = df.groupby(['AGE'])[['CNT']].sum().reset_index()
    age_order = ['20대', '30대', '40대', '50대', '60대', '70대', '법인및사업자']
    fig_age = px.pie(df_age, values="CNT", names="AGE", hole=.3, category_orders={'AGE': age_order})
    st.plotly_chart(fig_age, use_container_width=True)

with bot3le:
    st.subheader('연도별 용도별 신규등록대수')
    use = df_use['CAR_USE'].unique().tolist()
    #use.sort()
    name = st.selectbox("용도", use)
    sele_use_df = df_use[df_use['CAR_USE'] == name]
    # 기본 전처리
    pre_use_df = sele_use_df.iloc[:, 1:].transpose()
    pre_use_df.rename(columns=pre_use_df.iloc[0], inplace=True)
    pre_use_df = pre_use_df.drop(pre_use_df.index[0])
    pre_use_df.index = [2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
    pre_use_df.reset_index(inplace=True)
    pre_use_df.rename(columns={'index': '연도'}, inplace=True)
    csv = pre_use_df.to_csv().encode('cp949')
    #st.download_button("현재 데이터 다운로드", data=csv, file_name='연도별 용도 데이터.csv')
    # 그래프용 전처리
    numeric_df = pre_use_df.set_index('연도')
    rank_df = numeric_df.rank(axis=1, method='min', ascending=True)
    sort_fields = rank_df.loc[2012].sort_values().index
    # 범프 차트
    bump_fig = px.line(rank_df, x=rank_df.index, y=sort_fields)
    # 트레이스 별로 hovertemplate 설정
    for trace in bump_fig.data:
        trace.hovertemplate = '%{x}<br>등록대수: ' + \
                              numeric_df[trace.name].astype(str)
    # 그래프 레이아웃 및 트레이스 설정
    bump_fig.update_layout(
        xaxis_title='연도',
        #yaxis_title='용도',
        #yaxis_ticktext=sort_fields,
        yaxis_tickvals=list(range(1, len(sort_fields) + 1)),
        hovermode='x',
        width=600,
        height=600
    ).update_traces(mode='lines+markers', marker_size=10)

    st.plotly_chart(bump_fig, use_container_width=True)

with bot3ri:
    st.subheader('브랜드 모델별 신규등록대수')
    brand = df['ORG_CAR_MAKER_KOR'].unique().tolist()
    brand.sort()
    name = st.selectbox("브랜드", brand)

    date_mon = df['EXTRACT_DE'].unique().tolist()
    date_mon.sort()
    mon = st.selectbox("등록 월", date_mon)
    df1 = df[(df['ORG_CAR_MAKER_KOR'] == name) & (df['EXTRACT_DE'] == mon)]
    csv = df1.to_csv().encode('cp949')
    #st.download_button("현재 데이터 다운로드",data = csv, file_name=f'{mon[:-2]} 신규등록데이터.csv')
    df1 = df1.groupby(["CAR_MOEL_DT"])['CNT'].sum().reset_index().sort_values(by='CNT', ascending = False)
    fig2 = px.bar(df1, x='CAR_MOEL_DT', y = 'CNT', color = 'CAR_MOEL_DT',labels=dict(CAR_MOEL_DT="모델", CNT="대수"))
    st.plotly_chart(fig2, use_container_width=True)


with open('./assets/carcharts.png', "rb") as f:
    data = f.read()


footer=f"""<style>
.footer {{
position: fixed;
left: 0;
bottom: 0;
width: 100%;
height : 30px;
background-color: white;
color: black;
border-width : 5px;
border-color : gray white white white;
border-style:double none none none;
text-align: center;

}}
</style>

<div class="footer">
<center> &copy; 2023. SJAhn. All rights reserved. |  <a href="https://carcharts.carisyou.net/" target=_blank><img src="data:image/png;base64,{base64.b64encode(data).decode()}" class='img-fluid' style = "width:75px; height:25px;"> </center>
</div>

"""

st.markdown(footer,unsafe_allow_html=True)

# streamlit run summary.py
# https://data-science-at-swast-handover-poc-handover-yfa2kz.streamlit.app/
# 위에 이거 함 드가서 코드 훔쳐오자