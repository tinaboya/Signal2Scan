# Outcome Labeling & Validation Status — Signal2Scan

This document is the authoritative record of **how the CT outcome labels were
produced, how far they have been validated, and what remains to be done**. It
exists because the honest answer to "how did you validate your labels?" is
important to state plainly for reviewers, collaborators, and our future selves.

**TL;DR — current status:** Labels were assigned by **rule-based regular
expressions** during the datathon. They have **not yet been validated against a
clinician-adjudicated ground truth.** A concrete validation plan is specified in
§3 below and is the project's highest-priority open task before any result is
considered final.

---

## 1. How labels are currently produced  `[BUILT]`

Each head-CT report is classified by regular expressions over the
`IMPRESSION` / `FINDINGS` sections of the MIMIC-IV-Note radiology text.

**Implementation:** [`Final dataset and code/Classifying CT reports.sql`](Final%20dataset%20and%20code/Classifying%20CT%20reports.sql)
and [`results/signal2scan_feature_extraction_4h_sql_query.txt`](results/signal2scan_feature_extraction_4h_sql_query.txt).

| Label | Rule (summary) |
|-------|----------------|
| **Negative** | "no acute intracranial", "unremarkable", chronic-only changes, … |
| **Positive** | hemorrhage / infarct / fracture / mass effect / edema / hydrocephalus …, **with negation handling** (excludes "no / without / chronic / prior" matches) |
| **Post-surgical / Unchanged** | "postoperative", "craniotomy", "unchanged from prior", … |
| **Unclear** | none of the above matched confidently |

Positive scans are further sub-typed: Hemorrhage, Infarct, Fracture, Mass
Effect, Hydrocephalus.

**Resulting label distribution** (n = 4,638 CT orders in `final_ct_head_dataset.csv`):

| Class | Count | % |
|-------|-------|---|
| Negative | 3,383 | 72.9% |
| Positive | 1,004 | 21.6% |
| Unclear | 169 | 3.6% |
| Post-surgical / Unchanged | 82 | 1.8% |

Modeling uses the **Positive-vs-Negative** subset (4,387 rows); Unclear and
Post-surgical/Unchanged are excluded (see [`DATA_LINEAGE.md`](DATA_LINEAGE.md)).

## 2. What validation has — and has NOT — been done

### ✅ Done
- **Face validity check.** Rule-derived Positive vs. Negative groups differ in
  the clinically expected directions (e.g. Negative group: higher INR/PTT, lower
  platelets, lower GCS), consistent with the labels capturing real signal rather
  than noise. See the notebook's descriptive tables (`ML_models_CT_head.ipynb`,
  cohort-summary cells).
- **Negation handling built into the rules** (the Positive branch explicitly
  excludes "no / without / chronic / prior" hemorrhage/fracture/etc.).

### ❌ Not done (the key gap)
- **No clinician-adjudicated gold standard.** The regex labels have **never been
  compared against manual, expert labels.**
- **No reported accuracy metrics** for the labeler (no sensitivity, specificity,
  PPV, NPV, or confusion matrix vs. a ground truth).
- **No inter-rater agreement** (no second annotator, no Cohen's / Fleiss' κ).
- **No manual annotation artifact exists in the repo.** (What is sometimes
  mis-remembered as "manual annotation" from the datathon was the manual
  *variable-to-itemid mapping* in `Datathon-DataTracking.xlsx` and the manual
  *authoring of the regex rules* — neither is a validated gold-standard label
  set.)

> This gap is acknowledged as a limitation in the datathon presentation
> ("Rule-based labeling of radiology reports, potential misclassification") and
> is flagged as the **#1 gap** in `Signal2Scan_Study_Design_v2` §4: *"the regex
> labels have no reported validation against a clinician-adjudicated ground
> truth … the single highest-value addition to the project."*

## 3. Label-validation plan  `[TO ADD — priority 1]`

Adapted from `Signal2Scan_Study_Design_v2` §4.1. This is the agreed procedure to
close the gap; it has **not been executed yet**.

1. **Gold set.** Draw a **stratified random sample of ~300–500 reports**,
   **over-sampling Positive and Unclear** so those classes are adequately
   represented.
2. **Codebook.** The physician lead signs off a written positive-finding
   codebook, including borderline handling (small stable subdural,
   microhemorrhage, chronic-only changes). `[DECISION — physician lead]`
3. **Double annotation.** **Two clinicians** label the gold set independently
   against the codebook; a **third resolves disagreements.**
4. **Agreement.** Report **Cohen's κ** (two raters) / **Fleiss' κ** (more).
5. **Pipeline metrics.** Compute the regex labeler's **sensitivity, specificity,
   PPV, NPV, and confusion matrix** vs. the adjudicated gold set — overall and
   **per positive subtype.**
6. **Acceptance gate.** Pre-specify a threshold (e.g. **κ ≥ 0.80**); if the
   labeler falls below it, **revise the rules before any modeling result is
   treated as final.** `[DECISION — physician lead sets threshold]`

### Open decisions blocking execution
- [ ] Physician lead signs off the positive-finding **codebook** + borderline rules.
- [ ] Physician lead sets the **κ acceptance threshold**.
- [ ] Confirm **who** the two annotators + adjudicator are.
- [ ] Decide handling of **Unclear (169)** and **Post-surgical/Unchanged (82)**
      in the gold set and in the reported metrics.

## 4. Why this matters

The outcome label is the foundation of every downstream result — the model
metrics (AUROC/AUPRC/Brier), the SHAP predictor rankings, and the ICU-subgroup
findings all inherit whatever error the labeler carries. Until the labeler is
validated against expert ground truth, those results should be read as
**provisional**. The target venue (a medical-informatics / critical-care
journal) will scrutinize exactly this step, so closing it is a prerequisite for
write-up, not an optional extra.

---

*Status maintained alongside `DATA_LINEAGE.md`. Update this file when the
validation in §3 is executed — record the gold-set size, κ, and the labeler's
sensitivity/specificity/PPV/NPV here.*
