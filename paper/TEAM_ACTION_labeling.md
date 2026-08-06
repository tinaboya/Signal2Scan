# Action Needed: Clinician Label Review (unlocks the paper)

**Who:** two clinical annotators + one adjudicator.
**Time:** ~450 short IMPRESSION reads, split across two annotators.
**Why it matters:** every remaining result in the paper is blocked on this. The
gold labels it produces unlock the label-audit metrics, the appropriateness-flag
evaluation, and the test of whether the coagulation finding is a label artifact.

---

## Background in three sentences

Our CT labels were assigned by regex over report text and never validated. A
large LLM (Qwen3.5-397B), used as a second opinion over all 7,737 reports,
disagreed on ~21% and flagged 654 reports the regex called Negative but that
appear Positive (e.g. a report saying "no hemorrhage" that also describes an
infarct). We now need clinicians to establish the ground truth on a stratified
sample so we can measure how wrong the regex labels actually are.

## What we need you to do

1. Open `outputs/e08_gold_sample_BLIND.csv` (450 reports). It is **blinded** — you
   will not see the regex or LLM labels, so your judgment is not primed.
2. For each row, fill four columns:
   - **TRUE_LABEL**: `Positive` or `Negative`. Positive = an acute, clinically
     significant intracranial finding.
   - **finding_type**: `acute`, `chronic-stable`, `post-surgical`, or `none`.
     This is the call the automated methods get wrong — a chronic or stable
     finding should usually be Negative for our purpose.
   - **confidence**: `high` or `low` (mark the ones you are unsure about).
   - **notes**: anything worth recording.
3. Two annotators do this **independently**. A third resolves disagreements.

We compute Cohen's κ between the two annotators, then score the regex labeler
against the adjudicated gold set (sensitivity, specificity, PPV, NPV).

## Before you start: two definitions to lock

These are in `PHYSICIAN_REVIEW_labeling.md` and need the clinical lead's sign-off:

- **What counts as Positive** — the regex and the LLM used slightly different
  lists (e.g. tumor, abscess, hematoma). Please confirm the canonical list.
- **Acute vs chronic/stable** — how to label "stable subdural," microhemorrhage,
  chronic-only infarct. This drives most of the disagreements.

## The sample (450 reports, why these)

Stratified across all four regex-vs-LLM cells so we can measure true error rates,
not just review disagreements:

| Cell (regex / LLM) | n in sample | purpose |
|---|---:|---|
| Negative / Positive | 150 | suspected false negatives (highest risk) |
| Positive / Negative | 150 | suspected false positives / chronic confusion |
| Negative / Negative | 100 | check for shared blind spots |
| Positive / Positive | 50 | check for shared false positives |

## What happens with your labels

Return the filled `e08_gold_sample_BLIND.csv`. We join it to the hidden key and
produce, in one pass:

1. Cohen's κ (annotator agreement) and the regex labeler's sensitivity /
   specificity / PPV / NPV.
2. The appropriateness-flag tool re-run on audited labels (its current numbers
   are preliminary, computed on the unaudited regex labels).
3. A test of whether the coagulation finding (high INR/PTT → Negative CT) is real
   or an artifact of the label errors.

## Files

- `outputs/e08_gold_sample_BLIND.csv` — the 450 reports to label (blinded).
- `PHYSICIAN_REVIEW_labeling.md` — the definitions to sign off first.
- `METHODS_AND_CONTRIBUTIONS.md` — how this fits the paper's three contributions.
- `outputs/llm_label_audit_report.html` (open in a browser) — the audit overview.
