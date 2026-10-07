"""
AegisText Comprehensive Evaluation & Calibration Metrics Suite

Computes publication-standard evaluation metrics:
- ROC-AUC, PR-AUC
- Accuracy, Precision, Recall, Macro-F1, Binary-F1
- FPR at 95% and 99% TPR (Standard IEEE metric for low false accusation rate)
- Brier Score
- Expected Calibration Error (ECE)
- Confusion Matrix
"""

from typing import Dict, Any, Tuple
import numpy as np
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    brier_score_loss,
    confusion_matrix,
    roc_curve,
)


def compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """
    Computes Expected Calibration Error (ECE).
    Measures the alignment between predicted probabilities and empirical accuracy.
    """
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]

    ece = 0.0
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        in_bin = (y_prob > bin_lower) & (y_prob <= bin_upper)
        prop_in_bin = np.mean(in_bin)

        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(y_true[in_bin])
            avg_confidence_in_bin = np.mean(y_prob[in_bin])
            ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin

    return float(ece)


def compute_fpr_at_fixed_tpr(y_true: np.ndarray, y_prob: np.ndarray, target_tpr: float = 0.95) -> float:
    """
    Calculates False Positive Rate (FPR) when True Positive Rate (TPR) is at least `target_tpr`.
    Crucial in academic and moderation settings to minimize false positives against human authors.
    """
    fprs, tprs, _ = roc_curve(y_true, y_prob)
    idx = np.where(tprs >= target_tpr)[0]
    if len(idx) > 0:
        return float(fprs[idx[0]])
    return 1.0


def evaluate_detector_predictions(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    Calculates the full battery of AegisText performance & calibration metrics.
    """
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob).astype(float)
    y_pred = (y_prob >= threshold).astype(int)

    roc_auc = float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.5
    pr_auc = float(average_precision_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.5

    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1_bin = float(f1_score(y_true, y_pred, average="binary", zero_division=0))
    f1_mac = float(f1_score(y_true, y_pred, average="macro", zero_division=0))

    brier = float(brier_score_loss(y_true, y_prob))
    ece = float(compute_ece(y_true, y_prob))
    fpr_95 = float(compute_fpr_at_fixed_tpr(y_true, y_prob, 0.95))
    fpr_99 = float(compute_fpr_at_fixed_tpr(y_true, y_prob, 0.99))

    cm = confusion_matrix(y_true, y_pred).tolist()

    return {
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_binary": round(f1_bin, 4),
        "f1_macro": round(f1_mac, 4),
        "brier_score": round(brier, 4),
        "ece": round(ece, 4),
        "fpr_at_95_tpr": round(fpr_95, 4),
        "fpr_at_99_tpr": round(fpr_99, 4),
        "confusion_matrix": cm,
        "n_samples": int(len(y_true)),
    }
