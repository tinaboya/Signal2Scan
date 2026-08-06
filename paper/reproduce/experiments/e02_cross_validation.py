"""e02 — Repeated patient-grouped cross-validation with 95% CIs.

Replaces the datathon's single 80/20 split with repeated StratifiedGroupKFold,
reporting mean and percentile 95% CI per metric per model. This is the evaluation
protocol the paper requires (Methods 3.4 / Results 4.2).

Run from repo root:  python paper/reproduce/experiments/e02_cross_validation.py
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import N_CV_REPEATS, N_CV_FOLDS, OUTPUT_DIR
from s2s.data import load_dataset
from s2s.models import make_models, make_pipeline
from s2s.metrics import evaluate_fitted, ci95, METRIC_NAMES

warnings.filterwarnings("ignore")


def main():
    ds = load_dataset()
    print(f"Loaded {len(ds.y)} rows | positive rate {ds.y.mean():.1%}")
    print(f"Protocol: {N_CV_REPEATS} repeats x {N_CV_FOLDS}-fold "
          f"StratifiedGroupKFold (patient-grouped)\n")
    OUTPUT_DIR.mkdir(exist_ok=True)

    per_model = {n: {m: [] for m in METRIC_NAMES} for n in make_models()}
    for rep in range(N_CV_REPEATS):
        skf = StratifiedGroupKFold(n_splits=N_CV_FOLDS, shuffle=True,
                                   random_state=rep)
        for tr, te in skf.split(ds.X, ds.y, ds.groups):
            for name, est in make_models().items():
                pipe = make_pipeline(ds.preprocessor, est)
                pipe.fit(ds.X.iloc[tr], ds.y[tr])
                r = evaluate_fitted(pipe, ds.X.iloc[te], ds.y[te], ds.pos_idx)
                for m in METRIC_NAMES:
                    per_model[name][m].append(r[m])
        print(f"  repeat {rep+1}/{N_CV_REPEATS} done")

    print("\n" + "=" * 78)
    print("Repeated grouped CV — mean [95% CI]")
    print("=" * 78)
    print(f"{'Model':<20}" + "".join(f"{m:>17}" for m in METRIC_NAMES))
    print("-" * 88)
    rows = []
    for name in make_models():
        cells, row = [], {"model": name}
        for m in METRIC_NAMES:
            mean, lo, hi = ci95(per_model[name][m])
            cells.append(f"{mean:.3f}[{lo:.3f},{hi:.3f}]")
            row[f"{m}_mean"], row[f"{m}_lo"], row[f"{m}_hi"] = mean, lo, hi
        rows.append(row)
        print(f"{name:<20}" + "".join(f"{c:>17}" for c in cells))
    pd.DataFrame(rows).to_csv(OUTPUT_DIR / "e02_cv_results.csv", index=False)
    print(f"\nSaved: {OUTPUT_DIR/'e02_cv_results.csv'}")
    print("These mean±CI numbers replace the single-split table in the paper.")


if __name__ == "__main__":
    main()
