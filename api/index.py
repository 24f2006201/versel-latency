# api/index.py
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import json
import numpy as np
from pathlib import Path

app = FastAPI(title="Latency Analytics Service")

# 1. Custom middleware — attaches CORS headers to EVERY response
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        response = Response(status_code=200)
    else:
        response = await call_next(request)

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE, PATCH, HEAD, *"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Expose-Headers"] = "*, Access-Control-Allow-Origin, access-control-allow-origin"
    response.headers["Access-Control-Max-Age"] = "0"
    return response

# 2. Standard CORSMiddleware (belt-and-suspenders approach)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*", "Access-Control-Allow-Origin", "access-control-allow-origin"],
    max_age=0,
)

# Load the telemetry dataset
# Looks in api/ first, then the project root
DATA_FILE = Path(__file__).parent / "q-vercel-latency.json"
if not DATA_FILE.exists():
    DATA_FILE = Path(__file__).parent.parent / "q-vercel-latency.json"

with open(DATA_FILE, "r", encoding="utf-8") as f:
    TELEMETRY_DATA = json.load(f)

# Handle OPTIONS preflight requests (browsers send these before POST)
@app.options("/{full_path:path}")
async def options_handler():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PUT, DELETE, PATCH, HEAD, *",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Expose-Headers": "*, Access-Control-Allow-Origin, access-control-allow-origin",
            "Access-Control-Max-Age": "0",
        }
    )

# GET routes — health check so you can confirm the API is alive
@app.get("/")
@app.get("/api")
@app.get("/api/")
async def health_check():
    return {
        "status": "online",
        "message": "Latency Analytics API is running. Send a POST request to analyze telemetry data."
    }

# POST routes — the actual analytics endpoint
@app.post("/")
@app.post("/api")
@app.post("/api/")
async def calculate_metrics(request: Request):
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    regions_requested = payload.get("regions", [])
    threshold_ms = float(payload.get("threshold_ms", 180))

    results = []

    for region in regions_requested:
        # Filter telemetry records for this region
        region_records = [d for d in TELEMETRY_DATA if d.get("region") == region]

        if region_records:
            latencies = [d["latency_ms"] for d in region_records if "latency_ms" in d]
            uptimes   = [d["uptime_pct"] for d in region_records if "uptime_pct" in d]

            avg_lat     = round(float(np.mean(latencies)), 2)       if latencies else 0.0
            p95_lat     = round(float(np.percentile(latencies, 95)), 2) if latencies else 0.0
            avg_upt     = round(float(np.mean(uptimes)), 3)          if uptimes   else 0.0
            breach_count = sum(1 for lat in latencies if lat > threshold_ms)

            results.append({
                "region":      region,
                "avg_latency": avg_lat,
                "p95_latency": p95_lat,
                "avg_uptime":  avg_upt,
                "breaches":    breach_count
            })

    return {"regions": results}
