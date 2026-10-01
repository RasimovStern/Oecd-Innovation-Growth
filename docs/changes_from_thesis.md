# Changes from the thesis code

The thesis estimated the model in EViews 10 and drew the country graphs with a Python script (Appendix D). This repository keeps the same model and data but fixes a few problems in the graphing script and adds robustness checks.

## Estimation

- The model is re-estimated in Python with country fixed effects. Coefficients, standard errors, R-squared (0.9897), standard error of regression (2696) and sample size (386) match the EViews output.
- Regressors are rescaled before fitting because some are in the 10^13 range, which made the design matrix numerically unstable. Coefficients are converted back to the original units.
- Standard errors clustered by country are reported next to the conventional ones. With a Durbin-Watson statistic of 0.88 the residuals are serially correlated, so conventional standard errors understate uncertainty. Under clustering, imports per capita (p = 0.19) and R&D personnel per worker (p = 0.28) lose significance; the other six variables stay significant.
- The within R-squared (0.655) is reported as well. Most of the 0.99 overall R-squared comes from the country fixed effects.

## Graphs (Appendix D script)

1. **MVA repairs were not applied.** The script read the raw Excel sheet, where MVA for Australia, Austria and Belgium is inflated by a factor of 1,000-10,000. The EViews estimation used corrected values, but the graphs did not, which is why these three countries appeared in the low-accuracy group. With the corrected data, Austria and Belgium fit well (mean absolute percentage error about 3%).
2. **Missing values were set to zero** (`fillna(0)`), so years with a missing regressor got distorted fitted values. Fitted values are now left blank when an input is missing.
3. **Fixed effects were re-derived** from averaged pooled residuals. The script now uses the effects estimated by the model.
4. **2022-2024 values were drawn as fitted values**, although those years are outside the estimation period and use carried-forward innovation variables. They are now drawn separately as a projection.
5. **Accuracy groups were a fixed list.** Countries are now grouped by mean absolute percentage error: high below 5%, medium 5-10%, low above 10%.
6. Hard-coded local file paths were replaced with paths relative to the repository.
