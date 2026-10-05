import pandas as pd
from pathlib import Path


# -----------------------------------------
# FILE PATHS
# -----------------------------------------

INPUT_FILE = Path("data/rNVDA_1H.csv")

OUTPUT_FILE = Path(
    "data/rNVDA_1H_prepared.csv"
)


print("====================================")
print("rFactor Lab - Data Preparation")
print("====================================")


# -----------------------------------------
# LOAD DATA
# -----------------------------------------

df = pd.read_csv(INPUT_FILE)

df["datetime_utc"] = pd.to_datetime(
    df["datetime_utc"],
    utc=True
)

df = df.sort_values("datetime_utc")

df = df.set_index("datetime_utc")


# -----------------------------------------
# CREATE COMPLETE HOURLY TIMELINE
# -----------------------------------------

full_timeline = pd.date_range(
    start=df.index.min(),
    end=df.index.max(),
    freq="1h",
    tz="UTC"
)

df = df.reindex(full_timeline)

df.index.name = "datetime_utc"


# -----------------------------------------
# MARK MISSING CANDLES
# -----------------------------------------

df["missing_candle"] = (
    df["close"].isna()
)


# -----------------------------------------
# CONVERT UTC → NEW YORK TIME
# -----------------------------------------

df["datetime_et"] = (
    df.index
    .tz_convert("America/New_York")
)


# -----------------------------------------
# EXTRA TIME INFORMATION
# -----------------------------------------

df["weekday"] = (
    df["datetime_et"]
    .dt.day_name()
)

df["hour_et"] = (
    df["datetime_et"]
    .dt.hour
)

df["minute_et"] = (
    df["datetime_et"]
    .dt.minute
)


# -----------------------------------------
# SESSION CLASSIFICATION
# -----------------------------------------

def classify_session(timestamp):

    weekday = timestamp.weekday()

    hour = timestamp.hour

    minute = timestamp.minute


    # Saturday or Sunday
    if weekday >= 5:

        return "Weekend"


    # 04:00 - 09:00
    if 4 <= hour < 9:

        return "Pre-Market"


    # 09:00 candle crosses the
    # 09:30 US market opening time.
    if hour == 9:

        return "Transition"


    # 10:00 - 15:59
    if 10 <= hour < 16:

        return "Regular"


    # 16:00 - 19:59
    if 16 <= hour < 20:

        return "After-Hours"


    # 20:00 - 03:59
    return "Overnight"


df["session"] = (
    df["datetime_et"]
    .apply(classify_session)
)


# -----------------------------------------
# CHECK SESSION COUNTS
# -----------------------------------------

print("\n1. SESSION COUNTS")

print(
    df["session"]
    .value_counts()
)


# -----------------------------------------
# CHECK MISSING CANDLES
# -----------------------------------------

print("\n2. MISSING CANDLES")

missing = df[
    df["missing_candle"]
]

print(
    "Missing hourly candles:",
    len(missing)
)


if len(missing) > 0:

    print("\nFirst 10 missing hours:\n")

    print(
        missing[
            [
                "datetime_et",
                "weekday",
                "session"
            ]
        ].head(10)
    )


# -----------------------------------------
# SAVE PREPARED DATA
# -----------------------------------------

df = df.reset_index()

df.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n====================================")
print("PREPARATION COMPLETE")
print("====================================")

print(
    "Rows:",
    len(df)
)

print(
    "Saved to:",
    OUTPUT_FILE
)