# Signal2Scan — Project Primer

**Read this first.** It explains, from zero, what the project is asking and what
has actually been built.

Written for anyone joining the project: new collaborators, the CS student, the
clinical annotators, and the team itself. No prior context assumed.

Companion documents: [`STATUS.md`](STATUS.md) (what is in progress right now),
[`DATA_LINEAGE.md`](DATA_LINEAGE.md) (how each data file was made),
[`LABELING.md`](LABELING.md) (how outcome labels were made and what is unvalidated).

---

## 1. The clinical question

Head CT scans are ordered frequently in the ICU, and a large fraction come back
showing nothing acute. Every scan carries real cost: radiation, and — more
importantly for an ICU patient — the risk of physically transporting someone
unstable to the scanner and back.

> **Can data already in the chart, before the scan is ordered, predict whether
> that scan will show an acute finding?**

If it can, the deliverable is a **non-blocking flag**: at the moment a clinician
orders a head CT, the system marks requests that look *likely low-yield* for
optional second thought. Like a drug-interaction alert — advisory, never
removing the clinician's decision.

Two design commitments follow from the clinical setting:

1. **It must use only pre-scan data.** If a feature could be influenced by the
   scan's result, the prediction is circular and worthless in practice.
2. **It must almost never tell you to skip a scan that would have found
   something.** A missed intracranial hemorrhage is catastrophic; an unnecessary
   scan is merely wasteful. The two errors are not symmetric, and the tool is
   tuned accordingly (§5).

---

## 2. The data

Everything comes from **MIMIC-IV** — a de-identified database of ICU stays from
Beth Israel Deaconess Medical Center, hosted on PhysioNet and queried through
Google BigQuery.

Access requires CITI training and a signed Data Use Agreement. **Under that DUA,
no patient-derived file may be redistributed.**

Two kinds of MIMIC-IV tables are used:

- **Radiology notes** — the free text of each head CT report. This is where the
  *outcome* comes from.
- **ICU clinical tables** — chartevents (vitals, neuro scores), labevents
  (bloodwork), medication tables. This is where the *predictors* come from.

---

## 3. How it works

```
          radiology notes (mimiciv_note.radiology)
                          │
                          │  keep head CT reports
                          ▼
                 one row per CT order
              (patient, admission, scan time)
                          │
            ┌─────────────┴──────────────┐
            │                            │
   ① label the report text      ② for each order, pull ICU
      (regex over the report)      data from the 4h BEFORE it
            │                            │
            ▼                            ▼
     Positive / Negative /        GCS, RASS, vitals, labs,
     Unclear / Post-surgical      meds, unit context
            │                            │
            └─────────────┬──────────────┘
                          ▼
             17,314 CT orders (features + label)
                          │
                          │  ③ exclude neurological admissions
                          ▼
                      4,638 orders
                          │
                          │  keep Positive/Negative only;
                          │  drop high-missingness columns
                          ▼
                 4,387 rows × 42 features
                          │
                          │  train, evaluate, interpret
                          │  (splits grouped by patient)
                          ▼
               probability → threshold → the flag
```

The radiology notes define the **rows**; the ICU tables only supply **columns**
for rows that already exist. Aggregating the 4 hours before a scan requires
knowing when it was ordered, so the feature-extraction query reads the radiology
table too — which is why it carries its own copy of the labelling logic, and why
two versions of that logic exist ([`DATA_LINEAGE.md`](DATA_LINEAGE.md) §2b).

### ① Labeling: turning a report into Positive or Negative

A radiology report is prose. Something has to decide whether it describes an
acute finding. Currently that "something" is a set of **regular expressions** —
text patterns — applied to the report's IMPRESSION and FINDINGS sections:

| Label | Rule, in plain terms |
|---|---|
| **Negative** | The text contains a phrase like "no acute intracranial", "unremarkable", "normal head CT", or describes only chronic changes |
| **Positive** | The text contains a finding word — hemorrhage, infarct, fracture, mass effect, edema, hydrocephalus — **and** is not negated ("no", "without", "chronic", "prior") |
| **Post-surgical / Unchanged** | "postoperative", "craniotomy", "unchanged from prior" |
| **Unclear** | None of the above matched confidently |

Order matters: Negative is checked **first**, so a report matching both a
negation phrase and a finding word is labelled Negative.

**Result:** 4,638 CT orders — 3,383 Negative, 1,004 Positive, 169 Unclear, 82
Post-surgical. Modeling uses only the **4,387 Positive/Negative** rows.
Positive rate: **22.9%**.

### ② Features: the 4-hour pre-scan window

For each CT order, clinical data is aggregated over the **4 hours immediately
before the scan** — a snapshot of what the clinician could have seen when
deciding to order it.

After dropping columns that are mostly empty, **42 features** remain:

- **Neurological** — GCS (eye/verbal/motor/total), RASS sedation score, CAM-ICU
  delirium items, seizure and altered-consciousness flags
- **Vitals** — heart rate (min/max), SpO₂, respiratory rate
- **Labs** — INR, PTT, platelets, sodium, glucose, plus coagulopathy and
  hyponatremia flags
- **Events / meds** — cardiac arrest, respiratory arrest, fall, new vasopressor,
  new antiepileptic
- **Demographics** — age, sex, race
- **Missingness indicators** — four flags recording whether INR, PTT, GCS, or
  RASS was measured at all. *That a test was ordered is itself information.*

**What was dropped:** pupillometry (~100% missing),
temperature (94%), pCO₂ (75%), MAP (60%), systolic BP (37%). Also dropped:
`first_careunit`, `shift`, `icu_hour_at_ct`. That last group was dropped
deliberately: they describe *context*, not physiology.

**Cohort exclusion.** Patients admitted *for* a neurological reason (trauma,
stroke, tumor, CNS infection, post-neurosurgery) are excluded. Otherwise the
model would just learn "brain disease predicts brain imaging," which is true and
useless. This exclusion is currently incomplete — see
[`DATA_LINEAGE.md`](DATA_LINEAGE.md) §3.

### ③ Modeling

Five standard classifiers, trained on the 42 features to predict the label.

**Splits are grouped by patient.** A patient with three CT scans has all three in
training or all three in testing, never split across. Otherwise the model could
memorize a patient and be scored on recognizing them again — inflated,
meaningless performance.

**Results** (20 repeats × 5-fold patient-grouped cross-validation, `e02`):

| Model | AUROC | AUPRC |
|---|---|---|
| **Random Forest** | **0.778** [0.744, 0.809] | **0.534** [0.457, 0.620] |
| Gradient Boosting | 0.770 | 0.514 |
| SVM | 0.770 | 0.518 |
| Logistic Regression | 0.751 | 0.474 |
| KNN | 0.690 | 0.381 |

Flexible models beat logistic regression only slightly, which points toward a
simple, deployable tool rather than a complex one.

---

## 4. The label audit

We ran a large language model (Qwen3.5) over the reports as a second opinion on
the regex labels, to see how much a different labeler disagrees and where.

Of 7,671 reports where both labelers returned Positive or Negative, they **agreed
on 78.9%** (6,052). The disagreement falls into two cells:

| | LLM Negative | LLM Positive |
|---|---|---|
| **regex Negative** | 4,587 | **654** |
| **regex Positive** | **965** | 1,465 |

**A disagreement does not tell you who is wrong.** Neither labeler has been
checked against a human expert. The regex is a set of text patterns. The LLM is a
model, and its prompt was written to catch missed findings, which pushes it toward
Positive — so the 654 are not proven regex errors, and the larger 965 cell should
not be ignored either.

Spot-checks show one way the regex can fail: a report that says *"no hemorrhage"*
but also describes a real infarct is labelled Negative, because the negation
matches first. We have seen this in a few reports. We have not measured how often
it happens.

**This shifted what the project is about** — from "can we predict head CT yield"
to "how good are the labels we measure against." Only clinician labels can settle
who is right, and only they can show whether the model is clinically accurate
rather than just agreeing with a text matcher.

The audit is still useful: nobody can review 7,671 reports, and the disagreements
point to the few hundred worth a clinician's time. The gold sample (`e08`) is
drawn from them.

---

## 5. The flag

The model outputs a probability; the tool needs a yes/no. That means picking a
threshold, and where to put it is a safety decision.

The rule: **flag as many requests as possible, as long as no more than 5% of
truly positive scans get flagged** (95% sensitivity).

On the current labels (`e07`), that threshold is 0.213: it flags **17.5% of
requests** and misses **5.0% of true positives**. About one request in six gets a
second look, at the cost of 1 in 20 positive scans being flagged — and the flag
is advisory, so a clinician who disagrees just orders the scan.

---

## 6. Questions newcomers ask

**Why not just use an LLM to label everything and skip the regex?**
That is exactly what the audit did — and it disagreed with the regex on 21% of
reports. But an LLM is also an unvalidated labeler; swapping one for another
without a human gold standard just changes which errors you have. The LLM's role
here is to *find candidate errors* cheaply so clinicians spend their scarce time
on the reports most likely to be mislabelled.

**The model gets 0.78 AUROC — isn't that good enough to be useful?**
Two problems. Roughly half of it is case mix ([`STATUS.md`](STATUS.md) §3), and
inside the medical ICUs
where most scans happen, the model is near 0.54. Also 0.78 is measured against
labels that are ~20% in dispute.

**Why is the clinician annotation only ~450 reports?**
It is a stratified sample, deliberately over-weighting the regex/LLM
disagreements — the reports most informative about where the labeler fails. 450 is
enough to estimate sensitivity/specificity with usable confidence intervals while
staying a realistic ask (~30 minutes per batch of 80).

**Can I start on the modeling improvements now?**
Better models, new features, and label-cleaning methods are all sensible and all
deliberately deferred ([`STATUS.md`](STATUS.md) §7). Tuning against labels that
are 20% in dispute optimizes noise, and the work would be redone once the labels
settle. The analyses that are *not* label-dependent — case mix, calibration, the
ED-rule benchmark — can proceed today.

**What is actually blocking everything?**
The clinician gold labels. One task, not yet started, gating 13 of 19 open items.
