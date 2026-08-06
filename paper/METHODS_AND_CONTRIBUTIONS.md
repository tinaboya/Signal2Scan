# Signal2Scan — Methods & Contributions (team alignment, v1)

**Purpose.** One page to lock what this paper claims, so the team, the clinical
lead, and the analysis all point the same way. The predictive model is **not**
the contribution — it is a component used as evidence. Comment inline.

---

## The re-framed thesis

> ICU head CT is often low-yield, but there is no ICU-specific tool to support
> *appropriateness* at ordering time. Building one requires trustworthy outcome
> labels — and we show that the rule-based labels this field routinely relies on
> are systematically wrong in a way that would make such a tool **flag the wrong
> patients**. We therefore (A) audit and correct the labels with an LLM-assisted
> procedure, (B) build a safe, high-sensitivity appropriateness-flagging method
> on the corrected labels, and (C) show that skipping the audit produces an
> unsafe tool. Label auditing is a *prerequisite* for clinically usable decision
> support, not an optional extra.

Working title:
*"Safe Appropriateness Flagging for ICU Head CT: Why Label Auditing Is a
Prerequisite for Clinically Usable Decision Support."*

---

## Three contributions (predictive model is a component, not a headline)

### A. LLM-assisted label audit  `[method]`
Rule-based (regex) labels are cheap and scalable but have a systematic failure
mode: a report saying "no hemorrhage" **plus** a real finding (infarct,
hydrocephalus) is mislabeled Negative. We use a strong LLM (Qwen3.5-397B) as an
independent second opinion over all 7,737 reports, and use the **disagreement
structure** to direct a limited expert-annotation budget to the highest-risk
reports, then measure the regex labeler's sensitivity/specificity/PPV/NPV and κ
against a clinician gold standard.
- **Evidence to produce:** LLM–regex agreement 78.9%; 654 suspected false
  negatives (12.5% of regex-Negatives); clinician-adjudicated error rates [pending].

### B. ICU head-CT appropriateness flag  `[clinical method — the headline]`
A **non-blocking, high-sensitivity, interpretable** flag: at ordering time, using
only pre-scan 4h structured data, mark a request as "predicted low-yield" for
optional review — like a drug-interaction alert. Design constraints:
1. **Advisory, not blocking** — never removes the clinician's decision.
2. **High-sensitivity operating point** — chosen so true positives are almost
   never flagged low-yield (missed-finding cost >> over-scan cost).
3. **Interpretable reason** — each flag cites its drivers (e.g. GCS unchanged
   from baseline, normal coagulation, no new deficit).
- **Evidence to produce:** decision-curve net benefit > scan-all / scan-none in
  the plausible threshold range; a stated operating point ("at 95% sensitivity,
  flags X% of requests, misses Y%").

### C. Dirty-vs-clean evidence  `[the stitch]`
Build the flag tool twice — on regex labels and on audited labels — and show the
regex-based tool flags the **wrong** patients (because its labels miscall true
positives as negative). This simultaneously proves the value of A and the
necessity of A for B.
- **Evidence to produce:** the coagulation direction (high INR/PTT → Negative)
  weakens or reverses under clean labels, i.e. a dirty-label artifact; and the
  flag tool's safety metrics differ materially between label sets.

---

## Why the predictive model is demoted
It is the machinery behind the flag, and the object of the dirty-vs-clean test —
but "AUROC 0.78" is not a contribution on its own (standard models, single
center, no external validation). Reported as: RF AUROC 0.778 [0.744, 0.809]
(repeated grouped CV), interpretable models near-equivalent.

---

## The one dependency that gates everything
```
Physician labels 450 stratified reports  ->  clean gold labels  ->  unlocks:
    A: audit sens/spec/PPV/NPV + kappa
    B: appropriateness flag decision curve + operating point
    C: dirty-vs-clean comparison (coagulation artifact)
```
Everything else (code, sampling sheet, figures) can be staged now so results
appear the moment labels return.

## Honest scope
This paper *proposes and shows promise on retrospective MIMIC-IV data*. Real
deployment needs prospective, multi-center validation — stated as future work,
not claimed here.

## Open decisions for the team / clinical lead
- [ ] Confirm the re-framing (audit + flag, not "a predictor").
- [ ] Positive-finding definition + borderline rules (see PHYSICIAN_REVIEW_labeling.md).
- [ ] Missed-finding vs over-scan cost ratio → sets the flag's operating point.
- [ ] Who annotates (2 clinicians + adjudicator) and when.
