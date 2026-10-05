import requests
import pandas as pd
import time

from datetime import datetime, timezone
from pathlib import Path


# =========================================================
# SETTINGS
# =========================================================

UNIVERSE_FILE = Path(
    "data/reality_stock_info.csv"
)

OUTPUT_FILE = Path(
    "data/weekend_universe_coverage.csv"
)

BASE_URL = "https://api.bitget.com"

ENDPOINT = "/api/v3/market/candles"

INTERVAL = "1H"


# Same historical period used in our original project

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


EXPECTED_HOURS = int(
    (
        END_TIME - START_TIME
    ).total_seconds()
    / 3600
) + 1


print("====================================")
print("rFactor Lab")
print("Weekend Universe Coverage Scanner")
print("====================================")

print(
    "Research period:",
    START_TIME,
    "→",
    END_TIME
)

print(
    "Expected hourly positions:",
    EXPECTED_HOURS
)


# =========================================================
# LOAD REALITY UNIVERSE
# =========================================================

universe = pd.read_csv(
    UNIVERSE_FILE
)


weekend = universe[
    universe[
        "weekend_tradable"
    ]
    .astype(str)
    .str.lower()
    .eq("yes")
].copy()


print(
    "\nWeekend-tradable assets:",
    len(weekend)
)


# =========================================================
# DOWNLOAD TIMESTAMPS
# =========================================================

def scan_symbol(symbol):

    current_end = END_MS

    timestamps = []


    while current_end >= START_MS:

        params = {
            "category": "SPOT",
            "symbol": symbol,
            "interval": INTERVAL,
            "type": "market",
            "endTime": str(current_end),
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

            return {
                "success": False,
                "error": str(error)
            }


        if result.get("code") != "00000":

            return {
                "success": False,
                "error": str(result)
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


        timestamps.extend(
            batch_timestamps
        )


        oldest = min(
            batch_timestamps
        )


        if oldest <= START_MS:

            break


        current_end = (
            oldest - 1
        )


        # Gentle API pacing
        time.sleep(0.15)


    # =====================================================
    # CLEAN
    # =====================================================

    timestamps = sorted(
        set(timestamps)
    )


    timestamps = [
        ts
        for ts in timestamps
        if START_MS <= ts <= END_MS
    ]


    if not timestamps:

        return {
            "success": True,
            "candles": 0
        }


    dt = pd.to_datetime(
        timestamps,
        unit="ms",
        utc=True
    )


    # =====================================================
    # WEEKEND CANDLE COUNT
    # =====================================================

    dt_et = dt.tz_convert(
        "America/New_York"
    )


    weekend_count = sum(
        timestamp.weekday() >= 5
        for timestamp in dt_et
    )


    return {
        "success": True,

        "candles":
        len(timestamps),

        "first_candle":
        dt.min(),

        "last_candle":
        dt.max(),

        "weekend_candles":
        weekend_count
    }


# =========================================================
# SCAN EVERY WEEKEND-TRADABLE ASSET
# =========================================================

results = []


for number, row in enumerate(
    weekend.itertuples(),
    start=1
):

    symbol = row.rtoken_symbol

    ticker = row.native_ticker


    print(
        f"[{number}/{len(weekend)}]",
        symbol,
        "→",
        ticker
    )


    scan = scan_symbol(
        symbol
    )


    if not scan["success"]:

        print(
            "   ERROR:",
            scan.get(
                "error"
            )
        )

        results.append(
            {
                "rtoken_symbol":
                symbol,

                "native_ticker":
                ticker,

                "status":
                "error"
            }
        )

        continue


    candles = scan.get(
        "candles",
        0
    )


    coverage_pct = (
        candles
        /
        EXPECTED_HOURS
        * 100
    )


    weekend_candles = (
        scan.get(
            "weekend_candles",
            0
        )
    )


    print(
        "   Candles:",
        candles,
        "| Coverage:",
        round(
            coverage_pct,
            2
        ),
        "%",
        "| Weekend:",
        weekend_candles
    )


    results.append(
        {
            "rtoken_symbol":
            symbol,

            "native_ticker":
            ticker,

            "name":
            row.name,

            "candles":
            candles,

            "coverage_pct":
            coverage_pct,

            "weekend_candles":
            weekend_candles,

            "first_candle":
            scan.get(
                "first_candle"
            ),

            "last_candle":
            scan.get(
                "last_candle"
            ),

            "status":
            "ok"
        }
    )


# =========================================================
# RESULT TABLE
# =========================================================

results_df = pd.DataFrame(
    results
)


# =========================================================
# OBJECTIVE ELIGIBILITY RULE
# =========================================================

results_df[
    "research_eligible"
] = (
    (
        results_df[
            "coverage_pct"
        ] >= 80
    )
    &
    (
        results_df[
            "weekend_candles"
        ] >= 100
    )
    &
    (
        results_df[
            "status"
        ] == "ok"
    )
)


results_df = results_df.sort_values(
    [
        "research_eligible",
        "coverage_pct",
        "weekend_candles"
    ],
    ascending=[
        False,
        False,
        False
    ]
)


# =========================================================
# SAVE
# =========================================================

results_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# SUMMARY
# =========================================================

eligible = results_df[
    results_df[
        "research_eligible"
    ]
]


print("\n====================================")
print("COVERAGE SCAN COMPLETE")
print("====================================")


print(
    "Weekend-tradable assets:",
    len(results_df)
)


print(
    "Research-eligible assets:",
    len(eligible)
)


print(
    "\nTop eligible assets by data completeness:\n"
)


print(
    eligible[
        [
            "rtoken_symbol",
            "native_ticker",
            "candles",
            "coverage_pct",
            "weekend_candles"
        ]
    ]
    .head(30)
    .round(2)
    .to_string(index=False)
)


print(
    "\nSaved to:",
    OUTPUT_FILE
)