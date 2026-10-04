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
    "Access-Control-Allow-Headers": "*",          # allow ANY header the portal sends
    "Access-Control-Allow-Private-Network": "true",
    "Access-Control-Max-Age": "86400",            # cache preflight for 24h
}

class handler(BaseHTTPRequestHandler):

    def send_cors_headers(self):
        for key, value in CORS_HEADERS.items():
            self.send_header(key, value)
        self.send_header("Content-Type", "application/json")

    def do_OPTIONS(self):
        self.send_response(204)          # 204 No Content is more correct for preflights
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):                    # some portals probe with GET first
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())

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

    def log_message(self, format, *args):
        pass   # suppress Vercel log noise
