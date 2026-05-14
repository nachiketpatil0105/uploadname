"""
config.py — All fixed configuration values for the RBSK portal.

If any of these values change (e.g. the domain, state, district),
update them here and nowhere else.
"""

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
AWC_CSV_PATH    = "data/awc.csv"
SCHOOL_CSV_PATH = "data/school.csv"

# ---------------------------------------------------------------------------
# Upload behaviour
# ---------------------------------------------------------------------------
REQUEST_DELAY_SECONDS = 1.5   # Pause between uploads to avoid firewall blocks

# ---------------------------------------------------------------------------
# Required columns in the student CSV
# ---------------------------------------------------------------------------
REQUIRED_CSV_COLUMNS = ["name", "father", "mother", "gender", "dob",
                         "address", "pincode", "mobile"]
