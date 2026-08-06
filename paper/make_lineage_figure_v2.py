"""
Figure 1 (v2) — method overview matching the reframed paper.

Story left-to-right:
  Radiology reports  ->  THREE label sources
     (regex noisy | LLM audit disagreement | clinician gold)
  ->  noise-robust learning under a safety constraint
  ->  safe CT utility predictor (non-blocking low-yield flag)

Colors: regex=blue, LLM=amber, clinician gold=green, robust-learning=purple,
clinical output=teal. Wide + short for a two-column figure* at page top.

Output: paper/signal2scan_fig1.pdf  (+ _preview.png)
Run: python paper/make_lineage_figure_v2.py
"""
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

mpl.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12,
                     "pdf.fonttype": 42, "ps.fonttype": 42})

C_SRC   = "#2c3e50"  # reports (source)
C_REGEX = "#34699A"  # noisy regex labels
C_LLM   = "#C08A2E"  # LLM audit / disagreement signal
C_GOLD  = "#4E8542"  # clinician gold
C_ROB   = "#7A3E7A"  # noise-robust learning
C_OUT   = "#2E7D74"  # clinical output
INK = "#1a1a1a"; WHITE = "#ffffff"; EDGE = "#5a5a5a"

fig, ax = plt.subplots(figsize=(14, 6.2))
ax.set_xlim(0, 30.5); ax.set_ylim(0, 10); ax.axis("off")


def box(x, y, w, h, title, color, sub=None, fs=12, tc=WHITE):
    ax.add_patch(FancyBboxPatch((x - w/2, y - h/2), w, h,
                 boxstyle="round,pad=0.02,rounding_size=0.15",
                 linewidth=1.0, edgecolor=color, facecolor=color, zorder=3))
    if sub:
        ax.text(x, y + h*0.17, title, ha="center", va="center", color=tc,
                fontsize=fs, weight="bold", zorder=4)
        ax.text(x, y - h*0.24, sub, ha="center", va="center", color=tc,
                fontsize=fs-2, style="italic", zorder=4)
    else:
        ax.text(x, y, title, ha="center", va="center", color=tc,
                fontsize=fs, weight="bold", zorder=4)


def arrow(x1, y1, x2, y2, color=EDGE, label=None, lx=0, ly=0.45, lc=INK):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                 mutation_scale=11, linewidth=1.3, color=color, zorder=2,
                 shrinkA=2, shrinkB=2))
    if label:
        ax.text((x1+x2)/2+lx, (y1+y2)/2+ly, label, ha="center", va="center",
                fontsize=9, color=lc, style="italic", zorder=5,
                bbox=dict(boxstyle="round,pad=0.2", fc=WHITE, ec="none", alpha=0.92))


# ---- Source: radiology reports ----
box(2.9, 5.0, 4.8, 1.7, "Radiology reports", C_SRC, sub="MIMIC-IV-Note, pre-scan")

# ---- Three label sources ----
# regex (top)
arrow(5.3, 5.7, 7.0, 8.0, C_REGEX)
box(9.6, 8.2, 5.2, 1.6, "Regex labels", C_REGEX, sub="cheap, noisy (all reports)")
# LLM audit (middle)
arrow(5.3, 5.0, 7.0, 5.0, C_LLM)
box(9.6, 5.0, 5.2, 1.6, "LLM audit", C_LLM, sub="disagreement = noise-prior")
# clinician gold (bottom)
arrow(5.3, 4.3, 7.0, 2.0, C_GOLD)
box(9.6, 1.8, 5.2, 1.6, "Clinician gold", C_GOLD, sub="small, adjudicated")

# ---- Noise-robust learning ----
arrow(12.2, 8.0, 14.6, 5.7, C_ROB)
arrow(12.2, 5.0, 14.6, 5.0, C_ROB)
arrow(12.2, 2.0, 14.6, 4.3, C_ROB)
box(17.8, 5.0, 5.8, 2.3, "Noise-robust", C_ROB,
    sub="learn from 3 sources")
ax.text(17.8, 3.4, "safety constraint: sensitivity ≥ 95%", ha="center",
        va="center", fontsize=9.5, color=C_ROB, style="italic", zorder=5)

# ---- Safe clinical output ----
arrow(20.3, 5.0, 23.0, 5.0, C_OUT)
box(26.6, 5.0, 6.0, 2.3, "Safe CT utility\npredictor", C_OUT,
    sub="non-blocking low-yield flag")

# ---- contribution tags ----
ax.text(9.6, 9.55, "(A) audit → 3 label sources", ha="center", fontsize=10.5,
        color=INK, weight="bold")
ax.text(17.8, 7.05, "(A) robust learning", ha="center", fontsize=10.5,
        color=INK, weight="bold")
ax.text(26.6, 7.05, "(B) clinical tool", ha="center", fontsize=10.5,
        color=INK, weight="bold")

plt.tight_layout(pad=0.3)
plt.savefig("paper/signal2scan_fig1.pdf", bbox_inches="tight")
plt.savefig("paper/signal2scan_fig1_preview.png", dpi=200, bbox_inches="tight")
print("Saved paper/signal2scan_fig1.pdf")
