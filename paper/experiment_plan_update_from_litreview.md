# Experiment Plan Update — informed by the clinical literature review

*Companion to `Signal2Scan_Study_Design_v2`. This file records what the team's
47-article literature review (`literature_review/`) changes about the planned
experiments. It does not replace the study design; it adds and re-prioritizes
experiments that the review now makes both possible and expected by reviewers.*

**Source of truth:** `literature_review/final_articles_formatted_by_year_and_relevance__june2026.xlsx`
(47 curated articles) + `signal2scan_litreview_summary.docx`.

---

## What the review establishes (and why it changes the plan)

1. **The field is ED-centric and rule-based.** 26/47 studies are ED; only 8 are
   ICU. **None uses machine learning / a multivariable predictive model on
   structured data.** → Strengthens the novelty framing; also means our *only*
   fair external comparators are hand-built clinical scores, not prior ML.
2. **There is a field benchmark to beat/contextualize:** Orlando meta-analysis —
   **98.4% sens / 17.9% spec, 16.2% CT reduction** [Cassidy 2025].
3. **There are ICU yield anchors** that validate our cohort: Chokshi 2016
   (22.8% AMS yield ≈ our 21.6% positive rate), Khan 2014 (12.1%), Purmer 2012
   (51% mixed), Balachandran 2009 (low yield in nonfocal exams).
4. **The recurring predictors across rules are known and mostly available to us:**
   focal neurologic deficit, GCS < 14/15, malignancy, nausea/vomiting,
   **coagulopathy/anticoagulant use**, headache, age, dilated pupils.

---

## NEW / RE-PRIORITIZED experiments

### E1. Benchmark against established clinical decision rules  `[NEW — high value]`
The single most reviewer-persuasive addition the review unlocks.
- Re-implement 1–2 ED rules on our ICU cohort using our features as proxies —
  **Rothrock/Orlando** (age ≥ 60, focal deficit, headache+vomiting, AMS) and
  **Scott-King** (focal deficit, GCS < 15, malignancy, vomiting, coagulopathy,
  headache). Map each rule variable to the closest feature we have; document
  every proxy and any variable we cannot represent.
- Report each rule's **sensitivity / specificity / PPV / NPV / net benefit** on our
  ICU cohort, side-by-side with our model. Expected story: ED rules keep high
  sensitivity but **very low specificity** in the ICU (consistent with Orlando's
  17.9%), and a learned model shifts the operating point.
- [DECISION] Which rules are faithfully reproducible from MIMIC-IV structured
  data? Any rule requiring un-captured variables (e.g. "headache" in a sedated
  patient) is reported as a limitation, not silently dropped.

### E2. Report yield in the ICU-yield-literature frame  `[NEW — easy, expected]`
- Report our cohort's positive rate **overall and by ICU type / indication
  signal**, and explicitly compare to Chokshi (22.8%), Khan (12.1% overall;
  30% focal, 16.2% seizure, 7.4% AMS), Purmer (51%), Balachandran.
- This both validates cohort construction and positions our numbers in the known
  ICU range — cheap credibility.

### E3. Predictor concordance check (SHAP vs. literature)  `[NEW — interpretation]`
- Cross-tabulate our SHAP-important predictors against the literature's recurrent
  predictors (focal deficit, GCS, coagulopathy, age, malignancy, vomiting).
- **Where we agree** (e.g. GCS depression → positive) → reinforces validity.
- **Where we disagree** — notably our **coagulopathy → *Negative*** direction,
  which *inverts* the literature's coagulopathy→positive association — becomes a
  headline discussion point, framed as a selection/collider effect (Study Design
  §8). The review makes this contrast explicit and therefore mandatory to explain.

### E4. Feature-set ablation motivated by known predictors  `[NEW — optional]`
- Compare a **"literature-predictor-only" model** (just the variables ED rules
  use, as available) against our **full pre-scan feature set**. Quantifies the
  added value of routine ICU structured data beyond the classic checklist —
  a direct, interpretable argument for the ICU/structured-data contribution.

---

## Experiments already planned in the Study Design — now RE-ORDERED

The review does not remove any prior task; it sets their order. Recommended
priority for a Proceedings submission:

| # | Task | Source | Priority |
|---|------|--------|----------|
| P1 | **Label validation** vs. clinician gold standard (κ, sens/spec) | Study Design §4.1 · `LABELING.md` | 🔴 blocking |
| P2 | **Repeated/nested CV + 95% CIs** (replace single split) | Study Design §6/§7 | 🔴 blocking |
| P3 | **E1 — benchmark vs. ED clinical rules** | this doc | 🟠 high (novelty proof) |
| P4 | **Calibration + decision-curve analysis** | Study Design §7 | 🟠 high |
| P5 | **E3 — coagulation-direction clinical interpretation** | this doc · Study Design §8 | 🟠 high (reviewer flag) |
| P6 | E2 — yield in literature frame; E4 — feature ablation | this doc | 🟡 medium |
| P7 | Sensitivity analyses (label handling, imputation, fairness) | Study Design §7.1 | 🟡 medium |

---

## Open decisions the review surfaces (for the next meeting)
- [ ] Which clinical decision rules to reproduce in E1, and how to map each rule
      variable to a MIMIC-IV feature (physician lead sign-off on proxies).
- [ ] Whether to frame the primary result as **"beats/complements ED rules in the
      ICU"** (needs E1) or **"first ICU structured-data model"** (needs only E2).
- [ ] Confirm the coagulation-direction interpretation before it goes in the paper.

*Maintained alongside the paper draft (`paper/ml4h_signal2scan_draft.md`) and the
study design. Update priorities as blocking items close.*
