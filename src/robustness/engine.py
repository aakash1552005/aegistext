"""
AegisText Robustness & Adversarial Perturbation Engine

Simulates realistic adversarial attacks and humanization transformations:
1. Zero-width unicode insertion (Adversarial Evasion)
2. Homoglyph confusable substitution
3. Synonym replacement (Vocabulary manipulation)
4. Punctuation jittering & typo simulation
5. Sentence split & merge (Burstiness manipulation)
6. Commercial Humanizer simulation (QuillBot/UndetectableAI multi-technique pipeline)
"""

import random
import re
from typing import List, Dict, Tuple, Any

from src.preprocessing.normalizer import HOMOGLYPH_MAP, ZERO_WIDTH_CHARS

# Common synonym mappings for evasion
SYNONYMS = {
    "important": ["crucial", "essential", "vital", "significant", "key"],
    "show": ["demonstrate", "illustrate", "exhibit", "reveal", "display"],
    "use": ["utilize", "employ", "leverage", "apply", "harness"],
    "help": ["assist", "aid", "facilitate", "support"],
    "make": ["generate", "produce", "create", "construct"],
    "good": ["favorable", "advantageous", "beneficial", "sound"],
    "bad": ["adverse", "detrimental", "unfavorable", "suboptimal"],
    "often": ["frequently", "commonly", "typically", "routinely"],
    "fast": ["rapid", "swift", "expeditious", "speedy"],
    "slow": ["gradual", "deliberate", "measured", "unhurried"],
    "furthermore": ["moreover", "in addition", "additionally", "what is more"],
    "consequently": ["as a result", "therefore", "thus", "accordingly"],
    "however": ["nevertheless", "yet", "nonetheless", "conversely"],
    "in conclusion": ["to summarize", "in summary", "overall", "to conclude"],
}

# Humanizer fillers used to reduce standard AI formulaic predictability
HUMANIZER_FILLERS = [
    "Honestly,", "To be fair,", "In reality,", "As it turns out,",
    "Interestingly enough,", "Frankly speaking,", "Mind you,", "In practice,"
]


class AdversarialPerturbationEngine:
    """Applies controlled adversarial transformations to text for robustness evaluation."""

    def __init__(self, seed: int = 42):
        self.random = random.Random(seed)

    def inject_zero_width_chars(self, text: str, rate: float = 0.05) -> str:
        """Injects invisible zero-width characters into words to break tokenization."""
        zw_chars = list(ZERO_WIDTH_CHARS.keys())
        chars = list(text)
        result = []
        for c in chars:
            result.append(c)
            if c.isalnum() and self.random.random() < rate:
                result.append(self.random.choice(zw_chars))
        return "".join(result)

    def inject_homoglyphs(self, text: str, rate: float = 0.08) -> str:
        """Replaces standard ASCII characters with visually identical homoglyphs."""
        result = []
        # Invert map: Latin char -> possible homoglyphs
        latin_to_homo: Dict[str, List[str]] = {}
        for homo, latin in HOMOGLYPH_MAP.items():
            latin_to_homo.setdefault(latin, []).append(homo)

        for c in text:
            if c in latin_to_homo and self.random.random() < rate:
                result.append(self.random.choice(latin_to_homo[c]))
            else:
                result.append(c)
        return "".join(result)

    def substitute_synonyms(self, text: str, rate: float = 0.15) -> str:
        """Substitutes frequent words with synonyms to alter perplexity and n-grams."""
        words = text.split()
        res = []
        for w in words:
            clean = re.sub(r'[^\w]', '', w).lower()
            if clean in SYNONYMS and self.random.random() < rate:
                syn = self.random.choice(SYNONYMS[clean])
                # preserve casing if possible
                if w.istitle():
                    syn = syn.capitalize()
                # preserve trailing punctuation
                trail = ""
                if w and not w[-1].isalnum():
                    trail = w[-1]
                res.append(syn + trail)
            else:
                res.append(w)
        return " ".join(res)

    def jitter_punctuation_and_sentences(self, text: str) -> str:
        """Manipulates sentence boundaries and punctuation rhythm to spoof burstiness."""
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        if not sentences:
            return text

        new_sentences = []
        for i, s in enumerate(sentences):
            # occasionally split a compound sentence
            if ", and " in s and self.random.random() < 0.3:
                parts = s.split(", and ", 1)
                new_sentences.append(parts[0] + ".")
                new_sentences.append("And " + parts[1])
            elif ", but " in s and self.random.random() < 0.3:
                parts = s.split(", but ", 1)
                new_sentences.append(parts[0] + ".")
                new_sentences.append("However, " + parts[1])
            else:
                new_sentences.append(s)

        # occasionally inject conversational filler to start of a sentence
        if new_sentences and self.random.random() < 0.4:
            idx = self.random.randint(0, len(new_sentences) - 1)
            filler = self.random.choice(HUMANIZER_FILLERS)
            new_sentences[idx] = f"{filler} {new_sentences[idx]}"

        return " ".join(new_sentences)

    def simulate_commercial_humanizer(self, text: str, severity: str = "medium") -> str:
        """
        Simulates an advanced AI Humanizer (e.g. QuillBot, Undetectable.ai):
        Combines synonym substitution, discourse restyling, and sentence restructuring.
        """
        rates = {
            "low": {"syn": 0.08, "jitter": 0.2},
            "medium": {"syn": 0.18, "jitter": 0.5},
            "high": {"syn": 0.30, "jitter": 0.8},
        }.get(severity, {"syn": 0.18, "jitter": 0.5})

        transformed = self.substitute_synonyms(text, rate=rates["syn"])
        transformed = self.jitter_punctuation_and_sentences(transformed)
        return transformed

    def apply_attack(self, text: str, attack_type: str, severity: float = 0.5) -> Tuple[str, Dict[str, Any]]:
        """
        Unified dispatch for applying adversarial attacks.
        Returns: (perturbed_text, metadata)
        """
        if attack_type == "zero_width":
            rate = 0.02 + 0.08 * severity
            pert = self.inject_zero_width_chars(text, rate=rate)
        elif attack_type == "homoglyph":
            rate = 0.03 + 0.12 * severity
            pert = self.inject_homoglyph_sub = self.inject_homoglyphs(text, rate=rate)
            pert = pert
        elif attack_type == "synonym":
            rate = 0.05 + 0.25 * severity
            pert = self.substitute_synonyms(text, rate=rate)
        elif attack_type == "humanizer":
            sev_level = "low" if severity < 0.33 else ("medium" if severity < 0.67 else "high")
            pert = self.simulate_commercial_humanizer(text, severity=sev_level)
        elif attack_type == "combined":
            # Multi-vector attack
            pert = self.inject_homoglyphs(text, rate=0.03 * severity)
            pert = self.substitute_synonyms(pert, rate=0.15 * severity)
            pert = self.jitter_punctuation_and_sentences(pert)
        else:
            pert = text

        return pert, {
            "attack_type": attack_type,
            "severity": severity,
            "original_length": len(text),
            "perturbed_length": len(pert),
        }
