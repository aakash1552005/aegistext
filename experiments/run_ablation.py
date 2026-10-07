"""
AegisText Multi-Signal Feature Ablation Experiment

Tests Claim C5: Multi-signal fusion improves detection over single-signal approaches.
Evaluates:
1. Stylometry only
2. Structural only
3. Predictability only
4. Semantic only
5. Full Fusion (Stylometry + Structural + Predictability + Semantic)
"""

import os
import json
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from src.data.schema import TextSample, TextOrigin
from src.features.pipeline import MasterFeaturePipeline
from src.evaluation.metrics import evaluate_detector_predictions
from experiments.run_benchmark import load_split_samples


def run_ablation_study():
    print("=" * 60)
    print(" AegisText Multi-Signal Feature Ablation Study")
    print("=" * 60)

    data_dir = "data/processed"
    train_samples = load_split_samples(os.path.join(data_dir, "train.jsonl"))
    test_samples = load_split_samples(os.path.join(data_dir, "test.jsonl"))

    pipeline = MasterFeaturePipeline()
    feature_names = pipeline.feature_names

    X_train_full, _ = pipeline.extract_batch([s.text for s in train_samples])
    y_train = np.array([0 if s.origin == TextOrigin.HUMAN else 1 for s in train_samples], dtype=int)

    X_test_full, _ = pipeline.extract_batch([s.text for s in test_samples])
    y_test = np.array([0 if s.origin == TextOrigin.HUMAN else 1 for s in test_samples], dtype=int)

    # Subsets
    feature_subsets = {
        "Stylometry_Only": [i for i, name in enumerate(feature_names) if name.startswith("sty_")],
        "Structural_Only": [i for i, name in enumerate(feature_names) if name.startswith("str_")],
        "Predictability_Only": [i for i, name in enumerate(feature_names) if name.startswith("prd_")],
        "Semantic_Only": [i for i, name in enumerate(feature_names) if name.startswith("sem_")],
        "Full_MultiSignal_Fusion": list(range(len(feature_names))),
    }

    ablation_results = {}

    for name, indices in feature_subsets.items():
        print(f"\nTraining on subset: {name} ({len(indices)} features)...")
        X_tr = X_train_full[:, indices]
        X_te = X_test_full[:, indices]

        clf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
        clf.fit(X_tr, y_train)

        probs = clf.predict_proba(X_te)[:, 1]
        metrics = evaluate_detector_predictions(y_test, probs)
        ablation_results[name] = {
            "num_features": len(indices),
            "roc_auc": metrics["roc_auc"],
            "pr_auc": metrics["pr_auc"],
            "f1_binary": metrics["f1_binary"],
            "accuracy": metrics["accuracy"],
            "ece": metrics["ece"],
        }
        print(f"  ROC-AUC: {metrics['roc_auc']:.4f} | F1: {metrics['f1_binary']:.4f} | Accuracy: {metrics['accuracy']:.4f}")

    out_file = "research/experiments/ablation_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(ablation_results, f, indent=2)

    print(f"\nAblation study results written to {out_file}")
    return ablation_results


if __name__ == "__main__":
    run_ablation_study()
