"""
AegisText Production FastAPI Server

High-performance REST API for Adversarially Robust AI Text Detection:
- Single text detection with calibrated probabilities
- In-depth explainability with per-sentence heatmap and linguistic diagnostics
- Adversarial tampering sanitization and audit
- High-throughput batch detection
- Real-time model health and benchmark metrics
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.features.pipeline import MasterFeaturePipeline
from src.models.tabular_ensemble import AegisEnsembleDetector
from src.preprocessing.normalizer import TextSanitizer
from src.explainability.explainer import AegisExplainer

# Global resources initialized on startup
pipeline: Optional[MasterFeaturePipeline] = None
detector: Optional[AegisEnsembleDetector] = None
sanitizer: Optional[TextSanitizer] = None
explainer: Optional[AegisExplainer] = None
start_time: float = time.time()


def init_resources():
    global pipeline, detector, sanitizer, explainer
    if pipeline is None:
        pipeline = MasterFeaturePipeline()
    if sanitizer is None:
        sanitizer = TextSanitizer()
    if explainer is None:
        explainer = AegisExplainer(pipeline)
    if detector is None or not detector.is_fitted:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_path = os.path.join(project_root, "artifacts", "checkpoints", "aegistext_ensemble.joblib")
        if not os.path.exists(model_path):
            model_path = os.path.join(project_root, "models", "checkpoints", "aegistext_ensemble.joblib")
        detector = AegisEnsembleDetector()
        if os.path.exists(model_path):
            detector.load(model_path)


# Ensure initialization on import
init_resources()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_resources()
    yield
    print("Shutting down AegisText Engine.")


app = FastAPI(
    title="AegisText API",
    version="1.0.0",
    description="Adversarially Robust, Explainable and Humanization-Aware AI-Generated Text Detection API",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request & Response Models ---

class TextDetectionRequest(BaseModel):
    text: str = Field(..., min_length=10, description="The input text sample to analyze")
    sanitize_adversarial: bool = Field(True, description="Whether to sanitize homoglyphs and hidden unicode")


class DetectionResponse(BaseModel):
    classification: str
    ai_probability: float
    confidence_band: str
    word_count: int
    char_count: int
    processing_time_ms: float
    tampering_detected: bool
    tampering_report: Dict[str, Any]


class ExplanationResponse(BaseModel):
    detection: DetectionResponse
    feature_attributions: List[Dict[str, Any]]
    sentence_heatmap: List[Dict[str, Any]]
    linguistic_diagnostics: List[Dict[str, Any]]


class BatchDetectionRequest(BaseModel):
    texts: List[str] = Field(..., max_length=50, description="List of texts to analyze (up to 50)")


class BatchDetectionResponse(BaseModel):
    results: List[DetectionResponse]
    total_processed: int
    total_time_ms: float


class SanitizeRequest(BaseModel):
    text: str = Field(..., min_length=1)


class SanitizeResponse(BaseModel):
    sanitized_text: str
    tampering_audit: Dict[str, Any]


from fastapi.responses import FileResponse


@app.get("/")
def root():
    return {
        "service": "AegisText API",
        "status": "online",
        "app_ui": "/app",
        "docs_url": "/docs",
        "version": "1.0.0",
    }


@app.get("/app")
def serve_app():
    index_file = os.path.join(web_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Web interface not found")


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "model_loaded": detector.is_fitted if detector else False,
        "features_registered": pipeline.num_features if pipeline else 0,
        "uptime_seconds": round(time.time() - start_time, 2),
    }


@app.post("/api/v1/sanitize", response_model=SanitizeResponse)
def sanitize_text(payload: SanitizeRequest):
    if not sanitizer:
        raise HTTPException(status_code=500, detail="Sanitizer not initialized")
    clean_text, audit = sanitizer.sanitize(payload.text)
    return SanitizeResponse(sanitized_text=clean_text, tampering_audit=audit)


@app.post("/api/v1/detect", response_model=DetectionResponse)
def detect_text(payload: TextDetectionRequest):
    if not detector or not detector.is_fitted or not pipeline or not sanitizer:
        raise HTTPException(status_code=503, detail="Detector model is not currently ready.")

    t0 = time.perf_counter()
    raw_text = payload.text
    sanitized_text, audit = sanitizer.sanitize(raw_text)

    # Use sanitized text if requested
    text_to_eval = sanitized_text if payload.sanitize_adversarial else raw_text

    # Extract features
    vec = pipeline.extract_vector(text_to_eval).reshape(1, -1)
    probs = detector.predict_proba(vec)[0]

    ai_prob = float(probs[1]) if len(probs) > 1 else float(probs[0])
    label = "AI_GENERATED" if ai_prob >= 0.5 else "HUMAN_WRITTEN"

    dist = abs(ai_prob - 0.5)
    if dist > 0.35:
        confidence = "VERY_HIGH"
    elif dist > 0.20:
        confidence = "HIGH"
    elif dist > 0.10:
        confidence = "MODERATE"
    else:
        confidence = "LOW_BORDERLINE"

    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    return DetectionResponse(
        classification=label,
        ai_probability=round(ai_prob, 4),
        confidence_band=confidence,
        word_count=len(raw_text.split()),
        char_count=len(raw_text),
        processing_time_ms=round(elapsed_ms, 2),
        tampering_detected=audit.get("adversarial_markers_present", False),
        tampering_report=audit,
    )


@app.post("/api/v1/explain", response_model=ExplanationResponse)
def explain_text(payload: TextDetectionRequest):
    if not detector or not detector.is_fitted or not explainer or not sanitizer:
        raise HTTPException(status_code=503, detail="Detector model is not currently ready.")

    t0 = time.perf_counter()
    raw_text = payload.text
    sanitized_text, audit = sanitizer.sanitize(raw_text)

    text_to_eval = sanitized_text if payload.sanitize_adversarial else raw_text
    vec = pipeline.extract_vector(text_to_eval).reshape(1, -1)
    probs = detector.predict_proba(vec)[0]
    ai_prob = float(probs[1]) if len(probs) > 1 else float(probs[0])

    importances = detector.get_feature_importances()
    explanation = explainer.explain_prediction(
        text=text_to_eval,
        ai_probability=ai_prob,
        model_feature_importances=importances,
    )

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    label = "AI_GENERATED" if ai_prob >= 0.5 else "HUMAN_WRITTEN"

    dist = abs(ai_prob - 0.5)
    confidence = "VERY_HIGH" if dist > 0.35 else ("HIGH" if dist > 0.20 else ("MODERATE" if dist > 0.10 else "LOW_BORDERLINE"))

    detection_resp = DetectionResponse(
        classification=label,
        ai_probability=round(ai_prob, 4),
        confidence_band=confidence,
        word_count=len(raw_text.split()),
        char_count=len(raw_text),
        processing_time_ms=round(elapsed_ms, 2),
        tampering_detected=audit.get("adversarial_markers_present", False),
        tampering_report=audit,
    )

    return ExplanationResponse(
        detection=detection_resp,
        feature_attributions=explanation["feature_attributions"],
        sentence_heatmap=explanation["sentence_heatmap"],
        linguistic_diagnostics=explanation["linguistic_diagnostics"],
    )


@app.post("/api/v1/batch", response_model=BatchDetectionResponse)
def batch_detect(payload: BatchDetectionRequest):
    if not detector or not detector.is_fitted or not pipeline or not sanitizer:
        raise HTTPException(status_code=503, detail="Detector model is not currently ready.")

    t0 = time.perf_counter()
    results = []

    for t in payload.texts:
        sub_req = TextDetectionRequest(text=t, sanitize_adversarial=True)
        results.append(detect_text(sub_req))

    total_ms = (time.perf_counter() - t0) * 1000.0
    return BatchDetectionResponse(
        results=results,
        total_processed=len(results),
        total_time_ms=round(total_ms, 2),
    )


@app.get("/api/v1/metrics")
def get_benchmarks():
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    results_path = os.path.join(project_root, "research", "experiments", "benchmark_results.json")
    if os.path.exists(results_path):
        with open(results_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"message": "Benchmark results not yet generated."}


# Mount Static Web UI
from fastapi.staticfiles import StaticFiles

web_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "web")
if not os.path.exists(web_dir):
    web_dir = "web"

if os.path.exists(web_dir):
    app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")

