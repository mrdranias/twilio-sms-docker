# Cell 1 — Title / Prereqs
# Jupyter SMS Sender (Twilio + HTTP API)
# If needed, install deps in a notebook cell:
# %pip install twilio requests python-dotenv

# Cell 2 — Imports
import os
import json
from typing import Optional

import requests
from twilio.rest import Client

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Cell 3 — Load environment (.env) and config
# If you keep a .env in project root, load it (optional)
if load_dotenv:
    load_dotenv()

# Twilio credentials (either Auth Token OR API Key/Secret)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_API_KEY = os.getenv("TWILIO_API_KEY")
TWILIO_API_SECRET = os.getenv("TWILIO_API_SECRET")

# From settings (use one): Messaging Service SID or a From number
TWILIO_MESSAGING_SERVICE_SID = os.getenv("TWILIO_MESSAGING_SERVICE_SID")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")

# Destination and default message
TO_NUMBER = os.getenv("TO_NUMBER")  # e.g., +15551234567
DEFAULT_MESSAGE = os.getenv("MESSAGE", "Hello from Jupyter!")

# HTTP API config (Milestone 2)
API_BASE = os.getenv("SMS_API_BASE", "http://localhost:8000")
API_TOKEN = os.getenv("API_TOKEN")  # Bearer token for your FastAPI service

# Cell 4 — Helper: Twilio client builder
def make_twilio_client() -> Client:
    if TWILIO_API_KEY and TWILIO_API_SECRET and TWILIO_ACCOUNT_SID:
        return Client(TWILIO_API_KEY, TWILIO_API_SECRET, TWILIO_ACCOUNT_SID)
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
        return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    raise RuntimeError(
        "Missing Twilio credentials. Set either (ACCOUNT_SID + AUTH_TOKEN) or (API_KEY + API_SECRET + ACCOUNT_SID)."
    )

# Cell 5 — Send via Twilio SDK (direct)
def send_sms_via_twilio(to: str, body: str) -> str:
    if not (TWILIO_MESSAGING_SERVICE_SID or TWILIO_FROM_NUMBER):
        raise RuntimeError("Configure TWILIO_MESSAGING_SERVICE_SID or TWILIO_FROM_NUMBER in your environment.")
    client = make_twilio_client()
    kwargs = {"to": to, "body": body}
    if TWILIO_MESSAGING_SERVICE_SID:
        kwargs["messaging_service_sid"] = TWILIO_MESSAGING_SERVICE_SID
    else:
        kwargs["from_"] = TWILIO_FROM_NUMBER
    msg = client.messages.create(**kwargs)
    return msg.sid

# Cell 6 — Send via HTTP API (FastAPI service)
def send_sms_via_api(to: str, body: str, base: Optional[str] = None, token: Optional[str] = None) -> dict:
    base = base or API_BASE
    token = token or API_TOKEN
    if not token:
        raise RuntimeError("API_TOKEN is not set. Provide a token for the Bearer Authorization header.")
    url = f"{base.rstrip('/')}/send"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {"to": to, "message": body}
    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"API Error {resp.status_code}: {resp.text}")
    return resp.json()

# Cell 7 — Try sending (choose one or both)
if __name__ == "__main__":
    to = TO_NUMBER or "+15551234567"  # replace if TO_NUMBER not set
    body = DEFAULT_MESSAGE

    print("Attempting direct Twilio send...")
    try:
        sid_direct = send_sms_via_twilio(to, body)
        print("Direct Twilio send OK. SID:", sid_direct)
    except Exception as e:
        print("Direct Twilio send failed:", e)

    print("\nAttempting API send...")
    try:
        result_api = send_sms_via_api(to, body)
        print("API send OK. Response:", result_api)
    except Exception as e:
        print("API send failed:", e)

# Cell 8 — Notes / Troubleshooting
# - Ensure .env has valid LIVE Twilio creds and either a Messaging Service SID or From number.
# - Trial accounts can only message verified numbers.
# - For API calls:
#   - docker compose up -d api
#   - API_TOKEN must be set in .env and passed to the container (already handled by docker-compose.yml).
#   - Test via curl:
#       TOKEN=$(grep '^API_TOKEN=' .env | cut -d= -f2-)
#       curl -X POST http://localhost:8000/send \
#         -H "Authorization: Bearer $TOKEN" \
#         -H "Content-Type: application/json" \
#         -d '{"to":"+15551234567","message":"Hello from API via curl"}'
