"""Clean the raw OECD panel and build the regression variables.

Input:  data/raw/oecd_panel_raw.csv   (World Bank WDI series, 38 countries, 2010-2024)
Output: data/processed/panel_clean.csv

Steps
1. Convert World Bank missing-value markers ("..", ",,") to NaN.
2. Repair manufacturing value added (MVA) entries whose decimal separator was lost
   during export. These rows are hundreds to thousands of times larger than the
   country's GDP, which is impossible. Each is rescaled by the power of ten that
   brings MVA/GDP back into the normal 3-35% range. Affected: Australia
   2010-2024, Austria 2010-2024, Belgium 2010-2014. Every repaired row is
   written to results/mva_repairs.csv.
3. Build the transformed regressors used in the thesis model.
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "oecd_panel_raw.csv"
OUT = ROOT / "data" / "processed" / "panel_clean.csv"
REPAIRS = ROOT / "results" / "mva_repairs.csv"

NUMERIC = ["GDP", "Pop", "Labor", "PatentRe", "PatentNonRe", "MVA",
           "MedHTMVA", "HTEX", "IMP", "EXP", "RDEXP", "RDPop"]

# Manufacturing value added is normally 3-35% of GDP in OECD countries.
PLAUSIBLE_SHARE = (0.03, 0.35)
TYPICAL_MVA_SHARE = 0.12


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(RAW)
    df = df.replace({"..": np.nan, ",,": np.nan})
    for col in NUMERIC:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Year"] = df["Year"].astype(int)
    return df


def _repair_power(share: float) -> int:
    """Power of ten that brings an impossible MVA/GDP share into a normal range."""
    candidates = [k for k in range(1, 7)
                  if PLAUSIBLE_SHARE[0] <= share / 10 ** k <= PLAUSIBLE_SHARE[1]]
    if not candidates:
        raise ValueError(f"Cannot repair MVA share {share:.1f}")
    return min(candidates, key=lambda k: abs(share / 10 ** k - TYPICAL_MVA_SHARE))


def repair_mva(df: pd.DataFrame) -> pd.DataFrame:
    share = df["MVA"] / df["GDP"]
    bad = share > 1  # manufacturing cannot exceed total GDP
    power = np.array([_repair_power(s) if b else 0 for s, b in zip(share, bad)])
    repaired = df.loc[bad, ["Country", "Year", "MVA"]].copy()
    df["MVA"] = df["MVA"] / 10.0 ** power
    repaired["MVA_repaired"] = df.loc[bad, "MVA"]
    repaired["divided_by"] = (10.0 ** power[bad]).astype(int)
    REPAIRS.parent.mkdir(parents=True, exist_ok=True)
    repaired.to_csv(REPAIRS, index=False)
    print(f"Repaired {bad.sum()} MVA values (see {REPAIRS.relative_to(ROOT)})")
    return df


def build_variables(df: pd.DataFrame) -> pd.DataFrame:
    df["GDP_POP"] = df["GDP"] / df["Pop"]
    df["HTEX_LABOR"] = df["HTEX"] / df["Labor"]
    df["IMP_POP"] = df["IMP"] / df["Pop"]
    df["MVA_MEDHT"] = df["MVA"] * df["MedHTMVA"] / 100
    df["LOG_PATENTRE"] = np.log(df["PatentRe"].where(df["PatentRe"] > 0))
    df["EXP_LABOR"] = df["EXP"] / df["Labor"]
    df["LOG_PATENTNONRE"] = np.log(df["PatentNonRe"].where(df["PatentNonRe"] > 0))
    df["RDEXP_GDP"] = df["RDEXP"] * df["GDP"] / 100
    df["RDPOP_LABOR"] = df["RDPop"] / df["Labor"]
    return df


def main() -> None:
    df = build_variables(repair_mva(load_raw()))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Saved {len(df)} rows to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
