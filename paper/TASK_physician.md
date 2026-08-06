# Task Brief — Clinical Annotators

**Goal of your part:** produce a small, trustworthy set of "gold-standard" CT
labels. These become the anchor that everything else in the project is validated
against, and that the prediction model is trained to trust. Without them the rest
cannot proceed.

**Effort:** ~450 short IMPRESSION reads, split between two annotators, plus a
third to resolve disagreements.

---

## Why this is needed (context in three sentences)

Our CT outcome labels were assigned automatically by text rules (regex) and were
never checked. A large language model, used as an independent second reader over
all 7,737 reports, disagreed on about 21% and flagged 654 that the rules called
Negative but that look Positive (e.g. a report saying "no hemorrhage" that also
describes an infarct). We need clinicians to set the truth on a representative
sample so we can measure how wrong the automatic labels are and give the modeling
team a clean anchor.

## What to do

1. Open `outputs/e08_gold_sample_BLIND.csv` (450 reports). It is **blinded** — the
   automatic labels are hidden so your judgment is not influenced.
2. For each row, fill four columns:
   - **TRUE_LABEL** — `Positive` or `Negative`. Positive = an *acute*, clinically
     significant intracranial finding.
   - **finding_type** — `acute`, `chronic-stable`, `post-surgical`, or `none`.
     This is the distinction the automated methods get wrong; a chronic or stable
     finding is usually Negative for our purpose.
   - **confidence** — `high` or `low`.
   - **notes** — anything worth recording.
3. Two annotators label **independently**. A third adjudicates disagreements.

## Two definitions to lock first (clinical lead sign-off)

See `PHYSICIAN_REVIEW_labeling.md` for the full form. Decide once, up front:
- **What counts as Positive** — the rule labeler and the LLM used slightly
  different finding lists (tumor, abscess, hematoma, etc.). Confirm the canonical
  list.
- **Acute vs chronic/stable** — how to treat "stable subdural," microhemorrhage,
  chronic-only infarct, post-surgical change. This drives most disagreements.

## The sample (why these 450)

Stratified across the four rule-vs-LLM agreement cells so we can estimate true
error rates, not just review the disagreements:

| Cell (rule / LLM) | n | purpose |
|---|---:|---|
| Negative / Positive | 150 | suspected missed findings (highest priority) |
| Positive / Negative | 150 | suspected over-calls / chronic confusion |
| Negative / Negative | 100 | catch errors both methods share |
| Positive / Positive | 50 | catch shared over-calls |

## What we produce from your labels

- Agreement between the two annotators (Cohen's κ).
- The rule labeler's sensitivity, specificity, PPV, NPV against your adjudicated
  labels — i.e. how trustworthy the automatic labels really are.
- A clean gold-standard set that the modeling team uses to train and validate the
  prediction tool.

## Deliverable
The filled `e08_gold_sample_BLIND.csv` from each annotator, plus the adjudicator's
resolutions. That is the hand-off to the modeling side.

## Files
- `outputs/e08_gold_sample_BLIND.csv` — the 450 reports to label.
- `PHYSICIAN_REVIEW_labeling.md` — definitions to sign off first.
- `outputs/llm_label_audit_report.html` — open in a browser for the audit overview.
