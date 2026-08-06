"""Evaluation metrics — shared across experiments."""
import numpy as np
from sklearn.metrics import (roc_auc_score, average_precision_score,
                             accuracy_score, brier_score_loss)

METRIC_NAMES = ["AUROC", "AUPRC", "Accuracy", "Brier"]


def score(y_true, y_prob, y_pred) -> dict:
    """Compute the standard metric set for one prediction."""
    return {
        "AUROC": roc_auc_score(y_true, y_prob),
        "AUPRC": average_precision_score(y_true, y_prob),
        "Accuracy": accuracy_score(y_true, y_pred),
        "Brier": brier_score_loss(y_true, y_prob),
    }


def evaluate_fitted(pipeline, X_test, y_test, pos_idx) -> dict:
    """Fit-already pipeline -> metric dict on the test split."""
    y_prob = pipeline.predict_proba(X_test)[:, pos_idx]
    y_pred = pipeline.predict(X_test)
    return score(y_test, y_prob, y_pred)


def ci95(values) -> tuple[float, float, float]:
    """Return (mean, lo, hi) as a percentile 95% CI over repeated runs."""
    a = np.asarray(values, dtype=float)
    return float(a.mean()), float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))
