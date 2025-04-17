import streamlit as st
import pandas as pd
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import folium
import base64
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title= "[카이즈유] 자동차 등록데이터", layout="wide", initial_sidebar_state="auto")


ci_data = pd.read_csv('./data/CI 전처리 데이터.csv')
st.markdown("# 승용차 내구성 분석")
# 사이드바 메뉴 설정
with st.sidebar:

    st.write("CARISYOU DATALAB")
    st.link_button("CarCharts Free", "https://carcharts-free.carisyou.net/")


#st.header('승용차 내구성 분석')
st.markdown("## 승용차 주행거리 기준 내구성 분석")
st.markdown("- 집계 기간 : 2024년 1월 ~ 12월")
st.markdown("- 집계 대상 : 승용(자가용), 말소등록데이터 자진말소(폐차)")
st.markdown("- 제외 대상 : 주행거리 0, null, 100만 이상")
st.markdown("- 대이터 수 : 580,433")
tab1, tab2 = st.tabs(['컨슈머인사이트','CLM&S'])
with tab1:
    st.markdown("- 분석 방법 : 지정기간 브랜드/모델별 말소 대수 집계")
    st.markdown("- 분석 범위 : 최초등록연도 기준 2010년 ~ 2015년")
    st.markdown("- 전처리 후 데이터 수 : 165,055")
    left1, right1 = st.columns([2, 2], gap="large")
    with left1:
        ci_dist = px.histogram(ci_data, x="TRVL_DSTNC", nbins=100, title='전처리 후 주행거리 분포(CI)', color_discrete_sequence=['#00dac4'])
        ci_dist.update_layout(xaxis_title_text='주행거리')
        st.plotly_chart(ci_dist, use_container_width=True)
    with right1:
        ci_year = px.histogram(ci_data, x="FRST_YYYY",
                           category_orders=dict(FRST_YYYY=["2010", "2011", "2012", "2013", "2014", "2015"]),
                           title='최초등록 연도별 말소대수', color_discrete_sequence=['#00dac4'])
        ci_year.update_layout(xaxis_title_text='최초등록연도')
        ci_year.update_layout(bargap=0.2)
        st.plotly_chart(ci_year, use_container_width=True)
    left2, right2 = st.columns([2, 2], gap="large")
    with left2:
        fuel_box = px.box(ci_data, x="FUEL", y="TRVL_DSTNC", color="FUEL",
                          title='연료별 주행거리 Boxplot')
        fuel_box.update_traces(quartilemethod="exclusive")
        st.plotly_chart(fuel_box, use_container_width=True)
    with right2:
        bt_box = px.box(ci_data, x="CAR_BT", y="TRVL_DSTNC", color="CAR_BT",
                     title='외형별 주행거리 Boxplot')
        bt_box.update_traces(quartilemethod="exclusive")
        st.plotly_chart(bt_box, use_container_width=True)
    left3, right3 = st.columns([2, 2], gap="large")
    with left3:
        gb = ci_data.groupby('FRST_YYYY')[['TRVL_DSTNC']].mean()
        mean_bar = px.bar(gb, x=gb.index, y='TRVL_DSTNC', title='최초등록연도별 평균 주행거리', color="TRVL_DSTNC")
        st.plotly_chart(mean_bar, use_container_width=True)
    with right3:
        pivot_data = ci_data.pivot_table(index='CAR_BT',
                                        columns='FUEL',
                                        values='TRVL_DSTNC',
                                        aggfunc='mean'
        )
        pivo = px.imshow(pivot_data,
                        text_auto=True,
                        color_continuous_scale='Inferno',
                        labels=dict(x="연료", y="외형", color="평균 주행거리(km)"),
                        title="외형 x 연료 조합별 평균 주행거리"
        )

        pivo.update_layout(
            xaxis_title="연료",
            yaxis_title="외형",
            autosize=False,
            width=600,
            height=600
        )
        st.plotly_chart(pivo, use_container_width=True)

    # 상위 20개 제조사만 필터링
    top20_makers = ci_data['ORG_CAR_MAKER_KOR'].value_counts().head(20)#.index
    filtered_df = ci_data[ci_data['ORG_CAR_MAKER_KOR'].isin(top20_makers.index)]
    grouped = filtered_df.groupby(['ORG_CAR_MAKER_KOR', 'CAR_BT', 'FUEL'])['TRVL_DSTNC'].mean().reset_index()

    # 버블 크기를 조정할 수 있도록 정규화
    grouped['버블크기'] = grouped['TRVL_DSTNC'] / grouped['TRVL_DSTNC'].max() * 40  # 버블 최대크기 조정

    # 3D Scatter plot 생성
    plot3d = go.Figure(data=[go.Scatter3d(
        x=grouped['ORG_CAR_MAKER_KOR'],
        y=grouped['CAR_BT'],
        z=grouped['FUEL'],
        mode='markers',
        marker=dict(
            size=grouped['버블크기'],
            color=grouped['TRVL_DSTNC'],
            colorscale='Viridis',
            colorbar=dict(title='평균 주행거리(km)'),
            opacity=0.8
        ),
        text=grouped.apply(lambda
                               row: f"제조사: {row['ORG_CAR_MAKER_KOR']}<br>외형: {row['CAR_BT']}<br>연료: {row['FUEL']}<br>평균주행거리: {row['TRVL_DSTNC']:.0f}km",
                           axis=1),
        hoverinfo='text'
    )])

    plot3d.update_layout(
        scene=dict(
            xaxis_title='제조사',
            yaxis_title='외형',
            zaxis_title='연료'
        ),
        title='TOP 20 제조사 x 외형 x 연료별 평균 폐차 주행거리 (3D 시각화)',
        height=700
    )
    st.plotly_chart(plot3d, use_container_width=True)
    st.markdown("#### 말소 대수 상위 20개 브랜드 리스트")
    col_config = {"브랜드": "말소 대수"}
    st.dataframe(top20_makers, column_config=col_config, width=400)
with tab2:
    st.markdown("- 분석 방법 : 구간별 브랜드/모델별 말소 대수 집계")
    st.markdown("- 분석 범위 : 최초등록연도 기준 구간 집계\n"
                "   * ~ 1999년\n"
                "   * 2000년 ~ 2004년\n"
                "   * 2005년 ~ 2009년\n"
                "   * 2010년 ~ 2014년\n")
    st.markdown("- 전처리 후 데이터 수 : 536,328")

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

# https://velog.io/@sirasony12/%EC%A7%80%EB%8F%84-%EC%8B%9C%EA%B0%81%ED%99%94 이거 지도 시각화임