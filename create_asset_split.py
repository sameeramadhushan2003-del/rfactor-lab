import pandas as pd
import numpy as np
from pathlib import Path


# -----------------------------------------
# SETTINGS
# -----------------------------------------

INPUT_FILE = Path(
    "data/weekend_universe_coverage.csv"
)

OUTPUT_FILE = Path(
    "data/research_asset_split.csv"
)

RANDOM_SEED = 42


print("====================================")
print("rFactor Lab")
print("Frozen Research Asset Split")
print("====================================")


# -----------------------------------------
# LOAD ELIGIBLE ASSETS
# -----------------------------------------

df = pd.read_csv(
    INPUT_FILE
)


eligible = df[
    df["research_eligible"]
    .astype(str)
    .str.lower()
    .eq("true")
].copy()


eligible = eligible[
    [
        "rtoken_symbol",
        "native_ticker",
        "candles",
        "coverage_pct",
        "weekend_candles"
    ]
]


eligible = eligible.sort_values(
    "native_ticker"
).reset_index(drop=True)


print(
    "\nEligible assets:",
    len(eligible)
)


# -----------------------------------------
# FIXED RANDOM SHUFFLE
# -----------------------------------------

rng = np.random.default_rng(
    RANDOM_SEED
)


indices = np.arange(
    len(eligible)
)


rng.shuffle(
    indices
)


eligible = (
    eligible
    .iloc[indices]
    .reset_index(drop=True)
)


# -----------------------------------------
# 60 / 20 / 20 SPLIT
# -----------------------------------------

n = len(eligible)

development_n = round(
    n * 0.60
)

validation_n = round(
    n * 0.20
)

holdout_n = (
    n
    - development_n
    - validation_n
)


eligible["research_group"] = ""


eligible.loc[
    :development_n - 1,
    "research_group"
] = "Development"


eligible.loc[
    development_n:
    development_n + validation_n - 1,
    "research_group"
] = "Validation"


eligible.loc[
    development_n + validation_n:,
    "research_group"
] = "Holdout"


# -----------------------------------------
# LOCK INFORMATION
# -----------------------------------------

eligible["split_seed"] = (
    RANDOM_SEED
)

eligible["split_frozen"] = True


# -----------------------------------------
# DISPLAY
# -----------------------------------------

print("\nSplit sizes:")

print(
    eligible[
        "research_group"
    ].value_counts()
)


for group in [
    "Development",
    "Validation",
    "Holdout"
]:

    print(
        f"\n{group.upper()}"
    )

    subset = eligible[
        eligible[
            "research_group"
        ] == group
    ]

    print(
        subset[
            [
                "rtoken_symbol",
                "native_ticker",
                "coverage_pct",
                "weekend_candles"
            ]
        ]
        .sort_values(
            "native_ticker"
        )
        .round(2)
        .to_string(
            index=False
        )
    )


# -----------------------------------------
# SAVE
# -----------------------------------------

eligible.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n====================================")
print("SPLIT FROZEN")
print("====================================")

print(
    "Development:",
    development_n
)

print(
    "Validation:",
    validation_n
)

print(
    "Holdout:",
    holdout_n
)

print(
    "Random seed:",
    RANDOM_SEED
)

print(
    "Saved to:",
    OUTPUT_FILE
)

print(
    "\nDo NOT move assets between groups "
    "after strategy results are observed."
)