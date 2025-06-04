"""
storage.py

Provides two functions:
- append_row: add a timestamped mood entry to Google Sheets.
- get_today_counts: fetch counts of each mood (1-5) for today.
"""

import os
import json
import streamlit as st 
from datetime import datetime
from zoneinfo import ZoneInfo

from gspread.auth import service_account_from_dict
from gspread.utils import ValueInputOption

from dotenv import load_dotenv

load_dotenv()

# ─── CONFIGS ─────────────────────────────────────────────────────────────
# used the os.getenv initially, but after setting the streamlit-autorefresh, it got shakey and would fail credential checks..
#       so swapped to using streamlit secrets
GOOGLE_SECRETS = st.secrets["GOOGLE"]
SERVICE_ACCOUNT_JSON = GOOGLE_SECRETS["SERVICE_ACCOUNT_JSON"]
SHEET_ID = GOOGLE_SECRETS["SHEET_ID"].strip()

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

def _authorize():
    """
    Build and return an authorized gspread client using the JSON in SERVICE_ACCOUNT_JSON.
    """
    try:
        cred_dict = json.loads(SERVICE_ACCOUNT_JSON)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid SERVICE_ACCOUNT_JSON: {e}")

    try:
        client = service_account_from_dict(cred_dict, scopes=SCOPE)
        return client
    except Exception as e:
        raise RuntimeError(f"gspread authorization failed: {e}")


def append_row(mood: int, note: str = "") -> bool:
    """
    Append a row [timestamp, mood, note] to the first worksheet of the Sheet.
    Timestamp is ISO8601 in US/Pacific time.
    Returns True on success, False otherwise.
    """
    try:
        client = _authorize()
        sheet = client.open_by_key(SHEET_ID).sheet1
    except Exception as e:
        st.error(f"Auth error: {e}")
        return False

    timestamp = datetime.now(tz=ZoneInfo("US/Pacific")).isoformat(sep=" ", timespec="seconds")
    row = [timestamp, mood, note]
    try:
        sheet.append_row(row, value_input_option=ValueInputOption.user_entered)
        return True
    except Exception as e:
        st.error(f"Failed to append row: {e}")
        return False


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
    except Exception as e:
        st.error(f"Auth error (get_counts): {e}")
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


def get_latest_notes() -> dict[int, str]:
    """
    Returns a dict {1: latest_note_for_mood1, 2: …, …, 5: …}.
    """
    client = _authorize()
    sheet = client.open_by_key(SHEET_ID).sheet1
    records = sheet.get_all_records()  # each record has "timestamp","mood","note"
    latest = {}
    for rec in records:
        mood_val = int(rec.get("mood", 0))
        note_text = rec.get("note", "") or ""
        ts = str(rec.get("timestamp", ""))
        if not note_text or not ts:
            continue
        if (
            mood_val not in latest
            or ts > latest[mood_val][0]
        ):
            latest[mood_val] = (ts, note_text)
    # Convert to just note‐text, default to empty string if none:
    return {i: latest.get(i, ("", ""))[1] for i in range(1, 6)}