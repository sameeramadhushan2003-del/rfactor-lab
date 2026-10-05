import requests
import pandas as pd
from pathlib import Path


URL = (
    "https://api.bitget.com"
    "/api/v3/reality/market/stock-info"
)


print("====================================")
print("rFactor Lab")
print("Complete Reality Universe")
print("====================================")


response = requests.get(
    URL,
    timeout=30
)

response.raise_for_status()

result = response.json()


if result.get("code") != "00000":

    print("Bitget error:")
    print(result)

    raise SystemExit


data = result.get(
    "data",
    []
)


rows = []


for item in data:

    trading_period = item.get(
        "tradingPeriod",
        []
    )

    if isinstance(
        trading_period,
        list
    ):

        trading_period = ",".join(
            trading_period
        )


    rows.append(
        {
            "rtoken_symbol":
            item.get("symbol"),

            "native_ticker":
            item.get("code"),

            "name":
            item.get("name"),

            "trading_period":
            trading_period,

            "weekend_tradable":
            item.get(
                "weekendTradable"
            )
        }
    )


df = pd.DataFrame(rows)


if df.empty:

    print(
        "No Reality symbols returned."
    )

    raise SystemExit


df = df.drop_duplicates(
    subset=[
        "rtoken_symbol"
    ]
)


df = df.sort_values(
    [
        "native_ticker",
        "rtoken_symbol"
    ]
)


Path("data").mkdir(
    exist_ok=True
)


OUTPUT_FILE = Path(
    "data/reality_stock_info.csv"
)


df.to_csv(
    OUTPUT_FILE,
    index=False
)


print(
    "\nTotal Reality pairs:",
    len(df)
)


weekend = df[
    df["weekend_tradable"]
    .astype(str)
    .str.lower()
    == "yes"
]


print(
    "Weekend-tradable pairs:",
    len(weekend)
)


print(
    "\nFirst 30 pairs:\n"
)


print(
    df.head(30)
    .to_string(index=False)
)


print(
    "\nCheck important symbols:"
)


for ticker in [
    "AAPL",
    "NVDA",
    "TSLA",
    "SPY",
    "QQQ"
]:

    match = df[
        df["native_ticker"]
        == ticker
    ]

    if not match.empty:

        print(
            ticker,
            "->",
            match.iloc[0][
                "rtoken_symbol"
            ],
            "| Weekend:",
            match.iloc[0][
                "weekend_tradable"
            ]
        )

    else:

        print(
            ticker,
            "-> NOT FOUND"
        )


print(
    "\nSaved to:",
    OUTPUT_FILE
)

print("====================================")
print("UNIVERSE DOWNLOAD COMPLETE")
print("====================================")