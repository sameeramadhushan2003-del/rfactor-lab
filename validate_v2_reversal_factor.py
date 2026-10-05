import pandas as pd
import numpy as np
from pathlib import Path


# =========================================================
# SETTINGS
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

OUTPUT_FILE = Path(
    "data/v2_validation_reversal_ic.csv"
)


# =========================================================
# FROZEN FACTOR
# =========================================================

FACTOR = "momentum_1h"

TARGET = "forward_return_1h"

EXPECTED_SIGN = -1


# =========================================================
# TIME PERIOD
# =========================================================

PROJECT_START = pd.Timestamp(
    "2025-09-25 06:00:00",
    tz="UTC"
)


VALIDATION_START = (
    PROJECT_START
    +
    pd.Timedelta(days=240)
)


VALIDATION_END = (
    PROJECT_START
    +
    pd.Timedelta(days=300)
)


# =========================================================
# PREDEFINED VALIDATION RULES
# =========================================================

MIN_ASSETS_PER_TIMESTAMP = 4

MIN_IC_TIMESTAMPS = 300

MIN_ABS_MEAN_IC = 0.03


print("====================================")
print("rFactor Lab")
print("V2 Strict Validation")
print("====================================")


print(
    "\nFrozen factor:",
    FACTOR
)

print(
    "Target:",
    TARGET
)

print(
    "Expected IC sign:",
    "Negative"
)


print(
    "\nValidation period:",
    VALIDATION_START,
    "→",
    VALIDATION_END
)


# =========================================================
# LOAD VALIDATION ASSETS
# =========================================================

split = pd.read_csv(
    SPLIT_FILE
)


validation = split[
    split["v2_group"]
    ==
    "Validation"
].copy()


print(
    "\nValidation assets:",
    len(validation)
)


print(
    sorted(
        validation[
            "native_ticker"
        ].tolist()
    )
)


# =========================================================
# LOAD MARKET MASK
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
# HALF SPLIT
# =========================================================

MIDPOINT = (
    VALIDATION_START
    +
    pd.Timedelta(days=30)
)


def assign_half(timestamp):

    if timestamp < MIDPOINT:
        return "Half_1"

    return "Half_2"


# =========================================================
# STORE OBSERVATIONS
# =========================================================

all_observations = []


# =========================================================
# PROCESS EACH VALIDATION ASSET
# =========================================================

for row in validation.itertuples():

    ticker = row.native_ticker


    print(
        "\nProcessing:",
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
    # Keep a little history before validation start
    # so lagged factor calculation works correctly.
    # =====================================================

    calculation_start = (
        VALIDATION_START
        -
        pd.Timedelta(hours=24)
    )


    df = df[
        (
            df[
                "datetime_utc"
            ]
            >= calculation_start
        )
        &
        (
            df[
                "datetime_utc"
            ]
            < VALIDATION_END
        )
    ].copy()


    df = df.sort_values(
        "datetime_utc"
    ).reset_index(drop=True)


    # =====================================================
    # MARKET MASK
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


    df["px"] = df["close"].where(
        df[
            "expected_market_hour"
        ]
    )


    # =====================================================
    # FROZEN 1-HOUR MOMENTUM
    # =====================================================

    df[
        "momentum_1h"
    ] = (
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


    # =====================================================
    # FORWARD 1-HOUR RETURN
    # =====================================================

    df[
        "forward_return_1h"
    ] = (
        df["px"]
        .shift(-1)
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


    # =====================================================
    # STRICT VALIDATION PERIOD ONLY
    # =====================================================

    df = df[
        (
            df[
                "datetime_utc"
            ]
            >= VALIDATION_START
        )
        &
        (
            df[
                "datetime_utc"
            ]
            < VALIDATION_END
        )
        &
        (
            df[
                "expected_market_hour"
            ]
        )
    ].copy()


    df["asset"] = ticker


    df["half"] = (
        df[
            "datetime_utc"
        ]
        .apply(
            assign_half
        )
    )


    all_observations.append(
        df[
            [
                "datetime_utc",
                "asset",
                "half",
                "momentum_1h",
                "forward_return_1h"
            ]
        ]
    )


# =========================================================
# COMBINE
# =========================================================

observations = pd.concat(
    all_observations,
    ignore_index=True
)


# =========================================================
# SPEARMAN CROSS-SECTIONAL IC
# =========================================================

def calculate_ic(group):

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
# CALCULATE IC BY TIMESTAMP
# =========================================================

records = []


for timestamp, group in (
    observations.groupby(
        "datetime_utc"
    )
):

    ic = calculate_ic(
        group
    )


    if pd.isna(ic):
        continue


    records.append(
        {
            "datetime_utc":
            timestamp,

            "half":
            group[
                "half"
            ].iloc[0],

            "asset_count":
            group[
                [
                    FACTOR,
                    TARGET
                ]
            ]
            .dropna()
            .shape[0],

            "ic":
            ic
        }
    )


ic_df = pd.DataFrame(
    records
)


ic_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# RESULTS
# =========================================================

values = (
    ic_df["ic"]
    .dropna()
)


timestamps = len(
    values
)


mean_ic = (
    values.mean()
)


median_ic = (
    values.median()
)


std_ic = (
    values.std(
        ddof=1
    )
)


negative_ic_pct = (
    (
        values < 0
    ).mean()
    * 100
)


if (
    timestamps >= 2
    and
    std_ic > 0
):

    naive_t_stat = (
        mean_ic
        /
        (
            std_ic
            /
            np.sqrt(
                timestamps
            )
        )
    )

else:

    naive_t_stat = np.nan


# =========================================================
# HALF RESULTS
# =========================================================

half_summary = (
    ic_df.groupby(
        "half"
    )[
        "ic"
    ]
    .agg(
        [
            "count",
            "mean",
            "median"
        ]
    )
)


half_1 = (
    half_summary.loc[
        "Half_1",
        "mean"
    ]
    if "Half_1"
    in half_summary.index
    else np.nan
)


half_2 = (
    half_summary.loc[
        "Half_2",
        "mean"
    ]
    if "Half_2"
    in half_summary.index
    else np.nan
)


# =========================================================
# FROZEN PASS RULES
# =========================================================

timestamps_ok = (
    timestamps
    >=
    MIN_IC_TIMESTAMPS
)


sign_ok = (
    np.sign(
        mean_ic
    )
    ==
    EXPECTED_SIGN
)


magnitude_ok = (
    abs(
        mean_ic
    )
    >=
    MIN_ABS_MEAN_IC
)


halves_ok = (
    not pd.isna(
        half_1
    )
    and
    not pd.isna(
        half_2
    )
    and
    np.sign(
        half_1
    )
    ==
    EXPECTED_SIGN
    and
    np.sign(
        half_2
    )
    ==
    EXPECTED_SIGN
)


passes_validation = (
    timestamps_ok
    and
    sign_ok
    and
    magnitude_ok
    and
    halves_ok
)


# =========================================================
# DISPLAY
# =========================================================

print("\n====================================")
print("VALIDATION RESULT")
print("====================================")


print(
    "IC timestamps:",
    timestamps
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
        negative_ic_pct,
        2
    ),
    "%"
)


print(
    "Naive t-stat:",
    round(
        naive_t_stat,
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


print(
    "\nChecks:"
)


print(
    "Enough timestamps:",
    timestamps_ok
)


print(
    "Correct sign:",
    sign_ok
)


print(
    "Sufficient magnitude:",
    magnitude_ok
)


print(
    "Both halves negative:",
    halves_ok
)


print(
    "\nPASSES VALIDATION:",
    passes_validation
)


print("\n====================================")
print("VALIDATION COMPLETE")
print("====================================")


print(
    "Saved to:",
    OUTPUT_FILE
)


print(
    "\nAMD, GLW and META were NOT used."
)

print(
    "Final days 301-365 were NOT used."
)