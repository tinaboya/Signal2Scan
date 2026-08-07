# Task Brief — Case-Mix & Calibration

**What you are establishing:** how much of the model's reported performance comes
from clinical physiology, and how much from the fact that different ICUs have very
different rates of positive scans. The answer determines what the paper is allowed
to claim, and where the tool could actually be deployed.

**Why this thread matters:** the pooled AUROC of 0.778 is roughly half case mix.
That is not a flaw to be hidden — "which ICUs is this usable in" is a more useful
contribution than one pooled number — but the paper currently states the pooled
number as if it were clinical discrimination, and that has to change.

**Why you can start immediately:** unlike most of the project, this thread does
**not** depend on the clinician gold labels. Case mix is a validity threat under
any labeler. The same is true of calibration.

> **This thread has an owner, and the deliverables below are a starting position,
> not a specification.** Reorder them, drop them, add to them. The one standing
> rule is [`STATUS.md`](../STATUS.md) §7: build and run whatever is useful against
> the current labels, but treat every number as provisional and do not settle a
> conclusion on them — they are contested on roughly a fifth of the cohort.

---

## What already exists — do not redo this

`paper/reproduce/experiments/e09_casemix_baseline.py` (~7 min to run) covers four
parts. Read the code and `outputs/e09_*.csv` before starting.

| Part | Question | Result |
|---|---|---|
| **P1** | Does the clinical model beat a case-mix baseline, pooled? | Care unit alone 0.786; context alone (4 vars) 0.816; clinical (42 features) 0.778; clinical+context 0.833 |
| **P2** | Within each ICU, where prevalence cannot help, does the clinical model discriminate? | Pooled 0.777 vs size-weighted within-unit **0.618** |
| **P3** | Does it transfer to a unit absent from training? | 0.49–0.80 by unit — a *different* question from P2, kept separate on purpose |
| **P4** | Do the results survive dropping the neuro units? | Yes; clinical then beats care-unit-only on AUPRC (0.505 vs 0.399) |

Per-unit within-unit AUROC (P2): TSICU 0.802 · SICU 0.748 · MICU/SICU 0.605 ·
CCU 0.551 · **MICU 0.544** · CVICU 0.508. The medical units are ~60% of the
cohort.

Note that `first_careunit`, `shift`, and `icu_hour_at_ct` are in `DROP_COLS`
(`config.py`) — the paper's model never sees them. e09 adds them back as
*comparators*, not as model features.

## Deliverable 1 — within-unit incremental value

P1 compares feature sets pooled; P2 scores the clinical model within units. Nobody
has asked the question the paper's claim actually rests on: **inside a single ICU,
does the clinical model beat a context-only baseline?**

Within one unit, care unit is constant, so context reduces to shift, ICU hour, and
first-vs-repeat. If clinical stays meaningfully above that within units, the
incremental-value claim holds. If it does not, the claim is much weaker than the
pooled 0.833 vs 0.816 comparison suggests.

Report per unit, with CIs, for units above ~300 orders.

## Deliverable 2 — calibration, before the decision curve

Probabilities are currently uncalibrated: a predicted 0.30 has never been checked
against "30% of such patients are positive." The flag is a threshold on a
probability and the decision curve is computed across thresholds, so both
currently rest on an unchecked assumption. `e03_calibration_dca.py` has the
scaffold.

Do this **per unit as well as pooled**. A model calibrated on a cohort averaging
22.9% positive will be badly miscalibrated in CVICU (2.5%) and Neuro Stepdown
(69.6%). That is a concrete, falsifiable prediction — check it.

## Deliverable 3 — what the operating point does in each unit

The flag uses one global threshold (0.213 → 17.5% flagged, 5.0% of positives
missed). Prevalence ranges from 2.5% to 69.6% across units, so the flag rate and
the missed-positive rate almost certainly do not hold unit by unit.

Compute both per unit at the global threshold. If the tool flags most requests in
one unit and almost none in another, or if the 5% safety constraint is violated
somewhere, that is a deployment finding and belongs in the paper — the safety
guarantee is currently stated as a cohort-level average.

## Deliverable 4 — a position on whether care unit should be a feature

Not a number; a written argument, because it is a design decision with an ethical
edge.

Including care unit improves discrimination. It also means the tool partly
recommends against scanning because patients *in that unit* have historically had
fewer positive scans. If historical imaging practice was itself imperfect, the
tool can entrench it — including under-imaging of a population. Excluding it costs
performance and arguably discards legitimate base-rate information.

Take a position, state the reasoning, and note what would change your mind. This
becomes a Discussion paragraph. `[DECISION — team]`

## Deliverable 5 — the reframed results table

Propose the table and the accompanying claim. The paper currently leads with a
pooled AUROC; it should lead with incremental value over case mix, and say where
the tool works and where it does not. Bring a draft table plus one paragraph of
proposed claim language.

---

## Out of scope for now

Deferred deliberately, with reasoning in [`STATUS.md`](../STATUS.md) §7 — not
rejected:

- **Additional model families** (EBM, CatBoost, LightGBM). The five existing
  models sit within noise of each other; the paper states the engine is not the
  headline.
- **Label-cleaning methods** (cleanlab / confident learning). Already scoped as
  part of the noise-robust method and dependent on the gold labels.
- **New features** (GCS deltas, sedation-aware neuro features, sodium / ammonia /
  lactate). Promising — the counterintuitive GCS direction is plausibly sedation
  confounding — but each needs a fresh BigQuery extraction, and the extraction
  queries are currently missing from the repo (see below).

Missingness indicators already exist for INR, PTT, GCS, and RASS (`config.py`).

## Interfaces and dependencies

- **Does not depend on the gold labels.** Start now.
- **Reuse `s2s/data.py`** — it builds X, y, and patient groups, and is the single
  source of truth for the preprocessing contract. Do not rebuild it.
- **Splits must be grouped by patient** (`StratifiedGroupKFold` on `subject_id`).
  A patient can have several CTs.
- **Script everything** under `paper/reproduce/experiments/` so results
  regenerate. Follow the `e09` layout: one part per question, one CSV per part.
- **`outputs/` is deny-listed in `.gitignore`.** New output files are private
  unless explicitly whitelisted, and only aggregate tables may be — never anything
  carrying `note_id`, `subject_id`, `hadm_id`, or report text.
- **Cohort caveat:** the SQL that produced `final_ct_head_dataset.csv` is not in
  the repo, so the 17,314 → 4,638 exclusion cannot currently be re-executed or
  verified. Work from the CSV; flag anything that looks inconsistent with
  [`DATA_LINEAGE.md`](../DATA_LINEAGE.md).

## Reading

- [`PROJECT_PRIMER.md`](../PROJECT_PRIMER.md) — the project from zero
- [`STATUS.md`](../STATUS.md) — current state, blocking decisions, what is deferred
- [`DATA_LINEAGE.md`](../DATA_LINEAGE.md) §2b and §3 — the two labeler versions,
  and the incomplete neuro exclusion
- Vickers & Elkin 2006 — decision-curve analysis / net benefit
- Van Calster et al. 2019, *BMC Medicine* — calibration hierarchy, and why
  discrimination alone is insufficient for a clinical tool
