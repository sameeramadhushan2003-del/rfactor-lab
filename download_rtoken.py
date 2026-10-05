import requests
import pandas as pd
import time

from datetime import datetime, timezone, timedelta
from pathlib import Path


# ----------------------------------------
# SETTINGS
# ----------------------------------------

SYMBOL = "rNVDAUSDT"

INTERVAL = "1H"

DAYS_TO_DOWNLOAD = 90

BASE_URL = "https://api.bitget.com"

ENDPOINT = "/api/v3/market/candles"


# ----------------------------------------
# CALCULATE TIME RANGE
# ----------------------------------------

end_time = datetime.now(timezone.utc)

start_time = end_time - timedelta(days=DAYS_TO_DOWNLOAD)

start_ms = int(start_time.timestamp() * 1000)

current_end_ms = int(end_time.timestamp() * 1000)


print("===================================")
print("rFactor Lab - rToken Downloader")
print("===================================")

print("Symbol:", SYMBOL)

print("Interval:", INTERVAL)

print("Requested start:", start_time)

print("Requested end:", end_time)

print()


# ----------------------------------------
# STORE DOWNLOADED CANDLES
# ----------------------------------------

all_candles = []


# ----------------------------------------
# DOWNLOAD DATA
# ----------------------------------------

while current_end_ms > start_ms:

    params = {
        "category": "SPOT",
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "type": "market",
        "endTime": str(current_end_ms),
        "limit": "1000"
    }

    try:

        response = requests.get(
            BASE_URL + ENDPOINT,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        result = response.json()

    except Exception as error:

        print("Request failed:")
        print(error)

        break


    # Check Bitget response

    if result.get("code") != "00000":

        print("Bitget returned an error:")

        print(result)

        break


    candles = result.get("data", [])


    if not candles:

        print("No more candles available.")

        break


    all_candles.extend(candles)


    # Find oldest timestamp in this batch

    oldest_timestamp = min(
        int(candle[0])
        for candle in candles
    )


    oldest_date = datetime.fromtimestamp(
        oldest_timestamp / 1000,
        tz=timezone.utc
    )


    print(
        "Downloaded:",
        len(candles),
        "candles | Oldest:",
        oldest_date
    )


    # Stop when we have passed our target date

    if oldest_timestamp <= start_ms:

        break


    # Move backwards in time

    current_end_ms = oldest_timestamp - 1


    # Small delay to be nice to the API

    time.sleep(0.2)


# ----------------------------------------
# CHECK DATA
# ----------------------------------------

if not all_candles:

    print("\nNo candle data downloaded.")

    raise SystemExit


# ----------------------------------------
# CONVERT TO DATAFRAME
# ----------------------------------------

df = pd.DataFrame(
    all_candles,
    columns=[
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "turnover"
    ]
)


# Convert timestamp to number

df["timestamp"] = pd.to_numeric(
    df["timestamp"]
)


# Remove duplicate candles

df = df.drop_duplicates(
    subset=["timestamp"]
)


# Keep only requested date range

df = df[
    df["timestamp"] >= start_ms
]


# Sort oldest → newest

df = df.sort_values(
    "timestamp"
)


# Convert numeric columns

numeric_columns = [
    "open",
    "high",
    "low",
    "close",
    "volume",
    "turnover"
]


for column in numeric_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# Create readable UTC time

df["datetime_utc"] = pd.to_datetime(
    df["timestamp"],
    unit="ms",
    utc=True
)


# Put readable date first

df = df[
    [
        "datetime_utc",
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "turnover"
    ]
]


# ----------------------------------------
# SAVE CSV
# ----------------------------------------

Path("data").mkdir(
    exist_ok=True
)


output_file = Path(
    "data/rNVDA_1H.csv"
)


df.to_csv(
    output_file,
    index=False
)


# ----------------------------------------
# FINAL INFORMATION
# ----------------------------------------

print("\n===================================")

print("DOWNLOAD COMPLETE")

print("===================================")

print("Total candles:", len(df))

print(
    "First candle:",
    df["datetime_utc"].iloc[0]
)

print(
    "Last candle:",
    df["datetime_utc"].iloc[-1]
)

print(
    "Saved to:",
    output_file
)