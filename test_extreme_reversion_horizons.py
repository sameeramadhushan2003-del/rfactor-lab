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

STRENGTH_THRESHOLD = 1.0

HORIZONS = [
    1,
    3,
    6
]


print("====================================")
print("rFactor Lab")
print("Extreme Reversion Horizon Test")
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
    + pd.Timedelta(days=DEVELOPMENT_DAYS)
)


print(
    "\nDevelopment:",
    PROJECT_START,
    "→",
    DEVELOPMENT_END
)


# =========================================================
# STORE ALL TRADES
# =========================================================

all_trades = []


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


    for column in [
        "open",
        "close"
    ]:

        df[column] = pd.to_numeric(
            df[column],
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
    # HOURLY RETURNS
    # =====================================================

    df["return_1h"] = (
        df["close"]
        /
        df["close"].shift(1)
        - 1
    )


    valid_return = (
        df["close"].notna()
        &
        df["close"].shift(1).notna()
    )


    df.loc[
        ~valid_return,
        "return_1h"
    ] = np.nan


    # =====================================================
    # TRAILING VOLATILITY
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
    # VOLATILITY-NORMALIZED STRENGTH
    # =====================================================

    df["expected_vol_6h"] = (
        df["volatility_24h"]
        *
        np.sqrt(MOMENTUM_HOURS)
    )


    df["factor_strength"] = (
        df["momentum_6h"].abs()
        /
        df["expected_vol_6h"]
    )


    # =====================================================
    # TEST EACH HORIZON
    # =====================================================

    for horizon in HORIZONS:

        next_allowed_index = 0

        trade_count = 0


        for i in range(
            len(df) - horizon
        ):

            # Prevent overlapping positions

            if i < next_allowed_index:

                continue


            row = df.iloc[i]


            # ---------------------------------------------
            # SIGNAL REQUIREMENTS
            # ---------------------------------------------

            if row["session"] != "Weekend":

                continue


            if pd.isna(
                row["momentum_6h"]
            ):

                continue


            if pd.isna(
                row["factor_strength"]
            ):

                continue


            if (
                row["factor_strength"]
                < STRENGTH_THRESHOLD
            ):

                continue


            # ---------------------------------------------
            # FUTURE HOLDING WINDOW
            # ---------------------------------------------

            future = df.iloc[
                i + 1:
                i + horizon + 1
            ]


            if len(future) != horizon:

                continue


            # Every holding hour must remain weekend

            if not (
                future["session"]
                == "Weekend"
            ).all():

                continue


            # Entry = next hour OPEN

            entry_price = (
                future.iloc[0]["open"]
            )


            # Exit = final holding hour CLOSE

            exit_price = (
                future.iloc[-1]["close"]
            )


            if (
                pd.isna(entry_price)
                or
                pd.isna(exit_price)
            ):

                continue


            # Require complete prices in holding window

            if future["close"].isna().any():

                continue


            # ---------------------------------------------
            # MEAN-REVERSION SIGNAL
            # ---------------------------------------------

            signal = (
                -np.sign(
                    row["momentum_6h"]
                )
            )


            if signal == 0:

                continue


            raw_return = (
                exit_price
                /
                entry_price
                - 1
            )


            strategy_return = (
                signal
                *
                raw_return
            )


            all_trades.append(
                {
                    "asset":
                    asset,

                    "signal_time":
                    row["datetime_utc"],

                    "horizon_hours":
                    horizon,

                    "factor_strength":
                    row["factor_strength"],

                    "momentum_6h_pct":
                    row["momentum_6h"]
                    * 100,

                    "signal":
                    signal,

                    "entry_price":
                    entry_price,

                    "exit_price":
                    exit_price,

                    "raw_return_pct":
                    raw_return * 100,

                    "strategy_return_pct":
                    strategy_return * 100
                }
            )


            trade_count += 1


            # Do not allow another signal
            # until this position is finished

            next_allowed_index = (
                i + horizon + 1
            )


        print(
            horizon,
            "hour trades:",
            trade_count
        )


# =========================================================
# CREATE RESULT TABLE
# =========================================================

results = pd.DataFrame(
    all_trades
)


if results.empty:

    raise SystemExit(
        "No valid trades found."
    )


results["winner"] = (
    results["strategy_return_pct"]
    > 0
)


# =========================================================
# SUMMARY FUNCTION
# =========================================================

def summarize(group):

    values = group[
        "strategy_return_pct"
    ]


    return pd.Series(
        {
            "trades":
            len(values),

            "mean_pct":
            values.mean(),

            "median_pct":
            values.median(),

            "std_pct":
            values.std(),

            "hit_rate_pct":
            (
                values > 0
            ).mean() * 100
        }
    )


# =========================================================
# COMBINED BY HORIZON
# =========================================================

print(
    "\n1. COMBINED RESULTS BY HORIZON"
)


combined = (
    results.groupby(
        "horizon_hours"
    )
    .apply(
        summarize,
        include_groups=False
    )
)


print(
    combined.round(4)
)


# =========================================================
# BY ASSET AND HORIZON
# =========================================================

print(
    "\n2. RESULTS BY ASSET AND HORIZON"
)


asset_results = (
    results.groupby(
        [
            "asset",
            "horizon_hours"
        ]
    )
    .apply(
        summarize,
        include_groups=False
    )
)


print(
    asset_results.round(4)
)


# =========================================================
# SAVE
# =========================================================

OUTPUT_FILE = Path(
    "data/extreme_reversion_horizons_development.csv"
)


results.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n====================================")
print("HORIZON TEST COMPLETE")
print("====================================")

print(
    "Saved to:",
    OUTPUT_FILE
)

print(
    "Out-of-sample data remains hidden."
)