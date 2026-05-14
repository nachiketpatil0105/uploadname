"""
routes/session_routes.py — Step 1: Collect token, IDs, and institution selection.

Handles:
  GET  /          → Show the home/setup page
  POST /start     → Save token + IDs to session, set portal context
  GET  /api/institutions  → Return AWC or school list as JSON (for dropdowns)
"""

from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for
from institutions import get_awc_list, get_school_list
from portal_api import create_session, set_institution_context
from config import INSTITUTION_TYPE_AWC, INSTITUTION_TYPE_SCHOOL, HEALTH_BLOCK_CODE
import job_store

session_bp = Blueprint("session_bp", __name__)


@session_bp.route("/")
def index():
    """Home page — Step 1: Enter token, IDs, and choose institution."""
    return render_template("step1_setup.html",
                           awc_list=get_awc_list(),
                           school_list=get_school_list(),
                           health_block_code=HEALTH_BLOCK_CODE)


@session_bp.route("/start", methods=["POST"])
def start():
    """
    Save user inputs to the Flask session and verify the token
    by calling the portal's context endpoint.
    """
    token             = request.form.get("token", "").strip()
    health_block_code = HEALTH_BLOCK_CODE          # fixed — not taken from form
    login_id          = request.form.get("login_id", "").strip()
    institution_type  = request.form.get("institution_type", "").strip()
    institution_code  = request.form.get("institution_code", "").strip()

    # --- Basic validation ---
    errors = []
    if not token:            errors.append("Access Token is required.")
    if not login_id:         errors.append("Login ID is required.")
    if not institution_code: errors.append("Please select an institution.")

    if errors:
        return render_template("step1_setup.html",
                               awc_list=get_awc_list(),
                               school_list=get_school_list(),
                               health_block_code=HEALTH_BLOCK_CODE,
                               errors=errors,
                               form=request.form)

    # --- Try connecting to the portal ---
    inst_type = int(institution_type)
    inst_code = int(institution_code)
    hb_code   = HEALTH_BLOCK_CODE

    http_session = create_session(token)
    result = set_institution_context(http_session, inst_type, inst_code, hb_code)

    if not result["success"]:
        return render_template("step1_setup.html",
                               awc_list=get_awc_list(),
                               school_list=get_school_list(),
                               health_block_code=HEALTH_BLOCK_CODE,
                               errors=[result["message"]],
                               form=request.form)

    # --- Save credentials + settings in job_store (server memory), NOT the cookie ---
    # Flask cookies have a hard 4KB limit — long access tokens are silently truncated.
    # We store the full token server-side and only keep a short job_id in the cookie.
    job_id = session.get("job_id")
    if not job_id or not job_store.get_job(job_id):
        job_id = job_store.new_job()
        session["job_id"] = job_id

    job_store.set_config(
        job_id,
        token             = token,
        health_block_code = hb_code,
        login_id          = int(login_id),
        institution_type  = inst_type,
        institution_code  = inst_code,
    )
    print(f"[DEBUG] Config saved for job_id={job_id}, config={job_store.get_config(job_id)}")

    return redirect(url_for("csv_bp.upload_csv"))


@session_bp.route("/api/institutions")
def api_institutions():
    """
    Returns the institution list as JSON based on type parameter.
    Used by JavaScript to update the dropdown dynamically.
    Example: /api/institutions?type=1  → AWC list
    """
    inst_type = request.args.get("type", "1")
    if inst_type == "2":
        data = get_school_list()
    else:
        data = get_awc_list()
    return jsonify(data)


@session_bp.route("/new-upload")
def new_upload():
    """
    Clear the current job from server memory and start fresh.
    Keeps the token + institution settings so the user doesn't have to re-enter them.
    """
    old_job_id = session.pop("job_id", None)
    if old_job_id:
        job_store.delete_job(old_job_id)
    return redirect(url_for("csv_bp.upload_csv"))
