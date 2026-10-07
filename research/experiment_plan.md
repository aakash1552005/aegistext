# Experiment Plan

## Overview
This document outlines all planned experiments, their required resources, and expected outputs.

## Phase 3 — Baselines

| ID | Experiment | Model | Dataset | GPU Required | Status |
|----|-----------|-------|---------|-------------|--------|
| E01 | TF-IDF + LogReg | LogisticRegression | HC3/MAGE subset | No | PENDING |
| E02 | TF-IDF + LinearSVM | LinearSVC | HC3/MAGE subset | No | PENDING |
| E03 | Random Forest | RandomForestClassifier | HC3/MAGE subset | No | PENDING |
| E04 | XGBoost | XGBClassifier | HC3/MAGE subset | No | PENDING |
| E05 | LightGBM | LGBMClassifier | HC3/MAGE subset | No | PENDING |
| E06 | Stylometric Classifier | Custom features + LR | HC3/MAGE subset | No | PENDING |
| E07 | Predictability Classifier | Perplexity features + LR | HC3/MAGE subset | Yes (small) | PENDING |
| E08 | RoBERTa fine-tune | roberta-base | HC3/MAGE subset | Yes | PENDING |
| E09 | DeBERTa fine-tune | deberta-v3-base | HC3/MAGE subset | Yes | PENDING |

## Phase 4 — Signal Engine

| ID | Experiment | Signal Family | Features | GPU Required | Status |
|----|-----------|--------------|----------|-------------|--------|
| E10 | Predictability extraction | Predictability | perplexity, entropy, burstiness, rank stats | Yes (small) | PENDING |
| E11 | Stylometry extraction | Stylometry | TTR, MTLD, HD-D, POS, function words | No | PENDING |
| E12 | Semantic extraction | Semantic | DeBERTa embeddings, consistency | Yes | PENDING |
| E13 | Structural extraction | Structural | paragraph stats, discourse markers, transitions | No | PENDING |

## Phase 7 — Adaptive Fusion

| ID | Experiment | Description | GPU Required | Status |
|----|-----------|-------------|-------------|--------|
| E14 | Static ensemble | RF + XGB + LGBM + LR meta | No | PENDING |
| E15 | Adaptive gating | Gating network training | Yes (small) | PENDING |

## Phase 9 — Signal Persistence

| ID | Experiment | Description | Status |
|----|-----------|-------------|--------|
| E16 | Light transform persistence | All signals on lightly paraphrased text | PENDING |
| E17 | Medium transform persistence | All signals on medium paraphrased text | PENDING |
| E18 | Heavy transform persistence | All signals on heavily paraphrased text | PENDING |

## Phase 10-13 — Robustness & Generalization

| ID | Experiment | Description | Status |
|----|-----------|-------------|--------|
| E19 | Cross-humanizer leave-one-out | Train on N-1 humanizers, test on held-out | PENDING |
| E20 | Cross-generator leave-one-out | Train on N-1 generators, test on held-out | PENDING |
| E21 | Cross-domain leave-one-out | Train on N-1 domains, test on held-out | PENDING |
| E22 | Length robustness | Evaluate at 50/100/200/300/500/1000/2000+ words | PENDING |

## Phase 14 — Calibration

| ID | Experiment | Description | Status |
|----|-----------|-------------|--------|
| E23 | Temperature scaling | Post-hoc calibration | PENDING |
| E24 | Isotonic regression | Non-parametric calibration | PENDING |

## Phase 17 — Ablation

| ID | Experiment | Signals Used | Status |
|----|-----------|-------------|--------|
| E25 | Predictability only | P | PENDING |
| E26 | Stylometry only | S | PENDING |
| E27 | Semantic only | Se | PENDING |
| E28 | Structural only | St | PENDING |
| E29 | P + S | Predictability + Stylometry | PENDING |
| E30 | S + Se | Stylometry + Semantic | PENDING |
| E31 | Se + St | Semantic + Structural | PENDING |
| E32 | All static | P + S + Se + St (no gating) | PENDING |
| E33 | All + gating | P + S + Se + St + adaptive gating | PENDING |
| E34 | All + adversarial | Full AegisText with adversarial training | PENDING |
| E35 | Full AegisText | Complete system | PENDING |
