import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime



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