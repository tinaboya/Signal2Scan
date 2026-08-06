"""Central configuration: paths, constants, and the preprocessing contract.

Every experiment imports from here so there is a single source of truth for the
data location, the column drop-list, the label mapping, and default seeds.
"""
from pathlib import Path

# --- Paths -----------------------------------------------------------------
# Repo root = three levels up from this file (repo/paper/reproduce/config.py).
REPO_ROOT = Path(__file__).resolve().parents[2]

# The final analysis dataset (credentialed, gitignored — not redistributable).
DATA_PATH = REPO_ROOT / "extracted" / "team2-ZZZ Lab" / \
    "Final dataset and code" / "final_ct_head_dataset.csv"

# Where generated tables/figures go (gitignored).
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"

# --- Task definition -------------------------------------------------------
LABEL_COL = "ct_classification"
POSITIVE_CLASSES = ["Positive", "Negative"]   # binary task keeps only these
POSITIVE_LABEL = "Positive"
GROUP_COL = "subject_id"                       # patient-level grouping (no leakage)
ID_COLS = ["ct_classification", "subject_id", "hadm_id", "stay_id"]

# Columns dropped in the datathon (high missingness / identifiers / free text).
# Kept identical so e00 reproduces the published numbers exactly.
DROP_COLS = [
    "note_id", "ct_order_time", "icu_intime",
    "npi_right_min", "npi_left_min",   # ~100% missing
    "temp_max", "flag_fever",          # ~94% missing
    "pco2_max", "flag_hypercapnia",    # ~75% missing
    "map_min", "flag_map_low",         # ~60% missing
    "sbp_max",                         # ~37% missing
    "pupil_size_right", "pupil_size_left",
    "first_careunit", "icu_hour_at_ct", "shift",
]

# Missingness-indicator flags added before imputation.
MISSINGNESS_FLAG_COLS = ["inr", "ptt", "gcs_total_min", "rass_last"]

# --- Reproducibility -------------------------------------------------------
RANDOM_STATE = 42        # the datathon's single-split seed
TEST_SIZE = 0.2
N_ROBUSTNESS_SEEDS = 25  # for e00's stability check
N_CV_REPEATS = 20        # for e02's repeated grouped CV
N_CV_FOLDS = 5

# Published datathon single-split numbers (for e00's diff check).
PUBLISHED_RESULTS = {
    "Logistic Regression": dict(AUROC=0.714, AUPRC=0.437, Accuracy=0.675, Brier=0.209),
    "Random Forest":       dict(AUROC=0.766, AUPRC=0.470, Accuracy=0.758, Brier=0.179),
    "Gradient Boosting":   dict(AUROC=0.757, AUPRC=0.479, Accuracy=0.804, Brier=0.144),
    "SVM":                 dict(AUROC=0.742, AUPRC=0.447, Accuracy=0.721, Brier=0.146),
}
