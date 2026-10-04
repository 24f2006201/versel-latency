from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import json
import statistics

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

with open("q-vercel-latency.json") as f:
    data = json.load(f)


def percentile(values, p):
    values = sorted(values)

    if len(values) == 1:
        return values[0]

    position = (len(values) - 1) * p
    lower = int(position)
    upper = min(lower + 1, len(values))
    fraction = position - lower

    return values[lower] + (values[upper] - values[lower]) * fraction


@app.get("/")
def home():
    return {"status": "ok"}

@app.options("/api")
async def options():
    return Response(
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
    )

@app.post("/api")
async def analytics(request: Request):
    body = await request.json()
    regions = body["regions"]
    threshold = body["threshold_ms"]

    result = {}

    for region in regions:
        records = [
            r for r in data
            if r["region"] == region
        ]

        latencies = [
            r["latency_ms"] for r in records
        ]

        uptimes = [
            r["uptime_pct"] for r in records
        ]

        result[region] = {
            "avg_latency": statistics.mean(latencies),
            "p95_latency": percentile(latencies, 0.95),
            "avg_uptime": statistics.mean(uptimes),
            "breaches": sum(
                x > threshold for x in latencies
            )
        }

    return result
