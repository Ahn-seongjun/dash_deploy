from typing import Dict, List, Optional
import pandas as pd

from .constants import COLS, CATS

def normalize_labels(df: pd.DataFrame, col: str, mapping: Dict[str, str]) -> pd.DataFrame:
    out = df.copy()
    if col in out.columns:
        out[col] = out[col].map(lambda x: mapping.get(str(x), x))
    return out

def parse_yearmonth(df: pd.DataFrame, src_col: str, dst_col: str) -> pd.DataFrame:
    out = df.copy()
    if src_col not in out.columns:
        return out
    # 정수/문자 형태의 YYYYMM → Period/문자
    out[dst_col] = pd.to_datetime(out[src_col].astype(str) + "01", format="%Y%m%d").dt.to_period("M").astype(str)
    return out

def apply_filters(df: pd.DataFrame, filters: Dict[str, Optional[list]]) -> pd.DataFrame:
    out = df.copy()
    if not filters:
        return out
    for col, vals in filters.items():
        if vals in (None, [], "전체"):
            continue
        if col in out.columns:
            if isinstance(vals, list):
                out = out[out[col].isin(vals)]
            else:
                out = out[out[col] == vals]
    return out

def group_monthly(df: pd.DataFrame, date_col: str, value_col: str, dims: Optional[List[str]] = None) -> pd.DataFrame:
    """
    월별 합계/평균 등 집계(기본 합계)
    """
    out = df.copy()
    by = [date_col] + (dims or [])
    g = out.groupby(by, dropna=False, as_index=False)[value_col].sum()
    return g.sort_values(by=by)

def calc_yoy(df: pd.DataFrame, date_col: str, value_col: str, keys: Optional[List[str]] = None) -> pd.DataFrame:
    """
    전년 동월 대비 증감률 계산: (현재 - 작년) / 작년
    keys: 비교 그룹 키(브랜드 등)
    """
    out = df.copy()
    by = keys or []
    # 연/월 분리 후 전년 매칭
    tmp = out.copy()
    tmp["__YYYY"] = pd.to_datetime(tmp[date_col] + "-01").dt.year
    tmp["__MM"] = pd.to_datetime(tmp[date_col] + "-01").dt.month
    curr = tmp.rename(columns={value_col: "__curr"})
    prev = tmp.rename(columns={value_col: "__prev"})
    prev["__YYYY"] = prev["__YYYY"] + -1
    on = by + ["__YYYY", "__MM"]
    merged = pd.merge(curr[on + ["__curr"]], prev[on + ["__prev"]], on=on, how="left")
    merged["YoY"] = (merged["__curr"] - merged["__prev"]) / merged["__prev"]
    # 원래 df에 결합
    out = out.merge(merged[by + [date_col, "YoY"]], on=by + [date_col], how="left")
    return out

def calc_mom(df: pd.DataFrame, date_col: str, value_col: str, keys: Optional[List[str]] = None) -> pd.DataFrame:
    """
    전월 대비 증감률: (현재 - 전월) / 전월
    """
    out = df.copy().sort_values(by=(keys or []) + [date_col])
    by = keys or []
    out["__prev"] = out.groupby(by, dropna=False)[value_col].shift(1)
    out["MoM"] = (out[value_col] - out["__prev"]) / out["__prev"]
    return out.drop(columns=["__prev"])

def share_by(df: pd.DataFrame, group_cols: List[str], value_col: str, within: Optional[List[str]] = None) -> pd.DataFrame:
    """
    within(분모 그룹) 기준으로 비중(%) 계산
    """
    out = df.copy()
    g = out.groupby(group_cols, dropna=False, as_index=False)[value_col].sum()
    if within:
        total = g.groupby(within, dropna=False, as_index=False)[value_col].sum().rename(columns={value_col: "__total"})
        g = g.merge(total, on=within, how="left")
        g["SHARE"] = g[value_col] / g["__total"]
        g = g.drop(columns="__total")
    else:
        total = g[value_col].sum()
        g["SHARE"] = g[value_col] / total if total else 0.0
    return g