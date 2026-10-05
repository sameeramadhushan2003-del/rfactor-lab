import pandas as pd
import numpy as np
from pathlib import Path


# =========================================================
# FILES
# =========================================================

SPLIT_FILE = Path(
    "data/v2_research_split.csv"
)

PREPARED_FOLDER = Path(
    "data/v2_prepared"
)

MASK_FILE = Path(
    "data/v2_market_mask.csv"
)

RETURN_OUTPUT = Path(
    "data/v2_portfolio_returns.csv"
)

SUMMARY_OUTPUT = Path(
    "data/v2_portfolio_summary.csv"
)


# =========================================================
# PROJECT DATES
# =========================================================

PROJECT_START = pd.Timestamp(
    "2025-09-25 06:00:00",
    tz="UTC"
)

DEVELOPMENT_END = (
    PROJECT_START
    + pd.Timedelta(days=240)
)

VALIDATION_END = (
    PROJECT_START
    + pd.Timedelta(days=300)
)

PROJECT_END = (
    PROJECT_START
    + pd.Timedelta(days=365)
)


# =========================================================
# FROZEN PORTFOLIO RULE
# =========================================================

QUANTILE = 0.25

MIN_RESEARCH_ASSETS = 8

MIN_HOLDOUT_ASSETS = 3


# Hypothetical one-way costs
COST_SCENARIOS_BPS = [
    0.0,
    2.5,
    5.0,
    10.0
]


print("====================================")
print("rFactor Lab")
print("V2 Factor Portfolio Backtest")
print("====================================")

print(
    "\nFrozen rule:"
)

print(
    "Bottom 25% 1h momentum = LONG"
)

print(
    "Top 25% 1h momentum = SHORT"
)

print(
    "Holding period = 1 hour"
)


# =========================================================
# LOAD SPLIT
# =========================================================

split = pd.read_csv(
    SPLIT_FILE
)


research_assets = split[
    split["v2_group"].isin(
        [
            "Development",
            "Validation"
        ]
    )
][
    "native_ticker"
].tolist()


holdout_assets = split[
    split["v2_group"]
    ==
    "AssetHoldout"
][
    "native_ticker"
].tolist()


print(
    "\nResearch assets:",
    len(research_assets)
)

print(
    "Asset holdout:",
    holdout_assets
)


# =========================================================
# MARKET MASK
# =========================================================

mask = pd.read_csv(
    MASK_FILE
)


mask["datetime_utc"] = pd.to_datetime(
    mask["datetime_utc"],
    utc=True
)


mask["expected_market_hour"] = (
    mask[
        "expected_market_hour"
    ]
    .astype(str)
    .str.lower()
    .eq("true")
)


mask = mask[
    [
        "datetime_utc",
        "expected_market_hour"
    ]
]


# =========================================================
# LOAD ASSET DATA
# =========================================================

def load_assets(tickers):

    frames = []


    for ticker in tickers:

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


        df = df.merge(
            mask,
            on="datetime_utc",
            how="left"
        )


        df[
            "expected_market_hour"
        ] = (
            df[
                "expected_market_hour"
            ]
            .fillna(False)
        )


        df["px"] = (
            df["close"]
            .where(
                df[
                    "expected_market_hour"
                ]
            )
        )


        # Previous 1-hour return
        df["momentum_1h"] = (
            df["px"]
            /
            df["px"].shift(1)
            -
            1
        )


        valid_signal = (
            df["px"].notna()
            &
            df["px"]
            .shift(1)
            .notna()
        )


        df.loc[
            ~valid_signal,
            "momentum_1h"
        ] = np.nan


        # Next 1-hour return
        df["forward_return_1h"] = (
            df["px"].shift(-1)
            /
            df["px"]
            -
            1
        )


        valid_forward = (
            df["px"].notna()
            &
            df["px"]
            .shift(-1)
            .notna()
        )


        df.loc[
            ~valid_forward,
            "forward_return_1h"
        ] = np.nan


        df["asset"] = ticker


        frames.append(
            df[
                [
                    "datetime_utc",
                    "asset",
                    "momentum_1h",
                    "forward_return_1h"
                ]
            ]
        )


    return pd.concat(
        frames,
        ignore_index=True
    )


# =========================================================
# PORTFOLIO ENGINE
# =========================================================

def build_portfolio(
    data,
    min_assets,
    universe_name
):

    rows = []

    previous_weights = {}


    for timestamp, group in (
        data.groupby(
            "datetime_utc"
        )
    ):

        valid = group[
            group[
                "momentum_1h"
            ].notna()
            &
            group[
                "forward_return_1h"
            ].notna()
        ].copy()


        n = len(valid)


        if n < min_assets:

            continue


        valid = valid.sort_values(
            "momentum_1h"
        )


        n_select = max(
            1,
            int(
                np.floor(
                    n * QUANTILE
                )
            )
        )


        longs = valid.head(
            n_select
        )


        shorts = valid.tail(
            n_select
        )


        weights = {}


        # 50% gross long exposure
        long_weight = (
            0.5
            /
            n_select
        )


        # 50% gross short exposure
        short_weight = (
            -0.5
            /
            n_select
        )


        for asset in longs["asset"]:

            weights[asset] = (
                long_weight
            )


        for asset in shorts["asset"]:

            weights[asset] = (
                short_weight
            )


        # -----------------------------------------
        # GROSS PORTFOLIO RETURN
        # -----------------------------------------

        return_map = dict(
            zip(
                valid["asset"],
                valid[
                    "forward_return_1h"
                ]
            )
        )


        gross_return = sum(
            weight
            *
            return_map[
                asset
            ]

            for asset, weight
            in weights.items()
        )


        # -----------------------------------------
        # TURNOVER
        #
        # Sum absolute weight changes.
        # -----------------------------------------

        all_assets = set(
            previous_weights
        ) | set(
            weights
        )


        turnover = sum(
            abs(
                weights.get(
                    asset,
                    0.0
                )
                -
                previous_weights.get(
                    asset,
                    0.0
                )
            )

            for asset
            in all_assets
        )


        previous_weights = (
            weights.copy()
        )


        rows.append(
            {
                "datetime_utc":
                timestamp,

                "universe":
                universe_name,

                "assets_available":
                n,

                "long_assets":
                ",".join(
                    longs[
                        "asset"
                    ].tolist()
                ),

                "short_assets":
                ",".join(
                    shorts[
                        "asset"
                    ].tolist()
                ),

                "gross_return":
                gross_return,

                "turnover":
                turnover
            }
        )


    return pd.DataFrame(
        rows
    )


# =========================================================
# BUILD PORTFOLIOS
# =========================================================

research_data = load_assets(
    research_assets
)


holdout_data = load_assets(
    holdout_assets
)


research_portfolio = build_portfolio(
    research_data,
    MIN_RESEARCH_ASSETS,
    "Research20"
)


holdout_portfolio = build_portfolio(
    holdout_data,
    MIN_HOLDOUT_ASSETS,
    "AssetHoldout3"
)


portfolio = pd.concat(
    [
        research_portfolio,
        holdout_portfolio
    ],
    ignore_index=True
)


# =========================================================
# PERIOD LABEL
# =========================================================

def period_label(timestamp):

    if timestamp < DEVELOPMENT_END:

        return "Development"

    if timestamp < VALIDATION_END:

        return "Validation"

    return "FinalTimeHoldout"


portfolio["period"] = (
    portfolio[
        "datetime_utc"
    ].apply(
        period_label
    )
)


# =========================================================
# COST SCENARIOS
# =========================================================

summary_rows = []


for cost_bps in (
    COST_SCENARIOS_BPS
):

    cost_rate = (
        cost_bps
        /
        10000
    )


    portfolio[
        f"net_return_{cost_bps}bps"
    ] = (
        portfolio[
            "gross_return"
        ]
        -
        (
            portfolio[
                "turnover"
            ]
            *
            cost_rate
        )
    )


    # =====================================================
    # SUMMARIZE BY UNIVERSE + PERIOD
    # =====================================================

    for (
        universe_name,
        period
    ), group in portfolio.groupby(
        [
            "universe",
            "period"
        ]
    ):

        returns = (
            group[
                f"net_return_{cost_bps}bps"
            ]
            .dropna()
        )


        if len(returns) == 0:

            continue


        equity = (
            1
            +
            returns
        ).cumprod()


        total_return = (
            equity.iloc[-1]
            -
            1
        )


        equity_peak = (
            equity.cummax()
        )


        drawdown = (
            equity
            /
            equity_peak
            -
            1
        )


        max_drawdown = (
            drawdown.min()
        )


        mean_return = (
            returns.mean()
        )


        std_return = (
            returns.std(
                ddof=1
            )
        )


        # -----------------------------------------
        # OBSERVED BARS PER YEAR
        # -----------------------------------------

        first_time = (
            group[
                "datetime_utc"
            ].min()
        )


        last_time = (
            group[
                "datetime_utc"
            ].max()
        )


        days = (
            last_time
            -
            first_time
        ).total_seconds() / 86400


        if days > 0:

            bars_per_year = (
                len(returns)
                /
                days
                *
                365.25
            )

        else:

            bars_per_year = np.nan


        # -----------------------------------------
        # NAIVE ANNUALIZED SHARPE
        # -----------------------------------------

        if (
            std_return > 0
            and
            not np.isnan(
                bars_per_year
            )
        ):

            sharpe = (
                mean_return
                /
                std_return
                *
                np.sqrt(
                    bars_per_year
                )
            )

        else:

            sharpe = np.nan


        # -----------------------------------------
        # SORTINO
        # -----------------------------------------

        downside = returns[
            returns < 0
        ]


        if len(downside) > 0:

            downside_dev = (
                np.sqrt(
                    np.mean(
                        np.square(
                            downside
                        )
                    )
                )
            )

        else:

            downside_dev = np.nan


        if (
            not np.isnan(
                downside_dev
            )
            and
            downside_dev > 0
            and
            not np.isnan(
                bars_per_year
            )
        ):

            sortino = (
                mean_return
                /
                downside_dev
                *
                np.sqrt(
                    bars_per_year
                )
            )

        else:

            sortino = np.nan


        # -----------------------------------------
        # WIN RATE
        # -----------------------------------------

        win_rate = (
            (
                returns > 0
            ).mean()
            * 100
        )


        summary_rows.append(
            {
                "universe":
                universe_name,

                "period":
                period,

                "cost_bps":
                cost_bps,

                "observations":
                len(returns),

                "cumulative_return_pct":
                total_return * 100,

                "mean_hourly_return_pct":
                mean_return * 100,

                "median_hourly_return_pct":
                returns.median() * 100,

                "win_rate_pct":
                win_rate,

                "max_drawdown_pct":
                max_drawdown * 100,

                "avg_turnover":
                group[
                    "turnover"
                ].mean(),

                "annualized_sharpe_naive":
                sharpe,

                "annualized_sortino_naive":
                sortino
            }
        )


# =========================================================
# SAVE
# =========================================================

summary = pd.DataFrame(
    summary_rows
)


portfolio.to_csv(
    RETURN_OUTPUT,
    index=False
)


summary.to_csv(
    SUMMARY_OUTPUT,
    index=False
)


# =========================================================
# DISPLAY
# =========================================================

print("\n====================================")
print("PORTFOLIO BACKTEST SUMMARY")
print("====================================\n")


print(
    summary[
        [
            "universe",
            "period",
            "cost_bps",
            "observations",
            "cumulative_return_pct",
            "win_rate_pct",
            "max_drawdown_pct",
            "avg_turnover",
            "annualized_sharpe_naive"
        ]
    ]
    .round(4)
    .to_string(
        index=False
    )
)


print("\n====================================")
print("BACKTEST COMPLETE")
print("====================================")


print(
    "Returns:",
    RETURN_OUTPUT
)

print(
    "Summary:",
    SUMMARY_OUTPUT
)

print(
    "\nCost scenarios are hypothetical."
)

print(
    "Naive annualized Sharpe does not "
    "correct for serial dependence."
)