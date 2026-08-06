# Email draft (short) — to clinical annotators

> Fill in the [BRACKETS] before sending.
> The PDF can be attached (no patient data). The CSV contains MIMIC-IV report
> text (DUA-restricted) and must go through the approved channel, NOT as an email
> attachment.

---

**Subject:** Signal2Scan — draft paper + a short head CT labeling task (80 reports)

Hi [names],

Attached is the current draft of our Signal2Scan paper (PDF) so you can see how
your input fits in. To finish it we need a small set of clinician-verified CT
labels, and I'd like to start with a first batch of 80 to check the task works.

**The labeling task.** 80 head CT reports. For each, based on the IMPRESSION,
mark whether the scan shows an **acute, clinically significant** intracranial
finding, and fill four columns (TRUE_LABEL, finding_type, confidence, notes).
The file is `e08_batch1_BLIND.csv`. About 30 minutes.

Please label independently (two of you), and a third can resolve disagreements.

**Where to get the labeling file.** These are real de-identified MIMIC-IV reports,
so it is not attached to this email. Access it here:
**[APPROVED CHANNEL — e.g. shared drive path / secure link / the MIMIC-approved machine]**.
Please keep it within that environment.

If you can do the 80 by **[DATE]**, that keeps us on schedule. Happy to walk
through it on a quick call.

Thanks,
[Your name]

---

**Attach (no patient data):** `ml4h_signal2scan.pdf`
**Share via approved channel (report text):** `e08_batch1_BLIND.csv`
