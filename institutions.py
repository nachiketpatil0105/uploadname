"""
institutions.py — Loads AWC and school lists from CSV files.

Used to populate the dropdown menus on the website.
"""

import csv
from config import AWC_CSV_PATH_K, SCHOOL_CSV_PATH_K, AWC_CSV_PATH_D, SCHOOL_CSV_PATH_D


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


def get_awc_list(suffix: str) -> list[dict]:
    path = AWC_CSV_PATH_K if suffix == "k" else AWC_CSV_PATH_D
    return load_institutions(path)


def get_school_list(suffix: str) -> list[dict]:
    path = SCHOOL_CSV_PATH_K if suffix == "k" else SCHOOL_CSV_PATH_D
    return load_institutions(path)
