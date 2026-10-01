"""Estimate the fixed-effects panel model from the thesis.

Model (EViews 10 command used in the thesis):
    LS(CX=F) GDP/POP C HTEX/LABOR IMP/POP MVA*MEDHTMVA/100 LOG(PATENTRE)
             EXP01/LABOR LOG(PATENTNONRE) RDEXP*GDP/100 RDPOP/LABOR

Sample: 37 OECD countries, 2010-2021, rows with no missing values (386 obs).

The script reports two versions:
  * conventional standard errors (identical to the EViews output in the thesis)
  * standard errors clustered by country (robust to the serial correlation
    signalled by the low Durbin-Watson statistic)

Outputs: results/regression_table.csv, results/regression_table.md,
         results/fixed_effects.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "panel_clean.csv"
RESULTS = ROOT / "results"

REGRESSORS = ["HTEX_LABOR", "IMP_POP", "MVA_MEDHT", "LOG_PATENTRE",
              "EXP_LABOR", "LOG_PATENTNONRE", "RDEXP_GDP", "RDPOP_LABOR"]

# Coefficients reported by EViews in the thesis (Figure 3), used as a check.
EVIEWS = {"HTEX_LABOR": 1.241924, "IMP_POP": -0.497622, "MVA_MEDHT": 6.26e-08,
          "LOG_PATENTRE": -2172.586, "EXP_LABOR": 0.572588,
          "LOG_PATENTNONRE": -1757.572, "RDEXP_GDP": 2.81e-08,
          "RDPOP_LABOR": -997902.5}


def estimation_sample() -> pd.DataFrame:
    df = pd.read_csv(DATA)
    df = df[df["Year"].between(2010, 2021)]
    return df.dropna(subset=["GDP_POP"] + REGRESSORS)


def fit(sample: pd.DataFrame, clustered: bool):
    panel = sample.set_index(["Country", "Year"])
    # Rescale regressors before fitting: some are in the 1e13 range, which makes
    # the design matrix numerically ill-conditioned. Coefficients are scaled back.
    scale = panel[REGRESSORS].std()
    model = PanelOLS(panel["GDP_POP"], panel[REGRESSORS] / scale,
                     entity_effects=True, check_rank=False)
    if clustered:
        res = model.fit(cov_type="clustered", cluster_entity=True)
    else:
        res = model.fit(cov_type="unadjusted")
    return res, scale


def main() -> None:
    sample = estimation_sample()
    print(f"Sample: {len(sample)} observations, "
          f"{sample['Country'].nunique()} countries")

    plain, scale = fit(sample, clustered=False)
    robust, _ = fit(sample, clustered=True)

    table = pd.DataFrame({
        "coefficient": plain.params / scale,
        "se": plain.std_errors / scale,
        "p_value": plain.pvalues,
        "se_clustered": robust.std_errors / scale,
        "p_value_clustered": robust.pvalues,
        "eviews_coefficient": pd.Series(EVIEWS),
    })
    table.index.name = "variable"

    # Check that the Python estimates reproduce the thesis output.
    rel_diff = (table["coefficient"] / table["eviews_coefficient"] - 1).abs()
    print(f"Largest relative difference from EViews: {rel_diff.max():.4%}")

    RESULTS.mkdir(exist_ok=True)
    table.to_csv(RESULTS / "regression_table.csv")

    fe = plain.estimated_effects.groupby(level="Country").first()
    fe.columns = ["fixed_effect"]
    fe.to_csv(RESULTS / "fixed_effects.csv")

    def fmt(x):
        return f"{x:.4g}"

    lines = ["| Variable | Coefficient | p (conventional) | p (clustered by country) |",
             "|---|---|---|---|"]
    for var, row in table.iterrows():
        lines.append(f"| {var} | {fmt(row.coefficient)} | {row.p_value:.4f} | "
                     f"{row.p_value_clustered:.4f} |")
    lines += ["",
              f"Observations: {int(plain.nobs)}; countries: {sample['Country'].nunique()}",
              f"Within R-squared: {plain.rsquared_within:.3f}",
              f"R-squared including country effects (EViews definition): "
              f"{1 - (plain.resids ** 2).sum() / ((sample['GDP_POP'] - sample['GDP_POP'].mean()) ** 2).sum():.4f}"]
    (RESULTS / "regression_table.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
