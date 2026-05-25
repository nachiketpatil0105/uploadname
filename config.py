"""
config.py — All fixed configuration values for the RBSK portal.

If any of these values change (e.g. the domain, state, district),
update them here and nowhere else.
"""

import hashlib
import os
from dotenv import load_dotenv

load_dotenv()  # reads the .env file

TEAM_CONFIG = {
    "MHT-1270379": {
        "login_id_hash":     hashlib.sha256(os.getenv("KK_LOGIN_ID", "").encode()).hexdigest(),
        "health_block_code": 148,
        "suffix":            "k",
    },
    "MHT-1270371": {
        "login_id_hash":     hashlib.sha256(os.getenv("DD_LOGIN_ID", "").encode()).hexdigest(),
        "health_block_code": 148,
        "suffix":            "d",
    },
    "MHT-1270375": {
        "login_id_hash":     hashlib.sha256(os.getenv("SS_LOGIN_ID", "").encode()).hexdigest(),
        "health_block_code": 148,
        "suffix":            "s",
    },
    "MHT-1270367": {
        "login_id_hash":     hashlib.sha256(os.getenv("GG_LOGIN_ID", "").encode()).hexdigest(),
        "health_block_code": 148,
        "suffix":            "g",
    },
}

# ---------------------------------------------------------------------------
# Portal domain
# ---------------------------------------------------------------------------
DOMAIN = "rbsk.mohfw.gov.in"

# ---------------------------------------------------------------------------
# API endpoint URLs
# ---------------------------------------------------------------------------
LIST_URL = f"https://{DOMAIN}/rbsk_webapi/api/Student/Getstudents_List"  # Used to verify token is valid
SAVE_URL = f"https://{DOMAIN}/rbsk_webapi/api/Student/Create_Update_Students"

# ---------------------------------------------------------------------------
# Fixed geographic codes (Maharashtra, Nashik district)
# ---------------------------------------------------------------------------
STATE_CODE         = 27
DISTRICT_CODE      = 3
HEALTH_BLOCK_CODE  = 148   # Chopda block — fixed, do not change

# ---------------------------------------------------------------------------
# Institution types
# ---------------------------------------------------------------------------
INSTITUTION_TYPE_AWC    = 1   # Anganwadi Centre
INSTITUTION_TYPE_SCHOOL = 2   # School

# ---------------------------------------------------------------------------
# Paths to institution list CSV files
# ---------------------------------------------------------------------------
# Instead of AWC_CSV_PATH_K, AWC_CSV_PATH_D separately — use one dict
AWC_CSV_PATHS = {
    "k": "data/awc_k.csv",
    "d": "data/awc_d.csv",
    "s": "data/awc_s.csv",
    "g": "data/awc_g.csv",
}

SCHOOL_CSV_PATHS = {
    "k": "data/school_k.csv",
    "d": "data/school_d.csv",
    "s": "data/school_s.csv",
    "g": "data/school_g.csv",
}


# ---------------------------------------------------------------------------
# Upload behaviour
# ---------------------------------------------------------------------------
REQUEST_DELAY_SECONDS = 1.5   # Pause between uploads to avoid firewall blocks

# ---------------------------------------------------------------------------
# Required columns in the student CSV
# ---------------------------------------------------------------------------
REQUIRED_CSV_COLUMNS = ["name", "father", "mother", "gender", "dob",
                         "address", "pincode", "mobile"]
