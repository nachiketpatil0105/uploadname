"""
routes/session_routes.py — Step 1: Collect token, IDs, and institution selection.

Handles:
  GET  /               -> Show the home/setup page
  POST /verify-team    -> Verify team ID + login ID match (called by JavaScript)
  POST /start          -> Save token + institution to job_store, verify token works
  GET  /api/institutions -> Return AWC or school list as JSON (for dropdowns)
  GET  /new-upload     -> Start a new CSV upload without re-entering credentials
"""

from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for
from institutions import get_awc_list, get_school_list
from portal_api import create_session, set_institution_context
from config import HEALTH_BLOCK_CODE, TEAM_CONFIG
import job_store
import hashlib

session_bp = Blueprint("session_bp", __name__)


@session_bp.route("/")
def index():
    """Home page — Step 1: Verify team, then enter token and select institution."""
    return render_template("step1_setup.html",
                           health_block_code=HEALTH_BLOCK_CODE)


@session_bp.route("/verify-team", methods=["POST"])
def verify_team():
    """
    Called by JavaScript when user clicks Verify.
    Checks that the team_id exists and the login_id matches its stored hash.
    Returns JSON with the institution lists for that team's dropdowns.
    """
    team_id  = request.json.get("team_id", "").strip()
    login_id = request.json.get("login_id", "").strip()

    team = TEAM_CONFIG.get(team_id)
    if not team:
        return jsonify({"success": False, "message": "Unknown Team ID."})

    entered_hash = hashlib.sha256(login_id.encode()).hexdigest()
    if entered_hash != team["login_id_hash"]:
        return jsonify({"success": False, "message": "Login ID does not match this Team ID."})

    suffix      = team["suffix"]
    awc_list    = get_awc_list(suffix)
    school_list = get_school_list(suffix)
    return jsonify({"success": True, "suffix": suffix,
                    "awc_list": awc_list, "school_list": school_list})


@session_bp.route("/start", methods=["POST"])
def start():
    """
    Receive the full form (token + institution), verify the token works
    against the portal, then save everything to job_store (server-side).

    NOTE: team_id and login_id arrive as hidden fields — they were already
    verified by /verify-team before the form was shown to the user.
    """
    team_id           = request.form.get("team_id", "").strip()
    token             = request.form.get("token", "").strip()
    login_id          = request.form.get("login_id", "").strip()
    institution_type  = request.form.get("institution_type", "").strip()
    institution_code  = request.form.get("institution_code", "").strip()
    institution_name  = request.form.get("institution_name", "").strip()
    hb_code           = HEALTH_BLOCK_CODE   # fixed — not taken from form

    # Basic validation
    errors = []
    if not token:            errors.append("Access Token is required.")
    if not login_id:         errors.append("Login ID is required.")
    if not institution_code: errors.append("Please select an institution.")
    if not team_id or team_id not in TEAM_CONFIG:
        errors.append("Invalid Team ID. Please go back and verify again.")

    if errors:
        return render_template("step1_setup.html",
                               health_block_code=hb_code,
                               errors=errors)

    # Verify token works against the portal
    inst_type    = int(institution_type)
    inst_code    = int(institution_code)
    http_session = create_session(token)
    result       = set_institution_context(http_session, inst_type, inst_code, hb_code)

    if not result["success"]:
        return render_template("step1_setup.html",
                               health_block_code=hb_code,
                               errors=[result["message"]])

    # Save all credentials in job_store (server memory), NOT the cookie.
    # Flask cookies have a 4KB limit — long access tokens get silently truncated.
    job_id = session.get("job_id")
    if not job_id or not job_store.get_job(job_id):
        job_id = job_store.new_job()
        session["job_id"] = job_id

    suffix = TEAM_CONFIG[team_id]["suffix"]
    job_store.set_config(
        job_id,
        token             = token,
        health_block_code = hb_code,
        login_id          = int(login_id),
        institution_type  = inst_type,
        institution_code  = inst_code,
        team_id           = team_id,
        suffix            = suffix,
        institution_name  = institution_name,
    )

    return redirect(url_for("csv_bp.upload_csv"))


@session_bp.route("/api/institutions")
def api_institutions():
    """
    Returns the institution list as JSON based on type parameter.
    Used by JavaScript to update the institution dropdown dynamically.
    Reads the team suffix from the active job so it returns the right team's list.
    Example: /api/institutions?type=1  -> AWC list for this team
    """
    inst_type = request.args.get("type", "1")
    job_id    = session.get("job_id")
    config    = job_store.get_config(job_id) if job_id else None
    suffix    = config["suffix"] if config else "k"

    if inst_type == "2":
        data = get_school_list(suffix)
    else:
        data = get_awc_list(suffix)

    return jsonify(data)


@session_bp.route("/new-upload")
def new_upload():
    """
    Clear the current job and session completely,
    then redirect to the home page for fresh login.
    """
    old_job_id = session.get("job_id")
    if old_job_id:
        job_store.delete_job(old_job_id)
    session.clear()
    return redirect(url_for("session_bp.index"))
