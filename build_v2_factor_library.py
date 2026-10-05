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

OBSERVATION_FILE = Path(
    "data/v2_development_factor_observations.csv"
)

IC_FILE = Path(
    "data/v2_development_factor_ic.csv"
)

CANDIDATE_FILE = Path(
    "data/v2_development_factor_candidates.csv"
)


# =========================================================
# RESEARCH PERIOD
# =========================================================

START_TIME = pd.Timestamp(
    "2025-09-25 06:00:00",
    tz="UTC"
)

DISCOVERY_DAYS = 240

DISCOVERY_END = (
    START_TIME
    +
    pd.Timedelta(days=DISCOVERY_DAYS)
)


# =========================================================
# FACTORS
# =========================================================

FACTORS = [
    "momentum_1h",
    "momentum_3h",
    "momentum_6h",
    "momentum_24h",
    "vol_norm_momentum_6h",
    "volatility_expansion",
    "distance_ma24",
    "distance_ma72"
]


TARGETS = {
    "forward_return_1h": 1,
    "forward_return_3h": 3,
    "forward_return_6h": 6
}


# =========================================================
# FROZEN DISCOVERY RULES
# =========================================================

MIN_ASSETS_PER_TIMESTAMP = 8

MIN_IC_TIMESTAMPS = 200

MIN_ABS_MEAN_IC = 0.03

MIN_SUPPORTING_FOLDS = 3

MIN_ABS_SUPPORTING_FOLD_IC = 0.01

MIN_MEDIAN_ABS_FOLD_IC = 0.02


print("====================================")
print("rFactor Lab")
print("V2 Development Factor Library")
print("====================================")

print(
    "\nDiscovery period:",
    START_TIME,
    "→",
    DISCOVERY_END
)


# =========================================================
# LOAD FROZEN V2 SPLIT
# =========================================================

split = pd.read_csv(
    SPLIT_FILE
)


development = split[
    split["v2_group"]
    ==
    "Development"
].copy()


print(
    "\nDevelopment assets:",
    len(development)
)


print(
    sorted(
        development[
            "native_ticker"
        ].tolist()
    )
)


# =========================================================
# LOAD EXPECTED-MARKET MASK
# =========================================================

market_mask = pd.read_csv(
    MASK_FILE
)


market_mask[
    "datetime_utc"
] = pd.to_datetime(
    market_mask[
        "datetime_utc"
    ],
    utc=True
)


market_mask[
    "expected_market_hour"
] = (
    market_mask[
        "expected_market_hour"
    ]
    .astype(str)
    .str.lower()
    .eq("true")
)


market_mask = market_mask[
    [
        "datetime_utc",
        "expected_market_hour"
    ]
]


# =========================================================
# FOLD ASSIGNMENT
# 4 x 60-day development folds
# =========================================================

def assign_fold(timestamp):

    elapsed_days = (
        timestamp
        -
        START_TIME
    ).total_seconds() / 86400


    if elapsed_days < 60:
        return "Fold_1"

    if elapsed_days < 120:
        return "Fold_2"

    if elapsed_days < 180:
        return "Fold_3"

    return "Fold_4"


# =========================================================
# STORAGE
# =========================================================

all_observations = []


# =========================================================
# PROCESS DEVELOPMENT ASSETS
# =========================================================

for row in development.itertuples():

    ticker = row.native_ticker


    print(
        "\n------------------------------------"
    )

    print(
        "Processing:",
        ticker
    )


    file = (
        PREPARED_FOLDER
        /
        f"{ticker}_prepared.csv"
    )


    df = pd.read_csv(
        file
    )


    df[
        "datetime_utc"
    ] = pd.to_datetime(
        df[
            "datetime_utc"
        ],
        utc=True
    )


    df["close"] = pd.to_numeric(
        df["close"],
        errors="coerce"
    )


    # =====================================================
    # DISCOVERY PERIOD ONLY
    # =====================================================

    df = df[
        (
            df["datetime_utc"]
            >= START_TIME
        )
        &
        (
            df["datetime_utc"]
            < DISCOVERY_END
        )
    ].copy()


    df = df.sort_values(
        "datetime_utc"
    ).reset_index(
        drop=True
    )


    # =====================================================
    # MERGE EXPECTED MARKET MASK
    # =====================================================

    df = df.merge(
        market_mask,
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


    # Price is usable only during
    # expected market timestamps.

    df["px"] = df["close"].where(
        df[
            "expected_market_hour"
        ]
    )


    # =====================================================
    # MOMENTUM FUNCTION
    # =====================================================

    def momentum(hours):

        result = (
            df["px"]
            /
            df["px"].shift(hours)
            -
            1
        )


        valid_window = (
            df["px"]
            .notna()
            .rolling(
                hours + 1
            )
            .sum()
        )


        result[
            valid_window
            != hours + 1
        ] = np.nan


        return result


    # =====================================================
    # MOMENTUM FACTORS
    # =====================================================

    df[
        "momentum_1h"
    ] = momentum(1)


    df[
        "momentum_3h"
    ] = momentum(3)


    df[
        "momentum_6h"
    ] = momentum(6)


    df[
        "momentum_24h"
    ] = momentum(24)


    # =====================================================
    # 1-HOUR RETURNS
    # =====================================================

    df[
        "return_1h"
    ] = (
        df["px"]
        /
        df["px"].shift(1)
        -
        1
    )


    valid_return = (
        df["px"].notna()
        &
        df["px"]
        .shift(1)
        .notna()
    )


    df.loc[
        ~valid_return,
        "return_1h"
    ] = np.nan


    # =====================================================
    # VOLATILITY
    # =====================================================

    df[
        "volatility_24h"
    ] = (
        df["return_1h"]
        .shift(1)
        .rolling(
            24,
            min_periods=12
        )
        .std()
    )


    df[
        "volatility_6h"
    ] = (
        df["return_1h"]
        .shift(1)
        .rolling(
            6,
            min_periods=4
        )
        .std()
    )


    # =====================================================
    # VOL-NORMALIZED MOMENTUM
    # =====================================================

    df[
        "vol_norm_momentum_6h"
    ] = (
        df["momentum_6h"]
        /
        (
            df["volatility_24h"]
            *
            np.sqrt(6)
        )
    )


    # =====================================================
    # VOLATILITY EXPANSION
    # =====================================================

    df[
        "volatility_expansion"
    ] = (
        df["volatility_6h"]
        /
        df["volatility_24h"]
    )


    # =====================================================
    # DISTANCE FROM ROLLING MEAN
    # =====================================================

    ma24 = (
        df["px"]
        .shift(1)
        .rolling(
            24,
            min_periods=12
        )
        .mean()
    )


    ma72 = (
        df["px"]
        .shift(1)
        .rolling(
            72,
            min_periods=36
        )
        .mean()
    )


    df[
        "distance_ma24"
    ] = (
        df["px"]
        /
        ma24
        -
        1
    )


    df[
        "distance_ma72"
    ] = (
        df["px"]
        /
        ma72
        -
        1
    )


    # =====================================================
    # FORWARD RETURN FUNCTION
    #
    # Requires every future hourly price
    # to exist, preventing jumps across
    # systemic market closures.
    # =====================================================

    def forward_return(hours):

        result = (
            df["px"]
            .shift(-hours)
            /
            df["px"]
            -
            1
        )


        valid = (
            df["px"].notna()
        )


        for step in range(
            1,
            hours + 1
        ):

            valid = (
                valid
                &
                df["px"]
                .shift(-step)
                .notna()
            )


        result[
            ~valid
        ] = np.nan


        return result


    # =====================================================
    # TARGETS
    # =====================================================

    df[
        "forward_return_1h"
    ] = forward_return(1)


    df[
        "forward_return_3h"
    ] = forward_return(3)


    df[
        "forward_return_6h"
    ] = forward_return(6)


    # =====================================================
    # KEEP EXPECTED MARKET HOURS
    # =====================================================

    df = df[
        df[
            "expected_market_hour"
        ]
    ].copy()


    df["asset"] = ticker


    df["fold"] = (
        df[
            "datetime_utc"
        ]
        .apply(
            assign_fold
        )
    )


    columns = [
        "datetime_utc",
        "asset",
        "fold"
    ] + FACTORS + list(
        TARGETS.keys()
    )


    all_observations.append(
        df[
            columns
        ]
    )


    print(
        "Usable market rows:",
        len(df)
    )


# =========================================================
# COMBINE
# =========================================================

observations = pd.concat(
    all_observations,
    ignore_index=True
)


observations.to_csv(
    OBSERVATION_FILE,
    index=False
)


print(
    "\nTotal observations:",
    len(observations)
)


# =========================================================
# CROSS-SECTIONAL SPEARMAN IC
# =========================================================

def calculate_ic(
    factor,
    future_return
):

    valid = (
        factor.notna()
        &
        future_return.notna()
    )


    x = factor[
        valid
    ]


    y = future_return[
        valid
    ]


    if len(x) < (
        MIN_ASSETS_PER_TIMESTAMP
    ):

        return np.nan


    if (
        x.nunique() < 2
        or
        y.nunique() < 2
    ):

        return np.nan


    return (
        x.rank()
        .corr(
            y.rank()
        )
    )


# =========================================================
# CALCULATE IC
# =========================================================

ic_records = []


for factor in FACTORS:

    for target in TARGETS:

        data = observations[
            [
                "datetime_utc",
                "fold",
                "asset",
                factor,
                target
            ]
        ]


        for timestamp, group in (
            data.groupby(
                "datetime_utc"
            )
        ):

            ic = calculate_ic(
                group[factor],
                group[target]
            )


            if pd.isna(ic):

                continue


            ic_records.append(
                {
                    "datetime_utc":
                    timestamp,

                    "fold":
                    group[
                        "fold"
                    ].iloc[0],

                    "factor":
                    factor,

                    "target":
                    target,

                    "asset_count":
                    group[
                        [
                            factor,
                            target
                        ]
                    ]
                    .dropna()
                    .shape[0],

                    "ic":
                    ic
                }
            )


ic_df = pd.DataFrame(
    ic_records
)


ic_df.to_csv(
    IC_FILE,
    index=False
)


# =========================================================
# SUMMARY
# =========================================================

def summarize_ic(group):

    x = (
        group["ic"]
        .dropna()
    )


    n = len(x)


    if n == 0:

        return pd.Series(
            dtype=float
        )


    mean_ic = x.mean()

    std_ic = x.std(
        ddof=1
    )


    if (
        n >= 2
        and
        std_ic > 0
    ):

        naive_t = (
            mean_ic
            /
            (
                std_ic
                /
                np.sqrt(n)
            )
        )

    else:

        naive_t = np.nan


    return pd.Series(
        {
            "timestamps":
            n,

            "mean_ic":
            mean_ic,

            "median_ic":
            x.median(),

            "std_ic":
            std_ic,

            "positive_ic_pct":
            (
                x > 0
            ).mean() * 100,

            "naive_t_stat":
            naive_t
        }
    )


summary = (
    ic_df.groupby(
        [
            "factor",
            "target"
        ]
    )
    .apply(
        summarize_ic,
        include_groups=False
    )
    .reset_index()
)


# =========================================================
# FOLD SUMMARY
# =========================================================

fold_summary = (
    ic_df.groupby(
        [
            "factor",
            "target",
            "fold"
        ]
    )[
        "ic"
    ]
    .mean()
    .reset_index()
)


fold_pivot = (
    fold_summary
    .pivot_table(
        index=[
            "factor",
            "target"
        ],
        columns="fold",
        values="ic"
    )
    .reset_index()
)


combined = summary.merge(
    fold_pivot,
    on=[
        "factor",
        "target"
    ],
    how="left"
)


# =========================================================
# PREDEFINED STABILITY TEST
# =========================================================

def stability_test(row):

    if (
        row[
            "timestamps"
        ]
        <
        MIN_IC_TIMESTAMPS
    ):

        return False


    if abs(
        row[
            "mean_ic"
        ]
    ) < (
        MIN_ABS_MEAN_IC
    ):

        return False


    overall_sign = np.sign(
        row[
            "mean_ic"
        ]
    )


    folds = [
        row.get(
            "Fold_1",
            np.nan
        ),

        row.get(
            "Fold_2",
            np.nan
        ),

        row.get(
            "Fold_3",
            np.nan
        ),

        row.get(
            "Fold_4",
            np.nan
        )
    ]


    valid_folds = [
        value
        for value in folds
        if not pd.isna(value)
    ]


    if len(
        valid_folds
    ) < 4:

        return False


    supporting = sum(
        (
            np.sign(value)
            ==
            overall_sign
        )
        and
        (
            abs(value)
            >=
            MIN_ABS_SUPPORTING_FOLD_IC
        )

        for value in valid_folds
    )


    median_abs_fold = np.median(
        [
            abs(value)
            for value
            in valid_folds
        ]
    )


    if (
        supporting
        <
        MIN_SUPPORTING_FOLDS
    ):

        return False


    if (
        median_abs_fold
        <
        MIN_MEDIAN_ABS_FOLD_IC
    ):

        return False


    return True


combined[
    "passes_stability"
] = (
    combined.apply(
        stability_test,
        axis=1
    )
)


combined.to_csv(
    CANDIDATE_FILE,
    index=False
)


# =========================================================
# DISPLAY
# =========================================================

print("\n====================================")
print("1. OVERALL FACTOR SUMMARY")
print("====================================\n")


print(
    summary
    .sort_values(
        "mean_ic",
        key=lambda x:
        x.abs(),
        ascending=False
    )
    .round(4)
    .to_string(
        index=False
    )
)


print("\n====================================")
print("2. FOUR-FOLD WALK-FORWARD IC")
print("====================================\n")


print(
    fold_pivot
    .round(4)
    .to_string(
        index=False
    )
)


print("\n====================================")
print("3. STABLE DEVELOPMENT CANDIDATES")
print("====================================\n")


candidates = combined[
    combined[
        "passes_stability"
    ]
].copy()


if candidates.empty:

    print(
        "No candidate passed "
        "the predefined rules."
    )

else:

    candidates[
        "abs_mean_ic"
    ] = (
        candidates[
            "mean_ic"
        ].abs()
    )


    candidates = candidates.sort_values(
        "abs_mean_ic",
        ascending=False
    )


    print(
        candidates[
            [
                "factor",
                "target",
                "timestamps",
                "mean_ic",
                "median_ic",
                "Fold_1",
                "Fold_2",
                "Fold_3",
                "Fold_4"
            ]
        ]
        .round(4)
        .to_string(
            index=False
        )
    )


print("\n====================================")
print("V2 DEVELOPMENT RESEARCH COMPLETE")
print("====================================")


print(
    "Observations:",
    OBSERVATION_FILE
)


print(
    "IC data:",
    IC_FILE
)


print(
    "Candidates:",
    CANDIDATE_FILE
)


print(
    "\nValidation assets were NOT used."
)

print(
    "Asset Holdout was NOT used."
)

print(
    "Time periods after day 240 "
    "were NOT used."
)