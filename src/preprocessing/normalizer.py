"""
AegisText Preprocessing & Adversarial Sanitization Pipeline

Provides:
- Unicode normalization (NFKC)
- Zero-width character and invisible unicode injection detection & removal
- Homoglyph / confusable character normalization
- Whitespace and formatting normalization
- Adversarial artifact inspection report
"""

import re
import unicodedata
from typing import Dict, Any, Tuple, List

# Common homoglyph mappings (Cyrillic / Greek / Latin confusables frequently used in evading detectors)
HOMOGLYPH_MAP = {
    'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'у': 'y', 'х': 'x',  # Cyrillic lower
    'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M', 'Н': 'H', 'О': 'O',  # Cyrillic upper
    'Р': 'P', 'С': 'C', 'Т': 'T', 'Х': 'X',
    'α': 'a', 'β': 'b', 'ο': 'o', 'ν': 'v', 'τ': 't',                     # Greek lower
    'Α': 'A', 'Β': 'B', 'Ε': 'E', 'Ζ': 'Z', 'Η': 'H', 'Ι': 'I', 'Κ': 'K',  # Greek upper
    'Μ': 'M', 'Ν': 'N', 'Ο': 'O', 'Ρ': 'P', 'Τ': 'T', 'Υ': 'Y', 'Χ': 'X',
    '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',                 # Full-width digits
    '５': '5', '６': '6', '７': '7', '８': '8', '９': '9',
}

# Zero-width and hidden unicode characters
ZERO_WIDTH_CHARS = {
    '\u200b': 'ZERO_WIDTH_SPACE',
    '\u200c': 'ZERO_WIDTH_NON_JOINER',
    '\u200d': 'ZERO_WIDTH_JOINER',
    '\u2060': 'WORD_JOINER',
    '\ufeff': 'ZERO_WIDTH_NO_BREAK_SPACE',
    '\u00ad': 'SOFT_HYPHEN',
    '\u200e': 'LEFT_TO_RIGHT_MARK',
    '\u200f': 'RIGHT_TO_LEFT_MARK',
}


class TextSanitizer:
    """Sanitizes text and inspects it for adversarial character-level tampering."""

    def __init__(self, strip_homoglyphs: bool = True, strip_zero_width: bool = True):
        self.strip_homoglyphs = strip_homoglyphs
        self.strip_zero_width = strip_zero_width

    def inspect_adversarial_artifacts(self, text: str) -> Dict[str, Any]:
        """
        Inspect text for adversarial tampering markers without altering text.
        Returns a detailed report.
        """
        zero_width_found: List[Dict[str, Any]] = []
        homoglyphs_found: List[Dict[str, Any]] = []

        for idx, char in enumerate(text):
            if char in ZERO_WIDTH_CHARS:
                zero_width_found.append({
                    "char": repr(char),
                    "name": ZERO_WIDTH_CHARS[char],
                    "position": idx
                })
            elif char in HOMOGLYPH_MAP:
                homoglyphs_found.append({
                    "char": char,
                    "replacement": HOMOGLYPH_MAP[char],
                    "unicode_name": unicodedata.name(char, "UNKNOWN"),
                    "position": idx
                })

        # Check for mixed script anomalies (e.g., Latin mixed with Cyrillic)
        has_suspicious_mixed_scripts = len(homoglyphs_found) > 0 and any(ord(c) < 128 for c in text)

        return {
            "adversarial_markers_present": len(zero_width_found) > 0 or len(homoglyphs_found) > 0,
            "zero_width_count": len(zero_width_found),
            "zero_width_details": zero_width_found[:20],  # cap details
            "homoglyph_count": len(homoglyphs_found),
            "homoglyph_details": homoglyphs_found[:20],
            "mixed_script_anomaly": has_suspicious_mixed_scripts,
            "adversarial_risk_score": min(1.0, (len(zero_width_found) * 0.2 + len(homoglyphs_found) * 0.1)),
        }

    def sanitize(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Sanitizes text by removing hidden characters, normalising homoglyphs,
        and applying standard NFKC canonicalization.
        Returns: (sanitized_text, audit_report)
        """
        if not text:
            return "", {"adversarial_markers_present": False, "zero_width_count": 0, "homoglyph_count": 0}

        report = self.inspect_adversarial_artifacts(text)
        cleaned = text

        # 1. Remove zero-width characters
        if self.strip_zero_width and report["zero_width_count"] > 0:
            for char in ZERO_WIDTH_CHARS:
                cleaned = cleaned.replace(char, "")

        # 2. Normalize homoglyphs
        if self.strip_homoglyphs and report["homoglyph_count"] > 0:
            for bad_char, good_char in HOMOGLYPH_MAP.items():
                cleaned = cleaned.replace(bad_char, good_char)

        # 3. Unicode normalization (NFKC decomposes compatibility chars and canonicalizes)
        cleaned = unicodedata.normalize('NFKC', cleaned)

        # 4. Normalize multiple whitespaces except single paragraph linebreaks
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        cleaned = cleaned.strip()

        return cleaned, report
