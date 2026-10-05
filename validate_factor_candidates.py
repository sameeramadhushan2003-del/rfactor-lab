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

OUTPUT_FILE = Path(
    "data/validation_factor_results.csv"
)


DEVELOPMENT_DAYS = 60

MIN_ASSETS_PER_TIMESTAMP = 3

MIN_VALID_TIMESTAMPS = 30

MIN_ABS_VALIDATION_IC = 0.03


# =========================================================
# FROZEN CANDIDATES
# =========================================================

CANDIDATES = {

    "distance_from_reference": {
        "target":
        "forward_return_3h",

        "expected_sign":
        -1
    },

    "volatility_expansion": {
        "target":
        "forward_return_1h",

        "expected_sign":
        1
    },

    "short_reversal_3h": {
        "target":
        "forward_return_1h",

        "expected_sign":
        1
    }
}


print("====================================")
print("rFactor Lab")
print("Validation Factor Test")
print("====================================")


# =========================================================
# LOAD VALIDATION ASSETS ONLY
# =========================================================

quality = pd.read_csv(
    QUALITY_FILE
)


quality[
    "weekend_factor_eligible"
] = (
    quality[
        "weekend_factor_eligible"
    ]
    .astype(str)
    .str.lower()
    .eq("true")
)


validation = quality[
    (
        quality[
            "research_group"
        ]
        == "Validation"
    )
    &
    (
        quality[
            "weekend_factor_eligible"
        ]
    )
].copy()


print(
    "\nValidation assets:",
    len(validation)
)

print(
    validation[
        "native_ticker"
    ]
    .sort_values()
    .tolist()
)


# =========================================================
# PROJECT START
# =========================================================

start_dates = []


for row in validation.itertuples():

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


VALIDATION_END = (
    PROJECT_START
    +
    pd.Timedelta(
        days=DEVELOPMENT_DAYS
    )
)


MIDPOINT = (
    PROJECT_START
    +
    pd.Timedelta(
        days=DEVELOPMENT_DAYS / 2
    )
)


print(
    "\nValidation period:"
)

print(
    PROJECT_START,
    "→",
    VALIDATION_END
)


# =========================================================
# HALF ASSIGNMENT
# =========================================================

def assign_half(timestamp):

    if timestamp < MIDPOINT:

        return "Half_1"

    return "Half_2"


# =========================================================
# STORE OBSERVATIONS
# =========================================================

all_observations = []


# =========================================================
# PROCESS VALIDATION ASSETS
# =========================================================

for row in validation.itertuples():

    ticker = (
        row.native_ticker
    )


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


    for column in [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "turnover"
    ]:

        df[column] = pd.to_numeric(
            df[column],
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
            < VALIDATION_END
        )
    ].copy()


    df = df.sort_values(
        "datetime_utc"
    ).reset_index(
        drop=True
    )


    # =====================================================
    # 1-HOUR RETURN
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
    # 3-HOUR MOMENTUM
    # =====================================================

    df[
        "momentum_3h"
    ] = (
        df["close"]
        /
        df["close"].shift(3)
        -
        1
    )


    valid_3h = (
        df["close"]
        .notna()
        .rolling(4)
        .sum()
    )


    df.loc[
        valid_3h != 4,
        "momentum_3h"
    ] = np.nan


    df[
        "short_reversal_3h"
    ] = (
        -df[
            "momentum_3h"
        ]
    )


    # =====================================================
    # VOLATILITY
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
    # WEEKEND BLOCKS
    # =====================================================

    df[
        "is_weekend"
    ] = (
        df["session"]
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
        ].cumsum()
    )


    df[
        "reference_price"
    ] = np.nan


    weekend_ids = (
        df.loc[
            df[
                "is_weekend"
            ],
            "weekend_id"
        ]
        .unique()
    )


    # =====================================================
    # REFERENCE PRICE
    # =====================================================

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
            df[
                "is_weekend"
            ]
        )


        indexes = (
            df.index[
                mask
            ]
        )


        if len(indexes) == 0:

            continue


        first_index = (
            indexes[0]
        )


        if first_index == 0:

            continue


        previous = df.loc[
            :first_index - 1
        ]


        previous = previous[
            previous[
                "close"
            ].notna()
        ]


        if previous.empty:

            continue


        reference_price = (
            previous
            .iloc[-1][
                "close"
            ]
        )


        df.loc[
            indexes,
            "reference_price"
        ] = reference_price


    # =====================================================
    # DISTANCE FROM REFERENCE
    # =====================================================

    df[
        "distance_from_reference"
    ] = (
        df["close"]
        /
        df["reference_price"]
        -
        1
    )


    # =====================================================
    # FORWARD 1-HOUR RETURN
    # =====================================================

    df[
        "forward_return_1h"
    ] = (
        df["close"]
        .shift(-1)
        /
        df["close"]
        -
        1
    )


    valid_forward_1h = (
        df["close"].notna()
        &
        df["close"]
        .shift(-1)
        .notna()
        &
        (
            df["session"]
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
        df["close"]
        .shift(-3)
        /
        df["close"]
        -
        1
    )


    valid_forward_3h = (
        df["close"].notna()
        &
        df["close"]
        .shift(-1)
        .notna()
        &
        df["close"]
        .shift(-2)
        .notna()
        &
        df["close"]
        .shift(-3)
        .notna()
        &
        (
            df["session"]
            .shift(-1)
            ==
            "Weekend"
        )
        &
        (
            df["session"]
            .shift(-2)
            ==
            "Weekend"
        )
        &
        (
            df["session"]
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
    # WEEKEND ONLY
    # =====================================================

    df = df[
        df[
            "session"
        ]
        ==
        "Weekend"
    ].copy()


    df[
        "asset"
    ] = ticker


    df[
        "half"
    ] = (
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
                "distance_from_reference",
                "volatility_expansion",
                "short_reversal_3h",
                "forward_return_1h",
                "forward_return_3h"
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
# CROSS-SECTIONAL SPEARMAN IC
# =========================================================

def calculate_ic(
    group,
    factor,
    target
):

    valid = (
        group[
            factor
        ].notna()
        &
        group[
            target
        ].notna()
    )


    x = group.loc[
        valid,
        factor
    ]


    y = group.loc[
        valid,
        target
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
# VALIDATE EACH CANDIDATE
# =========================================================

results = []


for factor, settings in (
    CANDIDATES.items()
):

    target = (
        settings[
            "target"
        ]
    )


    expected_sign = (
        settings[
            "expected_sign"
        ]
    )


    ic_rows = []


    for timestamp, group in (
        observations.groupby(
            "datetime_utc"
        )
    ):

        ic = calculate_ic(
            group,
            factor,
            target
        )


        if pd.isna(ic):

            continue


        ic_rows.append(
            {
                "datetime_utc":
                timestamp,

                "half":
                group[
                    "half"
                ].iloc[0],

                "ic":
                ic
            }
        )


    ic_df = pd.DataFrame(
        ic_rows
    )


    if ic_df.empty:

        continue


    mean_ic = (
        ic_df[
            "ic"
        ].mean()
    )


    half_means = (
        ic_df.groupby(
            "half"
        )[
            "ic"
        ]
        .mean()
    )


    half_1 = (
        half_means.get(
            "Half_1",
            np.nan
        )
    )


    half_2 = (
        half_means.get(
            "Half_2",
            np.nan
        )
    )


    timestamps = (
        len(
            ic_df
        )
    )


    sign_ok = (
        np.sign(
            mean_ic
        )
        ==
        expected_sign
    )


    magnitude_ok = (
        abs(
            mean_ic
        )
        >=
        MIN_ABS_VALIDATION_IC
    )


    timestamps_ok = (
        timestamps
        >=
        MIN_VALID_TIMESTAMPS
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
        expected_sign
        and
        np.sign(
            half_2
        )
        ==
        expected_sign
    )


    passed = (
        sign_ok
        and
        magnitude_ok
        and
        timestamps_ok
        and
        halves_ok
    )


    minimum_half_strength = (
        min(
            abs(
                half_1
            ),
            abs(
                half_2
            )
        )
        if (
            not pd.isna(
                half_1
            )
            and
            not pd.isna(
                half_2
            )
        )
        else np.nan
    )


    results.append(
        {
            "factor":
            factor,

            "target":
            target,

            "timestamps":
            timestamps,

            "mean_ic":
            mean_ic,

            "half_1_ic":
            half_1,

            "half_2_ic":
            half_2,

            "expected_sign":
            expected_sign,

            "sign_ok":
            sign_ok,

            "magnitude_ok":
            magnitude_ok,

            "timestamps_ok":
            timestamps_ok,

            "halves_ok":
            halves_ok,

            "passes_validation":
            passed,

            "minimum_half_strength":
            minimum_half_strength
        }
    )


results = pd.DataFrame(
    results
)


# =========================================================
# SAVE
# =========================================================

results.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# DISPLAY
# =========================================================

print("\n====================================")
print("VALIDATION RESULTS")
print("====================================\n")


print(
    results[
        [
            "factor",
            "target",
            "timestamps",
            "mean_ic",
            "half_1_ic",
            "half_2_ic",
            "passes_validation"
        ]
    ]
    .round(4)
    .to_string(
        index=False
    )
)


passed = results[
    results[
        "passes_validation"
    ]
].copy()


print("\n====================================")
print("PASSING CANDIDATES")
print("====================================\n")


if passed.empty:

    print(
        "No candidate passed validation."
    )


else:

    passed = passed.sort_values(
        "minimum_half_strength",
        ascending=False
    )


    print(
        passed[
            [
                "factor",
                "target",
                "mean_ic",
                "half_1_ic",
                "half_2_ic",
                "minimum_half_strength"
            ]
        ]
        .round(4)
        .to_string(
            index=False
        )
    )


    winner = (
        passed.iloc[0]
    )


    print(
        "\nFROZEN VALIDATION WINNER:"
    )

    print(
        winner[
            "factor"
        ],
        "→",
        winner[
            "target"
        ]
    )


print("\n====================================")
print("VALIDATION COMPLETE")
print("====================================")


print(
    "Holdout assets were NOT used."
)

print(
    "Do not alter the validation rules "
    "after seeing these results."
)