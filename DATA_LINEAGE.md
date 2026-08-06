# Data Lineage — Signal2Scan

This document traces every dataset in the project from its source (MIMIC-IV) to
the final analysis file, describing exactly how each intermediate artifact is
produced. It is the reference for reproducing the cohort and for reviewers /
readers who need to understand how the labels and features were derived.

> **Data access note.** All patient-derived files below come from **MIMIC-IV**, a
> credentialed, de-identified critical-care database. Access requires CITI
> training and a signed PhysioNet Data Use Agreement. Per the DUA, none of the
> real-patient CSVs are redistributable — they are `.gitignore`d and never
> pushed. Only the synthetic/example file and tracking spreadsheet are public.

---

## Source

| Source | Detail |
|--------|--------|
| **Database** | MIMIC-IV (Beth Israel Deaconess Medical Center ICU) |
| **Access** | Google BigQuery — `physionet-data.mimiciv_*` |
| **Note tables** | `mimiciv_note.radiology`, `mimiciv_note.radiology_detail` |
| **Clinical tables** | ICU chart/lab/med tables (chartevents, labevents, etc.) |

---

## Pipeline overview

```
MIMIC-IV (BigQuery)
        │
        ├──[SQL 1: report labeling]────────────► CT labels  (Negative / Positive / …)
        │                                          Classifying CT reports.sql
        │
        └──[SQL 2: feature extraction]─────────► 4-hour pre-scan structured features
                                                   signal2scan_feature_extraction_4h.*
        │
        ▼
   merge labels + features, apply cohort exclusions
        │
        ▼
   final_ct_head_dataset.csv   (4,638 rows × 57 cols)
        │
        ▼
   notebook filtering + preprocessing (ML_models_CT_head.ipynb, CELL 1)
        │
        ▼
   4,387 Positive/Negative rows → GroupShuffleSplit → 5 models + SHAP
```

---

## Step 1 — Label CT reports (rule-based NLP)

**Script:** [`Final dataset and code/Classifying CT reports.sql`](Final%20dataset%20and%20code/Classifying%20CT%20reports.sql)

- Pull radiology reports from `mimiciv_note.radiology` joined to
  `radiology_detail`, keeping only three head-CT types:
  `CT HEAD W/O CONTRAST`, `CT HEAD W/ & W/O CONTRAST`, `CT HEAD W/ CONTRAST`.
- Apply **regular expressions** over the `IMPRESSION` / `FINDINGS` sections to
  assign each report a class:

  | Label | Rule (summary) |
  |-------|----------------|
  | **Negative** | "no acute intracranial", "unremarkable", chronic-only changes, … |
  | **Positive** | hemorrhage / infarct / fracture / mass effect / edema / hydrocephalus …, **with negation handling** (excludes "no / chronic / prior" matches) |
  | **Post-surgical / Unchanged** | "postoperative", "craniotomy", "unchanged from prior", … |
  | **Unclear** | none of the above matched confidently |

- Positive scans are further sub-typed: Hemorrhage, Infarct, Fracture, Mass
  Effect, Hydrocephalus.
- `ROW_NUMBER()` assigns a per-patient, per-admission CT sequence number.

**Output:** CT-level labels (the `ct_classification` column downstream).

## Step 2 — Extract pre-scan structured features (4-hour window)

**Script:** [`results/signal2scan_feature_extraction_4h_sql_query.txt`](results/signal2scan_feature_extraction_4h_sql_query.txt)

For each CT order, structured clinical features are aggregated from the
**4-hour window immediately preceding the scan**:

- **Neurological:** GCS (eye / verbal / motor / total), RASS, pupil size &
  reactivity (NPi), CAM-ICU delirium items, seizure flags
- **Vitals:** MAP, systolic BP, heart rate, SpO₂, respiratory rate, temperature
- **Labs:** INR, PTT, platelets, sodium, glucose (+ coagulopathy / hyponatremia flags)
- **Medications:** new vasopressor, new antiepileptic
- **Context:** ICU type, shift, hours since ICU admission, demographics (age, sex, race)

**Output:** `signal2scan_feature_extraction_4h.csv` (17,314 rows of raw features).

## Step 2b — ⚠️ Two labeler versions: a 21% label discrepancy

**The two SQL scripts above each contain their own copy of the labeling CASE
expression, and the copies are not identical.** Anyone joining the two files will
find the same scan carrying two different labels. This is expected, not a bug in
the join — but it must be understood before using either file.

| Script | Regex scope | Window | Resulting Negative % |
|---|---|---|---|
| `Classifying CT reports.sql` (→ **final dataset**) | `IMPRESSION` **or** `FINDINGS` | 800 chars | **72.9%** |
| `signal2scan_feature_extraction_4h_sql_query.txt` | `IMPRESSION` only | 500 chars | 24.8% |

`Negative` is the **first** branch of the CASE, so a wider search window makes a
Negative match more likely to fire first. The wider version therefore labels far
more scans Negative.

**Measured effect** (inner join on `subject_id, hadm_id, stay_id, ct_order_time`;
all 4,638 rows match):

- **978 rows (21.1%) carry different labels** — 864 (19.7%) within the
  Positive/Negative modeling subset.
- The disagreement is **entirely one-directional**: no scan labelled Positive in
  the final dataset is labelled Negative by the 4-hour file. 372 final-Negative
  scans are Positive in the 4-hour file.
- Positive rate: **21.6%** (final) vs **65.6%** (4-hour file).

**Which one is authoritative:** the **final dataset** (`Classifying CT
reports.sql`). A 65.6% positive rate for ICU head CT is not clinically plausible,
and the narrower `IMPRESSION`-only/500-character window misses negation phrasing
that appears later in the report or under `FINDINGS`.

> **This does not mean the final labels are correct** — only that they are the
> ones every downstream artifact and the paper draft are built on. Neither
> labeler has been validated against clinician-adjudicated ground truth, and the
> fact that two plausible regex variants disagree on a fifth of the cohort is
> itself evidence for why that validation is the project's blocking task. See
> [`LABELING.md`](LABELING.md).

**Practical rule:** use `signal2scan_feature_extraction_4h.csv` for *features
only*; take `ct_classification` from `final_ct_head_dataset.csv`.

## Step 3 — Merge & apply cohort exclusions

Labels (Step 1) and features (Step 2) are joined at the CT-order level. Patients
whose **admission diagnosis is itself a neurological indication for CT** (trauma,
stroke, tumor, CNS infection, hydrocephalus, post-neurosurgery, seizure, anoxic
injury, …) are excluded so the model does not simply learn that structural
neurological disease predicts imaging. Exclusion ICD-9/ICD-10 lists are in
[`ICD codes to exclude.docx`](ICD%20codes%20to%20exclude.docx).

> ⚠️ **The exclusion is incomplete.** 393 CT orders (9.0% of the modeling
> subset) still come from the three neuro units — Neuro Stepdown (n=161, 70%
> positive), Neuro Intermediate (n=171, 59%), Neuro SICU (n=61, 49%) — against a
> cohort-wide positive rate of 22.9%. The exclusion is defined on *admission
> diagnosis*, so a patient admitted for a non-neurological reason and later
> transferred to a neuro unit survives it. `e09` part P4 quantifies how much the
> results depend on these rows. `[DECISION — physician lead: exclude by care unit
> as well as by admission diagnosis?]`

**Output:** **`final_ct_head_dataset.csv`** — the analysis dataset.

| Property | Value |
|----------|-------|
| Rows (CT orders) | **4,638** |
| Columns | 57 |
| Unique patients | 3,649 |
| Unique admissions | 3,819 |
| Class distribution | Negative 3,383 · Positive 1,004 · Unclear 169 · Post-surgical/Unchanged 82 |

## Step 4 — Notebook filtering & preprocessing

**Notebook:** [`Final dataset and code/ML_models_CT_head.ipynb`](Final%20dataset%20and%20code/ML_models_CT_head.ipynb) (CELL 1)

1. **Restrict to binary task** — keep only `Positive` / `Negative`:
   4,638 → **4,387 rows** (drops 169 Unclear + 82 Post-surgical/Unchanged).
2. **Drop high-missingness / identifier columns** —
   `npi_*` (100% missing), `temp_max` (94%), `pco2_max` (75%), `map_min` (60%),
   `sbp_max` (37%), pupil sizes, and free-text/id columns.
3. **Add missingness flags** for `inr`, `ptt`, `gcs_total_min`, `rass_last`
   before imputation.
4. **Impute** (numeric: median; categorical: most-frequent), **standardize**,
   **one-hot encode**.
5. **Patient-level split** — `GroupShuffleSplit(test_size=0.2)` on `subject_id`
   to prevent the same patient appearing in both train and test (no leakage).
   → Train 3,519 rows (23.2% positive) · Test 868 rows (21.7% positive).

## Step 5 — Modeling

Five classifiers are trained and compared (Logistic Regression, Random Forest,
Gradient Boosting, SVM, KNN), evaluated with **AUROC, AUPRC, accuracy, and Brier
score**, and interpreted with **SHAP**. See the notebook and `README.md`.

---

## Artifact inventory

| File | Rows | Stage | Tracked in git? |
|------|------|-------|-----------------|
| `mimitc-ct-head-example.csv` | 230,181 | Raw CT report text extract | 🔒 no (DUA) |
| `bquxjob_*.csv` | 4,638 | BigQuery export of CT labels | 🔒 no (DUA) |
| `dataset_v2.csv` | 4,638 | Intermediate structured dataset | 🔒 no (DUA) |
| `signal2scan_feature_extraction_4h.csv` / `.xlsx` | 17,314 | 4h feature extraction output | 🔒 no (DUA) |
| `signal2scan_feature_extraction_4h_100.csv` | 100 | Sample of the above | 🔒 no (DUA) |
| **`final_ct_head_dataset.csv`** | **4,638** | **Final analysis dataset** | 🔒 no (DUA) |
| `mimic_ct_head_synthetic.csv` | 288 | Synthetic report examples | ✅ yes (public) |
| `Datathon-DataTracking.xlsx` | — | Variable / progress tracking | ✅ yes (public) |

> **Path note.** The notebook reads `final_ct_head_dataset.csv` by relative path,
> so it must be run from `extracted/team2-ZZZ Lab/Final dataset and code/`, where
> the real (git-ignored) data lives.
