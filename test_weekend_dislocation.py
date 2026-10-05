import pandas as pd
import numpy as np
from pathlib import Path


# =========================================================
# SETTINGS
# =========================================================

ASSETS = {
    "rNVDA": Path("data/rNVDA_1H_prepared.csv"),
    "rAAPL": Path("data/rAAPL_1H_prepared.csv"),
    "rTSLA": Path("data/rTSLA_1H_prepared.csv")
}

DEVELOPMENT_DAYS = 60

VOLATILITY_WINDOW = 24

# Fixed before seeing results
Z_THRESHOLD = 1.5

HORIZONS = [
    3,
    6
]


print("====================================")
print("rFactor Lab")
print("Weekend Dislocation Factor")
print("====================================")


# =========================================================
# FIND DEVELOPMENT PERIOD
# =========================================================

starts = []

for asset, file in ASSETS.items():

    temp = pd.read_csv(file)

    temp["datetime_utc"] = pd.to_datetime(
        temp["datetime_utc"],
        utc=True
    )

    starts.append(
        temp["datetime_utc"].min()
    )


PROJECT_START = min(starts)

DEVELOPMENT_END = (
    PROJECT_START
    + pd.Timedelta(days=DEVELOPMENT_DAYS)
)


print(
    "\nDevelopment:",
    PROJECT_START,
    "→",
    DEVELOPMENT_END
)


# =========================================================
# RESULTS
# =========================================================

all_trades = []


# =========================================================
# PROCESS ASSETS
# =========================================================

for asset, file in ASSETS.items():

    print("\n====================================")
    print("Processing:", asset)
    print("====================================")

    df = pd.read_csv(file)

    df["datetime_utc"] = pd.to_datetime(
        df["datetime_utc"],
        utc=True
    )

    for col in ["open", "close"]:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )


    df = df[
        df["datetime_utc"] < DEVELOPMENT_END
    ].copy()


    df = df.sort_values(
        "datetime_utc"
    ).reset_index(drop=True)


    # =====================================================
    # HOURLY RETURN
    # =====================================================

    df["return_1h"] = (
        df["close"]
        /
        df["close"].shift(1)
        - 1
    )


    valid_return = (
        df["close"].notna()
        &
        df["close"].shift(1).notna()
    )


    df.loc[
        ~valid_return,
        "return_1h"
    ] = np.nan


    # =====================================================
    # TRAILING VOLATILITY
    # =====================================================

    df["volatility_24h"] = (
        df["return_1h"]
        .shift(1)
        .rolling(
            VOLATILITY_WINDOW,
            min_periods=12
        )
        .std()
    )


    # =====================================================
    # IDENTIFY WEEKEND BLOCKS
    # =====================================================

    df["is_weekend"] = (
        df["session"] == "Weekend"
    )


    df["weekend_start"] = (
        df["is_weekend"]
        &
        ~df["is_weekend"].shift(
            1,
            fill_value=False
        )
    )


    df["weekend_id"] = (
        df["weekend_start"]
        .cumsum()
    )


    # =====================================================
    # PROCESS EACH WEEKEND
    # =====================================================

    weekend_ids = (
        df.loc[
            df["is_weekend"],
            "weekend_id"
        ]
        .unique()
    )


    for weekend_id in weekend_ids:

        weekend = df[
            (df["weekend_id"] == weekend_id)
            &
            (df["is_weekend"])
        ].copy()


        if weekend.empty:

            continue


        first_index = weekend.index[0]


        if first_index == 0:

            continue


        # -----------------------------------------------
        # FIND LAST VALID PRICE BEFORE WEEKEND
        # -----------------------------------------------

        previous_data = df.loc[
            :first_index - 1
        ]


        previous_valid = previous_data[
            previous_data["close"].notna()
        ]


        if previous_valid.empty:

            continue


        reference_row = (
            previous_valid.iloc[-1]
        )


        reference_price = (
            reference_row["close"]
        )


        # -----------------------------------------------
        # HOURS SINCE WEEKEND START
        # -----------------------------------------------

        weekend["hours_from_reference"] = (
            np.arange(
                1,
                len(weekend) + 1
            )
        )


        # -----------------------------------------------
        # PRICE DISLOCATION
        # -----------------------------------------------

        weekend["dislocation"] = (
            weekend["close"]
            /
            reference_price
            - 1
        )


        # -----------------------------------------------
        # EXPECTED MOVE
        # -----------------------------------------------

        weekend["expected_move"] = (
            weekend["volatility_24h"]
            *
            np.sqrt(
                weekend[
                    "hours_from_reference"
                ]
            )
        )


        # -----------------------------------------------
        # DISLOCATION Z-SCORE
        # -----------------------------------------------

        weekend["dislocation_z"] = (
            weekend["dislocation"].abs()
            /
            weekend["expected_move"]
        )


        # =================================================
        # TEST EACH HOLDING HORIZON
        # =================================================

        for horizon in HORIZONS:

            next_allowed_index = -1


            for i in weekend.index:

                if i <= next_allowed_index:

                    continue


                row = df.loc[i]


                weekend_row = weekend.loc[i]


                if pd.isna(
                    weekend_row[
                        "dislocation_z"
                    ]
                ):

                    continue


                if (
                    weekend_row[
                        "dislocation_z"
                    ]
                    < Z_THRESHOLD
                ):

                    continue


                if pd.isna(
                    weekend_row[
                        "dislocation"
                    ]
                ):

                    continue


                # ---------------------------------------
                # FUTURE WINDOW
                # ---------------------------------------

                future = df.iloc[
                    i + 1:
                    i + horizon + 1
                ]


                if len(future) != horizon:

                    continue


                # Must remain completely weekend

                if not (
                    future["session"]
                    == "Weekend"
                ).all():

                    continue


                if (
                    future["open"].isna().any()
                    or
                    future["close"].isna().any()
                ):

                    continue


                entry_price = (
                    future.iloc[0]["open"]
                )

                exit_price = (
                    future.iloc[-1]["close"]
                )


                # ---------------------------------------
                # CONTRARIAN SIGNAL
                # ---------------------------------------

                signal = (
                    -np.sign(
                        weekend_row[
                            "dislocation"
                        ]
                    )
                )


                if signal == 0:

                    continue


                raw_return = (
                    exit_price
                    /
                    entry_price
                    - 1
                )


                strategy_return = (
                    signal
                    *
                    raw_return
                )


                all_trades.append(
                    {
                        "asset":
                        asset,

                        "signal_time":
                        row[
                            "datetime_utc"
                        ],

                        "horizon_hours":
                        horizon,

                        "reference_price":
                        reference_price,

                        "current_price":
                        weekend_row[
                            "close"
                        ],

                        "dislocation_pct":
                        weekend_row[
                            "dislocation"
                        ] * 100,

                        "dislocation_z":
                        weekend_row[
                            "dislocation_z"
                        ],

                        "signal":
                        signal,

                        "entry_price":
                        entry_price,

                        "exit_price":
                        exit_price,

                        "strategy_return_pct":
                        strategy_return * 100
                    }
                )


                next_allowed_index = (
                    i + horizon
                )


# =========================================================
# RESULT TABLE
# =========================================================

results = pd.DataFrame(
    all_trades
)


if results.empty:

    raise SystemExit(
        "No signals found."
    )


results["winner"] = (
    results[
        "strategy_return_pct"
    ] > 0
)


# =========================================================
# SUMMARY
# =========================================================

def summarize(group):

    x = group[
        "strategy_return_pct"
    ]


    return pd.Series(
        {
            "trades":
            len(x),

            "mean_pct":
            x.mean(),

            "median_pct":
            x.median(),

            "std_pct":
            x.std(),

            "hit_rate_pct":
            (
                x > 0
            ).mean() * 100
        }
    )


# =========================================================
# COMBINED RESULTS
# =========================================================

print(
    "\n1. COMBINED RESULTS"
)


combined = (
    results.groupby(
        "horizon_hours"
    )
    .apply(
        summarize,
        include_groups=False
    )
)


print(
    combined.round(4)
)


# =========================================================
# BY ASSET
# =========================================================

print(
    "\n2. RESULTS BY ASSET"
)


by_asset = (
    results.groupby(
        [
            "asset",
            "horizon_hours"
        ]
    )
    .apply(
        summarize,
        include_groups=False
    )
)


print(
    by_asset.round(4)
)


# =========================================================
# SIGNAL COUNTS
# =========================================================

print(
    "\n3. SIGNAL COUNTS"
)


print(
    results.groupby(
        [
            "asset",
            "horizon_hours"
        ]
    ).size()
)


# =========================================================
# SAVE
# =========================================================

OUTPUT_FILE = Path(
    "data/weekend_dislocation_development.csv"
)


results.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n====================================")
print("DISLOCATION TEST COMPLETE")
print("====================================")

print(
    "Saved to:",
    OUTPUT_FILE
)

print(
    "Out-of-sample period remains hidden."
)