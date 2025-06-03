"""
storage.py

Provides two functions:
- append_row: add a timestamped mood entry to Google Sheets.
- get_today_counts: fetch counts of each mood (1-5) for today.
"""

import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import gspread
from gspread.auth import service_account_from_dict
from gspread.utils import ValueInputOption

from dotenv import load_dotenv

load_dotenv()

# ─── CONFIGURATION ─────────────────────────────────────────────────────────────
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "").strip()

if not SHEET_ID:
    raise RuntimeError("Please set the GOOGLE_SHEET_ID environment variable.")

def _authorize():
    """
    Build and return an authorized gspread client using the JSON in SERVICE_ACCOUNT_JSON.
    """
    raw = os.getenv("SERVICE_ACCOUNT_JSON", "")
    if not raw:
        raise RuntimeError("SERVICE_ACCOUNT_JSON not set.")

    try:
        cred_dict = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError("SERVICE_ACCOUNT_JSON is not valid JSON.") from e

    client = service_account_from_dict(cred_dict, scopes=SCOPE)
    return client

def append_row(mood: int, note: str = "") -> bool:
    """
    Append a row [timestamp, mood, note] to the first worksheet of the Sheet.
    Timestamp is ISO8601 in US/Pacific time.
    Returns True on success, False otherwise.
    """
    try:
        client = _authorize()
        sheet = client.open_by_key(SHEET_ID).sheet1
    except Exception:
        return False

    timestamp = datetime.now(tz=ZoneInfo("US/Pacific")).isoformat(sep=" ", timespec="seconds")
    row = [timestamp, mood, note]
    try:
        sheet.append_row(row, value_input_option=ValueInputOption.user_entered)
        return True
    except Exception:
        return False

def get_today_counts() -> dict[int, int]:
    """
    Fetch all rows from the first worksheet, filter for today's entries (US/Pacific),
    and return a dict mapping mood (1-5) to its count.
    """
    counts = {i: 0 for i in range(1, 6)}
    try:
        client = _authorize()
        sheet = client.open_by_key(SHEET_ID).sheet1
        all_records = sheet.get_all_records()
    except Exception:
        return counts  # return zeros on failure

    today_str = datetime.now(tz=ZoneInfo("US/Pacific")).date().isoformat()
    for rec in all_records:
        # assuming headers: "timestamp", "mood", "note"
        ts = rec.get("timestamp", "")
        if not ts:
            continue
        # ts format: "YYYY-MM-DD HH:MM:SS"
        date_part = str(ts)[:10]
        if date_part != today_str:
            continue
        try:
            mood_val = int(rec.get("mood", 0))
        except ValueError:
            continue
        if 1 <= mood_val <= 5:
            counts[mood_val] += 1

    return counts


def get_counts_between(start_date: str, end_date: str) -> dict[int, int]:
    """
    Return a dict of mood-counts between start_date and end_date (inclusive).
    Dates are strings in "YYYY-MM-DD" format (US/Pacific).
    """
    counts = {i: 0 for i in range(1, 6)}
    try:
        client = _authorize()
        sheet = client.open_by_key(SHEET_ID).sheet1
        all_records = sheet.get_all_records()
    except Exception:
        return counts

    # Ensure dates are comparable:
    for rec in all_records:
        ts = rec.get("timestamp", "")
        if not ts:
            continue
        date_part = str(ts)[:10]  # "YYYY-MM-DD"
        if not (start_date <= date_part <= end_date):
            continue
        try:
            mood_val = int(rec.get("mood", 0))
        except ValueError:
            continue
        if 1 <= mood_val <= 5:
            counts[mood_val] += 1
    return counts
