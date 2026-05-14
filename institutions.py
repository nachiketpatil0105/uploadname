"""
institutions.py — Loads AWC and school lists from CSV files.

Used to populate the dropdown menus on the website.
"""

import csv
from config import AWC_CSV_PATH, SCHOOL_CSV_PATH


def load_institutions(csv_path: str) -> list[dict]:
    """
    Read a CSV file with columns: code, name
    Returns a list of dicts like: [{"code": 105630, "name": "GARTAD 1"}, ...]
    """
    institutions = []
    try:
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                institutions.append({
                    "code": int(str(row["code"]).strip()),
                    "name": str(row["name"]).strip()
                })
    except FileNotFoundError:
        print(f"[!] Warning: Could not find file: {csv_path}")
    return institutions


def get_awc_list() -> list[dict]:
    return load_institutions(AWC_CSV_PATH)


def get_school_list() -> list[dict]:
    return load_institutions(SCHOOL_CSV_PATH)
