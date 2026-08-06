"""e00 — Reproduce the datathon table and check seed robustness.

Goal 1 (REPRODUCE): re-run the exact datathon pipeline on the same data and
  confirm the single-split numbers match the published table.
Goal 2 (ROBUSTNESS): the datathon used ONE GroupShuffleSplit; repeat over many
  seeds to show how stable those numbers are — motivating the move to repeated
  CV with CIs (e02). Also runs KNN (absent from the published table).

Run from repo root:  python paper/reproduce/experiments/e00_reproduce.py
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

# make repo/paper/reproduce importable regardless of CWD
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import (RANDOM_STATE, TEST_SIZE, N_ROBUSTNESS_SEEDS,
                    PUBLISHED_RESULTS, OUTPUT_DIR)
from s2s.data import load_dataset
from s2s.models import make_models, make_pipeline
from s2s.metrics import evaluate_fitted, METRIC_NAMES

warnings.filterwarnings("ignore")


def _split(ds, seed):
    return next(GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE,
                                  random_state=seed).split(ds.X, ds.y, ds.groups))


def _eval_all(ds, tr, te):
    out = {}
    for name, est in make_models().items():
        pipe = make_pipeline(ds.preprocessor, est)
        pipe.fit(ds.X.iloc[tr], ds.y[tr])
        out[name] = evaluate_fitted(pipe, ds.X.iloc[te], ds.y[te], ds.pos_idx)
    return out


def main():
    ds = load_dataset()
    print(f"Loaded {len(ds.y)} rows | classes {list(ds.label_encoder.classes_)} "
          f"| positive rate {ds.y.mean():.1%}\n")
    OUTPUT_DIR.mkdir(exist_ok=True)

    # ---- Goal 1: reproduce single split (seed 42) ----
    tr, te = _split(ds, RANDOM_STATE)
    print(f"Split (seed {RANDOM_STATE}): train {len(tr)} | test {len(te)} "
          f"| test positive rate {ds.y[te].mean():.1%}\n")
    res = _eval_all(ds, tr, te)

    print("=" * 70)
    print("GOAL 1 — REPRODUCE single-split table (repro vs. published)")
    print("=" * 70)
    rows, max_abs = [], 0.0
    hdr = f"{'Model':<20}{'metric':<9}{'repro':>8}{'pub':>8}{'delta':>8}"
    print(hdr); print("-" * len(hdr))
    for name in PUBLISHED_RESULTS:
        for m in METRIC_NAMES:
            r, p = res[name][m], PUBLISHED_RESULTS[name][m]
            d = r - p
            max_abs = max(max_abs, abs(d))
            rows.append(dict(model=name, metric=m, repro=r, published=p, delta=d))
            print(f"{name:<20}{m:<9}{r:>8.3f}{p:>8.3f}{d:>+8.3f}")
    print("-" * len(hdr))
    k = res["KNN"]
    print(f"KNN (dropped from published table): AUROC={k['AUROC']:.3f} "
          f"AUPRC={k['AUPRC']:.3f} Acc={k['Accuracy']:.3f} Brier={k['Brier']:.3f}")
    verdict = ("MATCH" if max_abs < 0.005 else
               "CLOSE" if max_abs < 0.02 else "MISMATCH")
    print(f"\n==> max |delta| = {max_abs:.4f}  ->  REPRODUCTION: {verdict}")
    pd.DataFrame(rows).to_csv(OUTPUT_DIR / "e00_reproduce_table.csv", index=False)

    # ---- Goal 2: robustness across seeds ----
    print("\n" + "=" * 70)
    print(f"GOAL 2 — ROBUSTNESS across {N_ROBUSTNESS_SEEDS} patient-grouped splits")
    print("=" * 70)
    acc = {n: {m: [] for m in METRIC_NAMES} for n in make_models()}
    for s in range(N_ROBUSTNESS_SEEDS):
        tr, te = _split(ds, s)
        r = _eval_all(ds, tr, te)
        for n in r:
            for m in METRIC_NAMES:
                acc[n][m].append(r[n][m])

    print(f"{'Model':<20}{'AUROC mean±std [min,max]':<32}{'AUPRC mean':>11}")
    print("-" * 63)
    rob_rows = []
    for n in make_models():
        a = np.array(acc[n]["AUROC"]); pr = np.array(acc[n]["AUPRC"])
        print(f"{n:<20}{a.mean():.3f}±{a.std():.3f} "
              f"[{a.min():.3f},{a.max():.3f}]      {pr.mean():>6.3f}")
        rob_rows.append(dict(model=n, auroc_mean=a.mean(), auroc_std=a.std(),
                             auroc_min=a.min(), auroc_max=a.max(),
                             auprc_mean=pr.mean()))
    pd.DataFrame(rob_rows).to_csv(OUTPUT_DIR / "e00_robustness.csv", index=False)
    print("\nWide [min,max] => the single-split headline is not trustworthy alone;")
    print("that is exactly why e02 replaces it with repeated CV + 95% CIs.")
    print(f"\nSaved: {OUTPUT_DIR/'e00_reproduce_table.csv'}, "
          f"{OUTPUT_DIR/'e00_robustness.csv'}")


if __name__ == "__main__":
    main()
