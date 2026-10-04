from http.server import BaseHTTPRequestHandler
import json
import numpy as np
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "q-vercel-latency.json"
with open(DATA_PATH) as f:
    RAW_DATA = json.load(f)

CORS_HEADERS = [
    ("Access-Control-Allow-Origin", "*"),
    ("Access-Control-Allow-Methods", "POST, OPTIONS"),
    ("Access-Control-Allow-Headers", "Content-Type"),
    ("Content-Type", "application/json"),
]

class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        for k, v in CORS_HEADERS:
            self.send_header(k, v)
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        regions = body.get("regions", [])
        threshold_ms = body.get("threshold_ms", 180)

        result = {}
        for region in regions:
            records = [r for r in RAW_DATA if r["region"] == region]
            if not records:
                result[region] = {"avg_latency": None, "p95_latency": None,
                                  "avg_uptime": None, "breaches": 0}
                continue
            latencies = [r["latency_ms"] for r in records]
            uptimes   = [r["uptime_pct"] for r in records]
            result[region] = {
                "avg_latency": round(float(np.mean(latencies)), 4),
                "p95_latency": round(float(np.percentile(latencies, 95)), 4),
                "avg_uptime":  round(float(np.mean(uptimes)), 4),
                "breaches":    int(sum(1 for l in latencies if l > threshold_ms))
            }

        payload = json.dumps(result).encode()
        self.send_response(200)
        for k, v in CORS_HEADERS:
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
