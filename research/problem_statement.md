# Research Foundation

## Problem Statement
AI-generated text detection has become a critical component of academic integrity, content moderation, and misinformation mitigation. Existing detectors largely focus on surface-level statistical irregularities and often fail when faced with **humanized AI text**—AI output that has been post‑processed by commercial humanizers (e.g., QuillBot, Wordtune) or manual editing. This creates a **robustness gap**: the detectors are vulnerable to simple transformations that substantially alter the text while preserving its semantic content.

## Research Gap
- **Humanization‑aware detection** is largely unexplored; most works treat AI‑generated and human‑generated text as two static classes.
- **Signal persistence** across transformation pipelines has not been quantified.
- **Adaptive fusion** of heterogeneous signals (predictability, stylometry, semantic, structural) with a gating mechanism is missing from prior art.

## Research Questions
1. How do the four signal families degrade under increasingly severe humanization transformations?
2. Can an adaptive gating network learn to weight signals according to their reliability for a given input?
3. Does a calibrated, abstention‑enabled model improve trustworthiness in low‑confidence scenarios?
4. How does the proposed system generalize across generators, humanizers, domains, and text lengths?

## Hypotheses
- H1: Predictability features degrade most quickly under heavy paraphrasing, while stylometric features remain relatively stable.
- H2: An adaptive gating network will outperform a static ensemble by up‑weighting the most reliable signal per instance.
- H3: Calibration (temperature scaling, isotonic regression) reduces Expected Calibration Error (ECE) and improves risk‑coverage trade‑offs.
- H4: The system will maintain >70 % AUROC on **unseen humanizer** and **unseen generator** test sets when trained on a diverse mixture of sources.

## Novelty Claims
- First end‑to‑end benchmark that jointly evaluates **AI‑raw**, **AI‑humanized**, and **human‑edited‑AI** corpora.
- Introduction of a **Humanization‑Aware Adaptive Signal Fusion** network that dynamically re‑weights four orthogonal signal families.
- Comprehensive **Signal Persistence** analysis across transformation severity levels.
- Publicly released reproducible pipeline (datasets, code, experiments) under an open‑source licence.

## Baseline Methods
- TF‑IDF + Logistic Regression
- TF‑IDF + Linear SVM
- Random Forest (feature‑based)
- XGBoost (feature‑based)
- LightGBM (feature‑based)
- Stylometric classifier (function‑word frequencies, TTR, etc.)
- Predictability classifier (perplexity, token‑rank statistics)
- RoBERTa fine‑tuned for binary detection
- DeBERTa fine‑tuned for binary detection
- Ghostbuster‑style detection (output‑probability entropy)
- Fast‑DetectGPT‑style detection (log‑probability gap)
- Binoculars‑style detection (cross‑model agreement)

## Evaluation Methodology
- **Metrics**: AUROC, AUPRC, Accuracy, F1, ECE, Brier score, Risk‑Coverage curves.
- **Cross‑humanizer / cross‑generator / cross‑domain** leave‑one‑out splits.
- **Length stratification** (50 – 2000 + tokens) to assess length robustness.
- **Statistical validation** (bootstrap CI, McNemar, DeLong).
- **Calibration**: temperature scaling, isotonic regression.
- **Ablation**: evaluate each signal family alone and in combinations.

## Deliverables for Phase 1
- `research/problem_statement.md` (this file).
- `research/research_questions.md`.
- `research/hypotheses.md`.
- `research/nova_claims.md`.
- `research/baselines.md`.
- `research/evaluation_plan.md`.
- Updated `research/literature/literature_matrix.csv` with real entries (to be filled later).
- `research/claim_registry.yaml` (placeholder for tracking claims).
