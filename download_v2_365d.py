import requests
import pandas as pd
import time

from datetime import datetime, timezone
from pathlib import Path


# =========================================================
# SETTINGS
# =========================================================

UNIVERSE_FILE = Path(
    "data/long_history_universe.csv"
)

OUTPUT_FOLDER = Path(
    "data/v2_raw"
)

MANIFEST_FILE = Path(
    "data/v2_download_manifest.csv"
)

BASE_URL = "https://api.bitget.com"

ENDPOINT = "/api/v3/market/candles"

INTERVAL = "1H"


# =========================================================
# EXACT 365-DAY RESEARCH PERIOD
# =========================================================

START_TIME = datetime(
    2025, 9, 25, 6, 0,
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


EXPECTED_HOURS = int(
    (
        END_TIME
        -
        START_TIME
    ).total_seconds()
    / 3600
) + 1


OUTPUT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


print("====================================")
print("rFactor Lab")
print("V2 - 365 Day Downloader")
print("====================================")

print(
    "\nPeriod:",
    START_TIME,
    "→",
    END_TIME
)

print(
    "Expected hourly positions:",
    EXPECTED_HOURS
)


# =========================================================
# LOAD 24-ASSET UNIVERSE
# =========================================================

universe = pd.read_csv(
    UNIVERSE_FILE
)


print(
    "\nAssets:",
    len(universe)
)


# =========================================================
# DOWNLOAD ONE ASSET
# =========================================================

def download_asset(
    symbol,
    ticker
):

    output_file = (
        OUTPUT_FOLDER
        /
        f"{ticker}_365d_1H.csv"
    )


    print("\n------------------------------------")
    print(symbol, "→", ticker)
    print("------------------------------------")


    # -----------------------------------------------------
    # RESUME SUPPORT
    # -----------------------------------------------------

    if output_file.exists():

        existing = pd.read_csv(
            output_file
        )

        print(
            "Already exists:",
            len(existing),
            "rows"
        )

        return {
            "status": "existing",
            "rows": len(existing),
            "file": str(output_file)
        }


    current_end = END_MS

    all_candles = []


    # =====================================================
    # MULTIPLE API BATCHES
    # =====================================================

    while current_end >= START_MS:

        params = {
            "category": "SPOT",
            "symbol": symbol,
            "interval": INTERVAL,
            "type": "market",
            "endTime": str(current_end),
            "limit": "1000"
        }


        success = False


        # Retry request up to 3 times
        for attempt in range(3):

            try:

                response = requests.get(
                    BASE_URL + ENDPOINT,
                    params=params,
                    timeout=25
                )

                response.raise_for_status()

                result = response.json()


                if (
                    result.get("code")
                    != "00000"
                ):

                    raise Exception(
                        result
                    )


                success = True

                break


            except Exception as error:

                print(
                    "Attempt",
                    attempt + 1,
                    "failed:"
                )

                print(error)

                time.sleep(2)


        if not success:

            return {
                "status": "error",
                "rows": 0,
                "file": str(output_file)
            }


        candles = result.get(
            "data",
            []
        )


        if not candles:

            break


        all_candles.extend(
            candles
        )


        timestamps = [
            int(candle[0])
            for candle in candles
        ]


        oldest = min(
            timestamps
        )


        oldest_date = (
            datetime.fromtimestamp(
                oldest / 1000,
                tz=timezone.utc
            )
        )


        print(
            "Batch:",
            len(candles),
            "| Oldest:",
            oldest_date
        )


        # We reached our required start
        if oldest <= START_MS:

            break


        current_end = (
            oldest - 1
        )


        # Gentle API pacing
        time.sleep(0.15)


    # =====================================================
    # CHECK
    # =========================================================

    if not all_candles:

        return {
            "status": "empty",
            "rows": 0,
            "file": str(output_file)
        }


    # =====================================================
    # DATAFRAME
    # =========================================================

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
        df["timestamp"],
        errors="coerce"
    )


    df = df.dropna(
        subset=[
            "timestamp"
        ]
    )


    df["timestamp"] = (
        df["timestamp"]
        .astype("int64")
    )


    # =====================================================
    # REMOVE DUPLICATES
    # =========================================================

    df = df.drop_duplicates(
        subset=[
            "timestamp"
        ]
    )


    # =====================================================
    # KEEP EXACT 365-DAY PERIOD
    # =========================================================

    df = df[
        (
            df["timestamp"]
            >= START_MS
        )
        &
        (
            df["timestamp"]
            <= END_MS
        )
    ].copy()


    # =====================================================
    # CONVERT VALUES
    # =========================================================

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


    df = df.sort_values(
        "datetime_utc"
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


    # =====================================================
    # SAVE
    # =========================================================

    df.to_csv(
        output_file,
        index=False
    )


    coverage = (
        len(df)
        /
        EXPECTED_HOURS
        * 100
    )


    print(
        "\nRows:",
        len(df)
    )

    print(
        "Coverage:",
        round(
            coverage,
            2
        ),
        "%"
    )

    print(
        "First:",
        df[
            "datetime_utc"
        ].min()
    )

    print(
        "Last:",
        df[
            "datetime_utc"
        ].max()
    )

    print(
        "Saved:",
        output_file
    )


    return {
        "status": "downloaded",
        "rows": len(df),
        "coverage_pct": coverage,
        "file": str(output_file)
    }


# =========================================================
# DOWNLOAD ALL 24
# =========================================================

manifest = []


for number, row in enumerate(
    universe.itertuples(),
    start=1
):

    print(
        "\n===================================="
    )

    print(
        f"[{number}/{len(universe)}]"
    )


    result = download_asset(
        row.rtoken_symbol,
        row.native_ticker
    )


    manifest.append(
        {
            "rtoken_symbol":
            row.rtoken_symbol,

            "native_ticker":
            row.native_ticker,

            "status":
            result.get(
                "status"
            ),

            "rows":
            result.get(
                "rows",
                0
            ),

            "coverage_pct":
            result.get(
                "coverage_pct"
            ),

            "file":
            result.get(
                "file"
            )
        }
    )


# =========================================================
# MANIFEST
# =========================================================

manifest_df = pd.DataFrame(
    manifest
)


manifest_df.to_csv(
    MANIFEST_FILE,
    index=False
)


# =========================================================
# SUMMARY
# =========================================================

print("\n====================================")
print("V2 DOWNLOAD SUMMARY")
print("====================================")


print(
    manifest_df[
        "status"
    ].value_counts()
)


print(
    "\nTotal downloaded rows:",
    manifest_df[
        "rows"
    ].sum()
)


print(
    "\nAverage raw coverage:",
    round(
        manifest_df[
            "rows"
        ].mean()
        /
        EXPECTED_HOURS
        * 100,
        2
    ),
    "%"
)


print(
    "\nLowest row counts:\n"
)


print(
    manifest_df[
        [
            "native_ticker",
            "rows"
        ]
    ]
    .sort_values(
        "rows"
    )
    .head(10)
    .to_string(
        index=False
    )
)


print(
    "\nManifest:",
    MANIFEST_FILE
)

print("====================================")
print("365-DAY DOWNLOAD COMPLETE")
print("====================================")