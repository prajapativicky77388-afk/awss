"""
Local Backend Server for FloodSense AI.
Simulates AWS API Gateway + Lambda + DynamoDB + SNS locally without requiring AWS credentials or SAM CLI.
"""
import http.server
import json
import time
import uuid
import urllib.request

PORT = 5001

ZONES = {
    "minto-bridge": (28.6320, 77.2250, 0.95),
    "pul-prahladpur": (28.5030, 77.3000, 0.95),
    "ito": (28.6290, 77.2420, 0.70),
    "kashmere-gate": (28.6670, 77.2290, 0.50),
    "lajpat-nagar": (28.5680, 77.2430, 0.35),
    "ring-who": (28.6320, 77.2400, 0.80),
    "zakhira": (28.6600, 77.1500, 0.80),
    "jahangirpuri": (28.7260, 77.1630, 0.70),
    "loni-golchakkar": (28.6830, 77.2900, 0.70),
    "karala": (28.7380, 77.0550, 0.70),
    "aiims": (28.5670, 77.2070, 0.55),
    "moolchand": (28.5640, 77.2330, 0.60),
    "dhaula-kuan": (28.5920, 77.1620, 0.50),
}

# In-memory stores simulating DynamoDB and SNS
stored_reports = []
subscriptions = []


class FloodSenseHandler(http.server.BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")
        if path in ("/risk", "/Prod/risk"):
            now = int(time.time())
            items = []
            for zone_id, (lat, lon, low) in ZONES.items():
                zone_reps = [r for r in stored_reports if r["zone"] == zone_id and r["ts"] > now - 3 * 3600]
                rep_count = sum(r["severity"] for r in zone_reps)
                score = round(min(1.0, 0.1 * low + rep_count * 0.15), 2)
                items.append({
                    "zone": zone_id,
                    "score": score,
                    "reports": len(zone_reps),
                    "updated": now,
                })
            self._send_json(200, {"zones": items})
        else:
            self._send_json(404, {"error": "Not Found", "path": self.path})

    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON body"})
            return

        if path in ("/reports", "/Prod/reports"):
            zone = body.get("zone")
            severity = int(body.get("severity", 1))
            note = str(body.get("note", ""))[:280]

            rid = str(uuid.uuid4())
            stored_reports.append({
                "id": rid,
                "zone": zone,
                "severity": severity,
                "note": note,
                "ts": int(time.time()),
            })
            print(f" [REPORT SAVED] Zone: {zone} | Severity: {severity} | ID: {rid}")
            self._send_json(201, {"id": rid, "message": "Report saved to local DynamoDB simulation"})

        elif path in ("/subscribe", "/Prod/subscribe"):
            protocol = body.get("protocol")
            endpoint = body.get("endpoint")
            zones = body.get("zones", [])

            sub_id = f"sub-{uuid.uuid4().hex[:8]}"
            subscriptions.append({
                "id": sub_id,
                "protocol": protocol,
                "endpoint": endpoint,
                "zones": zones,
                "created": int(time.time()),
            })
            print(f"🔔 [SUBSCRIPTION SAVED] {protocol.upper()}: {endpoint} for zones {zones}")
            self._send_json(200, {
                "ok": True,
                "subscriptionArn": f"arn:aws:sns:local:simulated-topic:{sub_id}",
                "message": f"Subscribed {endpoint} successfully via simulated SNS"
            })
        else:
            self._send_json(404, {"error": "Endpoint not recognized", "path": self.path})

    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def log_message(self, format, *args):
        # Concise logging
        print(f"[API Gateway Simulator] {self.address_string()} - {args[0]}")


if __name__ == "__main__":
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), FloodSenseHandler)
    print("=" * 60)
    print(f"🚀 FloodSense AI - Local API Gateway Simulator running on:")
    print(f"   http://localhost:{PORT}/")
    print(f"   Endpoints: /reports, /risk, /subscribe")
    print("=" * 60)
    server.serve_forever()
