import yfinance as yf
import pandas as pd
from pathlib import Path


# -----------------------------------------
# SETTINGS
# -----------------------------------------

TICKER = "NVDA"

OUTPUT_FILE = Path(
    "data/NVDA_15m.csv"
)


print("====================================")
print("rFactor Lab - NVDA 15m Download")
print("====================================")

print("Ticker:", TICKER)


# -----------------------------------------
# DOWNLOAD
# -----------------------------------------

stock = yf.Ticker(TICKER)

df = stock.history(
    period="60d",
    interval="15m",
    prepost=True,
    auto_adjust=False
)


if df.empty:

    print("No data downloaded.")

    raise SystemExit


# -----------------------------------------
# PREPARE DATA
# -----------------------------------------

df = df.reset_index()


if "Datetime" in df.columns:

    df = df.rename(
        columns={"Datetime": "datetime"}
    )


df["datetime"] = pd.to_datetime(
    df["datetime"],
    utc=True
)


df = df.rename(
    columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    }
)


df = df[
    [
        "datetime",
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]
]


df = df.sort_values(
    "datetime"
)


# -----------------------------------------
# SAVE
# -----------------------------------------

Path("data").mkdir(
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# -----------------------------------------
# RESULTS
# -----------------------------------------

print("\nRows downloaded:", len(df))

print(
    "First candle:",
    df["datetime"].iloc[0]
)

print(
    "Last candle:",
    df["datetime"].iloc[-1]
)

print(
    "Saved to:",
    OUTPUT_FILE
)


print("\nFirst 10 timestamps:\n")

print(
    df[
        [
            "datetime",
            "close"
        ]
    ]
    .head(10)
    .to_string(index=False)
)


print("\n====================================")
print("DOWNLOAD COMPLETE")
print("====================================")