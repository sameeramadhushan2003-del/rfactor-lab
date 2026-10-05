# rFactor Lab — Factor Autopsy

## Final Factor

**Factor:** 1-hour cross-sectional momentum

**Observed behaviour:** Short-term mean reversion

Recent relative losers tended to outperform recent relative winners during the following hour.

## Factor Validation

- **Development**: Mean IC = -0.0744, Median IC = -0.0819, Observations = 3762
- **Validation**: Mean IC = -0.0351, Median IC = -0.0286, Observations = 893
- **FinalTimeHoldout**: Mean IC = -0.0708, Median IC = -0.0872, Observations = 1066
- **FinalAssetHoldout**: Mean IC = -0.0812, Median IC = -0.5000, Observations = 1059

## Interpretation

The factor maintained a negative IC during development, validation, future-time holdout, and separate-asset holdout testing.

This supports a persistent cross-sectional short-term reversal relationship.

## Portfolio Implementation

Portfolio rule:
- Long bottom 25% of previous-hour momentum
- Short top 25%
- Approximately market-neutral
- Maximum hourly turnover = 0.50

## Gross Performance

- **Validation6**: 2.88% cumulative return, -7.91% max drawdown
- **FinalTime20**: 13.36% cumulative return, -5.36% max drawdown
- **FinalAsset3**: 21.72% cumulative return, -5.15% max drawdown

## Cost Sensitivity — 2.5 bps One-Way Assumption

- **Validation6**: -7.96% cumulative return
- **FinalTime20**: -0.78% cumulative return
- **FinalAsset3**: 6.91% cumulative return

## Autopsy Finding

**Factor status: VALIDATED**

**Economic implementation status: COST-SENSITIVE**

The predictive relationship survived multiple out-of-sample tests, but frequent portfolio rebalancing produced substantial turnover.

Transaction-cost sensitivity therefore represents the primary limitation of the current implementation.

The results demonstrate why statistical factor strength and real trading profitability should be evaluated separately.

## Research Discipline

The final factor was frozen before validation. Validation and holdout results were not used to change the factor.

Execution experiments were performed only after factor validation and are reported separately.