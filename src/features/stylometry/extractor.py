"""
AegisText Stylometry Feature Extractor

Extracts linguistic style features that capture writing patterns:
- Lexical richness (TTR, MTLD, HD-D, hapax ratio)
- Function word frequencies
- Sentence/word/paragraph length statistics
- Punctuation patterns
- POS tag distributions (when spaCy is available)
- Pronoun, modal, tense, conjunction usage
- Discourse markers
"""

import re
import math
import string
from collections import Counter
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


# Common English function words
FUNCTION_WORDS = {
    "the", "a", "an", "this", "that", "these", "those",
    "is", "am", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did",
    "will", "would", "shall", "should", "may", "might", "can", "could", "must",
    "not", "and", "but", "or", "nor", "for", "yet", "so",
    "in", "on", "at", "to", "for", "with", "by", "from", "of", "about",
    "if", "then", "than", "because", "while", "although", "though",
    "he", "she", "it", "they", "we", "I", "you", "me", "him", "her",
    "us", "them", "my", "your", "his", "its", "our", "their",
    "who", "whom", "which", "what", "where", "when", "how", "why",
}

DISCOURSE_MARKERS = {
    "however", "therefore", "moreover", "furthermore", "nevertheless",
    "consequently", "additionally", "meanwhile", "nonetheless",
    "in conclusion", "in summary", "for example", "for instance",
    "on the other hand", "in contrast", "as a result", "in addition",
    "first", "second", "third", "finally", "lastly",
    "indeed", "certainly", "clearly", "obviously", "apparently",
}

MODAL_VERBS = {"can", "could", "may", "might", "must", "shall", "should", "will", "would"}

PRONOUNS_FIRST = {"i", "me", "my", "mine", "myself", "we", "us", "our", "ours", "ourselves"}
PRONOUNS_SECOND = {"you", "your", "yours", "yourself", "yourselves"}
PRONOUNS_THIRD = {"he", "him", "his", "himself", "she", "her", "hers", "herself",
                   "it", "its", "itself", "they", "them", "their", "theirs", "themselves"}

CONJUNCTIONS = {"and", "but", "or", "nor", "for", "yet", "so",
                "because", "although", "while", "if", "unless", "until", "since", "after", "before"}


def _tokenize_simple(text: str) -> List[str]:
    """Simple whitespace + punctuation tokenizer."""
    return re.findall(r"\b\w+\b", text.lower())


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences using regex."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs."""
    paragraphs = re.split(r'\n\s*\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


# ---- Lexical Richness ----

def type_token_ratio(tokens: List[str]) -> float:
    """Type-Token Ratio: unique words / total words."""
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


def hapax_ratio(tokens: List[str]) -> float:
    """Ratio of words appearing exactly once."""
    if not tokens:
        return 0.0
    freq = Counter(tokens)
    hapax = sum(1 for v in freq.values() if v == 1)
    return hapax / len(tokens)


def mtld(tokens: List[str], threshold: float = 0.72) -> float:
    """
    Measure of Textual Lexical Diversity.
    Calculates the average number of consecutive words needed to reach the TTR threshold.
    """
    if len(tokens) < 10:
        return 0.0

    def _mtld_forward(toks):
        factors = 0.0
        segment_start = 0
        for i in range(1, len(toks) + 1):
            segment = toks[segment_start:i]
            ttr = len(set(segment)) / len(segment)
            if ttr <= threshold:
                factors += 1
                segment_start = i
        # Partial factor
        if segment_start < len(toks):
            remaining = toks[segment_start:]
            ttr = len(set(remaining)) / len(remaining)
            factors += (1 - ttr) / (1 - threshold) if threshold < 1 else 0
        return len(toks) / factors if factors > 0 else len(toks)

    forward = _mtld_forward(tokens)
    backward = _mtld_forward(tokens[::-1])
    return (forward + backward) / 2


def hd_d(tokens: List[str], sample_size: int = 42) -> float:
    """
    HD-D (vocd-D approximation): hypergeometric distribution D.
    Estimates vocabulary diversity independent of text length.
    """
    if len(tokens) < sample_size:
        return 0.0

    freq = Counter(tokens)
    n = len(tokens)
    contributions = 0.0

    for word_type, count in freq.items():
        # Probability of sampling this type at least once
        # using hypergeometric
        try:
            # P(X >= 1) = 1 - P(X = 0)
            # P(X=0) = C(count,0)*C(n-count, sample_size) / C(n, sample_size)
            log_p0 = (
                _log_comb(n - count, sample_size) - _log_comb(n, sample_size)
            )
            contributions += 1 - math.exp(log_p0)
        except (ValueError, OverflowError):
            contributions += 1.0  # If count is large, very likely to be sampled

    return contributions


def _log_comb(n: int, k: int) -> float:
    """Log of combination C(n, k) using lgamma."""
    if k < 0 or k > n:
        return float("-inf")
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


# ---- Full Feature Extractor ----

@dataclass
class StylometryFeatures:
    """All stylometric features for a text sample."""
    # Lexical richness
    ttr: float = 0.0
    mtld_score: float = 0.0
    hd_d_score: float = 0.0
    hapax: float = 0.0

    # Word statistics
    word_count: int = 0
    unique_word_count: int = 0
    avg_word_length: float = 0.0
    std_word_length: float = 0.0
    max_word_length: int = 0

    # Sentence statistics
    sentence_count: int = 0
    avg_sentence_length: float = 0.0
    std_sentence_length: float = 0.0
    max_sentence_length: int = 0
    min_sentence_length: int = 0

    # Paragraph statistics
    paragraph_count: int = 0
    avg_paragraph_length: float = 0.0

    # Function word ratio
    function_word_ratio: float = 0.0

    # Punctuation
    comma_ratio: float = 0.0
    period_ratio: float = 0.0
    question_ratio: float = 0.0
    exclamation_ratio: float = 0.0
    semicolon_ratio: float = 0.0
    colon_ratio: float = 0.0
    dash_ratio: float = 0.0
    quote_ratio: float = 0.0

    # Pronouns
    first_person_ratio: float = 0.0
    second_person_ratio: float = 0.0
    third_person_ratio: float = 0.0

    # Modals & conjunctions
    modal_ratio: float = 0.0
    conjunction_ratio: float = 0.0

    # Discourse markers
    discourse_marker_count: int = 0
    discourse_marker_ratio: float = 0.0

    # Contractions
    contraction_ratio: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to flat dictionary for ML features."""
        from dataclasses import asdict
        return asdict(self)

    def to_vector(self) -> List[float]:
        """Convert to feature vector."""
        d = self.to_dict()
        return [float(v) for v in d.values()]

    @staticmethod
    def feature_names() -> List[str]:
        """Return ordered feature names."""
        return list(StylometryFeatures().to_dict().keys())


def extract_stylometry(text: str) -> StylometryFeatures:
    """Extract all stylometric features from text."""
    tokens = _tokenize_simple(text)
    sentences = _split_sentences(text)
    paragraphs = _split_paragraphs(text)

    if not tokens:
        return StylometryFeatures()

    word_lengths = [len(t) for t in tokens]
    sentence_lengths = [len(_tokenize_simple(s)) for s in sentences] if sentences else [0]

    # Punctuation counts
    char_count = len(text) if text else 1

    features = StylometryFeatures(
        # Lexical richness
        ttr=type_token_ratio(tokens),
        mtld_score=mtld(tokens),
        hd_d_score=hd_d(tokens),
        hapax=hapax_ratio(tokens),

        # Word stats
        word_count=len(tokens),
        unique_word_count=len(set(tokens)),
        avg_word_length=sum(word_lengths) / len(word_lengths),
        std_word_length=_std(word_lengths),
        max_word_length=max(word_lengths),

        # Sentence stats
        sentence_count=len(sentences),
        avg_sentence_length=sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0,
        std_sentence_length=_std(sentence_lengths),
        max_sentence_length=max(sentence_lengths) if sentence_lengths else 0,
        min_sentence_length=min(sentence_lengths) if sentence_lengths else 0,

        # Paragraph stats
        paragraph_count=len(paragraphs),
        avg_paragraph_length=len(tokens) / len(paragraphs) if paragraphs else 0,

        # Function words
        function_word_ratio=sum(1 for t in tokens if t in FUNCTION_WORDS) / len(tokens),

        # Punctuation
        comma_ratio=text.count(",") / char_count,
        period_ratio=text.count(".") / char_count,
        question_ratio=text.count("?") / char_count,
        exclamation_ratio=text.count("!") / char_count,
        semicolon_ratio=text.count(";") / char_count,
        colon_ratio=text.count(":") / char_count,
        dash_ratio=(text.count("-") + text.count("—")) / char_count,
        quote_ratio=(text.count('"') + text.count("'") + text.count("\u201c") + text.count("\u201d")) / char_count,

        # Pronouns
        first_person_ratio=sum(1 for t in tokens if t in PRONOUNS_FIRST) / len(tokens),
        second_person_ratio=sum(1 for t in tokens if t in PRONOUNS_SECOND) / len(tokens),
        third_person_ratio=sum(1 for t in tokens if t in PRONOUNS_THIRD) / len(tokens),

        # Modals & conjunctions
        modal_ratio=sum(1 for t in tokens if t in MODAL_VERBS) / len(tokens),
        conjunction_ratio=sum(1 for t in tokens if t in CONJUNCTIONS) / len(tokens),

        # Discourse markers (check text for multi-word markers too)
        discourse_marker_count=sum(1 for dm in DISCOURSE_MARKERS if dm in text.lower()),
        discourse_marker_ratio=sum(1 for dm in DISCOURSE_MARKERS if dm in text.lower()) / len(sentences) if sentences else 0,

        # Contractions
        contraction_ratio=len(re.findall(r"\b\w+'\w+\b", text)) / len(tokens),
    )

    return features


def _std(values: List[float]) -> float:
    """Standard deviation."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)


class StylometryExtractor:
    """Wrapper class providing standard extractor interface."""

    def extract(self, text: str) -> Dict[str, Any]:
        return extract_stylometry(text).to_dict()

    def extract_vector(self, text: str) -> List[float]:
        return extract_stylometry(text).to_vector()

    def feature_names(self) -> List[str]:
        return StylometryFeatures.feature_names()
