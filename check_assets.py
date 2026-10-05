import requests


symbols = [
    "rNVDAUSDT",
    "rAAPLUSDT",
    "rTSLAUSDT"
]


url = "https://api.bitget.com/api/v3/market/instruments"


print("====================================")
print("rFactor Lab - Asset Check")
print("====================================")


for symbol in symbols:

    params = {
        "category": "SPOT",
        "symbol": symbol
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        result = response.json()

        data = result.get("data", [])


        if data:

            asset = data[0]

            print(
                "\n",
                symbol,
                "FOUND"
            )

            print(
                "Status:",
                asset.get("status")
            )

            print(
                "Reality:",
                asset.get("isReality")
            )

        else:

            print(
                "\n",
                symbol,
                "NOT FOUND"
            )


    except Exception as error:

        print(
            "\nError checking",
            symbol
        )

        print(error)


print("\n====================================")
print("CHECK COMPLETE")
print("====================================")