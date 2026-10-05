import requests

url = "https://api.bitget.com/api/v3/market/instruments"

params = {
    "category": "SPOT",
    "symbol": "rNVDAUSDT"
}

response = requests.get(url, params=params, timeout=15)

print("HTTP Status:", response.status_code)

data = response.json()

print("Bitget code:", data.get("code"))
print("Message:", data.get("msg"))

if data.get("data"):
    instrument = data["data"][0]

    print("\nSymbol:", instrument.get("symbol"))
    print("Base coin:", instrument.get("baseCoin"))
    print("Quote coin:", instrument.get("quoteCoin"))
    print("Reality token:", instrument.get("isReality"))
    print("Status:", instrument.get("status"))
else:
    print("\nNo instrument data returned.")