from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import streamlit as st
from dateutil.relativedelta import relativedelta

today = datetime.today()
month_ago = datetime(today.year, today.month, today.day) + relativedelta(months=-1)
month = month_ago.strftime("%m")


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


@st.cache_data(ttl=3600)
def load_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"[data_loader] 파일이 없습니다: {path}")
    return pd.read_parquet(path)


def _normalize_raw_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    rename_map = {
        "USE_FUEL_NM": "FUEL",
        "SOU_GB": "OWNER_GB",
        "SOU_AGE": "AGE",
    }
    for source, target in rename_map.items():
        if source in out.columns and target not in out.columns:
            out[target] = out[source]

    if "CNT" not in out.columns:
        out["CNT"] = 1
    out["CNT"] = pd.to_numeric(out["CNT"], errors="coerce").fillna(0)

    if "EXTRACT_DE" in out.columns:
        out["EXTRACT_DE"] = pd.to_numeric(out["EXTRACT_DE"], errors="coerce").fillna(0).astype(int)
        out["YEA"] = (out["EXTRACT_DE"] // 100).astype(int)
        out["MON"] = (out["EXTRACT_DE"] % 100).astype(int)

    return out


def _build_monthly_total(raw_df: pd.DataFrame) -> pd.DataFrame:
    return (
        raw_df.groupby(["YEA", "MON"], as_index=False)["CNT"]
        .sum()
        .sort_values(["YEA", "MON"])
        .reset_index(drop=True)
    )


def _build_monthly_detail(raw_df: pd.DataFrame) -> pd.DataFrame:
    dim_cols = [
        "CL_HMMD_IMP_SE_NM",
        "ORG_CAR_MAKER_KOR",
        "CAR_MOEL_DT",
        "CAR_SZ",
        "CAR_BT",
        "USE_FUEL_NM",
    ]
    use_cols = [col for col in dim_cols if col in raw_df.columns]
    return (
        raw_df.groupby(["YEA", "MON", *use_cols], as_index=False)["CNT"]
        .sum()
        .sort_values(["YEA", "MON"])
        .reset_index(drop=True)
    )


def _build_segment_frame(raw_df: pd.DataFrame) -> pd.DataFrame:
    seg_cols = [col for col in ["EXTRACT_DE", "CAR_SZ", "CAR_BT", "USE_FUEL_NM"] if col in raw_df.columns]
    return (
        raw_df.groupby(seg_cols, as_index=False)["CNT"]
        .sum()
        .sort_values("EXTRACT_DE")
        .reset_index(drop=True)
    )


def _build_top_table(raw_df: pd.DataFrame) -> pd.DataFrame:
    latest_month = int(raw_df["EXTRACT_DE"].max())
    latest_df = raw_df[raw_df["EXTRACT_DE"] == latest_month].copy()
    grouped = (
        latest_df.groupby(["CL_HMMD_IMP_SE_NM", "ORG_CAR_MAKER_KOR", "CAR_MOEL_DT"], as_index=False)["CNT"]
        .sum()
        .sort_values(["CL_HMMD_IMP_SE_NM", "CNT"], ascending=[True, False])
    )
    grouped["RN"] = grouped.groupby("CL_HMMD_IMP_SE_NM").cumcount() + 1
    return grouped[grouped["RN"] <= 10].reset_index(drop=True)


def _load_newreg_parquet(base: Path) -> dict[str, pd.DataFrame]:
    raw_df = _normalize_raw_frame(load_parquet(base / "newreg_2025_2026.parquet"))
    monthly = (
        raw_df.groupby("EXTRACT_DE", as_index=False)["CNT"]
        .sum()
        .rename(columns={"EXTRACT_DE": "date"})
        .sort_values("date")
        .reset_index(drop=True)
    )

    use_long = load_parquet(base / "car_use_yearly_summary.parquet")
    use_wide = (
        use_long.pivot_table(
            index=["CAR_USE", "CAR_USE_DETAL"],
            columns="YEAR",
            values="CNT",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )
    use_wide.columns = [
        str(col)[-2:] if isinstance(col, int) else col
        for col in use_wide.columns
    ]

    return {
        "monthly": monthly,
        "cum": use_wide,
        "dim": raw_df,
    }


def _load_ersr_parquet(base: Path) -> dict[str, pd.DataFrame]:
    raw_df = _normalize_raw_frame(load_parquet(base / "ersrreg_2025_2026.parquet"))
    return {"monthly": raw_df}


def _load_used_parquet(base: Path) -> pd.DataFrame:
    return _normalize_raw_frame(load_parquet(base / "usedreg_2025_2026.parquet"))


@st.cache_data(ttl=3600, show_spinner="Overview 데이터를 준비하는 중...")
def get_overview_data(base_dir: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    base = Path(base_dir) if base_dir else Path("./data")

    parquet_paths = [
        base / "newreg_2025_2026.parquet",
        base / "usedreg_2025_2026.parquet",
        base / "ersrreg_2025_2026.parquet",
    ]
    if all(path.exists() for path in parquet_paths):
        new_raw = _normalize_raw_frame(load_parquet(parquet_paths[0]))
        used_raw = _normalize_raw_frame(load_parquet(parquet_paths[1]))
        ersr_raw = _normalize_raw_frame(load_parquet(parquet_paths[2]))

        return {
            "new_top": _build_top_table(new_raw),
            "use_top": _build_top_table(used_raw),
            "ersr_top": _build_top_table(ersr_raw),
            "new_mon_cnt": _build_monthly_detail(new_raw),
            "used_mon_cnt": _build_monthly_detail(used_raw),
            "er_mon_cnt": _build_monthly_detail(ersr_raw),
            "new_seg": _build_segment_frame(new_raw),
            "used_seg": _build_segment_frame(used_raw),
            "er_seg": _build_segment_frame(ersr_raw),
        }

    try:
        p_top = base / f"26{month}_top.xlsx"
        p_mon = base / "25_26_moncnt.xlsx"
        p_seg = base / f"26{month}차급외형연료.xlsx"

        top_wb = load_workbook(p_top, sheets=["신규", "이전", "말소"])
        mon_wb = load_workbook(p_mon, sheets=["신규", "이전", "말소"])
        seg_wb = load_workbook(p_seg, sheets=["신규", "이전", "말소"])
    except Exception:
        nodata = datetime(today.year, today.month, today.day) + relativedelta(months=-2)
        preyearmon = nodata.strftime("%y%m")
        p_top = base / f"{preyearmon}_top.xlsx"
        p_mon = base / "25_26_moncnt.xlsx"
        p_seg = base / f"{preyearmon}차급외형연료.xlsx"
        top_wb = load_workbook(p_top, sheets=["신규", "이전", "말소"])
        mon_wb = load_workbook(p_mon, sheets=["신규", "이전", "말소"])
        seg_wb = load_workbook(p_seg, sheets=["신규", "이전", "말소"])

    return {
        "new_top": top_wb["신규"],
        "use_top": top_wb["이전"],
        "ersr_top": top_wb["말소"],
        "new_mon_cnt": mon_wb["신규"],
        "used_mon_cnt": mon_wb["이전"],
        "er_mon_cnt": mon_wb["말소"],
        "new_seg": seg_wb["신규"].copy(),
        "used_seg": seg_wb["이전"].copy(),
        "er_seg": seg_wb["말소"].copy(),
    }


@st.cache_data(ttl=3600, show_spinner="신규등록 데이터를 불러오는 중...")
def get_newreg_data(base_dir: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    base = Path(base_dir) if base_dir else Path("./data")
    parquet_path = base / "newreg_2025_2026.parquet"
    if parquet_path.exists():
        return _load_newreg_parquet(base)

    paths = {
        "monthly": base / "simple_monthly_cnt.csv",
        "cum": base / "16-25누적 용도별 등록대수.csv",
        "dim": base / "2025년 누적 데이터.csv",
    }
    data = {
        "monthly": load_csv(paths["monthly"]),
        "cum": load_csv(paths["cum"]),
        "dim": load_csv(paths["dim"]),
    }
    data["dim"] = _normalize_raw_frame(data["dim"])
    return data


@st.cache_data(ttl=3600, show_spinner="말소등록 데이터를 불러오는 중...")
def get_ersr_data(base_dir: Optional[str] = "data") -> Dict[str, pd.DataFrame]:
    base = Path(base_dir) if base_dir else Path("./data")
    parquet_path = base / "ersrreg_2025_2026.parquet"
    if parquet_path.exists():
        return _load_ersr_parquet(base)

    df = load_csv(base / "2025년 말소데이터.csv")
    return {"monthly": _normalize_raw_frame(df)}
