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


# =========================================================
# FROZEN FACTOR + EXECUTION
# =========================================================

QUANTILE = 0.25

MAX_TURNOVER = 0.50

MIN_ASSETS = 8


COST_SCENARIOS_BPS = [
    0.0,
    2.5,
    5.0,
    10.0
]


print("====================================")
print("rFactor Lab")
print("Turnover-Capped Execution")
print("DEVELOPMENT ONLY")
print("====================================")

print(
    "\nFactor: 1-hour cross-sectional reversal"
)

print(
    "Maximum hourly turnover:",
    MAX_TURNOVER
)


# =========================================================
# RESEARCH ASSETS
# =========================================================

split = pd.read_csv(
    SPLIT_FILE
)


assets = split[
    split["v2_group"]
    ==
    "Development"
][
    "native_ticker"
].tolist()


print(
    "\nResearch assets:",
    len(assets)
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
# LOAD DATA
# =========================================================

frames = []


for ticker in assets:

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


    df["expected_market_hour"] = (
        df["expected_market_hour"]
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


    # DEVELOPMENT ONLY
    df = df[
        (
            df["datetime_utc"]
            >= PROJECT_START
        )
        &
        (
            df["datetime_utc"]
            < DEVELOPMENT_END
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


data = pd.concat(
    frames,
    ignore_index=True
)


# =========================================================
# PORTFOLIO ENGINE
# =========================================================

rows = []

previous_weights = {}


for timestamp, group in (
    data.groupby(
        "datetime_utc"
    )
):

    valid = group[
        group["momentum_1h"].notna()
        &
        group["forward_return_1h"].notna()
    ].copy()


    n = len(valid)


    if n < MIN_ASSETS:

        continue


    valid = valid.sort_values(
        "momentum_1h"
    )


    # =====================================================
    # TARGET PORTFOLIO
    # =====================================================

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


    # =====================================================
    # AVAILABLE ASSETS
    # =====================================================

    available_assets = set(
        valid["asset"]
    )


    # Positions whose data disappeared are forced out.
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


    # =====================================================
    # DESIRED CHANGE
    # =====================================================

    all_assets = (
        set(current_weights)
        |
        set(target_weights)
    )


    desired_changes = {
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
        in desired_changes.values()
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


    # =====================================================
    # PARTIAL MOVE TOWARD TARGET
    # =====================================================

    new_weights = {}


    for asset in all_assets:

        old_weight = (
            current_weights.get(
                asset,
                0.0
            )
        )


        change = (
            desired_changes[
                asset
            ]
            *
            scale
        )


        new_weight = (
            old_weight
            +
            change
        )


        if abs(
            new_weight
        ) > 1e-12:

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


    # =====================================================
    # RETURN
    # =====================================================

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


portfolio = pd.DataFrame(
    rows
)


# =========================================================
# COST ANALYSIS
# =========================================================

summary_rows = []


for cost_bps in COST_SCENARIOS_BPS:

    cost_rate = (
        cost_bps
        /
        10000
    )


    returns = (
        portfolio["gross_return"]
        -
        portfolio["turnover"]
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


    first_time = (
        portfolio[
            "datetime_utc"
        ].min()
    )


    last_time = (
        portfolio[
            "datetime_utc"
        ].max()
    )


    days = (
        last_time
        -
        first_time
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


    win_rate = (
        (
            returns > 0
        ).mean()
        *
        100
    )


    summary_rows.append(
        {
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
            portfolio[
                "turnover"
            ].mean(),

            "max_turnover":
            portfolio[
                "turnover"
            ].max(),

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


summary = pd.DataFrame(
    summary_rows
)


# =========================================================
# DISPLAY
# =========================================================

print("\n====================================")
print("DEVELOPMENT TURNOVER-CAP RESULTS")
print("====================================\n")


print(
    summary
    .round(4)
    .to_string(
        index=False
    )
)


print(
    "\nFactor was NOT changed."
)

print(
    "Validation and Final Holdout "
    "were NOT inspected in this test."
)