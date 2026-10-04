from http.server import BaseHTTPRequestHandler
import json
import numpy as np
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "q-vercel-latency.json")
with open(DATA_PATH, "r") as f:
    ALL_RECORDS = json.load(f)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",  # changed from *
    "Content-Type": "application/json",
}


class handler(BaseHTTPRequestHandler):

    def send_cors_headers(self):
        for key, value in CORS_HEADERS.items():
            self.send_header(key, value)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))

        regions = body.get("regions", [])
        threshold_ms = body.get("threshold_ms", 180)

        results = {}
        for region in regions:
            records = [r for r in ALL_RECORDS if r["region"] == region]
            if not records:
                results[region] = None
                continue
            latencies = [r["latency_ms"] for r in records]
            uptimes   = [r["uptime_pct"] for r in records]
            results[region] = {
                "avg_latency": float(np.mean(latencies)),
                "p95_latency": float(np.percentile(latencies, 95)),
                "avg_uptime":  float(np.mean(uptimes)),
                "breaches":    int(sum(1 for l in latencies if l > threshold_ms)),
            }

        response = json.dumps(results).encode()
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(response)
