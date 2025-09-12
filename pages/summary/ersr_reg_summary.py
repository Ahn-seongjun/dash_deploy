import streamlit as st
import pandas as pd
import plotly.express as px
import warnings
warnings.filterwarnings('ignore')
import base64
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

@st.cache_data(ttl=3600, show_spinner="말소등록 데이터 불러오는 중...")
def load_csv(path: Path, dtype=None, parse_dates=None):
    return pd.read_csv(path, dtype=dtype, parse_dates=parse_dates)

@st.cache_data(ttl=3600)
def get_ersr_data(base_dir="data/ersr"):
    base = Path(base_dir)
    df = load_csv(base / "2024년 말소데이터.csv")
    return {
        "monthly": df,
    }

# --- 스트림릿 UI 시작 ---
st.set_page_config(page_title="말소 등록 요약", page_icon="🗑️", layout="wide")
st.title("말소 등록 요약")

data = get_ersr_data(base_dir="data")
df   = data["monthly"]



# st.set_page_config(page_title= "[카이즈유] 자동차 등록데이터", layout="wide", initial_sidebar_state="auto")
#
# df = pd.read_csv('./data/2024년 말소데이터.csv')
df['val'] = '1'
df['val'] = df['val'].astype('int')
df['EXTRACT_DE'] = df['EXTRACT_DE'].astype('str')
df['EXTRACT_DE'] = pd.to_datetime(df['EXTRACT_DE'])
# 단순 대수 전처리
reg = format(len(df), ',d')


# 사이드바 메뉴 설정
with st.sidebar:
    st.write("CARISYOU DATALAB")
    st.link_button("CarCharts Free", "https://carcharts-free.carisyou.net/")


st.markdown("## 2024 Yearly Summary")
st.markdown(f"### 2024년 자진말소(폐차) 등록대수 : {reg}")
st.markdown("- 승용차 대상 집계")
st.markdown('- 말소 등록 : 자진말소(폐차)')
st.markdown('----')
st.subheader('연료별 말소 대수 및 증감률')
fuel = st.selectbox("연료", df['연료'].unique().tolist())
# 월별 등록대수 및 증감률 전처리 및 그래프
er_pivo = pd.pivot_table(df,
              index = 'EXTRACT_DE',
              columns = '연료',
              values = 'val',
              aggfunc = 'sum')

er_pivo[f'{fuel}-1년'] = er_pivo[fuel].shift(1)
er_pivo[f'{fuel}_증감'] = ((er_pivo[fuel]-er_pivo[f'{fuel}-1년'])/er_pivo[f'{fuel}-1년'])*100


# 이중 Y축 그래프 만들기
mon_reg = make_subplots(specs=[[{"secondary_y": True}]])

# 첫 번째 Y축: 바 차트 (말소대수)
# Bar: 말소대수
mon_reg.add_trace(
    go.Bar(
        x=er_pivo.index,
        y=er_pivo[fuel],
        name=f'{fuel} 말소대수',
        marker_color='lightblue',
        hovertemplate='%{x}<extra></extra><br>%{y:,.0f}대'
    ),
    secondary_y=False,
)

# 두 번째 Y축: 선 그래프 (전년대비 증감률)
mon_reg.add_trace(
    go.Scatter(
        x=er_pivo.index,
        y=er_pivo[f'{fuel}_증감'],
        name='전월대비 증감률(%)',
        mode='lines+markers',
        line=dict(dash='dash', color='red'),
        marker=dict(size=10),
        hovertemplate='%{x}<extra></extra><br>%{y}%'
    ),
    secondary_y=True,
)

# 레이아웃 설정
mon_reg.update_layout(
    xaxis_title='2024년',
    yaxis_title='말소대수',
    legend=dict(x=0.01, y=0.99),
    template='plotly_white'

)

mon_reg.update_yaxes(title_text='말소대수', secondary_y=False)
mon_reg.update_yaxes(title_text='증감률(%)', secondary_y=True)

st.plotly_chart(mon_reg, use_container_width=True)

midleft_column, midright_column = st.columns([2,2], gap="large")
botleft_column, botright_column = st.columns(2, gap="large")
bot2left, bot2right = st.columns(2, gap="large")
bot3le,bot3ri = st.columns(2, gap="large")


with midleft_column:
    st.subheader('국산 말소대수 TOP 10')
    brand_na = df[df['CL_HMMD_IMP_SE_NM']=='국산'].groupby('ORG_CAR_MAKER_KOR')[['val']].sum().sort_values(by='val', ascending=False).head(10).reset_index()
    br_na = px.bar(brand_na, x="val", y="ORG_CAR_MAKER_KOR", color='ORG_CAR_MAKER_KOR', orientation='h',
                 hover_data=["ORG_CAR_MAKER_KOR", "val"],
                 height=600,
                 title='국산 브랜드별 말소 대수 TOP 10')
    br_na.update_layout(
        xaxis_title='대수',
        yaxis_title='브랜드',
        legend_title_text = '브랜드',
        template='plotly_white'

    )
    st.plotly_chart(br_na, use_container_width=True)

    mo_na_cnt = df[df['CL_HMMD_IMP_SE_NM'] == '국산'].groupby('CAR_MOEL_DT')[['val']].sum().sort_values(by='val',
                                                                                                      ascending=False).head(
        10).reset_index()
    mo_na = px.bar(mo_na_cnt, x="val", y="CAR_MOEL_DT", color='CAR_MOEL_DT', orientation='h',
                   hover_data=["CAR_MOEL_DT", "val"],
                   height=600,
                   title='국산 모델별 말소 대수 TOP 10')
    mo_na.update_layout(
        xaxis_title='대수',
        yaxis_title='모델',
        legend_title_text = '모델',
        template='plotly_white'

    )
    st.plotly_chart(mo_na, use_container_width=True)
with midright_column:
    st.subheader('수입 말소대수 TOP 10')
    brand_im = df[df['CL_HMMD_IMP_SE_NM']=='외산'].groupby('ORG_CAR_MAKER_KOR')[['val']].sum().sort_values(by='val', ascending=False).head(10).reset_index()
    br_im = px.bar(brand_im, x="val", y="ORG_CAR_MAKER_KOR", color='ORG_CAR_MAKER_KOR', orientation='h',
                 hover_data=["ORG_CAR_MAKER_KOR", "val"],
                 height=600,
                 title='수입 브랜드별 말소 대수 TOP 10')
    br_im.update_layout(
        xaxis_title='대수',
        yaxis_title='브랜드',
        legend_title_text = '브랜드',
        template='plotly_white'

    )
    st.plotly_chart(br_im, use_container_width=True)

    mo_im_cnt = df[df['CL_HMMD_IMP_SE_NM'] == '외산'].groupby('CAR_MOEL_DT')[['val']].sum().sort_values(by='val',
                                                                                                      ascending=False).head(
        10).reset_index()
    mo_im = px.bar(mo_im_cnt, x="val", y="CAR_MOEL_DT", color='CAR_MOEL_DT', orientation='h',
                   hover_data=["CAR_MOEL_DT", "val"],
                   height=600,
                   title='수입 모델별 말소 대수 TOP 10')
    mo_im.update_layout(
        xaxis_title='대수',
        yaxis_title='모델',
        legend_title_text = '모델',
        template='plotly_white'

    )
    st.plotly_chart(mo_im, use_container_width=True)

with botleft_column:
    sou_gb = px.sunburst(df, path=['소유자유형', '성별', '연령'], values='val', color='성별', title= '소유자 유형별 분포')
    st.plotly_chart(sou_gb, use_container_width=True)

with botright_column:
    df1 = df.groupby('연령')['val'].sum().reset_index()
    sou_age = px.pie(df1, values="val", names="연령", hole=.3,title="소유자 연령별 분포")
    st.plotly_chart(sou_age, use_container_width=True)

# with bot3le:
#
# with bot3ri:







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