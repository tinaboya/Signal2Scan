# Task Brief — CS Student (Modeling)

**What you are building:** a prediction tool that estimates, from a patient's
pre-scan structured ICU data, whether an ordered head CT will show an acute
finding — and that is trained to be *robust to the fact that most of its training
labels are noisy*. The clinical form of the tool is a non-blocking
"predicted-low-yield" flag shown when a clinician orders a head CT.

**The technical novelty is not the model architecture** (standard classifiers are
fine). It is that the tool learns from **a large set of noisy rule-based labels +
a small set of clinician gold labels + a per-report "suspicious" signal from an
LLM**, jointly, instead of pretending the labels are clean.

---

## The data you get (the label interface)

Three label sources for the same reports:
1. **Noisy labels** — `outputs/e05_llm_vs_regex.csv` gives the regex label for
   ~4,600 modeled CT orders. Cheap, cover everything, systematically wrong in
   places (the "no hemorrhage but also an infarct" failure mode).
2. **Gold labels** — from the clinicians (450 reports, arriving as
   `e08_gold_adjudicated.csv`). Trustworthy but small.
3. **Disagreement / suspicion signal** — `outputs/e05_llm_vs_regex.csv` also has
   the LLM label per report; where LLM ≠ regex, the regex label is more likely
   wrong. Treat this as a noise-prior.

Features: `paper/reproduce/s2s/data.py` already builds X (pre-scan 4h structured
features), y (label), and patient groups. Reuse it.

## Build it in two stages

### Stage 1 — baseline (does NOT need the gold labels; start now)
Train the prediction tool the naive way and establish the reference numbers.
- Use the existing pipeline (`s2s/data.py`, `s2s/models.py`) — this already
  reproduces the datathon results (see `reproduce/experiments/e00_reproduce.py`
  and the CV in `e02_cross_validation.py`).
- Deliverable: repeated patient-grouped CV, AUROC/AUPRC/Brier, plus the
  high-sensitivity operating point already prototyped in
  `e07_appropriateness_flag.py`. This is your safety-net result.

### Stage 2 — the contribution (needs the gold labels; design now, run when they arrive)
Make the tool robust to label noise, combining all three label sources. Design and
compare at least two of:
- **Gold-anchored fine-tuning** — train on noisy labels, then correct/fine-tune
  on the gold subset.
- **Disagreement-weighted training** — down-weight (or relabel) samples where the
  LLM disagrees with the regex label; the LLM signal is your noise-prior.
- **Confident learning / label-error estimation** (see cleanlab) to prune or
  reweight likely-wrong labels, using the gold set to calibrate.
- **LLM soft labels** — use the LLM's judgment as a soft target where gold is
  absent.
Deliverable: show these beat the Stage-1 baseline **on the gold-labeled test
data**, and quantify how much the gold anchor helps.

### Safety constraint (the "safe tool" definition)
The flag must almost never call a true-positive scan "low-yield." Choose the
operating point under an explicit constraint like sensitivity ≥ 0.95, and report
the flag rate and missed-positive rate there (template in `e07`). "Safe" here is a
measurable guarantee: P(flag low-yield | truly positive) ≤ ε.

### Dirty-vs-clean experiment (ties the paper together)
Build the flag tool twice — once trained on regex labels, once on gold/robust
labels — and report how many patients the regex-trained tool would wrongly flag as
low-yield that the clean tool does not. This is the evidence that label auditing is
a prerequisite for a safe tool.

## Reading list
- **cleanlab / confident learning** — Northcutt et al., "Confident Learning:
  Estimating Uncertainty in Dataset Labels" (JAIR 2021).
- **Active label cleaning** — Bernhardt et al., Nature Communications 2022
  (prioritizing re-annotation under budget). Know it well — differentiate from it.
- **Noisy labels in medical ML** — scoping review, JAMIA 2024 (31(7):1596).
- **Decision-curve analysis** — Vickers & Elkin 2006 (net benefit), for the
  safety/operating-point evaluation.
- Repo context: `METHODS_AND_CONTRIBUTIONS.md`, and the existing experiments
  `e00`–`e08` under `paper/reproduce/`.

## What "done" looks like
1. Stage-1 baseline reproduced with CV + operating point.
2. Stage-2 robust method beating baseline on gold test data, with the safety
   constraint met.
3. The dirty-vs-clean comparison quantified.
4. Everything scripted under `paper/reproduce/experiments/` so results regenerate.

## Interfaces / dependencies
- **Depends on clinicians** for `e08_gold_adjudicated.csv` (Stage 2). Stage 1 and
  all method *design/implementation* can start immediately on existing labels.
- **Features/pipeline** already exist in `s2s/`. Do not rebuild them.
- Coordinate the Positive definition with the clinical lead — it must match what
  the gold labels use.
