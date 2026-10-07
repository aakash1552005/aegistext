"""
AegisText Predictability Feature Extractor

Extracts features that measure how "predictable" the text is —
AI text tends to be more predictable and less bursty than human text.

Features:
- Token-level entropy and burstiness (statistical, no LM needed)
- Repetition metrics (n-gram repeat rate, vocabulary recycling)
- Word rank statistics (zipfian distribution analysis)
- Sentence-level regularity measures

NOTE: Perplexity-based features (requiring a language model) are implemented
in a separate module that depends on transformers/torch.
"""

import re
import math
from collections import Counter
from typing import Dict, List, Any
from dataclasses import dataclass, asdict


TOKEN_PATTERN = re.compile(r"\b\w+\b")


def _tokenize(text: str) -> List[str]:
    return TOKEN_PATTERN.findall(text.lower())


def _ngrams(tokens: List[str], n: int) -> List[str]:
    return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


@dataclass
class PredictabilityFeatures:
    """All predictability features for a text sample."""
    # Entropy-based
    unigram_entropy: float = 0.0
    bigram_entropy: float = 0.0
    trigram_entropy: float = 0.0
    char_entropy: float = 0.0

    # Burstiness
    burstiness: float = 0.0  # (std - mean) / (std + mean) of inter-arrival times
    vocab_burstiness: float = 0.0

    # Repetition
    bigram_repeat_rate: float = 0.0   # fraction of bigrams appearing >1 time
    trigram_repeat_rate: float = 0.0
    exact_sentence_repeat_rate: float = 0.0

    # Word rank statistics
    avg_word_rank: float = 0.0    # average position in frequency-sorted vocabulary
    std_word_rank: float = 0.0
    top10_coverage: float = 0.0   # fraction of text covered by top-10 words
    top50_coverage: float = 0.0

    # Vocabulary recycling
    new_word_rate: float = 0.0    # rate of introducing new words through the text
    vocab_growth_rate: float = 0.0

    # Sentence regularity
    sentence_length_cv: float = 0.0  # coefficient of variation
    sentence_start_entropy: float = 0.0  # entropy of sentence-starting words

    # Conditional entropy approximation (bigram)
    conditional_entropy: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_vector(self) -> List[float]:
        return [float(v) for v in self.to_dict().values()]

    @staticmethod
    def feature_names() -> List[str]:
        return list(PredictabilityFeatures().to_dict().keys())


def _entropy(counter: Counter, total: int) -> float:
    """Shannon entropy from a Counter."""
    if total == 0:
        return 0.0
    ent = 0.0
    for count in counter.values():
        if count > 0:
            p = count / total
            ent -= p * math.log2(p)
    return ent


def _burstiness_measure(tokens: List[str]) -> float:
    """
    Burstiness: measures how irregular word occurrences are.
    B = (sigma - mu) / (sigma + mu) where sigma = std, mu = mean of inter-arrival times.
    AI text tends to have lower burstiness (more uniform).
    """
    if len(tokens) < 10:
        return 0.0

    # Compute inter-arrival times for each word type
    positions: Dict[str, List[int]] = {}
    for i, token in enumerate(tokens):
        if token not in positions:
            positions[token] = []
        positions[token].append(i)

    all_intervals = []
    for word, pos_list in positions.items():
        if len(pos_list) < 2:
            continue
        intervals = [pos_list[i] - pos_list[i - 1] for i in range(1, len(pos_list))]
        all_intervals.extend(intervals)

    if not all_intervals:
        return 0.0

    mean = sum(all_intervals) / len(all_intervals)
    if len(all_intervals) < 2:
        return 0.0
    variance = sum((x - mean) ** 2 for x in all_intervals) / (len(all_intervals) - 1)
    std = math.sqrt(variance)

    if std + mean == 0:
        return 0.0
    return (std - mean) / (std + mean)


def _new_word_rate(tokens: List[str]) -> float:
    """Fraction of tokens that are being seen for the first time at their position."""
    if not tokens:
        return 0.0
    seen = set()
    new_count = 0
    for t in tokens:
        if t not in seen:
            new_count += 1
            seen.add(t)
    return new_count / len(tokens)


def _vocab_growth_rate(tokens: List[str], window_size: int = 50) -> float:
    """
    Average rate of new vocabulary introduction per window.
    Lower for AI text (which tends to reuse vocabulary more uniformly).
    """
    if len(tokens) < window_size * 2:
        return 0.0

    rates = []
    for i in range(0, len(tokens) - window_size, window_size):
        window = tokens[i:i + window_size]
        unique = len(set(window))
        rates.append(unique / window_size)

    if not rates:
        return 0.0
    return sum(rates) / len(rates)


def extract_predictability(text: str) -> PredictabilityFeatures:
    """Extract all predictability features from text."""
    tokens = _tokenize(text)
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    if not tokens:
        return PredictabilityFeatures()

    # N-gram counters
    uni_counter = Counter(tokens)
    bi_grams = _ngrams(tokens, 2)
    tri_grams = _ngrams(tokens, 3)
    bi_counter = Counter(bi_grams)
    tri_counter = Counter(tri_grams)

    # Character-level entropy
    char_counter = Counter(text.lower())
    char_total = len(text)

    # Sentence lengths
    sent_lengths = [len(s.split()) for s in sentences] if sentences else [0]
    sent_mean = sum(sent_lengths) / len(sent_lengths)
    sent_std = math.sqrt(
        sum((x - sent_mean) ** 2 for x in sent_lengths) / max(len(sent_lengths) - 1, 1)
    )
    sent_cv = sent_std / sent_mean if sent_mean > 0 else 0

    # Sentence starters
    starters = [s.strip().split()[0].lower() if s.strip().split() else "" for s in sentences]
    starter_counter = Counter(starters)

    # Word rank statistics
    sorted_words = uni_counter.most_common()
    rank_map = {word: rank for rank, (word, _) in enumerate(sorted_words)}
    ranks = [rank_map[t] for t in tokens]
    avg_rank = sum(ranks) / len(ranks)
    std_rank = math.sqrt(sum((r - avg_rank) ** 2 for r in ranks) / max(len(ranks) - 1, 1))

    # Top-N coverage
    top_10_words = {w for w, _ in sorted_words[:10]}
    top_50_words = {w for w, _ in sorted_words[:50]}
    top10_cov = sum(1 for t in tokens if t in top_10_words) / len(tokens)
    top50_cov = sum(1 for t in tokens if t in top_50_words) / len(tokens)

    # Bigram/trigram repeat rate
    bi_repeats = sum(1 for c in bi_counter.values() if c > 1) / max(len(bi_counter), 1)
    tri_repeats = sum(1 for c in tri_counter.values() if c > 1) / max(len(tri_counter), 1)

    # Exact sentence repetition
    sent_normalized = [" ".join(s.lower().split()) for s in sentences]
    sent_counter = Counter(sent_normalized)
    sent_repeat = sum(1 for c in sent_counter.values() if c > 1) / max(len(sent_counter), 1)

    # Conditional entropy: H(X|Y) = H(X,Y) - H(Y)
    bi_entropy = _entropy(bi_counter, len(bi_grams))
    uni_entropy = _entropy(uni_counter, len(tokens))
    cond_entropy = max(0, bi_entropy - uni_entropy)

    return PredictabilityFeatures(
        unigram_entropy=uni_entropy,
        bigram_entropy=bi_entropy,
        trigram_entropy=_entropy(tri_counter, len(tri_grams)),
        char_entropy=_entropy(char_counter, char_total),
        burstiness=_burstiness_measure(tokens),
        vocab_burstiness=_burstiness_measure(list(uni_counter.keys())),
        bigram_repeat_rate=bi_repeats,
        trigram_repeat_rate=tri_repeats,
        exact_sentence_repeat_rate=sent_repeat,
        avg_word_rank=avg_rank,
        std_word_rank=std_rank,
        top10_coverage=top10_cov,
        top50_coverage=top50_cov,
        new_word_rate=_new_word_rate(tokens),
        vocab_growth_rate=_vocab_growth_rate(tokens),
        sentence_length_cv=sent_cv,
        sentence_start_entropy=_entropy(starter_counter, len(starters)),
        conditional_entropy=cond_entropy,
    )


class PredictabilityExtractor:
    """Wrapper class providing standard extractor interface."""

    def extract(self, text: str) -> Dict[str, Any]:
        return extract_predictability(text).to_dict()

    def extract_vector(self, text: str) -> List[float]:
        return extract_predictability(text).to_vector()

    def feature_names(self) -> List[str]:
        return PredictabilityFeatures.feature_names()

