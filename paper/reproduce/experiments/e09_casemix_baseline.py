"""e09 — Case-mix baselines: how much of the performance is ICU location?

Motivated by an external review (V. Sharma, 2026-08): a baseline using only
`first_careunit` performs unexpectedly well, which raises the question of how
much of the reported AUROC reflects clinical physiology versus differences in
case mix between ICUs.

Note that `first_careunit`, `shift`, and `icu_hour_at_ct` are in `DROP_COLS`
(config.py), so the paper's model never sees them. This experiment adds them
back as explicit *comparators*, not as model features.

Four parts, each answering a different question:

  P1  Feature-set comparison — is the clinical model better than a case-mix
      baseline at all? Reports care-unit-only / context-only / clinical-only /
      clinical+context under the paper's own CV protocol.

  P2  Within-unit discrimination — pooled clinical model, out-of-fold
      predictions scored *separately inside each ICU*. This is the question the
      paper's claim actually rests on: given a patient already in a given unit,
      do the clinical features discriminate? Between-unit prevalence cannot
      contribute here.

  P3  Leave-one-ICU-out — train on all other units, test on the held-out unit.
      This is a *different* question from P2 (transfer to an unseen unit, not
      within-unit discrimination) and the two must not be conflated.

  P4  Cohort sensitivity — the exclusion criteria are meant to remove
      neurological admissions, but the three Neuro units are still present
      (~9% of the cohort, 49-70% positive). Re-runs P1 without them.

Run from repo root:  python paper/reproduce/experiments/e09_casemix_baseline.py
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import roc_auc_score, average_precision_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import (DATA_PATH, LABEL_COL, POSITIVE_CLASSES, POSITIVE_LABEL,
                    N_CV_FOLDS, OUTPUT_DIR, RANDOM_STATE)
from s2s.data import load_dataset
from s2s.models import make_models
from s2s.metrics import ci95

warnings.filterwarnings("ignore")

# The context variables the paper drops. Kept here as comparators only.
CONTEXT_COLS = ["first_careunit", "shift", "icu_hour_at_ct", "is_repeat"]
NEURO_UNITS = ["Neuro Stepdown", "Neuro Intermediate",
               "Neuro Surgical Intensive Care Unit (Neuro SICU)"]
# Two models suffice: the linear reference and the paper's best performer.
COMPARATORS = ["Logistic Regression", "Random Forest"]
N_REPEATS = 20
MIN_UNIT_N = 40          # units smaller than this are not scored separately


# --------------------------------------------------------------------------
def load_with_context():
    """Paper's modeling frame + the dropped context columns, row-aligned.

    `load_dataset()` filters to the binary task without reordering, so
    re-applying the same filter to the raw CSV reproduces the identical row
    order. Asserted rather than assumed.
    """
    ds = load_dataset()
    raw = pd.read_csv(DATA_PATH)
    raw = raw[raw[LABEL_COL].isin(POSITIVE_CLASSES)].copy()
    assert len(raw) == len(ds.X), "row alignment broken between raw and modeling frame"
    assert ((raw[LABEL_COL] == POSITIVE_LABEL).astype(int).values == ds.y).all(), \
        "label alignment broken between raw and modeling frame"

    raw["ct_order_time"] = pd.to_datetime(raw["ct_order_time"])
    # First vs repeat CT within an admission; ranked without reordering `raw`.
    order = raw.groupby(["subject_id", "hadm_id"])["ct_order_time"].rank(method="first")
    raw["is_repeat"] = (order > 1).astype(int)

    ctx = raw[CONTEXT_COLS].reset_index(drop=True)
    return ds, ctx


def make_preprocessor(X):
    """Same preprocessing contract as s2s.data, fit inside each fold."""
    num = X.select_dtypes(include=["int64", "float64", "int32"]).columns.tolist()
    cat = X.select_dtypes(include=["object"]).columns.tolist()
    return ColumnTransformer([
        ("num", Pipeline([("imputer", SimpleImputer(strategy="median")),
                          ("scaler", StandardScaler())]), num),
        ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                          ("onehot", OneHotEncoder(handle_unknown="ignore",
                                                   sparse_output=False))]), cat),
    ])


def feature_sets(ds, ctx):
    """The four comparators. Order is the order they appear in the paper table."""
    clinical = ds.X.reset_index(drop=True)
    return {
        "A. care unit only": ctx[["first_careunit"]],
        "B. context only": ctx,
        "C. clinical only (paper model)": clinical,
        "D. clinical + context": pd.concat([clinical, ctx], axis=1),
    }


def cv_scores(X, y, groups, estimator_name, n_repeats=N_REPEATS):
    """Repeated StratifiedGroupKFold -> (AUROC list, AUPRC list)."""
    auroc, auprc = [], []
    for rep in range(n_repeats):
        skf = StratifiedGroupKFold(n_splits=N_CV_FOLDS, shuffle=True, random_state=rep)
        for tr, te in skf.split(X, y, groups):
            est = make_models()[estimator_name]
            pipe = Pipeline([("preprocessor", make_preprocessor(X)),
                             ("classifier", est)])
            pipe.fit(X.iloc[tr], y[tr])
            p = pipe.predict_proba(X.iloc[te])[:, 1]
            auroc.append(roc_auc_score(y[te], p))
            auprc.append(average_precision_score(y[te], p))
    return auroc, auprc


# --------------------------------------------------------------------------
def part1_feature_sets(ds, ctx, mask=None, tag="P1", title=None):
    """Feature-set comparison under the paper's CV protocol."""
    y, groups = ds.y, ds.groups
    sets = feature_sets(ds, ctx)
    if mask is not None:
        y, groups = y[mask], groups[mask]
        sets = {k: v[mask].reset_index(drop=True) for k, v in sets.items()}

    print("\n" + "=" * 86)
    print(title or "P1 — Feature-set comparison "
          f"({N_REPEATS}x{N_CV_FOLDS}-fold patient-grouped CV)")
    print("=" * 86)
    print(f"n = {len(y)} | positive rate {y.mean():.1%}")
    print(f"\n{'Feature set':<32}{'Model':<22}{'AUROC [95% CI]':>22}{'AUPRC [95% CI]':>22}")
    print("-" * 98)

    rows = []
    for set_name, X in sets.items():
        for model_name in COMPARATORS:
            auroc, auprc = cv_scores(X, y, groups, model_name)
            ro, ra = ci95(auroc), ci95(auprc)
            rows.append(dict(feature_set=set_name, model=model_name,
                             n_features=X.shape[1], n=len(y),
                             AUROC_mean=ro[0], AUROC_lo=ro[1], AUROC_hi=ro[2],
                             AUPRC_mean=ra[0], AUPRC_lo=ra[1], AUPRC_hi=ra[2]))
            print(f"{set_name:<32}{model_name:<22}"
                  f"{f'{ro[0]:.3f} [{ro[1]:.3f},{ro[2]:.3f}]':>22}"
                  f"{f'{ra[0]:.3f} [{ra[1]:.3f},{ra[2]:.3f}]':>22}")

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_DIR / f"e09_{tag}_feature_sets.csv", index=False)
    return df


def part2_within_unit(ds, ctx, model_name="Random Forest", n_repeats=5):
    """Pooled clinical model, out-of-fold predictions scored inside each unit.

    Between-unit prevalence differences cannot inflate a within-unit AUROC, so
    this isolates the discrimination the clinical features actually provide.
    """
    X, y, groups = ds.X.reset_index(drop=True), ds.y, ds.groups
    unit = ctx["first_careunit"].values

    per_unit = {}
    pooled = []
    for rep in range(n_repeats):
        oof = np.full(len(y), np.nan)
        skf = StratifiedGroupKFold(n_splits=N_CV_FOLDS, shuffle=True, random_state=rep)
        for tr, te in skf.split(X, y, groups):
            pipe = Pipeline([("preprocessor", make_preprocessor(X)),
                             ("classifier", make_models()[model_name])])
            pipe.fit(X.iloc[tr], y[tr])
            oof[te] = pipe.predict_proba(X.iloc[te])[:, 1]
        pooled.append(roc_auc_score(y, oof))
        for u in np.unique(unit):
            sel = unit == u
            if sel.sum() < MIN_UNIT_N or len(np.unique(y[sel])) < 2:
                continue
            per_unit.setdefault(u, []).append(roc_auc_score(y[sel], oof[sel]))

    print("\n" + "=" * 86)
    print("P2 — Within-unit discrimination of the pooled clinical model")
    print("=" * 86)
    print(f"model: {model_name} | {n_repeats} repeats of {N_CV_FOLDS}-fold OOF prediction")
    pm, plo, phi = ci95(pooled)
    print(f"\nPooled (all units together)      AUROC = {pm:.3f} [{plo:.3f},{phi:.3f}]")
    print("\nSame predictions, scored inside each unit:")
    print(f"{'Care unit':<50}{'n':>6}{'pos':>7}{'AUROC [95% CI]':>24}")
    print("-" * 87)

    rows = [dict(care_unit="(pooled)", n=len(y), positive_rate=float(y.mean()),
                 AUROC_mean=pm, AUROC_lo=plo, AUROC_hi=phi)]
    for u, vals in sorted(per_unit.items(), key=lambda kv: -np.mean(kv[1])):
        sel = unit == u
        m, lo, hi = ci95(vals)
        rows.append(dict(care_unit=u, n=int(sel.sum()),
                         positive_rate=float(y[sel].mean()),
                         AUROC_mean=m, AUROC_lo=lo, AUROC_hi=hi))
        print(f"{u:<50}{sel.sum():>6}{y[sel].mean():>7.2f}"
              f"{f'{m:.3f} [{lo:.3f},{hi:.3f}]':>24}")

    n_scored = sum(1 for u in per_unit)
    weighted = np.average([r["AUROC_mean"] for r in rows[1:]],
                          weights=[r["n"] for r in rows[1:]])
    print(f"\nSize-weighted mean of within-unit AUROC ({n_scored} units): {weighted:.3f}")
    print(f"Pooled AUROC exceeds it by {pm - weighted:+.3f} — "
          "that gap is between-unit case mix, not clinical discrimination.")

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_DIR / "e09_P2_within_unit.csv", index=False)
    return df


def part3_leave_one_icu_out(ds, ctx, model_name="Random Forest"):
    """Train on all other units, test on the held-out unit (transfer, not P2)."""
    X, y = ds.X.reset_index(drop=True), ds.y
    unit = ctx["first_careunit"].values

    print("\n" + "=" * 86)
    print("P3 — Leave-one-ICU-out (transfer to an unseen unit)")
    print("=" * 86)
    print("Distinct from P2: here the unit is absent from training entirely.")
    print(f"\n{'Held-out care unit':<50}{'n':>6}{'pos':>7}{'AUROC':>9}{'AUPRC':>9}")
    print("-" * 81)

    rows = []
    for u in pd.Series(unit).value_counts().index:
        te = unit == u
        if te.sum() < MIN_UNIT_N or len(np.unique(y[te])) < 2:
            print(f"{u:<50}{te.sum():>6}   (skipped: too small / single class)")
            continue
        pipe = Pipeline([("preprocessor", make_preprocessor(X)),
                         ("classifier", make_models()[model_name])])
        pipe.fit(X[~te], y[~te])
        p = pipe.predict_proba(X[te])[:, 1]
        au, ap = roc_auc_score(y[te], p), average_precision_score(y[te], p)
        rows.append(dict(held_out_unit=u, n=int(te.sum()),
                         positive_rate=float(y[te].mean()), AUROC=au, AUPRC=ap))
        print(f"{u:<50}{te.sum():>6}{y[te].mean():>7.2f}{au:>9.3f}{ap:>9.3f}")

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_DIR / "e09_P3_leave_one_icu_out.csv", index=False)
    return df


def part4_neuro_sensitivity(ds, ctx):
    """P1 re-run with the Neuro units removed (cohort-exclusion sensitivity)."""
    keep = ~ctx["first_careunit"].isin(NEURO_UNITS).values
    n_drop = (~keep).sum()
    print("\n" + "=" * 86)
    print("P4 — Cohort sensitivity: Neuro units excluded")
    print("=" * 86)
    print(f"Dropping {n_drop} rows ({n_drop/len(keep):.1%}) in {NEURO_UNITS}.")
    print("The exclusion criteria intend to remove neurological admissions; these")
    print("units survived it, so the main analysis should be shown to not depend")
    print("on them.")
    return part1_feature_sets(ds, ctx, mask=keep, tag="P4",
                              title="P4 — Feature-set comparison, Neuro units excluded")


# --------------------------------------------------------------------------
def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    ds, ctx = load_with_context()
    print(f"Loaded {len(ds.y)} rows | positive rate {ds.y.mean():.1%}")
    print(f"Clinical features: {ds.X.shape[1]} | context comparators: {CONTEXT_COLS}")

    print("\nPositive rate by care unit (the case-mix spread in question):")
    tab = (pd.DataFrame({"unit": ctx["first_careunit"], "y": ds.y})
           .groupby("unit")["y"].agg(n="size", positive_rate="mean")
           .sort_values("positive_rate", ascending=False))
    print(tab.to_string(float_format=lambda v: f"{v:.3f}"))
    tab.to_csv(OUTPUT_DIR / "e09_P0_prevalence_by_unit.csv")

    print("\nPositive rate by first vs repeat CT:")
    print(pd.DataFrame({"is_repeat": ctx["is_repeat"], "y": ds.y})
          .groupby("is_repeat")["y"].agg(n="size", positive_rate="mean")
          .to_string(float_format=lambda v: f"{v:.3f}"))

    part1_feature_sets(ds, ctx)
    part2_within_unit(ds, ctx)
    part3_leave_one_icu_out(ds, ctx)
    part4_neuro_sensitivity(ds, ctx)

    print("\n" + "=" * 86)
    print(f"Saved 5 tables to {OUTPUT_DIR}/e09_*.csv")
    print("=" * 86)


if __name__ == "__main__":
    main()
