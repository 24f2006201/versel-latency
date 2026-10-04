# api/index.py
import json
import os
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Step A: Enable CORS so any website/dashboard can call this endpoint
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # allow requests from ANY website
    allow_methods=["*"],       # allow GET, POST, etc.
    allow_headers=["*"],       # allow any headers
)

# Step B: Define what the incoming JSON body should look like
class AnalyticsRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

# Step C: Load the telemetry data from the JSON file
#         __file__ means "the folder where this script lives"
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "q-vercel-latency.json")

with open(DATA_PATH, "r") as f:
    ALL_RECORDS = json.load(f)

# Step D: Define the POST endpoint at the root URL "/"
@app.post("/")
def analytics(request: AnalyticsRequest):
    results = {}

    for region in request.regions:
        # Filter records that belong to this region
        region_records = [r for r in ALL_RECORDS if r["region"] == region]

        if not region_records:
            results[region] = None
            continue

        # Pull out the latency and uptime values into lists
        latencies = [r["latency_ms"] for r in region_records]
        uptimes = [r["uptime_pct"] for r in region_records]


        # Calculate the stats
        avg_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        avg_uptime  = float(np.mean(uptimes))
        breaches    = int(sum(1 for l in latencies if l > request.threshold_ms))

        results[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime":  avg_uptime,
            "breaches":    breaches,
        }

    return results
