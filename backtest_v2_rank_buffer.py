import pandas as pd
import numpy as np
from pathlib import Path


# =========================================================
# FILES
# =========================================================

SPLIT_FILE = Path("data/v2_research_split.csv")
PREPARED_FOLDER = Path("data/v2_prepared")
MASK_FILE = Path("data/v2_market_mask.csv")

RETURN_OUTPUT = Path(
    "data/v2_rank_buffer_returns.csv"
)

SUMMARY_OUTPUT = Path(
    "data/v2_rank_buffer_summary.csv"
)


# =========================================================
# DATES
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
# FROZEN EXECUTION RULES
# =========================================================

ENTRY_QUANTILE = 0.25

EXIT_BUFFER = 0.40

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
print("Rank-Buffer Portfolio")
print("====================================")

print(
    "\nFactor remains frozen:"
)

print(
    "1-hour cross-sectional reversal"
)

print(
    "\nExecution:"
)

print(
    "Enter long: bottom 25%"
)

print(
    "Keep long: until above bottom 40%"
)

print(
    "Enter short: top 25%"
)

print(
    "Keep short: until below top 40%"
)


# =========================================================
# SPLIT
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
]["native_ticker"].tolist()


holdout_assets = split[
    split["v2_group"]
    ==
    "AssetHoldout"
]["native_ticker"].tolist()


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
    mask["expected_market_hour"]
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
# LOAD DATA
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


        df["px"] = df["close"].where(
            df["expected_market_hour"]
        )


        # Frozen factor
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
            df["px"].shift(1).notna()
        )


        df.loc[
            ~valid_signal,
            "momentum_1h"
        ] = np.nan


        # Next-hour return
        df["forward_return_1h"] = (
            df["px"].shift(-1)
            /
            df["px"]
            -
            1
        )


        valid_target = (
            df["px"].notna()
            &
            df["px"].shift(-1).notna()
        )


        df.loc[
            ~valid_target,
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
# BUFFER PORTFOLIO
# =========================================================

def build_buffer_portfolio(
    data,
    min_assets,
    name
):

    rows = []

    long_positions = set()
    short_positions = set()

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


        # -----------------------------------------
        # PERCENTILE RANK
        # 0 = weakest recent momentum
        # 1 = strongest recent momentum
        # -----------------------------------------

        valid["rank_pct"] = (
            valid[
                "momentum_1h"
            ]
            .rank(
                method="first",
                pct=True
            )
        )


        rank_map = dict(
            zip(
                valid["asset"],
                valid["rank_pct"]
            )
        )


        available_assets = set(
            valid["asset"]
        )


        # Remove unavailable assets
        long_positions &= available_assets
        short_positions &= available_assets


        # -----------------------------------------
        # EXIT BUFFER
        # -----------------------------------------

        long_positions = {
            asset
            for asset
            in long_positions
            if rank_map[asset]
            <= EXIT_BUFFER
        }


        short_positions = {
            asset
            for asset
            in short_positions
            if rank_map[asset]
            >= (
                1
                -
                EXIT_BUFFER
            )
        }


        # -----------------------------------------
        # TARGET NUMBER
        # -----------------------------------------

        target_count = max(
            1,
            int(
                np.floor(
                    n
                    *
                    ENTRY_QUANTILE
                )
            )
        )


        # -----------------------------------------
        # NEW LONG CANDIDATES
        # -----------------------------------------

        long_candidates = (
            valid[
                valid[
                    "rank_pct"
                ]
                <=
                ENTRY_QUANTILE
            ]
            .sort_values(
                "momentum_1h"
            )["asset"]
            .tolist()
        )


        # -----------------------------------------
        # NEW SHORT CANDIDATES
        # -----------------------------------------

        short_candidates = (
            valid[
                valid[
                    "rank_pct"
                ]
                >=
                (
                    1
                    -
                    ENTRY_QUANTILE
                )
            ]
            .sort_values(
                "momentum_1h",
                ascending=False
            )["asset"]
            .tolist()
        )


        # -----------------------------------------
        # REPLENISH LONG SIDE
        # -----------------------------------------

        for asset in long_candidates:

            if (
                len(long_positions)
                >= target_count
            ):
                break


            if (
                asset
                not in short_positions
            ):

                long_positions.add(
                    asset
                )


        # -----------------------------------------
        # REPLENISH SHORT SIDE
        # -----------------------------------------

        for asset in short_candidates:

            if (
                len(short_positions)
                >= target_count
            ):
                break


            if (
                asset
                not in long_positions
            ):

                short_positions.add(
                    asset
                )


        # Need both sides
        if (
            len(long_positions) == 0
            or
            len(short_positions) == 0
        ):

            continue


        # -----------------------------------------
        # WEIGHTS
        # -----------------------------------------

        weights = {}


        long_weight = (
            0.5
            /
            len(long_positions)
        )


        short_weight = (
            -0.5
            /
            len(short_positions)
        )


        for asset in long_positions:

            weights[asset] = (
                long_weight
            )


        for asset in short_positions:

            weights[asset] = (
                short_weight
            )


        # -----------------------------------------
        # RETURNS
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
            return_map[asset]

            for asset, weight
            in weights.items()
        )


        # -----------------------------------------
        # TURNOVER
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
                    0
                )
                -
                previous_weights.get(
                    asset,
                    0
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
                name,

                "assets_available":
                n,

                "long_count":
                len(
                    long_positions
                ),

                "short_count":
                len(
                    short_positions
                ),

                "long_assets":
                ",".join(
                    sorted(
                        long_positions
                    )
                ),

                "short_assets":
                ",".join(
                    sorted(
                        short_positions
                    )
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
# BUILD
# =========================================================

research_data = load_assets(
    research_assets
)


holdout_data = load_assets(
    holdout_assets
)


research_portfolio = (
    build_buffer_portfolio(
        research_data,
        MIN_RESEARCH_ASSETS,
        "Research20"
    )
)


holdout_portfolio = (
    build_buffer_portfolio(
        holdout_data,
        MIN_HOLDOUT_ASSETS,
        "AssetHoldout3"
    )
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
    ]
    .apply(
        period_label
    )
)


# =========================================================
# COST + METRICS
# =========================================================

summary_rows = []


for cost_bps in COST_SCENARIOS_BPS:

    cost_rate = (
        cost_bps
        /
        10000
    )


    column = (
        f"net_return_{cost_bps}bps"
    )


    portfolio[column] = (
        portfolio["gross_return"]
        -
        portfolio["turnover"]
        *
        cost_rate
    )


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
            group[column]
            .dropna()
        )


        if len(returns) == 0:
            continue


        equity = (
            1
            +
            returns
        ).cumprod()


        cumulative_return = (
            equity.iloc[-1]
            -
            1
        )


        peak = (
            equity.cummax()
        )


        drawdown = (
            equity
            /
            peak
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


        win_rate = (
            (
                returns > 0
            ).mean()
            *
            100
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
                cumulative_return
                *
                100,

                "win_rate_pct":
                win_rate,

                "max_drawdown_pct":
                max_drawdown
                *
                100,

                "avg_turnover":
                group[
                    "turnover"
                ].mean(),

                "annualized_sharpe_naive":
                sharpe
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
print("RANK-BUFFER BACKTEST SUMMARY")
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
print("RANK-BUFFER TEST COMPLETE")
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
    "\nThe factor itself was NOT changed."
)