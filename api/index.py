# api/index.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json, numpy as np
from pathlib import Path

app = FastAPI()

DATA_PATH = Path(__file__).parent.parent / "q-vercel-latency.json"
with open(DATA_PATH) as f:
    RAW_DATA = json.load(f)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}

# Handle preflight OPTIONS request
@app.options("/analytics")
def options_analytics():
    return JSONResponse(content={}, headers=CORS_HEADERS)

@app.post("/analytics")
async def analytics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 180)

    result = {}
    for region in regions:
        records = [r for r in RAW_DATA if r["region"] == region]

        if not records:
            result[region] = {"avg_latency": None, "p95_latency": None, "avg_uptime": None, "breaches": 0}
            continue

        latencies = [r["latency_ms"] for r in records]
        uptimes   = [r["uptime_pct"] for r in records]

        result[region] = {
            "avg_latency": round(float(np.mean(latencies)), 4),
            "p95_latency": round(float(np.percentile(latencies, 95)), 4),
            "avg_uptime":  round(float(np.mean(uptimes)), 4),
            "breaches":    int(sum(1 for l in latencies if l > threshold_ms))
        }

    return JSONResponse(content=result, headers=CORS_HEADERS)

@app.get("/")
def root():
    return JSONResponse(content={"status": "ok"}, headers=CORS_HEADERS)
