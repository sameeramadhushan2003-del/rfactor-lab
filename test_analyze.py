import csv
import tempfile
import unittest
from pathlib import Path
from analyze import analyze, load_prices


class FactorLabTests(unittest.TestCase):
    def test_example_analysis(self):
        rows = load_prices(Path(__file__).resolve().parents[1] / "sample_prices.csv")
        report = analyze(rows)
        self.assertEqual(len(report), len(rows) - 4)
        self.assertEqual(report[-1]["day"], "Day 14")
        self.assertIn("rtoken_volatility_pct", report[-1])

    def test_reject_invalid_prices(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "invalid.csv"
            with path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["day", "rtoken_close", "stock_close"])
                for i in range(1, 7):
                    writer.writerow([f"Day {i}", -1 if i == 2 else 100, 100])
            with self.assertRaises(ValueError):
                load_prices(path)


if __name__ == "__main__":
    unittest.main()
