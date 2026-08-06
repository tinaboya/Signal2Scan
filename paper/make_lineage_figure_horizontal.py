"""
Horizontal, compact data-lineage figure for the ML4H paper (figure* / top-of-page).

Left-to-right flow: MIMIC-IV source -> two parallel extraction paths (labeling /
features) -> merge -> final dataset -> preprocess -> CV -> models. Short and wide
so it drops cleanly into a two-column figure* at the top of a page.

Outputs (into paper/):
  - signal2scan_data_lineage.pdf   (vector; overwrites the tall version used by the tex)
  - signal2scan_data_lineage_h.png (preview)

Run:  python paper/make_lineage_figure_horizontal.py
"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib as mpl

mpl.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8,
    "pdf.fonttype": 42, "ps.fonttype": 42,
})

C_SOURCE = "#2c3e50"; C_LABEL = "#34699A"; C_FEAT = "#4E8542"
C_MERGE = "#8C5A3B"; C_MODEL = "#7A3E7A"; C_EDGE = "#5a5a5a"
INK = "#1a1a1a"; WHITE = "#ffffff"

fig, ax = plt.subplots(figsize=(13.5, 5.6))   # wide + short
ax.set_xlim(0, 26); ax.set_ylim(-2.6, 9); ax.axis("off")


def box(x, y, w, h, text, color, fs=8, weight="normal", sub=None, tc=WHITE):
    ax.add_patch(FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.15",
        linewidth=1.0, edgecolor=color, facecolor=color, zorder=3))
    if sub:
        ax.text(x, y + h*0.17, text, ha="center", va="center", color=tc,
                fontsize=fs, weight=weight, zorder=4)
        ax.text(x, y - h*0.26, sub, ha="center", va="center", color=tc,
                fontsize=fs-1.5, style="italic", zorder=4)
    else:
        ax.text(x, y, text, ha="center", va="center", color=tc,
                fontsize=fs, weight=weight, zorder=4)


def arrow(x1, y1, x2, y2, color=C_EDGE, label=None, lx=0, ly=0.5):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                 mutation_scale=11, linewidth=1.2, color=color, zorder=2,
                 shrinkA=2, shrinkB=2))
    if label:
        ax.text((x1+x2)/2 + lx, (y1+y2)/2 + ly, label, ha="center", va="center",
                fontsize=6.5, color=INK, style="italic", zorder=5,
                bbox=dict(boxstyle="round,pad=0.2", fc=WHITE, ec="none", alpha=0.9))


# Source (left)
box(2.6, 4.5, 4.2, 1.5, "MIMIC-IV", C_SOURCE, fs=9, weight="bold",
    sub="BigQuery; de-identified ICU")

# Two parallel paths
arrow(4.7, 5.2, 6.9, 6.6, C_LABEL)
arrow(4.7, 3.8, 6.9, 2.4, C_FEAT)
box(9.2, 6.8, 4.4, 1.7, "Label CT reports", C_LABEL, fs=8, weight="bold",
    sub="rule-based regex NLP")
box(9.2, 2.2, 4.4, 1.7, "Extract features", C_FEAT, fs=8, weight="bold",
    sub="4-hour pre-scan window")

# Merge
arrow(11.4, 6.4, 13.4, 5.2, C_MERGE)
arrow(11.4, 2.6, 13.4, 3.8, C_MERGE)
box(16.0, 4.5, 4.8, 1.9, "Merge + exclude", C_MERGE, fs=8, weight="bold",
    sub="neuro-indication ICD-9/10")

# Final dataset
arrow(18.4, 4.5, 20.0, 4.5, C_MERGE)
box(22.6, 4.5, 5.2, 2.0, "final dataset", C_MERGE, fs=8.5, weight="bold",
    sub="4,638 orders / 3,649 pts")

# Modeling row (bottom band, clear of the feature/label boxes)
arrow(22.6, 3.5, 22.6, -0.4, C_MODEL, label="Pos/Neg -> 4,387", ly=0.0, lx=1.3)
box(22.6, -1.4, 5.2, 1.6, "Preprocess + CV", C_MODEL, fs=8, weight="bold",
    sub="grouped, leakage-safe")
arrow(20.0, -1.4, 12.0, -1.4, C_MODEL)
box(8.4, -1.4, 6.4, 1.6, "5 classifiers + SHAP", C_MODEL, fs=8, weight="bold",
    sub="AUROC / AUPRC / Brier")

# Title
ax.text(13, 8.6, "Signal2Scan — Data Lineage & Study Flow",
        ha="center", va="center", fontsize=11, weight="bold", color=INK)

plt.tight_layout(pad=0.3)
plt.savefig("paper/signal2scan_data_lineage.pdf", bbox_inches="tight")
plt.savefig("paper/signal2scan_data_lineage_h.png", dpi=300, bbox_inches="tight")
print("Saved: paper/signal2scan_data_lineage.pdf (horizontal)")
print("Saved: paper/signal2scan_data_lineage_h.png")
