from http.server import BaseHTTPRequestHandler
import json
import numpy as np
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "q-vercel-latency.json"
with open(DATA_PATH) as f:
    RAW_DATA = json.load(f)


class handler(BaseHTTPRequestHandler):

    # Every response, including 501/400/500 from send_error, gets CORS headers
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def _send_json(self, status, obj):
        payload = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        self._send_json(200, {"status": "ok", "usage": "POST {regions: [...], threshold_ms: 180}"})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            return self._send_json(400, {"error": "invalid JSON body"})

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
            uptimes = [r["uptime_pct"] for r in records]
            result[region] = {
                "avg_latency": round(float(np.mean(latencies)), 4),
                "p95_latency": round(float(np.percentile(latencies, 95)), 4),
                "avg_uptime": round(float(np.mean(uptimes)), 4),
                "breaches": int(sum(1 for l in latencies if l > threshold_ms)),
            }

        self._send_json(200, result)