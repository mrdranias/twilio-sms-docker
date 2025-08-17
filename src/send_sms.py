import os
import sys
from twilio.rest import Client


def get_env(name: str, required: bool = True, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if required and not value:
        print(f"Missing required environment variable: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def masked(value: str, keep_prefix: int = 4, keep_suffix: int = 4) -> str:
    if not value:
        return ""
    if len(value) <= keep_prefix + keep_suffix:
        return "*" * len(value)
    return value[:keep_prefix] + "*" * (len(value) - keep_prefix - keep_suffix) + value[-keep_suffix:]


def main() -> None:
    account_sid = get_env("TWILIO_ACCOUNT_SID")

    # Auth can be via Auth Token OR API Key/Secret
    api_key = os.getenv("TWILIO_API_KEY")
    api_secret = os.getenv("TWILIO_API_SECRET")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    if api_key and api_secret:
        client = Client(api_key, api_secret, account_sid)
        auth_mode = "api_key"
    elif auth_token:
        client = Client(account_sid, auth_token)
        auth_mode = "auth_token"
    else:
        print(
            "Provide either (TWILIO_AUTH_TOKEN) or (TWILIO_API_KEY and TWILIO_API_SECRET)",
            file=sys.stderr,
        )
        sys.exit(1)

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

    if os.getenv("DEBUG") == "1":
        print(
            f"Using auth_mode={auth_mode}, ACCOUNT_SID={masked(account_sid)}, "
            f"FROM={'MSG_SVC' if messaging_service_sid else masked(from_number)}, TO={masked(to_number)}"
        )

    msg_kwargs: dict[str, str] = {"to": to_number, "body": message_body}
    if messaging_service_sid:
        msg_kwargs["messaging_service_sid"] = messaging_service_sid
    else:
        msg_kwargs["from_"] = from_number  # note underscore per Twilio SDK

    message = client.messages.create(**msg_kwargs)
    print(f"Message sent. SID: {message.sid}")


if __name__ == "__main__":
    main()
