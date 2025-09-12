# app_core/footer.py
import base64
from pathlib import Path
import streamlit as st

ASSET = Path("./assets/carcharts.png")
LINK = "https://carcharts.carisyou.net/"
COPY = "© 2023. SJAhn. All rights reserved."

def _b64(p: Path) -> str:
    try:
        return base64.b64encode(p.read_bytes()).decode()
    except Exception:
        return ""

def render():
    logo = _b64(ASSET)
    html = f"""
    <style>
    .footer {{
        position: fixed; left:0; bottom:0; width:100%; height:30px;
        background-color:white; color:black;
        border-width:5px; border-color:gray white white white;
        border-style:double none none none; text-align:center; z-index:999;
    }}
    .footer img {{ width:75px; height:25px; vertical-align:middle; }}
    </style>
    <div class="footer">
      <center>
        {COPY} |
        <a href="{LINK}" target="_blank">
          {"<img src='data:image/png;base64," + logo + "' class='img-fluid' />" if logo else "CarCharts"}
        </a>
      </center>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
