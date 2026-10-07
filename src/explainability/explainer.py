"""
AegisText Explainability & Linguistic Attribution Engine

Generates human-interpretable explanations for detection decisions:
1. Feature-level attribution (identifies top linguistic cues pushing towards AI vs Human)
2. Sentence-level heatmap scoring (scores each sentence individually for UI highlighting)
3. Structural anomaly diagnostics (identifies formulaic transitions, low burstiness, monotonous lengths)
4. Confidence and uncertainty calibration summary
"""

import math
import re
from typing import Dict, List, Any, Optional
import numpy as np

from src.features.pipeline import MasterFeaturePipeline
from src.preprocessing.normalizer import TextSanitizer


class AegisExplainer:
    """Produces multi-tiered explanations for model predictions."""

    def __init__(self, feature_pipeline: MasterFeaturePipeline):
        self.pipeline = feature_pipeline
        self.sanitizer = TextSanitizer()

    def explain_prediction(
        self,
        text: str,
        ai_probability: float,
        model_feature_importances: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Creates a comprehensive explainability package for a text sample.
        """
        # 1. Adversarial & Security Inspection
        _, security_report = self.sanitizer.sanitize(text)

        # 2. Extract full feature dictionary
        features = self.pipeline.extract_dict(text)

        # 3. Compute top feature contributors
        contributors = self._compute_feature_attributions(features, ai_probability, model_feature_importances)

        # 4. Sentence-level segmentation and scoring
        sentence_analysis = self._analyze_sentences(text)

        # 5. Diagnostic linguistic rules
        diagnostics = self._generate_linguistic_diagnostics(features, security_report)

        return {
            "ai_probability": round(ai_probability, 4),
            "classification": "AI_GENERATED" if ai_probability >= 0.5 else "HUMAN_WRITTEN",
            "confidence_band": self._get_confidence_band(ai_probability),
            "feature_attributions": contributors,
            "sentence_heatmap": sentence_analysis,
            "linguistic_diagnostics": diagnostics,
            "security_tampering_audit": security_report,
        }

    def _get_confidence_band(self, prob: float) -> str:
        dist_from_threshold = abs(prob - 0.5)
        if dist_from_threshold > 0.35:
            return "VERY_HIGH_CONFIDENCE"
        elif dist_from_threshold > 0.20:
            return "HIGH_CONFIDENCE"
        elif dist_from_threshold > 0.10:
            return "MODERATE_CONFIDENCE"
        else:
            return "BORDERLINE_UNCERTAIN"

    def _compute_feature_attributions(
        self,
        features: Dict[str, float],
        prob: float,
        model_importances: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        """Identifies key linguistic signals that influenced the score."""
        attributions = []

        # Feature interpretation heuristics based on linguistic literature
        heuristics = {
            "prd_burstiness_word_length": {
                "name": "Word Length Burstiness",
                "ai_direction": "low",
                "desc": "AI text typically lacks natural variation in word length rhythm.",
            },
            "prd_token_entropy": {
                "name": "Vocabulary Entropy",
                "ai_direction": "low",
                "desc": "Robotic text exhibits constrained lexical entropy compared to human prose.",
            },
            "str_transition_word_density": {
                "name": "Formal Transition Density",
                "ai_direction": "high",
                "desc": "LLMs overuse formal discourse markers (furthermore, moreover, consequently).",
            },
            "sty_ttr": {
                "name": "Type-Token Ratio (TTR)",
                "ai_direction": "low",
                "desc": "Repetitive or constrained vocabulary diversity.",
            },
            "sem_semantic_monotony_index": {
                "name": "Semantic Monotony",
                "ai_direction": "high",
                "desc": "Excessively uniform inter-sentence semantic similarity.",
            },
            "str_sentence_length_std": {
                "name": "Sentence Length Rhythm (Std Dev)",
                "ai_direction": "low",
                "desc": "Human text has high sentence length rhythm variance (staccato vs compound).",
            },
        }

        for feat_key, info in heuristics.items():
            if feat_key in features:
                val = features[feat_key]
                weight = 1.0
                if model_importances and feat_key in model_importances:
                    weight = model_importances[feat_key] * 5.0

                attributions.append({
                    "feature": feat_key,
                    "display_name": info["name"],
                    "value": round(val, 4),
                    "ai_indicative": info["ai_direction"],
                    "weight_impact": round(weight, 3),
                    "explanation": info["desc"],
                })

        # Sort by impact
        attributions.sort(key=lambda x: x["weight_impact"], reverse=True)
        return attributions

    def _analyze_sentences(self, text: str) -> List[Dict[str, Any]]:
        """Per-sentence granularity scoring for frontend visual highlight."""
        raw_sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        if not raw_sents:
            return []

        results = []
        for idx, sent in enumerate(raw_sents):
            # Evaluate sentence-level indicators
            words = sent.split()
            word_count = len(words)
            has_formal_transition = any(sent.lower().startswith(t) for t in [
                "furthermore", "moreover", "in conclusion", "consequently", "additionally", "in summary"
            ])
            has_buzzwords = any(w.lower() in ["tapestry", "delve", "testament", "crucial", "multifaceted"] for w in words)

            # Heuristic sentence AI likelihood
            score = 0.5
            if has_formal_transition:
                score += 0.25
            if has_buzzwords:
                score += 0.20
            if 15 <= word_count <= 25:
                # LLM sweet spot
                score += 0.10
            elif word_count < 6 or word_count > 40:
                # Extreme sentence length more typical in human prose
                score -= 0.15

            score = max(0.05, min(0.95, score))

            results.append({
                "sentence_index": idx,
                "text": sent,
                "word_count": word_count,
                "ai_probability": round(score, 3),
                "suspicion_level": "HIGH" if score >= 0.7 else ("MODERATE" if score >= 0.55 else "LOW"),
            })

        return results

    def _generate_linguistic_diagnostics(
        self,
        features: Dict[str, float],
        security_report: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generates plain English diagnostic findings."""
        diagnostics = []

        if security_report.get("zero_width_count", 0) > 0:
            diagnostics.append({
                "category": "SECURITY",
                "severity": "CRITICAL",
                "title": "Invisible Zero-Width Character Injection Detected",
                "description": f"Found {security_report['zero_width_count']} invisible characters inserted, a signature evasion technique."
            })

        if security_report.get("homoglyph_count", 0) > 0:
            diagnostics.append({
                "category": "SECURITY",
                "severity": "WARNING",
                "title": "Homoglyph / Confusable Characters Detected",
                "description": f"Found {security_report['homoglyph_count']} cross-alphabet character substitutions."
            })

        if features.get("str_sentence_length_std", 10.0) < 3.5:
            diagnostics.append({
                "category": "STYLE",
                "severity": "MODERATE",
                "title": "Low Sentence Rhythm Variation",
                "description": "Sentence lengths are unnaturally uniform across paragraphs, characteristic of generative language models."
            })

        if features.get("str_transition_word_density", 0.0) > 0.06:
            diagnostics.append({
                "category": "DISCOURSE",
                "severity": "MODERATE",
                "title": "High Discourse Transition Density",
                "description": "Disproportionate density of transitional connectors (furthermore, additionally, consequently)."
            })

        if features.get("prd_burstiness_word_length", 0.5) < 0.2:
            diagnostics.append({
                "category": "PREDICTABILITY",
                "severity": "HIGH",
                "title": "Low Token Burstiness",
                "description": "Word length and information packaging lack the natural burstiness observed in human writing."
            })

        return diagnostics
