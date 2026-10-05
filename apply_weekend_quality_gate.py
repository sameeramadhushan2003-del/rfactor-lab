import pandas as pd
from pathlib import Path


# =========================================================
# FILES
# =========================================================

SPLIT_FILE = Path(
    "data/research_asset_split.csv"
)

QUALITY_FILE = Path(
    "data/universe_quality_report.csv"
)

OUTPUT_FILE = Path(
    "data/research_asset_split_quality.csv"
)


# =========================================================
# FROZEN QUALITY RULES
# =========================================================

MIN_OVERALL_COVERAGE = 80.0

MIN_WEEKEND_COVERAGE = 60.0


print("====================================")
print("rFactor Lab")
print("Weekend Quality Gate")
print("====================================")


# =========================================================
# LOAD
# =========================================================

split = pd.read_csv(
    SPLIT_FILE
)

quality = pd.read_csv(
    QUALITY_FILE
)


# Only take quality columns we need

quality = quality[
    [
        "native_ticker",
        "rtoken_symbol",
        "research_group",
        "duplicates",
        "invalid_high",
        "invalid_low",
        "coverage_pct",
        "weekend_coverage_pct"
    ]
]


# =========================================================
# MERGE
# =========================================================

df = split.merge(
    quality,
    on=[
        "native_ticker",
        "rtoken_symbol",
        "research_group"
    ],
    how="left",
    suffixes=(
        "_scan",
        "_quality"
    )
)


# =========================================================
# QUALITY TESTS
# =========================================================

df[
    "overall_quality_ok"
] = (
    df[
        "coverage_pct_quality"
    ]
    >= MIN_OVERALL_COVERAGE
)


df[
    "weekend_quality_ok"
] = (
    df[
        "weekend_coverage_pct"
    ]
    >= MIN_WEEKEND_COVERAGE
)


df[
    "candle_quality_ok"
] = (
    (df["duplicates"] == 0)
    &
    (df["invalid_high"] == 0)
    &
    (df["invalid_low"] == 0)
)


df[
    "weekend_factor_eligible"
] = (
    df[
        "overall_quality_ok"
    ]
    &
    df[
        "weekend_quality_ok"
    ]
    &
    df[
        "candle_quality_ok"
    ]
)


# =========================================================
# SAVE
# =========================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# SUMMARY
# =========================================================

print("\n1. QUALITY RULE")

print(
    "Minimum overall coverage:",
    MIN_OVERALL_COVERAGE,
    "%"
)

print(
    "Minimum weekend coverage:",
    MIN_WEEKEND_COVERAGE,
    "%"
)


print("\n2. ELIGIBLE ASSETS BY GROUP")


summary = (
    df.groupby(
        "research_group"
    )[
        "weekend_factor_eligible"
    ]
    .agg(
        [
            "count",
            "sum"
        ]
    )
)


summary = summary.rename(
    columns={
        "count":
        "total_assets",

        "sum":
        "eligible_assets"
    }
)


summary[
    "excluded_assets"
] = (
    summary[
        "total_assets"
    ]
    -
    summary[
        "eligible_assets"
    ]
)


print(summary)


# =========================================================
# DEVELOPMENT ASSETS
# =========================================================

print(
    "\n3. DEVELOPMENT ASSETS ALLOWED "
    "FOR FACTOR RESEARCH\n"
)


development = df[
    (
        df["research_group"]
        == "Development"
    )
    &
    (
        df[
            "weekend_factor_eligible"
        ]
    )
]


print(
    development[
        [
            "native_ticker",
            "rtoken_symbol",
            "coverage_pct_quality",
            "weekend_coverage_pct"
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


# =========================================================
# EXCLUDED ASSETS
# =========================================================

print(
    "\n4. EXCLUDED FOR WEEKEND FACTORS\n"
)


excluded = df[
    ~df[
        "weekend_factor_eligible"
    ]
]


print(
    excluded[
        [
            "native_ticker",
            "research_group",
            "coverage_pct_quality",
            "weekend_coverage_pct"
        ]
    ]
    .sort_values(
        [
            "research_group",
            "weekend_coverage_pct"
        ]
    )
    .round(2)
    .to_string(
        index=False
    )
)


print("\n====================================")
print("QUALITY GATE FROZEN")
print("====================================")

print(
    "Saved to:",
    OUTPUT_FILE
)

print(
    "\nDo NOT change the 60% threshold "
    "after factor results are observed."
)