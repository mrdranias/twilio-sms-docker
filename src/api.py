from typing import Optional
import os
from fastapi import FastAPI, Depends, HTTPException, status, Header, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from twilio.rest import Client

app = FastAPI(title="Twilio SMS API")

security = HTTPBearer(auto_error=False)


class SendRequest(BaseModel):
    to: str = Field(..., description="Destination number in E.164 format, e.g. +15551234567")
    message: str = Field(..., min_length=1, max_length=1600)


def get_auth_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> None:
    expected = os.getenv("API_TOKEN")
    if not expected:
        # If API_TOKEN not set, lock down the API by default
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="API not configured")
    if not credentials or credentials.scheme != "Bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = credentials.credentials
    if token != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")


def twilio_client() -> Client:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    if not account_sid:
        raise HTTPException(status_code=500, detail="Missing TWILIO_ACCOUNT_SID")

    api_key = os.getenv("TWILIO_API_KEY")
    api_secret = os.getenv("TWILIO_API_SECRET")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    if api_key and api_secret:
        return Client(api_key, api_secret, account_sid)
    if auth_token:
        return Client(account_sid, auth_token)
    raise HTTPException(status_code=500, detail="Missing Twilio credentials")


@app.post("/send")
def send_sms(payload: SendRequest, _: None = Depends(get_auth_token)):
    messaging_service_sid = os.getenv("TWILIO_MESSAGING_SERVICE_SID")
    from_number = os.getenv("TWILIO_FROM_NUMBER")

    if not messaging_service_sid and not from_number:
        raise HTTPException(status_code=500, detail="Configure TWILIO_MESSAGING_SERVICE_SID or TWILIO_FROM_NUMBER")

    client = twilio_client()

    kwargs = {"to": payload.to, "body": payload.message}
    if messaging_service_sid:
        kwargs["messaging_service_sid"] = messaging_service_sid
    else:
        kwargs["from_"] = from_number

    try:
        message = client.messages.create(**kwargs)
    except Exception as e:
        # TwilioRestException or other client error
        raise HTTPException(status_code=502, detail=str(e))

    return {"sid": message.sid}
