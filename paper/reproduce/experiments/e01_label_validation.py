"""e01 — Label validation: regex labeler vs. clinician gold standard.  [SCAFFOLD]

BLOCKING for submission. Once the clinician-adjudicated gold set exists
(see LABELING.md §3), this computes the labeler's confusion matrix,
sensitivity/specificity/PPV/NPV (overall and per subtype) and inter-rater
Cohen's/Fleiss' kappa.

STATUS: scaffold. It needs a gold-label file that does not exist yet:
  outputs/gold_labels.csv  with columns:
    note_id, regex_label, gold_label   (+ optional rater1, rater2 for kappa)

Run from repo root:  python paper/reproduce/experiments/e01_label_validation.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import OUTPUT_DIR

GOLD_PATH = OUTPUT_DIR / "gold_labels.csv"


def main():
    if not GOLD_PATH.exists():
        print("=" * 70)
        print("e01 LABEL VALIDATION — not runnable yet (no gold set).")
        print("=" * 70)
        print(f"\nExpected gold file: {GOLD_PATH}")
        print("Required columns: note_id, regex_label, gold_label")
        print("Optional (for kappa): rater1, rater2\n")
        print("To produce it (LABELING.md §3):")
        print("  1. Stratified random sample ~300-500 reports "
              "(over-sample Positive/Unclear).")
        print("  2. Two clinicians label vs. a codebook; a third adjudicates.")
        print("  3. Save adjudicated labels + both raters here.\n")
        print("Once present, this script will report: confusion matrix,")
        print("sensitivity/specificity/PPV/NPV (overall + per subtype), and kappa.")
        return

    # --- Real computation, enabled once the gold set exists ---
    import pandas as pd
    from sklearn.metrics import confusion_matrix, cohen_kappa_score

    gold = pd.read_csv(GOLD_PATH)
    y_true = (gold["gold_label"] == "Positive").astype(int)
    y_pred = (gold["regex_label"] == "Positive").astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    sens = tp / (tp + fn) if (tp + fn) else float("nan")
    spec = tn / (tn + fp) if (tn + fp) else float("nan")
    ppv = tp / (tp + fp) if (tp + fp) else float("nan")
    npv = tn / (tn + fn) if (tn + fn) else float("nan")

    print("Label validation (Positive vs. rest):")
    print(f"  confusion: TP={tp} FP={fp} FN={fn} TN={tn}")
    print(f"  sensitivity={sens:.3f} specificity={spec:.3f} "
          f"PPV={ppv:.3f} NPV={npv:.3f}")
    if {"rater1", "rater2"}.issubset(gold.columns):
        kappa = cohen_kappa_score(gold["rater1"], gold["rater2"])
        print(f"  inter-rater Cohen's kappa = {kappa:.3f}")

    pd.DataFrame([dict(TP=tp, FP=fp, FN=fn, TN=tn, sensitivity=sens,
                       specificity=spec, PPV=ppv, NPV=npv)]).to_csv(
        OUTPUT_DIR / "e01_label_validation.csv", index=False)
    print(f"\nSaved: {OUTPUT_DIR/'e01_label_validation.csv'}")


if __name__ == "__main__":
    main()
