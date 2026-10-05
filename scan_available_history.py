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

OUTPUT_FILE = Path(
    "data/available_history_report.csv"
)

BASE_URL = "https://api.bitget.com"

ENDPOINT = "/api/v3/market/candles"

INTERVAL = "1H"

# Keep the same end date as our project
END_TIME = datetime(
    2026, 9, 25, 5, 0,
    tzinfo=timezone.utc
)

END_MS = int(
    END_TIME.timestamp() * 1000
)

# Safety limit:
# 20 batches × 1000 hours
# is more than 2 years.
MAX_BATCHES = 20


print("====================================")
print("rFactor Lab")
print("Historical Availability Scanner")
print("====================================")


# =========================================================
# LOAD 29-ASSET UNIVERSE
# =========================================================

universe = pd.read_csv(
    SPLIT_FILE
)


print(
    "\nAssets:",
    len(universe)
)


# =========================================================
# SCAN ONE SYMBOL
# =========================================================

def scan_history(symbol):

    current_end = END_MS

    timestamps = set()

    batches = 0


    while batches < MAX_BATCHES:

        params = {
            "category": "SPOT",
            "symbol": symbol,
            "interval": INTERVAL,
            "type": "market",
            "endTime": str(current_end),
            "limit": "1000"
        }


        success = False


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
                    "failed:",
                    error
                )

                time.sleep(2)


        if not success:

            return {
                "status": "error"
            }


        candles = result.get(
            "data",
            []
        )


        if not candles:

            break


        batch_timestamps = [
            int(candle[0])
            for candle in candles
        ]


        previous_count = len(
            timestamps
        )


        timestamps.update(
            batch_timestamps
        )


        # No new data means stop
        if len(timestamps) == previous_count:

            break


        oldest = min(
            batch_timestamps
        )


        newest = max(
            batch_timestamps
        )


        print(
            "   Batch:",
            batches + 1,
            "| Rows:",
            len(candles),
            "| Oldest:",
            datetime.fromtimestamp(
                oldest / 1000,
                tz=timezone.utc
            )
        )


        current_end = (
            oldest - 1
        )


        batches += 1


        time.sleep(0.15)


    # =====================================================
    # RESULTS
    # =====================================================

    if not timestamps:

        return {
            "status": "empty"
        }


    timestamps = sorted(
        timestamps
    )


    first = datetime.fromtimestamp(
        timestamps[0] / 1000,
        tz=timezone.utc
    )


    last = datetime.fromtimestamp(
        timestamps[-1] / 1000,
        tz=timezone.utc
    )


    history_days = (
        last - first
    ).total_seconds() / 86400


    return {
        "status": "ok",

        "first_candle":
        first,

        "last_candle":
        last,

        "history_days":
        history_days,

        "candles":
        len(timestamps),

        "batches":
        batches
    }


# =========================================================
# SCAN ALL ASSETS
# =========================================================

results = []


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
        row.rtoken_symbol,
        "→",
        row.native_ticker,
        "|",
        row.research_group
    )


    scan = scan_history(
        row.rtoken_symbol
    )


    results.append(
        {
            "rtoken_symbol":
            row.rtoken_symbol,

            "native_ticker":
            row.native_ticker,

            "research_group":
            row.research_group,

            "status":
            scan.get("status"),

            "first_candle":
            scan.get("first_candle"),

            "last_candle":
            scan.get("last_candle"),

            "history_days":
            scan.get("history_days"),

            "candles":
            scan.get("candles"),

            "batches":
            scan.get("batches")
        }
    )


# =========================================================
# SAVE REPORT
# =========================================================

df = pd.DataFrame(
    results
)


df.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# SUMMARY
# =========================================================

valid = df[
    df["status"] == "ok"
].copy()


print("\n====================================")
print("HISTORY SUMMARY")
print("====================================")


print(
    "Assets successfully scanned:",
    len(valid)
)


print(
    "Minimum history:",
    round(
        valid["history_days"].min(),
        2
    ),
    "days"
)


print(
    "Median history:",
    round(
        valid["history_days"].median(),
        2
    ),
    "days"
)


print(
    "Maximum history:",
    round(
        valid["history_days"].max(),
        2
    ),
    "days"
)


print(
    "\nAssets with >= 180 days:"
)

print(
    (
        valid["history_days"]
        >= 180
    ).sum()
)


print(
    "Assets with >= 270 days:"
)

print(
    (
        valid["history_days"]
        >= 270
    ).sum()
)


print(
    "Assets with >= 365 days:"
)

print(
    (
        valid["history_days"]
        >= 365
    ).sum()
)


print(
    "\nTop history coverage:\n"
)


print(
    valid[
        [
            "native_ticker",
            "research_group",
            "first_candle",
            "history_days",
            "candles"
        ]
    ]
    .sort_values(
        "history_days",
        ascending=False
    )
    .head(20)
    .round(2)
    .to_string(
        index=False
    )
)


print("\nSaved to:", OUTPUT_FILE)

print("====================================")
print("SCAN COMPLETE")
print("====================================")