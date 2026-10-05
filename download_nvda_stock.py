import yfinance as yf
import pandas as pd
from pathlib import Path


# -----------------------------------------
# SETTINGS
# -----------------------------------------

TICKER = "NVDA"

OUTPUT_FILE = Path(
    "data/NVDA_1H.csv"
)


print("====================================")
print("rFactor Lab - Native Stock Download")
print("====================================")

print("Ticker:", TICKER)


# -----------------------------------------
# DOWNLOAD NVDA DATA
# -----------------------------------------

stock = yf.Ticker(TICKER)

df = stock.history(
    period="60d",
    interval="1h",
    prepost=True,
    auto_adjust=False
)


# -----------------------------------------
# CHECK RESULT
# -----------------------------------------

if df.empty:

    print("\nNo stock data downloaded.")

    raise SystemExit


print(
    "\nRows downloaded:",
    len(df)
)


# -----------------------------------------
# MOVE DATETIME INDEX INTO COLUMN
# -----------------------------------------

df = df.reset_index()


# -----------------------------------------
# FIND DATETIME COLUMN
# -----------------------------------------

if "Datetime" in df.columns:

    df = df.rename(
        columns={"Datetime": "datetime"}
    )

elif "Date" in df.columns:

    df = df.rename(
        columns={"Date": "datetime"}
    )


# -----------------------------------------
# CONVERT TIME TO UTC
# -----------------------------------------

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


# -----------------------------------------
# KEEP REQUIRED COLUMNS
# -----------------------------------------

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


# -----------------------------------------
# SORT DATA
# -----------------------------------------

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
# SUMMARY
# -----------------------------------------

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


print("\nFirst 5 rows:\n")

print(
    df.head().to_string(
        index=False
    )
)


print("\n====================================")
print("DOWNLOAD COMPLETE")
print("====================================")