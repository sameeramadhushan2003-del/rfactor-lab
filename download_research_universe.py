import requests
import pandas as pd
import time

from datetime import datetime, timezone
from pathlib import Path


# =========================================================
# SETTINGS
# =========================================================

SPLIT_FILE = Path(
    "data/research_asset_split.csv"
)

OUTPUT_FOLDER = Path(
    "data/universe_raw"
)

MANIFEST_FILE = Path(
    "data/universe_download_manifest.csv"
)

BASE_URL = "https://api.bitget.com"

ENDPOINT = "/api/v3/market/candles"

INTERVAL = "1H"


# Same research period

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


OUTPUT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


print("====================================")
print("rFactor Lab")
print("Research Universe Downloader")
print("====================================")


# =========================================================
# LOAD FROZEN SPLIT
# =========================================================

universe = pd.read_csv(
    SPLIT_FILE
)


print(
    "\nAssets to download:",
    len(universe)
)


print(
    universe["research_group"]
    .value_counts()
)


# =========================================================
# DOWNLOAD FUNCTION
# =========================================================

def download_symbol(
    symbol,
    native_ticker
):

    print("\n------------------------------------")
    print(symbol, "→", native_ticker)
    print("------------------------------------")


    output_file = (
        OUTPUT_FOLDER
        /
        f"{native_ticker}_rToken_1H.csv"
    )


    # -----------------------------------------------------
    # RESUME SUPPORT
    # -----------------------------------------------------

    if output_file.exists():

        print(
            "Already downloaded. Skipping."
        )

        existing = pd.read_csv(
            output_file
        )

        return {
            "status": "existing",
            "rows": len(existing),
            "file": str(output_file)
        }


    current_end = END_MS

    all_candles = []


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


        # -------------------------------------------------
        # RETRY UP TO 3 TIMES
        # -------------------------------------------------

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

                time.sleep(
                    2
                )


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


        oldest_timestamp = min(
            int(
                candle[0]
            )
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


        if (
            oldest_timestamp
            <= START_MS
        ):

            break


        current_end = (
            oldest_timestamp - 1
        )


        time.sleep(
            0.15
        )


    # =====================================================
    # CREATE DATAFRAME
    # =====================================================

    if not all_candles:

        return {
            "status": "empty",
            "rows": 0,
            "file": str(output_file)
        }


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


    # -----------------------------------------------------
    # DUPLICATES
    # -----------------------------------------------------

    df = df.drop_duplicates(
        subset=[
            "timestamp"
        ]
    )


    # -----------------------------------------------------
    # EXACT RESEARCH PERIOD
    # -----------------------------------------------------

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
    ]


    # -----------------------------------------------------
    # NUMERIC VALUES
    # -----------------------------------------------------

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
    # =====================================================

    df.to_csv(
        output_file,
        index=False
    )


    print(
        "Saved:",
        output_file
    )

    print(
        "Rows:",
        len(df)
    )


    return {
        "status": "downloaded",
        "rows": len(df),
        "file": str(output_file)
    }


# =========================================================
# DOWNLOAD ALL 29
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

    print(
        "Group:",
        row.research_group
    )


    result = download_symbol(
        row.rtoken_symbol,
        row.native_ticker
    )


    manifest.append(
        {
            "rtoken_symbol":
            row.rtoken_symbol,

            "native_ticker":
            row.native_ticker,

            "research_group":
            row.research_group,

            "status":
            result["status"],

            "rows":
            result["rows"],

            "file":
            result["file"]
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


print("\n====================================")
print("DOWNLOAD SUMMARY")
print("====================================")


print(
    manifest_df[
        "status"
    ].value_counts()
)


print(
    "\nRows by research group:"
)


print(
    manifest_df.groupby(
        "research_group"
    )["rows"]
    .sum()
)


print(
    "\nSaved manifest to:",
    MANIFEST_FILE
)


print(
    "\nIMPORTANT:"
)

print(
    "Downloading holdout raw data is OK."
)

print(
    "Do NOT calculate or inspect "
    "holdout strategy results."
)