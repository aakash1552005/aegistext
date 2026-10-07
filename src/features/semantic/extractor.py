"""
AegisText Semantic & Perplexity Feature Extractor

Computes:
1. N-Gram Perplexity & Cross-Entropy Surprisal (Character and Word levels)
2. Sentence-to-Sentence Semantic Coherence & Transition Smoothness
3. Repetition & Semantic Monotony Index
4. Vocabulary Richness & Semantic Spread
"""

import math
import re
from collections import Counter
from typing import Dict, List, Any


class SemanticFeatureExtractor:
    """Extracts semantic, perplexity, and coherence features."""

    def __init__(self, n_gram_order: int = 3):
        self.n_gram_order = n_gram_order

    def _tokenize_words(self, text: str) -> List[str]:
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return words

    def _split_sentences(self, text: str) -> List[str]:
        sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        return sents

    def compute_word_ngram_perplexity(self, words: List[str], n: int = 2) -> Dict[str, float]:
        """
        Computes statistical n-gram cross-entropy and perplexity.
        AI text typically displays lower perplexity (more standard transitions).
        """
        if len(words) < n:
            return {"ngram_cross_entropy": 0.0, "ngram_perplexity": 1.0}

        # Count n-grams and (n-1)-grams
        ngrams = [tuple(words[i:i+n]) for i in range(len(words) - n + 1)]
        prefix_counts = Counter(ngrams[i][:-1] for i in range(len(ngrams)))
        ngram_counts = Counter(ngrams)

        vocab_size = max(len(set(words)), 10)
        alpha = 0.1  # Laplace smoothing

        log_prob_sum = 0.0
        for ng in ngrams:
            prefix = ng[:-1]
            count = ngram_counts[ng]
            prefix_count = prefix_counts[prefix]
            # Add-alpha smoothed conditional probability
            prob = (count + alpha) / (prefix_count + alpha * vocab_size)
            log_prob_sum += math.log2(prob)

        avg_neg_log_prob = -log_prob_sum / len(ngrams)
        # Cap perplexity to avoid overflow
        perplexity = min(2 ** avg_neg_log_prob, 10000.0)

        return {
            f"word_{n}gram_cross_entropy": round(avg_neg_log_prob, 4),
            f"word_{n}gram_perplexity": round(perplexity, 4),
        }

    def compute_sentence_coherence(self, sentences: List[str]) -> Dict[str, float]:
        """
        Measures sentence-to-sentence vocabulary overlap and semantic cosine similarity.
        Human writing typically has higher variance in inter-sentence similarity.
        """
        if len(sentences) < 2:
            return {
                "inter_sentence_jaccard_mean": 0.0,
                "inter_sentence_jaccard_std": 0.0,
                "semantic_monotony_index": 0.0,
            }

        sent_word_sets = [set(self._tokenize_words(s)) for s in sentences]
        jaccard_sims = []

        for i in range(len(sent_word_sets) - 1):
            s1 = sent_word_sets[i]
            s2 = sent_word_sets[i + 1]
            union = s1 | s2
            if union:
                jaccard = len(s1 & s2) / len(union)
            else:
                jaccard = 0.0
            jaccard_sims.append(jaccard)

        mean_sim = sum(jaccard_sims) / len(jaccard_sims)
        var_sim = sum((x - mean_sim) ** 2 for x in jaccard_sims) / len(jaccard_sims)
        std_sim = math.sqrt(var_sim)

        # Monotony index: high mean overlap with low variance implies robotic uniformity
        monotony = round(mean_sim / (std_sim + 0.05), 4)

        return {
            "inter_sentence_jaccard_mean": round(mean_sim, 4),
            "inter_sentence_jaccard_std": round(std_sim, 4),
            "semantic_monotony_index": monotony,
        }

    def compute_repetitive_ngrams(self, words: List[str]) -> Dict[str, float]:
        """Detects robotic phrasing repetitions and loops."""
        if len(words) < 6:
            return {"trigram_repetition_rate": 0.0, "quadgram_repetition_rate": 0.0}

        trigrams = [tuple(words[i:i+3]) for i in range(len(words) - 2)]
        quadgrams = [tuple(words[i:i+4]) for i in range(len(words) - 3)]

        unique_tri = len(set(trigrams))
        unique_quad = len(set(quadgrams))

        tri_rep = 1.0 - (unique_tri / len(trigrams))
        quad_rep = 1.0 - (unique_quad / len(quadgrams))

        return {
            "trigram_repetition_rate": round(max(0.0, tri_rep), 4),
            "quadgram_repetition_rate": round(max(0.0, quad_rep), 4),
        }

    def extract(self, text: str) -> Dict[str, float]:
        """Extracts complete dictionary of semantic features."""
        words = self._tokenize_words(text)
        sentences = self._split_sentences(text)

        feats: Dict[str, float] = {}
        feats.update(self.compute_word_ngram_perplexity(words, n=2))
        feats.update(self.compute_word_ngram_perplexity(words, n=3))
        feats.update(self.compute_sentence_coherence(sentences))
        feats.update(self.compute_repetitive_ngrams(words))

        return feats

    def extract_vector(self, text: str) -> List[float]:
        feats = self.extract(text)
        return list(feats.values())

    def feature_names(self) -> List[str]:
        dummy = "This is a sample document to discover feature keys."
        return list(self.extract(dummy).keys())
