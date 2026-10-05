import pandas as pd
import numpy as np
from pathlib import Path


# =========================================================
# SETTINGS
# =========================================================

INPUT_FILE = Path(
    "data/weekend_dislocation_development.csv"
)

OUTPUT_FILE = Path(
    "data/candidate_backtest_development.csv"
)

HORIZON = 3

# Assumed round-trip trading cost.
# This is a modelling assumption, NOT a claimed Bitget fee.
ROUND_TRIP_COST_PCT = 0.10


print("====================================")
print("rFactor Lab")
print("Development Backtest")
print("====================================")


# =========================================================
# LOAD
# =========================================================

df = pd.read_csv(INPUT_FILE)

df["signal_time"] = pd.to_datetime(
    df["signal_time"],
    utc=True
)

df["strategy_return_pct"] = pd.to_numeric(
    df["strategy_return_pct"],
    errors="coerce"
)


# =========================================================
# KEEP FROZEN STRATEGY
# =========================================================

df = df[
    df["horizon_hours"] == HORIZON
].copy()


df = df.sort_values(
    "signal_time"
).reset_index(drop=True)


# =========================================================
# COSTS
# =========================================================

df["gross_return"] = (
    df["strategy_return_pct"]
    / 100
)

df["cost"] = (
    ROUND_TRIP_COST_PCT
    / 100
)

df["net_return"] = (
    df["gross_return"]
    -
    df["cost"]
)


print("\nTrades:", len(df))

print(
    "Assumed round-trip cost:",
    ROUND_TRIP_COST_PCT,
    "%"
)


# =========================================================
# EQUITY CURVE
# =========================================================

INITIAL_CAPITAL = 1.0

df["equity"] = (
    INITIAL_CAPITAL
    *
    (1 + df["net_return"])
    .cumprod()
)


df["cumulative_return_pct"] = (
    (
        df["equity"]
        / INITIAL_CAPITAL
    )
    - 1
) * 100


# =========================================================
# DRAWDOWN
# =========================================================

df["equity_peak"] = (
    df["equity"]
    .cummax()
)

df["drawdown"] = (
    df["equity"]
    /
    df["equity_peak"]
    - 1
)

df["drawdown_pct"] = (
    df["drawdown"] * 100
)


max_drawdown_pct = (
    df["drawdown_pct"]
    .min()
)


# =========================================================
# BASIC METRICS
# =========================================================

net = df["net_return"]


mean_trade = (
    net.mean()
)

median_trade = (
    net.median()
)

std_trade = (
    net.std(ddof=1)
)

hit_rate = (
    (net > 0).mean()
    * 100
)


total_return_pct = (
    df["cumulative_return_pct"]
    .iloc[-1]
)


# =========================================================
# TRADE-LEVEL SHARPE
# =========================================================

if std_trade > 0:

    trade_sharpe = (
        mean_trade
        /
        std_trade
    )

else:

    trade_sharpe = np.nan


# =========================================================
# SORTINO
# =========================================================

negative_returns = net[
    net < 0
]


downside_deviation = (
    np.sqrt(
        np.mean(
            np.square(
                negative_returns
            )
        )
    )
    if len(negative_returns) > 0
    else np.nan
)


if (
    not np.isnan(downside_deviation)
    and downside_deviation > 0
):

    trade_sortino = (
        mean_trade
        /
        downside_deviation
    )

else:

    trade_sortino = np.nan


# =========================================================
# ANNUALIZATION ESTIMATE
# =========================================================

first_time = (
    df["signal_time"].min()
)

last_time = (
    df["signal_time"].max()
)


period_days = (
    last_time
    - first_time
).total_seconds() / 86400


if period_days > 0:

    trades_per_year = (
        len(df)
        /
        period_days
        * 365.25
    )

else:

    trades_per_year = np.nan


if (
    not np.isnan(
        trades_per_year
    )
    and
    trades_per_year > 0
):

    annualized_sharpe = (
        trade_sharpe
        *
        np.sqrt(
            trades_per_year
        )
    )

    annualized_sortino = (
        trade_sortino
        *
        np.sqrt(
            trades_per_year
        )
    )

else:

    annualized_sharpe = np.nan
    annualized_sortino = np.nan


# =========================================================
# TURNOVER
# =========================================================

# One entry + one exit = 2 notional turnovers
# per completed trade.

total_turnover_units = (
    2 * len(df)
)


if period_days > 0:

    annualized_turnover_units = (
        total_turnover_units
        /
        period_days
        * 365.25
    )

else:

    annualized_turnover_units = np.nan


# =========================================================
# PRINT RESULTS
# =========================================================

print("\n====================================")
print("DEVELOPMENT BACKTEST METRICS")
print("====================================")


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
        mean_trade * 100,
        4
    ),
    "%"
)

print(
    "Median net trade:",
    round(
        median_trade * 100,
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
        max_drawdown_pct,
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

print(
    "Estimated trades/year:",
    round(
        trades_per_year,
        2
    )
)

print(
    "Annualized Sharpe estimate:",
    round(
        annualized_sharpe,
        4
    )
)

print(
    "Annualized Sortino estimate:",
    round(
        annualized_sortino,
        4
    )
)

print(
    "Total turnover units:",
    total_turnover_units
)

print(
    "Annualized turnover units:",
    round(
        annualized_turnover_units,
        2
    )
)


# =========================================================
# ASSET BREAKDOWN
# =========================================================

print("\n====================================")
print("RESULTS BY ASSET")
print("====================================")


asset_summary = (
    df.groupby("asset")
    .agg(
        trades=(
            "net_return",
            "count"
        ),

        avg_net_return=(
            "net_return",
            "mean"
        ),

        median_net_return=(
            "net_return",
            "median"
        )
    )
)


asset_summary[
    "avg_net_return_pct"
] = (
    asset_summary[
        "avg_net_return"
    ]
    * 100
)


asset_summary[
    "median_net_return_pct"
] = (
    asset_summary[
        "median_net_return"
    ]
    * 100
)


print(
    asset_summary[
        [
            "trades",
            "avg_net_return_pct",
            "median_net_return_pct"
        ]
    ].round(4)
)


# =========================================================
# SAVE
# =========================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n====================================")
print("BACKTEST COMPLETE")
print("====================================")

print(
    "Saved to:",
    OUTPUT_FILE
)

print(
    "The final out-of-sample period "
    "was NOT used."
)