# Physician Review — CT Label Definition & LLM Prompt

**For:** clinical lead(s)
**Why this matters:** the definition of "Positive" is a clinical judgment, not an
engineering choice. Every downstream result (model performance, SHAP predictors,
the counterintuitive coagulation finding) rests on it. This document asks you to
sign off — or correct — how a head CT is labeled. Please comment inline.

Context: our rule-based (regex) labeler was never validated. As a screening step
we ran a large LLM (Qwen3.5-397B) over all **7,737** real reports as a "second
opinion." It disagreed with the regex labels on ~21%, and flagged **654** reports
that the regex called *Negative* but the LLM called *Positive* — suspected
**false negatives**. Spot checks confirm the pattern: a report saying *"no acute
hemorrhage"* **plus** a real finding (e.g. a fracture or infarct) was mislabeled
Negative by the regex. We need you to (a) confirm the label definitions and
(b) adjudicate a sample of these disagreements.

---

## 1. The exact LLM prompt used (please review the wording)

> You are labeling a head CT radiology report. Based ONLY on the IMPRESSION and
> FINDINGS, classify the scan as exactly one word: **'Positive'** if it shows an
> ACUTE clinically significant intracranial finding (hemorrhage, infarct, acute
> fracture, mass effect, midline shift, acute edema, hydrocephalus), or
> **'Negative'** if there is no acute finding. **Even if the report also says
> 'no hemorrhage', answer Positive if ANY acute finding is present.** Answer with
> only the single word.

**⚠️ Known bias to flag:** the sentence in **bold** deliberately pushes the model
toward Positive to catch the regex's false negatives. This makes the LLM a good
*screening* tool but means its raw Positive count is likely an over-estimate.
It is **not** a substitute for your adjudication.

**Your comments on the prompt wording:**
> _[physician: is this clinical definition of "acute clinically significant" correct? edit here]_

---

## 2. Definition mismatch to resolve  ⬅ key decision

The LLM prompt and the SQL regex labeler use **different** lists of what counts as
Positive. Please decide the canonical list.

| Finding | In SQL labeler? | In LLM prompt? | Positive? (physician) |
|---|:---:|:---:|:---:|
| hemorrhage / hematoma / bleed | ✅ | ✅ | ☐ yes ☐ no |
| infarct / ischemia | ✅ | ✅ | ☐ yes ☐ no |
| fracture | ✅ (any) | ✅ (**acute** only) | ☐ any ☐ acute only |
| mass effect / midline shift / herniation | ✅ | ✅ | ☐ yes ☐ no |
| edema | ✅ (any) | ✅ (**acute** only) | ☐ any ☐ acute only |
| hydrocephalus | ✅ | ✅ | ☐ yes ☐ no |
| **abscess** | ✅ | ❌ | ☐ yes ☐ no |
| **tumor / mass** | ✅ | ❌ | ☐ yes ☐ no |
| **pneumocephalus** | ✅ | ❌ | ☐ yes ☐ no |
| **hypoxic brain injury** | ✅ | ❌ | ☐ yes ☐ no |

**Borderline handling** (please specify, per `LABELING.md`):
- Small / stable chronic subdural: ☐ Positive ☐ Negative
- Microhemorrhage: ☐ Positive ☐ Negative
- Chronic-only infarct / chronic small-vessel disease: ☐ Positive ☐ Negative
- Post-surgical / unchanged-from-prior: ☐ separate class ☐ exclude ☐ ___

---

## 3. What we need from you (the physician TODO)

1. **Sign off / correct the Positive definition** (Section 2 table + borderline rules).
2. **Adjudicate a gold-standard sample.** We will hand you a stratified sample
   (~300–500 reports, over-sampling Positive and the 654 disagreements). You label
   Positive/Negative against the agreed definition; a second clinician labels
   independently; a third resolves ties. → yields **Cohen's κ** + the regex
   labeler's **sensitivity / specificity / PPV / NPV**.
3. **Set the acceptance threshold** below which the labeler must be revised
   (e.g. κ ≥ 0.80).
4. **Interpret the coagulation finding** (higher INR/PTT/low platelets →
   *Negative* CT) — is this a real signal or a selection/collider artifact,
   possibly worsened by the label errors above?

**These four items gate publication.** Until they are done, all model results are
provisional.

---

## 4. What is ready for you now

- `outputs/e05_disagreements_for_review.csv` — the **654 suspected false
  negatives** (regex=Negative, LLM=Positive), full report text included, for
  adjudication.
- `outputs/e05_llm_vs_regex.csv` — LLM vs regex label for all 7,737 reports.
- `LABELING.md` — the full label-validation protocol this feeds into.
