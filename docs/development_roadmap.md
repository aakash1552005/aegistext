# Development Roadmap

This roadmap outlines the sequential phases (0‑27) defined in the project specification, their primary goals, and estimated effort. Each phase will be executed only after the previous one passes its validation checklist.

| Phase | Goal | Key Deliverables | Approx. Time |
|------|------|------------------|--------------|
| 0 | Repository & environment audit | Docs, status file, repo init | 1 h |
| 1 | Research foundation | Problem statement, literature matrix, claim registry | 2 h |
| 2 | Dataset system | Schema, ingestion scripts, leakage checks | 4 h |
| 3 | Baselines | Classic ML & transformer baselines | 6 h |
| 4 | Signal engine | Feature extraction for all families | 8 h |
| 5 | Expert models | Individual expert classes | 8 h |
| 6 | Static ensemble baseline | RandomForest/XGBoost/LightGBM + meta‑learner | 4 h |
| 7 | Adaptive fusion model | Gating network, end‑to‑end training | 8 h |
| 8 | Humanization severity index | Transformation metrics, normalization | 4 h |
| 9 | Signal persistence analysis | Degradation tables & plots | 4 h |
|10‑12| Robustness & generalisation | Cross‑humanizer/generator/domain evals | 12 h |
|13‑15| Length robustness, calibration & abstention | Empirical curves, calibrated inference | 6 h |
|16‑17| Mixed‑authorship & explainability | Segment‑level models, SHAP/IG outputs | 8 h |
|18‑19| Ablation & statistical validation | Full ablation suite, bootstrap CI | 8 h |
|20‑21| Research dashboard & API | FastAPI service, OpenAPI spec | 8 h |
|22‑24| Frontend UI & deployment | Next.js app, Docker, Cloudflare config | 12 h |
|25‑27| Testing, paper artifacts, final audit | Unit/integ tests, paper sections, reproducibility docs | 10 h |

All phases are **test‑driven**; after each phase the test suite must pass before moving forward.
