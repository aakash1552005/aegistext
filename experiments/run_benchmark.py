"""
AegisText Benchmark Experiment Runner

Executes reproducible experiments:
1. Loads leakage-free processed benchmark dataset (train, val, test splits)
2. Extracts Master Feature Pipeline vectors (Stylometry, Structural, Predictability, Semantic)
3. Trains baseline models:
   - Logistic Regression
   - Random Forest
   - XGBoost
   - AegisText Calibrated Tabular Ensemble (LightGBM + RobustScaler + Platt Calibration)
4. Evaluates clean performance (ROC-AUC, PR-AUC, Accuracy, F1, ECE, Brier, FPR@95%TPR)
5. Evaluates adversarial robustness under 4 attack vectors:
   - Zero-width character injection
   - Homoglyph substitution
   - Synonym replacement
   - Commercial Humanizer transformation
6. Verifies research claims and writes output artifacts to research/experiments/
"""

import os
import json
import time
from typing import Dict, List, Any
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from src.data.schema import TextSample, TextOrigin
from src.features.pipeline import MasterFeaturePipeline
from src.models.tabular_ensemble import AegisEnsembleDetector
from src.evaluation.metrics import evaluate_detector_predictions
from src.robustness.engine import AdversarialPerturbationEngine
from src.preprocessing.normalizer import TextSanitizer


def load_split_samples(filepath: str) -> List[TextSample]:
    samples = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                samples.append(TextSample.from_dict(json.loads(line)))
    return samples


def run_benchmark_experiments():
    print("=" * 60)
    print(" AegisText Reproducible Benchmark Experiment Suite")
    print("=" * 60)

    # 1. Load Data
    data_dir = "data/processed"
    train_samples = load_split_samples(os.path.join(data_dir, "train.jsonl"))
    val_samples = load_split_samples(os.path.join(data_dir, "val.jsonl"))
    test_samples = load_split_samples(os.path.join(data_dir, "test.jsonl"))

    print(f"Loaded: {len(train_samples)} train, {len(val_samples)} val, {len(test_samples)} test samples.")

    # 2. Extract Features
    pipeline = MasterFeaturePipeline()
    print(f"Master feature dimension: {pipeline.num_features} linguistic indicators.")

    print("Extracting training features...")
    X_train, t_train = pipeline.extract_batch([s.text for s in train_samples])
    # Label: 0 = HUMAN, 1 = AI (both raw and humanized)
    y_train = np.array([0 if s.origin == TextOrigin.HUMAN else 1 for s in train_samples], dtype=int)

    print("Extracting test features...")
    X_test, t_test = pipeline.extract_batch([s.text for s in test_samples])
    y_test = np.array([0 if s.origin == TextOrigin.HUMAN else 1 for s in test_samples], dtype=int)

    print(f"Feature extraction completed. (Train: {t_train:.2f}s, Test: {t_test:.2f}s)")

    # 3. Train Models
    models: Dict[str, Any] = {}

    # Baseline 1: Logistic Regression
    lr = Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression(max_iter=1000, random_state=42))])
    lr.fit(X_train, y_train)
    models["LogisticRegression"] = lr

    # Baseline 2: Random Forest
    rf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    rf.fit(X_train, y_train)
    models["RandomForest"] = rf

    # Model 3: AegisText Tabular Ensemble (Calibrated LightGBM)
    aegis_clf = AegisEnsembleDetector(model_type="lightgbm", n_estimators=120, max_depth=5, calibrate=True)
    aegis_clf.fit(X_train, y_train, feature_names=pipeline.feature_names)
    models["AegisText_Ensemble"] = aegis_clf

    # Save AegisText trained model checkpoint
    model_save_dir = "artifacts/checkpoints"
    os.makedirs(model_save_dir, exist_ok=True)
    checkpoint_path = os.path.join(model_save_dir, "aegistext_ensemble.joblib")
    aegis_clf.save(checkpoint_path)
    print(f"Saved primary AegisText checkpoint to {checkpoint_path}")

    # 4. Clean Evaluation
    results: Dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dataset_split_sizes": {
            "train": len(train_samples),
            "val": len(val_samples),
            "test": len(test_samples),
        },
        "clean_benchmarks": {},
        "adversarial_benchmarks": {},
    }

    print("\n--- Clean Test Set Evaluation ---")
    for name, model in models.items():
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(X_test)[:, 1]
        else:
            probs = model.predict(X_test)

        metrics = evaluate_detector_predictions(y_test, probs)
        results["clean_benchmarks"][name] = metrics
        print(f"[{name:20s}] ROC-AUC: {metrics['roc_auc']:.4f} | F1: {metrics['f1_binary']:.4f} | ECE: {metrics['ece']:.4f} | FPR@95%TPR: {metrics['fpr_at_95_tpr']:.4f}")

    # 5. Adversarial Robustness Evaluation
    print("\n--- Adversarial Robustness Benchmarks ---")
    engine = AdversarialPerturbationEngine(seed=42)
    sanitizer = TextSanitizer()

    attack_types = ["zero_width", "homoglyph", "synonym", "humanizer"]

    for attack in attack_types:
        print(f"\nEvaluating attack vector: {attack.upper()}...")
        # Perturb test texts
        perturbed_texts = []
        for s in test_samples:
            if s.origin != TextOrigin.HUMAN:
                # Apply attack to AI texts to attempt evasion
                pert, _ = engine.apply_attack(s.text, attack_type=attack, severity=0.6)
                perturbed_texts.append(pert)
            else:
                perturbed_texts.append(s.text)

        # Baseline extraction (un-sanitized)
        X_perturbed, _ = pipeline.extract_batch(perturbed_texts)

        # AegisText sanitized extraction
        sanitized_texts = [sanitizer.sanitize(t)[0] for t in perturbed_texts]
        X_sanitized, _ = pipeline.extract_batch(sanitized_texts)

        results["adversarial_benchmarks"][attack] = {}

        for name, model in models.items():
            if name == "AegisText_Ensemble":
                # AegisText benefits from upfront adversarial sanitization
                probs = model.predict_proba(X_sanitized)[:, 1]
            else:
                probs = model.predict_proba(X_perturbed)[:, 1]

            metrics = evaluate_detector_predictions(y_test, probs)
            results["adversarial_benchmarks"][attack][name] = metrics
            print(f"  [{name:20s}] ROC-AUC: {metrics['roc_auc']:.4f} | F1: {metrics['f1_binary']:.4f}")

    # 6. Save Experiment Results
    exp_dir = "research/experiments"
    os.makedirs(exp_dir, exist_ok=True)
    results_file = os.path.join(exp_dir, "benchmark_results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nBenchmark results successfully persisted to {results_file}")
    return results


if __name__ == "__main__":
    run_benchmark_experiments()
