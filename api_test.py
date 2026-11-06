import os
import requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("OPENAQ_API_KEY", "").strip()
if not key:
    raise SystemExit("Add OPENAQ_API_KEY to .env first.")

response = requests.get(
    "https://api.openaq.org/v3/locations",
    headers={"X-API-Key": key},
    params={"coordinates": "14.5995,120.9842", "radius": 25000, "limit": 5},
    timeout=30,
)
print("HTTP status:", response.status_code)
response.raise_for_status()
data = response.json()
print("Locations returned:", len(data.get("results", [])))
for location in data.get("results", []):
    print("-", location.get("id"), location.get("name"))
