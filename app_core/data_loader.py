# app_core/data_loader.py
from __future__ import annotations
from typing import Optional, Dict
from pathlib import Path
import pandas as pd
import streamlit as st

# ── 개별 로더: 스피너 없음(중복 방지) ─────────────────────────────────
@st.cache_data(ttl=3600)
def load_excel(path: Path, sheet_name=0, dtype=None) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"[data_loader] 파일이 없습니다: {path}")
    return pd.read_excel(path, sheet_name=sheet_name, dtype=dtype, engine="openpyxl")

@st.cache_data(ttl=3600)
def load_workbook(path: Path, sheets: list[str] | None = None) -> dict[str, pd.DataFrame]:
    if not path.exists():
        raise FileNotFoundError(f"[data_loader] 파일이 없습니다: {path}")
    dfs = pd.read_excel(path, sheet_name=sheets, engine="openpyxl")
    if isinstance(dfs, pd.DataFrame):
        key = sheets if isinstance(sheets, str) else "Sheet1"
        dfs = {key: dfs}
    return dfs

@st.cache_data(ttl=3600)
def load_csv(path: Path, dtype=None, parse_dates=None) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"[data_loader] 파일이 없습니다: {path}")
    return pd.read_csv(path, dtype=dtype, parse_dates=parse_dates)

# ── 번들러: 스피너 1회 표시 ──────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner="🚗 데이터 엔진 예열 중…")
def get_overview_data(base_dir: Optional[str] = None) -> Dict[str, pd.DataFrame]:

    base = Path(base_dir) if base_dir else Path("./data")
    p_top = base / "2509_top.xlsx"
    p_mon = base / "24_25_moncnt.xlsx"
    p_seg = base / "2509차급외형연료.xlsx"

    top_wb = load_workbook(p_top, sheets=["신규","이전","말소"])
    mon_wb = load_workbook(p_mon, sheets=["신규","이전","말소"])
    seg_wb = load_workbook(p_seg, sheets=["신규","이전","말소"])

    return {
        "new_top":      top_wb["신규"],
        "use_top":      top_wb["이전"],
        "ersr_top":     top_wb["말소"],
        "new_mon_cnt":  mon_wb["신규"],
        "used_mon_cnt": mon_wb["이전"],
        "er_mon_cnt":   mon_wb["말소"],
        "new_seg":      seg_wb["신규"].copy(),
        "used_seg":     seg_wb["이전"].copy(),
        "er_seg":       seg_wb["말소"].copy(),
    }


@st.cache_data(ttl=3600, show_spinner="신규등록 데이터 불러오는 중...")
def get_newreg_data(base_dir: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    base = Path(base_dir) if base_dir else Path("./data")
    paths = {
        "monthly": base / "simple_monthly_cnt.csv",
        "cum":     base / "12-24누적 용도별 등록대수.csv",
        "dim":     base / "2024년 누적 데이터.csv",
    }
    return {
        "monthly": load_csv(paths["monthly"]),
        "cum":     load_csv(paths["cum"]),
        "dim":     load_csv(paths["dim"]),
    }

@st.cache_data(ttl=3600, show_spinner="말소등록 데이터 불러오는 중...")
def get_ersr_data(base_dir: Optional[str] = "data/ersr") -> Dict[str, pd.DataFrame]:
    base = Path(base_dir) if base_dir else Path("./data/ersr")
    df = load_csv(base / "2024년 말소데이터.csv")
    return {"monthly": df}