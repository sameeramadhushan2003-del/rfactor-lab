import yfinance as yf
import pandas as pd
from pathlib import Path


# -----------------------------------------
# STOCKS
# -----------------------------------------

STOCKS = {
    "AAPL": "AAPL_15m.csv",
    "TSLA": "TSLA_15m.csv"
}


# -----------------------------------------
# DOWNLOAD FUNCTION
# -----------------------------------------

def download_stock(ticker, filename):

    print("\n====================================")
    print("Downloading native stock:", ticker)
    print("====================================")

    stock = yf.Ticker(ticker)

    df = stock.history(
        period="60d",
        interval="15m",
        prepost=True,
        auto_adjust=False
    )


    # -------------------------------------
    # CHECK DATA
    # -------------------------------------

    if df.empty:

        print(
            "No data downloaded for",
            ticker
        )

        return


    # -------------------------------------
    # RESET INDEX
    # -------------------------------------

    df = df.reset_index()


    # -------------------------------------
    # FIND DATETIME COLUMN
    # -------------------------------------

    if "Datetime" in df.columns:

        df = df.rename(
            columns={
                "Datetime": "datetime"
            }
        )

    elif "Date" in df.columns:

        df = df.rename(
            columns={
                "Date": "datetime"
            }
        )


    # -------------------------------------
    # CONVERT DATETIME
    # -------------------------------------

    df["datetime"] = pd.to_datetime(
        df["datetime"],
        utc=True
    )


    # -------------------------------------
    # RENAME COLUMNS
    # -------------------------------------

    df = df.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume"
        }
    )


    # -------------------------------------
    # KEEP NEEDED COLUMNS
    # -------------------------------------

    df = df[
        [
            "datetime",
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]
    ]


    df = df.sort_values(
        "datetime"
    )


    # -------------------------------------
    # SAVE
    # -------------------------------------

    output_file = Path(
        "data"
    ) / filename

    output_file.parent.mkdir(
        exist_ok=True
    )

    df.to_csv(
        output_file,
        index=False
    )


    # -------------------------------------
    # RESULTS
    # -------------------------------------

    print(
        "Rows:",
        len(df)
    )

    print(
        "First:",
        df["datetime"].iloc[0]
    )

    print(
        "Last:",
        df["datetime"].iloc[-1]
    )

    print(
        "Saved to:",
        output_file
    )


# -----------------------------------------
# RUN
# -----------------------------------------

print("====================================")
print("rFactor Lab")
print("Native Stock Multi Downloader")
print("====================================")


for ticker, filename in STOCKS.items():

    download_stock(
        ticker,
        filename
    )


print("\n====================================")
print("ALL STOCK DOWNLOADS COMPLETE")
print("====================================")