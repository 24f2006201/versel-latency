from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os
import numpy as np

app = Flask(__name__)
CORS(app)

# Vercel-safe path resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "q-vercel-latency.json")

try:
    with open(DATA_PATH, "r") as f:
        ALL_RECORDS = json.load(f)
except Exception as e:
    ALL_RECORDS = []
    LOAD_ERROR = str(e)
else:
    LOAD_ERROR = None

@app.route("/", methods=["GET", "POST", "OPTIONS"])
@app.route("/<path:path>", methods=["GET", "POST", "OPTIONS"])
def handle(path=""):
    if LOAD_ERROR:
        return jsonify({"error": f"Data load failed: {LOAD_ERROR}"}), 500

    if request.method in ("GET", "OPTIONS"):
        return jsonify({"status": "ok"})

    body         = request.get_json(force=True) or {}
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

    return jsonify(results)
