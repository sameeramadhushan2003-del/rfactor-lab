import pandas as pd
from pathlib import Path


# =========================================================
# SETTINGS
# =========================================================

UNIVERSE_FILE = Path(
    "data/long_history_universe.csv"
)

PREPARED_FOLDER = Path(
    "data/v2_prepared"
)

OLD_QUALITY_FILE = Path(
    "data/v2_quality_report.csv"
)

MASK_FILE = Path(
    "data/v2_market_mask.csv"
)

QUALITY_OUTPUT = Path(
    "data/v2_final_quality.csv"
)


# Timestamp is considered normally tradable
# when at least 80% of the universe has data.

MIN_UNIVERSE_PRESENCE = 0.80


# Asset must contain at least 95%
# of those normally tradable timestamps.

MIN_ASSET_COVERAGE = 0.95


print("====================================")
print("rFactor Lab")
print("V2 Expected Market Mask")
print("====================================")


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
# COLLECT AVAILABILITY
# =========================================================

availability_frames = []


for number, row in enumerate(
    universe.itertuples(),
    start=1
):

    ticker = row.native_ticker

    print(
        f"[{number}/{len(universe)}]",
        ticker
    )


    file = (
        PREPARED_FOLDER
        /
        f"{ticker}_prepared.csv"
    )


    df = pd.read_csv(
        file,
        usecols=[
            "datetime_utc",
            "datetime_et",
            "session",
            "close"
        ]
    )


    df["datetime_utc"] = pd.to_datetime(
        df["datetime_utc"],
        utc=True
    )


    df["datetime_et"] = pd.to_datetime(
        df["datetime_et"],
        utc=True
    ).dt.tz_convert(
        "America/New_York"
    )


    df["close"] = pd.to_numeric(
        df["close"],
        errors="coerce"
    )


    df["available"] = (
        df["close"].notna()
    )


    df["asset"] = ticker


    availability_frames.append(
        df[
            [
                "datetime_utc",
                "datetime_et",
                "session",
                "asset",
                "available"
            ]
        ]
    )


# =========================================================
# COMBINE
# =========================================================

data = pd.concat(
    availability_frames,
    ignore_index=True
)


# =========================================================
# GENERAL FACTOR RESEARCH:
# WEEKDAYS ONLY
# =========================================================

data["weekday_num"] = (
    data["datetime_et"]
    .dt.weekday
)


weekday = data[
    data["weekday_num"] < 5
].copy()


# =========================================================
# UNIVERSE AVAILABILITY BY TIMESTAMP
# =========================================================

timestamp_summary = (
    weekday.groupby(
        "datetime_utc"
    )
    .agg(
        assets_expected=(
            "asset",
            "nunique"
        ),

        assets_available=(
            "available",
            "sum"
        )
    )
    .reset_index()
)


timestamp_summary[
    "universe_presence_pct"
] = (
    timestamp_summary[
        "assets_available"
    ]
    /
    timestamp_summary[
        "assets_expected"
    ]
    * 100
)


# =========================================================
# EXPECTED MARKET TIMESTAMP
# =========================================================

timestamp_summary[
    "expected_market_hour"
] = (
    timestamp_summary[
        "assets_available"
    ]
    /
    timestamp_summary[
        "assets_expected"
    ]
    >=
    MIN_UNIVERSE_PRESENCE
)


expected_times = set(
    timestamp_summary.loc[
        timestamp_summary[
            "expected_market_hour"
        ],
        "datetime_utc"
    ]
)


print(
    "\nWeekday timestamps:",
    len(
        timestamp_summary
    )
)


print(
    "Expected market timestamps:",
    len(
        expected_times
    )
)


print(
    "Systemically unavailable timestamps:",
    len(
        timestamp_summary
    )
    -
    len(
        expected_times
    )
)


# =========================================================
# SAVE MARKET MASK
# =========================================================

timestamp_summary.to_csv(
    MASK_FILE,
    index=False
)


# =========================================================
# OLD CANDLE QUALITY
# =========================================================

old_quality = pd.read_csv(
    OLD_QUALITY_FILE
)


quality_results = []


# =========================================================
# ASSET COVERAGE AGAINST CORRECT MASK
# =========================================================

for row in universe.itertuples():

    ticker = row.native_ticker

    symbol = row.rtoken_symbol


    file = (
        PREPARED_FOLDER
        /
        f"{ticker}_prepared.csv"
    )


    df = pd.read_csv(
        file,
        usecols=[
            "datetime_utc",
            "close"
        ]
    )


    df["datetime_utc"] = pd.to_datetime(
        df["datetime_utc"],
        utc=True
    )


    df["close"] = pd.to_numeric(
        df["close"],
        errors="coerce"
    )


    df = df[
        df["datetime_utc"]
        .isin(
            expected_times
        )
    ]


    expected = len(
        expected_times
    )


    available = int(
        df["close"]
        .notna()
        .sum()
    )


    coverage = (
        available
        /
        expected
        if expected > 0
        else 0
    )


    old = old_quality[
        old_quality[
            "native_ticker"
        ]
        ==
        ticker
    ].iloc[0]


    candle_quality_ok = (
        old["duplicates"] == 0
        and
        old["invalid_high"] == 0
        and
        old["invalid_low"] == 0
    )


    general_factor_eligible = (
        candle_quality_ok
        and
        coverage
        >=
        MIN_ASSET_COVERAGE
    )


    quality_results.append(
        {
            "native_ticker":
            ticker,

            "rtoken_symbol":
            symbol,

            "expected_market_hours":
            expected,

            "available_market_hours":
            available,

            "corrected_coverage_pct":
            coverage * 100,

            "duplicates":
            old["duplicates"],

            "invalid_high":
            old["invalid_high"],

            "invalid_low":
            old["invalid_low"],

            "candle_quality_ok":
            candle_quality_ok,

            "general_factor_eligible":
            general_factor_eligible
        }
    )


# =========================================================
# RESULT TABLE
# =========================================================

quality = pd.DataFrame(
    quality_results
)


quality.to_csv(
    QUALITY_OUTPUT,
    index=False
)


eligible = quality[
    quality[
        "general_factor_eligible"
    ]
]


# =========================================================
# SUMMARY
# =========================================================

print("\n====================================")
print("FINAL V2 QUALITY SUMMARY")
print("====================================")


print(
    "Total assets:",
    len(quality)
)


print(
    "General-factor eligible:",
    len(eligible)
)


print(
    "Excluded:",
    len(quality)
    -
    len(eligible)
)


print(
    "Average corrected coverage:",
    round(
        quality[
            "corrected_coverage_pct"
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
            "corrected_coverage_pct"
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
    ~quality[
        "general_factor_eligible"
    ]
]


if excluded.empty:

    print(
        "None"
    )

else:

    print(
        excluded[
            [
                "native_ticker",
                "corrected_coverage_pct"
            ]
        ]
        .sort_values(
            "corrected_coverage_pct"
        )
        .round(2)
        .to_string(
            index=False
        )
    )


print("\n====================================")
print("MARKET MASK COMPLETE")
print("====================================")


print(
    "Market mask:",
    MASK_FILE
)


print(
    "Quality report:",
    QUALITY_OUTPUT
)


print(
    "\nNo factor or strategy returns "
    "were inspected."
)