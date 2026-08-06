"""Data loading and preprocessing — the single source of truth.

`load_dataset()` returns everything an experiment needs: the feature frame X,
the binary label y, patient groups, a fitted-per-fold preprocessing transformer,
and the positive-class index. The transformation is byte-for-byte the datathon
pipeline (ML_models_CT_head.ipynb, CELL 1) so e00 reproduces the published table.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from config import (DATA_PATH, LABEL_COL, POSITIVE_CLASSES, POSITIVE_LABEL,
                    GROUP_COL, ID_COLS, DROP_COLS, MISSINGNESS_FLAG_COLS)


@dataclass
class Dataset:
    X: pd.DataFrame
    y: np.ndarray
    groups: np.ndarray
    preprocessor: ColumnTransformer
    pos_idx: int
    label_encoder: LabelEncoder
    numeric_features: list
    categorical_features: list


def _make_preprocessor(X: pd.DataFrame) -> tuple[ColumnTransformer, list, list]:
    numeric = X.select_dtypes(include=["int64", "float64"]).columns.tolist()
    categorical = X.select_dtypes(include=["object"]).columns.tolist()
    pre = ColumnTransformer([
        ("num", Pipeline([("imputer", SimpleImputer(strategy="median")),
                          ("scaler", StandardScaler())]), numeric),
        ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                          ("onehot", OneHotEncoder(handle_unknown="ignore",
                                                   sparse_output=False))]), categorical),
    ])
    return pre, numeric, categorical


def load_dataset(data_path=DATA_PATH) -> Dataset:
    """Load the final CT-head dataset and build the modeling inputs."""
    if not data_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {data_path}. This is credentialed MIMIC-IV "
            "data (gitignored); confirm the extracted/ folder is present."
        )
    df = pd.read_csv(data_path)

    # 1. binary task
    df = df[df[LABEL_COL].isin(POSITIVE_CLASSES)].copy()

    # 2. drop high-missingness / identifier / free-text columns
    df = df.drop(columns=[c for c in DROP_COLS if c in df.columns])

    # 3. missingness flags before imputation
    for col in MISSINGNESS_FLAG_COLS:
        if col in df.columns:
            df[f"{col}_missing"] = df[col].isna().astype(int)

    # 4. encode target (Negative=0, Positive=1)
    le = LabelEncoder()
    y = le.fit_transform(df[LABEL_COL])
    pos_idx = int(le.transform([POSITIVE_LABEL])[0])

    # 5. features / groups
    X = df.drop(columns=[c for c in ID_COLS if c in df.columns])
    groups = df[GROUP_COL].values

    pre, numeric, categorical = _make_preprocessor(X)
    return Dataset(X=X, y=y, groups=groups, preprocessor=pre, pos_idx=pos_idx,
                   label_encoder=le, numeric_features=numeric,
                   categorical_features=categorical)
