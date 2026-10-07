"""
AegisText Master Feature Extraction Pipeline

Orchestrates all feature extraction sub-modules:
- Stylometry (lexical richness, word length, function words, punctuation)
- Structural (discourse patterns, transitions, paragraphs)
- Predictability (entropy, burstiness, rank distributions)
- Semantic (n-gram perplexity, inter-sentence coherence)

Outputs:
- Unified numerical feature vector (numpy ndarray)
- Named dictionary for explainability / SHAP / UI attribution
- Metadata on extraction speed and dimensionality
"""

import time
from typing import Dict, List, Any, Tuple
import numpy as np

from src.features.stylometry.extractor import StylometryExtractor
from src.features.structural.extractor import StructuralExtractor
from src.features.predictability.extractor import PredictabilityExtractor
from src.features.semantic.extractor import SemanticFeatureExtractor


class MasterFeaturePipeline:
    """Unified feature extractor creating the multi-dimensional AegisText linguistic signature."""

    def __init__(self):
        self.stylometry_extractor = StylometryExtractor()
        self.structural_extractor = StructuralExtractor()
        self.predictability_extractor = PredictabilityExtractor()
        self.semantic_extractor = SemanticFeatureExtractor()

        # Cache feature names
        self._feature_names = self._build_feature_names()

    def _build_feature_names(self) -> List[str]:
        dummy = "AegisText is an advanced framework for AI generated text detection. It operates robustly."
        names = []
        names.extend([f"sty_{k}" for k in self.stylometry_extractor.extract(dummy).keys()])
        names.extend([f"str_{k}" for k in self.structural_extractor.extract(dummy).keys()])
        names.extend([f"prd_{k}" for k in self.predictability_extractor.extract(dummy).keys()])
        names.extend([f"sem_{k}" for k in self.semantic_extractor.extract(dummy).keys()])
        return names

    @property
    def feature_names(self) -> List[str]:
        return self._feature_names

    @property
    def num_features(self) -> int:
        return len(self._feature_names)

    def extract_dict(self, text: str) -> Dict[str, float]:
        """Extracts a flat dictionary mapping feature name to float value."""
        res: Dict[str, float] = {}

        sty = self.stylometry_extractor.extract(text)
        for k, v in sty.items():
            res[f"sty_{k}"] = float(v)

        stru = self.structural_extractor.extract(text)
        for k, v in stru.items():
            res[f"str_{k}"] = float(v)

        pred = self.predictability_extractor.extract(text)
        for k, v in pred.items():
            res[f"prd_{k}"] = float(v)

        sem = self.semantic_extractor.extract(text)
        for k, v in sem.items():
            res[f"sem_{k}"] = float(v)

        return res

    def extract_vector(self, text: str) -> np.ndarray:
        """Extracts numerical numpy vector in deterministic feature order."""
        feat_dict = self.extract_dict(text)
        # Ensure all feature names are present
        vec = [feat_dict.get(fname, 0.0) for fname in self._feature_names]
        return np.array(vec, dtype=np.float32)

    def extract_batch(self, texts: List[str]) -> Tuple[np.ndarray, float]:
        """Batch extraction returning a 2D matrix (N_samples, N_features) and elapsed seconds."""
        t0 = time.perf_counter()
        matrix = [self.extract_vector(t) for t in texts]
        elapsed = time.perf_counter() - t0
        return np.vstack(matrix), elapsed
