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

VOLATILITY_WINDOW = 24

# Signal occurs only when the
# 6-hour move is larger than
# 1 expected 6-hour volatility unit

STRENGTH_THRESHOLD = 1.0


print("====================================")
print("rFactor Lab")
print("Volatility-Normalized Reversion")
print("====================================")


# =========================================================
# PROJECT START
# =========================================================

starts = []


for asset, file in ASSETS.items():

    temp = pd.read_csv(file)

    temp["datetime_utc"] = pd.to_datetime(
        temp["datetime_utc"],
        utc=True
    )

    starts.append(
        temp["datetime_utc"].min()
    )


PROJECT_START = min(starts)

DEVELOPMENT_END = (
    PROJECT_START
    + pd.Timedelta(
        days=DEVELOPMENT_DAYS
    )
)


print(
    "\nDevelopment:",
    PROJECT_START,
    "→",
    DEVELOPMENT_END
)


# =========================================================
# STORE RESULTS
# =========================================================

all_results = []


# =========================================================
# PROCESS EACH ASSET
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
    # HOURLY RETURN
    # =====================================================

    df["return_1h"] = (
        df["close"]
        /
        df["close"].shift(1)
        - 1
    )


    valid_hourly = (
        df["close"].notna()
        &
        df["close"].shift(1).notna()
    )


    df.loc[
        ~valid_hourly,
        "return_1h"
    ] = np.nan


    # =====================================================
    # TRAILING 24-HOUR VOLATILITY
    #
    # shift(1) means current return is NOT
    # used to calculate its own volatility
    # =====================================================

    df["volatility_24h"] = (
        df["return_1h"]
        .shift(1)
        .rolling(
            VOLATILITY_WINDOW,
            min_periods=12
        )
        .std()
    )


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


    # Require complete 7-price window

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
    # EXPECTED 6-HOUR VOLATILITY
    # =====================================================

    df["expected_vol_6h"] = (
        df["volatility_24h"]
        *
        np.sqrt(
            MOMENTUM_HOURS
        )
    )


    # =====================================================
    # FACTOR STRENGTH
    # =====================================================

    df["factor_strength"] = (
        df["momentum_6h"].abs()
        /
        df["expected_vol_6h"]
    )


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


    # Next hour must also be weekend

    df["next_session"] = (
        df["session"].shift(-1)
    )


    # =====================================================
    # EXTREME WEEKEND SIGNALS ONLY
    # =====================================================

    signals = df[
        (df["session"] == "Weekend")
        &
        (df["next_session"] == "Weekend")
        &
        (
            df["factor_strength"]
            >= STRENGTH_THRESHOLD
        )
        &
        df["momentum_6h"].notna()
        &
        df["forward_return_1h"].notna()
    ].copy()


    # =====================================================
    # MEAN-REVERSION POSITION
    # =====================================================

    signals["signal"] = (
        -np.sign(
            signals["momentum_6h"]
        )
    )


    signals["strategy_return"] = (
        signals["signal"]
        *
        signals["forward_return_1h"]
    )


    signals["strategy_return_pct"] = (
        signals["strategy_return"]
        * 100
    )


    signals["asset"] = asset


    print(
        "Extreme signals:",
        len(signals)
    )


    all_results.append(
        signals[
            [
                "datetime_utc",
                "asset",
                "momentum_6h",
                "factor_strength",
                "forward_return_1h",
                "strategy_return_pct"
            ]
        ]
    )


# =========================================================
# COMBINE RESULTS
# =========================================================

results = pd.concat(
    all_results,
    ignore_index=True
)


results["correct"] = (
    results["strategy_return_pct"]
    > 0
)


# =========================================================
# T STAT
# =========================================================

def calculate_t_stat(series):

    x = series.dropna()

    if len(x) < 2:

        return np.nan


    std = x.std(ddof=1)


    if std == 0:

        return np.nan


    return (
        x.mean()
        /
        (
            std
            /
            np.sqrt(len(x))
        )
    )


# =========================================================
# ASSET SUMMARY
# =========================================================

summary = (
    results.groupby("asset")
    .agg(

        signals=(
            "strategy_return_pct",
            "count"
        ),

        mean_return_pct=(
            "strategy_return_pct",
            "mean"
        ),

        median_return_pct=(
            "strategy_return_pct",
            "median"
        ),

        std_pct=(
            "strategy_return_pct",
            "std"
        ),

        hit_rate_pct=(
            "correct",
            lambda x:
            x.mean() * 100
        ),

        avg_strength=(
            "factor_strength",
            "mean"
        ),

        t_stat=(
            "strategy_return_pct",
            calculate_t_stat
        )
    )
)


print(
    "\n1. EXTREME REVERSION BY ASSET"
)

print(
    summary.round(4)
)


# =========================================================
# COMBINED
# =========================================================

combined = (
    results[
        "strategy_return_pct"
    ]
)


print(
    "\n2. COMBINED RESULTS"
)


print(
    "Signals:",
    len(results)
)

print(
    "Mean:",
    round(
        combined.mean(),
        4
    ),
    "%"
)

print(
    "Median:",
    round(
        combined.median(),
        4
    ),
    "%"
)

print(
    "Hit rate:",
    round(
        (
            combined > 0
        ).mean() * 100,
        2
    ),
    "%"
)

print(
    "Naive t-stat:",
    round(
        calculate_t_stat(
            combined
        ),
        4
    )
)


# =========================================================
# SAVE
# =========================================================

OUTPUT_FILE = Path(
    "data/volatility_normalized_reversion_development.csv"
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
    "Out-of-sample period remains hidden."
)