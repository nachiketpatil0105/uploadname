"""
portal_api.py — All communication with the RBSK portal API.

This module handles:
  - Creating an authenticated HTTP session
  - Setting the institution context (required before uploading)
  - Uploading a single student record

All other files should import from here instead of making
their own requests.post() calls.
"""

import time
import urllib3
import requests
from config import (
    DOMAIN, LIST_URL, SAVE_URL,
    STATE_CODE, DISTRICT_CODE, REQUEST_DELAY_SECONDS
)

# Suppress SSL warnings (portal uses a self-signed certificate)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def create_session(token: str) -> requests.Session:
    """
    Create an authenticated requests.Session using the access token
    copied from the browser. Returns the session object.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent":   (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept":       "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin":       f"https://{DOMAIN}",
        "Referer":      f"https://{DOMAIN}/RBSK/studentmaster",
    })
    session.cookies.set("accessToken", token, domain=DOMAIN)
    return session


def verify_token(session: requests.Session, institution_type: int,
                 institution_code: int, health_block_code: int) -> dict:
    """
    Verify that the access token is valid by making a lightweight list call.

    NOTE: There is no separate "set context" endpoint on this portal.
    Institution info is embedded in every upload_student payload directly.
    This function only checks that the token is accepted by the server.

    Returns: {"success": True/False, "message": "..."}
    """
    payload = {
        "state_code":        STATE_CODE,
        "district_code":     DISTRICT_CODE,
        "health_block_code": health_block_code,
        "institution_type":  institution_type,
        "institution_code":  institution_code,
        "status":            1,
        "student_code":      0,
        "student_name":      "",
        "abha_number":       "",
    }
    try:
        response = session.post(LIST_URL, json=payload, verify=False, timeout=15)
        if response.status_code == 401:
            return {"success": False, "message": "Token expired or invalid. Please copy a fresh token from your browser."}
        if response.status_code != 200:
            return {"success": False, "message": f"Server returned HTTP {response.status_code}"}
        return {"success": True, "message": "Token verified successfully."}
    except requests.RequestException as e:
        return {"success": False, "message": f"Could not reach the portal: {e}"}


# Alias for backward compatibility
def set_institution_context(session, institution_type, institution_code, health_block_code):
    return verify_token(session, institution_type, institution_code, health_block_code)


def upload_student(session: requests.Session, student: dict, institution_type: int,
                   institution_code: int, health_block_code: int, created_by: int) -> dict:
    """
    Upload a single student record to the portal.

    Parameters:
        session           : Authenticated requests.Session
        student           : Dict with keys: name, father, mother, gender,
                            dob, address, pincode, mobile
        institution_type  : 1 (AWC) or 2 (School)
        institution_code  : Numeric institution ID
        health_block_code : Numeric health block ID
        created_by        : loginID of the logged-in portal user

    Returns: {"success": True/False, "message": "..."}
    """
    payload = {
        "action":              "Insert",
        "student_code":        0,
        "institution_type":    institution_type,
        "institution_code":    institution_code,
        "state_code":          STATE_CODE,
        "district_code":       DISTRICT_CODE,
        "health_block_code":   health_block_code,
        "created_By":          created_by,

        # Student personal details
        "student_name":        str(student["name"]).strip(),
        "student_father":      str(student["father"]).strip(),
        "student_mother":      str(student["mother"]).strip(),
        "student_gender":      str(student["gender"]).strip().upper(),
        "student_dob":         str(student["dob"]).strip(),
        "student_address":     str(student["address"]).strip(),
        "pin_code":            int(student["pincode"]),
        "mobile":              str(student["mobile"]).strip(),

        # Fixed defaults
        "whose_mobile":        1,
        "ip_address":          "NA",
        "birth_place":         0,
        "birth_place_name":    "",
        "birth_weight":        0,
        "student_class":       0,
        "student_section":     0,
        "student_roll_number": "",
        "student_blood_group": "",
        "student_remarks":     "",
        "apaar_id":            None,
        "abha_detail":         None,
        "pen_id":              "",
    }

    try:
        response = session.post(SAVE_URL, json=payload, verify=False, timeout=15)

        if response.status_code == 401:
            return {"success": False, "message": "Token expired. Please refresh."}
        if response.status_code != 200:
            return {"success": False, "message": f"HTTP {response.status_code}: {response.text}"}

        result = {k.lower(): v for k, v in response.json().items()}

        # Note: 'succecced' is a typo in the portal's own API response
        if result.get("succecced") is True:
            return {"success": True, "message": "Added successfully"}
        else:
            msg = result.get("message", "Server rejected the record.")
            return {"success": False, "message": msg}

    except requests.RequestException as e:
        return {"success": False, "message": f"Network error: {e}"}
    except ValueError:
        return {"success": False, "message": "Could not read server response."}


# upload_all_students has been removed from this file.
# The upload loop now lives in routes/upload_routes.py (_do_upload function)
# where it can update live progress via job_store between each student.
