import os
import time
import io
import json
import re
import tempfile
from typing import List

import numpy as np
import sounddevice as sd
import soundfile as sf
import requests
from dotenv import load_dotenv
from openai import OpenAI

# Load environment
load_dotenv()

# Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE = os.getenv("SMS_API_BASE", "http://localhost:8000")
API_TOKEN = os.getenv("API_TOKEN")
TO_NUMBER = os.getenv("TO_NUMBER")
DEFAULT_MESSAGE = os.getenv("MESSAGE", "Keyword detected from microphone")
KEYWORDS = [k.strip() for k in os.getenv("KEYWORDS", "chicken nugget,chicken nuggets").split(",") if k.strip()]
STT_MODEL = os.getenv("STT_MODEL", "gpt-4o-mini-transcribe")  # fallback: whisper-1 if your project has access
USE_LOCAL_STT = os.getenv("USE_LOCAL_STT", "0") in ("1", "true", "True")
LOCAL_STT_MODEL = os.getenv("LOCAL_STT_MODEL", "base.en")  # faster-whisper model id
PRINT_TRANSCRIPTS = os.getenv("PRINT_TRANSCRIPTS", "1") in ("1", "true", "True")

# Listener params
SAMPLE_RATE = int(os.getenv("MIC_SAMPLE_RATE", "16000"))  # Whisper-friendly rate
CHANNELS = 1
BUFFER_SECONDS = float(os.getenv("BUFFER_SECONDS", "4"))
COOLDOWN_SECONDS = float(os.getenv("DETECTION_COOLDOWN_SECONDS", "15"))
SILENCE_THRESHOLD = float(os.getenv("SILENCE_THRESHOLD", "0.001"))  # RMS threshold to skip near-silence

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def _rms(audio: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(audio), dtype=np.float64)))


def record_buffer(seconds: float = BUFFER_SECONDS) -> np.ndarray:
    frames = int(seconds * SAMPLE_RATE)
    audio = sd.rec(frames, samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32")
    sd.wait()
    return audio.reshape(-1)


def transcribe_with_whisper(audio: np.ndarray) -> str:
    if not client:
        raise RuntimeError("OPENAI_API_KEY not set. Please set it in your .env.")

    # Write to an in-memory WAV
    buf = io.BytesIO()
    sf.write(buf, audio, SAMPLE_RATE, format="WAV")
    buf.seek(0)

    # Call OpenAI Speech-to-Text API
    resp = client.audio.transcriptions.create(
        model=STT_MODEL,
        file=("buffer.wav", buf, "audio/wav"),
        temperature=0.0,
    )
    # SDK returns an object with .text
    return resp.text.strip() if hasattr(resp, "text") else str(resp)


def transcribe_with_faster_whisper(audio: np.ndarray) -> str:
    try:
        from faster_whisper import WhisperModel
    except Exception as e:
        raise RuntimeError(
            "Local STT fallback requires 'faster-whisper'. Install it with: pip install faster-whisper\n"
            "Also ensure FFmpeg is available on PATH (Windows: winget install Gyan.FFmpeg or choco install ffmpeg)."
        ) from e

    # Write temp WAV (deleted immediately after)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
        sf.write(tmp.name, audio, SAMPLE_RATE, format="WAV")
        model = WhisperModel(LOCAL_STT_MODEL, compute_type="int8")
        segments, _ = model.transcribe(tmp.name, language="en")
        text = " ".join(seg.text for seg in segments).strip()
        return text


def normalize_text(s: str) -> str:
    # Lowercase, collapse whitespace, strip punctuation
    s = s.casefold()
    # Python's re does not support \p{Punct}; remove non-word, non-space chars
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def contains_keyword(text: str, keywords: List[str]) -> bool:
    norm = normalize_text(text)
    for kw in keywords:
        if kw and kw.casefold() in norm:
            return True
    return False


def send_via_api(to: str, message: str) -> dict:
    url = f"{API_BASE.rstrip('/')}/send"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {"to": to, "message": message}
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
    r.raise_for_status()
    return r.json()


def main():
    if not API_TOKEN:
        raise RuntimeError("API_TOKEN is required to call the SMS API. Set it in your .env.")
    if not TO_NUMBER:
        raise RuntimeError("TO_NUMBER is required. Set it in your .env.")
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is required for Whisper API. Set it in your .env.")

    print("Mic keyword listener started.")
    print(f"Keywords: {KEYWORDS}")
    print(f"Buffer: {BUFFER_SECONDS}s, Sample rate: {SAMPLE_RATE} Hz, Cooldown: {COOLDOWN_SECONDS}s")
    print("Press Ctrl+C to stop.")

    last_detect_ts = 0.0

    while True:
        try:
            audio = record_buffer(BUFFER_SECONDS)
            # Skip near-silence to save API calls
            if _rms(audio) < SILENCE_THRESHOLD:
                continue

            text = ""
            if USE_LOCAL_STT:
                text = transcribe_with_faster_whisper(audio)
            else:
                try:
                    text = transcribe_with_whisper(audio)
                except Exception as e:
                    # If OpenAI STT unavailable, attempt local fallback
                    err_msg = str(e)
                    if any(code in err_msg for code in ("model_not_found", "insufficient_quota", "401", "403")):
                        try:
                            print("OpenAI STT unavailable; falling back to local faster-whisper...")
                            text = transcribe_with_faster_whisper(audio)
                        except Exception as e2:
                            print("Local STT fallback failed:", e2)
                            continue
                    else:
                        print("OpenAI STT error:", e)
                        continue
            if not text:
                continue
            
            # Print the raw transcription to stdout (toggle via PRINT_TRANSCRIPTS)
            if PRINT_TRANSCRIPTS:
                print(f"Transcription: {text}")

            if contains_keyword(text, KEYWORDS):
                now = time.time()
                if now - last_detect_ts < COOLDOWN_SECONDS:
                    # Debounce repeated detections
                    continue
                last_detect_ts = now

                msg = f"Keyword detected: '{text}'" if DEFAULT_MESSAGE == "Keyword detected from microphone" else DEFAULT_MESSAGE
                try:
                    resp = send_via_api(TO_NUMBER, msg)
                    print("SMS sent:", resp)
                except Exception as e:
                    print("Failed to send SMS:", e)
            # else: drop the buffer; do nothing
        except KeyboardInterrupt:
            print("\nStopping listener.")
            break
        except Exception as e:
            print("Error:", e)
            time.sleep(1)


if __name__ == "__main__":
    main()
