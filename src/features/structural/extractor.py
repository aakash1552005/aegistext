"""
AegisText Structural / Discourse Feature Extractor

Extracts document-level structural features:
- Paragraph structure & statistics
- Sentence transition patterns
- Heading structure
- Discourse markers & rhetorical structure
- Topic transition indicators
- Structural repetition patterns
- Information-ordering features
"""

import re
import math
from collections import Counter
from typing import Dict, List, Any
from dataclasses import dataclass, asdict


# Transition words / sentence starters indicating discourse structure
TRANSITION_ADDITION = {"additionally", "furthermore", "moreover", "also", "besides", "in addition"}
TRANSITION_CONTRAST = {"however", "nevertheless", "nonetheless", "conversely", "on the other hand", "in contrast", "yet", "but"}
TRANSITION_CAUSE = {"therefore", "consequently", "thus", "hence", "as a result", "because"}
TRANSITION_SEQUENCE = {"first", "second", "third", "next", "then", "finally", "lastly", "subsequently"}
TRANSITION_EXAMPLE = {"for example", "for instance", "specifically", "namely", "such as"}
TRANSITION_CONCLUSION = {"in conclusion", "in summary", "to summarize", "overall", "in short"}

ALL_TRANSITIONS = (
    TRANSITION_ADDITION | TRANSITION_CONTRAST | TRANSITION_CAUSE |
    TRANSITION_SEQUENCE | TRANSITION_EXAMPLE | TRANSITION_CONCLUSION
)


SENTENCE_SPLIT_PATTERN = re.compile(r'(?<=[.!?])\s+')
PARAGRAPH_SPLIT_PATTERN = re.compile(r'\n\s*\n')
MARKDOWN_HEADING_PATTERN = re.compile(r'^#{1,6}\s+')


def _split_sentences(text: str) -> List[str]:
    sentences = SENTENCE_SPLIT_PATTERN.split(text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _split_paragraphs(text: str) -> List[str]:
    paragraphs = PARAGRAPH_SPLIT_PATTERN.split(text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


def _detect_headings(text: str) -> List[str]:
    """Detect markdown-style or short uppercase headings."""
    headings = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Markdown heading
        if MARKDOWN_HEADING_PATTERN.match(line):
            headings.append(line)
        # Short all-caps lines (potential headings)
        elif len(line) < 80 and line.isupper() and len(line.split()) < 10:
            headings.append(line)
    return headings


def _sentence_starter(sentence: str) -> str:
    """Get the first word of a sentence (lowered)."""
    words = sentence.strip().split()
    return words[0].lower().rstrip(".,!?:;") if words else ""


@dataclass
class StructuralFeatures:
    """All structural / discourse features for a text sample."""
    # Paragraph structure
    paragraph_count: int = 0
    avg_paragraph_word_count: float = 0.0
    std_paragraph_word_count: float = 0.0
    min_paragraph_word_count: int = 0
    max_paragraph_word_count: int = 0
    paragraph_length_ratio: float = 0.0  # max/min ratio

    # Sentence transitions
    avg_sentences_per_paragraph: float = 0.0
    std_sentences_per_paragraph: float = 0.0

    # Heading structure
    heading_count: int = 0
    has_headings: int = 0  # binary

    # Transition word analysis
    transition_addition_count: int = 0
    transition_contrast_count: int = 0
    transition_cause_count: int = 0
    transition_sequence_count: int = 0
    transition_example_count: int = 0
    transition_conclusion_count: int = 0
    total_transitions: int = 0
    transition_density: float = 0.0  # transitions per sentence

    # Sentence starter diversity
    starter_diversity: float = 0.0  # unique starters / total sentences
    repeated_starter_ratio: float = 0.0  # ratio of starters used more than once

    # Structural repetition
    paragraph_start_repetition: float = 0.0  # how often paragraphs start the same way

    # Information ordering
    avg_sentence_position_similarity: float = 0.0  # how similar adjacent sentences are in length
    sentence_length_trend: float = 0.0  # positive = getting longer, negative = getting shorter

    # Document structure complexity
    structure_score: float = 0.0  # composite score of structural elements

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_vector(self) -> List[float]:
        d = self.to_dict()
        return [float(v) for v in d.values()]

    @staticmethod
    def feature_names() -> List[str]:
        return list(StructuralFeatures().to_dict().keys())


def _std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(var)


def extract_structural(text: str) -> StructuralFeatures:
    """Extract all structural/discourse features from text."""
    paragraphs = _split_paragraphs(text)
    sentences = _split_sentences(text)
    headings = _detect_headings(text)
    text_lower = text.lower()

    if not sentences:
        return StructuralFeatures()

    # Paragraph word counts
    para_word_counts = [len(p.split()) for p in paragraphs] if paragraphs else [0]
    # Sentences per paragraph
    sents_per_para = [len(_split_sentences(p)) for p in paragraphs] if paragraphs else [0]

    # Transition counting
    add_c = sum(1 for t in TRANSITION_ADDITION if t in text_lower)
    con_c = sum(1 for t in TRANSITION_CONTRAST if t in text_lower)
    cau_c = sum(1 for t in TRANSITION_CAUSE if t in text_lower)
    seq_c = sum(1 for t in TRANSITION_SEQUENCE if t in text_lower)
    ex_c = sum(1 for t in TRANSITION_EXAMPLE if t in text_lower)
    ccl_c = sum(1 for t in TRANSITION_CONCLUSION if t in text_lower)
    total_trans = add_c + con_c + cau_c + seq_c + ex_c + ccl_c

    # Sentence starters
    starters = [_sentence_starter(s) for s in sentences]
    starter_freq = Counter(starters)
    starter_diversity = len(set(starters)) / len(starters) if starters else 0
    repeated = sum(1 for v in starter_freq.values() if v > 1)
    repeated_ratio = repeated / len(starter_freq) if starter_freq else 0

    # Paragraph start repetition
    para_starters = [_sentence_starter(p) for p in paragraphs]
    para_starter_freq = Counter(para_starters)
    para_start_rep = sum(1 for v in para_starter_freq.values() if v > 1) / len(para_starter_freq) if para_starter_freq else 0

    # Sentence length trend
    sent_lengths = [len(s.split()) for s in sentences]
    if len(sent_lengths) >= 2:
        # Simple linear trend: correlation of position with length
        n = len(sent_lengths)
        x_mean = (n - 1) / 2
        y_mean = sum(sent_lengths) / n
        cov = sum((i - x_mean) * (l - y_mean) for i, l in enumerate(sent_lengths))
        var_x = sum((i - x_mean) ** 2 for i in range(n))
        trend = cov / var_x if var_x > 0 else 0
    else:
        trend = 0.0

    # Adjacent sentence length similarity
    if len(sent_lengths) >= 2:
        diffs = [abs(sent_lengths[i] - sent_lengths[i - 1]) for i in range(1, len(sent_lengths))]
        avg_diff = sum(diffs) / len(diffs)
    else:
        avg_diff = 0.0

    # Structure complexity score
    structure_score = (
        (1 if headings else 0) * 2 +
        min(len(paragraphs), 10) +
        min(total_trans, 20) / 2 +
        starter_diversity * 5
    )

    min_para = min(para_word_counts) if para_word_counts else 0
    max_para = max(para_word_counts) if para_word_counts else 0

    return StructuralFeatures(
        paragraph_count=len(paragraphs),
        avg_paragraph_word_count=sum(para_word_counts) / len(para_word_counts) if para_word_counts else 0,
        std_paragraph_word_count=_std(para_word_counts),
        min_paragraph_word_count=min_para,
        max_paragraph_word_count=max_para,
        paragraph_length_ratio=max_para / min_para if min_para > 0 else 0,
        avg_sentences_per_paragraph=sum(sents_per_para) / len(sents_per_para) if sents_per_para else 0,
        std_sentences_per_paragraph=_std(sents_per_para),
        heading_count=len(headings),
        has_headings=1 if headings else 0,
        transition_addition_count=add_c,
        transition_contrast_count=con_c,
        transition_cause_count=cau_c,
        transition_sequence_count=seq_c,
        transition_example_count=ex_c,
        transition_conclusion_count=ccl_c,
        total_transitions=total_trans,
        transition_density=total_trans / len(sentences) if sentences else 0,
        starter_diversity=starter_diversity,
        repeated_starter_ratio=repeated_ratio,
        paragraph_start_repetition=para_start_rep,
        avg_sentence_position_similarity=avg_diff,
        sentence_length_trend=trend,
        structure_score=structure_score,
    )


class StructuralExtractor:
    """Wrapper class providing standard extractor interface."""

    def extract(self, text: str) -> Dict[str, Any]:
        return extract_structural(text).to_dict()

    def extract_vector(self, text: str) -> List[float]:
        return extract_structural(text).to_vector()

    def feature_names(self) -> List[str]:
        return StructuralFeatures.feature_names()

