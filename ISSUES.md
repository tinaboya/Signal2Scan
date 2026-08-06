# Open Work — ready to file as GitHub issues

Every `\TODO` and `\DECISION` in the paper draft, plus the open decisions in
[`LABELING.md`](LABELING.md) and [`DATA_LINEAGE.md`](DATA_LINEAGE.md), collected
in one place. Duplicates of the same underlying blocker are merged.

Once these are filed on GitHub, **delete this file** — two trackers is worse than
one. It exists only to make the initial batch easy to create.

Labels used below: `blocking` · `needs-clinician` · `analysis` · `writing`

---

## A. Blocked on clinician gold labels

The gold set is the single bottleneck: 13 of the draft's 19 `\TODO`s resolve the
moment it exists. File #1 as the parent and link the rest to it.

| # | Title | Labels | Where |
|---|---|---|---|
| 1 | **Produce the clinician-adjudicated gold label set (~450 reports)** — blind sheet already built (`e08`), annotation not begun | `blocking` `needs-clinician` | `LABELING.md` §3 |
| 2 | Compute the regex labeler's sens/spec/PPV/NPV + confusion matrix vs gold, overall and per positive subtype | `blocking` `analysis` | tex 266–271, 297, 425 · `e01` |
| 3 | Compute inter-rater agreement (Cohen's / Fleiss' κ) and check it against the acceptance threshold | `blocking` `analysis` | tex 269–274 · `e01` |
| 4 | Run noise-robust vs noise-naive comparison on the gold test set (AUROC/AUPRC, flagged/missed at sens ≥ 0.95) | `blocking` `analysis` | tex 94–96, 473, 599 · `e07` pt3 |
| 5 | Run the dirty-vs-clean flag comparison — operating point + which patients get flagged, regex vs audited | `blocking` `analysis` | tex 109, 482, 499 · `e07` pt3 |
| 6 | Re-check whether the coagulation SHAP direction is a dirty-label artifact | `analysis` | tex 615 |

## B. Decisions only a clinician can make

Each of these stops a downstream analysis. Batch them into one meeting.

| # | Title | Labels | Where |
|---|---|---|---|
| 7 | Sign off the positive-finding **codebook** + borderline rules (small stable subdural, microhemorrhage, chronic-only) | `blocking` `needs-clinician` | `LABELING.md` §3 |
| 8 | Set the **κ acceptance threshold** for the regex labeler (e.g. 0.80) | `blocking` `needs-clinician` | tex 274 |
| 9 | Name the **two annotators + adjudicator** | `blocking` `needs-clinician` | `LABELING.md` §3 |
| 10 | Decide handling of **Unclear (169)** and **Post-surgical (82)** — in the gold set and in the reported metrics; pre-specify, don't leave incidental | `needs-clinician` | tex 255 · `LABELING.md` §3 |
| 11 | Confirm the **ICD exclusion list** is clinically complete and is the intended population | `needs-clinician` | tex 247 |
| 12 | **Exclude neuro units by care unit as well as admission diagnosis?** 393 rows (9%) survive the current exclusion at 49–70% positive | `needs-clinician` | `DATA_LINEAGE.md` §3 · `e09` P4 |
| 13 | Confirm the **sensitivity floor** (ε = 0.05) for the flag's operating point | `needs-clinician` | tex 349, 607 |

## C. Analysis that is NOT blocked — do these now

These depend on neither the gold labels nor a clinician decision.

| # | Title | Labels | Where |
|---|---|---|---|
| 14 | **Reframe the paper around incremental value over case mix** — pooled 0.777 vs within-unit 0.618; report where the tool works (TSICU/SICU) and where it does not (MICU/CCU/CVICU, 60% of the cohort) | `blocking` `writing` | `STATUS.md` §3 · `e09` |
| 15 | **Calibrate probabilities before the decision-curve step** — the flag is a threshold on a probability, so calibration is a precondition, not a nicety | `analysis` | tex 563 · `e03` |
| 16 | Add calibration plots per model + fairness across age/sex/race | `analysis` | tex 563 |
| 17 | Justify the column drop rule; add an imputation-vs-drop sensitivity analysis (dropping pupillometry may discard real signal) | `analysis` | tex 395 |
| 18 | Report the class-imbalance resampling comparison (currently only class weighting) | `analysis` | tex 404 |
| 19 | Benchmark against Rothrock/Orlando and Scott-King ED rules on the ICU cohort; document every proxy | `analysis` | tex 568, 571 · `e04` |
| 20 | Report first-vs-repeat CT **stratified** (18.9% vs 43.2% positive); separate models did not help (0.776 / 0.756 vs 0.774) | `analysis` | `STATUS.md` §3 · `e09` |
| 21 | Re-check every SHAP direction; test the sedation-confounding explanation with RASS-conditioned, baseline-referenced GCS deltas | `analysis` | tex 584 |

## D. Reporting decisions (team)

| # | Title | Labels | Where |
|---|---|---|---|
| 22 | Choose the **primary reported model** — RF (best discrimination) vs logistic regression (interpretable, near-equivalent) | `writing` | tex 556 |
| 23 | Report KNN or state its exclusion explicitly — do not drop it silently | `writing` | tex 547 |
| 24 | Add a single held-out locked test set if a deployment claim is made? | `writing` | tex 412 |
| 25 | ~~Publish the `.tex` draft to GitHub?~~ **Decided:** separate private repo, synced to Overleaf. Double-blind review makes a public draft undesirable anyway | `writing` | `.gitignore` |
| 26 | Confirm with Leo that **AMAI** is the intended MICCAI workshop — "MICCAI" spans dozens with very different scope | `writing` | `STATUS.md` |
| 27 | Convert the draft to **LNCS** and cut 14 pages → 8 (+2 refs). **Do not start** until results stabilize; cutting before the gold labels land means cutting twice | `writing` | `STATUS.md` |

---

### Filing these

`gh` is not installed on this machine. Either:

- install it (`brew install gh`, then `gh auth login`) and file them in a batch, or
- create them by hand at <https://github.com/tinaboya/Signal2Scan/issues>

Start with **#1** — six other issues close behind it.
