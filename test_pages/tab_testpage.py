import streamlit as st
import extra_streamlit_components as stx
import warnings
warnings.filterwarnings('ignore')
import base64
import pandas as pd


st.set_page_config(page_title= "[테스트] 탭 테스트 페이지", layout="wide", initial_sidebar_state="auto")

st.markdown("## 내구성 분석")
listTabs = ['시대별 TOP 5','국산/수입 TOP 5','차급 TOP 5','연료 TOP 5','외형 TOP 5']
whitespace = 5
tab1, tab2, tab3, tab4, tab5 = st.tabs([s.center(whitespace,"\u2001") for s in listTabs])

tabs_font_css = """
<style>
button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
  font-size: 24px;
}
</style>
"""
era = ['~ 1999','2000 ~ 2004', '2005 ~ 2009', '2010 ~ 2014']
temp = [['~ 1999','aa'],['2000 ~ 2004','bb'],['2005 ~ 2009','cc'],['2010 ~ 2014','dd']]
df =pd.DataFrame(temp, columns=['시대','구분'])
with tab1:
    sele_era = st.selectbox("시대", era)
    df1 = df[df['시대'] ==sele_era]
    st.dataframe(df1, use_container_width=True)



st.write(tabs_font_css, unsafe_allow_html=True)

# 사이드바 메뉴 설정
with st.sidebar:
    st.write("CARISYOU DATALAB")
    st.link_button("CarCharts Free", "https://carcharts-free.carisyou.net/")



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