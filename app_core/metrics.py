from typing import Dict, Any
import math

def safe_div(n, d, default=0.0) -> float:
    try:
        if d is None or d == 0:
            return default
        return float(n) / float(d)
    except Exception:
        return default

def rate_change(curr, prev) -> float:
    return safe_div(curr - prev, prev, default=float("nan"))

def format_number(x, kind: str = "int", digits: int = 1) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "-"
    if kind == "int":
        return f"{int(round(x)):,}"
    if kind == "float":
        return f"{x:.{digits}f}"
    if kind == "percent":
        return f"{x*100:.{digits}f}%"
    return str(x)

def kpi_values(df, spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    spec 예:
    {
      "total": {"col": "CNT", "agg": "sum"},  # 전체 합계
      "mom": {"col": "MoM", "agg": "last"},   # 최근 월 MoM
      "yoy": {"col": "YoY", "agg": "last"},
    }
    """
    out = {}
    for k, cfg in spec.items():
        col = cfg["col"]
        agg = cfg.get("agg", "sum")
        if col not in df.columns:
            out[k] = None
            continue
        if agg == "sum":
            out[k] = float(df[col].sum())
        elif agg == "mean":
            out[k] = float(df[col].mean())
        elif agg == "last":
            out[k] = float(df[col].iloc[-1])
        else:
            out[k] = None
    return out