# Architecture Overview

The **AegisText** system is organized into three logical layers:

1. **Data & Benchmark Layer** – Handles dataset ingestion, transformation tracking, deduplication, leakage prevention, and manifest generation. All raw and processed data live under `datasets/` and the metadata lives in `research/`.
2. **Model & Signal Layer** – Implements four independent signal experts (Predictability, Stylometry, Semantic, Structural), the adaptive‑gating fusion network, calibration, and abstention logic. Code resides under `src/models/` and `src/features/`.
3. **Service & UI Layer** – Provides a FastAPI inference service (`apps/api/`) and a professional Next.js frontend (`apps/frontend/`). The UI communicates with the API via typed OpenAPI schemas and displays calibrated evidence.

Each layer is **configuration‑driven** via YAML files in `configs/` and experiment scripts in `experiments/`. All artifacts (models, reports, figures) are version‑controlled and tracked with MLflow/DVC.

---

### Component Diagram (high‑level)
```
+-------------------+      +-------------------+      +-------------------+
|  Data & Benchmark | ---> |  Model & Signal   | ---> | Service & UI      |
|  Layer            |      |  Layer            |      | Layer             |
+-------------------+      +-------------------+      +-------------------+
```
*Arrows indicate data flow: raw corpora → feature extraction → model training/inference → API response → UI visualization.*
