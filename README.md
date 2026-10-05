# rFactor Lab

**rFactor Lab** is a quantitative research platform for **Bitget Reality rTokens**. It helps users explore rToken markets, discover factor candidates, validate signals on independent data, backtest execution rules, study transaction-cost sensitivity, inspect live market data through the Bitget Agent Hub SDK, and generate research-ready insights.

> **Research only.** Historical results do not guarantee future performance.

---

## Project Highlights

- Explore a broad Reality rToken universe
- Filter assets by tradability, history, and data quality
- Discover and compare factor candidates
- Validate a frozen factor on independent validation data
- Test final time and asset holdouts
- Run historical backtests with turnover constraints
- Compare 0, 2.5, 5, and 10 bps hypothetical one-way transaction-cost scenarios
- Visualize cumulative equity and drawdown
- Inspect factor diagnostics with Factor Autopsy
- Access live Bitget rToken market data through the official Bitget Agent Hub SDK
- Ask research questions through the Research Copilot
- Generate a research report inside the application

---

## Selected Factor

The frozen selected factor is a **1-hour cross-sectional reversal signal**.

- Signal: previous 1-hour momentum
- Target: next 1-hour return
- Expected relationship: negative cross-sectional information coefficient
- Interpretation: relative losers over the previous hour tended to rank stronger over the following hour, while relative winners tended to rank weaker

The factor parameters were frozen before independent validation and holdout testing.

---

## Research Pipeline

The research workflow is:

```text
2,587 Reality pairs
        ↓
90 weekend-tradable pairs
        ↓
24 assets with at least 365 days of history
        ↓
23 data-quality eligible assets
        ↓
14 Development assets
        ↓
6 Validation assets
        ↓
3 Final Asset Holdout assets
```

The research also uses a final time holdout to test the factor on unseen future periods.

---

## Validation Results

The selected reversal factor showed negative IC in the independent validation and final holdout tests.

### Validation

- Mean IC: approximately **-0.035**
- Negative IC rate: approximately **52.9%**
- Result: **PASS**

### Final Time Holdout

- Mean IC: approximately **-0.071**
- Negative IC rate: approximately **59.2%**
- Result: **PASS**

### Final Asset + Time Holdout

- Mean IC: approximately **-0.081**
- Negative IC rate: approximately **55.1%**
- Result: **PASS**

The factor is therefore described as **validated in the historical sample**, not as a guarantee of future alpha.

---

## Historical Backtest

The frozen execution test uses:

- Long: bottom 25% of the cross-sectional 1-hour momentum ranking
- Short: top 25%
- Rebalance frequency: 1 hour
- Maximum hourly turnover: 0.50
- Cost scenarios: 0, 2.5, 5, and 10 bps one-way

### Final Time Holdout

| Cost | Return | Win Rate | Max Drawdown | Avg Turnover | Naive Sharpe |
|---|---:|---:|---:|---:|---:|
| 0 bps | +13.36% | 57.32% | -5.36% | 0.50 | 4.35 |
| 2.5 bps | -0.78% | 51.97% | -8.02% | 0.50 | -0.18 |
| 5 bps | -13.16% | — | -15.08% | 0.50 | -4.72 |
| 10 bps | -33.48% | — | -33.98% | 0.50 | -13.78 |

The key conclusion is:

> **The factor is statistically validated, but the implementation is highly sensitive to transaction costs.**

The transaction-cost values are hypothetical research scenarios and are **not Bitget fee claims**.

---

## Factor Autopsy

Factor Autopsy separates signal quality from implementation quality.

Main conclusion:

```text
Signal: VALIDATED
Execution: COST-SENSITIVE
```

The factor can have a measurable historical relationship with future returns while still being difficult to monetize after realistic trading frictions.

---

## Live Bitget Integration

The application includes read-only live rToken market data using the official **Bitget Agent Hub SDK**.

Architecture:

```text
React Frontend
      ↓
FastAPI Backend
      ↓
Node.js Bridge
      ↓
@bitget-ai/bitget-agent-sdk
      ↓
Bitget public SPOT market data
```

No trading or account credentials are required for the live ticker integration.

---

## Main Pages

### Overview
Shows the complete research pipeline and current project status.

### Token Explorer
Explore historical token data and compare selected assets. Also displays live Bitget rToken ticker information.

### Factor Explorer
Compare candidate factors and development-period results.

### Factor Validation
Shows independent validation and holdout statistics for the frozen factor.

### Backtest & Execution
Displays:
- cumulative equity
- drawdown
- transaction-cost sensitivity
- turnover-constrained execution
- validation, time-holdout, and asset-holdout backtests

### Factor Autopsy
Explains why signal validity and implementation profitability should be evaluated separately.

### Research Timeline
Shows the full research process from universe construction to final diagnostics.

### Research Copilot
Allows users to ask research questions and request live rToken market information.

### Research Report
Presents a browser-ready research report that can be printed or saved as PDF.

---

## Tech Stack

### Frontend
- React
- Vite
- Framer Motion
- Recharts
- Lucide React

### Backend
- FastAPI
- Python
- Node.js bridge
- Bitget Agent Hub SDK

### Research
- Python
- pandas
- NumPy
- SciPy / statistical analysis tools
- CSV / JSON research datasets

---

## Project Structure

```text
rfactor-lab/
├── backend/
│   ├── main.py
│   ├── bitget_bridge.mjs
│   └── ...
├── frontend/
│   ├── src/
│   ├── public/
│   └── ...
├── data/
├── export_factor_explorer.py
├── export_token_explorer.py
├── export_v2_turnover_cap_timeseries.py
├── validate_v2_turnover_cap.py
├── .gitignore
└── README.md
```

---

## Run Locally

### 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd rfactor-lab
```

### 2. Start the backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

The backend runs at:

```text
http://127.0.0.1:8000
```

### 3. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Then open the Vite URL shown in the terminal.

---

## Environment Variables

Create:

```text
backend/.env
```

Add the required local environment variables there.

**Do not commit `.env` files or API keys to GitHub.**

The repository `.gitignore` is configured to exclude secrets and dependency folders.

---

## Important Research Limitations

- Historical results do not guarantee future performance.
- Transaction costs are hypothetical one-way scenarios.
- Naive Sharpe is annualized from the observed hourly series and is not adjusted for serial dependence.
- The 3-asset holdout has coarse Spearman IC resolution.
- Historical candle availability should not automatically be interpreted as live-traded rToken history for all earlier periods.
- Execution experiments are separate from factor selection.
- No execution parameters were retuned after the validation and holdout results were observed.

---

## Research Philosophy

rFactor Lab is designed around one principle:

> **A signal can be statistically real and still be difficult to trade.**

The platform focuses on separating factor discovery, independent validation, holdout testing, execution design, and transaction-cost analysis so that research conclusions remain transparent.

---

## Disclaimer

This project is for educational, research, and hackathon demonstration purposes only. It does not provide financial advice, investment recommendations, or guarantees of future returns.
