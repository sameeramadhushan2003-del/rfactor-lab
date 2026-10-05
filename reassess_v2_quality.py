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

OUTPUT_FILE = Path(
    "data/v2_reassessed_quality.csv"
)


# Frozen before factor performance is examined
MIN_WEEKDAY_COVERAGE = 95.0


print("====================================")
print("rFactor Lab")
print("V2 - Corrected Quality Analysis")
print("====================================")


# =========================================================
# LOAD
# =========================================================

universe = pd.read_csv(
    UNIVERSE_FILE
)

old_quality = pd.read_csv(
    OLD_QUALITY_FILE
)


results = []


# =========================================================
# PROCESS EVERY ASSET
# =========================================================

for number, row in enumerate(
    universe.itertuples(),
    start=1
):

    ticker = row.native_ticker

    symbol = row.rtoken_symbol


    print(
        "\n===================================="
    )

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
        file
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


    # =====================================================
    # WEEKDAY COVERAGE
    # =====================================================

    df["et_weekday"] = (
        df["datetime_et"]
        .dt.weekday
    )


    weekday = df[
        df["et_weekday"] < 5
    ].copy()


    weekday_expected = len(
        weekday
    )


    weekday_available = int(
        weekday["close"]
        .notna()
        .sum()
    )


    weekday_coverage = (
        weekday_available
        /
        weekday_expected
        * 100
        if weekday_expected > 0
        else 0
    )


    # =====================================================
    # WEEKEND DATA
    # =====================================================

    weekend = df[
        df["session"]
        == "Weekend"
    ].copy()


    weekend_valid = weekend[
        weekend["close"]
        .notna()
    ]


    # =====================================================
    # FIRST ACTUAL WEEKEND CANDLE
    # =====================================================

    if weekend_valid.empty:

        first_weekend_candle = pd.NaT

        active_weekend_expected = 0

        active_weekend_available = 0

        active_weekend_coverage = 0

        full_active_weekends = 0

        usable_active_weekends = 0


    else:

        first_weekend_candle = (
            weekend_valid[
                "datetime_utc"
            ].min()
        )


        active_weekend = weekend[
            weekend[
                "datetime_utc"
            ]
            >=
            first_weekend_candle
        ].copy()


        active_weekend_expected = len(
            active_weekend
        )


        active_weekend_available = int(
            active_weekend[
                "close"
            ]
            .notna()
            .sum()
        )


        active_weekend_coverage = (
            active_weekend_available
            /
            active_weekend_expected
            * 100
            if active_weekend_expected > 0
            else 0
        )


        # =================================================
        # IDENTIFY WEEKEND BLOCKS AFTER ACTIVATION
        # =================================================

        active_weekend[
            "weekend_date"
        ] = (
            active_weekend[
                "datetime_et"
            ]
            -
            pd.to_timedelta(
                active_weekend[
                    "datetime_et"
                ]
                .dt.weekday
                - 5,
                unit="D"
            )
        ).dt.date


        weekend_blocks = []


        for weekend_date, block in (
            active_weekend.groupby(
                "weekend_date"
            )
        ):

            expected = len(
                block
            )


            available = int(
                block[
                    "close"
                ]
                .notna()
                .sum()
            )


            # Ignore very small edge fragments
            if expected < 20:

                continue


            coverage = (
                available
                /
                expected
                * 100
            )


            weekend_blocks.append(
                {
                    "weekend_date":
                    weekend_date,

                    "expected":
                    expected,

                    "available":
                    available,

                    "coverage":
                    coverage
                }
            )


        weekend_blocks = pd.DataFrame(
            weekend_blocks
        )


        if weekend_blocks.empty:

            full_active_weekends = 0

            usable_active_weekends = 0


        else:

            full_active_weekends = len(
                weekend_blocks
            )


            usable_active_weekends = int(
                (
                    weekend_blocks[
                        "coverage"
                    ]
                    >= 60
                ).sum()
            )


    # =====================================================
    # EXISTING CANDLE QUALITY
    # =====================================================

    quality_row = old_quality[
        old_quality[
            "native_ticker"
        ]
        == ticker
    ]


    duplicates = int(
        quality_row.iloc[0][
            "duplicates"
        ]
    )


    invalid_high = int(
        quality_row.iloc[0][
            "invalid_high"
        ]
    )


    invalid_low = int(
        quality_row.iloc[0][
            "invalid_low"
        ]
    )


    candle_quality_ok = (
        duplicates == 0
        and
        invalid_high == 0
        and
        invalid_low == 0
    )


    # =====================================================
    # GENERAL 365-DAY FACTOR ELIGIBILITY
    # =====================================================

    general_factor_eligible = (
        candle_quality_ok
        and
        weekday_coverage
        >=
        MIN_WEEKDAY_COVERAGE
    )


    # =====================================================
    # SAVE RESULT
    # =====================================================

    results.append(
        {
            "native_ticker":
            ticker,

            "rtoken_symbol":
            symbol,

            "weekday_expected":
            weekday_expected,

            "weekday_available":
            weekday_available,

            "weekday_coverage_pct":
            weekday_coverage,

            "first_weekend_candle":
            first_weekend_candle,

            "active_weekend_expected":
            active_weekend_expected,

            "active_weekend_available":
            active_weekend_available,

            "active_weekend_coverage_pct":
            active_weekend_coverage,

            "full_active_weekends":
            full_active_weekends,

            "usable_active_weekends":
            usable_active_weekends,

            "duplicates":
            duplicates,

            "invalid_high":
            invalid_high,

            "invalid_low":
            invalid_low,

            "general_factor_eligible":
            general_factor_eligible
        }
    )


    print(
        "Weekday coverage:",
        round(
            weekday_coverage,
            2
        ),
        "%"
    )


    print(
        "First weekend candle:",
        first_weekend_candle
    )


    print(
        "Active weekend coverage:",
        round(
            active_weekend_coverage,
            2
        ),
        "%"
    )


    print(
        "Usable active weekends:",
        usable_active_weekends
    )


# =========================================================
# RESULT TABLE
# =========================================================

results = pd.DataFrame(
    results
)


results.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# SUMMARY
# =========================================================

general = results[
    results[
        "general_factor_eligible"
    ]
]


print("\n====================================")
print("CORRECTED V2 QUALITY SUMMARY")
print("====================================")


print(
    "Total assets:",
    len(results)
)


print(
    "General-factor eligible:",
    len(general)
)


print(
    "Average weekday coverage:",
    round(
        results[
            "weekday_coverage_pct"
        ].mean(),
        2
    ),
    "%"
)


print(
    "\nGENERAL FACTOR UNIVERSE:\n"
)


print(
    general[
        [
            "native_ticker",
            "weekday_coverage_pct",
            "first_weekend_candle",
            "usable_active_weekends"
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
    "\nWEEKEND AVAILABILITY:\n"
)


print(
    results[
        [
            "native_ticker",
            "first_weekend_candle",
            "active_weekend_coverage_pct",
            "usable_active_weekends"
        ]
    ]
    .sort_values(
        "usable_active_weekends",
        ascending=False
    )
    .round(2)
    .to_string(
        index=False
    )
)


print("\n====================================")
print("REASSESSMENT COMPLETE")
print("====================================")


print(
    "Saved to:",
    OUTPUT_FILE
)


print(
    "\nNo strategy returns were calculated."
)