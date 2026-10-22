"""Create a Gmail draft from rendered newsletter HTML, embedding images inline.

The first run opens a browser for Google sign-in and saves token.json.

Usage:
    python tools/create_gmail_draft.py --content .tmp/ai-agents/content.json [--to you@example.com]
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import sys
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]
ROOT = Path(__file__).resolve().parent.parent


def get_credentials() -> Credentials:
    token_path, creds_path = ROOT / "token.json", ROOT / "credentials.json"
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        if not creds_path.exists():
            sys.exit(f"Missing {creds_path}. Download an OAuth Desktop client from Google Cloud Console.")
        creds = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES).run_local_server(port=0)
    token_path.write_text(creds.to_json())
    return creds


def html_to_text(markup: str) -> str:
    text = re.sub(r"<(style|title)[^>]*>.*?</\1>", "", markup, flags=re.S)
    text = re.sub(r"<a [^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", r"\2 (\1)", text, flags=re.S)
    text = re.sub(r"<(br|/p|/h\d|/li|/div)[^>]*>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return html.unescape(text).strip()


def build_message(markup: str, subject: str, to: str, images_dir: Path) -> MIMEMultipart:
    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    if to:
        msg["To"] = to

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(html_to_text(markup), "plain", "utf-8"))
    alt.attach(MIMEText(markup, "html", "utf-8"))
    msg.attach(alt)

    for cid in sorted(set(re.findall(r'src="cid:([^"]+)"', markup))):
        matches = list(images_dir.glob(f"{cid}.*"))
        if not matches:
            sys.exit(f"HTML references cid:{cid} but no matching file is in {images_dir}")
        img = MIMEImage(matches[0].read_bytes())
        img.add_header("Content-ID", f"<{cid}>")
        img.add_header("Content-Disposition", "inline", filename=matches[0].name)
        msg.attach(img)
    return msg


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content", required=True, help="Path to content.json (newsletter.html must sit beside it)")
    parser.add_argument("--to", help="Recipient; defaults to GMAIL_TO in .env")
    args = parser.parse_args()

    load_dotenv()
    content_path = Path(args.content)
    content = json.loads(content_path.read_text())
    markup = (content_path.parent / "newsletter.html").read_text()
    to = args.to or os.getenv("GMAIL_TO", "")

    msg = build_message(markup, content["subject"], to, content_path.parent / "images")
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    service = build("gmail", "v1", credentials=get_credentials())
    draft = service.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
    print(f"Created Gmail draft {draft['id']} (to: {to or 'no recipient set'})")
    print("Open it at https://mail.google.com/mail/u/0/#drafts")


if __name__ == "__main__":
    main()
