import json, os, time, uuid, base64, urllib.request
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key

ddb = boto3.resource("dynamodb")
reports = ddb.Table(os.environ["REPORTS_TABLE"])
risk = ddb.Table(os.environ["RISK_TABLE"])
sns = boto3.client("sns")
s3 = boto3.client("s3")

HEADERS = {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}
ALERT_THRESHOLD = 0.65

# Zone id -> (lat, lon, low-lying factor 0..1). Replace with real road data.
ZONES = {
    "minto-bridge": (28.6320, 77.2250, 0.95),
    "pul-prahladpur": (28.5030, 77.3000, 0.95),
    "ito": (28.6290, 77.2420, 0.70),
    "kashmere-gate": (28.6670, 77.2290, 0.50),
    "lajpat-nagar": (28.5680, 77.2430, 0.35),
}


def resp(code, body):
    return {"statusCode": code, "headers": HEADERS, "body": json.dumps(body, default=lambda o: float(o) if isinstance(o, Decimal) else str(o))}


def post_report(event, _ctx=None):
    """POST /reports  {zone, severity(1-3), note, photo_base64?}"""
    b = json.loads(event.get("body") or "{}")
    zone, sev = b.get("zone"), int(b.get("severity", 1))
    if zone not in ZONES or sev not in (1, 2, 3):
        return resp(400, {"error": "zone must be a known zone id and severity 1-3"})
    rid, photo_key = str(uuid.uuid4()), None
    if b.get("photo_base64"):
        photo_key = f"reports/{rid}.jpg"
        s3.put_object(Bucket=os.environ["PHOTO_BUCKET"], Key=photo_key, Body=base64.b64decode(b["photo_base64"]), ContentType="image/jpeg")
    reports.put_item(Item={
        "zone": zone, "ts": int(time.time()), "id": rid, "severity": sev,
        "note": b.get("note", "")[:280], "photo": photo_key,
        "expires": int(time.time()) + 6 * 3600,  # DynamoDB TTL: reports go stale
    })
    return resp(201, {"id": rid})


def get_risk(_event, _ctx=None):
    """GET /risk -> latest risk score per zone, for the map."""
    items = risk.scan()["Items"]
    return resp(200, {"zones": items})


def forecast_mm_per_hr(lat, lon):
    """Open-Meteo is free and needs no key. Swap for IMD data if you have access."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=precipitation&forecast_days=1"
    with urllib.request.urlopen(url, timeout=5) as r:
        hourly = json.load(r)["hourly"]["precipitation"]
    return max(hourly[:6] or [0])  # worst hour in the next 6 hours


def score_zones(_event=None, _ctx=None):
    """Runs on a schedule (EventBridge). risk = rain x low-lying factor + recent reports."""
    now = int(time.time())
    for zone, (lat, lon, low) in ZONES.items():
        try:
            rain = forecast_mm_per_hr(lat, lon)
        except Exception:
            rain = 0
        recent = reports.query(KeyConditionExpression=Key("zone").eq(zone) & Key("ts").gt(now - 3 * 3600))["Items"]
        score = min(1.0, rain / 55 * low * 1.15 + sum(r["severity"] for r in recent) * 0.1)
        prev = risk.get_item(Key={"zone": zone}).get("Item", {})
        risk.put_item(Item={"zone": zone, "score": Decimal(str(round(score, 2))), "rain": Decimal(str(rain)), "reports": len(recent), "updated": now})
        # Alert only when a zone crosses the threshold, so people are not spammed.
        if score >= ALERT_THRESHOLD and float(prev.get("score", 0)) < ALERT_THRESHOLD:
            sns.publish(
                TopicArn=os.environ["ALERT_TOPIC"],
                Subject=f"Flood risk: {zone.replace('-', ' ').title()}",
                Message=f"{zone.replace('-', ' ').title()} is likely to waterlog (risk {int(score * 100)}%). Avoid this road and check FloodSense for a safer route.",
            )
    return {"ok": True}
