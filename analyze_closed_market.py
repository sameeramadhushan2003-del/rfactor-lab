import pandas as pd
import numpy as np
from pathlib import Path


# -----------------------------------------
# SETTINGS
# -----------------------------------------

RTOKEN_FILE = Path(
    "data/rNVDA_1H_factors.csv"
)

STOCK_FILE = Path(
    "data/NVDA_1H_aligned.csv"
)

OUTPUT_FILE = Path(
    "data/closed_market_development.csv"
)

DEVELOPMENT_DAYS = 60

MIN_CLOSURE_HOURS = 24


print("====================================")
print("rFactor Lab")
print("Closed-Market Event Study")
print("====================================")


# -----------------------------------------
# LOAD rNVDA
# -----------------------------------------

rtoken = pd.read_csv(
    RTOKEN_FILE
)

rtoken["datetime_utc"] = pd.to_datetime(
    rtoken["datetime_utc"],
    utc=True
)

rtoken["close"] = pd.to_numeric(
    rtoken["close"],
    errors="coerce"
)

rtoken = rtoken.sort_values(
    "datetime_utc"
).reset_index(drop=True)


# -----------------------------------------
# DEVELOPMENT PERIOD
# -----------------------------------------

project_start = (
    rtoken["datetime_utc"].min()
)

development_end = (
    project_start
    + pd.Timedelta(
        days=DEVELOPMENT_DAYS
    )
)


print("\n1. DEVELOPMENT PERIOD")

print(
    "Start:",
    project_start
)

print(
    "End:",
    development_end
)


rtoken = rtoken[
    rtoken["datetime_utc"]
    < development_end
].copy()


# -----------------------------------------
# LOAD NATIVE NVDA
# -----------------------------------------

stock = pd.read_csv(
    STOCK_FILE
)

stock["datetime_utc"] = pd.to_datetime(
    stock["datetime_utc"],
    utc=True
)


for column in [
    "open",
    "high",
    "low",
    "close"
]:

    stock[column] = pd.to_numeric(
        stock[column],
        errors="coerce"
    )


# -----------------------------------------
# HANDLE valid_hour COLUMN
# -----------------------------------------

if stock["valid_hour"].dtype != bool:

    stock["valid_hour"] = (
        stock["valid_hour"]
        .astype(str)
        .str.lower()
        .eq("true")
    )


stock = stock[
    stock["valid_hour"]
].copy()


stock = stock[
    stock["datetime_utc"]
    < development_end
].copy()


stock = stock.sort_values(
    "datetime_utc"
).reset_index(drop=True)


print(
    "\nValid native NVDA hours:",
    len(stock)
)


# -----------------------------------------
# FIND LONG MARKET CLOSURES
# -----------------------------------------

events = []


for i in range(
    len(stock) - 1
):

    before = stock.iloc[i]

    after = stock.iloc[i + 1]


    closure_hours = (
        after["datetime_utc"]
        - before["datetime_utc"]
    ).total_seconds() / 3600


    # Ignore ordinary gaps
    if closure_hours < MIN_CLOSURE_HOURS:

        continue


    # -------------------------------------
    # rNVDA PRICE AT START OF CLOSURE
    # -------------------------------------

    start_match = rtoken[
        (
            rtoken["datetime_utc"]
            ==
            before["datetime_utc"]
        )
        &
        (
            rtoken["close"].notna()
        )
    ]


    if start_match.empty:

        continue


    rtoken_start_price = (
        start_match.iloc[0]["close"]
    )


    # -------------------------------------
    # rNVDA CANDLES DURING CLOSURE
    # -------------------------------------

    during_closure = rtoken[
        (
            rtoken["datetime_utc"]
            >
            before["datetime_utc"]
        )
        &
        (
            rtoken["datetime_utc"]
            <
            after["datetime_utc"]
        )
        &
        (
            rtoken["close"].notna()
        )
    ].copy()


    if during_closure.empty:

        continue


    # Last available rToken candle
    # before native NVDA trading resumes

    final_rtoken = (
        during_closure.iloc[-1]
    )

    rtoken_end_price = (
        final_rtoken["close"]
    )


    # -------------------------------------
    # rTOKEN CLOSED-MARKET RETURN
    # -------------------------------------

    rtoken_return = (
        rtoken_end_price
        /
        rtoken_start_price
        - 1
    )


    # -------------------------------------
    # NATIVE NVDA REOPEN GAP
    # -------------------------------------

    nvda_before = (
        before["close"]
    )

    nvda_after_open = (
        after["open"]
    )


    native_reopen_gap = (
        nvda_after_open
        /
        nvda_before
        - 1
    )


    # -------------------------------------
    # TRACKING DIFFERENCE
    # -------------------------------------

    tracking_difference = (
        rtoken_return
        -
        native_reopen_gap
    )


    # -------------------------------------
    # MAX rTOKEN MOVE DURING CLOSURE
    # -------------------------------------

    deviations = (
        during_closure["close"]
        /
        rtoken_start_price
        - 1
    )


    max_absolute_move = (
        deviations
        .abs()
        .max()
    )


    # -------------------------------------
    # SAME DIRECTION?
    # -------------------------------------

    same_direction = (
        np.sign(
            rtoken_return
        )
        ==
        np.sign(
            native_reopen_gap
        )
    )


    # -------------------------------------
    # NEW YORK TIMES FOR DISPLAY
    # -------------------------------------

    start_et = (
        before["datetime_utc"]
        .tz_convert(
            "America/New_York"
        )
    )

    reopen_et = (
        after["datetime_utc"]
        .tz_convert(
            "America/New_York"
        )
    )


    # -------------------------------------
    # SAVE EVENT
    # -------------------------------------

    events.append(
        {
            "closure_start_et":
            start_et,

            "reopen_et":
            reopen_et,

            "closure_hours":
            closure_hours,

            "rtoken_start_price":
            rtoken_start_price,

            "rtoken_end_price":
            rtoken_end_price,

            "rtoken_return_pct":
            rtoken_return * 100,

            "nvda_close_before":
            nvda_before,

            "nvda_reopen_open":
            nvda_after_open,

            "nvda_reopen_gap_pct":
            native_reopen_gap * 100,

            "tracking_difference_pct":
            tracking_difference * 100,

            "max_rtoken_move_pct":
            max_absolute_move * 100,

            "same_direction":
            same_direction,

            "rtoken_candles":
            len(during_closure)
        }
    )


# -----------------------------------------
# CREATE RESULTS TABLE
# -----------------------------------------

results = pd.DataFrame(
    events
)


print("\n2. CLOSED-MARKET EVENTS")

print(
    "Events found:",
    len(results)
)


if results.empty:

    print(
        "No qualifying events found."
    )

    raise SystemExit


# -----------------------------------------
# SHOW EACH EVENT
# -----------------------------------------

display_columns = [
    "closure_start_et",
    "reopen_et",
    "closure_hours",
    "rtoken_return_pct",
    "nvda_reopen_gap_pct",
    "tracking_difference_pct",
    "max_rtoken_move_pct",
    "same_direction"
]


print("\n3. EVENT RESULTS\n")

print(
    results[
        display_columns
    ]
    .round(4)
    .to_string(
        index=False
    )
)


# -----------------------------------------
# SUMMARY
# -----------------------------------------

print("\n4. SUMMARY")

print(
    "Average rNVDA closed-market return:",
    round(
        results[
            "rtoken_return_pct"
        ].mean(),
        4
    ),
    "%"
)


print(
    "Average NVDA reopen gap:",
    round(
        results[
            "nvda_reopen_gap_pct"
        ].mean(),
        4
    ),
    "%"
)


print(
    "Average absolute tracking difference:",
    round(
        results[
            "tracking_difference_pct"
        ].abs().mean(),
        4
    ),
    "%"
)


direction_agreement = (
    results[
        "same_direction"
    ].mean()
    * 100
)


print(
    "Direction agreement:",
    round(
        direction_agreement,
        2
    ),
    "%"
)


# -----------------------------------------
# CORRELATION
# -----------------------------------------

if len(results) >= 2:

    correlation = (
        results[
            "rtoken_return_pct"
        ]
        .corr(
            results[
                "nvda_reopen_gap_pct"
            ]
        )
    )

    print(
        "Closed-market/reopen correlation:",
        round(
            correlation,
            4
        )
    )


# -----------------------------------------
# SAVE
# -----------------------------------------

results.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n====================================")
print("EVENT STUDY COMPLETE")
print("====================================")

print(
    "Saved to:",
    OUTPUT_FILE
)

print(
    "Out-of-sample period "
    "was NOT tested."
)