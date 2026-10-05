import pandas as pd
import numpy as np
from pathlib import Path


# =========================================================
# SETTINGS
# =========================================================

INPUT_FILE = Path(
    "data/weekend_dislocation_development.csv"
)

OUTPUT_FILE = Path(
    "data/candidate_strategy_validation.csv"
)

HORIZON = 3

# Cost sensitivity in percentage points.
# Example:
# 0.05 = 0.05% round-trip total cost.
COST_SCENARIOS = [
    0.00,
    0.05,
    0.10,
    0.20
]


print("====================================")
print("rFactor Lab")
print("Candidate Strategy Validation")
print("====================================")


# =========================================================
# LOAD
# =========================================================

df = pd.read_csv(INPUT_FILE)

df["signal_time"] = pd.to_datetime(
    df["signal_time"],
    utc=True
)

df["strategy_return_pct"] = pd.to_numeric(
    df["strategy_return_pct"],
    errors="coerce"
)


# =========================================================
# KEEP FIXED 3-HOUR CANDIDATE
# =========================================================

df = df[
    df["horizon_hours"] == HORIZON
].copy()


print(
    "\nCandidate trades:",
    len(df)
)


# =========================================================
# NEW YORK TIME
# =========================================================

df["signal_time_et"] = (
    df["signal_time"]
    .dt.tz_convert(
        "America/New_York"
    )
)


# =========================================================
# GROUP INTO WEEKEND CLUSTERS
# =========================================================

# Signal is on Saturday/Sunday.
# Move backward to most recent Friday.

df["signal_date"] = (
    df["signal_time_et"]
    .dt.date
)


df["weekday"] = (
    df["signal_time_et"]
    .dt.weekday
)


df["weekend_start"] = (
    df["signal_time_et"]
    -
    pd.to_timedelta(
        (
            df["weekday"] - 4
        ) % 7,
        unit="D"
    )
)


df["weekend_id"] = (
    df["weekend_start"]
    .dt.date
)


# =========================================================
# RAW TRADE SUMMARY
# =========================================================

print(
    "\n1. RAW 3-HOUR STRATEGY"
)

print(
    "Trades:",
    len(df)
)

print(
    "Mean:",
    round(
        df["strategy_return_pct"].mean(),
        4
    ),
    "%"
)

print(
    "Median:",
    round(
        df["strategy_return_pct"].median(),
        4
    ),
    "%"
)

print(
    "Hit rate:",
    round(
        (
            df["strategy_return_pct"] > 0
        ).mean() * 100,
        2
    ),
    "%"
)


# =========================================================
# WEEKEND CLUSTER PERFORMANCE
# =========================================================

clusters = (
    df.groupby("weekend_id")
    .agg(
        trades=(
            "strategy_return_pct",
            "count"
        ),

        mean_return_pct=(
            "strategy_return_pct",
            "mean"
        ),

        median_return_pct=(
            "strategy_return_pct",
            "median"
        )
    )
    .reset_index()
)


clusters["positive_weekend"] = (
    clusters["mean_return_pct"] > 0
)


print(
    "\n2. WEEKEND-LEVEL RESULTS\n"
)

print(
    clusters.round(4)
    .to_string(index=False)
)


print(
    "\nPositive weekends:",
    int(
        clusters[
            "positive_weekend"
        ].sum()
    ),
    "/",
    len(clusters)
)


print(
    "Weekend hit rate:",
    round(
        clusters[
            "positive_weekend"
        ].mean() * 100,
        2
    ),
    "%"
)


# =========================================================
# LEAVE-ONE-WEEKEND-OUT
# =========================================================

print(
    "\n3. LEAVE-ONE-WEEKEND-OUT"
)


loo_means = []


for weekend in clusters["weekend_id"]:

    subset = df[
        df["weekend_id"]
        != weekend
    ]


    mean_return = (
        subset[
            "strategy_return_pct"
        ].mean()
    )


    loo_means.append(
        mean_return
    )


    print(
        "Removed:",
        weekend,
        "| Mean:",
        round(
            mean_return,
            4
        ),
        "%"
    )


print(
    "\nMinimum LOO mean:",
    round(
        min(loo_means),
        4
    ),
    "%"
)

print(
    "Maximum LOO mean:",
    round(
        max(loo_means),
        4
    ),
    "%"
)


# =========================================================
# TRANSACTION COST SENSITIVITY
# =========================================================

print(
    "\n4. TRANSACTION-COST SENSITIVITY"
)


cost_results = []


for cost in COST_SCENARIOS:

    net_returns = (
        df["strategy_return_pct"]
        - cost
    )


    mean_return = (
        net_returns.mean()
    )

    median_return = (
        net_returns.median()
    )

    hit_rate = (
        (
            net_returns > 0
        ).mean()
        * 100
    )


    cost_results.append(
        {
            "round_trip_cost_pct":
            cost,

            "mean_net_return_pct":
            mean_return,

            "median_net_return_pct":
            median_return,

            "hit_rate_pct":
            hit_rate
        }
    )


cost_table = pd.DataFrame(
    cost_results
)


print(
    cost_table.round(4)
    .to_string(index=False)
)


# =========================================================
# ASSET CONTRIBUTION
# =========================================================

print(
    "\n5. ASSET CONTRIBUTION"
)


asset_summary = (
    df.groupby("asset")
    .agg(
        trades=(
            "strategy_return_pct",
            "count"
        ),

        mean_pct=(
            "strategy_return_pct",
            "mean"
        ),

        median_pct=(
            "strategy_return_pct",
            "median"
        ),

        positive_trades=(
            "strategy_return_pct",
            lambda x:
            (x > 0).sum()
        )
    )
)


asset_summary[
    "hit_rate_pct"
] = (
    asset_summary[
        "positive_trades"
    ]
    /
    asset_summary[
        "trades"
    ]
    * 100
)


print(
    asset_summary.round(4)
)


# =========================================================
# SAVE
# =========================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n====================================")
print("VALIDATION COMPLETE")
print("====================================")

print(
    "Hidden out-of-sample period "
    "was NOT used."
)