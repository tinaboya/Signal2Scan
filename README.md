# Signal2Scan

**Can routine ICU data predict CT Head outcomes?**

Signal2Scan asks whether routinely collected ICU clinical data can predict whether a head CT scan will be clinically informative — helping distinguish patients who need urgent imaging from those unlikely to benefit. The goal is to support evidence-based imaging decisions that reduce unnecessary radiation exposure and transport risk for unstable patients, while preserving rapid imaging access for high-risk cases.

This work was developed by team **Signal2Scan** for the Mayo Clinic Datathon, using the [MIMIC-IV](https://physionet.org/content/mimiciv/) critical care database.

## Clinical motivation

Head CTs are frequently ordered in the ICU, but a large fraction return no acute findings. Predicting the likely yield of a scan from data already in the chart could:

- **Improve patient safety** — reduce unnecessary radiation and avoid risky transport of unstable patients.
- **Support smarter decisions** — evidence-based ordering, less defensive imaging when diagnostic yield is low.
- **Optimize resources** — preserve rapid imaging capacity for patients most likely to benefit.

## Approach

The pipeline has two main stages: labeling CT reports from free text, and predicting those labels from structured ICU data captured *before* the scan.

### 1. Labeling CT reports (SQL / NLP)

Radiology reports for head CTs (`CT HEAD W/O CONTRAST`, `CT HEAD W/ & W/O CONTRAST`, `CT HEAD W/ CONTRAST`) are pulled from the MIMIC-IV note tables and classified with rule-based regular expressions over the `IMPRESSION` / `FINDINGS` sections into:

| Label | Definition |
|-------|------------|
| **Negative** | No acute intracranial findings (e.g. "no acute abnormality", "unremarkable", chronic-only changes) |
| **Positive** | Acute findings — hemorrhage, infarct, fracture, mass effect, midline shift, edema, hydrocephalus, etc. (with negation handling) |
| **Post-surgical / Unchanged** | Post-operative or unchanged-from-prior studies |
| **Unclear** | Could not be confidently classified |

Positive scans are further sub-typed (Hemorrhage, Infarct, Fracture, Mass Effect, Hydrocephalus). See `Classifying CT reports.sql` and `results/signal2scan_feature_extraction_4h_sql_query.txt`.

### 2. Feature extraction

For each CT order, structured features are aggregated from the **4-hour window preceding the scan**, including:

- **Neurological:** GCS (eye / verbal / motor / total, with delta from baseline), RASS sedation, pupil size & reactivity, CAM-ICU delirium, seizure flags
- **Vitals:** MAP, systolic BP, heart rate, SpO₂, respiratory rate, temperature
- **Labs:** INR, PTT, platelets, sodium, glucose (plus coagulopathy / hyponatremia flags)
- **Medications:** new vasopressor, new antiepileptic
- **Context:** ICU type, shift, hours since ICU admission, demographics (age, sex, race)

Patients whose admission diagnosis is itself a neurological indication for CT (trauma, stroke, tumor, CNS infection, hydrocephalus, post-neurosurgery, seizure, anoxic injury, etc.) are excluded so the model does not simply learn that structural neurological disease predicts imaging. The exclusion ICD-9 / ICD-10 code lists are in `ICD codes to exclude.docx`.

### 3. Modeling

The classification task focuses on **Positive vs. Negative** scans. Columns with high missingness (e.g. pupillometry, temperature, PCO₂, MAP) are dropped. Several models are compared with grouped train/test splits (`GroupShuffleSplit` on patient ID to prevent leakage):

- Logistic Regression
- Random Forest
- Gradient Boosting
- Support Vector Machine
- K-Nearest Neighbors

Models are evaluated with **AUROC, AUPRC, accuracy, and Brier score** (calibration), and interpreted with **SHAP** feature importance. See `Final dataset and code/ML_models_CT_head.ipynb`.

## Key findings

Across the labeled cohort, the CT classification distribution was roughly:

| Class | Count |
|-------|-------|
| Negative | 3,383 |
| Positive | 1,004 |
| Unclear | 169 |
| Post-surgical / Unchanged | 82 |

Notable signal directions from the models:

- Higher **PTT, INR**, and **low platelets** → more likely **Negative** CT
- Lower **GCS motor and verbal** → more likely **Positive** CT
- Higher **respiratory rate** → more likely **Positive** CT

## Repository structure

```
.
├── README.md
├── datathon_codes.ipynb                 # Exploratory analysis & early models
├── Datathon-DataTracking.xlsx           # Variable / progress tracking
├── predictive variables.docx            # Candidate predictors + MIMIC itemids
├── ICD codes to exclude.docx            # Cohort exclusion code lists
├── dataset_v2.csv                       # Intermediate structured dataset
├── bquxjob_*.csv                        # BigQuery export of CT classifications
├── mimic_ct_head_synthetic.csv          # Synthetic CT report examples
├── mimitc-ct-head-example.csv           # Example CT report extract
├── Final dataset and code/
│   ├── ML_models_CT_head.ipynb          # Final modeling notebook (models + SHAP)
│   ├── Classifying CT reports.sql       # Report-labeling SQL
│   └── final_ct_head_dataset.csv        # Final analysis dataset
└── results/
    ├── signal2scan_feature_extraction_4h.csv / .xlsx
    ├── signal2scan_feature_extraction_4h_100.csv   # 100-row sample
    └── signal2scan_feature_extraction_4h_sql_query.txt
```

## Data access & ethics

This project uses **MIMIC-IV**, a credentialed, de-identified database. Access requires completing CITI training and signing the PhysioNet data use agreement. Per the DUA, raw MIMIC patient data is **not redistributable** — any real-patient CSVs in this repository should be treated accordingly, and the synthetic / example files are provided for illustration only.

## Limitations

- Single-center data
- Class imbalance (Negative ≫ Positive)
- Missing data for several candidate predictors
- Rule-based labeling of radiology reports may introduce misclassification

## Future directions

- External validation across multiple institutions
- Prospective, real-time evaluation in clinical workflow
- Subgroup analysis by ICU type
- EHR integration with cost and safety analysis

---

*Team Signal2Scan · Mayo Clinic Datathon*
