import streamlit as st
import pandas as pd
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import folium
import streamlit.components.v1 as components


st.set_page_config(page_title= "New Regist Data", layout="wide", initial_sidebar_state="auto")
df = pd.read_csv('../데이터/data/22년신규등록데이터.csv')

st.sidebar.write(df)





heat_df = df[['위도', '경도']]
heat_data = [[row['위도'],row['경도']] for index, row in heat_df.iterrows()]
df3 = df.groupby(['USE_STRNGHLD_ADRES_NM', '위도', '경도']).count()
df3.reset_index(inplace=True)

st.title('CAR_REG Dashboard')
chart = st.selectbox("차트종류", ['bubble', 'heat'])
kr = folium.Map(location=[36, 128.5], zoom_start=7, tiles='openStreetMap')
if chart =='heat':
    HeatMap(heat_data).add_to(kr)
else :
    for i in range(0, len(df3)):
        latitude = df3.iloc[i]['위도']
        longitude = df3.iloc[i]['경도']
        location = (latitude, longitude)
        folium.CircleMarker(location, radius=df3.iloc[i]['AGE'] / 1000, color='#3186cc', fill_color='#3186cc',
                            popup=df3.iloc[i]['USE_STRNGHLD_ADRES_NM']).add_to(kr)

    folium.LayerControl(collapsed=False).add_to(kr)
st_data = st_folium(kr, width = 725)



left_column, right_column = st.columns([1.5,2.5])
with left_column:
    st.subheader('Dataset')
    st.dataframe(df)



# https://velog.io/@sirasony12/%EC%A7%80%EB%8F%84-%EC%8B%9C%EA%B0%81%ED%99%94 이거 지도 시각화임