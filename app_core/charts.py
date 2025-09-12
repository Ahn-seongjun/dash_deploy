from typing import Optional
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from .constants import CHART_DEFAULTS

def _apply_layout(fig: go.Figure, title: Optional[str] = None, height: Optional[int] = None):
    fig.update_layout(
        title=title or "",
        template=CHART_DEFAULTS.template,
        height=height or CHART_DEFAULTS.height,
        margin=CHART_DEFAULTS.margin,
        legend=dict(orientation="h", y=1.07),
    )
    return fig

def render_monthly_dual_axis(
    df: pd.DataFrame,
    x: str,
    y_left: str,
    y_right: str,
    title: str,
    y_left_name: str = "대수",
    y_right_name: str = "증감률",
    height: Optional[int] = None,
):
    fig = go.Figure()
    fig.add_bar(x=df[x], y=df[y_left], name=y_left_name, yaxis="y1")
    fig.add_trace(go.Scatter(x=df[x], y=df[y_right], name=y_right_name, yaxis="y2", mode="lines+markers"))
    fig.update_layout(
        xaxis=dict(domain=[0.1, 0.9]),
        yaxis=dict(title=y_left_name),
        yaxis2=dict(title=y_right_name, overlaying="y", side="right", tickformat=".1%", rangemode="tozero"),
    )
    _apply_layout(fig, title, height)
    st.plotly_chart(fig, use_container_width=True)

def render_pie_share(df: pd.DataFrame, labels: str, values: str, title: str, height: Optional[int] = None):
    fig = go.Figure(data=[go.Pie(labels=df[labels], values=df[values], hole=0.5)])
    _apply_layout(fig, title, height)
    st.plotly_chart(fig, use_container_width=True)

def render_area_share(df: pd.DataFrame, x: str, y: str, group: str, title: str, height: Optional[int] = None):
    # 누적 영역: 그룹별 점유율(%) 시계열
    fig = go.Figure()
    for g, sub in df.groupby(group):
        fig.add_trace(go.Scatter(x=sub[x], y=sub[y], stackgroup="one", name=str(g), mode="none"))
    fig.update_yaxes(tickformat=".1%")
    _apply_layout(fig, title, height)
    st.plotly_chart(fig, use_container_width=True)

def render_top_bottom_bar(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    n: int = 10,
    ascending: bool = False,
    title: Optional[str] = None,
    percent: bool = False,
    height: Optional[int] = None,
):
    tmp = df.sort_values(value_col, ascending=ascending).head(n)
    fig = go.Figure(go.Bar(x=tmp[value_col], y=tmp[group_col], orientation="h"))
    if percent:
        fig.update_xaxes(tickformat=".1%")
    _apply_layout(fig, title, height)
    st.plotly_chart(fig, use_container_width=True)

def render_distribution_bar(df: pd.DataFrame, x: str, y: str, title: str, height: Optional[int] = None):
    fig = go.Figure(go.Bar(x=df[x], y=df[y]))
    _apply_layout(fig, title, height)
    st.plotly_chart(fig, use_container_width=True)