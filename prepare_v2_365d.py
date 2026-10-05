import pandas as pd
from pathlib import Path
from datetime import datetime, timezone


# =========================================================
# SETTINGS
# =========================================================

UNIVERSE_FILE = Path(
    "data/long_history_universe.csv"
)

RAW_FOLDER = Path(
    "data/v2_raw"
)

OUTPUT_FOLDER = Path(
    "data/v2_prepared"
)

QUALITY_FILE = Path(
    "data/v2_quality_report.csv"
)


START_TIME = datetime(
    2025, 9, 25, 6, 0,
    tzinfo=timezone.utc
)

END_TIME = datetime(
    2026, 9, 25, 5, 0,
    tzinfo=timezone.utc
)


# Frozen quality rules
MIN_WEEKEND_COVERAGE = 60.0

MIN_WEEKEND_BLOCK_COVERAGE = 60.0

MIN_USABLE_WEEKENDS = 30


OUTPUT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


print("====================================")
print("rFactor Lab")
print("V2 - 365 Day Data Preparation")
print("====================================")


# =========================================================
# SESSION CLASSIFICATION
# =========================================================

def classify_session(timestamp):

    weekday = timestamp.weekday()
    hour = timestamp.hour

    if weekday >= 5:
        return "Weekend"

    if 4 <= hour < 9:
        return "Pre-Market"

    if hour == 9:
        return "Transition"

    if 10 <= hour < 16:
        return "Regular"

    if 16 <= hour < 20:
        return "After-Hours"

    return "Overnight"


# =========================================================
# LOAD UNIVERSE
# =========================================================

universe = pd.read_csv(
    UNIVERSE_FILE
)


print(
    "\nAssets:",
    len(universe)
)


# =========================================================
# COMMON HOURLY TIMELINE
# =========================================================

full_timeline = pd.date_range(
    start=START_TIME,
    end=END_TIME,
    freq="1h"
)


EXPECTED_HOURS = len(
    full_timeline
)


print(
    "Expected hourly positions:",
    EXPECTED_HOURS
)


quality_rows = []


# =========================================================
# PROCESS EACH ASSET
# =========================================================

for number, row in enumerate(
    universe.itertuples(),
    start=1
):

    ticker = row.native_ticker

    symbol = row.rtoken_symbol


    print("\n====================================")

    print(
        f"[{number}/{len(universe)}]"
    )

    print(
        ticker,
        "|",
        symbol
    )


    input_file = (
        RAW_FOLDER
        /
        f"{ticker}_365d_1H.csv"
    )


    output_file = (
        OUTPUT_FOLDER
        /
        f"{ticker}_prepared.csv"
    )


    # =====================================================
    # LOAD
    # =====================================================

    df = pd.read_csv(
        input_file
    )


    df["datetime_utc"] = pd.to_datetime(
        df["datetime_utc"],
        utc=True
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


    # =====================================================
    # BASIC QUALITY CHECKS
    # =====================================================

    raw_rows = len(df)


    duplicate_count = (
        df.duplicated(
            subset=["datetime_utc"]
        ).sum()
    )


    invalid_high = (
        (
            df["high"] < df["open"]
        )
        |
        (
            df["high"] < df["close"]
        )
        |
        (
            df["high"] < df["low"]
        )
    ).sum()


    invalid_low = (
        (
            df["low"] > df["open"]
        )
        |
        (
            df["low"] > df["close"]
        )
        |
        (
            df["low"] > df["high"]
        )
    ).sum()


    df = df.drop_duplicates(
        subset=["datetime_utc"]
    )


    # =====================================================
    # EXACT V2 TIME RANGE
    # =====================================================

    df = df[
        (
            df["datetime_utc"]
            >= START_TIME
        )
        &
        (
            df["datetime_utc"]
            <= END_TIME
        )
    ].copy()


    df = df.sort_values(
        "datetime_utc"
    )


    df = df.set_index(
        "datetime_utc"
    )


    # =====================================================
    # COMPLETE HOURLY TIMELINE
    # =====================================================

    df = df.reindex(
        full_timeline
    )


    df.index.name = (
        "datetime_utc"
    )


    # =====================================================
    # MISSING DATA
    # =====================================================

    df["missing_candle"] = (
        df["close"].isna()
    )


    available_hours = int(
        df["close"]
        .notna()
        .sum()
    )


    missing_hours = (
        EXPECTED_HOURS
        -
        available_hours
    )


    coverage_pct = (
        available_hours
        /
        EXPECTED_HOURS
        * 100
    )


    # =====================================================
    # NEW YORK TIME
    # =====================================================

    df["datetime_et"] = (
        df.index
        .tz_convert(
            "America/New_York"
        )
    )


    df["weekday"] = (
        df["datetime_et"]
        .dt.day_name()
    )


    df["session"] = (
        df["datetime_et"]
        .map(
            classify_session
        )
    )


    # =====================================================
    # WEEKEND COVERAGE
    # =====================================================

    weekend = df[
        df["session"]
        == "Weekend"
    ].copy()


    weekend_expected = len(
        weekend
    )


    weekend_available = int(
        weekend["close"]
        .notna()
        .sum()
    )


    weekend_coverage_pct = (
        weekend_available
        /
        weekend_expected
        * 100
        if weekend_expected > 0
        else 0
    )


    # =====================================================
    # IDENTIFY INDIVIDUAL WEEKENDS
    # =====================================================

    df["is_weekend"] = (
        df["session"]
        == "Weekend"
    )


    df["weekend_start"] = (
        df["is_weekend"]
        &
        ~df["is_weekend"]
        .shift(
            1,
            fill_value=False
        )
    )


    df["weekend_id"] = (
        df["weekend_start"]
        .cumsum()
    )


    weekend_stats = []


    weekend_ids = (
        df.loc[
            df["is_weekend"],
            "weekend_id"
        ]
        .unique()
    )


    for weekend_id in weekend_ids:

        block = df[
            (
                df["weekend_id"]
                == weekend_id
            )
            &
            (
                df["is_weekend"]
            )
        ]


        expected = len(
            block
        )


        available = int(
            block["close"]
            .notna()
            .sum()
        )


        # Ignore partial edge weekends
        if expected < 40:

            continue


        block_coverage = (
            available
            /
            expected
            * 100
        )


        weekend_stats.append(
            {
                "weekend_id":
                weekend_id,

                "expected":
                expected,

                "available":
                available,

                "coverage_pct":
                block_coverage
            }
        )


    weekend_stats = pd.DataFrame(
        weekend_stats
    )


    if not weekend_stats.empty:

        full_weekends = len(
            weekend_stats
        )


        usable_weekends = int(
            (
                weekend_stats[
                    "coverage_pct"
                ]
                >=
                MIN_WEEKEND_BLOCK_COVERAGE
            ).sum()
        )


        median_weekend_coverage = (
            weekend_stats[
                "coverage_pct"
            ].median()
        )


    else:

        full_weekends = 0
        usable_weekends = 0
        median_weekend_coverage = 0


    # =====================================================
    # FINAL V2 QUALITY GATE
    # =====================================================

    candle_quality_ok = (
        duplicate_count == 0
        and
        invalid_high == 0
        and
        invalid_low == 0
    )


    weekend_quality_ok = (
        weekend_coverage_pct
        >= MIN_WEEKEND_COVERAGE
    )


    enough_weekends = (
        usable_weekends
        >= MIN_USABLE_WEEKENDS
    )


    v2_eligible = (
        candle_quality_ok
        and
        weekend_quality_ok
        and
        enough_weekends
    )


    # =====================================================
    # METADATA
    # =====================================================

    df["native_ticker"] = ticker

    df["rtoken_symbol"] = symbol


    # =====================================================
    # SAVE PREPARED FILE
    # =====================================================

    df = df.reset_index()


    df.to_csv(
        output_file,
        index=False
    )


    # =====================================================
    # QUALITY REPORT
    # =====================================================

    quality_rows.append(
        {
            "native_ticker":
            ticker,

            "rtoken_symbol":
            symbol,

            "raw_rows":
            raw_rows,

            "duplicates":
            duplicate_count,

            "invalid_high":
            invalid_high,

            "invalid_low":
            invalid_low,

            "available_hours":
            available_hours,

            "missing_hours":
            missing_hours,

            "coverage_pct":
            coverage_pct,

            "weekend_expected":
            weekend_expected,

            "weekend_available":
            weekend_available,

            "weekend_coverage_pct":
            weekend_coverage_pct,

            "full_weekends":
            full_weekends,

            "usable_weekends":
            usable_weekends,

            "median_weekend_coverage_pct":
            median_weekend_coverage,

            "candle_quality_ok":
            candle_quality_ok,

            "weekend_quality_ok":
            weekend_quality_ok,

            "enough_weekends":
            enough_weekends,

            "v2_eligible":
            v2_eligible
        }
    )


    print(
        "Overall coverage:",
        round(
            coverage_pct,
            2
        ),
        "%"
    )


    print(
        "Weekend coverage:",
        round(
            weekend_coverage_pct,
            2
        ),
        "%"
    )


    print(
        "Usable weekends:",
        usable_weekends,
        "/",
        full_weekends
    )


    print(
        "V2 eligible:",
        v2_eligible
    )


# =========================================================
# QUALITY REPORT
# =====================================================

quality = pd.DataFrame(
    quality_rows
)


quality.to_csv(
    QUALITY_FILE,
    index=False
)


# =========================================================
# SUMMARY
# =====================================================

eligible = quality[
    quality["v2_eligible"]
]


print("\n====================================")
print("V2 QUALITY SUMMARY")
print("====================================")


print(
    "Total assets:",
    len(quality)
)


print(
    "V2 eligible assets:",
    len(eligible)
)


print(
    "Excluded assets:",
    len(quality)
    -
    len(eligible)
)


print(
    "\nAverage overall coverage:",
    round(
        quality[
            "coverage_pct"
        ].mean(),
        2
    ),
    "%"
)


print(
    "Average weekend coverage:",
    round(
        quality[
            "weekend_coverage_pct"
        ].mean(),
        2
    ),
    "%"
)


print(
    "\nELIGIBLE ASSETS:\n"
)


print(
    eligible[
        [
            "native_ticker",
            "coverage_pct",
            "weekend_coverage_pct",
            "usable_weekends"
        ]
    ]
    .sort_values(
        "native_ticker"
    )
    .round(2)
    .to_string(
        index=False
    )
)


print(
    "\nEXCLUDED ASSETS:\n"
)


excluded = quality[
    ~quality["v2_eligible"]
]


if excluded.empty:

    print("None")

else:

    print(
        excluded[
            [
                "native_ticker",
                "coverage_pct",
                "weekend_coverage_pct",
                "usable_weekends"
            ]
        ]
        .sort_values(
            "weekend_coverage_pct"
        )
        .round(2)
        .to_string(
            index=False
        )
    )


print("\n====================================")
print("V2 PREPARATION COMPLETE")
print("====================================")


print(
    "Quality report:",
    QUALITY_FILE
)


print(
    "\nNo factor returns or strategy "
    "performance were inspected."
)