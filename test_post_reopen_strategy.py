import pandas as pd
import numpy as np
from pathlib import Path


# =========================================================
# SETTINGS
# =========================================================

EVENT_FILE = Path(
    "data/multi_asset_closed_market_development.csv"
)

RTOKEN_FILES = {
    "NVDA": Path("data/rNVDA_1H_prepared.csv"),
    "AAPL": Path("data/rAAPL_1H_prepared.csv"),
    "TSLA": Path("data/rTSLA_1H_prepared.csv")
}

HORIZONS = [
    1,
    3,
    6
]


print("====================================")
print("rFactor Lab")
print("Post-Reopen Strategy Test")
print("====================================")


# =========================================================
# LOAD DEVELOPMENT EVENTS
# =========================================================

events = pd.read_csv(
    EVENT_FILE
)

events["reopen_et"] = pd.to_datetime(
    events["reopen_et"]
)

events["rtoken_closed_return_pct"] = pd.to_numeric(
    events["rtoken_closed_return_pct"],
    errors="coerce"
)


print(
    "\nDevelopment events:",
    len(events)
)


# =========================================================
# LOAD ALL RTOKEN DATA
# =========================================================

rtoken_data = {}


for ticker, file in RTOKEN_FILES.items():

    df = pd.read_csv(file)

    df["datetime_utc"] = pd.to_datetime(
        df["datetime_utc"],
        utc=True
    )

    for column in [
        "open",
        "close"
    ]:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df = df.sort_values(
        "datetime_utc"
    ).reset_index(drop=True)

    rtoken_data[ticker] = df


# =========================================================
# STORE TEST RESULTS
# =========================================================

results = []


# =========================================================
# PROCESS EACH CLOSED-MARKET EVENT
# =========================================================

for _, event in events.iterrows():

    ticker = event["ticker"]

    df = rtoken_data[ticker]


    # -----------------------------------------------------
    # REOPEN TIME
    # -----------------------------------------------------

    reopen_et = event["reopen_et"]

    reopen_utc = (
        reopen_et
        .tz_convert("UTC")
    )


    # -----------------------------------------------------
    # ENTRY PRICE
    # -----------------------------------------------------

    entry_row = df[
        df["datetime_utc"]
        == reopen_utc
    ]


    if entry_row.empty:

        continue


    entry_price = (
        entry_row.iloc[0]["open"]
    )


    if pd.isna(entry_price):

        continue


    # -----------------------------------------------------
    # CLOSED-MARKET SIGNAL
    # -----------------------------------------------------

    closed_return = (
        event[
            "rtoken_closed_return_pct"
        ]
        / 100
    )


    if closed_return > 0:

        signal = 1

    elif closed_return < 0:

        signal = -1

    else:

        continue


    # =====================================================
    # TEST EACH HOLDING HORIZON
    # =====================================================

    for horizon in HORIZONS:

        # Candle whose close represents
        # the end of the holding period

        exit_timestamp = (
            reopen_utc
            + pd.Timedelta(
                hours=horizon - 1
            )
        )


        exit_row = df[
            df["datetime_utc"]
            == exit_timestamp
        ]


        if exit_row.empty:

            continue


        exit_price = (
            exit_row.iloc[0]["close"]
        )


        if pd.isna(exit_price):

            continue


        # -------------------------------------------------
        # RAW rTOKEN RETURN
        # -------------------------------------------------

        raw_return = (
            exit_price
            /
            entry_price
            - 1
        )


        # -------------------------------------------------
        # CONTINUATION STRATEGY
        # -------------------------------------------------

        continuation_return = (
            signal
            * raw_return
        )


        # -------------------------------------------------
        # MEAN REVERSION STRATEGY
        # -------------------------------------------------

        reversion_return = (
            -signal
            * raw_return
        )


        results.append(
            {
                "ticker":
                ticker,

                "reopen_et":
                reopen_et,

                "horizon_hours":
                horizon,

                "closed_return_pct":
                closed_return * 100,

                "entry_price":
                entry_price,

                "exit_price":
                exit_price,

                "raw_post_reopen_return_pct":
                raw_return * 100,

                "continuation_return_pct":
                continuation_return * 100,

                "reversion_return_pct":
                reversion_return * 100
            }
        )


# =========================================================
# CREATE DATAFRAME
# =========================================================

results = pd.DataFrame(
    results
)


print(
    "\nValid strategy observations:",
    len(results)
)


if results.empty:

    raise SystemExit(
        "No usable strategy observations."
    )


# =========================================================
# STRATEGY SUMMARY
# =========================================================

def strategy_summary(
    group,
    column
):

    values = group[column]

    return pd.Series(
        {
            "observations":
            len(values),

            "mean_pct":
            values.mean(),

            "median_pct":
            values.median(),

            "std_pct":
            values.std(),

            "hit_rate_pct":
            (
                values > 0
            ).mean() * 100
        }
    )


# =========================================================
# CONTINUATION
# =========================================================

print(
    "\n1. CONTINUATION STRATEGY"
)


continuation = (
    results.groupby(
        "horizon_hours"
    )
    .apply(
        lambda x:
        strategy_summary(
            x,
            "continuation_return_pct"
        ),
        include_groups=False
    )
)


print(
    continuation.round(4)
)


# =========================================================
# MEAN REVERSION
# =========================================================

print(
    "\n2. MEAN-REVERSION STRATEGY"
)


reversion = (
    results.groupby(
        "horizon_hours"
    )
    .apply(
        lambda x:
        strategy_summary(
            x,
            "reversion_return_pct"
        ),
        include_groups=False
    )
)


print(
    reversion.round(4)
)


# =========================================================
# BREAKDOWN BY ASSET
# =========================================================

print(
    "\n3. MEAN REVERSION BY ASSET AND HORIZON"
)


asset_summary = (
    results.groupby(
        [
            "ticker",
            "horizon_hours"
        ]
    )
    .apply(
        lambda x:
        strategy_summary(
            x,
            "reversion_return_pct"
        ),
        include_groups=False
    )
)


print(
    asset_summary.round(4)
)


# =========================================================
# SAVE
# =========================================================

output_file = Path(
    "data/post_reopen_strategy_development.csv"
)


results.to_csv(
    output_file,
    index=False
)


print("\n====================================")
print("POST-REOPEN TEST COMPLETE")
print("====================================")

print(
    "Saved to:",
    output_file
)

print(
    "Out-of-sample data remains hidden."
)