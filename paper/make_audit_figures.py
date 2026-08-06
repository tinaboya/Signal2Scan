"""Generate the two audit/clinical figures for the paper (real data only).

  Fig A: confusion matrix, LLM vs regex over all 7,737 reports (from e05).
  Fig B: decision curve for the appropriateness flag (from e07 template).

Outputs (into paper/): fig_audit_confusion.pdf, fig_decision_curve.pdf
Numbers are hard-coded from the committed e05/e07 outputs; no fabrication.

Run: python paper/make_audit_figures.py
"""
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

mpl.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "pdf.fonttype": 42, "ps.fonttype": 42})

ACCENT = "#34699A"; WARN = "#8C5A3B"; MUTED = "#888"; GOOD = "#4E8542"

# ---- Fig A: confusion matrix (e05) ----------------------------------------
cm = np.array([[4587, 654],   # regex Negative -> [LLM Neg, LLM Pos]
               [965, 1465]])  # regex Positive -> [LLM Neg, LLM Pos]
fig, ax = plt.subplots(figsize=(3.6, 3.2))
im = ax.imshow(cm, cmap="Blues", aspect="equal")
ax.set_xticks([0, 1], ["LLM: Neg", "LLM: Pos"])
ax.set_yticks([0, 1], ["regex: Neg", "regex: Pos"])
for i in range(2):
    for j in range(2):
        off = (i != j)
        ax.text(j, i, f"{cm[i,j]:,}", ha="center", va="center",
                color="white" if cm[i, j] > 2500 else "black",
                fontsize=13, fontweight="bold" if off else "normal")
ax.text(1, -0.62, "suspected\nfalse negatives", ha="center", va="center",
        fontsize=7.5, color=WARN, style="italic")
ax.set_title("LLM vs. regex labels (n=7,671)", fontsize=9.5)
plt.tight_layout()
plt.savefig("paper/fig_audit_confusion.pdf", bbox_inches="tight")
print("Saved paper/fig_audit_confusion.pdf")

# ---- Fig B: decision curve (e07) ------------------------------------------
pt = np.array([0.05, 0.10, 0.15, 0.20, 0.30])
model_nb = np.array([0.1883, 0.1433, 0.0972, 0.0596, 0.0064])
scan_all = np.array([0.1883, 0.1432, 0.0928, 0.0361, -0.1016])
fig, ax = plt.subplots(figsize=(4.2, 3.2))
ax.plot(pt, model_nb, "o-", color=ACCENT, lw=2, label="Appropriateness model")
ax.plot(pt, scan_all, "s--", color=WARN, lw=1.5, label="Scan all")
ax.axhline(0, color=MUTED, lw=1, ls=":", label="Scan none")
ax.set_xlabel("Threshold probability")
ax.set_ylabel("Net benefit")
ax.set_title("Decision-curve analysis", fontsize=9.5)
ax.legend(fontsize=7.5, frameon=False)
ax.grid(alpha=0.25)
plt.tight_layout()
plt.savefig("paper/fig_decision_curve.pdf", bbox_inches="tight")
print("Saved paper/fig_decision_curve.pdf")
