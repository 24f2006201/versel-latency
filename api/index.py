from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import numpy as np

app = FastAPI()

# This is the critical part you are missing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the telemetry data at startup
with open("q-vercel-latency.json") as f:
    DATA = json.load(f)

@app.post("/")
async def analytics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 180)

    result = {}
    for region in regions:
        records = [r for r in DATA if r["region"] == region]
        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime"] for r in records]
        result[region] = {
            "avg_latency": round(float(np.mean(latencies)), 4),
            "p95_latency": round(float(np.percentile(latencies, 95)), 4),
            "avg_uptime": round(float(np.mean(uptimes)), 4),
            "breaches": int(sum(1 for l in latencies if l > threshold_ms))
        }
    return result
