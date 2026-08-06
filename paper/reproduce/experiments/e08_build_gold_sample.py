"""e08 — Build the 450-report stratified, blinded gold-standard annotation sheet.

Draws a stratified random sample across all four LLM-vs-regex cells so the
clinician gold set can measure the regex labeler's true sensitivity/specificity
(NOT just review disagreements). Reports are BLINDED (regex/LLM labels removed)
and SHUFFLED so the annotator is not primed. A hidden key file maps rows back to
their automated labels for scoring after annotation.

Sampling plan (of 7,671 comparable reports):
  Neg/Pos (suspected false neg) : 654 total -> sample 150   (highest-risk)
  Pos/Neg (suspected false pos) : 965 total -> sample 150
  Neg/Neg (both Negative)       : 4587 total -> sample 100   (co-blind-spot check)
  Pos/Pos (both Positive)       : 1465 total -> sample  50   (shared false-pos check)
                                                 --------
                                                    450

Outputs:
  outputs/e08_gold_sample_BLIND.csv   -> give to clinicians (no automated labels)
  outputs/e08_gold_sample_KEY.csv     -> hidden; maps note_id -> regex/LLM cell

Determinism: fixed random_state so the sample is reproducible.

Run from repo root:  python paper/reproduce/experiments/e08_build_gold_sample.py
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import REPO_ROOT, OUTPUT_DIR

VR = OUTPUT_DIR / "e05_llm_vs_regex.csv"
REPORTS = REPO_ROOT / "extracted" / "team2-ZZZ Lab" / "mimitc-ct-head-example.csv"
BLIND = OUTPUT_DIR / "e08_gold_sample_BLIND.csv"
KEY = OUTPUT_DIR / "e08_gold_sample_KEY.csv"

SEED = 42
PLAN = {  # (regex, llm) -> n to sample
    ("Negative", "Positive"): 150,
    ("Positive", "Negative"): 150,
    ("Negative", "Negative"): 100,
    ("Positive", "Positive"): 50,
}


def extract_impression(text: str) -> str:
    m = re.search(r"(?i)IMPRESSION[:\s]*([\s\S]+)", text)
    imp = (m.group(1) if m else text).strip()
    return re.sub(r"\s+", " ", imp)[:600]


def main():
    vr = pd.read_csv(VR)
    reports = pd.read_csv(REPORTS)[["note_id", "text"]].drop_duplicates("note_id")
    vr = vr.merge(reports, on="note_id", how="left")

    picks = []
    for (rgx, llm), n in PLAN.items():
        cell = vr[(vr["regex_label"] == rgx) & (vr["llm_label"] == llm)]
        take = min(n, len(cell))
        if take < n:
            print(f"  WARNING: cell {rgx}/{llm} has only {len(cell)} < {n}; taking {take}")
        picks.append(cell.sample(take, random_state=SEED))
    sample = pd.concat(picks).sample(frac=1, random_state=SEED).reset_index(drop=True)
    sample.insert(0, "review_id", [f"R{ i:03d}" for i in range(1, len(sample) + 1)])

    # BLIND sheet for clinicians — no automated labels, only the report + blanks.
    blind = pd.DataFrame({
        "review_id": sample["review_id"],
        "IMPRESSION": sample["text"].apply(extract_impression),
        "TRUE_LABEL (Positive/Negative)": "",
        "finding_type (acute/chronic-stable/post-surgical/none)": "",
        "confidence (high/low)": "",
        "notes": "",
    })
    blind.to_csv(BLIND, index=False)

    # KEY (hidden) — maps back to automated labels + the stratum, for scoring.
    key = pd.DataFrame({
        "review_id": sample["review_id"],
        "note_id": sample["note_id"],
        "regex_label": sample["regex_label"],
        "llm_label": sample["llm_label"],
        "stratum": sample["regex_label"].str[:3] + "/" + sample["llm_label"].str[:3],
    })
    key.to_csv(KEY, index=False)

    print(f"Built {len(sample)}-report gold sample.")
    print("\nStratum counts:")
    print(key["stratum"].value_counts().to_string())
    print(f"\nGive to clinicians (blinded): {BLIND.name}")
    print(f"Keep hidden (scoring key):    {KEY.name}")
    print("\nProcess: 2 clinicians label BLIND independently -> Cohen's kappa;")
    print("a 3rd adjudicates ties -> gold labels -> join KEY -> regex sens/spec/PPV/NPV.")


if __name__ == "__main__":
    main()
