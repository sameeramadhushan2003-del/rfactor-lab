import pandas as pd
from pathlib import Path


# =========================================================
# SETTINGS
# =========================================================

INPUT_FILE = Path(
    "data/available_history_report.csv"
)

OUTPUT_FILE = Path(
    "data/long_history_universe.csv"
)

MIN_HISTORY_DAYS = 365


print("====================================")
print("rFactor Lab")
print("Long-History Universe")
print("====================================")


# =========================================================
# LOAD HISTORY REPORT
# =========================================================

df = pd.read_csv(
    INPUT_FILE
)


df["history_days"] = pd.to_numeric(
    df["history_days"],
    errors="coerce"
)


# =========================================================
# OBJECTIVE HISTORY FILTER
# =========================================================

eligible = df[
    (
        df["status"] == "ok"
    )
    &
    (
        df["history_days"]
        >= MIN_HISTORY_DAYS
    )
].copy()


eligible = eligible.sort_values(
    "native_ticker"
).reset_index(drop=True)


eligible[
    "long_history_eligible"
] = True


# =========================================================
# SAVE
# =========================================================

eligible.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# DISPLAY
# =========================================================

print(
    "\nMinimum history required:",
    MIN_HISTORY_DAYS,
    "days"
)

print(
    "Eligible assets:",
    len(eligible)
)


print(
    "\n365-day research universe:\n"
)


print(
    eligible[
        [
            "rtoken_symbol",
            "native_ticker",
            "history_days",
            "research_group"
        ]
    ]
    .round(2)
    .to_string(index=False)
)


print("\n====================================")
print("LONG-HISTORY UNIVERSE FROZEN")
print("====================================")

print(
    "Saved to:",
    OUTPUT_FILE
)

print(
    "\nNo strategy performance "
    "was used for this filter."
)