# Twilio SMS via Docker (Python)

A milestone-based project to reliably send SMS messages with Twilio, starting from a simple containerized script and growing into API and device integrations.

## Overview / Roadmap
- Milestone 1 (now): Container sends an SMS via Twilio API
- Milestone 2: Add an HTTP API (FastAPI) to trigger SMS on demand
- Milestone 3: Send SMS from a Jupyter Notebook
- Milestone 4: Integrate with a device (Raspberry Pi GPIO or Ring trigger)

---

## Milestone 1 — Container sends SMS (Current)
Send a test SMS to your phone using Twilio, packaged in Docker and run with Docker Compose.

### Prerequisites
- Twilio account with an Account SID and Auth Token
- Either:
  - A Messaging Service SID, or
  - A Twilio phone number capable of SMS
- Docker and Docker Compose installed

### Files
- `Dockerfile`: Python 3.11-slim base image
- `docker-compose.yml`: service `sms` that loads `.env`
- `requirements.txt`: includes `twilio`
- `src/send_sms.py`: one-shot script to send an SMS
- `.env.example`: copy to `.env` and fill in real values

### Setup
1. Create your env file:
   ```bash
   cp .env.example .env
   # Edit .env and fill in your real values
   ```

### Build and Run
```bash
# Build image
docker compose build

# Send a test message (uses default message)
docker compose run --rm sms

# Override the message at runtime
docker compose run --rm -e MESSAGE="Hello from Docker Compose!" sms
```
If successful, you'll see the message SID in the output.

### Environment Variables
- `TWILIO_ACCOUNT_SID` (required)
- `TWILIO_AUTH_TOKEN` (required)
- `TWILIO_MESSAGING_SERVICE_SID` (recommended; optional)
- `TWILIO_FROM_NUMBER` (optional if Messaging Service is used)
- `TO_NUMBER` (required; destination in E.164 format, e.g. `+15551234567`)
- `MESSAGE` (optional; custom message body)

> Notes:
> - On Twilio trial accounts you can only text verified numbers.
> - E.164 format required (leading `+` and country code).

---

## Milestone 2 — HTTP API Service (Plan)
Expose an endpoint to send SMS via HTTP, enabling webhooks and device triggers.

- Stack: FastAPI + Uvicorn in the same Docker/Compose setup.
- Endpoint: `POST /send` with JSON body `{ "to": "+1...", "message": "..." }`
- Auth: simple bearer token or basic auth via env vars (e.g., `API_TOKEN`).
- Compose: add a new service `api` exposing port 8000.

Example request (planned):
```bash
curl -X POST http://localhost:8000/send \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to":"+15551234567","message":"Hello from API"}'
```

> When you’re ready, I’ll scaffold `src/api.py`, dependency updates, and Compose changes.

---

## Milestone 3 — Jupyter Notebook Sender (Plan)
Send SMS directly from a notebook for experimentation and demos.

Options:
- Add a `jupyter` service in Compose using the same image and mount the repo.
- Or run a local notebook with `pip install twilio` and load `.env`.

Minimal Python cell:
```python
import os
from twilio.rest import Client

client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
message = client.messages.create(
    to=os.environ["TO_NUMBER"],
    from_=os.getenv("TWILIO_FROM_NUMBER"),  # or messaging_service_sid=...
    body="Hello from Jupyter"
)
message.sid
```

> I can add a `notebooks/` folder and a `docker-compose` Jupyter service (with token disabled for local).

---

## Milestone 4 — Device Integrations (Plan)
Connect physical or cloud devices to trigger SMS.

- Raspberry Pi:
  - Option A: call the HTTP API (Milestone 2) from Pi scripts.
  - Option B: run this container on the Pi and execute `docker run --env-file .env twilio-sms:latest` on events.
- Ring Doorbell:
  - If available, configure a webhook or use an integration to POST to the API service.
  - Alternatively, run a small polling/subscribe script that triggers the API when events occur.

> I’ll add example scripts and a small guide per device when you’re ready.

---

## Security
- Keep `.env` out of version control (already in `.gitignore`).
- Prefer Messaging Service over raw numbers for deliverability and management.
- Add basic auth/bearer token to the API service before exposing outside localhost.

## Next Actions
- Milestone 1: Fill `.env`, build, and run to send a test SMS.
- Tell me when to proceed and I’ll scaffold Milestone 2 (FastAPI service) next.



## GENERATE SSH KEY
ssh-keygen -t ed25519 -C "your_email@example.com"
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub
copy output; go to github.com; settings; SSH and GPG keys; New SSH key; paste; Add SSH key
