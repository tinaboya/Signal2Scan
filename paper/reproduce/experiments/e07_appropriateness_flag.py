"""e07 — ICU head-CT appropriateness-flag tool (the clinical contribution).

A non-blocking, high-sensitivity, interpretable flag: from pre-scan 4h structured
data, mark a CT request as "predicted low-yield" for optional review. This is the
paper's headline method; the predictive model is only its engine.

What this script does:
  1. HIGH-SENSITIVITY OPERATING POINT — pick the probability threshold that keeps
     sensitivity >= target (default 0.95), so true positives are almost never
     flagged low-yield. Report flag rate and missed-positive rate there.
  2. DECISION CURVE — net benefit vs threshold probability, compared to
     scan-all / scan-none, to show clinical utility.
  3. DIRTY-vs-CLEAN — run the whole thing twice, on regex labels and on audited
     gold labels, to show the regex-based tool flags the WRONG patients.

STATUS: parts 1-2 run today on the current (regex) labels as a template. Part 3
is a stub until the clinician gold labels exist (e08 -> adjudication). No numbers
are fabricated; the dirty-vs-clean comparison prints "pending gold labels" until
they are provided.

Run from repo root:  python paper/reproduce/experiments/e07_appropriateness_flag.py
"""
import sys
import warnings
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import N_CV_FOLDS, OUTPUT_DIR
from s2s.data import load_dataset
from s2s.models import make_models, make_pipeline

warnings.filterwarnings("ignore")

TARGET_SENS = 0.95   # high-sensitivity constraint: rarely flag a true positive
PRIMARY = "Random Forest"
GOLD_LABELS = OUTPUT_DIR / "e08_gold_adjudicated.csv"  # produced after annotation


def oof_probabilities(ds):
    """Out-of-fold positive-class probabilities for the primary model."""
    est = make_models()[PRIMARY]
    oof = np.full(len(ds.y), np.nan)
    skf = StratifiedGroupKFold(n_splits=N_CV_FOLDS, shuffle=True, random_state=0)
    for tr, te in skf.split(ds.X, ds.y, ds.groups):
        pipe = make_pipeline(ds.preprocessor, est)
        pipe.fit(ds.X.iloc[tr], ds.y[tr])
        oof[te] = pipe.predict_proba(ds.X.iloc[te])[:, ds.pos_idx]
    return oof


def high_sensitivity_point(y_true, y_prob, target=TARGET_SENS):
    """Highest threshold whose sensitivity >= target, i.e. the operating point
    that MAXIMIZES the flagged fraction subject to the safety constraint.

    A request is flagged "low-yield" when prob < thr, so raising thr flags more
    requests (more benefit) and lowers sensitivity (less safety). Sensitivity is
    therefore monotonically non-increasing in thr, the satisfying thresholds form
    a prefix, and the last one is the constrained maximum.

    Maximizing is the intended direction. Minimizing the flagged fraction is
    degenerate: flagging nothing meets any sensitivity constraint and delivers no
    clinical benefit.
    """
    thresholds = np.unique(np.round(y_prob, 3))   # np.unique returns them sorted
    pos = y_true == 1
    best = None
    for thr in thresholds:
        flagged_low = y_prob < thr                 # tool says "low-yield"
        # sensitivity = fraction of true positives NOT flagged low-yield
        sens = np.mean(~flagged_low[pos]) if pos.any() else np.nan
        if sens < target:
            break                                  # constraint violated from here on
        flag_rate = np.mean(flagged_low)
        missed_pos = np.mean(flagged_low[pos]) if pos.any() else np.nan
        best = dict(threshold=float(thr), sensitivity=float(sens),
                    flag_rate=float(flag_rate), missed_positive_rate=float(missed_pos))
    return best


def net_benefit(y_true, y_prob, thresholds):
    n = len(y_true)
    out = []
    for pt in thresholds:
        pred = (y_prob >= pt).astype(int)
        tp = np.sum((pred == 1) & (y_true == 1))
        fp = np.sum((pred == 1) & (y_true == 0))
        nb = tp / n - fp / n * (pt / (1 - pt)) if pt < 1 else np.nan
        nb_all = np.mean(y_true) - (1 - np.mean(y_true)) * (pt / (1 - pt)) if pt < 1 else np.nan
        out.append((pt, nb, nb_all))
    return out


def run_on_labels(ds, y, tag):
    print(f"\n=== Operating point on {tag} labels ({PRIMARY}) ===")
    prob = oof_probabilities(ds if tag == "regex" else ds)  # same features, given y
    op = high_sensitivity_point(y, prob, TARGET_SENS)
    if op:
        print(f"  target sensitivity >= {TARGET_SENS:.0%}")
        print(f"  threshold           = {op['threshold']:.3f}")
        print(f"  achieved sensitivity= {op['sensitivity']:.3f}")
        print(f"  FLAG RATE (requests flagged low-yield) = {op['flag_rate']:.1%}")
        print(f"  missed-positive rate                   = {op['missed_positive_rate']:.1%}")
        print(f"  -> 'At {op['sensitivity']:.0%} sensitivity, the tool flags "
              f"{op['flag_rate']:.0%} of requests as low-yield, "
              f"missing {op['missed_positive_rate']:.1%} of true positives.'")
    else:
        print("  no threshold met the sensitivity target")
    return prob, op


def main():
    ds = load_dataset()
    print(f"Loaded {len(ds.y)} rows | positive rate {ds.y.mean():.1%}")

    # Part 1+2 on current (regex) labels — the template
    prob, op = run_on_labels(ds, ds.y, "regex")

    print("\n=== Decision curve (regex labels) — net benefit vs threshold ===")
    print(f"{'pt':>6}{'model_NB':>12}{'scan_all_NB':>14}")
    for pt, nb, nb_all in net_benefit(ds.y, prob, [0.05, 0.1, 0.15, 0.2, 0.3]):
        print(f"{pt:>6.2f}{nb:>12.4f}{nb_all:>14.4f}")
    print("  (net benefit > scan_all and > 0 in this range => clinical utility)")

    # Part 3 — dirty vs clean (needs gold labels)
    print("\n=== Dirty-vs-clean comparison ===")
    if GOLD_LABELS.exists():
        import pandas as pd
        gold = pd.read_csv(GOLD_LABELS)
        print("  [gold labels found] TODO: remap ds.y to audited labels, rerun "
              "operating point, and report how many patients the regex-based tool "
              "flags that the clean-label tool does NOT (the wrong-patient count).")
    else:
        print("  [pending] No gold labels yet (expected: e08_gold_adjudicated.csv).")
        print("  Once clinicians finish the e08 blind sheet and it is adjudicated,")
        print("  this compares the flag tool built on regex vs audited labels and")
        print("  reports the wrong-patient count + whether the coagulation signal")
        print("  is a dirty-label artifact.")


if __name__ == "__main__":
    main()
