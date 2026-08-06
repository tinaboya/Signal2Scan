"""e06 — Build a clinician-friendly review sheet from the 654 disagreements.

Takes e05_disagreements_for_review.csv (regex=Negative, LLM=Positive) and produces
a sheet a clinician can fill in directly: extracted IMPRESSION, a compact keyword
hint, and blank adjudication columns. The adjudication columns encode the key
distinction we found (acute vs chronic/stable vs post-surgical) so the physician
resolves exactly what the two automated methods cannot.

Output: outputs/e06_clinician_review_sheet.csv

Run from repo root:  python paper/reproduce/experiments/e06_build_review_sheet.py
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import OUTPUT_DIR

SRC = OUTPUT_DIR / "e05_disagreements_for_review.csv"
OUT = OUTPUT_DIR / "e06_clinician_review_sheet.csv"

ACUTE_KW = re.compile(r"(?i)(hemorrhage|hematoma|infarct|fracture|mass effect|"
                      r"midline shift|edema|hydrocephalus|herniation|ischemi|bleed|"
                      r"pneumocephalus|abscess)")
STABLE_KW = re.compile(r"(?i)(stable|unchanged|chronic|old|prior|previously|"
                       r"resolution|resolved|improved|decreased|evolving|"
                       r"postsurgical|post-surgical|postoperative|craniotomy|"
                       r"status post|burr hole)")


def extract_impression(text: str) -> str:
    m = re.search(r"(?i)IMPRESSION[:\s]*([\s\S]+)", text)
    imp = (m.group(1) if m else text).strip()
    imp = re.sub(r"\s+", " ", imp)
    return imp[:500]


def main():
    if not SRC.exists():
        print(f"Missing {SRC}. Run e05 first.")
        return
    dis = pd.read_csv(SRC)
    rows = []
    for _, r in dis.iterrows():
        imp = extract_impression(r["text"])
        acute = bool(ACUTE_KW.search(imp))
        stable = bool(STABLE_KW.search(imp))
        # a quick automated hint (NOT the label — just to triage the physician's eye)
        if acute and stable:
            hint = "acute-finding-word + stable/chronic-word (needs your call)"
        elif acute:
            hint = "acute finding word present"
        else:
            hint = "no acute keyword (LLM may have over-called)"
        rows.append({
            "note_id": r["note_id"],
            "subject_id": r["subject_id"],
            "hadm_id": r["hadm_id"],
            "regex_label": "Negative",
            "llm_label": "Positive",
            "IMPRESSION": imp,
            "auto_hint": hint,
            # blank columns for the physician:
            "TRUE_LABEL (Pos/Neg)": "",
            "finding_type (acute / chronic-stable / post-surgical / none)": "",
            "physician_notes": "",
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(f"Wrote {len(out)} rows to {OUT.name}")
    print("\nColumns for the physician to fill:")
    print("  - TRUE_LABEL (Pos/Neg)")
    print("  - finding_type (acute / chronic-stable / post-surgical / none)")
    print("  - physician_notes")
    print("\nauto_hint breakdown (triage only, NOT labels):")
    print(out["auto_hint"].value_counts().to_string())


if __name__ == "__main__":
    main()
