import pandas as pd
import numpy as np
from pathlib import Path


# =========================================================
# SETTINGS
# =========================================================

ASSETS = {
    "rNVDA": Path("data/rNVDA_1H_prepared.csv"),
    "rAAPL": Path("data/rAAPL_1H_prepared.csv"),
    "rTSLA": Path("data/rTSLA_1H_prepared.csv")
}

DEVELOPMENT_DAYS = 60

MOMENTUM_HOURS = 6


print("====================================")
print("rFactor Lab")
print("Multi-Asset Weekend Mean Reversion")
print("====================================")


# =========================================================
# GET COMMON PROJECT START
# =========================================================

start_times = []


for asset, file in ASSETS.items():

    temp = pd.read_csv(file)

    temp["datetime_utc"] = pd.to_datetime(
        temp["datetime_utc"],
        utc=True
    )

    start_times.append(
        temp["datetime_utc"].min()
    )


PROJECT_START = min(start_times)

DEVELOPMENT_END = (
    PROJECT_START
    + pd.Timedelta(days=DEVELOPMENT_DAYS)
)


print("\nDevelopment start:", PROJECT_START)

print("Development end:", DEVELOPMENT_END)


# =========================================================
# STORE RESULTS
# =========================================================

all_results = []


# =========================================================
# PROCESS EACH RTOKEN
# =========================================================

for asset, file in ASSETS.items():

    print("\n====================================")
    print("Processing:", asset)
    print("====================================")


    df = pd.read_csv(file)


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
        < DEVELOPMENT_END
    ].copy()


    df = df.sort_values(
        "datetime_utc"
    ).reset_index(drop=True)


    # =====================================================
    # 6-HOUR MOMENTUM
    # =====================================================

    df["momentum_6h"] = (
        df["close"]
        /
        df["close"].shift(
            MOMENTUM_HOURS
        )
        - 1
    )


    # =====================================================
    # REQUIRE ALL 7 PRICES
    # current + previous 6 hours
    # =====================================================

    valid_momentum_window = (
        df["close"]
        .notna()
        .rolling(
            MOMENTUM_HOURS + 1
        )
        .sum()
    )


    df.loc[
        valid_momentum_window
        != MOMENTUM_HOURS + 1,
        "momentum_6h"
    ] = np.nan


    # =====================================================
    # NEXT-HOUR RETURN
    # =====================================================

    df["forward_return_1h"] = (
        df["close"].shift(-1)
        /
        df["close"]
        - 1
    )


    valid_forward = (
        df["close"].notna()
        &
        df["close"].shift(-1).notna()
    )


    df.loc[
        ~valid_forward,
        "forward_return_1h"
    ] = np.nan


    # =====================================================
    # NEXT HOUR SESSION
    # =====================================================

    df["next_session"] = (
        df["session"].shift(-1)
    )


    # =====================================================
    # PURE WEEKEND OBSERVATIONS ONLY
    # =====================================================

    weekend = df[
        (df["session"] == "Weekend")
        &
        (df["next_session"] == "Weekend")
        &
        (df["momentum_6h"].notna())
        &
        (df["forward_return_1h"].notna())
    ].copy()


    # =====================================================
    # MEAN-REVERSION SIGNAL
    # =====================================================

    weekend["reversion_signal"] = (
        -np.sign(
            weekend["momentum_6h"]
        )
    )


    weekend["reversion_return"] = (
        weekend["reversion_signal"]
        *
        weekend["forward_return_1h"]
    )


    weekend["reversion_return_pct"] = (
        weekend["reversion_return"]
        * 100
    )


    weekend["momentum_6h_pct"] = (
        weekend["momentum_6h"]
        * 100
    )


    weekend["asset"] = asset


    print(
        "Valid weekend observations:",
        len(weekend)
    )


    all_results.append(
        weekend[
            [
                "datetime_utc",
                "asset",
                "momentum_6h_pct",
                "forward_return_1h",
                "reversion_return_pct"
            ]
        ]
    )


# =========================================================
# COMBINE
# =========================================================

results = pd.concat(
    all_results,
    ignore_index=True
)


results["reversion_correct"] = (
    results["reversion_return_pct"] > 0
)


# =========================================================
# T-STAT FUNCTION
# =========================================================

def t_stat(series):

    values = series.dropna()

    if len(values) < 2:

        return np.nan


    std = values.std(ddof=1)


    if std == 0:

        return np.nan


    return (
        values.mean()
        /
        (
            std
            /
            np.sqrt(len(values))
        )
    )


# =========================================================
# SUMMARY BY ASSET
# =========================================================

summary = (
    results.groupby("asset")
    .agg(

        observations=(
            "reversion_return_pct",
            "count"
        ),

        mean_return_pct=(
            "reversion_return_pct",
            "mean"
        ),

        median_return_pct=(
            "reversion_return_pct",
            "median"
        ),

        std_pct=(
            "reversion_return_pct",
            "std"
        ),

        hit_rate_pct=(
            "reversion_correct",
            lambda x:
            x.mean() * 100
        ),

        t_stat=(
            "reversion_return_pct",
            t_stat
        )
    )
)


print(
    "\n1. WEEKEND MEAN REVERSION BY ASSET"
)

print(
    summary.round(4)
)


# =========================================================
# COMBINED SUMMARY
# =========================================================

combined_values = (
    results["reversion_return_pct"]
)


combined_mean = (
    combined_values.mean()
)

combined_median = (
    combined_values.median()
)

combined_std = (
    combined_values.std()
)

combined_hit_rate = (
    (
        combined_values > 0
    ).mean()
    * 100
)

combined_t = t_stat(
    combined_values
)


print(
    "\n2. COMBINED RESULT"
)

print(
    "Observations:",
    len(results)
)

print(
    "Mean return:",
    round(
        combined_mean,
        4
    ),
    "%"
)

print(
    "Median return:",
    round(
        combined_median,
        4
    ),
    "%"
)

print(
    "Standard deviation:",
    round(
        combined_std,
        4
    ),
    "%"
)

print(
    "Hit rate:",
    round(
        combined_hit_rate,
        2
    ),
    "%"
)

print(
    "Naive t-stat:",
    round(
        combined_t,
        4
    )
)


# =========================================================
# SAVE
# =========================================================

OUTPUT_FILE = Path(
    "data/weekend_mean_reversion_multiasset.csv"
)


results.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n====================================")
print("TEST COMPLETE")
print("====================================")

print(
    "Saved to:",
    OUTPUT_FILE
)

print(
    "Development data only."
)

print(
    "Out-of-sample data remains hidden."
)