import requests
import pandas as pd


print("====================================")
print("rFactor Lab")
print("Available rToken Scanner")
print("====================================")


url = "https://api.bitget.com/api/v3/market/instruments"

params = {
    "category": "SPOT"
}


response = requests.get(
    url,
    params=params,
    timeout=20
)

result = response.json()


if result.get("code") != "00000":

    print("Bitget error:")
    print(result)

    raise SystemExit


instruments = result.get(
    "data",
    []
)


rtokens = []


for asset in instruments:

    if (
        str(
            asset.get("isReality")
        ).lower()
        == "yes"
    ):

        rtokens.append(
            {
                "symbol":
                asset.get("symbol"),

                "baseCoin":
                asset.get("baseCoin"),

                "quoteCoin":
                asset.get("quoteCoin"),

                "status":
                asset.get("status")
            }
        )


df = pd.DataFrame(
    rtokens
)


print(
    "\nTotal Reality/rTokens found:",
    len(df)
)


if not df.empty:

    df = df.sort_values(
        "symbol"
    )

    print("\nAvailable rTokens:\n")

    print(
        df.to_string(
            index=False
        )
    )


    df.to_csv(
        "data/available_rtokens.csv",
        index=False
    )


    print(
        "\nSaved to:"
        " data/available_rtokens.csv"
    )


print("\n====================================")
print("SCAN COMPLETE")
print("====================================")