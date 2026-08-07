# Signal2Scan — Project Status

**Single source of truth for what is done, what is blocked, and what is next.**
If this file and anything else disagree, this file is stale — fix it here first.

> **Target venue: AMAI @ MICCAI 2027** (Applications of Medical AI workshop),
> deadline expected **~June 2027** — roughly 11 months out. Work is paced by
> correctness, not by the calendar; the ordering below is driven by dependencies.
> An earlier plan targeted ML4H Sept 10, 2026 — **not active**, deliberately
> passed over in favour of doing the labels properly first.

*Last updated: 2026-08-07*

### What the venue choice implies

| | |
|---|---|
| **Format** | Springer **LNCS**, **8 pages** + 2 for references |
| **Current draft** | **14 pages** in JMLR style — a substantial cut is coming, but not until the results stabilize |
| **Review** | **Double-blind** — the draft stays in a private repo and is anonymized at submission |
| **Why AMAI** | Its CFP is explicitly *"agnostic to medical data modalities … imaging and/or non-imaging data."* Most MICCAI workshops require medical images, which this project never touches — UNSURE matched on topic (label noise, calibration, risk management) but excludes non-image work |

`[TO CONFIRM — Leo]` that AMAI is the workshop he had in mind. "MICCAI" spans
dozens of workshops with very different scope. The AMAI 2027 CFP will not appear
until early 2027; dates above are inferred from the 2026 edition (deadline
June 25, 2026).

Alternatives considered and passed over: ML4H 2026 Findings (4pp, non-archival,
Sept 10 2026 — viable from existing results with no gold labels, deliberately
declined); NeurIPS RCMLR / AIDaR workshops (Aug 30 2026); CHIL 2027 (~Feb 2027);
MLHC 2027 (~Apr 2027). ICLR/NeurIPS main tracks are not a fit — this is a
clinical application paper, not a methods contribution.

---

## 1. Where the project stands

| Component | State |
|---|---|
| Cohort + feature extraction (4h pre-scan) | ✅ Built — 4,638 CT orders, 4,387 in the binary task |
| Rule-based (regex) outcome labels | ⚠️ Built, **not validated** — see [`LABELING.md`](LABELING.md) |
| LLM label audit (Qwen3.5) | ✅ Done — 78.9% concordance; disagreement cells 654 (regex−/LLM+) and 965 (regex+/LLM−). Neither labeler is validated, so neither cell attributes the error |
| Clinician gold labels | ⛔ **Not started** — blind sheet built (`e08`), annotation not begun |
| Baseline models (5 classifiers) | ✅ Reproduced — RF best, AUROC 0.778 [0.744, 0.809] |
| Case-mix baselines | ✅ Done (`e09`) — **changes what the paper can claim**, see §3 |
| Noise-robust flag method | 📐 Designed, not evaluated — needs gold labels |
| Calibration before decision curve | ❌ Not done |
| Paper draft | 🚧 19 `\TODO`, 10 `\DECISION` outstanding |

## 2. The dependency chain (this is what sets the order)

```
   clinician gold labels  (⛔ not started — THE bottleneck)
            │
            ├──► regex labeler validation (sens/spec/PPV/NPV, κ)      [e01]
            │
            ├──► noise-robust vs noise-naive comparison               [e07 part 3]
            │
            └──► dirty-vs-clean flag comparison  ── the paper's headline result
```

**Everything with a number in it inherits the label error.** Model metrics, SHAP
directions, the operating point, and the decision curve are all provisional until
the labels are validated. This is why feature engineering and additional model
families are deliberately *not* next — tuning on labels that are 20% in dispute
optimizes noise.

**Two things are safely parallel** (they do not depend on the labels):
- the case-mix analysis (§3) — a validity threat under *any* labeler
- calibration + the corrected operating point

## 3. Open findings that change the paper's claims

**Case mix dominates the headline number.** (`e09`, 2026-08-06 — prompted by
V. Sharma's review.)

| | AUROC |
|---|---|
| Pooled, all ICUs together | **0.777** |
| Same predictions, scored within each ICU (size-weighted) | **0.618** |

The 0.159 gap is between-unit prevalence, not clinical discrimination. Within
units the model works in surgical/trauma settings (TSICU 0.802, SICU 0.748) and
barely at all in medical ones (MICU 0.544, CCU 0.551, CVICU 0.508) — and those
medical units are 60% of the cohort.

A context-only baseline (care unit + shift + ICU hour + first/repeat CT, 4
variables) reaches AUROC 0.816 / AUPRC 0.572, above the clinical model.
Clinical + context is best (0.833 / 0.611), so the clinical features do carry
independent information — but the claim must be stated as **incremental value
over case mix**, not as an absolute AUROC.

`[DECISION — team]` Reframe the paper around where the tool works and where it
does not, rather than around a single pooled number.

**Two labeler versions disagree on 21% of scans.** The two SQL scripts use
different regex windows. The final dataset is authoritative; see
[`DATA_LINEAGE.md`](DATA_LINEAGE.md) §2b. Not a bug — but it is direct evidence
for why the gold standard is blocking.

**The neuro exclusion is incomplete.** 393 rows (9%) from neuro units survive an
exclusion defined on admission diagnosis. `e09` P4 shows results hold without
them, but the cohort definition still needs a decision — see `DATA_LINEAGE.md` §3.

**First vs repeat CTs have very different prevalence** (18.9% vs 43.2%).
Modeling them separately did *not* improve discrimination (0.776 / 0.756 vs 0.774
pooled), so the recommendation is stratified reporting, not separate tasks.

## 4. Who does what

| Thread | Owner | Produces | Brief |
|---|---|---|---|
| Gold labels | Clinicians (2 + adjudicator) | ~450 adjudicated labels, κ | [`paper/TASK_physician.md`](paper/TASK_physician.md) |
| Prediction tool | CS student | noise-robust flag, dirty-vs-clean | [`paper/TASK_cs_student.md`](paper/TASK_cs_student.md) |
| Case-mix / validity analysis | **Leads:** V.S. | `e09` extensions, calibration, reframing | [`paper/TASK_casemix.md`](paper/TASK_casemix.md) |
| Paper + integration | Lead | writing, figures, synthesis | this repo |

The threads meet at one interface: **the label.** Clinicians produce it, the
student's tool consumes it, the paper reports it.

Thread owners set their own priorities within their thread. The one cross-cutting
rule is §7: build and run freely against the current labels, but do not report or
decide anything on them, because they are contested on roughly a fifth of the
cohort. Contributions at this scale are co-author contributions — agree that up
front, not at submission.

## 5. Blocking decisions

These stop work when unanswered. Each should be a GitHub issue.

| # | Decision | Owner |
|---|---|---|
| 1 | Sign off the positive-finding codebook + borderline rules | Physician lead |
| 2 | Set the κ acceptance threshold for the regex labeler | Physician lead |
| 3 | Name the two annotators + adjudicator | Physician lead |
| 4 | Handling of Unclear (169) and Post-surgical (82) in the gold set | Physician lead |
| 5 | Exclude neuro units by care unit as well as admission diagnosis? | Physician lead |
| 6 | Reframe the paper around incremental-over-case-mix? | Team |
| 7 | ~~Publish the `.tex` draft to GitHub?~~ **Decided:** separate private repo, synced to Overleaf | ✔ |
| 8 | Confirm with Leo that **AMAI** is the intended MICCAI workshop | Lead |
| 9 | Should `first_careunit` be a model feature at all? See [`paper/TASK_casemix.md`](paper/TASK_casemix.md) deliverable 4 | Team |

## 6. Experiment inventory

Every number in the paper should trace to one of these.
Run from repo root: `python paper/reproduce/experiments/<script>`

| ID | What it answers | State |
|---|---|---|
| `e00` | Reproduces the datathon table + seed robustness | ✅ |
| `e01` | Regex labeler vs gold: sens/spec/PPV/NPV, κ | ⛔ blocked on gold |
| `e02` | Repeated patient-grouped CV with 95% CIs | ✅ |
| `e03` | Calibration + decision curves | 🚧 calibration missing |
| `e04` | Benchmark vs Rothrock / Scott-King ED rules | 📐 scaffold |
| `e05` | LLM labels all reports; LLM-vs-regex confusion | ✅ |
| `e06` | Builds the clinician review sheet | ✅ |
| `e07` | Flag operating point + decision curve + dirty-vs-clean | ✅ parts 1–2; part 3 blocked |
| `e08` | Builds the blind gold sample + batches | ✅ built, not annotated |
| `e09` | Case-mix baselines, within-unit, LOICUO, neuro sensitivity | ✅ |

## 7. What waits for the gold labels — and what does not

The line is between **running** an analysis and **concluding** from it. Building
and running against the current labels is cheap and worth doing now; every number
it produces is provisional until the labels are settled, so nothing gets reported
or decided on that basis. Writing the analysis before the gold labels exist is
also better practice than writing it after: pre-specification means nobody can
ask whether the method was tuned to the gold set.

**Build and run now, conclude later**

- **EBM / CatBoost / LightGBM.** `s2s/models.py` is a dict of estimators and
  `e02` re-runs everything, so adding these costs almost nothing and re-running
  on gold labels is one command. What waits is *choosing a primary model* and
  reporting a winner — the five existing models already sit within noise of one
  another (0.75–0.78), and a ranking taken from labels contested on ~20% of rows
  would not survive the labels changing.
- **Cleanlab / confident learning.** Calibrating it needs the gold set, but the
  implementation can be written now and dry-run on a held-out slice of the regex
  labels, so it runs the day the gold labels land. This matches Stage 2 in
  [`paper/TASK_cs_student.md`](paper/TASK_cs_student.md).
- **Calibration + the corrected operating point.** Does not depend on the labels
  at all. Assigned — [`paper/TASK_casemix.md`](paper/TASK_casemix.md).

**Genuinely blocked, for a different reason**

- **New features** — GCS deltas, sedation-aware neuro features, sodium / ammonia /
  lactate. Promising: the counterintuitive GCS direction is plausibly sedation
  confounding. But these need a fresh BigQuery extraction, and the SQL that built
  `final_ct_head_dataset.csv` is **not in the repo** (see
  [`DATA_LINEAGE.md`](DATA_LINEAGE.md)) — so adding a feature currently means
  reconstructing an extraction pipeline that does not exist. Recovering those
  queries from whoever ran them is the cheaper path and should happen first.
- *(Missingness indicators already exist for INR, PTT, GCS, RASS — see
  `config.py`.)*

---

## Keeping this file honest

Update it when a state changes, not on a schedule. If a section has been true for
months, that is information too — it usually means the thread has no owner.
