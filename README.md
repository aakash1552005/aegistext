# AegisText

**Adversarially Robust, Explainable and Humanization‑Aware AI‑Generated Text Detection**

This repository contains the full research‑grade benchmark, detection framework, adaptive fusion model, evaluation pipelines, and a production‑ready web application described in the project specification.

## Repository Structure

```
aegistext/
  apps/
    frontend/            # Next.js UI
    api/                 # FastAPI backend
  src/
    data/
    preprocessing/
    features/
      predictability/
      stylometry/
      semantic/
      structural/
    models/
      baselines/
      experts/
      fusion/
      calibration/
      localization/
    explainability/
    evaluation/
    robustness/
    security/
    inference/
  datasets/
    raw/
    processed/
    manifests/
  experiments/
    configs/
    scripts/
  models/
    checkpoints/
  reports/
    figures/
    tables/
    benchmark/
    ablations/
  research/
    literature/
    paper/
    citations/
  tests/
  docs/
    architecture.md
    roadmap.md
  docker/
  scripts/
  README.md
  .gitignore
  requirements.txt
```

## Getting Started

1. **Python** – Install Python 3.9 – 3.11 (recommended via Miniconda).  
2. **GPU** – NVIDIA RTX 3050 with CUDA 13.3 is detected; install the matching PyTorch build (`pip install torch --extra-index-url https://download.pytorch.org/whl/cu113`).
3. **Create a virtual environment**:
   ```bash
   conda create -n aegistext python=3.11 -y
   conda activate aegistext
   pip install -r requirements.txt
   ```
4. **Initialize the repo** (optional):
   ```bash
   git init
   git add .
   git commit -m "Initial commit – directory layout"
   ```
5. **Run the first script** to verify the environment:
   ```bash
   python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
   ```

Further instructions for each phase are in `docs/roadmap.md` and `research/experiment_plan.md`.
