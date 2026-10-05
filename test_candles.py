import requests
from datetime import datetime, timezone

url = "https://api.bitget.com/api/v3/market/candles"

params = {
    "category": "SPOT",
    "symbol": "rNVDAUSDT",
    "interval": "1H",
    "type": "market",
    "limit": "10"
}

response = requests.get(url, params=params, timeout=15)

print("HTTP Status:", response.status_code)

result = response.json()

print("Bitget code:", result.get("code"))
print("Message:", result.get("msg"))

candles = result.get("data", [])

print("Candles received:", len(candles))

print("\nLatest candles:\n")

for candle in candles:
    timestamp = int(candle[0])

    date = datetime.fromtimestamp(
        timestamp / 1000,
        tz=timezone.utc
    )

    print(
        date,
        "Open:", candle[1],
        "High:", candle[2],
        "Low:", candle[3],
        "Close:", candle[4],
        "Volume:", candle[5]
    )