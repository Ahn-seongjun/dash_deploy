
from __future__ import annotations
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ====== ② 유틸 ======
def to_yyyymm_str(df, year_col="YEA", mon_col="MON", out="YYYYMM"):
    outdf = df.copy()
    outdf[out] = pd.to_datetime(
        outdf[year_col].astype(str) + outdf[mon_col].astype(str).str.zfill(2),
        format="%Y%m"
    ).dt.strftime("%Y-%m")
    return outdf

def compute_change_table(df, dim_col, base_month, mode="MoM"):
    """
    df        : 상세 데이터프레임
    dim_col   : 'MODEL' 등 증감률을 보고 싶은 차원
    base_month: 'YYYY-MM' (예: '2025-08')
    mode      : 'MoM' or 'YoY'
    """
    d = to_yyyymm_str(df)

    base = pd.to_datetime(base_month + "-01")
    if mode == "MoM":
        comp = base - pd.offsets.MonthBegin(1)  # 전월
    else:
        comp = base - pd.DateOffset(years=1)    # 전년동월
    comp_month = comp.strftime("%Y-%m")

    g = d.groupby([dim_col, "YYYYMM"], as_index=False)["CNT"].sum()

    t_base = g[g["YYYYMM"] == base_month][[dim_col, "CNT"]].rename(columns={"CNT":"CNT_BASE"})
    t_comp = g[g["YYYYMM"] == comp_month][[dim_col, "CNT"]].rename(columns={"CNT":"CNT_COMP"})

    out = pd.merge(t_base, t_comp, on=dim_col, how="outer").fillna(0)

    # 증감률(%) 계산: (기준-비교)/비교 * 100
    out["CHANGE_PCT"] = (out["CNT_BASE"] - out["CNT_COMP"]) / out["CNT_COMP"].replace({0: pd.NA}) * 100
    out["CHANGE_PCT"] = out["CHANGE_PCT"].fillna(0)  # 분모 0 처리 정책: 0%로 대체
    out["CHANGE_ABS"] = out["CNT_BASE"] - out["CNT_COMP"]
    out["BASE_MONTH"] = base_month
    out["COMP_MONTH"] = comp_month
    return out.sort_values("CHANGE_PCT", ascending=False).reset_index(drop=True)

def color_by_sign(values):
    # +는 연빨강, -는 연파랑 (연한 계열)
    return ["lightcoral" if v >= 0 else "lightskyblue" for v in values]

def plot_top_bottom(tbl, dim_col, topn=5, title_prefix="증감률"):
    topN = tbl[(tbl["CNT_BASE"] >= 20) & (tbl["CNT_COMP"] >= 20)].nlargest(topn, "CHANGE_PCT").sort_values(by="CHANGE_PCT",ascending=True)
    botN = tbl[(tbl["CNT_BASE"] >= 20) & (tbl["CNT_COMP"] >= 20)].nsmallest(topn, "CHANGE_PCT").sort_values(by="CHANGE_PCT",ascending=True)
    # 증가 TOP
    fig_up = px.bar(
        topN,
        x="CHANGE_PCT", y=dim_col,
        orientation="h",
        text=round(topN["CHANGE_PCT"],2).astype(str)+"%",
        color=topN["CHANGE_PCT"],
        color_discrete_sequence=color_by_sign(topN["CHANGE_PCT"]),
        title=f"{title_prefix} 증가 TOP {topn}  (기준: {tbl['BASE_MONTH'][0]} / 비교: {tbl['COMP_MONTH'][0]})"
    )
    fig_up.update_traces(textposition="outside")
    fig_up.update_layout(xaxis_title="증감률(%)", showlegend=False)

    # 감소 BOTTOM
    fig_dn = px.bar(
        botN,
        x="CHANGE_PCT", y=dim_col,
        orientation="h",
        text=round(botN["CHANGE_PCT"],2).astype(str)+"%",
        color=botN["CHANGE_PCT"],
        color_discrete_sequence=color_by_sign(botN["CHANGE_PCT"]),
        title=f"{title_prefix} 감소 BOTTOM {topn}  (기준: {tbl['BASE_MONTH'][0]} / 비교: {tbl['COMP_MONTH'][0]})"
    )
    fig_dn.update_traces(textposition="outside")
    fig_dn.update_layout(xaxis_title="증감률(%)", showlegend=False)

    return fig_up, fig_dn

def _range_selector_buttons():
    return dict(buttons=list([
        dict(count=6, label="6m", step="month", stepmode="backward"),
        dict(count=1, label="YTD", step="year", stepmode="todate"),
        dict(count=1, label="1y", step="year", stepmode="backward"),
        dict(step="all")
    ]))

# ─────────────────────────────────────────────────────────────
# 1) 시계열 바/라인 + 범위 선택
def bar_with_range_selector(df, x, y, *, height=400, hover=None, color=None, labels=None):
    fig = px.bar(df, x=x, y=y, hover_data=hover, color=color, labels=labels, height=height)
    fig.update_xaxes(rangeslider_visible=True, rangeselector=_range_selector_buttons())
    return fig

def line_with_range_selector(df, x, y):
    fig = px.line(df, x=x, y=y)
    fig.update_xaxes(rangeslider_visible=True, rangeselector=_range_selector_buttons())
    return fig

# ─────────────────────────────────────────────────────────────
# 2) 카테고리 막대/파이/버블
def category_bar(df, x, y, *, color=None, orientation=None, labels=None):
    return px.bar(df, x=x, y=y, color=color, orientation=orientation, labels=labels)

def pie_simple(df, *, values, names, hole=0.3, category_orders=None, title=None):
    fig = px.pie(df, values=values, names=names, hole=hole, category_orders=category_orders, title=title)
    return fig

def scatter_bubble(df, *, x, y, size, hover_name, size_max=60, labels=None):
    return px.scatter(df, x=x, y=y, size=size, hover_name=hover_name, size_max=size_max, labels=labels)

# ─────────────────────────────────────────────────────────────
# 3) 시계열 스택 바 (예: 월별 OWNER_GB)
def stacked_bar_time(df, *, x, y, color, labels=None):
    return px.bar(df, x=x, y=y, color=color, labels=labels)

# ─────────────────────────────────────────────────────────────
# 4) 범프 차트(랭크 라인)
def bump_from_wide(numeric_df: pd.DataFrame):
    """
    numeric_df: index=연도, columns=항목, value=대수
    -> 각 연도 내 rank(작을수록 위) 후 라인 그래프
    """
    rank_df = numeric_df.rank(axis=1, method='min', ascending=True)
    sort_fields = rank_df.iloc[0].sort_values().index
    fig = px.line(rank_df, x=rank_df.index, y=sort_fields)
    # hover 템플릿은 호출부에서 주입 권장(원본과 동일 표현 위해)
    fig.update_traces(mode='lines+markers', marker_size=10)
    fig.update_layout(hovermode='x')
    return fig, rank_df, sort_fields

# ─────────────────────────────────────────────────────────────
# 5) 이중축: 막대(대수) + 라인(증감률)
def dual_axis_bar_line(x, bar_y, line_y, *, bar_name, line_name,
                       bar_color="lightblue", line_color="red", line_dash="dash",
                       x_title=None, y1_title=None, y2_title=None, template="plotly_white"):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=x, y=bar_y, name=bar_name, marker_color=bar_color,
               hovertemplate='%{x}<extra></extra><br>%{y:,.0f}대'),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=x, y=line_y, name=line_name, mode='lines+markers',
                   line=dict(dash=line_dash, color=line_color), marker=dict(size=10),
                   hovertemplate='%{x}<extra></extra><br>%{y}%'),
        secondary_y=True,
    )
    fig.update_layout(
        xaxis_title=x_title or "",
        yaxis_title=y1_title or "",
        legend=dict(x=0.01, y=0.99),
        template=template,
    )
    fig.update_yaxes(title_text=y1_title or "", secondary_y=False)
    fig.update_yaxes(title_text=y2_title or "", secondary_y=True)
    return fig

# ─────────────────────────────────────────────────────────────
# (옵션) sunburst
def sunburst_simple(df, *, path, values, color=None, title=None):
    return px.sunburst(df, path=path, values=values, color=color, title=title)