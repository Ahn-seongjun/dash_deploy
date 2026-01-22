# app_core/ui.py
from __future__ import annotations
import streamlit as st

def apply_tab_style():
    """탭 시각 스타일 공통 적용 (Overview에서 쓰던 CSS 그대로)."""
    st.markdown(
        """
        <style>
        .stTabs [role="tablist"] { gap: 6px; }

        .stTabs [data-baseweb="tab"],
        .stTabs [data-baseweb="tab"] > div,
        .stTabs [data-baseweb="tab"] p,
        .stTabs button[role="tab"] {
            font-size: 18px !important;
            font-weight: 700 !important;
            font-family: 'Arial', sans-serif !important;
            color: #333333 !important;
            padding: 8px 14px !important;
        }

        .stTabs [data-baseweb="tab"][aria-selected="true"],
        .stTabs button[role="tab"][aria-selected="true"] {
            color: #ffffff !important;
            background-color: #dce5f8 !important;
            border-radius: 8px 8px 0 0 !important;
        }

        .stTabs [data-baseweb="tab"]:hover,
        .stTabs button[role="tab"]:hover {
            background-color: #dce5f8 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def sidebar_links():
    """사이드바 하단 공통 링크 영역."""
    st.write("CARISYOU DATALAB")
    st.link_button("CarCharts Free", "https://carcharts-free.carisyou.net/")

def sidebar_filters_applied():
    """필터 적용시 공통 피드백(선택 사용)."""
    st.success("Filter Applied!")
    #st.balloons()
