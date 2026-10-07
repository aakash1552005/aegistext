"""
AegisText Dataset Schema & Data Models

Defines the canonical data types for all text samples flowing through the system.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib


class TextOrigin(Enum):
    """Classification of text origin."""
    HUMAN = "HUMAN"
    AI_RAW = "AI_RAW"
    AI_HUMANIZED = "AI_HUMANIZED"
    AI_PARAPHRASED = "AI_PARAPHRASED"
    HUMAN_EDITED_AI = "HUMAN_EDITED_AI"
    HUMAN_PARAPHRASED = "HUMAN_PARAPHRASED"
    ADVERSARIAL_AI = "ADVERSARIAL_AI"
    MIXED_AUTHORED = "MIXED_AUTHORED"


class TransformationSeverity(Enum):
    """Severity level of text transformation."""
    NONE = "NONE"
    LIGHT = "LIGHT"
    MEDIUM = "MEDIUM"
    HEAVY = "HEAVY"
    UNKNOWN = "UNKNOWN"


class Domain(Enum):
    """Content domain categories."""
    ACADEMIC = "ACADEMIC"
    NEWS = "NEWS"
    ESSAY = "ESSAY"
    TECHNICAL = "TECHNICAL"
    BUSINESS = "BUSINESS"
    CREATIVE = "CREATIVE"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    OTHER = "OTHER"


@dataclass
class TextSample:
    """A single text sample in the AegisText dataset."""
    sample_id: str
    text: str
    origin: TextOrigin
    domain: Domain
    language: str = "en"

    # Source tracking
    source_dataset: str = ""
    source_id: str = ""
    generator: Optional[str] = None          # e.g., "gpt-4", "claude-3", "llama-3"
    humanizer: Optional[str] = None          # e.g., "quillbot", "wordtune", "manual"
    transformation_severity: TransformationSeverity = TransformationSeverity.NONE

    # Lineage — link to parent sample before transformation
    parent_id: Optional[str] = None

    # Metadata
    word_count: int = 0
    char_count: int = 0
    sentence_count: int = 0
    content_hash: str = ""
    created_at: str = ""

    # Split assignment
    split: Optional[str] = None  # "train", "val", "test"
    fold: Optional[int] = None

    # Optional annotations
    annotations: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.word_count:
            self.word_count = len(self.text.split())
        if not self.char_count:
            self.char_count = len(self.text)
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.text.encode("utf-8")).hexdigest()
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert sample to JSON-serializable dictionary."""
        return {
            "sample_id": self.sample_id,
            "text": self.text,
            "origin": self.origin.value if isinstance(self.origin, TextOrigin) else str(self.origin),
            "domain": self.domain.value if isinstance(self.domain, Domain) else str(self.domain),
            "language": self.language,
            "source_dataset": self.source_dataset,
            "source_id": self.source_id,
            "generator": self.generator,
            "humanizer": self.humanizer,
            "transformation_severity": self.transformation_severity.value if isinstance(self.transformation_severity, TransformationSeverity) else str(self.transformation_severity),
            "parent_id": self.parent_id,
            "word_count": self.word_count,
            "char_count": self.char_count,
            "sentence_count": self.sentence_count,
            "content_hash": self.content_hash,
            "created_at": self.created_at,
            "split": self.split,
            "fold": self.fold,
            "annotations": self.annotations,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TextSample":
        """Reconstruct TextSample from dictionary."""
        data_copy = dict(data)
        if "origin" in data_copy and isinstance(data_copy["origin"], str):
            data_copy["origin"] = TextOrigin(data_copy["origin"])
        if "domain" in data_copy and isinstance(data_copy["domain"], str):
            data_copy["domain"] = Domain(data_copy["domain"])
        if "transformation_severity" in data_copy and isinstance(data_copy["transformation_severity"], str):
            data_copy["transformation_severity"] = TransformationSeverity(data_copy["transformation_severity"])
        return cls(**data_copy)


@dataclass
class DatasetManifest:
    """Metadata for a complete dataset version."""
    name: str
    version: str
    description: str
    created_at: str
    total_samples: int = 0
    origin_distribution: Dict[str, int] = field(default_factory=dict)
    domain_distribution: Dict[str, int] = field(default_factory=dict)
    generator_distribution: Dict[str, int] = field(default_factory=dict)
    humanizer_distribution: Dict[str, int] = field(default_factory=dict)
    split_sizes: Dict[str, int] = field(default_factory=dict)
    content_hash: str = ""  # Hash of the entire dataset for versioning
    source_datasets: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class SegmentAnnotation:
    """Annotation for a segment within a mixed-authorship document."""
    start_offset: int
    end_offset: int
    origin: TextOrigin
    confidence: float = 0.0
    text_snippet: str = ""
