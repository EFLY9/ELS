"""Google Sheets storage backend for ELS submissions."""
import json
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SHEET_ID = "1U-N0ELezeETFVgQR9Bqk42CwVq0eBz1xwQsVfkB8hiI"
HEADERS = ["id", "product_type", "brand", "model", "report_ref", "status", "submitted_at", "auto_approved", "json_data"]


def _get_sheet():
    """Get the Google Sheet worksheet, using Streamlit secrets for credentials."""
    import streamlit as st
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    try:
        ws = sheet.worksheet("submissions")
    except gspread.WorksheetNotFound:
        ws = sheet.add_worksheet("submissions", rows=1000, cols=len(HEADERS))
        ws.append_row(HEADERS)
    if not ws.row_values(1):
        ws.append_row(HEADERS)
    return ws


def load_all_submissions():
    """Load all submissions from Google Sheets."""
    ws = _get_sheet()
    rows = ws.get_all_records()
    subs = []
    for row in rows:
        try:
            data = json.loads(row.get("json_data", "{}"))
            subs.append(data)
        except (json.JSONDecodeError, TypeError):
            continue
    subs.sort(key=lambda s: s.get("submitted_at", ""), reverse=True)
    return subs


def save_submission(submission):
    """Save a new submission to Google Sheets."""
    ws = _get_sheet()
    row = [
        submission["id"],
        submission.get("product_type", "tv"),
        submission.get("brand", ""),
        submission.get("model", ""),
        submission.get("report_ref", ""),
        submission.get("status", "Pending Review"),
        submission.get("submitted_at", ""),
        str(submission.get("auto_approved", False)),
        json.dumps(submission),
    ]
    ws.append_row(row, value_input_option="RAW")


def update_submission(submission_id, updated_data):
    """Update an existing submission in Google Sheets."""
    ws = _get_sheet()
    cells = ws.col_values(1)
    row_idx = None
    for i, val in enumerate(cells):
        if val == submission_id:
            row_idx = i + 1
            break
    if row_idx is None:
        return False

    row = [
        updated_data["id"],
        updated_data.get("product_type", "tv"),
        updated_data.get("brand", ""),
        updated_data.get("model", ""),
        updated_data.get("report_ref", ""),
        updated_data.get("status", "Pending Review"),
        updated_data.get("submitted_at", ""),
        str(updated_data.get("auto_approved", False)),
        json.dumps(updated_data),
    ]
    ws.update(f"A{row_idx}:I{row_idx}", [row], value_input_option="RAW")
    return True


def delete_submission(submission_id):
    """Delete a submission from Google Sheets."""
    ws = _get_sheet()
    cells = ws.col_values(1)
    for i, val in enumerate(cells):
        if val == submission_id:
            ws.delete_rows(i + 1)
            return True
    return False


def get_submission(submission_id):
    """Get a single submission by ID."""
    ws = _get_sheet()
    rows = ws.get_all_records()
    for row in rows:
        if row.get("id") == submission_id:
            try:
                return json.loads(row.get("json_data", "{}"))
            except (json.JSONDecodeError, TypeError):
                return None
    return None
