import pandas as pd
from pathlib import Path


# =========================================================
# FILES
# =========================================================

DEV_FILE = Path(
    "data/v2_development_factor_candidates.csv"
)

VALIDATION_IC = Path(
    "data/v2_validation_reversal_ic.csv"
)

TIME_IC = Path(
    "data/v2_final_time_holdout_ic.csv"
)

ASSET_IC = Path(
    "data/v2_final_asset_holdout_ic.csv"
)

EXECUTION_FILE = Path(
    "data/v2_turnover_cap_final_validation.csv"
)

OUTPUT_MD = Path(
    "factor_autopsy_report.md"
)

OUTPUT_CSV = Path(
    "data/factor_autopsy_summary.csv"
)


print("====================================")
print("rFactor Lab")
print("Factor Autopsy")
print("====================================")


# =========================================================
# IC SUMMARY FUNCTION
# =========================================================

def summarize_ic(file):

    df = pd.read_csv(file)

    values = pd.to_numeric(
        df["ic"],
        errors="coerce"
    ).dropna()

    return {
        "timestamps": len(values),

        "mean_ic": values.mean(),

        "median_ic": values.median(),

        "negative_rate_pct":
        (values < 0).mean() * 100
    }


# =========================================================
# DEVELOPMENT RESULT
# =========================================================

dev = pd.read_csv(
    DEV_FILE
)


candidate = dev[
    (
        dev["factor"]
        ==
        "momentum_1h"
    )
    &
    (
        dev["target"]
        ==
        "forward_return_1h"
    )
].iloc[0]


development_result = {
    "timestamps":
    candidate["timestamps"],

    "mean_ic":
    candidate["mean_ic"],

    "median_ic":
    candidate["median_ic"]
}


# =========================================================
# OTHER FACTOR TESTS
# =========================================================

validation_result = summarize_ic(
    VALIDATION_IC
)

time_result = summarize_ic(
    TIME_IC
)

asset_result = summarize_ic(
    ASSET_IC
)


# =========================================================
# FACTOR SUMMARY
# =========================================================

factor_rows = [
    {
        "stage": "Development",
        **development_result
    },

    {
        "stage": "Validation",
        **validation_result
    },

    {
        "stage": "FinalTimeHoldout",
        **time_result
    },

    {
        "stage": "FinalAssetHoldout",
        **asset_result
    }
]


factor_summary = pd.DataFrame(
    factor_rows
)


factor_summary.to_csv(
    OUTPUT_CSV,
    index=False
)


# =========================================================
# EXECUTION RESULTS
# =========================================================

execution = pd.read_csv(
    EXECUTION_FILE
)


execution_0 = execution[
    execution["cost_bps"] == 0
]


execution_25 = execution[
    execution["cost_bps"] == 2.5
]


# =========================================================
# DISPLAY FACTOR
# =========================================================

print("\nFACTOR VALIDATION\n")


print(
    factor_summary
    .round(4)
    .to_string(index=False)
)


print(
    "\nEXECUTION — 0 BPS\n"
)


print(
    execution_0[
        [
            "test",
            "cumulative_return_pct",
            "max_drawdown_pct",
            "avg_turnover",
            "annualized_sharpe_naive"
        ]
    ]
    .round(4)
    .to_string(index=False)
)


print(
    "\nEXECUTION — 2.5 BPS\n"
)


print(
    execution_25[
        [
            "test",
            "cumulative_return_pct",
            "max_drawdown_pct",
            "avg_turnover",
            "annualized_sharpe_naive"
        ]
    ]
    .round(4)
    .to_string(index=False)
)


# =========================================================
# MARKDOWN REPORT
# =========================================================

lines = []

lines.append(
    "# rFactor Lab — Factor Autopsy\n"
)

lines.append(
    "## Final Factor\n"
)

lines.append(
    "**Factor:** 1-hour cross-sectional momentum\n"
)

lines.append(
    "**Observed behaviour:** Short-term mean reversion\n"
)

lines.append(
    "Recent relative losers tended to outperform "
    "recent relative winners during the following hour.\n"
)


lines.append(
    "## Factor Validation\n"
)


for _, row in factor_summary.iterrows():

    lines.append(
        f"- **{row['stage']}**: "
        f"Mean IC = {row['mean_ic']:.4f}, "
        f"Median IC = {row['median_ic']:.4f}, "
        f"Observations = {int(row['timestamps'])}"
    )


lines.append(
    "\n## Interpretation\n"
)

lines.append(
    "The factor maintained a negative IC during "
    "development, validation, future-time holdout, "
    "and separate-asset holdout testing."
)

lines.append(
    "\nThis supports a persistent cross-sectional "
    "short-term reversal relationship."
)


lines.append(
    "\n## Portfolio Implementation\n"
)

lines.append(
    "Portfolio rule:"
)

lines.append(
    "- Long bottom 25% of previous-hour momentum"
)

lines.append(
    "- Short top 25%"
)

lines.append(
    "- Approximately market-neutral"
)

lines.append(
    "- Maximum hourly turnover = 0.50"
)


lines.append(
    "\n## Gross Performance\n"
)


for _, row in execution_0.iterrows():

    lines.append(
        f"- **{row['test']}**: "
        f"{row['cumulative_return_pct']:.2f}% cumulative return, "
        f"{row['max_drawdown_pct']:.2f}% max drawdown"
    )


lines.append(
    "\n## Cost Sensitivity — 2.5 bps One-Way Assumption\n"
)


for _, row in execution_25.iterrows():

    lines.append(
        f"- **{row['test']}**: "
        f"{row['cumulative_return_pct']:.2f}% cumulative return"
    )


lines.append(
    "\n## Autopsy Finding\n"
)

lines.append(
    "**Factor status: VALIDATED**"
)

lines.append(
    "\n**Economic implementation status: COST-SENSITIVE**"
)

lines.append(
    "\nThe predictive relationship survived multiple "
    "out-of-sample tests, but frequent portfolio "
    "rebalancing produced substantial turnover."
)

lines.append(
    "\nTransaction-cost sensitivity therefore represents "
    "the primary limitation of the current implementation."
)

lines.append(
    "\nThe results demonstrate why statistical factor "
    "strength and real trading profitability should "
    "be evaluated separately."
)

lines.append(
    "\n## Research Discipline\n"
)

lines.append(
    "The final factor was frozen before validation. "
    "Validation and holdout results were not used to "
    "change the factor."
)

lines.append(
    "\nExecution experiments were performed only after "
    "factor validation and are reported separately."
)


OUTPUT_MD.write_text(
    "\n".join(lines),
    encoding="utf-8"
)


print("\n====================================")
print("AUTOPSY COMPLETE")
print("====================================")

print(
    "Report:",
    OUTPUT_MD
)

print(
    "Summary:",
    OUTPUT_CSV
)