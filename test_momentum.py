import pandas as pd
import numpy as np
from pathlib import Path


# -----------------------------------------
# SETTINGS
# -----------------------------------------

INPUT_FILE = Path(
    "data/rNVDA_1H_factors.csv"
)

DEVELOPMENT_DAYS = 60


print("====================================")
print("rFactor Lab - Momentum Test")
print("====================================")


# -----------------------------------------
# LOAD DATA
# -----------------------------------------

df = pd.read_csv(INPUT_FILE)

df["datetime_utc"] = pd.to_datetime(
    df["datetime_utc"],
    utc=True
)

df["close"] = pd.to_numeric(
    df["close"],
    errors="coerce"
)

df["momentum_6h"] = pd.to_numeric(
    df["momentum_6h"],
    errors="coerce"
)

df = df.sort_values(
    "datetime_utc"
).reset_index(drop=True)


# -----------------------------------------
# CREATE DEVELOPMENT / TEST SPLIT
# -----------------------------------------

start_time = df["datetime_utc"].min()

development_end = (
    start_time
    + pd.Timedelta(days=DEVELOPMENT_DAYS)
)


df["sample"] = "Out-of-Sample"

df.loc[
    df["datetime_utc"] < development_end,
    "sample"
] = "Development"


print("\n1. DATA SPLIT")

print("Start:", start_time)

print(
    "Development ends:",
    development_end
)

print(
    df["sample"].value_counts()
)


# -----------------------------------------
# CALCULATE NEXT-HOUR RETURN
# -----------------------------------------

df["forward_return_1h"] = (
    df["close"].shift(-1)
    / df["close"]
    - 1
)


# -----------------------------------------
# INVALIDATE RETURNS AROUND MISSING DATA
# -----------------------------------------

current_valid = (
    df["close"].notna()
)

next_valid = (
    df["close"]
    .shift(-1)
    .notna()
)

valid_forward_return = (
    current_valid
    & next_valid
)

df.loc[
    ~valid_forward_return,
    "forward_return_1h"
] = pd.NA


# -----------------------------------------
# CREATE MOMENTUM DIRECTION
# -----------------------------------------

df["momentum_sign"] = np.nan

df.loc[
    df["momentum_6h"] > 0,
    "momentum_sign"
] = 1

df.loc[
    df["momentum_6h"] < 0,
    "momentum_sign"
] = -1


# -----------------------------------------
# MOMENTUM CONTINUATION TEST
# -----------------------------------------

# If momentum is positive:
# future positive return = success
#
# If momentum is negative:
# future negative return = success

df["continuation_return"] = (
    df["momentum_sign"]
    * df["forward_return_1h"]
)


# Percentage values for display

df["forward_return_1h_pct"] = (
    df["forward_return_1h"]
    * 100
)

df["continuation_return_pct"] = (
    df["continuation_return"]
    * 100
)


# -----------------------------------------
# USE DEVELOPMENT DATA ONLY
# -----------------------------------------

dev = df[
    (df["sample"] == "Development")
    &
    (df["session"] != "Transition")
    &
    (df["momentum_6h"].notna())
    &
    (df["forward_return_1h"].notna())
].copy()


print("\n2. DEVELOPMENT OBSERVATIONS")

print(
    "Valid observations:",
    len(dev)
)


# -----------------------------------------
# HIT RATE
# -----------------------------------------

dev["momentum_correct"] = (
    dev["continuation_return"] > 0
)


# -----------------------------------------
# SUMMARY BY SESSION
# -----------------------------------------

summary = (
    dev.groupby("session")
    .agg(
        observations=(
            "continuation_return",
            "count"
        ),

        avg_continuation_return_pct=(
            "continuation_return_pct",
            "mean"
        ),

        median_continuation_return_pct=(
            "continuation_return_pct",
            "median"
        ),

        hit_rate_pct=(
            "momentum_correct",
            lambda x: x.mean() * 100
        )
    )
)


print(
    "\n3. MOMENTUM PREDICTIVE TEST"
)

print(
    summary.round(4)
)


# -----------------------------------------
# POSITIVE MOMENTUM ONLY
# -----------------------------------------

positive = dev[
    dev["momentum_sign"] == 1
]

positive_summary = (
    positive.groupby("session")
    ["forward_return_1h_pct"]
    .agg(
        [
            "count",
            "mean",
            "median",
            "std"
        ]
    )
)


print(
    "\n4. AFTER POSITIVE MOMENTUM"
)

print(
    positive_summary.round(4)
)


# -----------------------------------------
# NEGATIVE MOMENTUM ONLY
# -----------------------------------------

negative = dev[
    dev["momentum_sign"] == -1
]

negative_summary = (
    negative.groupby("session")
    ["forward_return_1h_pct"]
    .agg(
        [
            "count",
            "mean",
            "median",
            "std"
        ]
    )
)


print(
    "\n5. AFTER NEGATIVE MOMENTUM"
)

print(
    negative_summary.round(4)
)


print("\n====================================")
print("DEVELOPMENT TEST COMPLETE")
print("====================================")

print(
    "IMPORTANT: Out-of-sample results "
    "were NOT displayed."
)