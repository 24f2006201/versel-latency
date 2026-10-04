import json
import os
import numpy as np
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Load data
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "q-vercel-latency.json")
with open(DATA_PATH, "r") as f:
    ALL_RECORDS = json.load(f)

class AnalyticsRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

# This runs on EVERY response — adds CORS headers manually
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        response = JSONResponse(content={})
    else:
        response = await call_next(request)
    
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.options("/")
async def options():
    return JSONResponse(content={})

@app.post("/")
def analytics(request: AnalyticsRequest):
    results = {}
    for region in request.regions:
        region_records = [r for r in ALL_RECORDS if r["region"] == region]
        if not region_records:
            results[region] = None
            continue
        latencies = [r["latency_ms"] for r in region_records]
        uptimes   = [r["uptime_pct"] for r in region_records]
        results[region] = {
            "avg_latency": float(np.mean(latencies)),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime":  float(np.mean(uptimes)),
            "breaches":    int(sum(1 for l in latencies if l > request.threshold_ms)),
        }
    return results
