from flask import Flask, request, jsonify
import json, os
import numpy as np

app = Flask(__name__)

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "q-vercel-latency.json")
with open(DATA_PATH, "r") as f:
    ALL_RECORDS = json.load(f)

def cors(response):
    response.headers["Access-Control-Allow-Origin"]          = "*"
    response.headers["Access-Control-Allow-Methods"]         = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"]         = "*"
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    response.headers["Access-Control-Max-Age"]               = "86400"
    return response

@app.route("/", methods=["GET", "POST", "OPTIONS"])
@app.route("/<path:path>", methods=["GET", "POST", "OPTIONS"])
def handle(path=""):
    if request.method == "OPTIONS":
        return cors(app.response_class("", status=204))

    if request.method == "GET":
        return cors(jsonify({"status": "ok"}))

    body         = request.get_json(force=True)
    regions      = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 180)

    results = {}
    for region in regions:
        records = [r for r in ALL_RECORDS if r["region"] == region]
        if not records:
            results[region] = None
            continue
        latencies = [r["latency_ms"] for r in records]
        uptimes   = [r["uptime_pct"]  for r in records]
        results[region] = {
            "avg_latency": float(np.mean(latencies)),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime":  float(np.mean(uptimes)),
            "breaches":    int(sum(1 for l in latencies if l > threshold_ms)),
        }

    return cors(jsonify(results))
