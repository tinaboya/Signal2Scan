"""e04 — Benchmark our model against established ED clinical decision rules. [SCAFFOLD]

Re-implements ED head-CT rules (Rothrock/Orlando, Scott-King) on the ICU cohort
using our features as proxies, and reports each rule's sensitivity / specificity
/ PPV / NPV side-by-side with the learned model (Results 4.4). Expected finding:
ED rules keep high sensitivity but very low specificity in the ICU, consistent
with the Orlando meta-analysis (98.4% / 17.9%).

STATUS: scaffold. Each rule variable must be mapped to a MIMIC-IV feature; some
(e.g. "headache" in a sedated patient) may be unrepresentable and must be
documented as a limitation, NOT silently dropped. Physician-lead sign-off on the
proxies is required (DECISION in the experiment plan).

Run from repo root:  python paper/reproduce/experiments/e04_rule_benchmark.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from s2s.data import load_dataset

# Feature-proxy map — TODO: fill + get physician-lead sign-off before use.
# Each entry: rule_variable -> (feature_column, how_derived, representable?)
ROTHROCK_PROXIES = {
    "age >= 60": ("age", "age >= 60", True),
    "focal neurologic deficit": (None, "TODO: no direct column; candidate flags?", False),
    "headache with vomiting": (None, "TODO: not captured for sedated ICU pts", False),
    "altered mental status": ("gcs_total_min", "TODO: GCS<14 proxy? (Harris 2000)", True),
}
SCOTT_KING_PROXIES = {
    "focal deficit": (None, "TODO", False),
    "GCS < 15": ("gcs_total_min", "gcs_total_min < 15", True),
    "malignancy": (None, "TODO: from diagnoses?", False),
    "vomiting": (None, "TODO", False),
    "coagulopathy": ("flag_coagulopathy", "existing flag", True),
    "headache": (None, "TODO", False),
}


def _report_map(name, proxies):
    print(f"\n{name} — variable -> feature proxy")
    print("-" * 60)
    representable = 0
    for var, (col, how, ok) in proxies.items():
        mark = "OK " if ok else "?? "
        representable += ok
        print(f"  [{mark}] {var:<26} -> {col}  ({how})")
    print(f"  representable: {representable}/{len(proxies)} variables")


def main():
    ds = load_dataset()
    print("e04 — clinical-rule benchmark [SCAFFOLD]")
    print(f"Cohort: {len(ds.y)} rows | positive rate {ds.y.mean():.1%}")
    print("\nAvailable feature columns:")
    print("  " + ", ".join(ds.X.columns))

    _report_map("Rothrock / Orlando", ROTHROCK_PROXIES)
    _report_map("Scott-King", SCOTT_KING_PROXIES)

    print("\n[TODO] Once proxies are signed off by the clinical lead:")
    print("  1. Compute each rule's binary prediction on the cohort.")
    print("  2. Report sensitivity/specificity/PPV/NPV + net benefit.")
    print("  3. Compare side-by-side with the learned model (e02).")
    print("  4. Document every unrepresentable variable as a limitation.")


if __name__ == "__main__":
    main()
