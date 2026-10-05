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

OUTPUT_FILE = Path(
    "data/v2_missingness_diagnosis.csv"
)


print("====================================")
print("rFactor Lab")
print("V2 Missingness Diagnosis")
print("====================================")


# =========================================================
# LOAD UNIVERSE
# =========================================================

universe = pd.read_csv(
    UNIVERSE_FILE
)


all_rows = []


# =========================================================
# PROCESS EACH ASSET
# =========================================================

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


    df["asset"] = ticker


    df["et_weekday_num"] = (
        df["datetime_et"]
        .dt.weekday
    )


    df["et_weekday"] = (
        df["datetime_et"]
        .dt.day_name()
    )


    df["et_hour"] = (
        df["datetime_et"]
        .dt.hour
    )


    df["available"] = (
        df["close"].notna()
    )


    all_rows.append(
        df[
            [
                "datetime_utc",
                "datetime_et",
                "asset",
                "session",
                "et_weekday_num",
                "et_weekday",
                "et_hour",
                "available"
            ]
        ]
    )


# =========================================================
# COMBINE
# =========================================================

data = pd.concat(
    all_rows,
    ignore_index=True
)


# =========================================================
# WEEKDAY DATA ONLY
# =========================================================

weekday = data[
    data["et_weekday_num"] < 5
].copy()


# =========================================================
# 1. COVERAGE BY SESSION
# =========================================================

session_summary = (
    weekday.groupby(
        "session"
    )
    .agg(
        expected=(
            "available",
            "size"
        ),

        available=(
            "available",
            "sum"
        )
    )
)


session_summary[
    "coverage_pct"
] = (
    session_summary["available"]
    /
    session_summary["expected"]
    * 100
)


print("\n====================================")
print("1. WEEKDAY COVERAGE BY SESSION")
print("====================================\n")


print(
    session_summary
    .round(2)
)


# =========================================================
# 2. COVERAGE BY ET HOUR
# =========================================================

hour_summary = (
    weekday.groupby(
        "et_hour"
    )
    .agg(
        expected=(
            "available",
            "size"
        ),

        available=(
            "available",
            "sum"
        )
    )
)


hour_summary[
    "coverage_pct"
] = (
    hour_summary["available"]
    /
    hour_summary["expected"]
    * 100
)


print("\n====================================")
print("2. WEEKDAY COVERAGE BY ET HOUR")
print("====================================\n")


print(
    hour_summary
    .round(2)
)


# =========================================================
# 3. COVERAGE BY WEEKDAY
# =========================================================

day_summary = (
    weekday.groupby(
        [
            "et_weekday_num",
            "et_weekday"
        ]
    )
    .agg(
        expected=(
            "available",
            "size"
        ),

        available=(
            "available",
            "sum"
        )
    )
)


day_summary[
    "coverage_pct"
] = (
    day_summary["available"]
    /
    day_summary["expected"]
    * 100
)


print("\n====================================")
print("3. COVERAGE BY WEEKDAY")
print("====================================\n")


print(
    day_summary
    .round(2)
)


# =========================================================
# 4. WEEKDAY + HOUR MATRIX
# =========================================================

matrix = (
    weekday.groupby(
        [
            "et_weekday",
            "et_hour"
        ]
    )[
        "available"
    ]
    .mean()
    .mul(100)
    .unstack()
)


day_order = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday"
]


matrix = matrix.reindex(
    day_order
)


print("\n====================================")
print("4. COVERAGE MATRIX (%)")
print("====================================\n")


print(
    matrix.round(1)
    .to_string()
)


# =========================================================
# 5. ASSET WEEKDAY COVERAGE
# =========================================================

asset_summary = (
    weekday.groupby(
        "asset"
    )
    .agg(
        expected=(
            "available",
            "size"
        ),

        available=(
            "available",
            "sum"
        )
    )
)


asset_summary[
    "coverage_pct"
] = (
    asset_summary["available"]
    /
    asset_summary["expected"]
    * 100
)


print("\n====================================")
print("5. COVERAGE BY ASSET")
print("====================================\n")


print(
    asset_summary
    .sort_values(
        "coverage_pct",
        ascending=False
    )
    .round(2)
)


# =========================================================
# SAVE
# =========================================================

asset_summary.reset_index().to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n====================================")
print("DIAGNOSIS COMPLETE")
print("====================================")


print(
    "Saved to:",
    OUTPUT_FILE
)

print(
    "\nNo strategy or factor performance "
    "was calculated."
)