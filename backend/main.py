import json
import re
import subprocess
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = Path(__file__).resolve().parent

RESEARCH_FILE = (
    PROJECT_ROOT
    / "frontend"
    / "public"
    / "data"
    / "research.json"
)

BITGET_BRIDGE = (
    BACKEND_DIR
    / "bitget_bridge.mjs"
)


# =========================================================
# LOAD RESEARCH DATA
# =========================================================

with open(
    RESEARCH_FILE,
    "r",
    encoding="utf-8",
) as file:
    research_data = json.load(file)


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="rFactor Lab Research Backend"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# REQUEST MODEL
# =========================================================

class ChatRequest(BaseModel):
    question: str


# =========================================================
# RTOKEN SYMBOLS
# =========================================================

RTOKEN_TICKERS = [
    "AAOI",
    "AAPL",
    "AMD",
    "COIN",
    "CRCL",
    "GLW",
    "GOOGL",
    "HOOD",
    "INTC",
    "LITE",
    "META",
    "MRVL",
    "MSFT",
    "MSTR",
    "NBIS",
    "NVDA",
    "ORCL",
    "QQQ",
    "RKLB",
    "SNDK",
    "TSLA",
    "TSM",
    "VOO",
]


# =========================================================
# DETECT RTOKEN FROM QUESTION
# =========================================================

def detect_rtoken_symbol(
    question: str,
):
    text = question.upper()


    # Example:
    # RNVDAUSDT

    direct_match = re.search(
        r"\bR[A-Z0-9]+USDT\b",
        text,
    )

    if direct_match:
        return direct_match.group(0)


    # Example:
    # rNVDA

    short_match = re.search(
        r"\bR([A-Z0-9]+)\b",
        text,
    )

    if short_match:
        ticker = short_match.group(1)

        if ticker in RTOKEN_TICKERS:
            return f"R{ticker}USDT"


    # Example:
    # NVDA

    for ticker in RTOKEN_TICKERS:

        if re.search(
            rf"\b{ticker}\b",
            text,
        ):

            return (
                f"R{ticker}USDT"
            )


    return None


# =========================================================
# FETCH LIVE BITGET MARKET DATA
# =========================================================

def fetch_live_bitget_ticker(
    symbol: str,
):

    symbol = (
        symbol
        .strip()
        .upper()
    )


    if not re.fullmatch(
        r"R[A-Z0-9]+USDT",
        symbol,
    ):

        raise ValueError(
            "Invalid rToken symbol. "
            "Example: RNVDAUSDT"
        )


    if not BITGET_BRIDGE.exists():

        raise RuntimeError(
            "Bitget bridge file "
            "not found."
        )


    try:

        process = subprocess.run(
            [
                "node",
                str(
                    BITGET_BRIDGE
                ),
                symbol,
            ],
            cwd=str(
                BACKEND_DIR
            ),
            capture_output=True,
            text=True,
            timeout=20,
        )


    except subprocess.TimeoutExpired:

        raise RuntimeError(
            "Bitget request timed out."
        )


    # -----------------------------------------------------
    # NODE / BITGET ERROR
    # -----------------------------------------------------

    if process.returncode != 0:

        error_message = (
            process.stderr.strip()
            or
            process.stdout.strip()
            or
            "Unknown Bitget bridge error."
        )


        try:

            error_data = json.loads(
                error_message
            )

            error_message = (
                error_data.get(
                    "error",
                    error_message,
                )
            )


        except json.JSONDecodeError:

            pass


        raise RuntimeError(
            error_message
        )


    # -----------------------------------------------------
    # PARSE JSON
    # -----------------------------------------------------

    try:

        payload = json.loads(
            process.stdout
        )


    except json.JSONDecodeError:

        raise RuntimeError(
            "Bitget bridge returned "
            "invalid JSON."
        )


    result = payload.get(
        "result",
        {},
    )


    market_data = result.get(
        "data",
        [],
    )


    if not market_data:

        raise RuntimeError(
            f"No Bitget market data "
            f"found for {symbol}."
        )


    ticker = market_data[0]


    return {

        "connected":
            True,

        "integration":
            payload.get(
                "integration",
                "Bitget Agent Hub",
            ),

        "sdk":
            payload.get(
                "sdk",
                "@bitget-ai/bitget-agent-sdk",
            ),

        "mode":
            payload.get(
                "mode",
                "READ_ONLY",
            ),

        "symbol":
            symbol,

        "endpoint":
            result.get(
                "endpoint"
            ),

        "requestTime":
            result.get(
                "requestTime"
            ),

        "market": {

            "lastPrice":
                ticker.get(
                    "lastPrice"
                ),

            "openPrice24h":
                ticker.get(
                    "openPrice24h"
                ),

            "highPrice24h":
                ticker.get(
                    "highPrice24h"
                ),

            "lowPrice24h":
                ticker.get(
                    "lowPrice24h"
                ),

            "bid1Price":
                ticker.get(
                    "bid1Price"
                ),

            "ask1Price":
                ticker.get(
                    "ask1Price"
                ),

            "price24hPcnt":
                ticker.get(
                    "price24hPcnt"
                ),

            "volume24h":
                ticker.get(
                    "volume24h"
                ),

            "turnover24h":
                ticker.get(
                    "turnover24h"
                ),

            "platformTurnover24h":
                ticker.get(
                    "platformTurnover24h"
                ),

            "timestamp":
                ticker.get(
                    "ts"
                ),
        },
    }


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {

        "status":
            "online",

        "service":
            "rFactor Lab Research Backend",
    }


# =========================================================
# BITGET LIVE TICKER ENDPOINT
# =========================================================

@app.get(
    "/bitget/ticker/{symbol}"
)
def get_bitget_ticker(
    symbol: str,
):

    try:

        return fetch_live_bitget_ticker(
            symbol
        )


    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


    except RuntimeError as exc:

        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )


# =========================================================
# LOCAL RESEARCH COPILOT
# =========================================================

def local_fallback_answer(
    question: str,
):

    q = question.lower()


    validation = {

        item["stage"]:
            item

        for item
        in research_data[
            "validation"
        ]
    }


    execution = (
        research_data[
            "execution"
        ]
    )


    def get_execution(
        test,
        cost,
    ):

        for item in execution:

            if (
                item["test"] == test
                and
                float(
                    item["costBps"]
                )
                ==
                float(cost)
            ):

                return item


        return None


    # -----------------------------------------------------
    # FACTOR
    # -----------------------------------------------------

    if (
        "factor" in q
        or
        "discover" in q
        or
        "signal" in q
    ):

        dev = validation[
            "Development"
        ]


        return (
            "rFactor Lab discovered a "
            "1-hour cross-sectional reversal factor. "
            "Recent relative winners tended to rank "
            "weaker during the next hour, while recent "
            "relative losers tended to recover. "
            f"The Development mean IC was "
            f"{dev['meanIC']:.4f}."
        )


    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if (
        "validation" in q
        or
        "validate" in q
        or
        "survive" in q
    ):

        dev = validation[
            "Development"
        ]

        val = validation[
            "Validation"
        ]

        time = validation[
            "FinalTimeHoldout"
        ]

        asset = validation[
            "FinalAssetHoldout"
        ]


        return (
            "Yes. The expected negative relationship "
            "survived every research stage. "
            f"Development mean IC was "
            f"{dev['meanIC']:.4f}, "
            f"Validation was "
            f"{val['meanIC']:.4f}, "
            f"Final Time Holdout was "
            f"{time['meanIC']:.4f}, "
            f"and Final Asset Holdout was "
            f"{asset['meanIC']:.4f}."
        )


    # -----------------------------------------------------
    # TRANSACTION COST
    # -----------------------------------------------------

    if (
        "cost" in q
        or
        "transaction" in q
        or
        "friction" in q
        or
        "expensive" in q
    ):

        gross = get_execution(
            "FinalTime20",
            0,
        )

        cost = get_execution(
            "FinalTime20",
            2.5,
        )


        return (
            "The main economic limitation is "
            "transaction-cost sensitivity. "
            f"In the Final Time Holdout the portfolio "
            f"returned {gross['returnPct']:.2f}% "
            f"at 0 bps, but "
            f"{cost['returnPct']:.2f}% using a "
            "hypothetical 2.5 bps one-way "
            "transaction cost. "
            "Frequent hourly repositioning consumes "
            "much of the statistical edge."
        )


    # -----------------------------------------------------
    # HOLDOUT
    # -----------------------------------------------------

    if (
        "holdout" in q
        or
        "final test" in q
    ):

        time = validation[
            "FinalTimeHoldout"
        ]

        asset = validation[
            "FinalAssetHoldout"
        ]


        return (
            f"The Final Time Holdout had "
            f"{time['timestamps']} IC timestamps "
            f"and a mean IC of "
            f"{time['meanIC']:.4f}. "
            f"The separate Asset Holdout produced "
            f"a mean IC of "
            f"{asset['meanIC']:.4f}."
        )


    # -----------------------------------------------------
    # IC
    # -----------------------------------------------------

    if (
        "information coefficient"
        in q
        or
        " ic "
        in f" {q} "
        or
        q.startswith("ic")
    ):

        time = validation[
            "FinalTimeHoldout"
        ]


        return (
            "IC means Information Coefficient. "
            "It measures the relationship between "
            "factor rankings and future return rankings. "
            "For this reversal factor, a negative IC "
            "is expected. "
            f"The Final Time Holdout mean IC was "
            f"{time['meanIC']:.4f}."
        )


    # -----------------------------------------------------
    # PROFIT
    # -----------------------------------------------------

    if (
        "profit" in q
        or
        "profitable" in q
        or
        "return" in q
    ):

        gross = get_execution(
            "FinalTime20",
            0,
        )

        cost = get_execution(
            "FinalTime20",
            2.5,
        )


        return (
            "Gross historical performance was positive, "
            "but net economic performance was not robust "
            "to transaction costs. "
            f"The Final Time Holdout returned "
            f"{gross['returnPct']:.2f}% at 0 bps and "
            f"{cost['returnPct']:.2f}% under the "
            "hypothetical 2.5 bps cost assumption. "
            "Therefore the project separates factor "
            "validity from trading profitability."
        )


    # -----------------------------------------------------
    # LIMITATION
    # -----------------------------------------------------

    if (
        "weakness" in q
        or
        "limitation" in q
        or
        "problem" in q
    ):

        return (
            "The main limitation is economic "
            "implementation. "
            "The factor remained statistically stable, "
            "but the hourly portfolio requires "
            "substantial turnover. "
            "This makes the implementation sensitive "
            "to transaction costs."
        )


    # -----------------------------------------------------
    # DEFAULT
    # -----------------------------------------------------

    return (
        "The main rFactor Lab conclusion is that the "
        "1-hour cross-sectional reversal factor was "
        "statistically validated across independent "
        "tests, while the current portfolio "
        "implementation remains sensitive to turnover "
        "and transaction costs. "
        "You can ask about the factor, validation, "
        "holdouts, IC, transaction costs, limitations, "
        "or live rToken market data."
    )


# =========================================================
# CHAT ENDPOINT
# =========================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
):

    question = (
        request.question.strip()
    )


    if not question:

        return {

            "answer":
                "Please enter a question.",

            "mode":
                "local-fallback",
        }


    symbol = detect_rtoken_symbol(
        question
    )


    live_keywords = [
        "live",
        "current",
        "price",
        "24h",
        "24 hour",
        "bid",
        "ask",
        "market",
        "bitget",
    ]


    wants_live_data = any(

        keyword
        in question.lower()

        for keyword
        in live_keywords
    )


    # -----------------------------------------------------
    # LIVE BITGET QUESTION
    # -----------------------------------------------------

    if (
        symbol
        and
        wants_live_data
    ):

        try:

            live = (
                fetch_live_bitget_ticker(
                    symbol
                )
            )


            market = live[
                "market"
            ]


            change = (
                float(
                    market.get(
                        "price24hPcnt"
                    )
                    or 0
                )
                * 100
            )


            answer = (
                f"Live Bitget market data for "
                f"{live['symbol']}:\n\n"

                f"• Last price: "
                f"{market.get('lastPrice')}\n"

                f"• 24H change: "
                f"{change:+.2f}%\n"

                f"• 24H high: "
                f"{market.get('highPrice24h')}\n"

                f"• 24H low: "
                f"{market.get('lowPrice24h')}\n"

                f"• Best bid: "
                f"{market.get('bid1Price')}\n"

                f"• Best ask: "
                f"{market.get('ask1Price')}\n"

                f"• 24H volume: "
                f"{market.get('volume24h')}\n\n"

                f"Source: "
                f"{live['integration']} "
                f"({live['mode']} market data)."
            )


            return {

                "answer":
                    answer,

                "mode":
                    "bitget-agent-hub",

                "symbol":
                    symbol,
            }


        except Exception as exc:

            return {

                "answer":
                    (
                        "I detected this as a live "
                        "rToken market question, but "
                        "the Bitget request failed: "
                        f"{str(exc)}"
                    ),

                "mode":
                    "bitget-error",
            }


    # -----------------------------------------------------
    # NORMAL RESEARCH QUESTION
    # -----------------------------------------------------

    return {

        "answer":
            local_fallback_answer(
                question
            ),

        "mode":
            "local-fallback",
    }