from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import statistics

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

with open("q-vercel-latency.json") as f:
    data = json.load(f)


@app.post("/")
def analytics(request: dict):
    regions = request["regions"]
    threshold = request["threshold_ms"]

    result = {}

    for region in regions:
        records = [r for r in data if r["region"] == region]

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        result[region] = {
            "avg_latency": statistics.mean(latencies),
            "p95_latency": statistics.quantiles(latencies, n=100)[94],
            "avg_uptime": statistics.mean(uptimes),
            "breaches": sum(x > threshold for x in latencies)
        }

    return result

handler = app
