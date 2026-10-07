"""
AegisText Deduplication & Leakage Prevention

- Exact deduplication via content hashes
- Near-duplicate detection via MinHash/LSH
- Cross-split leakage detection (ensures transformed versions don't leak across splits)
- Grouped splitting (all versions of a source text stay in the same split)
"""

import hashlib
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict

from src.data.schema import TextSample


def compute_content_hash(text: str) -> str:
    """Compute SHA-256 hash of normalized text."""
    normalized = " ".join(text.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def exact_dedup(samples: List[TextSample]) -> Tuple[List[TextSample], int]:
    """
    Remove exact duplicates based on normalized content hash.
    Returns (deduplicated_samples, num_removed).
    """
    seen: Set[str] = set()
    deduped: List[TextSample] = []
    removed = 0

    for sample in samples:
        h = compute_content_hash(sample.text)
        if h not in seen:
            seen.add(h)
            deduped.append(sample)
        else:
            removed += 1

    return deduped, removed


def near_dedup_minhash(
    samples: List[TextSample],
    threshold: float = 0.8,
    num_perm: int = 128,
) -> Tuple[List[TextSample], List[Tuple[str, str, float]]]:
    """
    Remove near-duplicates using MinHash/LSH.
    Returns (deduplicated_samples, list_of_duplicate_pairs).
    """
    try:
        from datasketch import MinHash, MinHashLSH
    except ImportError:
        # Fallback: return input unchanged
        return samples, []

    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    minhashes: Dict[str, MinHash] = {}

    # Build MinHash for each sample
    for sample in samples:
        m = MinHash(num_perm=num_perm)
        words = sample.text.lower().split()
        # Use 3-grams (shingles)
        for i in range(len(words) - 2):
            shingle = " ".join(words[i:i + 3])
            m.update(shingle.encode("utf-8"))
        minhashes[sample.sample_id] = m

    # Insert into LSH and find duplicates
    duplicate_pairs: List[Tuple[str, str, float]] = []
    to_remove: Set[str] = set()

    for sid, mh in minhashes.items():
        if sid in to_remove:
            continue
        try:
            lsh.insert(sid, mh)
        except ValueError:
            # Already inserted (shouldn't happen with unique IDs)
            pass

    # Query each sample
    for sid, mh in minhashes.items():
        if sid in to_remove:
            continue
        results = lsh.query(mh)
        for other_sid in results:
            if other_sid != sid and other_sid not in to_remove:
                # Compute exact Jaccard
                jaccard = minhashes[sid].jaccard(minhashes[other_sid])
                if jaccard >= threshold:
                    duplicate_pairs.append((sid, other_sid, jaccard))
                    to_remove.add(other_sid)

    deduped = [s for s in samples if s.sample_id not in to_remove]
    return deduped, duplicate_pairs


def build_lineage_groups(samples: List[TextSample]) -> Dict[str, List[str]]:
    """
    Build lineage groups: all versions of a source text (original + transformations)
    must stay in the same split.

    Returns dict mapping group_id -> list of sample_ids.
    """
    # Find root for each sample by following parent_id chain
    parent_map = {s.sample_id: s.parent_id for s in samples}

    def find_root(sid: str) -> str:
        visited = set()
        current = sid
        while current in parent_map and parent_map[current] is not None:
            if current in visited:
                break  # cycle guard
            visited.add(current)
            current = parent_map[current]
        return current

    groups: Dict[str, List[str]] = defaultdict(list)
    for sample in samples:
        root = find_root(sample.sample_id)
        groups[root].append(sample.sample_id)

    return dict(groups)


def grouped_split(
    samples: List[TextSample],
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
) -> Dict[str, List[TextSample]]:
    """
    Split samples into train/val/test ensuring lineage groups stay together.
    """
    import random
    rng = random.Random(seed)

    groups = build_lineage_groups(samples)
    sample_map = {s.sample_id: s for s in samples}

    group_ids = list(groups.keys())
    rng.shuffle(group_ids)

    n = len(group_ids)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)

    splits: Dict[str, List[TextSample]] = {"train": [], "val": [], "test": []}

    for i, gid in enumerate(group_ids):
        if i < train_end:
            split_name = "train"
        elif i < val_end:
            split_name = "val"
        else:
            split_name = "test"

        for sid in groups[gid]:
            if sid in sample_map:
                sample_map[sid].split = split_name
                splits[split_name].append(sample_map[sid])

    return splits


def detect_cross_split_leakage(
    splits: Dict[str, List[TextSample]],
    threshold: float = 0.9,
) -> List[Dict]:
    """
    Detect potential data leakage across splits using content hashes and near-duplicate detection.
    Returns list of leakage warnings.
    """
    warnings = []

    # Check exact hash overlap
    split_hashes: Dict[str, Set[str]] = {}
    for split_name, samples in splits.items():
        split_hashes[split_name] = {compute_content_hash(s.text) for s in samples}

    split_names = list(splits.keys())
    for i in range(len(split_names)):
        for j in range(i + 1, len(split_names)):
            overlap = split_hashes[split_names[i]] & split_hashes[split_names[j]]
            if overlap:
                warnings.append({
                    "type": "exact_duplicate",
                    "splits": (split_names[i], split_names[j]),
                    "count": len(overlap),
                    "severity": "HIGH",
                })

    # Check lineage leakage
    split_assignment: Dict[str, str] = {}
    for split_name, samples in splits.items():
        for s in samples:
            split_assignment[s.sample_id] = split_name

    for split_name, samples in splits.items():
        for s in samples:
            if s.parent_id and s.parent_id in split_assignment:
                parent_split = split_assignment[s.parent_id]
                if parent_split != split_name:
                    warnings.append({
                        "type": "lineage_leakage",
                        "sample_id": s.sample_id,
                        "parent_id": s.parent_id,
                        "sample_split": split_name,
                        "parent_split": parent_split,
                        "severity": "CRITICAL",
                    })

    return warnings


class DeduplicationEngine:
    """Convenience class interface for deduplication and grouped splitting."""

    def __init__(self, threshold: float = 0.8, num_perm: int = 128):
        self.threshold = threshold
        self.num_perm = num_perm

    def exact_deduplicate(self, samples: List[TextSample]) -> Tuple[List[TextSample], Dict[str, Any]]:
        deduped, removed = exact_dedup(samples)
        return deduped, {"initial_count": len(samples), "exact_duplicates_removed": removed, "final_count": len(deduped)}

    def near_deduplicate(self, samples: List[TextSample]) -> Tuple[List[TextSample], List[Tuple[str, str, float]]]:
        return near_dedup_minhash(samples, threshold=self.threshold, num_perm=self.num_perm)

    def grouped_split(
        self,
        samples: List[TextSample],
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        seed: int = 42,
    ) -> Tuple[List[TextSample], List[TextSample], List[TextSample]]:
        splits = grouped_split(samples, train_ratio=train_ratio, val_ratio=val_ratio, test_ratio=test_ratio, seed=seed)
        return splits["train"], splits["val"], splits["test"]

