"""
Generate the Signal2Scan data-lineage / study-flow figure for publication.

Outputs (in the current working directory):
  - signal2scan_data_lineage.pdf   (vector — use this in LaTeX / Word)
  - signal2scan_data_lineage.png   (600 dpi raster — use for previews / slides)

Run:  python make_lineage_figure.py
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib as mpl

# ── Publication-grade style ───────────────────────────────────────────────────
mpl.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "pdf.fonttype": 42,   # embed TrueType (editable text in the PDF)
    "ps.fonttype": 42,
})

# Muted, print-safe palette (also legible in greyscale)
C_SOURCE = "#2c3e50"   # dark slate  — source
C_LABEL  = "#34699A"   # blue        — labeling path
C_FEAT   = "#4E8542"   # green       — feature path
C_MERGE  = "#8C5A3B"   # brown       — merge / dataset
C_MODEL  = "#7A3E7A"   # purple      — modeling
C_EDGE   = "#5a5a5a"
INK      = "#1a1a1a"
WHITE    = "#ffffff"

fig, ax = plt.subplots(figsize=(7.2, 9.2))   # single-column-friendly aspect
ax.set_xlim(0, 10)
ax.set_ylim(-0.6, 13)
ax.axis("off")


def box(x, y, w, h, text, color, text_color=WHITE, fontsize=9,
        weight="normal", sub=None):
    """Rounded box with centered text; optional smaller sub-line."""
    ax.add_patch(FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.12",
        linewidth=1.1, edgecolor=color, facecolor=color, zorder=3))
    if sub:
        ax.text(x, y + h * 0.16, text, ha="center", va="center",
                color=text_color, fontsize=fontsize, weight=weight, zorder=4)
        ax.text(x, y - h * 0.24, sub, ha="center", va="center",
                color=text_color, fontsize=fontsize - 2, zorder=4, style="italic")
    else:
        ax.text(x, y, text, ha="center", va="center",
                color=text_color, fontsize=fontsize, weight=weight, zorder=4)


def arrow(x1, y1, x2, y2, color=C_EDGE, label=None, lx=0, ly=0):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>", mutation_scale=13,
        linewidth=1.3, color=color, zorder=2,
        shrinkA=2, shrinkB=2))
    if label:
        ax.text((x1 + x2) / 2 + lx, (y1 + y2) / 2 + ly, label,
                ha="center", va="center", fontsize=7.5, color=INK,
                style="italic", zorder=5,
                bbox=dict(boxstyle="round,pad=0.2", fc=WHITE, ec="none", alpha=0.9))


# ── Title ──────────────────────────────────────────────────────────────────
ax.text(5, 12.7, "Signal2Scan — Data Lineage & Study Flow",
        ha="center", va="center", fontsize=12.5, weight="bold", color=INK)

# ── Source ─────────────────────────────────────────────────────────────────
box(5, 11.80, 6.6, 0.8, "MIMIC-IV  (BigQuery: physionet-data.mimiciv_*)",
    C_SOURCE, sub="de-identified ICU database")

# ── The radiology notes define the unit of analysis ────────────────────────
# They are drawn ABOVE the fork on purpose: one row is one CT order, and the
# feature extraction can only aggregate "the 4h before the scan" once the scan
# time is known. The two paths below attach labels and columns to these rows.
arrow(5, 11.40, 5, 11.05, C_LABEL)
box(5, 10.60, 5.4, 0.9, "radiology + radiology_detail", C_LABEL, fontsize=8.5,
    sub="3 head-CT types  →  IMPRESSION / FINDINGS")

arrow(5, 10.15, 5, 9.83, C_LABEL)
box(5, 9.40, 4.8, 0.85, "one row per CT order", C_SOURCE, fontsize=9.5,
    weight="bold", sub="patient · admission · scan time")

# ── Two things attached to those rows ──────────────────────────────────────
arrow(5, 8.98, 2.9, 8.45, C_LABEL)
arrow(5, 8.98, 7.1, 8.45, C_FEAT)

box(2.9, 7.95, 3.6, 1.0, "Step 1  ·  Label the report", C_LABEL, fontsize=9,
    sub="rule-based regex NLP")
box(7.1, 7.95, 3.6, 1.0, "Step 2  ·  Extract features", C_FEAT, fontsize=9,
    sub="4h pre-scan · chart / lab / med")

arrow(2.9, 7.45, 2.9, 7.05, C_LABEL)
arrow(7.1, 7.45, 7.1, 7.05, C_FEAT)

box(2.9, 6.55, 3.6, 1.0, "CT label", C_LABEL, fontsize=9.5, weight="bold",
    sub="Neg / Pos / Post-surg / Unclear")
box(7.1, 6.55, 3.6, 1.0, "pre-scan features", C_FEAT, fontsize=9.5,
    weight="bold", sub="GCS, RASS, vitals, labs, meds")

# ── Merge ──────────────────────────────────────────────────────────────────
arrow(2.9, 6.05, 4.4, 5.55, C_MERGE)
arrow(7.1, 6.05, 5.6, 5.55, C_MERGE)
box(5, 5.10, 6.9, 0.9, "17,314 CT orders  ·  features + label", C_MERGE,
    fontsize=9.5, weight="bold", sub="Step 3  ·  join on the CT order")

arrow(5, 4.65, 5, 4.18, C_MERGE,
      label="exclude neurologic-indication admissions (ICD-9/10)", ly=0.02)
box(5, 3.70, 6.9, 0.95, "final_ct_head_dataset.csv", C_MERGE, fontsize=10,
    weight="bold", sub="4,638 CT orders · 3,649 patients · 57 columns")

# ── Modeling ───────────────────────────────────────────────────────────────
arrow(5, 3.23, 5, 2.78, C_MODEL,
      label="keep Positive / Negative  →  4,387 rows", ly=0.02)
box(5, 2.30, 6.9, 0.95, "Step 4  ·  Preprocess", C_MODEL, fontsize=9.5,
    weight="bold", sub="drop high-missing cols · impute · scale · one-hot  →  42 features")

arrow(5, 1.83, 5, 1.56, C_MODEL)
box(5, 1.10, 6.9, 0.9, "Repeated StratifiedGroupKFold on subject_id", C_MODEL,
    fontsize=9, sub="20 × 5-fold · patient-level (no leakage)")

arrow(5, 0.65, 5, 0.38, C_MODEL)
box(5, 0.00, 6.9, 0.72,
    "Step 5  ·  5 classifiers  →  AUROC / AUPRC / Brier · SHAP",
    C_MODEL, fontsize=8.8, weight="bold")

plt.tight_layout(pad=0.4)
plt.savefig("signal2scan_data_lineage.pdf", bbox_inches="tight")
plt.savefig("signal2scan_data_lineage.png", dpi=600, bbox_inches="tight")
print("Saved: signal2scan_data_lineage.pdf")
print("Saved: signal2scan_data_lineage.png")
