# api/index.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json, os, numpy as np
from typing import List
from pathlib import Path

app = FastAPI()

# ── CORS: allow POST from any origin (required by the assignment) ──────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # any website can call this endpoint
    allow_methods=["POST"],
    allow_headers=["*"],
)

# ── Load the telemetry data once at startup ────────────────────────────────
# __file__ is api/index.py, so we go one level up to find the JSON
DATA_PATH = Path(__file__).parent.parent / "q-vercel-latency.json"
with open(DATA_PATH) as f:
    RAW_DATA = json.load(f)

# ── Define what the incoming request body looks like ──────────────────────
class AnalyticsRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

# ── The main endpoint ──────────────────────────────────────────────────────
@app.post("/analytics")
def analytics(req: AnalyticsRequest):
    result = {}

    for region in req.regions:
        # Filter records for this region only
        records = [r for r in RAW_DATA if r["region"] == region]

        if not records:
            result[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime":  None,
                "breaches":    0
            }
            continue

        latencies = [r["latency_ms"]  for r in records]
        uptimes   = [r["uptime_pct"]  for r in records]

        result[region] = {
            "avg_latency": round(float(np.mean(latencies)), 4),
            "p95_latency": round(float(np.percentile(latencies, 95)), 4),
            "avg_uptime":  round(float(np.mean(uptimes)), 4),
            "breaches":    int(sum(1 for l in latencies if l > req.threshold_ms))
        }

    return result

# ── Health check so you can confirm the deployment is live ─────────────────
@app.get("/")
def root():
    return {"status": "ok", "message": "Analytics API is running"}
