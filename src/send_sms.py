import os
import sys
from twilio.rest import Client


def get_env(name: str, required: bool = True, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if required and not value:
        print(f"Missing required environment variable: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def main() -> None:
    account_sid = get_env("TWILIO_ACCOUNT_SID")
    auth_token = get_env("TWILIO_AUTH_TOKEN")

    # Either use a Messaging Service SID (preferred) or a From number
    messaging_service_sid = os.getenv("TWILIO_MESSAGING_SERVICE_SID")
    from_number = os.getenv("TWILIO_FROM_NUMBER")

    if not messaging_service_sid and not from_number:
        print(
            "Provide either TWILIO_MESSAGING_SERVICE_SID or TWILIO_FROM_NUMBER in .env",
            file=sys.stderr,
        )
        sys.exit(1)

    to_number = get_env("TO_NUMBER")
    message_body = os.getenv("MESSAGE", "Hello from Twilio via Docker!")

    client = Client(account_sid, auth_token)

    msg_kwargs: dict[str, str] = {"to": to_number, "body": message_body}
    if messaging_service_sid:
        msg_kwargs["messaging_service_sid"] = messaging_service_sid
    else:
        msg_kwargs["from_"] = from_number  # note underscore per Twilio SDK

    message = client.messages.create(**msg_kwargs)
    print(f"Message sent. SID: {message.sid}")


if __name__ == "__main__":
    main()
