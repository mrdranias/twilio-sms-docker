# Twilio SMS via Docker (Python)

A milestone-based project to reliably send SMS messages with Twilio, starting from a simple containerized script and growing into API and device integrations.

## Overview / Roadmap
- Milestone 1 (done): Container sends an SMS via Twilio API
- Milestone 2 (done): HTTP API (FastAPI) to trigger SMS on demand
- Milestone 3 (done): Send SMS from a Jupyter Notebook
- Milestone 4 (current): Mic keyword listener (OpenAI Whisper) triggers SMS
- Milestone 5 (next): Event bridge + simple rules (device/webhook → event → SMS)
- Milestone 6 (final): Computer vision + semantic scene recognition → SMS

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

## Milestone 2 — HTTP API Service (Done)
Expose an endpoint to send SMS via HTTP, enabling webhooks and device triggers.

- Stack: FastAPI + Uvicorn in the same Docker/Compose setup.
- Endpoint: `POST /send` with JSON body `{ "to": "+1...", "message": "..." }`
- Auth: simple bearer token or basic auth via env vars (e.g., `API_TOKEN`).
- Compose: add a new service `api` exposing port 8000.

Example request (planned):
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

### Run via Docker Compose
```bash
docker compose build
docker compose up -d jupyter
# Open http://localhost:8888 and run your notebook or Python cells
```

> Tip: From containers, target the API as `http://api:8000`. From host, use `http://localhost:8000`.

---

## Milestone 4 — Mic Keyword Listener (Current)
Use the desktop microphone and OpenAI Whisper to detect keywords (e.g., "chicken nugget(s)") and send an SMS via the existing API.

### Setup
1. Add to `.env`:
   - `OPENAI_API_KEY=...`
   - Optional tuning: `KEYWORDS=chicken nugget,chicken nuggets`, `BUFFER_SECONDS=4`, `MIC_SAMPLE_RATE=16000`, `DETECTION_COOLDOWN_SECONDS=15`, `SILENCE_THRESHOLD=0.001`
2. Ensure the API is running:
   ```bash
   docker compose up -d api
   ```

### Run (host, recommended for mic access)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/keyword_listener.py
```

Speak the keywords; you'll receive an SMS upon detection. Buffers are not saved (in-memory only). This is a stepping stone; we can later containerize on WSL/Linux with proper audio device mapping.

## Milestone 5 — Event Bridge + Rules (Planned)
Add `POST /event` and a minimal rules engine to map events to messages (e.g., device=ring && type=motion → SMS). Provide examples for Raspberry Pi and webhooks (Home Assistant/IFTTT/ngrok/cloudflared).

## Milestone 6 — Computer Vision + Semantics (Planned)
Detect objects and scenes from a camera/stream and trigger SMS. Options:
- Local: YOLO/RT-DETR + CLIP/embeddings in a `cv` service posting events.
- Cloud: call a vision API on frames. Wire to `/event` → rules → SMS.

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
