import pandas as pd
import numpy as np
from pathlib import Path


# =========================================================
# FROZEN SETTINGS
# DO NOT MODIFY AFTER OOS RESULTS ARE SEEN
# =========================================================

ASSETS = {
    "rNVDA": Path("data/rNVDA_1H_prepared.csv"),
    "rAAPL": Path("data/rAAPL_1H_prepared.csv"),
    "rTSLA": Path("data/rTSLA_1H_prepared.csv")
}

DEVELOPMENT_DAYS = 60

VOLATILITY_WINDOW = 24

Z_THRESHOLD = 1.5

HORIZON = 3

ROUND_TRIP_COST_PCT = 0.10


print("====================================")
print("rFactor Lab")
print("FINAL OUT-OF-SAMPLE TEST")
print("====================================")


# =========================================================
# FIND PROJECT START
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

OOS_START = (
    PROJECT_START
    + pd.Timedelta(days=DEVELOPMENT_DAYS)
)


print("\nProject start:", PROJECT_START)

print("Out-of-sample starts:", OOS_START)


# =========================================================
# STORE TRADES
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
    # Only information already available is used.
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
    # IDENTIFY WEEKEND BLOCKS
    # =====================================================

    df["is_weekend"] = (
        df["session"] == "Weekend"
    )


    df["weekend_start"] = (
        df["is_weekend"]
        &
        ~df["is_weekend"].shift(
            1,
            fill_value=False
        )
    )


    df["weekend_id"] = (
        df["weekend_start"]
        .cumsum()
    )


    weekend_ids = (
        df.loc[
            df["is_weekend"],
            "weekend_id"
        ]
        .unique()
    )


    next_allowed_index = -1

    asset_trades = 0


    # =====================================================
    # PROCESS WEEKENDS
    # =====================================================

    for weekend_id in weekend_ids:

        weekend = df[
            (df["weekend_id"] == weekend_id)
            &
            df["is_weekend"]
        ].copy()


        if weekend.empty:

            continue


        first_index = weekend.index[0]


        if first_index == 0:

            continue


        # -------------------------------------------------
        # PRE-WEEKEND REFERENCE PRICE
        # -------------------------------------------------

        previous = df.loc[
            :first_index - 1
        ]


        previous_valid = previous[
            previous["close"].notna()
        ]


        if previous_valid.empty:

            continue


        reference_price = (
            previous_valid.iloc[-1]["close"]
        )


        weekend["hours_from_reference"] = (
            np.arange(
                1,
                len(weekend) + 1
            )
        )


        weekend["dislocation"] = (
            weekend["close"]
            /
            reference_price
            - 1
        )


        weekend["expected_move"] = (
            weekend["volatility_24h"]
            *
            np.sqrt(
                weekend["hours_from_reference"]
            )
        )


        weekend["dislocation_z"] = (
            weekend["dislocation"].abs()
            /
            weekend["expected_move"]
        )


        # =================================================
        # SIGNAL SEARCH
        # =================================================

        for i in weekend.index:

            if i <= next_allowed_index:
                continue


            row = df.loc[i]

            weekend_row = weekend.loc[i]


            # ---------------------------------------------
            # OUT-OF-SAMPLE SIGNALS ONLY
            # ---------------------------------------------

            if (
                row["datetime_utc"]
                < OOS_START
            ):
                continue


            if pd.isna(
                weekend_row["dislocation_z"]
            ):
                continue


            if (
                weekend_row["dislocation_z"]
                < Z_THRESHOLD
            ):
                continue


            if pd.isna(
                weekend_row["dislocation"]
            ):
                continue


            # ---------------------------------------------
            # FUTURE 3-HOUR WINDOW
            # ---------------------------------------------

            future = df.iloc[
                i + 1:
                i + HORIZON + 1
            ]


            if len(future) != HORIZON:
                continue


            if not (
                future["session"]
                == "Weekend"
            ).all():
                continue


            if (
                future["open"].isna().any()
                or
                future["close"].isna().any()
            ):
                continue


            entry_price = (
                future.iloc[0]["open"]
            )

            exit_price = (
                future.iloc[-1]["close"]
            )


            # ---------------------------------------------
            # FROZEN MEAN-REVERSION SIGNAL
            # ---------------------------------------------

            signal = (
                -np.sign(
                    weekend_row["dislocation"]
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


            gross_strategy_return = (
                signal
                *
                raw_return
            )


            net_strategy_return = (
                gross_strategy_return
                -
                (
                    ROUND_TRIP_COST_PCT
                    / 100
                )
            )


            all_trades.append(
                {
                    "asset":
                    asset,

                    "signal_time":
                    row["datetime_utc"],

                    "dislocation_pct":
                    weekend_row[
                        "dislocation"
                    ] * 100,

                    "dislocation_z":
                    weekend_row[
                        "dislocation_z"
                    ],

                    "entry_price":
                    entry_price,

                    "exit_price":
                    exit_price,

                    "gross_return_pct":
                    gross_strategy_return
                    * 100,

                    "net_return_pct":
                    net_strategy_return
                    * 100
                }
            )


            asset_trades += 1

            next_allowed_index = (
                i + HORIZON
            )


    print(
        "Out-of-sample trades:",
        asset_trades
    )


# =========================================================
# RESULTS
# =========================================================

results = pd.DataFrame(
    all_trades
)


print("\n====================================")
print("OUT-OF-SAMPLE RESULTS")
print("====================================")


if results.empty:

    print(
        "No qualifying OOS trades occurred."
    )

    raise SystemExit


results = results.sort_values(
    "signal_time"
).reset_index(drop=True)


# =========================================================
# EQUITY CURVE
# =========================================================

results["net_return"] = (
    results["net_return_pct"]
    / 100
)


results["equity"] = (
    1.0
    *
    (
        1
        +
        results["net_return"]
    ).cumprod()
)


results["cumulative_return_pct"] = (
    (
        results["equity"]
        - 1
    )
    * 100
)


results["equity_peak"] = (
    results["equity"]
    .cummax()
)


results["drawdown_pct"] = (
    (
        results["equity"]
        /
        results["equity_peak"]
        - 1
    )
    * 100
)


# =========================================================
# METRICS
# =========================================================

net = results["net_return"]


total_return_pct = (
    results[
        "cumulative_return_pct"
    ].iloc[-1]
)


mean_pct = (
    results[
        "net_return_pct"
    ].mean()
)


median_pct = (
    results[
        "net_return_pct"
    ].median()
)


hit_rate = (
    (
        results[
            "net_return_pct"
        ] > 0
    ).mean()
    * 100
)


max_drawdown = (
    results[
        "drawdown_pct"
    ].min()
)


std_return = (
    net.std(ddof=1)
)


if (
    len(net) >= 2
    and
    std_return > 0
):

    trade_sharpe = (
        net.mean()
        /
        std_return
    )

else:

    trade_sharpe = np.nan


negative = net[
    net < 0
]


if len(negative) > 0:

    downside = np.sqrt(
        np.mean(
            np.square(
                negative
            )
        )
    )

else:

    downside = np.nan


if (
    not np.isnan(downside)
    and
    downside > 0
):

    trade_sortino = (
        net.mean()
        /
        downside
    )

else:

    trade_sortino = np.nan


# =========================================================
# PRINT FINAL RESULT
# =========================================================

print(
    "Trades:",
    len(results)
)

print(
    "Net cumulative return:",
    round(
        total_return_pct,
        4
    ),
    "%"
)

print(
    "Average net trade:",
    round(
        mean_pct,
        4
    ),
    "%"
)

print(
    "Median net trade:",
    round(
        median_pct,
        4
    ),
    "%"
)

print(
    "Win rate:",
    round(
        hit_rate,
        2
    ),
    "%"
)

print(
    "Maximum drawdown:",
    round(
        max_drawdown,
        4
    ),
    "%"
)

print(
    "Trade-level Sharpe:",
    round(
        trade_sharpe,
        4
    )
)

print(
    "Trade-level Sortino:",
    round(
        trade_sortino,
        4
    )
)


# =========================================================
# ASSET BREAKDOWN
# =========================================================

print("\nRESULTS BY ASSET")


asset_summary = (
    results.groupby("asset")
    .agg(
        trades=(
            "net_return_pct",
            "count"
        ),

        avg_net_pct=(
            "net_return_pct",
            "mean"
        ),

        median_net_pct=(
            "net_return_pct",
            "median"
        ),

        hit_rate_pct=(
            "net_return_pct",
            lambda x:
            (
                x > 0
            ).mean() * 100
        )
    )
)


print(
    asset_summary.round(4)
)


# =========================================================
# SAVE
# =========================================================

OUTPUT_FILE = Path(
    "data/final_out_of_sample_results.csv"
)


results.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n====================================")
print("FINAL OOS TEST COMPLETE")
print("====================================")

print(
    "Saved to:",
    OUTPUT_FILE
)

print(
    "IMPORTANT: Do not modify the "
    "strategy after seeing these results."
)