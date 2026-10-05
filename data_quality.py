import pandas as pd
from pathlib import Path

# -----------------------------------------
# FILE
# -----------------------------------------

FILE = Path("data/rNVDA_1H.csv")


print("====================================")
print("rFactor Lab - Data Quality Check")
print("====================================")


# -----------------------------------------
# LOAD DATA
# -----------------------------------------

df = pd.read_csv(FILE)

df["datetime_utc"] = pd.to_datetime(
    df["datetime_utc"],
    utc=True
)

df = df.sort_values("datetime_utc")


# -----------------------------------------
# BASIC INFORMATION
# -----------------------------------------

print("\n1. BASIC INFORMATION")

print("Total candles:", len(df))

print(
    "First candle:",
    df["datetime_utc"].iloc[0]
)

print(
    "Last candle:",
    df["datetime_utc"].iloc[-1]
)

date_range = (
    df["datetime_utc"].iloc[-1]
    - df["datetime_utc"].iloc[0]
)

print(
    "Historical coverage:",
    round(date_range.total_seconds() / 86400, 2),
    "days"
)


# -----------------------------------------
# DUPLICATES
# -----------------------------------------

print("\n2. DUPLICATE CHECK")

duplicates = df.duplicated(
    subset=["timestamp"]
).sum()

print("Duplicate candles:", duplicates)


# -----------------------------------------
# MISSING VALUES
# -----------------------------------------

print("\n3. MISSING VALUES")

print(
    df[
        [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "turnover"
        ]
    ].isna().sum()
)


# -----------------------------------------
# ZERO VOLUME
# -----------------------------------------

print("\n4. ZERO VOLUME")

zero_volume = (
    df["volume"] == 0
).sum()

print(
    "Candles with zero volume:",
    zero_volume
)


# -----------------------------------------
# PRICE VALIDATION
# -----------------------------------------

print("\n5. PRICE VALIDATION")

invalid_high = df[
    (df["high"] < df["open"]) |
    (df["high"] < df["close"]) |
    (df["high"] < df["low"])
]

invalid_low = df[
    (df["low"] > df["open"]) |
    (df["low"] > df["close"]) |
    (df["low"] > df["high"])
]

print(
    "Invalid HIGH candles:",
    len(invalid_high)
)

print(
    "Invalid LOW candles:",
    len(invalid_low)
)


# -----------------------------------------
# FIND MISSING HOURS
# -----------------------------------------

print("\n6. TIME GAP CHECK")

df["time_difference"] = (
    df["datetime_utc"].diff()
)

gaps = df[
    df["time_difference"]
    > pd.Timedelta(hours=1)
].copy()


print(
    "Number of gaps:",
    len(gaps)
)


if len(gaps) > 0:

    print("\nFirst 10 gaps:\n")

    for index, row in gaps.head(10).iterrows():

        current_time = row["datetime_utc"]

        previous_time = df.loc[
            index - 1,
            "datetime_utc"
        ]

        gap_hours = (
            current_time - previous_time
        ).total_seconds() / 3600

        print(
            previous_time,
            "→",
            current_time,
            "| Gap:",
            gap_hours,
            "hours"
        )


# -----------------------------------------
# FINAL SUMMARY
# -----------------------------------------

print("\n====================================")
print("QUALITY CHECK COMPLETE")
print("====================================")