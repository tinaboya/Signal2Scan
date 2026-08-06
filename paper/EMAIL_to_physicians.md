# Email draft — to clinical annotators

> Fill in the [BRACKETS] before sending. The report file is NOT attached: it
> contains MIMIC-IV report text (DUA-restricted) and must be accessed only through
> the approved channel you specify below. This email body contains no patient data.

---

**Subject:** Signal2Scan — 30 min head CT labeling task (first batch of 80)

Hi [names],

Thanks for helping with the Signal2Scan head CT project. We need a small set of
clinician-verified CT labels to anchor the rest of the study, and I'd like to
start with a short first batch to check the task works before we do more.

**What it is.** 80 head CT radiology reports. For each, based on the IMPRESSION,
please record whether the scan shows an **acute, clinically significant**
intracranial finding.

**Before you start — one thing to agree (5 min).** Please confirm the definition
of "Positive" and how to treat chronic/stable and post-surgical findings. The
short form is in `PHYSICIAN_REVIEW_labeling.md` (attached). [NAME] to sign off.

**The task.** Open the file `e08_batch1_BLIND.csv` and fill four columns per row:
- **TRUE_LABEL** — Positive or Negative (Positive = an acute significant finding).
- **finding_type** — acute / chronic-stable / post-surgical / none.
- **confidence** — high / low.
- **notes** — anything worth recording.

The labels you'd expect from the automatic method are hidden on purpose, so please
judge each report on its own.

**Please label independently.** Two of you label the same 80 reports separately;
a third resolves any disagreements. This lets us report inter-rater agreement.

**Where to get the file (DUA note).** These are real de-identified MIMIC-IV
reports, so the file is not emailed. Access it here: **[APPROVED CHANNEL —
e.g. institutional shared drive path / secure link / the MIMIC-approved machine]**.
Please keep it within that environment and don't copy it elsewhere.

**When.** If you can do the 80 by **[DATE]**, that keeps us on track. It should
take about 30 minutes each.

**What happens next.** From your labels we measure how accurate the automatic
labels are and build the clean set the modeling work needs. If the first 80 go
smoothly, we'll send a second small batch to stack on top.

Full details are in `TASK_physician.md` (attached). Happy to hop on a quick call
if anything is unclear.

Thanks,
[Your name]

---

**Attach to the email (no patient data in these):**
- `TASK_physician.md`
- `PHYSICIAN_REVIEW_labeling.md`

**Share via the approved channel (contains report text):**
- `e08_batch1_BLIND.csv`
