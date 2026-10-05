import json
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent

RAW_DIR = BASE_DIR / "data" / "v2_raw"

SPLIT_FILE = (
    BASE_DIR
    / "data"
    / "v2_research_split.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "frontend"
    / "public"
    / "data"
    / "tokens.json"
)


# =========================================================
# LOAD TOKEN METADATA
# =========================================================

split_df = pd.read_csv(
    SPLIT_FILE
)


tokens = []


for _, meta in split_df.iterrows():

    ticker = str(
        meta["native_ticker"]
    ).strip()

    rtoken_symbol = str(
        meta["rtoken_symbol"]
    ).strip()


    # Example:
    # AAOI -> AAOI_365d_1H.csv
    matches = list(
        RAW_DIR.glob(
            f"{ticker}_365d_1H.csv"
        )
    )


    if not matches:

        print(
            f"Skipping {ticker}: raw file not found"
        )

        continue


    raw_file = matches[0]

    df = pd.read_csv(
        raw_file
    )


    if df.empty:
        continue


    # -----------------------------------------------------
    # DATETIME
    # -----------------------------------------------------

    df["datetime_utc"] = pd.to_datetime(
        df["datetime_utc"],
        utc=True,
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "datetime_utc",
            "close"
        ]
    ).copy()


    df = df.sort_values(
        "datetime_utc"
    )


    # -----------------------------------------------------
    # RETURNS / FACTOR
    # -----------------------------------------------------

    df["return_1h"] = (
        df["close"]
        .pct_change()
        * 100
    )

    df["next_return_1h"] = (
        df["close"]
        .shift(-1)
        / df["close"]
        - 1
    ) * 100


    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    latest = df.iloc[-1]

    latest_return = (
        df["return_1h"]
        .dropna()
        .iloc[-1]
        if df["return_1h"]
        .notna()
        .any()
        else 0
    )


    first_date = (
        df["datetime_utc"]
        .iloc[0]
    )

    last_date = (
        df["datetime_utc"]
        .iloc[-1]
    )


    history_days = (
        last_date -
        first_date
    ).total_seconds() / 86400


    # -----------------------------------------------------
    # RECENT CHART DATA
    # Keep last 30 days so JSON does not become huge
    # -----------------------------------------------------

    chart_start = (
        last_date -
        pd.Timedelta(days=30)
    )


    recent = df[
        df["datetime_utc"]
        >= chart_start
    ].copy()


    chart_data = []

    for _, row in recent.iterrows():

        chart_data.append({
            "datetime":
                row["datetime_utc"]
                .isoformat(),

            "close":
                round(
                    float(row["close"]),
                    6
                ),

            "return1h":
                None
                if pd.isna(
                    row["return_1h"]
                )
                else round(
                    float(
                        row["return_1h"]
                    ),
                    4
                ),

            "nextReturn1h":
                None
                if pd.isna(
                    row[
                        "next_return_1h"
                    ]
                )
                else round(
                    float(
                        row[
                            "next_return_1h"
                        ]
                    ),
                    4
                ),

            "volume":
                round(
                    float(
                        row["volume"]
                    ),
                    4
                ),
        })


    # -----------------------------------------------------
    # DISPLAY TOKEN NAME
    # RNVDAUSDT -> rNVDA
    # -----------------------------------------------------

    display_symbol = ticker

    if ticker:
        display_symbol = (
            "r" + ticker
        )


    tokens.append({
        "ticker":
            ticker,

        "displaySymbol":
            display_symbol,

        "rtokenSymbol":
            rtoken_symbol,

        "group":
            str(
                meta["v2_group"]
            ),

        "coveragePct":
            round(
                float(
                    meta[
                        "corrected_coverage_pct"
                    ]
                ),
                2
            ),

        "qualityOk":
            bool(
                meta[
                    "candle_quality_ok"
                ]
            ),

        "factorEligible":
            bool(
                meta[
                    "general_factor_eligible"
                ]
            ),

        "splitFrozen":
            bool(
                meta[
                    "split_frozen"
                ]
            ),

        "rows":
            int(len(df)),

        "historyDays":
            round(
                history_days,
                1
            ),

        "startDate":
            first_date.isoformat(),

        "endDate":
            last_date.isoformat(),

        "latestPrice":
            round(
                float(
                    latest["close"]
                ),
                6
            ),

        "latestMomentum1hPct":
            round(
                float(
                    latest_return
                ),
                4
            ),

        "chart":
            chart_data,
    })


# =========================================================
# OUTPUT
# =========================================================

output = {
    "totalTokens":
        len(tokens),

    "tokens":
        sorted(
            tokens,
            key=lambda x:
                x["ticker"]
        ),
}


OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        output,
        file,
        indent=2
    )


print(
    f"Exported {len(tokens)} tokens"
)

print(
    f"Saved to: {OUTPUT_FILE}"
)