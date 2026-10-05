import pandas as pd
import numpy as np
from pathlib import Path


# -----------------------------------------
# SETTINGS
# -----------------------------------------

RTOKEN_FILE = Path(
    "data/rNVDA_1H_factors.csv"
)

STOCK_FILE = Path(
    "data/NVDA_1H_aligned.csv"
)

OUTPUT_FILE = Path(
    "data/rNVDA_NVDA_development_comparison.csv"
)

DEVELOPMENT_DAYS = 60

MOMENTUM_HOURS = 6


print("====================================")
print("rFactor Lab")
print("rNVDA vs NVDA Comparison")
print("====================================")


# -----------------------------------------
# LOAD rNVDA
# -----------------------------------------

rtoken = pd.read_csv(
    RTOKEN_FILE
)

rtoken["datetime_utc"] = pd.to_datetime(
    rtoken["datetime_utc"],
    utc=True
)

rtoken["close"] = pd.to_numeric(
    rtoken["close"],
    errors="coerce"
)

rtoken["momentum_6h"] = pd.to_numeric(
    rtoken["momentum_6h"],
    errors="coerce"
)


# -----------------------------------------
# DEVELOPMENT PERIOD
# -----------------------------------------

project_start = (
    rtoken["datetime_utc"].min()
)

development_end = (
    project_start
    + pd.Timedelta(
        days=DEVELOPMENT_DAYS
    )
)


print("\n1. DEVELOPMENT PERIOD")

print(
    "Project start:",
    project_start
)

print(
    "Development ends:",
    development_end
)


# Keep development period only

rtoken = rtoken[
    rtoken["datetime_utc"]
    < development_end
].copy()


# -----------------------------------------
# LOAD ALIGNED NVDA
# -----------------------------------------

stock = pd.read_csv(
    STOCK_FILE
)

stock["datetime_utc"] = pd.to_datetime(
    stock["datetime_utc"],
    utc=True
)

stock["close"] = pd.to_numeric(
    stock["close"],
    errors="coerce"
)


# -----------------------------------------
# DEVELOPMENT PERIOD ONLY
# -----------------------------------------

stock = stock[
    stock["datetime_utc"]
    < development_end
].copy()


print("\n2. NATIVE STOCK DATA")

print(
    "NVDA first:",
    stock["datetime_utc"].min()
)

print(
    "NVDA last:",
    stock["datetime_utc"].max()
)


# -----------------------------------------
# CALCULATE NVDA MOMENTUM
# -----------------------------------------

stock = stock.sort_values(
    "datetime_utc"
).reset_index(drop=True)


stock["stock_momentum_6h"] = (
    stock["close"]
    /
    stock["close"].shift(
        MOMENTUM_HOURS
    )
    - 1
)


# -----------------------------------------
# REQUIRE CONTINUOUS VALID HOURS
# -----------------------------------------

valid_window = (
    stock["close"]
    .notna()
    .rolling(
        MOMENTUM_HOURS + 1
    )
    .sum()
)


stock.loc[
    valid_window
    != MOMENTUM_HOURS + 1,
    "stock_momentum_6h"
] = np.nan


# -----------------------------------------
# PREPARE rNVDA COLUMNS
# -----------------------------------------

rtoken = rtoken.rename(
    columns={
        "close":
        "rtoken_close",

        "momentum_6h":
        "rtoken_momentum_6h"
    }
)


stock = stock.rename(
    columns={
        "close":
        "stock_close"
    }
)


# -----------------------------------------
# MERGE EXACT TIMESTAMPS
# -----------------------------------------

comparison = pd.merge(
    rtoken[
        [
            "datetime_utc",
            "session",
            "rtoken_close",
            "rtoken_momentum_6h"
        ]
    ],

    stock[
        [
            "datetime_utc",
            "stock_close",
            "stock_momentum_6h",
            "valid_hour"
        ]
    ],

    on="datetime_utc",

    how="inner"
)


# -----------------------------------------
# CONVERT TO %
# -----------------------------------------

comparison[
    "rtoken_momentum_pct"
] = (
    comparison[
        "rtoken_momentum_6h"
    ] * 100
)


comparison[
    "stock_momentum_pct"
] = (
    comparison[
        "stock_momentum_6h"
    ] * 100
)


# -----------------------------------------
# FACTOR DIVERGENCE
# -----------------------------------------

comparison[
    "momentum_divergence_pct"
] = (
    comparison[
        "rtoken_momentum_pct"
    ]
    -
    comparison[
        "stock_momentum_pct"
    ]
)


# -----------------------------------------
# PRICE DIFFERENCE
# -----------------------------------------

comparison[
    "price_gap_pct"
] = (
    (
        comparison[
            "rtoken_close"
        ]
        /
        comparison[
            "stock_close"
        ]
    )
    - 1
) * 100


# -----------------------------------------
# VALID OBSERVATIONS
# -----------------------------------------

valid = comparison[
    comparison[
        "rtoken_momentum_pct"
    ].notna()

    &

    comparison[
        "stock_momentum_pct"
    ].notna()

    &

    comparison[
        "stock_close"
    ].notna()

    &

    (
        comparison["session"]
        != "Transition"
    )
].copy()


print("\n3. VALID COMPARISONS")

print(
    "Comparable observations:",
    len(valid)
)


print("\nComparable rows by session:")

print(
    valid["session"]
    .value_counts()
)


# -----------------------------------------
# SUMMARY
# -----------------------------------------

summary = (
    valid.groupby(
        "session"
    )
    .agg(

        observations=(
            "momentum_divergence_pct",
            "count"
        ),

        rtoken_avg_momentum_pct=(
            "rtoken_momentum_pct",
            "mean"
        ),

        stock_avg_momentum_pct=(
            "stock_momentum_pct",
            "mean"
        ),

        avg_divergence_pct=(
            "momentum_divergence_pct",
            "mean"
        ),

        median_divergence_pct=(
            "momentum_divergence_pct",
            "median"
        ),

        avg_absolute_divergence_pct=(
            "momentum_divergence_pct",
            lambda x:
            x.abs().mean()
        ),

        std_divergence_pct=(
            "momentum_divergence_pct",
            "std"
        ),

        avg_price_gap_pct=(
            "price_gap_pct",
            "mean"
        )
    )
)


print(
    "\n4. FACTOR DIVERGENCE BY SESSION"
)

print(
    summary.round(4)
)


# -----------------------------------------
# CORRELATION
# -----------------------------------------

print(
    "\n5. MOMENTUM CORRELATION"
)


for session in sorted(
    valid["session"]
    .dropna()
    .unique()
):

    subset = valid[
        valid["session"]
        == session
    ]

    correlation = (
        subset[
            "rtoken_momentum_pct"
        ]
        .corr(
            subset[
                "stock_momentum_pct"
            ]
        )
    )

    print(
        session,
        ":",
        round(
            correlation,
            4
        )
    )


# -----------------------------------------
# SAME DIRECTION %
# -----------------------------------------

print(
    "\n6. MOMENTUM DIRECTION AGREEMENT"
)


for session in sorted(
    valid["session"]
    .dropna()
    .unique()
):

    subset = valid[
        valid["session"]
        == session
    ].copy()

    same_direction = (
        np.sign(
            subset[
                "rtoken_momentum_pct"
            ]
        )
        ==
        np.sign(
            subset[
                "stock_momentum_pct"
            ]
        )
    )

    agreement = (
        same_direction.mean()
        * 100
    )

    print(
        session,
        ":",
        round(
            agreement,
            2
        ),
        "%"
    )


# -----------------------------------------
# SAVE
# -----------------------------------------

valid.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n====================================")
print("COMPARISON COMPLETE")
print("====================================")

print(
    "Saved to:",
    OUTPUT_FILE
)

print(
    "Out-of-sample period "
    "remains hidden."
)