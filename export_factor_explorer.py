import json
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "v2_development_factor_candidates.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "frontend"
    / "public"
    / "data"
    / "factors.json"
)


df = pd.read_csv(INPUT_FILE)


records = []

for _, row in df.iterrows():

    records.append({
        "factor": row["factor"],
        "target": row["target"],

        "timestamps": int(row["timestamps"]),

        "meanIC": float(row["mean_ic"]),
        "medianIC": float(row["median_ic"]),
        "stdIC": float(row["std_ic"]),

        "positiveICPct": float(
            row["positive_ic_pct"]
        ),

        "naiveTStat": float(
            row["naive_t_stat"]
        ),

        "folds": [
            float(row["Fold_1"]),
            float(row["Fold_2"]),
            float(row["Fold_3"]),
            float(row["Fold_4"]),
        ],

        "passesStability": bool(
            row["passes_stability"]
        ),
    })


output = {
    "totalCandidates": len(records),

    "factors": sorted(
        df["factor"]
        .dropna()
        .unique()
        .tolist()
    ),

    "targets": sorted(
        df["target"]
        .dropna()
        .unique()
        .tolist()
    ),

    "candidates": records,
}


OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        output,
        file,
        indent=2
    )


print(
    f"Exported {len(records)} factor candidates"
)

print(
    f"Saved to: {OUTPUT_FILE}"
)