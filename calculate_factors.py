import pandas as pd
from pathlib import Path


# -----------------------------------------
# SETTINGS
# -----------------------------------------

INPUT_FILE = Path(
    "data/rNVDA_1H_prepared.csv"
)

OUTPUT_FILE = Path(
    "data/rNVDA_1H_factors.csv"
)

MOMENTUM_HOURS = 6


print("====================================")
print("rFactor Lab - Factor Calculation")
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

df = df.sort_values(
    "datetime_utc"
).reset_index(drop=True)


# -----------------------------------------
# 1-HOUR RETURN
# -----------------------------------------

df["return_1h"] = (
    df["close"]
    / df["close"].shift(1)
    - 1
)


# -----------------------------------------
# REMOVE RETURNS ACROSS MISSING CANDLES
# -----------------------------------------

current_valid = df["close"].notna()

previous_valid = (
    df["close"]
    .shift(1)
    .notna()
)

valid_1h_return = (
    current_valid
    & previous_valid
)

df.loc[
    ~valid_1h_return,
    "return_1h"
] = pd.NA


# -----------------------------------------
# 6-HOUR MOMENTUM
# -----------------------------------------

df["momentum_6h"] = (
    df["close"]
    / df["close"].shift(MOMENTUM_HOURS)
    - 1
)


# -----------------------------------------
# CHECK FOR MISSING DATA INSIDE
# THE 6-HOUR MOMENTUM WINDOW
# -----------------------------------------

valid_prices_in_window = (
    df["close"]
    .notna()
    .rolling(
        MOMENTUM_HOURS + 1
    )
    .sum()
)

valid_momentum = (
    valid_prices_in_window
    == MOMENTUM_HOURS + 1
)

df.loc[
    ~valid_momentum,
    "momentum_6h"
] = pd.NA


# -----------------------------------------
# CONVERT TO PERCENTAGES FOR DISPLAY
# -----------------------------------------

df["return_1h_pct"] = (
    df["return_1h"] * 100
)

df["momentum_6h_pct"] = (
    df["momentum_6h"] * 100
)


# -----------------------------------------
# BASIC RESULTS
# -----------------------------------------

print("\n1. VALID FACTOR VALUES")

print(
    "Valid hourly returns:",
    df["return_1h"].notna().sum()
)

print(
    "Valid 6-hour momentum values:",
    df["momentum_6h"].notna().sum()
)


# -----------------------------------------
# MOMENTUM BY MARKET SESSION
# -----------------------------------------

print("\n2. AVERAGE 6-HOUR MOMENTUM BY SESSION")

session_momentum = (
    df.groupby("session")
    ["momentum_6h_pct"]
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
    session_momentum.round(4)
)


# -----------------------------------------
# POSITIVE VS NEGATIVE MOMENTUM
# -----------------------------------------

df["momentum_direction"] = pd.NA

df.loc[
    df["momentum_6h"] > 0,
    "momentum_direction"
] = "Positive"

df.loc[
    df["momentum_6h"] < 0,
    "momentum_direction"
] = "Negative"

df.loc[
    df["momentum_6h"] == 0,
    "momentum_direction"
] = "Flat"


print("\n3. MOMENTUM DIRECTION COUNTS")

print(
    pd.crosstab(
        df["session"],
        df["momentum_direction"]
    )
)


# -----------------------------------------
# SHOW SAMPLE
# -----------------------------------------

print("\n4. SAMPLE FACTOR DATA")

sample_columns = [
    "datetime_utc",
    "session",
    "close",
    "return_1h_pct",
    "momentum_6h_pct"
]

print(
    df[
        sample_columns
    ]
    .dropna()
    .head(10)
    .to_string(index=False)
)


# -----------------------------------------
# SAVE
# -----------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n====================================")
print("FACTOR CALCULATION COMPLETE")
print("====================================")

print(
    "Saved to:",
    OUTPUT_FILE
)