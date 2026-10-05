import pandas as pd
from pathlib import Path


# -----------------------------------------
# FILES
# -----------------------------------------

INPUT_FILE = Path(
    "data/NVDA_15m.csv"
)

OUTPUT_FILE = Path(
    "data/NVDA_1H_aligned.csv"
)


print("====================================")
print("rFactor Lab - NVDA Hourly Alignment")
print("====================================")


# -----------------------------------------
# LOAD 15-MINUTE DATA
# -----------------------------------------

df = pd.read_csv(INPUT_FILE)

df["datetime"] = pd.to_datetime(
    df["datetime"],
    utc=True
)

numeric_columns = [
    "open",
    "high",
    "low",
    "close",
    "volume"
]

for column in numeric_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


df = df.sort_values(
    "datetime"
)

df = df.set_index(
    "datetime"
)


# -----------------------------------------
# CREATE EXACT 1-HOUR CANDLES
# -----------------------------------------

hourly = (
    df.resample(
        "1h",
        label="left",
        closed="left"
    )
    .agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        bars_15m=("close", "count")
    )
)


# -----------------------------------------
# REQUIRE ALL FOUR 15-MINUTE BARS
# -----------------------------------------

hourly["valid_hour"] = (
    hourly["bars_15m"] == 4
)


# If the hour does not contain all four
# 15-minute candles, do not use its price.

price_columns = [
    "open",
    "high",
    "low",
    "close"
]

hourly.loc[
    ~hourly["valid_hour"],
    price_columns
] = pd.NA


# -----------------------------------------
# NEW YORK TIME
# -----------------------------------------

hourly["datetime_et"] = (
    hourly.index
    .tz_convert("America/New_York")
)


# -----------------------------------------
# SESSION CLASSIFICATION
# -----------------------------------------

def classify_session(timestamp):

    weekday = timestamp.weekday()
    hour = timestamp.hour

    # Saturday / Sunday
    if weekday >= 5:
        return "Weekend"

    # 04:00 - 08:59
    if 4 <= hour < 9:
        return "Pre-Market"

    # 09:00 - 09:59 crosses 09:30 opening
    if hour == 9:
        return "Transition"

    # 10:00 - 15:59
    if 10 <= hour < 16:
        return "Regular"

    # 16:00 - 19:59
    if 16 <= hour < 20:
        return "After-Hours"

    return "Closed"


hourly["session"] = (
    hourly["datetime_et"]
    .apply(classify_session)
)


# -----------------------------------------
# RESET INDEX
# -----------------------------------------

hourly = hourly.reset_index()

hourly = hourly.rename(
    columns={
        "datetime": "datetime_utc"
    }
)


# -----------------------------------------
# RESULTS
# -----------------------------------------

print("\n1. TOTAL HOURLY POSITIONS")

print(
    "Rows:",
    len(hourly)
)


print("\n2. VALID 1-HOUR CANDLES")

print(
    hourly["valid_hour"]
    .value_counts()
)


print("\n3. VALID HOURS BY SESSION")

valid = hourly[
    hourly["valid_hour"]
]

print(
    valid["session"]
    .value_counts()
)


print("\n4. FIRST 10 VALID HOURS")

print(
    valid[
        [
            "datetime_utc",
            "datetime_et",
            "session",
            "open",
            "high",
            "low",
            "close",
            "bars_15m"
        ]
    ]
    .head(10)
    .to_string(index=False)
)


# -----------------------------------------
# SAVE
# -----------------------------------------

hourly.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n====================================")
print("ALIGNMENT COMPLETE")
print("====================================")

print(
    "Saved to:",
    OUTPUT_FILE
)