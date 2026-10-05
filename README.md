# rToken FactorLab AI — Milestone 1

An offline educational prototype that compares *historical descriptive factors* for illustrative rToken and underlying-stock prices. No account, API key, funds, external libraries, or live orders are used.

## Run

1. Install Python 3.10+ from the official Python website, if it is not already installed.
2. Open this folder in VS Code or a terminal.
3. Run `python analyze.py` (on some systems use `python3 analyze.py`).
4. Read the printed table and generated `sample_report.json`.
5. Run tests: `python -m unittest discover -s tests -v`.

## Data

`sample_prices.csv` contains **made-up example prices** labeled Day 01–Day 14. These are not Bitget observations, historical prices, predictions, evidence of profitability, or competition-valid backtesting results.

`analyze.py` calculates 3-observation price momentum (`current / price_3_observations_ago - 1`) and sample standard deviation of the last 3 simple returns. There is no signal generation or simulation of transactions.

## Next research milestone

Find authorized read-only historical rToken data and an appropriately sourced underlying-stock dataset, verify timestamps/quote currencies/market hours/volume availability, then replace the sample dataset with clearly labeled real observations. Do not report synthetic observations as real market performance. The competition's historical-testing requirements cannot be satisfied with this example dataset.
