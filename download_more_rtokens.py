import requests
import pandas as pd
import time

from datetime import datetime, timezone
from pathlib import Path


# -----------------------------------------
# SETTINGS
# -----------------------------------------

ASSETS = {
    "rAAPLUSDT": "rAAPL_1H.csv",
    "rTSLAUSDT": "rTSLA_1H.csv"
}

INTERVAL = "1H"

BASE_URL = "https://api.bitget.com"

ENDPOINT = "/api/v3/market/candles"


# Use the SAME period as rNVDA
START_TIME = datetime(
    2026, 6, 27, 6, 0,
    tzinfo=timezone.utc
)

END_TIME = datetime(
    2026, 9, 25, 5, 0,
    tzinfo=timezone.utc
)


START_MS = int(
    START_TIME.timestamp() * 1000
)

END_MS = int(
    END_TIME.timestamp() * 1000
)


# -----------------------------------------
# DOWNLOAD FUNCTION
# -----------------------------------------

def download_asset(symbol, filename):

    print("\n====================================")
    print("Downloading:", symbol)
    print("====================================")

    current_end_ms = END_MS

    all_candles = []


    while current_end_ms > START_MS:

        params = {
            "category": "SPOT",
            "symbol": symbol,
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

            return


        if result.get("code") != "00000":

            print("Bitget error:")
            print(result)

            return


        candles = result.get(
            "data",
            []
        )


        if not candles:

            print(
                "No more candles found."
            )

            break


        all_candles.extend(
            candles
        )


        oldest_timestamp = min(
            int(candle[0])
            for candle in candles
        )


        oldest_date = (
            datetime.fromtimestamp(
                oldest_timestamp / 1000,
                tz=timezone.utc
            )
        )


        print(
            "Downloaded:",
            len(candles),
            "| Oldest:",
            oldest_date
        )


        if oldest_timestamp <= START_MS:

            break


        current_end_ms = (
            oldest_timestamp - 1
        )


        time.sleep(0.2)


    # -------------------------------------
    # CHECK
    # -------------------------------------

    if not all_candles:

        print(
            "No data downloaded for",
            symbol
        )

        return


    # -------------------------------------
    # CREATE DATAFRAME
    # -------------------------------------

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


    df["timestamp"] = pd.to_numeric(
        df["timestamp"]
    )


    df = df.drop_duplicates(
        subset=["timestamp"]
    )


    # Keep exact project period

    df = df[
        (df["timestamp"] >= START_MS)
        &
        (df["timestamp"] <= END_MS)
    ]


    df = df.sort_values(
        "timestamp"
    )


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


    df["datetime_utc"] = (
        pd.to_datetime(
            df["timestamp"],
            unit="ms",
            utc=True
        )
    )


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


    # -------------------------------------
    # SAVE
    # -------------------------------------

    output_file = Path(
        "data"
    ) / filename


    output_file.parent.mkdir(
        exist_ok=True
    )


    df.to_csv(
        output_file,
        index=False
    )


    # -------------------------------------
    # RESULTS
    # -------------------------------------

    print("\nDownload complete")

    print(
        "Total candles:",
        len(df)
    )

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


# -----------------------------------------
# RUN ALL ASSETS
# -----------------------------------------

print("====================================")
print("rFactor Lab - Multi rToken Download")
print("====================================")

print(
    "Start:",
    START_TIME
)

print(
    "End:",
    END_TIME
)


for symbol, filename in ASSETS.items():

    download_asset(
        symbol,
        filename
    )


print("\n====================================")
print("ALL DOWNLOADS COMPLETE")
print("====================================")