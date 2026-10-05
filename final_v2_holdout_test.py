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

TIME_OUTPUT = Path(
    "data/v2_final_time_holdout_ic.csv"
)

ASSET_OUTPUT = Path(
    "data/v2_final_asset_holdout_ic.csv"
)


# =========================================================
# FROZEN FACTOR
# =========================================================

FACTOR = "momentum_1h"

TARGET = "forward_return_1h"

EXPECTED_SIGN = -1


# =========================================================
# FINAL HOLDOUT PERIOD
# =========================================================

PROJECT_START = pd.Timestamp(
    "2025-09-25 06:00:00",
    tz="UTC"
)

HOLDOUT_START = (
    PROJECT_START
    +
    pd.Timedelta(days=300)
)

HOLDOUT_END = (
    PROJECT_START
    +
    pd.Timedelta(days=365)
)


print("====================================")
print("rFactor Lab")
print("FINAL V2 HOLDOUT TEST")
print("====================================")

print(
    "\nFactor:",
    FACTOR
)

print(
    "Target:",
    TARGET
)

print(
    "Expected relationship: NEGATIVE"
)

print(
    "\nFinal period:",
    HOLDOUT_START,
    "→",
    HOLDOUT_END
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


asset_holdout = split[
    split["v2_group"]
    ==
    "AssetHoldout"
][
    "native_ticker"
].tolist()


print(
    "\nTime-holdout assets:",
    len(research_assets)
)

print(
    "Asset holdout:",
    sorted(asset_holdout)
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
# BUILD OBSERVATIONS
# =========================================================

def build_observations(
    tickers
):

    all_rows = []


    for ticker in tickers:

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


        df["close"] = pd.to_numeric(
            df["close"],
            errors="coerce"
        )


        calculation_start = (
            HOLDOUT_START
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
                < HOLDOUT_END
            )
        ].copy()


        df = df.sort_values(
            "datetime_utc"
        ).reset_index(drop=True)


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


        # -----------------------------------------
        # Frozen factor
        # -----------------------------------------

        df["momentum_1h"] = (
            df["px"]
            /
            df["px"].shift(1)
            -
            1
        )


        valid_factor = (
            df["px"].notna()
            &
            df["px"]
            .shift(1)
            .notna()
        )


        df.loc[
            ~valid_factor,
            "momentum_1h"
        ] = np.nan


        # -----------------------------------------
        # Frozen target
        # -----------------------------------------

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
            df["px"]
            .shift(-1)
            .notna()
        )


        df.loc[
            ~valid_target,
            "forward_return_1h"
        ] = np.nan


        df = df[
            (
                df["datetime_utc"]
                >= HOLDOUT_START
            )
            &
            (
                df["datetime_utc"]
                < HOLDOUT_END
            )
            &
            (
                df[
                    "expected_market_hour"
                ]
            )
        ].copy()


        df["asset"] = ticker


        all_rows.append(
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
        all_rows,
        ignore_index=True
    )


# =========================================================
# IC ENGINE
# =========================================================

def calculate_ic_table(
    observations,
    min_assets
):

    records = []


    for timestamp, group in (
        observations.groupby(
            "datetime_utc"
        )
    ):

        valid = (
            group[
                FACTOR
            ].notna()
            &
            group[
                TARGET
            ].notna()
        )


        x = group.loc[
            valid,
            FACTOR
        ]


        y = group.loc[
            valid,
            TARGET
        ]


        if len(x) < min_assets:

            continue


        if (
            x.nunique() < 2
            or
            y.nunique() < 2
        ):

            continue


        ic = (
            x.rank()
            .corr(
                y.rank()
            )
        )


        if pd.isna(ic):

            continue


        records.append(
            {
                "datetime_utc":
                timestamp,

                "asset_count":
                len(x),

                "ic":
                ic
            }
        )


    return pd.DataFrame(
        records
    )


# =========================================================
# SUMMARY
# =========================================================

def summarize(
    name,
    ic_df
):

    values = (
        ic_df[
            "ic"
        ]
        .dropna()
    )


    n = len(values)


    if n == 0:

        print(
            name,
            ": NO VALID IC DATA"
        )

        return None


    mean_ic = (
        values.mean()
    )

    median_ic = (
        values.median()
    )

    negative_rate = (
        (
            values < 0
        ).mean()
        * 100
    )


    std = (
        values.std(
            ddof=1
        )
    )


    if (
        n >= 2
        and
        std > 0
    ):

        t_stat = (
            mean_ic
            /
            (
                std
                /
                np.sqrt(n)
            )
        )

    else:

        t_stat = np.nan


    midpoint = (
        HOLDOUT_START
        +
        (
            HOLDOUT_END
            -
            HOLDOUT_START
        )
        / 2
    )


    ic_df = ic_df.copy()


    ic_df["half"] = np.where(
        ic_df[
            "datetime_utc"
        ]
        <
        midpoint,
        "Half_1",
        "Half_2"
    )


    half_summary = (
        ic_df.groupby(
            "half"
        )["ic"]
        .agg(
            [
                "count",
                "mean",
                "median"
            ]
        )
    )


    print(
        "\n===================================="
    )

    print(name)

    print(
        "===================================="
    )


    print(
        "IC timestamps:",
        n
    )

    print(
        "Mean IC:",
        round(
            mean_ic,
            4
        )
    )

    print(
        "Median IC:",
        round(
            median_ic,
            4
        )
    )

    print(
        "Negative IC rate:",
        round(
            negative_rate,
            2
        ),
        "%"
    )

    print(
        "Naive t-stat:",
        round(
            t_stat,
            4
        )
    )


    print(
        "\nHalf-period results:"
    )

    print(
        half_summary.round(
            4
        )
    )


    return {
        "timestamps":
        n,

        "mean_ic":
        mean_ic,

        "median_ic":
        median_ic,

        "negative_rate":
        negative_rate,

        "t_stat":
        t_stat,

        "half_summary":
        half_summary
    }


# =========================================================
# TEST A — FINAL TIME HOLDOUT
# =========================================================

time_observations = (
    build_observations(
        research_assets
    )
)


time_ic = calculate_ic_table(
    time_observations,
    min_assets=10
)


time_ic.to_csv(
    TIME_OUTPUT,
    index=False
)


time_result = summarize(
    "1. FINAL TIME HOLDOUT",
    time_ic
)


# =========================================================
# TEST B — FINAL ASSET + TIME HOLDOUT
# =========================================================

asset_observations = (
    build_observations(
        asset_holdout
    )
)


asset_ic = calculate_ic_table(
    asset_observations,
    min_assets=3
)


asset_ic.to_csv(
    ASSET_OUTPUT,
    index=False
)


asset_result = summarize(
    "2. FINAL ASSET + TIME HOLDOUT",
    asset_ic
)


# =========================================================
# FROZEN PASS CONDITIONS
# =========================================================

print(
    "\n===================================="
)

print(
    "FINAL HOLDOUT CHECKS"
)

print(
    "===================================="
)


# Time holdout:
# enough data, negative,
# magnitude >= 0.02,
# both halves negative.

time_pass = False


if (
    time_result
    is not None
):

    hs = (
        time_result[
            "half_summary"
        ]
    )


    time_halves_negative = (
        "Half_1" in hs.index
        and
        "Half_2" in hs.index
        and
        hs.loc[
            "Half_1",
            "mean"
        ] < 0
        and
        hs.loc[
            "Half_2",
            "mean"
        ] < 0
    )


    time_pass = (
        time_result[
            "timestamps"
        ]
        >= 400
        and
        time_result[
            "mean_ic"
        ] <= -0.02
        and
        time_halves_negative
    )


# Asset holdout:
# only 3 assets, so we use
# a slightly simpler rule.

asset_pass = False


if (
    asset_result
    is not None
):

    hs = (
        asset_result[
            "half_summary"
        ]
    )


    asset_halves_negative = (
        "Half_1" in hs.index
        and
        "Half_2" in hs.index
        and
        hs.loc[
            "Half_1",
            "mean"
        ] < 0
        and
        hs.loc[
            "Half_2",
            "mean"
        ] < 0
    )


    asset_pass = (
        asset_result[
            "timestamps"
        ]
        >= 200
        and
        asset_result[
            "mean_ic"
        ] < 0
        and
        asset_halves_negative
    )


print(
    "Final time holdout passed:",
    time_pass
)

print(
    "Final asset+time holdout passed:",
    asset_pass
)


print(
    "\n===================================="
)

print(
    "FINAL HOLDOUT TEST COMPLETE"
)

print(
    "===================================="
)


print(
    "\nDo NOT alter the factor "
    "after seeing these results."
)