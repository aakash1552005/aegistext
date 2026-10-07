# AegisText Studio

**Adversarially Robust, Explainable and Humanization‑Aware AI‑Generated Text Detection**

[![GitHub Repository](https://img.shields.io/badge/GitHub-aakash1552005%2Faegistext-blue?logo=github)](https://github.com/aakash1552005/aegistext)
[![Tests Passing](https://img.shields.io/badge/tests-31%20passed-success)](https://github.com/aakash1552005/aegistext)
[![ROC-AUC](https://img.shields.io/badge/AUROC-0.9959-indigo)](https://github.com/aakash1552005/aegistext)
[![Cloudflare Pages](https://img.shields.io/badge/Cloudflare_Pages-Ready-orange?logo=cloudflare)](https://pages.cloudflare.com)

---

## 🚀 Overview

AegisText is a publication-grade, production-deployed forensic framework designed to detect AI-generated text with resilience against adversarial evasions, including:
- **Invisible Zero-Width Unicode Injection** (`\u200b`, `\u200c`, `\ufeff`)
- **Cyrillic & Greek Confusable Homoglyphs**
- **Commercial AI Humanizers & Paraphrasers** (e.g., QuillBot, Undetectable.ai)
- **Extreme Domain Variation** (Academic, News, Creative, Technical)

---

## 📊 Empirical Benchmarks (Multi-Domain Test Split)

| Model | ROC-AUC | PR-AUC | F1-Score | Accuracy | ECE (Calibration Error) | FPR @ 95% TPR |
|---|---|---|---|---|---|---|
| **Logistic Regression** | 0.9949 | 0.9963 | 0.9565 | 95.24% | 0.0393 | 0.0357 |
| **Random Forest** | 0.9990 | 0.9992 | 0.9859 | 98.41% | 0.1316 | 0.0000 |
| **AegisText Ensemble (Calibrated LightGBM)** | **0.9959** | **0.9969** | **0.9429** | **93.65%** | **0.0650** | **0.0714** |

### Adversarial Evasion Resilience

| Attack Type | Baseline RF AUROC | AegisText AUROC | Defense Status |
|---|---|---|---|
| **Zero-Width Character Injection** | 1.0000 (perturbed) | **0.9959 (sanitized)** | 100% Neutralized |
| **Homoglyph Character Substitution** | 1.0000 (perturbed) | **0.9959 (sanitized)** | 100% Normalized |
| **Commercial AI Humanizer** | 0.9990 | **0.9980** | Fully Resilient |
| **Synonym Jitter** | 0.9990 | **0.9959** | Fully Resilient |

---

## ⚡ Quick Start

### 1. Run Backend & Interactive Studio
```bash
# Set PYTHONPATH and launch server
$env:PYTHONPATH = "c:\Users\AAKASH.S.S\OneDrive\Desktop\Sukesh\aegistext"
& ".venv\Scripts\uvicorn.exe" src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Interactive Studio UI**: Open [http://localhost:8000/app](http://localhost:8000/app)
- **API Swagger Documentation**: Open [http://localhost:8000/docs](http://localhost:8000/docs)
- **System Health**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### 2. Execute Automated Tests
```bash
$env:PYTHONPATH = "c:\Users\AAKASH.S.S\OneDrive\Desktop\Sukesh\aegistext"
& ".venv\Scripts\pytest.exe" -v
```

---

## ☁️ Deploying to Cloudflare Pages

### Option A: Connect via Cloudflare Dashboard (Recommended)
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/) → **Workers & Pages** → **Create application** → **Pages** → **Connect to Git**.
2. Select repository: `aakash1552005/aegistext`.
3. Configure build settings:
   - **Framework preset**: `None`
   - **Build command**: *(leave blank)*
   - **Build output directory**: `web`
4. Click **Save and Deploy**. Cloudflare Pages will automatically deploy your frontend on every push to `main`!

### Option B: Deploy via Wrangler CLI
```bash
# Log in to Cloudflare
npx wrangler login

# Deploy static web studio
npx wrangler pages deploy web --project-name aegistext
```

### Option C: Automated GitHub Actions
Add your Cloudflare credentials as repository secrets:
- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

The workflow in `.github/workflows/cloudflare-pages.yml` will automatically build and deploy on every push to `main`.

---

## 📁 Repository Structure

```
aegistext/
├── src/
│   ├── api/             # FastAPI backend (detect, explain, batch, sanitize)
│   ├── data/            # Schema, loaders, MinHash deduplication
│   ├── preprocessing/   # Zero-width & homoglyph sanitization engine
│   ├── features/        # 84-dimensional stylometric, structural, predictability, & semantic features
│   ├── models/          # Calibrated LightGBM/XGBoost/RF tabular ensemble
│   ├── explainability/  # Sentence-level heatmap & feature attribution engine
│   ├── evaluation/      # Publication metrics (ROC-AUC, ECE, Brier, FPR@95%TPR)
│   └── robustness/      # Adversarial perturbation generator
├── web/                 # Professional Forensic Studio web frontend
│   ├── index.html       # Single-page interface
│   ├── styles.css       # Enterprise slate/dark design system
│   ├── app.js           # Interactive dial, heatmap, and export controller
│   └── _headers         # Cloudflare security & CORS headers
├── artifacts/           # Trained model checkpoints (.joblib)
├── experiments/         # Benchmark and ablation experiment scripts
├── research/            # Claim registry & empirical experiment JSONs
├── tests/               # 31 unit & integration tests
├── wrangler.toml        # Cloudflare Pages configuration
└── requirements.txt     # Python dependencies
```
