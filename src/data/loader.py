"""
AegisText Dataset Loader & Ingestion Pipeline

Handles loading raw datasets (HC3, MAGE, RAID, etc.),
converting them into the canonical TextSample schema,
and writing processed datasets with manifests.
"""

import json
import csv
import os
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any, Iterator
from datetime import datetime

from src.data.schema import TextSample, TextOrigin, Domain, DatasetManifest, TransformationSeverity


class DatasetLoader:
    """Load and convert raw datasets into AegisText TextSample format."""

    def __init__(self, raw_dir: str = "datasets/raw", processed_dir: str = "datasets/processed"):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def load_jsonl(self, filepath: Path) -> Iterator[Dict[str, Any]]:
        """Load a JSONL file line by line."""
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)

    def load_csv(self, filepath: Path) -> Iterator[Dict[str, Any]]:
        """Load a CSV file as dicts."""
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield row

    def ingest_hc3(self, filepath: Path) -> List[TextSample]:
        """
        Ingest HC3 (Human ChatGPT Comparison) dataset.
        Expected format: JSONL with 'human_answers' and 'chatgpt_answers' fields.
        """
        samples = []
        for idx, record in enumerate(self.load_jsonl(filepath)):
            question = record.get("question", "")
            # Human answers
            for h_idx, answer in enumerate(record.get("human_answers", [])):
                samples.append(TextSample(
                    sample_id=f"hc3_human_{idx}_{h_idx}",
                    text=answer,
                    origin=TextOrigin.HUMAN,
                    domain=Domain.OTHER,
                    source_dataset="HC3",
                    source_id=f"{idx}_{h_idx}",
                    annotations={"question": question},
                ))
            # ChatGPT answers
            for a_idx, answer in enumerate(record.get("chatgpt_answers", [])):
                samples.append(TextSample(
                    sample_id=f"hc3_ai_{idx}_{a_idx}",
                    text=answer,
                    origin=TextOrigin.AI_RAW,
                    domain=Domain.OTHER,
                    source_dataset="HC3",
                    source_id=f"{idx}_{a_idx}",
                    generator="chatgpt",
                    annotations={"question": question},
                ))
        return samples

    def ingest_generic_labeled(
        self,
        filepath: Path,
        text_field: str = "text",
        label_field: str = "label",
        source_name: str = "generic",
        label_map: Optional[Dict[str, TextOrigin]] = None,
    ) -> List[TextSample]:
        """
        Ingest a generic labeled dataset (JSONL or CSV).
        label_map maps raw label strings to TextOrigin values.
        """
        if label_map is None:
            label_map = {
                "human": TextOrigin.HUMAN,
                "ai": TextOrigin.AI_RAW,
                "machine": TextOrigin.AI_RAW,
                "generated": TextOrigin.AI_RAW,
            }

        ext = filepath.suffix.lower()
        if ext == ".jsonl":
            records = self.load_jsonl(filepath)
        elif ext == ".csv":
            records = self.load_csv(filepath)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        samples = []
        for idx, record in enumerate(records):
            text = record.get(text_field, "")
            raw_label = str(record.get(label_field, "")).lower().strip()
            origin = label_map.get(raw_label, TextOrigin.HUMAN)

            samples.append(TextSample(
                sample_id=f"{source_name}_{idx}",
                text=text,
                origin=origin,
                domain=Domain.OTHER,
                source_dataset=source_name,
                source_id=str(idx),
                generator=record.get("generator", record.get("model", None)),
            ))
        return samples

    def save_processed(self, samples: List[TextSample], name: str, version: str = "1.0") -> Path:
        """Save processed samples as JSONL with a manifest."""
        from dataclasses import asdict

        out_dir = self.processed_dir / name / version
        out_dir.mkdir(parents=True, exist_ok=True)

        # Write samples
        samples_path = out_dir / "samples.jsonl"
        with open(samples_path, "w", encoding="utf-8") as f:
            for sample in samples:
                d = asdict(sample)
                d["origin"] = sample.origin.value
                d["domain"] = sample.domain.value
                d["transformation_severity"] = sample.transformation_severity.value
                f.write(json.dumps(d, ensure_ascii=False) + "\n")

        # Build manifest
        origin_dist: Dict[str, int] = {}
        domain_dist: Dict[str, int] = {}
        gen_dist: Dict[str, int] = {}
        for s in samples:
            origin_dist[s.origin.value] = origin_dist.get(s.origin.value, 0) + 1
            domain_dist[s.domain.value] = domain_dist.get(s.domain.value, 0) + 1
            if s.generator:
                gen_dist[s.generator] = gen_dist.get(s.generator, 0) + 1

        all_text = "".join(s.content_hash for s in samples)
        dataset_hash = hashlib.sha256(all_text.encode()).hexdigest()

        manifest = DatasetManifest(
            name=name,
            version=version,
            description=f"Processed {name} dataset",
            created_at=datetime.utcnow().isoformat(),
            total_samples=len(samples),
            origin_distribution=origin_dist,
            domain_distribution=domain_dist,
            generator_distribution=gen_dist,
            content_hash=dataset_hash,
        )

        manifest_path = out_dir / "manifest.json"
        from dataclasses import asdict as da
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(da(manifest), f, indent=2)

        return out_dir
