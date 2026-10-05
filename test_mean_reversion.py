import pandas as pd
import numpy as np
from pathlib import Path


# -----------------------------------------
# SETTINGS
# -----------------------------------------

INPUT_FILE = Path(
    "data/rNVDA_1H_factors.csv"
)

OUTPUT_FILE = Path(
    "data/rNVDA_mean_reversion_development.csv"
)

DEVELOPMENT_DAYS = 60


print("====================================")
print("rFactor Lab - Mean Reversion Test")
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

df["momentum_6h_pct"] = (
    df["momentum_6h"] * 100
)

df = df.sort_values(
    "datetime_utc"
).reset_index(drop=True)


# -----------------------------------------
# DEVELOPMENT / OUT-OF-SAMPLE SPLIT
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
print("Development ends:", development_end)

print(
    df["sample"].value_counts()
)


# -----------------------------------------
# NEXT-HOUR RETURN
# -----------------------------------------

df["forward_return_1h"] = (
    df["close"].shift(-1)
    / df["close"]
    - 1
)


# -----------------------------------------
# PROTECT AGAINST MISSING CANDLES
# -----------------------------------------

valid_forward = (
    df["close"].notna()
    &
    df["close"].shift(-1).notna()
)

df.loc[
    ~valid_forward,
    "forward_return_1h"
] = np.nan


# -----------------------------------------
# CREATE MEAN-REVERSION SIGNAL
# -----------------------------------------

df["reversion_signal"] = np.nan


# Previous momentum positive
# → reversion expects next move DOWN

df.loc[
    df["momentum_6h"] > 0,
    "reversion_signal"
] = -1


# Previous momentum negative
# → reversion expects next move UP

df.loc[
    df["momentum_6h"] < 0,
    "reversion_signal"
] = 1


# -----------------------------------------
# REVERSION RETURN
# -----------------------------------------

df["reversion_return"] = (
    df["reversion_signal"]
    * df["forward_return_1h"]
)

df["reversion_return_pct"] = (
    df["reversion_return"] * 100
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

dev["reversion_correct"] = (
    dev["reversion_return"] > 0
)


# -----------------------------------------
# T-STAT FUNCTION
# -----------------------------------------

def calculate_t_stat(series):

    values = series.dropna()

    n = len(values)

    if n < 2:
        return np.nan

    std = values.std(ddof=1)

    if std == 0:
        return np.nan

    return (
        values.mean()
        /
        (std / np.sqrt(n))
    )


# -----------------------------------------
# RESULTS BY SESSION
# -----------------------------------------

summary = (
    dev.groupby("session")
    .agg(
        observations=(
            "reversion_return",
            "count"
        ),

        avg_reversion_return_pct=(
            "reversion_return_pct",
            "mean"
        ),

        median_reversion_return_pct=(
            "reversion_return_pct",
            "median"
        ),

        std_pct=(
            "reversion_return_pct",
            "std"
        ),

        hit_rate_pct=(
            "reversion_correct",
            lambda x: x.mean() * 100
        ),

        t_stat=(
            "reversion_return_pct",
            calculate_t_stat
        )
    )
)


print("\n3. MEAN REVERSION RESULTS")

print(
    summary.round(4)
)


# -----------------------------------------
# POSITIVE MOMENTUM REVERSAL
# -----------------------------------------

positive_momentum = dev[
    dev["momentum_6h"] > 0
]

positive_result = (
    positive_momentum
    .groupby("session")
    ["forward_return_1h"]
    .agg(
        [
            "count",
            "mean",
            "median",
            "std"
        ]
    )
)

positive_result[
    ["mean", "median", "std"]
] *= 100


print(
    "\n4. NEXT-HOUR RETURN AFTER "
    "POSITIVE MOMENTUM"
)

print(
    positive_result.round(4)
)


# -----------------------------------------
# NEGATIVE MOMENTUM REVERSAL
# -----------------------------------------

negative_momentum = dev[
    dev["momentum_6h"] < 0
]

negative_result = (
    negative_momentum
    .groupby("session")
    ["forward_return_1h"]
    .agg(
        [
            "count",
            "mean",
            "median",
            "std"
        ]
    )
)

negative_result[
    ["mean", "median", "std"]
] *= 100


print(
    "\n5. NEXT-HOUR RETURN AFTER "
    "NEGATIVE MOMENTUM"
)

print(
    negative_result.round(4)
)


# -----------------------------------------
# SAVE DEVELOPMENT RESULTS ONLY
# -----------------------------------------

dev.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n====================================")
print("MEAN REVERSION TEST COMPLETE")
print("====================================")

print(
    "Saved development data to:",
    OUTPUT_FILE
)

print(
    "Out-of-sample results remain hidden."
)