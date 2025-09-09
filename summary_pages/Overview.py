import streamlit as st
import pandas as pd
import plotly.express as px
import warnings
warnings.filterwarnings('ignore')
import base64
from datetime import datetime,timedelta
from dateutil.relativedelta import *

st.set_page_config(page_title= "[카이즈유] 자동차 등록데이터", layout="wide", initial_sidebar_state="auto")
# df_bar = pd.read_csv('./data/simple_monthly_cnt.csv')
df = pd.read_csv('./data/202508monthly_cnt.csv', index_col=0)
# df_use = pd.read_csv('./data/12-24누적 용도별 등록대수.csv')

# 전년, 전월대비 계산
def cal(x,y):
    result = round((x-y)/y,2)
    return result

today = datetime.today()
month_ago = datetime(today.year, today.month, today.day) + relativedelta(months= -1)
year =  today.year
month = "{}".format(month_ago.strftime('%m'))

# 사이드바 메뉴 설정
with st.sidebar:
    st.write("CARISYOU DATALAB")
    st.link_button("CarCharts Free", "https://carcharts-free.carisyou.net/")


st.markdown(f"## Summary")
st.markdown(f"### {year}년 {month}월")
cal(df['NEW_CNT'][202508],df['NEW_CNT'][202507])
st.header('월간 승용차 등록 집계',help = '전월대비 증감')
#print(df['NEW_CNT'][20250801])
new, used, ersr, op = st.columns(4)
new.metric("신규 등록", format(df['NEW_CNT'][202508],','),f"{cal(df['NEW_CNT'][202508], df['NEW_CNT'][202507])}%",border = True)
used.metric("이전 등록", format(df['USED_CNT'][202508],','),f"{cal(df['USED_CNT'][202508], df['USED_CNT'][202507])}%",border = True)
ersr.metric("말소 등록", format(df['ERSR_CNT'][202508],','),f"{cal(df['ERSR_CNT'][202508], df['ERSR_CNT'][202507])}%",border = True)
op.metric("운행 등록", format(int(26434579),','),f"{cal(26434579, 26425398)}%",border = True)

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