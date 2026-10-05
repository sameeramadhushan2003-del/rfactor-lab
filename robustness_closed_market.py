import pandas as pd
import numpy as np
from pathlib import Path


# =========================================================
# SETTINGS
# =========================================================

INPUT_FILE = Path(
    "data/multi_asset_closed_market_development.csv"
)

OUTPUT_FILE = Path(
    "data/closed_market_weekend_clusters.csv"
)


print("====================================")
print("rFactor Lab")
print("Closed-Market Robustness Test")
print("====================================")


# =========================================================
# LOAD DATA
# =========================================================

df = pd.read_csv(INPUT_FILE)


df["closure_start_et"] = pd.to_datetime(
    df["closure_start_et"],
    utc=True
)

df["reopen_et"] = pd.to_datetime(
    df["reopen_et"],
    utc=True
)


numeric_columns = [
    "rtoken_closed_return_pct",
    "native_reopen_gap_pct",
    "tracking_difference_pct",
    "rtoken_coverage_pct"
]


for column in numeric_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# =========================================================
# CREATE WEEKEND / EVENT DATE
# =========================================================

df["closure_start_et"] = (
    df["closure_start_et"]
    .dt.tz_convert(
        "America/New_York"
    )
)


df["event_date"] = (
    df["closure_start_et"]
    .dt.date
)


print("\n1. RAW DEVELOPMENT EVENTS")

print(
    "Asset-event observations:",
    len(df)
)

print(
    "Unique closure dates:",
    df["event_date"].nunique()
)


# =========================================================
# CLUSTER EACH WEEKEND
# =========================================================

def summarize_weekend(group):

    avg_rtoken = (
        group[
            "rtoken_closed_return_pct"
        ].mean()
    )

    avg_native = (
        group[
            "native_reopen_gap_pct"
        ].mean()
    )


    same_direction = (
        np.sign(avg_rtoken)
        ==
        np.sign(avg_native)
    )


    return pd.Series(
        {
            "assets":
            ",".join(
                sorted(
                    group["ticker"]
                    .unique()
                )
            ),

            "asset_count":
            len(group),

            "avg_rtoken_return_pct":
            avg_rtoken,

            "avg_native_gap_pct":
            avg_native,

            "median_rtoken_return_pct":
            group[
                "rtoken_closed_return_pct"
            ].median(),

            "median_native_gap_pct":
            group[
                "native_reopen_gap_pct"
            ].median(),

            "avg_abs_tracking_difference_pct":
            group[
                "tracking_difference_pct"
            ].abs().mean(),

            "asset_direction_agreement_pct":
            group[
                "same_direction"
            ].mean() * 100,

            "cluster_same_direction":
            same_direction
        }
    )


clusters = (
    df.groupby(
        "event_date"
    )
    .apply(
        summarize_weekend,
        include_groups=False
    )
    .reset_index()
)


# =========================================================
# SHOW WEEKEND RESULTS
# =========================================================

print("\n2. WEEKEND-LEVEL RESULTS\n")


print(
    clusters.round(4)
    .to_string(
        index=False
    )
)


# =========================================================
# WEEKEND-LEVEL DIRECTION AGREEMENT
# =========================================================

cluster_direction_agreement = (
    clusters[
        "cluster_same_direction"
    ].mean()
    * 100
)


print(
    "\n3. WEEKEND-LEVEL DIRECTION AGREEMENT"
)

print(
    "Agreement:",
    round(
        cluster_direction_agreement,
        2
    ),
    "%"
)


# =========================================================
# WEEKEND-LEVEL CORRELATION
# =========================================================

cluster_correlation = (
    clusters[
        "avg_rtoken_return_pct"
    ]
    .corr(
        clusters[
            "avg_native_gap_pct"
        ]
    )
)


print(
    "\n4. WEEKEND-LEVEL CORRELATION"
)

print(
    "Correlation:",
    round(
        cluster_correlation,
        4
    )
)


# =========================================================
# LEAVE-ONE-WEEKEND-OUT TEST
# =========================================================

print(
    "\n5. LEAVE-ONE-WEEKEND-OUT CORRELATION\n"
)


loo_results = []


for event_date in clusters["event_date"]:

    subset = clusters[
        clusters["event_date"]
        != event_date
    ]


    correlation = (
        subset[
            "avg_rtoken_return_pct"
        ]
        .corr(
            subset[
                "avg_native_gap_pct"
            ]
        )
    )


    loo_results.append(
        correlation
    )


    print(
        "Removed:",
        event_date,
        "| Correlation:",
        round(
            correlation,
            4
        )
    )


print(
    "\nLOO minimum correlation:",
    round(
        np.nanmin(
            loo_results
        ),
        4
    )
)

print(
    "LOO maximum correlation:",
    round(
        np.nanmax(
            loo_results
        ),
        4
    )
)


# =========================================================
# BOOTSTRAP BY WEEKEND
# =========================================================

print(
    "\n6. WEEKEND-CLUSTER BOOTSTRAP"
)


rng = np.random.default_rng(
    42
)

bootstrap_correlations = []

n_clusters = len(
    clusters
)


for _ in range(5000):

    sample_indexes = (
        rng.integers(
            0,
            n_clusters,
            n_clusters
        )
    )


    sample = clusters.iloc[
        sample_indexes
    ]


    # Need variation in both variables
    if (
        sample[
            "avg_rtoken_return_pct"
        ].nunique()
        < 2
    ):

        continue


    if (
        sample[
            "avg_native_gap_pct"
        ].nunique()
        < 2
    ):

        continue


    correlation = (
        sample[
            "avg_rtoken_return_pct"
        ]
        .corr(
            sample[
                "avg_native_gap_pct"
            ]
        )
    )


    if not np.isnan(
        correlation
    ):

        bootstrap_correlations.append(
            correlation
        )


bootstrap_correlations = np.array(
    bootstrap_correlations
)


if len(
    bootstrap_correlations
) > 0:

    lower = np.percentile(
        bootstrap_correlations,
        2.5
    )

    upper = np.percentile(
        bootstrap_correlations,
        97.5
    )


    print(
        "Bootstrap samples:",
        len(
            bootstrap_correlations
        )
    )

    print(
        "Approx. 95% correlation interval:",
        round(
            lower,
            4
        ),
        "to",
        round(
            upper,
            4
        )
    )


# =========================================================
# SAVE
# =========================================================

clusters.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n====================================")
print("ROBUSTNESS TEST COMPLETE")
print("====================================")

print(
    "Saved to:",
    OUTPUT_FILE
)

print(
    "Out-of-sample data was NOT used."
)