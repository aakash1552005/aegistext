"""
AegisText Abstract Base Model Interface

Defines the contract for all AI detectors in the framework:
- fit(X, y)
- predict(X) -> np.ndarray
- predict_proba(X) -> np.ndarray
- calibrate(X_val, y_val)
- evaluate(X_test, y_test) -> Dict[str, float]
- save(path) / load(path)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import numpy as np


class BaseDetector(ABC):
    """Abstract base class for all AegisText detectors."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.is_fitted = False
        self.classes_ = np.array([0, 1])  # 0: Human, 1: AI

    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs) -> "BaseDetector":
        """Train detector on feature matrix X and labels y."""
        pass

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict binary or multiclass label."""
        pass

    @abstractmethod
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict calibrated probabilities (shape: [N, n_classes])."""
        pass

    @abstractmethod
    def save(self, filepath: str) -> None:
        """Serialize model artifact to disk."""
        pass

    @abstractmethod
    def load(self, filepath: str) -> "BaseDetector":
        """Load model artifact from disk."""
        pass
