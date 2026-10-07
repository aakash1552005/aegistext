"""
Unit tests for AegisText feature extractors and data modules.
"""

import sys
import os
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.schema import TextSample, TextOrigin, Domain, TransformationSeverity
from src.data.dedup import (
    compute_content_hash, exact_dedup, build_lineage_groups,
    grouped_split, detect_cross_split_leakage,
)
from src.features.stylometry.extractor import extract_stylometry, StylometryFeatures
from src.features.structural.extractor import extract_structural, StructuralFeatures
from src.features.predictability.extractor import extract_predictability, PredictabilityFeatures


# ========== DATA SCHEMA TESTS ==========

class TestTextSample:
    def test_create_sample(self):
        s = TextSample(
            sample_id="test_1",
            text="This is a test sentence for AegisText.",
            origin=TextOrigin.HUMAN,
            domain=Domain.ACADEMIC,
        )
        assert s.sample_id == "test_1"
        assert s.origin == TextOrigin.HUMAN
        assert s.word_count == 7
        assert s.char_count == 38
        assert len(s.content_hash) == 64  # SHA-256

    def test_all_origins(self):
        for origin in TextOrigin:
            s = TextSample(sample_id="x", text="hello", origin=origin, domain=Domain.OTHER)
            assert s.origin == origin

    def test_hash_deterministic(self):
        s1 = TextSample(sample_id="a", text="Same text", origin=TextOrigin.HUMAN, domain=Domain.OTHER)
        s2 = TextSample(sample_id="b", text="Same text", origin=TextOrigin.AI_RAW, domain=Domain.OTHER)
        assert s1.content_hash == s2.content_hash


# ========== DEDUPLICATION TESTS ==========

class TestDedup:
    def _make_samples(self):
        return [
            TextSample(sample_id="s1", text="The quick brown fox.", origin=TextOrigin.HUMAN, domain=Domain.OTHER),
            TextSample(sample_id="s2", text="The quick brown fox.", origin=TextOrigin.AI_RAW, domain=Domain.OTHER),
            TextSample(sample_id="s3", text="A different sentence entirely.", origin=TextOrigin.HUMAN, domain=Domain.OTHER),
        ]

    def test_exact_dedup(self):
        samples = self._make_samples()
        deduped, removed = exact_dedup(samples)
        assert removed == 1
        assert len(deduped) == 2

    def test_content_hash_normalized(self):
        h1 = compute_content_hash("Hello   World")
        h2 = compute_content_hash("hello world")
        assert h1 == h2

    def test_lineage_groups(self):
        samples = [
            TextSample(sample_id="orig", text="Original text", origin=TextOrigin.AI_RAW, domain=Domain.OTHER),
            TextSample(sample_id="para", text="Paraphrased text", origin=TextOrigin.AI_HUMANIZED, domain=Domain.OTHER, parent_id="orig"),
            TextSample(sample_id="other", text="Unrelated text", origin=TextOrigin.HUMAN, domain=Domain.OTHER),
        ]
        groups = build_lineage_groups(samples)
        assert "orig" in groups
        assert "para" in groups["orig"]
        assert "other" in groups

    def test_grouped_split_no_leakage(self):
        samples = [
            TextSample(sample_id=f"s{i}", text=f"Text number {i}.", origin=TextOrigin.HUMAN, domain=Domain.OTHER)
            for i in range(100)
        ]
        splits = grouped_split(samples, seed=42)
        assert len(splits["train"]) > 0
        assert len(splits["val"]) > 0
        assert len(splits["test"]) > 0
        total = len(splits["train"]) + len(splits["val"]) + len(splits["test"])
        assert total == 100


# ========== STYLOMETRY TESTS ==========

HUMAN_TEXT = """
I've been thinking about this problem for a while now, and honestly, 
I'm not sure there's a simple answer. The thing is, when you look at 
the data from multiple angles — economic, social, environmental — 
each perspective reveals different trade-offs. Some people argue that 
the benefits outweigh the costs, but I'd push back on that claim. 
My experience suggests otherwise, though I'll admit I could be wrong.
"""

AI_TEXT = """
The analysis of this problem reveals several important considerations. 
First, the economic implications must be carefully evaluated. Second, 
the social dimensions require thorough examination. Third, the 
environmental factors present significant challenges. Furthermore, 
the data indicates that a comprehensive approach is necessary for 
addressing these multifaceted issues effectively. In conclusion, 
a balanced perspective that considers all stakeholders is essential.
"""


class TestStylometry:
    def test_basic_extraction(self):
        features = extract_stylometry("Hello world. This is a test.")
        assert isinstance(features, StylometryFeatures)
        assert features.word_count > 0
        assert features.sentence_count >= 1

    def test_empty_text(self):
        features = extract_stylometry("")
        assert features.word_count == 0

    def test_feature_vector(self):
        features = extract_stylometry("Some text here.")
        vec = features.to_vector()
        names = StylometryFeatures.feature_names()
        assert len(vec) == len(names)
        assert all(isinstance(v, float) for v in vec)

    def test_human_vs_ai_patterns(self):
        h = extract_stylometry(HUMAN_TEXT)
        a = extract_stylometry(AI_TEXT)
        # Human text typically has more contractions
        assert h.contraction_ratio >= a.contraction_ratio
        # AI text typically has more discourse markers
        assert a.discourse_marker_count >= h.discourse_marker_count

    def test_ttr_range(self):
        features = extract_stylometry("the the the the the")
        assert 0 <= features.ttr <= 1


# ========== STRUCTURAL TESTS ==========

class TestStructural:
    def test_basic_extraction(self):
        text = "First paragraph here.\n\nSecond paragraph here.\n\nThird paragraph."
        features = extract_structural(text)
        assert isinstance(features, StructuralFeatures)
        assert features.paragraph_count == 3

    def test_empty_text(self):
        features = extract_structural("")
        assert features.paragraph_count == 0

    def test_transition_detection(self):
        text = "However, this is important. Furthermore, we must consider alternatives. In conclusion, we agree."
        features = extract_structural(text)
        assert features.total_transitions >= 3

    def test_heading_detection(self):
        text = "# Introduction\n\nSome text here.\n\n# Methods\n\nMore text."
        features = extract_structural(text)
        assert features.heading_count >= 2
        assert features.has_headings == 1

    def test_feature_vector(self):
        features = extract_structural("Hello. World.")
        vec = features.to_vector()
        names = StructuralFeatures.feature_names()
        assert len(vec) == len(names)


# ========== PREDICTABILITY TESTS ==========

class TestPredictability:
    def test_basic_extraction(self):
        features = extract_predictability("The quick brown fox jumps over the lazy dog.")
        assert isinstance(features, PredictabilityFeatures)
        assert features.unigram_entropy > 0

    def test_empty_text(self):
        features = extract_predictability("")
        assert features.unigram_entropy == 0

    def test_repetitive_text_low_entropy(self):
        repetitive = "the the the the the the the the the the"
        diverse = "alpha bravo charlie delta echo foxtrot golf hotel india juliet"
        rep_feat = extract_predictability(repetitive)
        div_feat = extract_predictability(diverse)
        assert rep_feat.unigram_entropy < div_feat.unigram_entropy

    def test_burstiness_range(self):
        text = "This is a sample text with enough words to compute burstiness measure properly for testing purposes."
        features = extract_predictability(text)
        assert -1 <= features.burstiness <= 1

    def test_feature_vector(self):
        features = extract_predictability("Hello world.")
        vec = features.to_vector()
        names = PredictabilityFeatures.feature_names()
        assert len(vec) == len(names)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
