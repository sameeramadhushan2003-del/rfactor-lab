import json
import pandas as pd
from pathlib import Path


DATA = Path("data")

OUTPUT = Path(
    "frontend/public/data"
)

OUTPUT.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================================
# FACTOR VALIDATION SUMMARY
# =========================================================

autopsy = pd.read_csv(
    DATA / "factor_autopsy_summary.csv"
)


validation_rows = []


for _, row in autopsy.iterrows():

    validation_rows.append(
        {
            "stage": str(row["stage"]),
            "timestamps": int(row["timestamps"]),
            "meanIC": round(float(row["mean_ic"]), 4),
            "medianIC": round(float(row["median_ic"]), 4),
            "negativeRate": (
                None
                if pd.isna(row.get("negative_rate_pct"))
                else round(
                    float(row["negative_rate_pct"]),
                    2
                )
            )
        }
    )


# =========================================================
# DEVELOPMENT FOLDS
# =========================================================

candidates = pd.read_csv(
    DATA /
    "v2_development_factor_candidates.csv"
)


candidate = candidates[
    (
        candidates["factor"]
        ==
        "momentum_1h"
    )
    &
    (
        candidates["target"]
        ==
        "forward_return_1h"
    )
].iloc[0]


folds = [
    {
        "name": "Fold 1",
        "ic": round(
            float(candidate["Fold_1"]),
            4
        )
    },
    {
        "name": "Fold 2",
        "ic": round(
            float(candidate["Fold_2"]),
            4
        )
    },
    {
        "name": "Fold 3",
        "ic": round(
            float(candidate["Fold_3"]),
            4
        )
    },
    {
        "name": "Fold 4",
        "ic": round(
            float(candidate["Fold_4"]),
            4
        )
    }
]


# =========================================================
# EXECUTION
# =========================================================

execution = pd.read_csv(
    DATA /
    "v2_turnover_cap_final_validation.csv"
)


execution_rows = []


for _, row in execution.iterrows():

    execution_rows.append(
        {
            "test": str(row["test"]),
            "costBps": float(row["cost_bps"]),
            "returnPct": round(
                float(row["cumulative_return_pct"]),
                4
            ),
            "drawdownPct": round(
                float(row["max_drawdown_pct"]),
                4
            ),
            "turnover": round(
                float(row["avg_turnover"]),
                4
            ),
            "sharpe": round(
                float(row["annualized_sharpe_naive"]),
                4
            )
        }
    )


# =========================================================
# FINAL JSON
# =========================================================

dashboard_data = {
    "factor": {
        "name": "1H Cross-Sectional Reversal",
        "signal": "momentum_1h",
        "target": "forward_return_1h",
        "direction": "Negative",
        "status": "Validated"
    },

    "validation": validation_rows,

    "folds": folds,

    "execution": execution_rows
}


with open(
    OUTPUT / "research.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        dashboard_data,
        file,
        indent=2
    )


print(
    "Dashboard data exported to:",
    OUTPUT / "research.json"
)