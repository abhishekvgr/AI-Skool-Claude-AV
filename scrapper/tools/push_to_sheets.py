"""Push a CSV into a Google Sheet (new spreadsheet, or replace the first tab of an existing one).

The first run opens a browser for Google sign-in and saves token.json.

Usage:
    python tools/push_to_sheets.py --csv .tmp/dailyremote/jobs.csv [--title "My Sheet"] [--sheet-id <id>]
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--csv", required=True)
    ap.add_argument("--title", default=f"DailyRemote – Data Engineering – {date.today()}")
    ap.add_argument("--sheet-id", help="Existing spreadsheet ID; its first tab is overwritten")
    args = ap.parse_args()

    with open(args.csv, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    if len(rows) < 2:
        sys.exit(f"No data rows in {args.csv}")
    rows[0] = [h.replace("_", " ").title() for h in rows[0]]

    sheets = build("sheets", "v4", credentials=get_credentials()).spreadsheets()
    if args.sheet_id:
        sheet_id = args.sheet_id
        meta = sheets.get(spreadsheetId=sheet_id).execute()
    else:
        meta = sheets.create(body={"properties": {"title": args.title}}).execute()
        sheet_id = meta["spreadsheetId"]
    tab = meta["sheets"][0]["properties"]

    sheets.values().clear(spreadsheetId=sheet_id, range=tab["title"]).execute()
    sheets.values().update(
        spreadsheetId=sheet_id, range=f"'{tab['title']}'!A1",
        valueInputOption="RAW", body={"values": rows},
    ).execute()

    tab_id, ncols = tab["sheetId"], len(rows[0])
    sheets.batchUpdate(spreadsheetId=sheet_id, body={"requests": [
        {"updateSheetProperties": {"properties": {"sheetId": tab_id, "gridProperties": {"frozenRowCount": 1}},
                                   "fields": "gridProperties.frozenRowCount"}},
        {"repeatCell": {"range": {"sheetId": tab_id, "startRowIndex": 0, "endRowIndex": 1},
                        "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                        "fields": "userEnteredFormat.textFormat.bold"}},
        # Clip long text so rows stay one line high; widths are set rather than auto-sized for the same reason.
        {"repeatCell": {"range": {"sheetId": tab_id, "startRowIndex": 1},
                        "cell": {"userEnteredFormat": {"wrapStrategy": "CLIP"}},
                        "fields": "userEnteredFormat.wrapStrategy"}},
        {"updateDimensionProperties": {"range": {"sheetId": tab_id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": ncols},
                                       "properties": {"pixelSize": 180}, "fields": "pixelSize"}},
        # Descriptions contain line breaks, which grow rows to hundreds of pixels even when clipped.
        {"updateDimensionProperties": {"range": {"sheetId": tab_id, "dimension": "ROWS", "startIndex": 1, "endIndex": len(rows)},
                                       "properties": {"pixelSize": 21}, "fields": "pixelSize"}},
    ]}).execute()

    print(f"{len(rows) - 1} rows -> https://docs.google.com/spreadsheets/d/{sheet_id}")


if __name__ == "__main__":
    main()
