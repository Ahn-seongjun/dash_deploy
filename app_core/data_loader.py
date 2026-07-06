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

MARTS_DIRNAME = "marts"


@st.cache_data(ttl=3600)
def _load_excel_cached(path_str: str, sheet_name=0, dtype=None, mtime_ns: int | None = None) -> pd.DataFrame:
    return pd.read_excel(path_str, sheet_name=sheet_name, dtype=dtype, engine="openpyxl")


def load_excel(path: Path, sheet_name=0, dtype=None) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"[data_loader] file not found: {path}")
    return _load_excel_cached(str(path), sheet_name=sheet_name, dtype=dtype, mtime_ns=path.stat().st_mtime_ns)


@st.cache_data(ttl=3600)
def _load_workbook_cached(path_str: str, sheets: tuple[str, ...] | str | None = None, mtime_ns: int | None = None) -> dict[str, pd.DataFrame] | pd.DataFrame:
    return pd.read_excel(path_str, sheet_name=sheets, engine="openpyxl")


def load_workbook(path: Path, sheets: list[str] | None = None) -> dict[str, pd.DataFrame]:
    if not path.exists():
        raise FileNotFoundError(f"[data_loader] file not found: {path}")
    sheet_key = tuple(sheets) if isinstance(sheets, list) else sheets
    dfs = _load_workbook_cached(str(path), sheets=sheet_key, mtime_ns=path.stat().st_mtime_ns)
    if isinstance(dfs, pd.DataFrame):
        key = sheets if isinstance(sheets, str) else "Sheet1"
        dfs = {key: dfs}
    return dfs


@st.cache_data(ttl=3600)
def _load_csv_cached(path_str: str, dtype=None, parse_dates=None, mtime_ns: int | None = None) -> pd.DataFrame:
    return pd.read_csv(path_str, dtype=dtype, parse_dates=parse_dates)


def load_csv(path: Path, dtype=None, parse_dates=None) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"[data_loader] file not found: {path}")
    return _load_csv_cached(
        str(path),
        dtype=dtype,
        parse_dates=parse_dates,
        mtime_ns=path.stat().st_mtime_ns,
    )


@st.cache_data(ttl=3600)
def _load_parquet_cached(path_str: str, columns: tuple[str, ...] | None = None, mtime_ns: int | None = None) -> pd.DataFrame:
    return pd.read_parquet(path_str, columns=list(columns) if columns else None)


def load_parquet(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"[data_loader] file not found: {path}")
    column_key = tuple(columns) if columns is not None else None
    return _load_parquet_cached(str(path), columns=column_key, mtime_ns=path.stat().st_mtime_ns)


def _marts_dir(base: Path) -> Path:
    return base / MARTS_DIRNAME


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
        raw_df.groupby(["YEA", "MON", *use_cols], as_index=False, dropna=False)["CNT"]
        .sum()
        .sort_values(["YEA", "MON"])
        .reset_index(drop=True)
    )


def _build_segment_frame(raw_df: pd.DataFrame) -> pd.DataFrame:
    seg_cols = [col for col in ["EXTRACT_DE", "CAR_SZ", "CAR_BT", "USE_FUEL_NM"] if col in raw_df.columns]
    return (
        raw_df.groupby(seg_cols, as_index=False, dropna=False)["CNT"]
        .sum()
        .sort_values("EXTRACT_DE")
        .reset_index(drop=True)
    )


def _build_top_table(raw_df: pd.DataFrame) -> pd.DataFrame:
    latest_month = int(raw_df["EXTRACT_DE"].max())
    latest_df = raw_df[raw_df["EXTRACT_DE"] == latest_month].copy()
    grouped = (
        latest_df.groupby(
            ["CL_HMMD_IMP_SE_NM", "ORG_CAR_MAKER_KOR", "CAR_MOEL_DT"],
            as_index=False,
            dropna=False,
        )["CNT"]
        .sum()
        .sort_values(["CL_HMMD_IMP_SE_NM", "CNT"], ascending=[True, False])
    )
    grouped["RN"] = grouped.groupby("CL_HMMD_IMP_SE_NM").cumcount() + 1
    return grouped[grouped["RN"] <= 10].reset_index(drop=True)


def _load_newreg_detail_mart(base: Path) -> pd.DataFrame | None:
    path = _marts_dir(base) / "newreg_detail.parquet"
    if not path.exists():
        return None
    return _normalize_raw_frame(load_parquet(path))


def _load_used_detail_mart(base: Path) -> pd.DataFrame | None:
    path = _marts_dir(base) / "used_detail.parquet"
    if not path.exists():
        return None
    return _normalize_raw_frame(load_parquet(path))


def _load_erase_detail_mart(base: Path) -> pd.DataFrame | None:
    path = _marts_dir(base) / "erase_detail.parquet"
    if not path.exists():
        return None
    return _normalize_raw_frame(load_parquet(path))


def _load_car_use_mart(base: Path) -> pd.DataFrame:
    mart_path = _marts_dir(base) / "car_use_yearly_summary.parquet"
    root_path = base / "car_use_yearly_summary.parquet"
    if mart_path.exists():
        return load_parquet(mart_path)
    return load_parquet(root_path)


def _load_newreg_from_marts(base: Path) -> dict[str, pd.DataFrame] | None:
    detail = _load_newreg_detail_mart(base)
    if detail is None:
        return None

    monthly = (
        detail.groupby("EXTRACT_DE", as_index=False)["CNT"]
        .sum()
        .rename(columns={"EXTRACT_DE": "date"})
        .sort_values("date")
        .reset_index(drop=True)
    )

    use_long = _load_car_use_mart(base)
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
    use_wide.columns = [str(col)[-2:] if isinstance(col, int) else col for col in use_wide.columns]

    return {"monthly": monthly, "cum": use_wide, "dim": detail}


def _load_overview_from_marts(base: Path) -> Dict[str, pd.DataFrame] | None:
    new_detail = _load_newreg_detail_mart(base)
    used_detail = _load_used_detail_mart(base)
    erase_detail = _load_erase_detail_mart(base)
    if any(frame is None for frame in [new_detail, used_detail, erase_detail]):
        return None

    new_detail = new_detail.copy()
    used_detail = used_detail.copy()
    erase_detail = erase_detail.copy()

    return {
        "new_top": _build_top_table(new_detail),
        "use_top": _build_top_table(used_detail),
        "ersr_top": _build_top_table(erase_detail),
        "new_mon_cnt": _build_monthly_detail(new_detail),
        "used_mon_cnt": _build_monthly_detail(used_detail),
        "er_mon_cnt": _build_monthly_detail(erase_detail),
        "new_seg": _build_segment_frame(new_detail),
        "used_seg": _build_segment_frame(used_detail),
        "er_seg": _build_segment_frame(erase_detail),
    }


def _load_newreg_parquet(base: Path) -> dict[str, pd.DataFrame]:
    raw_df = _normalize_raw_frame(load_parquet(base / "newreg_2025_2026.parquet"))
    monthly = (
        raw_df.groupby("EXTRACT_DE", as_index=False)["CNT"]
        .sum()
        .rename(columns={"EXTRACT_DE": "date"})
        .sort_values("date")
        .reset_index(drop=True)
    )

    use_long = _load_car_use_mart(base)
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
    use_wide.columns = [str(col)[-2:] if isinstance(col, int) else col for col in use_wide.columns]

    return {"monthly": monthly, "cum": use_wide, "dim": raw_df}


def _load_ersr_parquet(base: Path) -> dict[str, pd.DataFrame]:
    raw_df = _normalize_raw_frame(load_parquet(base / "ersrreg_2025_2026.parquet"))
    return {"monthly": raw_df}


@st.cache_data(ttl=3600, show_spinner="Overview 데이터를 준비하는 중...")
def get_overview_data(base_dir: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    base = Path(base_dir) if base_dir else Path("./data")

    mart_data = _load_overview_from_marts(base)
    if mart_data is not None:
        return mart_data

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
        p_seg = base / f"26{month}차급차형연료.xlsx"

        top_wb = load_workbook(p_top, sheets=["신규", "이전", "말소"])
        mon_wb = load_workbook(p_mon, sheets=["신규", "이전", "말소"])
        seg_wb = load_workbook(p_seg, sheets=["신규", "이전", "말소"])
    except Exception:
        nodata = datetime(today.year, today.month, today.day) + relativedelta(months=-2)
        preyearmon = nodata.strftime("%y%m")
        p_top = base / f"{preyearmon}_top.xlsx"
        p_mon = base / "25_26_moncnt.xlsx"
        p_seg = base / f"{preyearmon}차급차형연료.xlsx"
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

    mart_data = _load_newreg_from_marts(base)
    if mart_data is not None:
        return mart_data

    parquet_path = base / "newreg_2025_2026.parquet"
    if parquet_path.exists():
        return _load_newreg_parquet(base)

    paths = {
        "monthly": base / "simple_monthly_cnt.csv",
        "cum": base / "16-25누적용도별등록대수.csv",
        "dim": base / "2025년누적데이터.csv",
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

    mart_detail = _load_erase_detail_mart(base)
    if mart_detail is not None:
        return {"monthly": mart_detail}

    parquet_path = base / "ersrreg_2025_2026.parquet"
    if parquet_path.exists():
        return _load_ersr_parquet(base)

    df = load_csv(base / "2025년말소데이터.csv")
    return {"monthly": _normalize_raw_frame(df)}
