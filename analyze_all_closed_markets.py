import pandas as pd
import numpy as np
from pathlib import Path


# =========================================================
# SETTINGS
# =========================================================

ASSETS = {
    "NVDA": {
        "rtoken": Path("data/rNVDA_1H_prepared.csv"),
        "stock": Path("data/NVDA_1H_aligned.csv")
    },

    "AAPL": {
        "rtoken": Path("data/rAAPL_1H_prepared.csv"),
        "stock": Path("data/AAPL_1H_aligned.csv")
    },

    "TSLA": {
        "rtoken": Path("data/rTSLA_1H_prepared.csv"),
        "stock": Path("data/TSLA_1H_aligned.csv")
    }
}


OUTPUT_FILE = Path(
    "data/multi_asset_closed_market_development.csv"
)

DEVELOPMENT_DAYS = 60

MIN_CLOSURE_HOURS = 24

# Require at least 80% of rToken hourly candles
# during a market closure.
MIN_RTOKEN_COVERAGE = 0.80


print("====================================")
print("rFactor Lab")
print("Multi-Asset Closed-Market Study")
print("====================================")


# =========================================================
# FIND GLOBAL PROJECT START
# =========================================================

project_starts = []


for ticker, files in ASSETS.items():

    temp = pd.read_csv(
        files["rtoken"]
    )

    temp["datetime_utc"] = pd.to_datetime(
        temp["datetime_utc"],
        utc=True
    )

    project_starts.append(
        temp["datetime_utc"].min()
    )


PROJECT_START = min(
    project_starts
)

DEVELOPMENT_END = (
    PROJECT_START
    + pd.Timedelta(
        days=DEVELOPMENT_DAYS
    )
)


print("\n1. DEVELOPMENT PERIOD")

print(
    "Start:",
    PROJECT_START
)

print(
    "End:",
    DEVELOPMENT_END
)


# =========================================================
# STORE ALL EVENTS
# =========================================================

all_events = []

excluded_low_coverage = 0

excluded_missing_boundary = 0


# =========================================================
# PROCESS EACH ASSET
# =========================================================

for ticker, files in ASSETS.items():

    print("\n====================================")
    print("Processing:", ticker)
    print("====================================")


    # -----------------------------------------------------
    # LOAD rTOKEN
    # -----------------------------------------------------

    rtoken = pd.read_csv(
        files["rtoken"]
    )

    rtoken["datetime_utc"] = pd.to_datetime(
        rtoken["datetime_utc"],
        utc=True
    )

    rtoken["close"] = pd.to_numeric(
        rtoken["close"],
        errors="coerce"
    )

    rtoken = rtoken[
        rtoken["datetime_utc"]
        < DEVELOPMENT_END
    ].copy()

    rtoken = rtoken.sort_values(
        "datetime_utc"
    ).reset_index(drop=True)


    # -----------------------------------------------------
    # LOAD NATIVE STOCK
    # -----------------------------------------------------

    stock = pd.read_csv(
        files["stock"]
    )

    stock["datetime_utc"] = pd.to_datetime(
        stock["datetime_utc"],
        utc=True
    )

    stock["open"] = pd.to_numeric(
        stock["open"],
        errors="coerce"
    )

    stock["close"] = pd.to_numeric(
        stock["close"],
        errors="coerce"
    )


    # Convert valid_hour safely to Boolean

    if stock["valid_hour"].dtype != bool:

        stock["valid_hour"] = (
            stock["valid_hour"]
            .astype(str)
            .str.lower()
            .eq("true")
        )


    stock = stock[
        stock["valid_hour"]
    ].copy()


    stock = stock[
        stock["datetime_utc"]
        < DEVELOPMENT_END
    ].copy()


    stock = stock.sort_values(
        "datetime_utc"
    ).reset_index(drop=True)


    print(
        "Valid stock hours:",
        len(stock)
    )


    asset_event_count = 0


    # =====================================================
    # FIND LARGE GAPS BETWEEN STOCK TRADING HOURS
    # =====================================================

    for i in range(
        len(stock) - 1
    ):

        before = stock.iloc[i]

        after = stock.iloc[i + 1]


        # The previous hourly candle ends
        # one hour after its timestamp.

        closure_start = (
            before["datetime_utc"]
            + pd.Timedelta(hours=1)
        )

        closure_end = (
            after["datetime_utc"]
        )


        closure_hours = (
            closure_end
            - closure_start
        ).total_seconds() / 3600


        # Ignore normal overnight gaps
        if closure_hours < MIN_CLOSURE_HOURS:

            continue


        # =================================================
        # rTOKEN START PRICE
        # =================================================

        start_match = rtoken[
            rtoken["datetime_utc"]
            ==
            before["datetime_utc"]
        ]


        if (
            start_match.empty
            or
            pd.isna(
                start_match.iloc[0]["close"]
            )
        ):

            excluded_missing_boundary += 1

            continue


        rtoken_start_price = (
            start_match.iloc[0]["close"]
        )


        # =================================================
        # EXACT rTOKEN END CANDLE
        # =================================================

        expected_final_timestamp = (
            after["datetime_utc"]
            - pd.Timedelta(hours=1)
        )


        end_match = rtoken[
            rtoken["datetime_utc"]
            ==
            expected_final_timestamp
        ]


        if (
            end_match.empty
            or
            pd.isna(
                end_match.iloc[0]["close"]
            )
        ):

            excluded_missing_boundary += 1

            continue


        rtoken_end_price = (
            end_match.iloc[0]["close"]
        )


        # =================================================
        # rTOKEN DATA DURING CLOSED PERIOD
        # =================================================

        during = rtoken[
            (
                rtoken["datetime_utc"]
                >= closure_start
            )
            &
            (
                rtoken["datetime_utc"]
                < closure_end
            )
        ].copy()


        valid_during = during[
            during["close"].notna()
        ].copy()


        expected_candles = int(
            closure_hours
        )


        if expected_candles <= 0:

            continue


        coverage = (
            len(valid_during)
            /
            expected_candles
        )


        # Reject incomplete closure periods
        if coverage < MIN_RTOKEN_COVERAGE:

            excluded_low_coverage += 1

            print(
                "Excluded",
                ticker,
                closure_start,
                "| Coverage:",
                round(
                    coverage * 100,
                    2
                ),
                "%"
            )

            continue


        # =================================================
        # rTOKEN CLOSED-MARKET RETURN
        # =================================================

        rtoken_return = (
            rtoken_end_price
            /
            rtoken_start_price
            - 1
        )


        # =================================================
        # NATIVE STOCK REOPENING GAP
        # =================================================

        native_close = (
            before["close"]
        )

        native_reopen_open = (
            after["open"]
        )


        native_reopen_gap = (
            native_reopen_open
            /
            native_close
            - 1
        )


        # =================================================
        # TRACKING ERROR
        # =================================================

        tracking_difference = (
            rtoken_return
            -
            native_reopen_gap
        )


        # =================================================
        # MAXIMUM rTOKEN MOVE
        # =================================================

        if not valid_during.empty:

            deviations = (
                valid_during["close"]
                /
                rtoken_start_price
                - 1
            )

            max_absolute_move = (
                deviations
                .abs()
                .max()
            )

        else:

            max_absolute_move = np.nan


        # =================================================
        # DIRECTION AGREEMENT
        # =================================================

        same_direction = (
            np.sign(
                rtoken_return
            )
            ==
            np.sign(
                native_reopen_gap
            )
        )


        # =================================================
        # NEW YORK TIMES
        # =================================================

        closure_start_et = (
            closure_start
            .tz_convert(
                "America/New_York"
            )
        )

        reopen_et = (
            closure_end
            .tz_convert(
                "America/New_York"
            )
        )


        # =================================================
        # SAVE EVENT
        # =================================================

        all_events.append(
            {
                "ticker":
                ticker,

                "closure_start_et":
                closure_start_et,

                "reopen_et":
                reopen_et,

                "closure_hours":
                closure_hours,

                "rtoken_coverage_pct":
                coverage * 100,

                "rtoken_start_price":
                rtoken_start_price,

                "rtoken_end_price":
                rtoken_end_price,

                "rtoken_closed_return_pct":
                rtoken_return * 100,

                "native_close_before":
                native_close,

                "native_reopen_open":
                native_reopen_open,

                "native_reopen_gap_pct":
                native_reopen_gap * 100,

                "tracking_difference_pct":
                tracking_difference * 100,

                "max_rtoken_move_pct":
                max_absolute_move * 100,

                "same_direction":
                same_direction,

                "valid_rtoken_candles":
                len(valid_during),

                "expected_rtoken_candles":
                expected_candles
            }
        )


        asset_event_count += 1


    print(
        "Accepted closed-market events:",
        asset_event_count
    )


# =========================================================
# CREATE RESULT DATAFRAME
# =========================================================

results = pd.DataFrame(
    all_events
)


print("\n====================================")
print("2. EVENT COLLECTION COMPLETE")
print("====================================")

print(
    "Total accepted events:",
    len(results)
)

print(
    "Excluded - low rToken coverage:",
    excluded_low_coverage
)

print(
    "Excluded - missing boundary price:",
    excluded_missing_boundary
)


if results.empty:

    print(
        "\nNo usable events found."
    )

    raise SystemExit


# =========================================================
# EVENTS PER ASSET
# =========================================================

print(
    "\n3. EVENTS PER ASSET"
)

print(
    results["ticker"]
    .value_counts()
)


# =========================================================
# SHOW EVENT TABLE
# =========================================================

display_columns = [
    "ticker",
    "closure_start_et",
    "reopen_et",
    "closure_hours",
    "rtoken_coverage_pct",
    "rtoken_closed_return_pct",
    "native_reopen_gap_pct",
    "tracking_difference_pct",
    "same_direction"
]


print(
    "\n4. CLOSED-MARKET EVENTS\n"
)

print(
    results[
        display_columns
    ]
    .to_string(
        index=False
    )
)


# =========================================================
# SUMMARY FUNCTION
# =========================================================

def summarize(group):

    count = len(group)

    direction_agreement = (
        group[
            "same_direction"
        ].mean()
        * 100
    )


    avg_tracking_error = (
        group[
            "tracking_difference_pct"
        ]
        .abs()
        .mean()
    )


    if count >= 2:

        correlation = (
            group[
                "rtoken_closed_return_pct"
            ]
            .corr(
                group[
                    "native_reopen_gap_pct"
                ]
            )
        )

    else:

        correlation = np.nan


    return pd.Series(
        {
            "events":
            count,

            "avg_rtoken_return_pct":
            group[
                "rtoken_closed_return_pct"
            ].mean(),

            "avg_native_gap_pct":
            group[
                "native_reopen_gap_pct"
            ].mean(),

            "avg_abs_tracking_difference_pct":
            avg_tracking_error,

            "direction_agreement_pct":
            direction_agreement,

            "correlation":
            correlation
        }
    )


# =========================================================
# SUMMARY BY ASSET
# =========================================================

print(
    "\n5. SUMMARY BY ASSET"
)


summary_by_asset = (
    results.groupby(
        "ticker"
    )
    .apply(
        summarize
    )
)


print(
    summary_by_asset.round(4)
)


# =========================================================
# COMBINED SUMMARY
# =========================================================

print(
    "\n6. COMBINED SUMMARY"
)


combined = summarize(
    results
)


print(
    combined.round(4)
)


# =========================================================
# SAVE RESULTS
# =========================================================

results.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n====================================")
print("MULTI-ASSET STUDY COMPLETE")
print("====================================")

print(
    "Saved to:",
    OUTPUT_FILE
)

print(
    "IMPORTANT:"
)

print(
    "Only development-period data "
    "was analyzed."
)

print(
    "Out-of-sample results remain hidden."
)