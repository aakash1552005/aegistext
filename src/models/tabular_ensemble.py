"""
AegisText Calibrated Tabular Ensemble Detector

Combines:
- LightGBM / XGBoost / Random Forest
- Robust scaling & missing value imputation
- Platt / Isotonic probability calibration
- Per-sample confidence and uncertainty estimation
"""

import os
from typing import Dict, Any, List, Optional
import joblib
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

from src.models.base import BaseDetector


class AegisEnsembleDetector(BaseDetector):
    """
    Production-grade tabular classifier utilizing ensemble gradient boosting
    with calibrated posterior probabilities.
    """

    def __init__(
        self,
        model_type: str = "lightgbm",
        n_estimators: int = 150,
        max_depth: int = 6,
        learning_rate: float = 0.05,
        random_state: int = 42,
        calibrate: bool = True,
    ):
        super().__init__(model_name=f"AegisEnsemble_{model_type}")
        self.model_type = model_type
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.random_state = random_state
        self.calibrate = calibrate

        self.pipeline: Optional[Pipeline] = None
        self.feature_names: List[str] = []
        self._init_base_model()

    def _init_base_model(self):
        if self.model_type == "lightgbm" and HAS_LIGHTGBM:
            base_clf = lgb.LGBMClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                learning_rate=self.learning_rate,
                random_state=self.random_state,
                verbose=-1,
                importance_type="gain",
            )
        elif self.model_type == "xgboost" and HAS_XGBOOST:
            base_clf = xgb.XGBClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                learning_rate=self.learning_rate,
                random_state=self.random_state,
                eval_metric="logloss",
            )
        else:
            base_clf = RandomForestClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                random_state=self.random_state,
                n_jobs=-1,
            )

        if self.calibrate:
            clf = CalibratedClassifierCV(estimator=base_clf, method="sigmoid", cv=3)
        else:
            clf = base_clf

        self.pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", RobustScaler()),
            ("classifier", clf),
        ])

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None) -> "AegisEnsembleDetector":
        """Fits the calibrated classifier pipeline."""
        if feature_names:
            self.feature_names = feature_names
        else:
            self.feature_names = [f"f_{i}" for i in range(X.shape[1])]

        self.pipeline.fit(X, y)
        self.is_fitted = True
        self.classes_ = np.unique(y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted yet.")
        return self.pipeline.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted yet.")
        return self.pipeline.predict_proba(X)

    def get_feature_importances(self) -> Dict[str, float]:
        """Returns sorted feature importances from base estimator."""
        if not self.is_fitted:
            return {}

        clf_step = self.pipeline.named_steps["classifier"]
        importances = None

        if isinstance(clf_step, CalibratedClassifierCV):
            # Average across calibrated folds
            imps = []
            for calibrated_classifier in clf_step.calibrated_classifiers_:
                estimator = calibrated_classifier.estimator
                if hasattr(estimator, "feature_importances_"):
                    imps.append(estimator.feature_importances_)
            if imps:
                importances = np.mean(imps, axis=0)
        elif hasattr(clf_step, "feature_importances_"):
            importances = clf_step.feature_importances_

        if importances is None:
            return {}

        # Normalize and map to names
        total = np.sum(importances)
        if total > 0:
            norm_imps = importances / total
        else:
            norm_imps = importances

        feat_imp_map = {
            name: float(norm_imps[i])
            for i, name in enumerate(self.feature_names)
            if i < len(norm_imps)
        }
        return dict(sorted(feat_imp_map.items(), key=lambda item: item[1], reverse=True))

    def save(self, filepath: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        joblib.dump({
            "model_type": self.model_type,
            "pipeline": self.pipeline,
            "feature_names": self.feature_names,
            "classes_": self.classes_,
            "is_fitted": self.is_fitted,
        }, filepath)

    def load(self, filepath: str) -> "AegisEnsembleDetector":
        data = joblib.load(filepath)
        self.model_type = data["model_type"]
        self.pipeline = data["pipeline"]
        self.feature_names = data["feature_names"]
        self.classes_ = data["classes_"]
        self.is_fitted = data["is_fitted"]
        return self
