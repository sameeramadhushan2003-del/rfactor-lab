import pandas as pd
from pathlib import Path
from datetime import datetime, timezone


# =========================================================
# SETTINGS
# =========================================================

SPLIT_FILE = Path(
    "data/research_asset_split.csv"
)

RAW_FOLDER = Path(
    "data/universe_raw"
)

OUTPUT_FOLDER = Path(
    "data/universe_prepared"
)

QUALITY_FILE = Path(
    "data/universe_quality_report.csv"
)


START_TIME = datetime(
    2026, 6, 27, 6, 0,
    tzinfo=timezone.utc
)

END_TIME = datetime(
    2026, 9, 25, 5, 0,
    tzinfo=timezone.utc
)


OUTPUT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


print("====================================")
print("rFactor Lab")
print("Research Universe Preparation")
print("====================================")


# =========================================================
# SESSION CLASSIFICATION
# =========================================================

def classify_session(timestamp):

    weekday = timestamp.weekday()

    hour = timestamp.hour


    # Saturday / Sunday
    if weekday >= 5:

        return "Weekend"


    # 04:00 - 08:59 ET
    if 4 <= hour < 9:

        return "Pre-Market"


    # 09:00 - 09:59
    # mixed pre-market + regular open
    if hour == 9:

        return "Transition"


    # 10:00 - 15:59
    if 10 <= hour < 16:

        return "Regular"


    # 16:00 - 19:59
    if 16 <= hour < 20:

        return "After-Hours"


    # 20:00 - 03:59
    return "Overnight"


# =========================================================
# LOAD FROZEN SPLIT
# =========================================================

universe = pd.read_csv(
    SPLIT_FILE
)


print(
    "\nAssets:",
    len(universe)
)


print(
    universe[
        "research_group"
    ].value_counts()
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
    "\nExpected hourly positions:",
    EXPECTED_HOURS
)


# =========================================================
# QUALITY RESULTS
# =========================================================

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

    group = row.research_group


    print(
        "\n===================================="
    )

    print(
        f"[{number}/{len(universe)}]"
    )

    print(
        ticker,
        "|",
        symbol,
        "|",
        group
    )


    input_file = (
        RAW_FOLDER
        /
        f"{ticker}_rToken_1H.csv"
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
    # BASIC QUALITY
    # =====================================================

    original_rows = len(df)


    duplicate_count = (
        df.duplicated(
            subset=[
                "datetime_utc"
            ]
        ).sum()
    )


    df = df.drop_duplicates(
        subset=[
            "datetime_utc"
        ]
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


    # =====================================================
    # EXACT COMMON TIME RANGE
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


    missing_count = int(
        df["missing_candle"]
        .sum()
    )


    available_count = (
        EXPECTED_HOURS
        -
        missing_count
    )


    coverage_pct = (
        available_count
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
        df[
            "datetime_et"
        ]
        .map(
            classify_session
        )
    )


    # =====================================================
    # WEEKEND QUALITY
    # =====================================================

    weekend_rows = df[
        df["session"]
        == "Weekend"
    ]


    weekend_available = int(
        weekend_rows[
            "close"
        ]
        .notna()
        .sum()
    )


    weekend_expected = len(
        weekend_rows
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
    # GAP COUNTS BY SESSION
    # =====================================================

    missing = df[
        df["missing_candle"]
    ]


    missing_weekend = int(
        (
            missing["session"]
            == "Weekend"
        ).sum()
    )


    missing_overnight = int(
        (
            missing["session"]
            == "Overnight"
        ).sum()
    )


    missing_regular = int(
        (
            missing["session"]
            == "Regular"
        ).sum()
    )


    # =====================================================
    # METADATA
    # =====================================================

    df["native_ticker"] = (
        ticker
    )

    df["rtoken_symbol"] = (
        symbol
    )

    df["research_group"] = (
        group
    )


    # =====================================================
    # SAVE PREPARED DATA
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

            "research_group":
            group,

            "raw_rows":
            original_rows,

            "duplicates":
            duplicate_count,

            "invalid_high":
            invalid_high,

            "invalid_low":
            invalid_low,

            "available_hours":
            available_count,

            "missing_hours":
            missing_count,

            "coverage_pct":
            coverage_pct,

            "weekend_available":
            weekend_available,

            "weekend_expected":
            weekend_expected,

            "weekend_coverage_pct":
            weekend_coverage_pct,

            "missing_weekend":
            missing_weekend,

            "missing_overnight":
            missing_overnight,

            "missing_regular":
            missing_regular,

            "prepared_file":
            str(output_file)
        }
    )


    print(
        "Available:",
        available_count,
        "/",
        EXPECTED_HOURS
    )

    print(
        "Coverage:",
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
        "Missing weekend:",
        missing_weekend
    )


# =========================================================
# QUALITY REPORT
# =========================================================

quality = pd.DataFrame(
    quality_rows
)


quality.to_csv(
    QUALITY_FILE,
    index=False
)


# =========================================================
# GROUP SUMMARY
# =========================================================

print("\n====================================")
print("QUALITY SUMMARY")
print("====================================")


summary = (
    quality.groupby(
        "research_group"
    )
    .agg(
        assets=(
            "native_ticker",
            "count"
        ),

        avg_coverage_pct=(
            "coverage_pct",
            "mean"
        ),

        avg_weekend_coverage_pct=(
            "weekend_coverage_pct",
            "mean"
        ),

        total_missing_hours=(
            "missing_hours",
            "sum"
        ),

        total_missing_weekend=(
            "missing_weekend",
            "sum"
        )
    )
)


print(
    summary.round(2)
)


print(
    "\nAssets with lowest weekend coverage:"
)


print(
    quality[
        [
            "native_ticker",
            "research_group",
            "coverage_pct",
            "weekend_coverage_pct"
        ]
    ]
    .sort_values(
        "weekend_coverage_pct"
    )
    .head(10)
    .round(2)
    .to_string(
        index=False
    )
)


print("\n====================================")
print("PREPARATION COMPLETE")
print("====================================")


print(
    "Quality report:",
    QUALITY_FILE
)


print(
    "\nIMPORTANT:"
)

print(
    "No factor or strategy performance "
    "was calculated."
)

print(
    "Validation and Holdout assets "
    "remain untouched for strategy research."
)