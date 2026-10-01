"""Actual vs fitted GDP per capita for each country.

Revised version of the plotting script in Appendix D of the thesis. Changes:
  * uses the repaired MVA series (see prepare_data.py)
  * uses the country fixed effects estimated by the model instead of
    re-deriving them from averaged residuals
  * leaves gaps where a regressor is missing instead of treating it as zero
  * draws 2022-2024 as a separate projection, since those years are outside
    the estimation sample and use carried-forward innovation variables
  * groups countries by an error measure (MAPE) instead of a fixed list

Outputs: results/figures/*.png, results/fit_accuracy.csv
"""

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "panel_clean.csv"
RESULTS = ROOT / "results"
FIGURES = RESULTS / "figures"

REGRESSORS = ["HTEX_LABOR", "IMP_POP", "MVA_MEDHT", "LOG_PATENTRE",
              "EXP_LABOR", "LOG_PATENTNONRE", "RDEXP_GDP", "RDPOP_LABOR"]
CARRY_FORWARD = ["LOG_PATENTRE", "LOG_PATENTNONRE", "RDEXP_GDP", "RDPOP_LABOR"]

# Accuracy groups by in-sample mean absolute percentage error.
HIGH, MEDIUM = 0.05, 0.10


def main() -> None:
    df = pd.read_csv(DATA).sort_values(["Country", "Year"])
    coefs = pd.read_csv(RESULTS / "regression_table.csv", index_col=0)["coefficient"]
    fe = pd.read_csv(RESULTS / "fixed_effects.csv", index_col=0)["fixed_effect"]

    # Carry the last observed (<=2021) innovation values into 2022-2024.
    for col in CARRY_FORWARD:
        last = (df[df["Year"] <= 2021].dropna(subset=[col])
                .groupby("Country")[col].last())
        late = (df["Year"] > 2021) & df[col].isna()
        df.loc[late, col] = df.loc[late, "Country"].map(last)

    df = df[df["Country"].isin(fe.index)].copy()
    df["fitted"] = df[REGRESSORS].mul(coefs[REGRESSORS]).sum(axis=1, min_count=len(REGRESSORS))
    df["fitted"] += df["Country"].map(fe)

    insample = df[df["Year"] <= 2021].dropna(subset=["fitted", "GDP_POP"])
    ape = (insample["fitted"] - insample["GDP_POP"]).abs() / insample["GDP_POP"]
    mape = ape.groupby(insample["Country"]).mean()
    n_obs = ape.groupby(insample["Country"]).size()
    groups = pd.cut(mape, [-np.inf, HIGH, MEDIUM, np.inf],
                    labels=["high", "medium", "low"]).astype(str)
    # With very few observations the country effect absorbs almost all error.
    groups[n_obs < 3] = "insufficient_data"
    acc = pd.DataFrame({"observations": n_obs, "mape": mape.round(4),
                        "group": groups}).sort_values("mape")
    acc.to_csv(RESULTS / "fit_accuracy.csv")
    print(acc["group"].value_counts().to_string())

    FIGURES.mkdir(parents=True, exist_ok=True)
    for country, cdf in df.groupby("Country"):
        est = cdf[cdf["Year"] <= 2021]
        proj = cdf[cdf["Year"] >= 2021]
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(cdf["Year"], cdf["GDP_POP"], "o-", color="#1f4e9a", lw=2, ms=4,
                label="Actual")
        ax.plot(est["Year"], est["fitted"], "s--", color="#e07b00", lw=2, ms=4,
                label="Fitted (2010-2021)")
        ax.plot(proj["Year"], proj["fitted"], ":", color="#e07b00", lw=2,
                label="Projection (2022-2024)")
        name = country.replace("Korea, Rep,", "Korea")
        ax.set_title(f"{name}: actual vs fitted GDP per capita "
                     f"(MAPE {mape.get(country, np.nan):.1%})", fontsize=10)
        ax.set_xlabel("Year")
        ax.set_ylabel("GDP per capita (USD)")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8, loc="upper left")
        fig.tight_layout()
        safe = name.replace(" ", "_").replace(",", "")
        fig.savefig(FIGURES / f"{acc.loc[country, 'group']}_{safe}.png", dpi=150)
        plt.close(fig)
    print(f"Saved {len(list(FIGURES.glob('*.png')))} figures to {FIGURES.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
