# Innovation and Economic Growth in OECD Countries

Code and data for my master's thesis at Vilnius Gediminas Technical University (VILNIUS TECH), 2026:

> **The Impact of Innovation on the Development of High Value-Added Industrial Enterprises and on Economic Growth in the Conditions of Globalization**
> Ramiz Huseynov. Supervisor: Assoc. Prof. Dr. Rūta Banelienė. Grade 9.06/10. [Full text (PDF)](docs/thesis.pdf).
> Presented at the 29th Conference for Lithuanian Junior Researchers "Science - Future of Lithuania", Vilnius, April 2026.

The thesis asks how innovation, manufacturing sophistication and trade relate to GDP per capita across the 37 OECD member states between 2010 and 2021. The original model was estimated in EViews 10. This repository rebuilds the whole analysis in Python, so it can be reproduced without EViews.

## Model

Panel least squares with country fixed effects:

```
GDP/POP = a_i + b1 HTEX/LABOR + b2 IMP/POP + b3 MVA*MEDHTMVA/100
              + b4 log(PATENTRE) + b5 EXP/LABOR + b6 log(PATENTNONRE)
              + b7 RDEXP*GDP/100 + b8 RDPOP/LABOR + e
```

| Variable | Meaning |
|---|---|
| GDP/POP | GDP per capita, current USD |
| HTEX/LABOR | High-technology exports per worker |
| IMP/POP | Imports per capita |
| MVA*MEDHTMVA/100 | Manufacturing value added from medium and high-tech industries |
| log(PATENTRE), log(PATENTNONRE) | Resident and non-resident patent applications (log) |
| EXP/LABOR | Exports per worker |
| RDEXP*GDP/100 | R&D expenditure in USD |
| RDPOP/LABOR | R&D researchers per million people, relative to the labour force |

Sample: 37 countries, 2010-2021, 386 country-year observations (unbalanced panel). All series come from the World Bank World Development Indicators.

## Results

The Python estimates reproduce the EViews output in the thesis (largest coefficient difference below 0.1%).

| Variable | Coefficient | p (conventional) | p (clustered by country) |
|---|---|---|---|
| HTEX/LABOR | 1.242 | <0.001 | 0.004 |
| IMP/POP | -0.498 | <0.001 | 0.192 |
| MVA*MEDHTMVA/100 | 6.26e-08 | <0.001 | <0.001 |
| log(PATENTRE) | -2173 | 0.002 | 0.009 |
| EXP/LABOR | 0.573 | <0.001 | 0.016 |
| log(PATENTNONRE) | -1758 | <0.001 | 0.002 |
| RDEXP*GDP/100 | 2.81e-08 | 0.001 | <0.001 |
| RDPOP/LABOR | -9.98e+05 | 0.002 | 0.278 |

R-squared including country effects: 0.990. Within R-squared: 0.655.

High-tech exports, exports per worker, high-tech manufacturing and R&D spending are positively associated with GDP per capita, and these results hold with standard errors clustered by country. The negative effects of imports per capita and R&D personnel are no longer significant once serial correlation within countries is accounted for (the Durbin-Watson statistic in the thesis was 0.88), so they should be read with caution.

Country-level fitted versus actual graphs are in `results/figures/`, grouped by mean absolute percentage error in `results/fit_accuracy.csv`.

## Repository structure

```
data/raw/oecd_panel_raw.csv        World Bank series as compiled for the thesis
data/raw/Data_EXCELSIOR.xlsx       Original Excel workbook used for the thesis
data/processed/panel_clean.csv     Cleaned panel with model variables (generated)
src/prepare_data.py                Cleaning, data repairs, variable construction
src/estimate_model.py              Fixed-effects estimation and comparison with EViews
src/fitted_graphs.py               Actual vs fitted graphs and accuracy groups
results/                           Tables, repairs log and figures (generated)
docs/eviews_output.txt             Original EViews 10 output from the thesis
docs/changes_from_thesis.md        What differs from the thesis code and why
docs/thesis.pdf                    Full text of the thesis
```

## How to run

Python 3.10 or later.

```
pip install -r requirements.txt
python src/prepare_data.py
python src/estimate_model.py
python src/fitted_graphs.py
```

## Data notes

- Missing values in the World Bank export are marked `..`; they are treated as missing, never as zero.
- Some manufacturing value added (MVA) entries for Australia, Austria and Belgium lost their decimal separator during export, making them hundreds of times larger than GDP. `prepare_data.py` rescales them and logs every change in `results/mva_repairs.csv`. These are the same corrections used for the EViews estimation in the thesis.
- Australia contributes only one complete observation to the estimation sample.

## Citation

If you use this code or data, please cite the thesis (see `CITATION.cff`). Data: World Bank, World Development Indicators (CC BY 4.0).

## License

Code: MIT License. Data: World Bank terms (CC BY 4.0).
