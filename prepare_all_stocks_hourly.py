import pandas as pd
from pathlib import Path


# -----------------------------------------
# STOCK FILES
# -----------------------------------------

STOCKS = {
    "NVDA": Path("data/NVDA_15m.csv"),
    "AAPL": Path("data/AAPL_15m.csv"),
    "TSLA": Path("data/TSLA_15m.csv")
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

    # 09:00 - 09:59 contains
    # the 09:30 regular-market opening
    if hour == 9:
        return "Transition"

    # 10:00 - 15:59
    if 10 <= hour < 16:
        return "Regular"

    # 16:00 - 19:59
    if 16 <= hour < 20:
        return "After-Hours"

    return "Closed"


# -----------------------------------------
# PREPARE ONE STOCK
# -----------------------------------------

def prepare_stock(ticker, input_file):

    print("\n====================================")
    print("Preparing:", ticker)
    print("====================================")

    df = pd.read_csv(input_file)

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


    # -------------------------------------
    # RESAMPLE TO EXACT 1-HOUR WINDOWS
    # -------------------------------------

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


    # -------------------------------------
    # VALID HOUR
    # -------------------------------------

    hourly["valid_hour"] = (
        hourly["bars_15m"] == 4
    )


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


    # -------------------------------------
    # NEW YORK TIME
    # -------------------------------------

    hourly["datetime_et"] = (
        hourly.index
        .tz_convert(
            "America/New_York"
        )
    )


    hourly["session"] = (
        hourly["datetime_et"]
        .apply(
            classify_session
        )
    )


    # -------------------------------------
    # RESET INDEX
    # -------------------------------------

    hourly = hourly.reset_index()

    hourly = hourly.rename(
        columns={
            "datetime": "datetime_utc"
        }
    )


    # -------------------------------------
    # RESULTS
    # -------------------------------------

    print(
        "Total hourly positions:",
        len(hourly)
    )

    print(
        "Valid hourly candles:",
        hourly["valid_hour"].sum()
    )


    print("\nValid hours by session:")

    print(
        hourly[
            hourly["valid_hour"]
        ]["session"]
        .value_counts()
    )


    # -------------------------------------
    # SAVE
    # -------------------------------------

    output_file = Path(
        f"data/{ticker}_1H_aligned.csv"
    )


    hourly.to_csv(
        output_file,
        index=False
    )


    print(
        "\nSaved to:",
        output_file
    )


# -----------------------------------------
# RUN ALL STOCKS
# -----------------------------------------

print("====================================")
print("rFactor Lab")
print("Multi-Stock Hourly Alignment")
print("====================================")


for ticker, file in STOCKS.items():

    prepare_stock(
        ticker,
        file
    )


print("\n====================================")
print("ALL STOCKS ALIGNED")
print("====================================")