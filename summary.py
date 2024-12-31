import webbrowser
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import warnings
warnings.filterwarnings('ignore')
from PIL import Image
from st_clickable_images import clickable_images
import base64
from pathlib import Path
import cx_Oracle
from datetime import datetime, timedelta
import calendar

os.putenv('NLS_LANG', '.UTF8')
try:
    cx_Oracle.init_oracle_client(lib_dir=r"C:\oracle\instantclient_21_3")
except:
    pass
connect = cx_Oracle.connect("CARREGISTDB", "pass", "192.168.0.114:1521/CARREGDB")
cursor = connect.cursor()

def st_button(url, label):
    st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">', unsafe_allow_html=True)
    button_code = f'''<a href="{url}" target=_blank 
    style = background-color: white;
        border-color : #ffffff;
        border-style:double;
        text-align: center;> {label}</a>'''

    return st.markdown(button_code, unsafe_allow_html=True)


st.set_page_config(page_title= "summary", layout="wide", initial_sidebar_state="auto")

df_bar = pd.read_sql("""select extract_de||'01' "date", count(*) CNT from CARCHART_PAID
                    where isa is null and reborn is null
                    and car_gb = '승용'
                    group by extract_de||'01'
                    order by 1 asc
                    """, con = connect)
df_bar['date'] = pd.to_datetime(df_bar['date'])
df = pd.read_csv('C:/Users/clmns/PycharmProjects/pythonProject1/carregdb/data/2023년 누적 데이터.csv', index_col=0)
df_use = pd.read_csv('C:/Users/clmns/PycharmProjects/pythonProject1/carregdb/data/12-23누적 용도별 등록대수.csv')

df['EXTRACT_DE'] = df['EXTRACT_DE'].astype('str')
reg = format(len(df), ',d')

start_date = datetime(2012, 1, 1)
end_date = datetime.now()
# start_date.strftime("%Y%m")
# end_date.strftime("%Y%m")

# 사이드바 메뉴 설정
with st.sidebar:
    # slider_range = st.sidebar.slider("날짜",min_value=start_date,max_value=end_date, value=(start_date, end_date),
    #                                  format="YYYYMM"
    # #step=timedelta(months=1)
    # )
    with st.sidebar.expander('Extract Date'):
        srt_year = st.selectbox("언제부터", list(range(2012,datetime.now().year+1,1)))
        month_abbr = calendar.month_abbr[1:]
        srt_mon = st.radio('시작월', month_abbr, horizontal=True)
        end_year = st.selectbox("언제까지", list(range(2012,datetime.now().year+1,1)))
        end_mon = st.radio('종료월', month_abbr, horizontal=True)


    select_multi_brand = st.sidebar.multiselect(
        '브랜드 선택(다중 선택 가능)',
        df['ORG_CAR_MAKER_KOR'].unique().tolist()
    )

    start_button = st.sidebar.button(
        "filter apply"  # "버튼에 표시될 내용"
    )
    st.write("CARISYOU DATALAB")

    CC = st.button("CarCharts_Free")
    if CC:
        webbrowser.open_new_tab("https://carcharts-free.carisyou.net/?utm_source=Carisyou&utm_medium=Banner&utm_campaign=P03_PC_Free&")

if month_abbr.index(srt_mon) + 1 < 10:
    srt_de = str(srt_year) + str(0) + str(month_abbr.index(srt_mon) + 1)
else:
    srt_de = str(srt_year) + str(month_abbr.index(srt_mon) + 1)

if month_abbr.index(end_mon) + 1 < 10:
    end_de = str(srt_year) + str(0) + str(month_abbr.index(end_mon) + 1)
else:
    end_de = str(srt_year) + str(month_abbr.index(end_mon) + 1)


if start_button:
    #slider input으로 받은 값에 해당하는 값을 기준으로 데이터를 필터링합니다.
    df2 = df[(df['EXTRACT_DE'] >= srt_de) & (df['EXTRACT_DE'] <= end_de) & (df['ORG_CAR_MAKER_KOR'].isin(select_multi_brand))]
    #st.table(tmp_df)
    # 성공문구 + 풍선이 날리는 특수효과
    st.sidebar.success("Filter Applied!")
    #st.balloons()
else :
    df2 = df[df["EXTRACT_DE"] == '20231201']

st.markdown("## 2024.12.03. Monthly Summary")
st.markdown(f"#### 2023년 누적 신규등록대수 : {reg}")

#left_column = st.columns(1, gap="large")
#right_column = st.columns(1, gap="large")
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

st.header('브랜드 모델별 신규등록대수')
brand = df['ORG_CAR_MAKER_KOR'].unique().tolist()
brand.sort()
name = st.selectbox("브랜드", brand)

date_mon = df['EXTRACT_DE'].unique().tolist()
date_mon.sort()
mon = st.selectbox("등록 월", date_mon)
df1 = df[(df['ORG_CAR_MAKER_KOR'] == name) & (df['EXTRACT_DE'] == mon)]
csv = df1.to_csv().encode('cp949')
st.download_button("현재 데이터 다운로드",data = csv, file_name='2023년 데이터.csv')
fig2 = px.histogram(df1, x="CAR_MOEL_DT", color = 'CAR_MOEL_DT')
st.plotly_chart(fig2, use_container_width=True)

with midleft_column:
    st.subheader('외형별 신규등록대수')

    # if not select_multi_species:
    #     df2 = df[df["EXTRACT_DE"] == '20231201']
    # else:
    #     df2 = df[df["ORG_CAR_MAKER_KOR"].isin(select_multi_species)]
    fig3 = px.histogram(df2, x="CAR_BT", color = 'CAR_BT')
    st.plotly_chart(fig3, use_container_width=True)


with midright_column:
    st.subheader('신규등록대수 연료비중')
    #df2 = df[df["EXTRACT_DE"] == '20231201']
    # if not select_multi_species:
    #     df3 = df[df["EXTRACT_DE"] == '20231201']
    # else:
    #     df3 = df[df["ORG_CAR_MAKER_KOR"].isin(select_multi_species)]
    df3 = df2.groupby("FUEL").count()
    df3.reset_index(inplace=True)
    fig4 = px.pie(df3, values = "EXTRACT_DE", names = "FUEL", hole=.3)
    st.plotly_chart(fig4, use_container_width=True)

with botleft_column:
    st.subheader('국산/수입별 신규등록대수')
    fig5 = px.histogram(df2, x="CL_HMMD_IMP_SE_NM", color = "CL_HMMD_IMP_SE_NM")
    st.plotly_chart(fig5, use_container_width=True)

with botright_column:
    st.subheader('외형별 연료별 신규등록대수 버블차트')
    df4 = df2.groupby(["FUEL", "CAR_BT"]).count()
    df4.reset_index(inplace=True)
    fig6 = px.scatter(df4, x="CAR_BT", y="FUEL", size="EXTRACT_DE", hover_name="EXTRACT_DE", size_max=60)
    st.plotly_chart(fig6, use_container_width=True)

#df5 = df[(df['EXTRACT_DE'] == 20231201) & (df['CL_HMMD_IMP_SE_NM'] == '국산')]
with bot2left:
    # df6 = pd.pivot_table(df5, values='ORG_CAR_MAKER_KOR', index='CAR_MOEL_DT',
    #                columns='CL_HMMD_IMP_SE_NM', aggfunc='count').sort_values(by='국산', ascending=False).head(10)
    st.subheader('국산 TOP 10')
    #st.dataframe(df2)

#df7 = df[(df['EXTRACT_DE'] == 20231201) & (df['CL_HMMD_IMP_SE_NM'] == '외산')]
with bot2right:
    # df8 = pd.pivot_table(df7, values='ORG_CAR_MAKER_KOR', index='CAR_MOEL_DT',
    #                columns='CL_HMMD_IMP_SE_NM', aggfunc='count').sort_values(by='국산', ascending=False).head(10)
    st.subheader('수입 TOP 10')
    #st.dataframe(df7)

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
    pre_use_df.index = [2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
    pre_use_df.reset_index(inplace=True)
    pre_use_df.rename(columns={'index': '연도'}, inplace=True)
    csv = pre_use_df.to_csv().encode('cp949')
    st.download_button("현재 데이터 다운로드", data=csv, file_name='연도별 용도 데이터.csv')
    # 그래프용 전처리
    numeric_df = pre_use_df.set_index('연도')
    rank_df = numeric_df.rank(axis=1, method='min', ascending=True)
    sort_fields = rank_df.loc[2012].sort_values().index
    # 범프 차트
    bump_fig = px.line(rank_df, x=rank_df.index, y=sort_fields,
                       title='연도별 분야별 지출 순위')
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
footer="""<style>
.footer {
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

}
</style>

<div class="footer">
<center> Copyright &copy; All rights reserved |  <a href="https://carcharts.carisyou.net/" target=_blank><img src='data:image/png;base64,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
' class='img-fluid' style = "width:75px; height:25px;"> </center>
</div>

"""


st.markdown(footer,unsafe_allow_html=True)

# import pandas as pd
# df = pd.read_csv('C:/Users/clmns/PycharmProjects/pythonProject1/carregdb/data/2023년 누적 데이터.csv', index_col=0)
# df5 = df[(df['EXTRACT_DE'] == 20231201) & (df['CL_HMMD_IMP_SE_NM'] == '국산')]
# print(df5)

# streamlit run summary.py
# https://data-science-at-swast-handover-poc-handover-yfa2kz.streamlit.app/
# 위에 이거 함 드가서 코드 훔쳐오자