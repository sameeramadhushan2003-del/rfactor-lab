import pandas as pd
import numpy as np
from pathlib import Path


# =========================================================
# FILES
# =========================================================

SPLIT_FILE = Path("data/v2_research_split.csv")
PREPARED_FOLDER = Path("data/v2_prepared")
MASK_FILE = Path("data/v2_market_mask.csv")

OUTPUT_FILE = Path(
    "data/v2_turnover_cap_final_validation.csv"
)
TIMESERIES_OUTPUT_FILE = Path(
    "data/v2_turnover_cap_timeseries.csv"
)

# =========================================================
# DATES
# =========================================================

PROJECT_START = pd.Timestamp(
    "2025-09-25 06:00:00",
    tz="UTC"
)

VALIDATION_START = (
    PROJECT_START
    + pd.Timedelta(days=240)
)

VALIDATION_END = (
    PROJECT_START
    + pd.Timedelta(days=300)
)

FINAL_START = (
    PROJECT_START
    + pd.Timedelta(days=300)
)

FINAL_END = (
    PROJECT_START
    + pd.Timedelta(days=365)
)


# =========================================================
# FROZEN IMPLEMENTATION
# =========================================================

QUANTILE = 0.25
MAX_TURNOVER = 0.50

COST_SCENARIOS_BPS = [
    0.0,
    2.5,
    5.0,
    10.0
]


print("====================================")
print("rFactor Lab")
print("Frozen Turnover-Cap Validation")
print("====================================")

print(
    "\nFactor: 1h cross-sectional reversal"
)

print(
    "Quantile:",
    QUANTILE
)

print(
    "Max turnover:",
    MAX_TURNOVER
)


# =========================================================
# LOAD SPLIT
# =========================================================

split = pd.read_csv(
    SPLIT_FILE
)


development_assets = split[
    split["v2_group"]
    ==
    "Development"
]["native_ticker"].tolist()


validation_assets = split[
    split["v2_group"]
    ==
    "Validation"
]["native_ticker"].tolist()


research20_assets = split[
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


print(
    "\nValidation assets:",
    sorted(validation_assets)
)

print(
    "Final research assets:",
    len(research20_assets)
)

print(
    "Final asset holdout:",
    sorted(holdout_assets)
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
# LOAD ASSETS
# =========================================================

def load_assets(
    tickers,
    period_start,
    period_end
):

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


        # Small buffer for lag calculation
        calculation_start = (
            period_start
            -
            pd.Timedelta(hours=24)
        )


        df = df[
            (
                df["datetime_utc"]
                >= calculation_start
            )
            &
            (
                df["datetime_utc"]
                < period_end
            )
        ].copy()


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


        # Frozen target
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


        df = df[
            (
                df["datetime_utc"]
                >= period_start
            )
            &
            (
                df["datetime_utc"]
                < period_end
            )
        ].copy()


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
# TURNOVER-CAPPED PORTFOLIO
# =========================================================

def build_portfolio(
    data,
    min_assets
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


        target_weights = {}


        for asset in longs["asset"]:

            target_weights[asset] = (
                0.5
                /
                n_select
            )


        for asset in shorts["asset"]:

            target_weights[asset] = (
                -0.5
                /
                n_select
            )


        available_assets = set(
            valid["asset"]
        )


        # Force exit unavailable assets
        forced_exit_turnover = sum(
            abs(weight)

            for asset, weight
            in previous_weights.items()

            if asset
            not in available_assets
        )


        current_weights = {
            asset:
            weight

            for asset, weight
            in previous_weights.items()

            if asset
            in available_assets
        }


        all_assets = (
            set(current_weights)
            |
            set(target_weights)
        )


        changes = {
            asset:
            (
                target_weights.get(
                    asset,
                    0.0
                )
                -
                current_weights.get(
                    asset,
                    0.0
                )
            )

            for asset
            in all_assets
        }


        desired_turnover = sum(
            abs(change)

            for change
            in changes.values()
        )


        remaining_budget = max(
            0.0,
            MAX_TURNOVER
            -
            forced_exit_turnover
        )


        if desired_turnover > 0:

            scale = min(
                1.0,
                remaining_budget
                /
                desired_turnover
            )

        else:

            scale = 0.0


        new_weights = {}


        for asset in all_assets:

            old_weight = (
                current_weights.get(
                    asset,
                    0.0
                )
            )


            new_weight = (
                old_weight
                +
                changes[asset]
                *
                scale
            )


            if abs(new_weight) > 1e-12:

                new_weights[
                    asset
                ] = new_weight


        actual_turnover = (
            forced_exit_turnover
            +
            sum(
                abs(
                    new_weights.get(
                        asset,
                        0.0
                    )
                    -
                    current_weights.get(
                        asset,
                        0.0
                    )
                )

                for asset
                in all_assets
            )
        )


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
            in new_weights.items()
        )


        gross_exposure = sum(
            abs(weight)

            for weight
            in new_weights.values()
        )


        net_exposure = sum(
            new_weights.values()
        )


        rows.append(
            {
                "datetime_utc":
                timestamp,

                "gross_return":
                gross_return,

                "turnover":
                actual_turnover,

                "gross_exposure":
                gross_exposure,

                "net_exposure":
                net_exposure
            }
        )


        previous_weights = (
            new_weights.copy()
        )


    return pd.DataFrame(
        rows
    )


# =========================================================
# SUMMARY
# =========================================================

def summarize(
    portfolio,
    test_name
):

    results = []


    for cost_bps in (
        COST_SCENARIOS_BPS
    ):

        cost_rate = (
            cost_bps
            /
            10000
        )


        returns = (
            portfolio[
                "gross_return"
            ]
            -
            portfolio[
                "turnover"
            ]
            *
            cost_rate
        )


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


        peak = equity.cummax()


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


        days = (
            portfolio[
                "datetime_utc"
            ].max()
            -
            portfolio[
                "datetime_utc"
            ].min()
        ).total_seconds() / 86400


        bars_per_year = (
            len(returns)
            /
            days
            *
            365.25
        )


        if std_return > 0:

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


        results.append(
            {
                "test":
                test_name,

                "cost_bps":
                cost_bps,

                "observations":
                len(returns),

                "cumulative_return_pct":
                cumulative_return
                * 100,

                "win_rate_pct":
                (
                    returns > 0
                ).mean()
                * 100,

                "max_drawdown_pct":
                max_drawdown
                * 100,

                "avg_turnover":
                portfolio[
                    "turnover"
                ].mean(),

                "avg_gross_exposure":
                portfolio[
                    "gross_exposure"
                ].mean(),

                "avg_abs_net_exposure":
                portfolio[
                    "net_exposure"
                ].abs().mean(),

                "annualized_sharpe_naive":
                sharpe
            }
        )


    return results

# =========================================================
# EQUITY / DRAWDOWN TIME SERIES
# =========================================================

def build_timeseries(
    portfolio,
    test_name
):

    frames = []

    for cost_bps in COST_SCENARIOS_BPS:

        cost_rate = (
            cost_bps
            / 10000
        )

        result = portfolio.copy()

        result["test"] = (
            test_name
        )

        result["cost_bps"] = (
            cost_bps
        )

        result["net_return"] = (
            result["gross_return"]
            -
            result["turnover"]
            * cost_rate
        )

        result["equity"] = (
            1
            +
            result["net_return"]
        ).cumprod()

        result["cumulative_return_pct"] = (
            result["equity"]
            -
            1
        ) * 100

        result["equity_peak"] = (
            result["equity"]
            .cummax()
        )

        result["drawdown"] = (
            result["equity"]
            /
            result["equity_peak"]
            -
            1
        )

        result["drawdown_pct"] = (
            result["drawdown"]
            * 100
        )

        frames.append(
            result[
                [
                    "datetime_utc",
                    "test",
                    "cost_bps",
                    "gross_return",
                    "turnover",
                    "gross_exposure",
                    "net_exposure",
                    "net_return",
                    "equity",
                    "cumulative_return_pct",
                    "equity_peak",
                    "drawdown",
                    "drawdown_pct",
                ]
            ]
        )


    return pd.concat(
        frames,
        ignore_index=True
    )
# =========================================================
# TEST 1 â€” VALIDATION ASSETS / VALIDATION TIME
# =========================================================

validation_data = load_assets(
    validation_assets,
    VALIDATION_START,
    VALIDATION_END
)


validation_portfolio = (
    build_portfolio(
        validation_data,
        min_assets=4
    )
)


# =========================================================
# TEST 2 â€” 20 ASSETS / FINAL TIME
# =========================================================

final_time_data = load_assets(
    research20_assets,
    FINAL_START,
    FINAL_END
)


final_time_portfolio = (
    build_portfolio(
        final_time_data,
        min_assets=10
    )
)


# =========================================================
# TEST 3 â€” AMD/GLW/META / FINAL TIME
# =========================================================

asset_holdout_data = load_assets(
    holdout_assets,
    FINAL_START,
    FINAL_END
)


asset_holdout_portfolio = (
    build_portfolio(
        asset_holdout_data,
        min_assets=3
    )
)


# =========================================================
# COMBINE RESULTS
# =========================================================

all_results = []


all_results += summarize(
    validation_portfolio,
    "Validation6"
)


all_results += summarize(
    final_time_portfolio,
    "FinalTime20"
)


all_results += summarize(
    asset_holdout_portfolio,
    "FinalAsset3"
)
# =========================================================
# COMBINE BACKTEST TIME SERIES
# =========================================================

all_timeseries = pd.concat(
    [
        build_timeseries(
            validation_portfolio,
            "Validation6"
        ),

        build_timeseries(
            final_time_portfolio,
            "FinalTime20"
        ),

        build_timeseries(
            asset_holdout_portfolio,
            "FinalAsset3"
        ),
    ],
    ignore_index=True
)


all_timeseries.to_csv(
    TIMESERIES_OUTPUT_FILE,
    index=False
)

summary = pd.DataFrame(
    all_results
)


summary.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n====================================")
print("FROZEN EXECUTION RESULTS")
print("====================================\n")


print(
    summary.round(4)
    .to_string(
        index=False
    )
)


print("\n====================================")
print("VALIDATION COMPLETE")
print("====================================")


print(
    "No execution parameters "
    "were changed."
)
