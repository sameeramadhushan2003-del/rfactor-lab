import pandas as pd
import numpy as np
from pathlib import Path


# =========================================================
# SETTINGS
# =========================================================

QUALITY_FILE = Path(
    "data/research_asset_split_quality.csv"
)

PREPARED_FOLDER = Path(
    "data/universe_prepared"
)

OBSERVATION_FILE = Path(
    "data/development_factor_observations.csv"
)

IC_FILE = Path(
    "data/development_factor_ic.csv"
)


DEVELOPMENT_DAYS = 60

MIN_ASSETS_PER_TIMESTAMP = 4


# ---------------------------------------------------------
# These criteria are frozen BEFORE factor results.
# Do not modify after seeing output.
# ---------------------------------------------------------

MIN_IC_TIMESTAMPS = 30

MIN_ABS_MEAN_IC = 0.05

MIN_ABS_FOLD_IC = 0.02


FACTORS = [
    "momentum_6h",
    "short_reversal_3h",
    "vol_norm_momentum_6h",
    "distance_from_reference",
    "weekend_dislocation_z",
    "volatility_expansion"
]


TARGETS = {
    "forward_return_1h": 1,
    "forward_return_3h": 3
}


print("====================================")
print("rFactor Lab")
print("Development Factor Library")
print("====================================")


# =========================================================
# LOAD QUALITY-GATED DEVELOPMENT ASSETS
# =========================================================

quality = pd.read_csv(
    QUALITY_FILE
)


def to_boolean(series):

    return (
        series
        .astype(str)
        .str.lower()
        .eq("true")
    )


quality[
    "weekend_factor_eligible"
] = to_boolean(
    quality[
        "weekend_factor_eligible"
    ]
)


development = quality[
    (
        quality[
            "research_group"
        ]
        == "Development"
    )
    &
    (
        quality[
            "weekend_factor_eligible"
        ]
    )
].copy()


print(
    "\nDevelopment assets:",
    len(development)
)


print(
    development[
        "native_ticker"
    ]
    .sort_values()
    .tolist()
)


# =========================================================
# FIND COMMON PROJECT START
# =========================================================

start_dates = []


for row in development.itertuples():

    file = (
        PREPARED_FOLDER
        /
        f"{row.native_ticker}_prepared.csv"
    )

    temp = pd.read_csv(
        file,
        usecols=[
            "datetime_utc"
        ]
    )

    temp[
        "datetime_utc"
    ] = pd.to_datetime(
        temp[
            "datetime_utc"
        ],
        utc=True
    )

    start_dates.append(
        temp[
            "datetime_utc"
        ].min()
    )


PROJECT_START = min(
    start_dates
)


DEVELOPMENT_END = (
    PROJECT_START
    +
    pd.Timedelta(
        days=DEVELOPMENT_DAYS
    )
)


print(
    "\nDevelopment period:"
)

print(
    PROJECT_START,
    "→",
    DEVELOPMENT_END
)


# =========================================================
# WALK-FORWARD FOLD FUNCTION
# =========================================================

FOLD_DAYS = (
    DEVELOPMENT_DAYS
    /
    3
)


def assign_fold(timestamp):

    elapsed_days = (
        timestamp
        -
        PROJECT_START
    ).total_seconds() / 86400


    if elapsed_days < FOLD_DAYS:

        return "Fold_1"


    elif elapsed_days < (
        FOLD_DAYS * 2
    ):

        return "Fold_2"


    return "Fold_3"


# =========================================================
# STORE OBSERVATIONS
# =========================================================

all_observations = []


# =========================================================
# PROCESS EACH DEVELOPMENT ASSET
# =========================================================

for row in development.itertuples():

    ticker = (
        row.native_ticker
    )

    file = (
        PREPARED_FOLDER
        /
        f"{ticker}_prepared.csv"
    )


    print(
        "\n------------------------------------"
    )

    print(
        "Processing:",
        ticker
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


    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "turnover"
    ]


    for column in numeric_columns:

        df[
            column
        ] = pd.to_numeric(
            df[
                column
            ],
            errors="coerce"
        )


    df = df[
        (
            df[
                "datetime_utc"
            ]
            >= PROJECT_START
        )
        &
        (
            df[
                "datetime_utc"
            ]
            < DEVELOPMENT_END
        )
    ].copy()


    df = df.sort_values(
        "datetime_utc"
    ).reset_index(
        drop=True
    )


    # =====================================================
    # HOURLY RETURN
    # =====================================================

    df[
        "return_1h"
    ] = (
        df["close"]
        /
        df["close"].shift(1)
        -
        1
    )


    valid_return = (
        df["close"].notna()
        &
        df["close"]
        .shift(1)
        .notna()
    )


    df.loc[
        ~valid_return,
        "return_1h"
    ] = np.nan


    # =====================================================
    # MOMENTUM
    # =====================================================

    def create_momentum(
        hours
    ):

        momentum = (
            df["close"]
            /
            df["close"]
            .shift(hours)
            -
            1
        )


        valid_window = (
            df["close"]
            .notna()
            .rolling(
                hours + 1
            )
            .sum()
        )


        momentum[
            valid_window
            != hours + 1
        ] = np.nan


        return momentum


    df[
        "momentum_3h"
    ] = create_momentum(
        3
    )


    df[
        "momentum_6h"
    ] = create_momentum(
        6
    )


    # =====================================================
    # SHORT-TERM REVERSAL FACTOR
    # =====================================================

    df[
        "short_reversal_3h"
    ] = (
        -df[
            "momentum_3h"
        ]
    )


    # =====================================================
    # TRAILING 24-HOUR VOLATILITY
    #
    # shift(1) prevents current return
    # from entering its own volatility estimate.
    # =====================================================

    df[
        "volatility_24h"
    ] = (
        df[
            "return_1h"
        ]
        .shift(1)
        .rolling(
            24,
            min_periods=12
        )
        .std()
    )


    # =====================================================
    # SHORT VOLATILITY
    # =====================================================

    df[
        "volatility_6h"
    ] = (
        df[
            "return_1h"
        ]
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

    expected_vol_6h = (
        df[
            "volatility_24h"
        ]
        *
        np.sqrt(6)
    )


    df[
        "vol_norm_momentum_6h"
    ] = (
        df[
            "momentum_6h"
        ]
        /
        expected_vol_6h
    )


    # =====================================================
    # VOLATILITY EXPANSION
    # =====================================================

    df[
        "volatility_expansion"
    ] = (
        df[
            "volatility_6h"
        ]
        /
        df[
            "volatility_24h"
        ]
    )


    # =====================================================
    # WEEKEND IDENTIFICATION
    # =====================================================

    df[
        "is_weekend"
    ] = (
        df[
            "session"
        ]
        ==
        "Weekend"
    )


    df[
        "weekend_start"
    ] = (
        df[
            "is_weekend"
        ]
        &
        ~df[
            "is_weekend"
        ].shift(
            1,
            fill_value=False
        )
    )


    df[
        "weekend_id"
    ] = (
        df[
            "weekend_start"
        ]
        .cumsum()
    )


    # Start empty

    df[
        "reference_price"
    ] = np.nan


    df[
        "hours_from_reference"
    ] = np.nan


    # =====================================================
    # PRE-WEEKEND REFERENCE PRICE
    # =====================================================

    weekend_ids = (
        df.loc[
            df[
                "is_weekend"
            ],
            "weekend_id"
        ]
        .unique()
    )


    for weekend_id in weekend_ids:

        mask = (
            (
                df[
                    "weekend_id"
                ]
                ==
                weekend_id
            )
            &
            (
                df[
                    "is_weekend"
                ]
            )
        )


        weekend_indexes = (
            df.index[
                mask
            ]
        )


        if len(
            weekend_indexes
        ) == 0:

            continue


        first_index = (
            weekend_indexes[0]
        )


        if first_index == 0:

            continue


        previous = df.loc[
            :first_index - 1
        ]


        previous_valid = (
            previous[
                previous[
                    "close"
                ]
                .notna()
            ]
        )


        if previous_valid.empty:

            continue


        reference_row = (
            previous_valid
            .iloc[-1]
        )


        reference_price = (
            reference_row[
                "close"
            ]
        )


        reference_time = (
            reference_row[
                "datetime_utc"
            ]
        )


        df.loc[
            weekend_indexes,
            "reference_price"
        ] = (
            reference_price
        )


        hours_from_reference = (
            (
                df.loc[
                    weekend_indexes,
                    "datetime_utc"
                ]
                -
                reference_time
            )
            .dt.total_seconds()
            /
            3600
        )


        df.loc[
            weekend_indexes,
            "hours_from_reference"
        ] = (
            hours_from_reference
            .values
        )


    # =====================================================
    # DISTANCE FROM REFERENCE
    # =====================================================

    df[
        "distance_from_reference"
    ] = (
        df[
            "close"
        ]
        /
        df[
            "reference_price"
        ]
        -
        1
    )


    # =====================================================
    # NORMALIZED WEEKEND DISLOCATION
    # =====================================================

    expected_weekend_move = (
        df[
            "volatility_24h"
        ]
        *
        np.sqrt(
            df[
                "hours_from_reference"
            ]
        )
    )


    df[
        "weekend_dislocation_z"
    ] = (
        df[
            "distance_from_reference"
        ]
        /
        expected_weekend_move
    )


    # =====================================================
    # FORWARD 1-HOUR RETURN
    # =====================================================

    df[
        "forward_return_1h"
    ] = (
        df[
            "close"
        ]
        .shift(-1)
        /
        df[
            "close"
        ]
        -
        1
    )


    valid_forward_1h = (
        df[
            "close"
        ]
        .notna()
        &
        df[
            "close"
        ]
        .shift(-1)
        .notna()
        &
        (
            df[
                "session"
            ]
            .shift(-1)
            ==
            "Weekend"
        )
    )


    df.loc[
        ~valid_forward_1h,
        "forward_return_1h"
    ] = np.nan


    # =====================================================
    # FORWARD 3-HOUR RETURN
    # =====================================================

    df[
        "forward_return_3h"
    ] = (
        df[
            "close"
        ]
        .shift(-3)
        /
        df[
            "close"
        ]
        -
        1
    )


    valid_forward_3h = (
        df[
            "close"
        ]
        .notna()
        &
        df[
            "close"
        ]
        .shift(-1)
        .notna()
        &
        df[
            "close"
        ]
        .shift(-2)
        .notna()
        &
        df[
            "close"
        ]
        .shift(-3)
        .notna()
        &
        (
            df[
                "session"
            ]
            .shift(-1)
            ==
            "Weekend"
        )
        &
        (
            df[
                "session"
            ]
            .shift(-2)
            ==
            "Weekend"
        )
        &
        (
            df[
                "session"
            ]
            .shift(-3)
            ==
            "Weekend"
        )
    )


    df.loc[
        ~valid_forward_3h,
        "forward_return_3h"
    ] = np.nan


    # =====================================================
    # KEEP WEEKEND OBSERVATIONS ONLY
    # =====================================================

    weekend_data = df[
        df[
            "session"
        ]
        ==
        "Weekend"
    ].copy()


    weekend_data[
        "asset"
    ] = ticker


    weekend_data[
        "fold"
    ] = (
        weekend_data[
            "datetime_utc"
        ]
        .apply(
            assign_fold
        )
    )


    columns = [
        "datetime_utc",
        "asset",
        "fold",
        "momentum_6h",
        "short_reversal_3h",
        "vol_norm_momentum_6h",
        "distance_from_reference",
        "weekend_dislocation_z",
        "volatility_expansion",
        "forward_return_1h",
        "forward_return_3h"
    ]


    all_observations.append(
        weekend_data[
            columns
        ]
    )


    print(
        "Weekend rows:",
        len(
            weekend_data
        )
    )


# =========================================================
# COMBINE DEVELOPMENT OBSERVATIONS
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
    "\nTotal weekend observations:",
    len(
        observations
    )
)


# =========================================================
# CROSS-SECTIONAL SPEARMAN IC
#
# At each timestamp:
# rank factor across assets
# rank future return across assets
# correlate ranks
# =========================================================

def rank_correlation(
    factor,
    future
):

    valid = (
        factor.notna()
        &
        future.notna()
    )


    x = factor[
        valid
    ]

    y = future[
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


ic_records = []


for factor in FACTORS:

    for target in TARGETS:

        grouped = (
            observations[
                [
                    "datetime_utc",
                    "fold",
                    "asset",
                    factor,
                    target
                ]
            ]
            .groupby(
                "datetime_utc"
            )
        )


        for timestamp, group in grouped:

            ic = rank_correlation(
                group[
                    factor
                ],
                group[
                    target
                ]
            )


            if pd.isna(ic):

                continue


            fold = (
                group[
                    "fold"
                ]
                .iloc[0]
            )


            ic_records.append(
                {
                    "datetime_utc":
                    timestamp,

                    "factor":
                    factor,

                    "target":
                    target,

                    "fold":
                    fold,

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
# SUMMARY FUNCTION
# =========================================================

def summarize_ic(group):

    values = (
        group[
            "ic"
        ]
        .dropna()
    )


    n = len(values)


    if n == 0:

        return pd.Series(
            dtype=float
        )


    mean_ic = (
        values.mean()
    )


    std_ic = (
        values.std(
            ddof=1
        )
    )


    if (
        n >= 2
        and
        std_ic > 0
    ):

        t_stat = (
            mean_ic
            /
            (
                std_ic
                /
                np.sqrt(n)
            )
        )

    else:

        t_stat = np.nan


    positive_pct = (
        (
            values > 0
        ).mean()
        * 100
    )


    dominant_sign_pct = max(
        positive_pct,
        100
        -
        positive_pct
    )


    return pd.Series(
        {
            "timestamps":
            n,

            "mean_ic":
            mean_ic,

            "median_ic":
            values.median(),

            "std_ic":
            std_ic,

            "positive_ic_pct":
            positive_pct,

            "dominant_sign_pct":
            dominant_sign_pct,

            "naive_t_stat":
            t_stat
        }
    )


# =========================================================
# OVERALL FACTOR SUMMARY
# =========================================================

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


print(
    "\n===================================="
)

print(
    "1. OVERALL FACTOR IC SUMMARY"
)

print(
    "====================================\n"
)


print(
    summary
    .round(4)
    .to_string(
        index=False
    )
)


# =========================================================
# WALK-FORWARD FOLD RESULTS
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


print(
    "\n===================================="
)

print(
    "2. WALK-FORWARD FOLD MEAN IC"
)

print(
    "====================================\n"
)


print(
    fold_pivot
    .round(4)
    .to_string(
        index=False
    )
)


# =========================================================
# PREDEFINED STABILITY TEST
# =========================================================

merged = summary.merge(
    fold_pivot,
    on=[
        "factor",
        "target"
    ],
    how="left"
)


def check_candidate(row):

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


    fold_values = [
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
        )
    ]


    if any(
        pd.isna(value)
        for value
        in fold_values
    ):

        return False


    overall_sign = np.sign(
        row[
            "mean_ic"
        ]
    )


    # All folds must have same sign
    # as overall relationship.

    if not all(
        np.sign(value)
        ==
        overall_sign
        for value
        in fold_values
    ):

        return False


    if min(
        abs(value)
        for value
        in fold_values
    ) < (
        MIN_ABS_FOLD_IC
    ):

        return False


    return True


merged[
    "passes_predefined_stability"
] = (
    merged.apply(
        check_candidate,
        axis=1
    )
)


print(
    "\n===================================="
)

print(
    "3. PREDEFINED STABILITY CANDIDATES"
)

print(
    "====================================\n"
)


candidates = merged[
    merged[
        "passes_predefined_stability"
    ]
]


if candidates.empty:

    print(
        "No factor passed the frozen "
        "stability criteria."
    )

else:

    print(
        candidates[
            [
                "factor",
                "target",
                "timestamps",
                "mean_ic",
                "median_ic",
                "dominant_sign_pct",
                "Fold_1",
                "Fold_2",
                "Fold_3"
            ]
        ]
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


print(
    "\n===================================="
)

print(
    "FACTOR LIBRARY COMPLETE"
)

print(
    "===================================="
)


print(
    "Observations saved to:",
    OBSERVATION_FILE
)


print(
    "IC results saved to:",
    IC_FILE
)


print(
    "\nValidation assets were NOT used."
)

print(
    "Holdout assets were NOT used."
)

print(
    "\nDo not modify the frozen "
    "stability thresholds after "
    "seeing these results."
)