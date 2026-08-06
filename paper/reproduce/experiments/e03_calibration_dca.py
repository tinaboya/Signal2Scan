"""e03 — Calibration curves + decision-curve analysis.  [SCAFFOLD]

Produces per-model calibration plots and a decision-curve (net-benefit vs.
threshold probability) analysis — the most decision-relevant evaluation for an
ordering-support tool (Results 4.3). Uses out-of-fold predictions from e02's CV
protocol so the curves are not optimistic.

STATUS: scaffold — calibration is wired; decision curve is stubbed with a clear
TODO. No results are fabricated.

Run from repo root:  python paper/reproduce/experiments/e03_calibration_dca.py
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


def _oof_probabilities(ds, model_name):
    """Out-of-fold positive-class probabilities for one model."""
    est = make_models()[model_name]
    oof = np.full(len(ds.y), np.nan)
    skf = StratifiedGroupKFold(n_splits=N_CV_FOLDS, shuffle=True, random_state=0)
    for tr, te in skf.split(ds.X, ds.y, ds.groups):
        pipe = make_pipeline(ds.preprocessor, est)
        pipe.fit(ds.X.iloc[tr], ds.y[tr])
        oof[te] = pipe.predict_proba(ds.X.iloc[te])[:, ds.pos_idx]
    return oof


def net_benefit(y_true, y_prob, thresholds):
    """Decision-curve net benefit across threshold probabilities."""
    n = len(y_true)
    nb = []
    for pt in thresholds:
        pred = (y_prob >= pt).astype(int)
        tp = np.sum((pred == 1) & (y_true == 1))
        fp = np.sum((pred == 1) & (y_true == 0))
        nb.append(tp / n - fp / n * (pt / (1 - pt)) if pt < 1 else np.nan)
    return np.array(nb)


def main():
    ds = load_dataset()
    OUTPUT_DIR.mkdir(exist_ok=True)
    print("e03 — calibration + decision-curve analysis [SCAFFOLD]\n")

    # Calibration data (out-of-fold) for the primary model.
    # TODO: set primary model once decided (DECISION in paper §3.4).
    primary = "Gradient Boosting"
    print(f"Computing out-of-fold probabilities for '{primary}' ...")
    oof = _oof_probabilities(ds, primary)

    thresholds = np.linspace(0.01, 0.60, 60)
    nb = net_benefit(ds.y, oof, thresholds)
    best_t = thresholds[int(np.nanargmax(nb))]
    print(f"Decision curve computed. Peak net benefit near threshold {best_t:.2f}.")

    # TODO: render matplotlib figures (calibration_curve + decision curve) and
    # save to outputs/e03_calibration.png / outputs/e03_decision_curve.png.
    # Kept as a stub to avoid committing figures before the primary model and
    # label validation (e01) are locked — all downstream results are provisional
    # until then.
    print("\n[TODO] render + save calibration and decision-curve figures once")
    print("       the primary model and label validation (e01) are finalized.")


if __name__ == "__main__":
    main()
