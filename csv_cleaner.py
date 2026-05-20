"""
csv_cleaner.py — Validates and cleans student CSV data.

This module checks each row of the uploaded student CSV and:
  - Flags missing required fields
  - Normalises gender to M/F
  - Validates date of birth format (YYYY-MM-DD)
  - Strips extra whitespace
  - Returns both cleaned rows and a list of problems found

Call check_and_clean() from your route handler.
"""

import re
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from config import REQUIRED_CSV_COLUMNS


def check_and_clean(rows: list[dict]) -> dict:
    """
    Validate and clean a list of student rows (each row is a dict from csv.DictReader).

    Returns a dict:
    {
        "cleaned":      [ ... list of cleaned rows ready to upload ... ],
        "needs_weight": [ ... rows for children under 1 year ... ],
        "problems":     [ ... list of problem descriptions ... ],
        "ready":        True/False  (True if no blocking errors)
    }
    """
    cleaned = []
    problems = []

    for i, row in enumerate(rows, start=2):  # start=2 because row 1 is the header
        row_errors = []

        # --- Check all required columns are present and non-empty ---
        for col in REQUIRED_CSV_COLUMNS:
            value = str(row.get(col, "")).strip()
            if not value:
                row_errors.append(f"'{col}' is empty")

        # --- Clean and validate gender ---
        gender = str(row.get("gender", "")).strip().upper()
        if gender not in ("M", "F"):
            row_errors.append(f"'gender' must be M or F, got: '{row.get('gender', '')}'")
        else:
            row["gender"] = gender

        # --- Validate date of birth format ---
        dob_str = str(row.get("dob", "")).strip()
        parsed_dob = None
        try:
            parsed_dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
            if parsed_dob > date.today():
                row_errors.append(f"'dob' is in the future: '{dob_str}'")
            else:
                row["dob"] = dob_str
        except ValueError:
            row_errors.append(f"'dob' must be YYYY-MM-DD format, got: '{dob_str}'")

        # --- Validate pincode is numeric ---
        pincode = str(row.get("pincode", "")).strip().split(".")[0]
        if not pincode.isdigit():
            row_errors.append(f"'pincode' must be a number, got: '{pincode}'")
        else:
            row["pincode"] = pincode

        # --- Validate mobile is numeric and 10 digits ---
        mobile = str(row.get("mobile", "")).strip()
        mobile = mobile.split(".")[0]  # strip .0 added by Excel/CSV float formatting
        if not re.fullmatch(r"\d{10}", mobile):
            row_errors.append(f"'mobile' must be exactly 10 digits, got: '{mobile}'")
        else:
            row["mobile"] = mobile

        # --- Strip whitespace from all string fields ---
        cleaned_row = {k: str(v).strip() for k, v in row.items()}

        if row_errors:
            problems.append({
                "row":    i,
                "name":   str(row.get("name", "Unknown")).strip(),
                "errors": row_errors
            })
        else:
            # Determine if child is under 1 year (needs birth weight).
            # parsed_dob is guaranteed to be a date object here (no dob error).
            age = relativedelta(date.today(), parsed_dob)
            if age.years < 1:
                cleaned_row["needs_weight"] = True
            else:
                cleaned_row["needs_weight"] = False
            cleaned.append(cleaned_row)

    return {
        "cleaned":      [r for r in cleaned if not r.get("needs_weight")],
        "needs_weight": [r for r in cleaned if r.get("needs_weight")],
        "problems":     problems,
        "ready":        len(problems) == 0
    }


def check_columns(fieldnames: list[str]) -> list[str]:
    """
    Check if all required columns are present in the CSV header.
    Returns a list of missing column names (empty list = all good).
    """
    fieldnames_lower = [f.strip().lower() for f in fieldnames]
    return [col for col in REQUIRED_CSV_COLUMNS if col not in fieldnames_lower]
