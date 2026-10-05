import pandas as pd
from pathlib import Path


# -----------------------------------------
# ASSETS
# -----------------------------------------

ASSETS = {
    "rNVDA": Path("data/rNVDA_1H.csv"),
    "rAAPL": Path("data/rAAPL_1H.csv"),
    "rTSLA": Path("data/rTSLA_1H.csv")
}


# -----------------------------------------
# SESSION CLASSIFICATION
# -----------------------------------------

def classify_session(timestamp):

    weekday = timestamp.weekday()
    hour = timestamp.hour

    # Saturday / Sunday
    if weekday >= 5:
        return "Weekend"

    # 04:00 - 08:59 ET
    if 4 <= hour < 9:
        return "Pre-Market"

    # Mixed hour:
    # 09:00 - 09:29 pre-market
    # 09:30 - 09:59 regular
    if hour == 9:
        return "Transition"

    # Regular session
    if 10 <= hour < 16:
        return "Regular"

    # After-hours
    if 16 <= hour < 20:
        return "After-Hours"

    # 20:00 - 03:59
    return "Overnight"


# -----------------------------------------
# PREPARE ONE ASSET
# -----------------------------------------

def prepare_asset(name, input_file):

    print("\n====================================")
    print("Preparing:", name)
    print("====================================")

    df = pd.read_csv(input_file)

    df["datetime_utc"] = pd.to_datetime(
        df["datetime_utc"],
        utc=True
    )

    df = df.sort_values(
        "datetime_utc"
    )

    # -------------------------------------
    # DUPLICATES
    # -------------------------------------

    duplicates = df.duplicated(
        subset=["timestamp"]
    ).sum()

    print("Duplicate candles:", duplicates)


    # -------------------------------------
    # PRICE VALIDATION
    # -------------------------------------

    invalid_high = df[
        (df["high"] < df["open"])
        |
        (df["high"] < df["close"])
        |
        (df["high"] < df["low"])
    ]

    invalid_low = df[
        (df["low"] > df["open"])
        |
        (df["low"] > df["close"])
        |
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


    # -------------------------------------
    # COMPLETE HOURLY TIMELINE
    # -------------------------------------

    df = df.set_index(
        "datetime_utc"
    )

    full_timeline = pd.date_range(
        start=df.index.min(),
        end=df.index.max(),
        freq="1h",
        tz="UTC"
    )

    df = df.reindex(
        full_timeline
    )

    df.index.name = "datetime_utc"


    # -------------------------------------
    # MISSING CANDLES
    # -------------------------------------

    df["missing_candle"] = (
        df["close"].isna()
    )

    missing_count = (
        df["missing_candle"].sum()
    )

    print(
        "Total hourly positions:",
        len(df)
    )

    print(
        "Missing hourly candles:",
        missing_count
    )

    print(
        "Available candles:",
        len(df) - missing_count
    )


    # -------------------------------------
    # NEW YORK TIME
    # -------------------------------------

    df["datetime_et"] = (
        df.index
        .tz_convert(
            "America/New_York"
        )
    )

    df["weekday"] = (
        df["datetime_et"]
        .dt.day_name()
    )

    df["session"] = (
        df["datetime_et"]
        .apply(
            classify_session
        )
    )


    # -------------------------------------
    # SESSION COUNTS
    # -------------------------------------

    print("\nSession counts:")

    print(
        df["session"]
        .value_counts()
    )


    # -------------------------------------
    # MISSING CANDLES BY SESSION
    # -------------------------------------

    missing = df[
        df["missing_candle"]
    ]

    print(
        "\nMissing candles by session:"
    )

    if len(missing) > 0:

        print(
            missing["session"]
            .value_counts()
        )

    else:

        print("None")


    # -------------------------------------
    # SAVE
    # -------------------------------------

    df = df.reset_index()

    output_file = Path(
        f"data/{name}_1H_prepared.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print(
        "\nSaved to:",
        output_file
    )


# -----------------------------------------
# RUN ALL ASSETS
# -----------------------------------------

print("====================================")
print("rFactor Lab")
print("Multi-Asset Data Preparation")
print("====================================")


for name, file in ASSETS.items():

    prepare_asset(
        name,
        file
    )


print("\n====================================")
print("ALL ASSETS PREPARED")
print("====================================")