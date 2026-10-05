"""Educational factor comparison using illustrative, NOT REAL market prices.

No trading, prediction, or competition-ready backtest is performed here.
"""
import csv
import json
import math
from pathlib import Path
from statistics import stdev

ROOT = Path(__file__).resolve().parent
WINDOW = 3  # compare each day's price with the price 3 observations before it


def load_prices(path):
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        expected = {"day", "rtoken_close", "stock_close"}
        if set(reader.fieldnames or []) != expected:
            raise ValueError(f"CSV must contain exactly these columns: {sorted(expected)}")
        rows = []
        seen = set()
        for entry in reader:
            day = entry["day"].strip()
            if not day or day in seen:
                raise ValueError("Each observation must have a unique, nonempty label")
            seen.add(day)
            a = float(entry["rtoken_close"])
            b = float(entry["stock_close"])
            if not all(math.isfinite(x) and x > 0 for x in (a, b)):
                raise ValueError("Prices must be finite positive numbers")
            rows.append({"day": day, "rtoken_close": a, "stock_close": b})
    if len(rows) < WINDOW + 2:
        raise ValueError("Not enough observations")
    return rows


def analyze(rows):
    """Compute historical 3-observation momentum and sample return volatility."""
    output = []
    for i in range(WINDOW + 1, len(rows)):
        record = {"day": rows[i]["day"]}
        for prefix in ("rtoken", "stock"):
            prices = [row[f"{prefix}_close"] for row in rows]
            momentum = prices[i] / prices[i - WINDOW] - 1
            recent_returns = [prices[j] / prices[j - 1] - 1
                              for j in range(i - WINDOW + 1, i + 1)]
            volatility = stdev(recent_returns)
            record[f"{prefix}_momentum_pct"] = round(momentum * 100, 4)
            record[f"{prefix}_volatility_pct"] = round(volatility * 100, 4)
        output.append(record)
    return output


def main():
    rows = load_prices(ROOT / "sample_prices.csv")
    results = analyze(rows)
    report = {
        "data_label": "ILLUSTRATIVE EXAMPLE DATA — NOT REAL MARKET DATA",
        "note": "Historical descriptive factors only; not a backtest or trading advice.",
        "window_observations": WINDOW,
        "results": results,
    }
    output_file = ROOT / "sample_report.json"
    output_file.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(report["data_label"])
    print("Day     rToken momentum  Stock momentum  rToken volatility  Stock volatility")
    for row in results[-5:]:
        print(f"{row['day']:<8}{row['rtoken_momentum_pct']:>13.2f}%"
              f"{row['stock_momentum_pct']:>16.2f}%"
              f"{row['rtoken_volatility_pct']:>18.2f}%"
              f"{row['stock_volatility_pct']:>17.2f}%")
    print(f"Report saved: {output_file.name}")


if __name__ == "__main__":
    main()
