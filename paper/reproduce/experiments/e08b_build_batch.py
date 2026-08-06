"""e08b — Batched gold-annotation sheets (start small, stack later).

Instead of one 450-report sheet, produce a small first batch to test whether the
task and definitions work, then stack more only if needed. Each batch is a
blinded, stratified, reproducible draw that does NOT overlap previous batches
(tracked by a persisted "already sampled" list).

Batch 1 default = 80 reports, weighted toward the high-risk disagreement cells
but still touching all four so sensitivity/specificity can be estimated:
  Neg/Pos (suspected false neg) : 30
  Pos/Neg (suspected false pos) : 25
  Neg/Neg (both Negative)       : 15   (blind-spot check)
  Pos/Pos (both Positive)       : 10
                                  ----
                                    80

Outputs (per batch N):
  outputs/e08_batchN_BLIND.csv   -> clinicians (no automated labels)
  outputs/e08_batchN_KEY.csv     -> hidden, for scoring
State:
  outputs/e08_sampled_note_ids.txt  -> accumulates across batches (no overlap)

Usage (from repo root):
  python paper/reproduce/experiments/e08b_build_batch.py            # batch 1, 80
  python paper/reproduce/experiments/e08b_build_batch.py 2 100      # batch 2, +100
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import REPO_ROOT, OUTPUT_DIR

VR = OUTPUT_DIR / "e05_llm_vs_regex.csv"
REPORTS = REPO_ROOT / "extracted" / "team2-ZZZ Lab" / "mimitc-ct-head-example.csv"
SAMPLED = OUTPUT_DIR / "e08_sampled_note_ids.txt"
SEED = 42

# batch size -> per-cell counts (scaled from the 30/25/15/10 template)
DEFAULT_BATCH1 = {("Negative", "Positive"): 30, ("Positive", "Negative"): 25,
                  ("Negative", "Negative"): 15, ("Positive", "Positive"): 10}


def extract_impression(text: str) -> str:
    m = re.search(r"(?i)IMPRESSION[:\s]*([\s\S]+)", text)
    imp = (m.group(1) if m else text).strip()
    return re.sub(r"\s+", " ", imp)[:600]


def plan_for(total):
    if total == 80:
        return DEFAULT_BATCH1
    # scale the template proportionally for other batch sizes
    base = DEFAULT_BATCH1
    s = sum(base.values())
    return {k: max(1, round(v * total / s)) for k, v in base.items()}


def main():
    batch = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    total = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    plan = plan_for(total)

    vr = pd.read_csv(VR)
    reports = pd.read_csv(REPORTS)[["note_id", "text"]].drop_duplicates("note_id")
    vr = vr.merge(reports, on="note_id", how="left")

    already = set()
    if SAMPLED.exists():
        already = set(SAMPLED.read_text().split())
    vr = vr[~vr["note_id"].astype(str).isin(already)]

    picks = []
    for (rgx, llm), n in plan.items():
        cell = vr[(vr["regex_label"] == rgx) & (vr["llm_label"] == llm)]
        take = min(n, len(cell))
        if take < n:
            print(f"  note: cell {rgx}/{llm} has {len(cell)} left; taking {take}")
        if take:
            picks.append(cell.sample(take, random_state=SEED + batch))
    sample = pd.concat(picks).sample(frac=1, random_state=SEED + batch).reset_index(drop=True)
    sample.insert(0, "review_id", [f"B{batch}-{i:03d}" for i in range(1, len(sample) + 1)])

    blind = pd.DataFrame({
        "review_id": sample["review_id"],
        "IMPRESSION": sample["text"].apply(extract_impression),
        "TRUE_LABEL (Positive/Negative)": "",
        "finding_type (acute/chronic-stable/post-surgical/none)": "",
        "confidence (high/low)": "",
        "notes": "",
    })
    key = pd.DataFrame({
        "review_id": sample["review_id"], "note_id": sample["note_id"],
        "regex_label": sample["regex_label"], "llm_label": sample["llm_label"],
        "stratum": sample["regex_label"].str[:3] + "/" + sample["llm_label"].str[:3],
    })
    blind.to_csv(OUTPUT_DIR / f"e08_batch{batch}_BLIND.csv", index=False)
    key.to_csv(OUTPUT_DIR / f"e08_batch{batch}_KEY.csv", index=False)

    # update sampled state
    new_ids = already | set(sample["note_id"].astype(str))
    SAMPLED.write_text("\n".join(sorted(new_ids)))

    print(f"Batch {batch}: {len(sample)} reports (cumulative sampled: {len(new_ids)}).")
    print(key["stratum"].value_counts().to_string())
    print(f"\nGive to clinicians: e08_batch{batch}_BLIND.csv")
    print(f"Keep hidden:        e08_batch{batch}_KEY.csv")
    print("\nProcess: annotate blind -> we compute agreement + regex sens/spec on")
    print("this batch. If estimates are stable, stop; else run the next batch to stack.")


if __name__ == "__main__":
    main()
