"""The model zoo — single source of truth for classifier definitions.

Hyperparameters match the datathon notebook so results are reproducible. KNN is
included here (the datathon defined it but dropped it from the published table).
"""
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline

from config import RANDOM_STATE


def make_models() -> dict:
    """Return {name: estimator}. Order matches the paper table."""
    return {
        "Logistic Regression": LogisticRegression(
            class_weight="balanced", max_iter=1000, random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(
            n_estimators=300, max_depth=8, min_samples_leaf=15,
            class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.05,
            random_state=RANDOM_STATE),
        "SVM": SVC(kernel="rbf", class_weight="balanced", probability=True,
                   random_state=RANDOM_STATE),
        "KNN": KNeighborsClassifier(),
    }


def make_pipeline(preprocessor, estimator) -> Pipeline:
    """Wrap a preprocessor + estimator so preprocessing is fit inside each fold."""
    return Pipeline([("preprocessor", preprocessor), ("classifier", estimator)])
