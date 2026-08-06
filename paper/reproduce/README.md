# Signal2Scan — Experiment Codebase

The working codebase for the Signal2Scan study (datathon → ML4H paper). Every
analysis in the paper is produced by a script here, so results are reproducible
and auditable.

> **Code is tracked; data is not.** The scripts here are committed so
> collaborators can read and run them. They read credentialed MIMIC-IV-derived
> data that cannot be redistributed under the PhysioNet DUA, so no input file is
> in the repo — obtain them through the approved channel and place them per
> [`../../DATA_LINEAGE.md`](../../DATA_LINEAGE.md).
>
> `outputs/` is **deny-listed by default** in `.gitignore`: a new experiment's
> output is private until explicitly whitelisted, and only aggregate tables
> (metrics, counts) may ever be whitelisted. Anything carrying a `note_id`,
> `subject_id`, `hadm_id`, or report text must not be.

## Layout

```
reproduce/
├── README.md                 # this file
├── config.py                 # paths, constants, the drop-list, seeds
├── s2s/                       # shared library (import from every experiment)
│   ├── data.py               # load + build X, y, groups, preprocessor
│   ├── models.py             # the model zoo (single source of truth)
│   └── metrics.py            # AUROC/AUPRC/Brier/... helpers
├── experiments/              # one script per paper analysis; each writes to outputs/
│   ├── e00_reproduce.py          # datathon table + seed robustness      [DONE]
│   ├── e01_label_validation.py   # regex-vs-gold metrics + kappa         [BLOCKED on gold]
│   ├── e02_cross_validation.py   # repeated grouped CV + 95% CIs         [DONE]
│   ├── e03_calibration_dca.py    # calibration + decision curves         [calibration missing]
│   ├── e04_rule_benchmark.py     # vs. Rothrock/Scott-King ED rules      [SCAFFOLD]
│   ├── e05_llm_label_all.py      # LLM audit of every report             [DONE]
│   ├── e06_build_review_sheet.py # clinician review sheet                [DONE]
│   ├── e07_appropriateness_flag.py # operating point + DCA + dirty/clean [parts 1-2 done]
│   ├── e08_build_gold_sample.py  # blind gold sample + batches           [built, unannotated]
│   └── e09_casemix_baseline.py   # case-mix baselines, within-unit, LOICUO [DONE]
└── outputs/                  # generated tables (deny-listed; see above)
```

Project state, blocking decisions, and which claim each experiment supports live
in [`../../STATUS.md`](../../STATUS.md).

## Setup

```bash
pip install -r requirements.txt   # scikit-learn, pandas, numpy, matplotlib
```

Set the data path once in `config.py` (defaults to the repo's `extracted/...`
location).

## Running

Each experiment is a standalone entry point run from the repo root:

```bash
python paper/reproduce/experiments/e00_reproduce.py
python paper/reproduce/experiments/e02_cross_validation.py
```

Results are written to `paper/reproduce/outputs/` (CSV tables, PNG figures) and
are safe to delete/regenerate.

## Status

| Experiment | Purpose | Paper section | Status |
|-----------|---------|---------------|--------|
| e00 | Reproduce datathon table; seed robustness | Results 4.2 | ✅ ready |
| e01 | Label validation vs. clinician gold set | Methods 3.2 / Results 4.1 | 🔴 blocking — needs gold labels |
| e02 | Repeated grouped CV + 95% CIs | Methods 3.4 / Results 4.2 | 🔴 blocking |
| e03 | Calibration + decision-curve analysis | Results 4.3 | 🟠 scaffold |
| e04 | Benchmark vs. ED clinical rules | Results 4.4 | 🟠 scaffold |

See `paper/experiment_plan_update_from_litreview.md` for priorities and rationale.
