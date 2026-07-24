from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

RAW_BASE = Path(r"C:\Users\clmns\PycharmProjects\pythonProject1\streamlit_git\dash_deploy_data\rawdata")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_BASE = PROJECT_ROOT / "data" / "marts"


def ensure_out_dir() -> None:
    OUT_BASE.mkdir(parents=True, exist_ok=True)


def read_parquet(name: str, columns: list[str] | None = None) -> pd.DataFrame:
    return pd.read_parquet(RAW_BASE / name, columns=columns)


def write_parquet(df: pd.DataFrame, name: str) -> None:
    target = OUT_BASE / name
    df.to_parquet(target, index=False, engine="pyarrow", compression="snappy")
    print(f"saved {target} {df.shape}")


def normalize_cnt(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    # Raw parquet is record-level data, so one row equals one registration unless CNT already exists.
    if "CNT" not in out.columns:
        out["CNT"] = 1
    out["CNT"] = pd.to_numeric(out["CNT"], errors="coerce").fillna(0).astype("int32")
    out["EXTRACT_DE"] = pd.to_numeric(out["EXTRACT_DE"], errors="coerce").astype("int32")
    return out


def build_newreg_detail() -> None:
    cols = [
        "EXTRACT_DE",
        "CL_HMMD_IMP_SE_NM",
        "ORG_CAR_MAKER_KOR",
        "CAR_MOEL_DT",
        "CAR_BT",
        "CAR_SZ",
        "USE_FUEL_NM",
        "SOU_GB",
        "SOU_AGE",
        "JUSO_SIDO",
        "CAR_USE",
        "CAR_USE_DETAL",
    ]
    df = normalize_cnt(read_parquet("newreg_2025_2026.parquet", columns=cols))
    grouped = (
        df.groupby(cols, as_index=False, dropna=False)["CNT"]
        .sum()
        .sort_values(["EXTRACT_DE", "ORG_CAR_MAKER_KOR", "CAR_MOEL_DT"])
        .reset_index(drop=True)
    )
    write_parquet(grouped, "newreg_detail.parquet")


def build_used_detail() -> None:
    cols = [
        "EXTRACT_DE",
        "CL_HMMD_IMP_SE_NM",
        "ORG_CAR_MAKER_KOR",
        "CAR_MOEL_DT",
        "CAR_MODEL_KOR",
        "CAR_BT",
        "CAR_SZ",
        "USE_FUEL_NM",
    ]
    df = normalize_cnt(read_parquet("usedreg_2025_2026.parquet", columns=cols))
    grouped = (
        df.groupby(cols, as_index=False, dropna=False)["CNT"]
        .sum()
        .sort_values(["EXTRACT_DE", "ORG_CAR_MAKER_KOR", "CAR_MOEL_DT", "CAR_MODEL_KOR"])
        .reset_index(drop=True)
    )
    write_parquet(grouped, "used_detail.parquet")


def build_erase_detail() -> None:
    cols = [
        "EXTRACT_DE",
        "CL_HMMD_IMP_SE_NM",
        "ORG_CAR_MAKER_KOR",
        "CAR_MOEL_DT",
        "CAR_BT",
        "CAR_SZ",
        "USE_FUEL_NM",
        "SOU_AGE",
        "F_YEAR",
    ]
    df = normalize_cnt(read_parquet("ersrreg_2025_2026.parquet", columns=cols))
    df["F_YEAR"] = pd.to_numeric(df["F_YEAR"], errors="coerce").fillna(0).astype("int16")
    grouped = (
        df.groupby(cols, as_index=False, dropna=False)["CNT"]
        .sum()
        .sort_values(["EXTRACT_DE", "ORG_CAR_MAKER_KOR", "CAR_MOEL_DT"])
        .reset_index(drop=True)
    )
    write_parquet(grouped, "erase_detail.parquet")


def copy_car_use_summary() -> None:
    source = RAW_BASE / "car_use_yearly_summary.parquet"
    target = OUT_BASE / "car_use_yearly_summary.parquet"
    shutil.copy2(source, target)
    print(f"copied {source} -> {target}")


def main() -> None:
    ensure_out_dir()
    build_newreg_detail()
    build_used_detail()
    build_erase_detail()
    copy_car_use_summary()
    print("done")


if __name__ == "__main__":
    main()
