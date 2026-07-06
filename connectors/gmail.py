import argparse
import base64
import os
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
]


def get_credentials_path():
    for candidate in [
        os.path.join(BASE_DIR, "Credentials.json"),
        os.path.join(BASE_DIR, "credentials.json"),
    ]:
        if os.path.exists(candidate):
            return candidate
    return os.path.join(BASE_DIR, "credentials.json")


def get_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                get_credentials_path(), SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def list_messages(service, max_results=10, query=None):
    results = service.users().messages().list(
        userId="me",
        maxResults=max_results,
        q=query,
    ).execute()
    return results.get("messages", [])


def get_message_summary(service, message_id):
    message = service.users().messages().get(
        userId="me",
        id=message_id,
        format="metadata",
        metadataHeaders=["Subject", "From"],
    ).execute()

    headers = {h["name"]: h["value"] for h in message.get("payload", {}).get("headers", [])}
    return {
        "id": message_id,
        "from": headers.get("From", "(unknown sender)"),
        "subject": headers.get("Subject", "(no subject)"),
        "snippet": message.get("snippet", ""),
    }


def create_message(to, subject, body):
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return {"raw": raw}


def send_message(service, to, subject, body):
    message = create_message(to, subject, body)
    return service.users().messages().send(userId="me", body=message).execute()


def create_draft(service, to, subject, body):
    message = create_message(to, subject, body)
    return service.users().drafts().create(userId="me", body={"message": message}).execute()


def summarize_from_sender(service, sender, max_results=10):
    messages = list_messages(service, max_results=max_results, query=f"from:{sender}")
    if not messages:
        print(f"No emails found from {sender}.")
        return

    print(f"Found {len(messages)} email(s) from {sender}:\n")
    for msg in messages:
        summary = get_message_summary(service, msg["id"])
        print(f"[{summary['id']}] {summary['subject']}")
        print(f"    {summary['snippet']}")
        print()


def prompt_action():
    menu = {
        "1": ("list", "List recent emails"),
        "2": ("read", "Read an email"),
        "3": ("draft", "Compose (save as draft)"),
        "4": ("send", "Send an email"),
        "5": ("summarize", "Summarize emails from a sender"),
        "6": ("quit", "Quit"),
    }
    while True:
        print("What would you like to do?")
        for key, (_, label) in menu.items():
            print(f"  {key}) {label}")
        choice = input("Enter choice: ").strip()
        if choice in menu:
            return menu[choice][0]
        print("Invalid choice. Please try again.\n")


def main():
    parser = argparse.ArgumentParser(description="Automate Gmail read/send actions")
    parser.add_argument("--to", help="Recipient email address")
    parser.add_argument("--subject", default=None, help="Email subject (prompted if omitted)")
    parser.add_argument("--body", default=None, help="Email body (prompted if omitted)")
    parser.add_argument("--message-id", help="Message ID to read")
    parser.add_argument("--max-results", type=int, default=10, help="Number of emails to list")
    parser.add_argument("--query", default="", help="Gmail search query")
    parser.add_argument("--sender", help="Email address to summarize messages from")

    args = parser.parse_args()
    service = get_service()

    while True:
        action = prompt_action()

        if action == "quit":
            break

        if action == "list":
            messages = list_messages(service, max_results=args.max_results, query=args.query)
            for msg in messages:
                summary = get_message_summary(service, msg["id"])
                print(f"[{summary['id']}] {summary['from']} - {summary['subject']}")
                print(f"    {summary['snippet']}")

        elif action == "read":
            message_id = args.message_id
            if message_id is None:
                messages = list_messages(service, max_results=1)
                if not messages:
                    print("No messages found.")
                    continue
                message_id = messages[0]["id"]

            summary = get_message_summary(service, message_id)
            print(f"From: {summary['from']}")
            print(f"Subject: {summary['subject']}")
            print(f"Snippet: {summary['snippet']}")

        elif action == "send":
            to = args.to or input("To: ").strip()
            if not to:
                print("A recipient email address is required.")
                continue
            subject = args.subject if args.subject is not None else input("Subject: ").strip()
            body = args.body if args.body is not None else input("Body: ").strip()
            result = send_message(service, to, subject, body)
            print(f"Email sent: {result.get('id')}")

        elif action == "summarize":
            sender = args.sender or input("Sender email: ").strip()
            if not sender:
                print("A sender email address is required.")
                continue
            summarize_from_sender(service, sender, max_results=args.max_results)

        elif action == "draft":
            to = args.to or input("To: ").strip()
            if not to:
                print("A recipient email address is required.")
                continue
            subject = args.subject if args.subject is not None else input("Subject: ").strip()
            body = args.body if args.body is not None else input("Body: ").strip()
            result = create_draft(service, to, subject, body)
            print(f"Draft created: {result.get('id')}")

        args.to = args.subject = args.body = args.message_id = args.sender = None
        print()


if __name__ == "__main__":
    main()
