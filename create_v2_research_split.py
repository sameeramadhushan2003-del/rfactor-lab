import pandas as pd
import numpy as np
from pathlib import Path


# =========================================================
# SETTINGS
# =========================================================

QUALITY_FILE = Path(
    "data/v2_final_quality.csv"
)

OLD_SPLIT_FILE = Path(
    "data/research_asset_split.csv"
)

OUTPUT_FILE = Path(
    "data/v2_research_split.csv"
)

RANDOM_SEED = 42


# We already inspected strategy results
# for these assets in Research Cycle V1.

LEGACY_OBSERVED = {
    "AAPL",
    "TSLA"
}


print("====================================")
print("rFactor Lab")
print("V2 Frozen Research Split")
print("====================================")


# =========================================================
# LOAD V2 ELIGIBLE UNIVERSE
# =========================================================

quality = pd.read_csv(
    QUALITY_FILE
)


quality[
    "general_factor_eligible"
] = (
    quality[
        "general_factor_eligible"
    ]
    .astype(str)
    .str.lower()
    .eq("true")
)


eligible = quality[
    quality[
        "general_factor_eligible"
    ]
].copy()


print(
    "\nV2 eligible assets:",
    len(eligible)
)


# =========================================================
# LOAD OLD V1 SPLIT
# =========================================================

old_split = pd.read_csv(
    OLD_SPLIT_FILE
)


old_groups = old_split[
    [
        "native_ticker",
        "research_group"
    ]
].rename(
    columns={
        "research_group":
        "v1_group"
    }
)


eligible = eligible.merge(
    old_groups,
    on="native_ticker",
    how="left"
)


# =========================================================
# LEGACY OBSERVATION FLAG
# =========================================================

eligible[
    "legacy_strategy_observed"
] = (
    eligible[
        "native_ticker"
    ].isin(
        LEGACY_OBSERVED
    )
)


# =========================================================
# CLEAN FINAL ASSET HOLDOUT
#
# Must:
# 1. Have been V1 Holdout
# 2. Be V2 quality eligible
# 3. Never have had strategy results inspected
# =========================================================

clean_holdout = eligible[
    (
        eligible[
            "v1_group"
        ]
        == "Holdout"
    )
    &
    (
        ~eligible[
            "legacy_strategy_observed"
        ]
    )
].copy()


print(
    "\nClean holdout assets:"
)

print(
    clean_holdout[
        "native_ticker"
    ]
    .sort_values()
    .tolist()
)


# =========================================================
# REMAINING RESEARCH POOL
# =========================================================

holdout_tickers = set(
    clean_holdout[
        "native_ticker"
    ]
)


research_pool = eligible[
    ~eligible[
        "native_ticker"
    ].isin(
        holdout_tickers
    )
].copy()


research_pool = (
    research_pool
    .sort_values(
        "native_ticker"
    )
    .reset_index(
        drop=True
    )
)


print(
    "\nResearch pool:",
    len(research_pool)
)


# =========================================================
# FIXED RANDOM DEVELOPMENT / VALIDATION SPLIT
# =========================================================

rng = np.random.default_rng(
    RANDOM_SEED
)


indexes = np.arange(
    len(research_pool)
)


rng.shuffle(
    indexes
)


research_pool = (
    research_pool
    .iloc[indexes]
    .reset_index(
        drop=True
    )
)


# 20 research assets:
# 14 Development
# 6 Validation

DEVELOPMENT_COUNT = 14


research_pool[
    "v2_group"
] = "Validation"


research_pool.loc[
    :DEVELOPMENT_COUNT - 1,
    "v2_group"
] = "Development"


# =========================================================
# LABEL HOLDOUT
# =========================================================

clean_holdout[
    "v2_group"
] = "AssetHoldout"


# =========================================================
# COMBINE
# =========================================================

final = pd.concat(
    [
        research_pool,
        clean_holdout
    ],
    ignore_index=True
)


final[
    "split_seed"
] = RANDOM_SEED


final[
    "split_frozen"
] = True


# =========================================================
# SAVE
# =========================================================

final.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# DISPLAY
# =========================================================

print("\n====================================")
print("V2 SPLIT SIZES")
print("====================================")


print(
    final[
        "v2_group"
    ].value_counts()
)


for group in [
    "Development",
    "Validation",
    "AssetHoldout"
]:

    print(
        f"\n{group.upper()}"
    )

    subset = final[
        final[
            "v2_group"
        ]
        == group
    ]


    print(
        subset[
            [
                "native_ticker",
                "rtoken_symbol",
                "corrected_coverage_pct",
                "legacy_strategy_observed"
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


print("\n====================================")
print("V2 SPLIT FROZEN")
print("====================================")


print(
    "Development:",
    (
        final[
            "v2_group"
        ]
        == "Development"
    ).sum()
)


print(
    "Validation:",
    (
        final[
            "v2_group"
        ]
        == "Validation"
    ).sum()
)


print(
    "Final Asset Holdout:",
    (
        final[
            "v2_group"
        ]
        == "AssetHoldout"
    ).sum()
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
    "\nIMPORTANT:"
)

print(
    "Do not move assets between "
    "groups after factor results "
    "are observed."
)