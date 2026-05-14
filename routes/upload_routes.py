"""
routes/upload_routes.py — Step 3: Confirm and run the student upload.

Handles:
  GET  /confirm        → Show list of students about to be uploaded
  POST /run            → Start upload in a BACKGROUND THREAD (returns immediately)
  GET  /progress       → Browser polls this every 2 sec to get live progress (JSON)
  GET  /results        → Show final results page once upload is done

WHY BACKGROUND THREAD:
  Flask's dev server is single-threaded. If /run does the upload directly,
  the server is completely frozen until all students are uploaded. The browser
  just sees a spinning tab with no feedback — looks like it crashed.

  Instead, /run starts a background thread and returns immediately.
  The browser polls /progress every 2 seconds and shows a live counter.
  When progress shows finished=True, the browser redirects to /results.
"""

import threading
from flask import (Blueprint, render_template, request,
                   session, redirect, url_for, jsonify)
from portal_api import create_session, upload_student
from config import REQUEST_DELAY_SECONDS
import job_store
import time

upload_bp = Blueprint("upload_bp", __name__)


# ── Guards ────────────────────────────────────────────────────────────────

def _require_session():
    job_id = session.get("job_id")
    config = job_store.get_config(job_id) if job_id else None
    if not job_id or config is None:
        print(f"[DEBUG] _require_session blocked: job_id={job_id}, config={config}")
        return redirect(url_for("session_bp.index"))
    return None

def _require_job():
    job_id = session.get("job_id")
    if not job_id or not job_store.get_job(job_id):
        return redirect(url_for("csv_bp.upload_csv"))
    return None

def _require_cleaned():
    job_id = session.get("job_id")
    job = job_store.get_job(job_id) if job_id else None
    if not job or not job.get("cleaned_rows"):
        return redirect(url_for("csv_bp.upload_csv"))
    return None


# ── Step 3a: Confirm page ─────────────────────────────────────────────────

@upload_bp.route("/confirm")
def confirm_upload():
    """Show the user a final list of students that will be uploaded."""
    guard = _require_session() or _require_cleaned()
    if guard: return guard

    job_id   = session["job_id"]
    students = job_store.get_job(job_id)["cleaned_rows"]
    return render_template("step3_confirm.html", students=students, total=len(students))


# ── Step 3b: Start upload (background thread) ─────────────────────────────

def _do_upload(job_id: str, token: str, institution_type: int,
               institution_code: int, health_block_code: int, login_id: int):
    """
    This function runs in a BACKGROUND THREAD.
    It uploads students one by one and updates the progress in job_store
    so the browser can poll for live updates.
    """
    job      = job_store.get_job(job_id)
    students = job["cleaned_rows"]
    total    = len(students)

    successful = []
    failed     = []

    # Build the authenticated HTTP session.
    # No separate "set context" call is needed — institution info is
    # embedded in every upload_student payload directly.
    http_session = create_session(token)

    # Upload each student, updating progress after each one
    for i, student in enumerate(students, start=1):
        result = upload_student(
            http_session, student,
            institution_type, institution_code,
            health_block_code, login_id
        )
        if result["success"]:
            successful.append({"name": student["name"], "message": result["message"]})
        else:
            failed.append({"name": student["name"], "message": result["message"]})

        # Update live progress counter.
        # Never mark finished=True here — results must be saved first.
        job_store.update_progress(job_id, done=i, total=total, finished=False)

        # Delay between requests to avoid firewall blocks
        time.sleep(REQUEST_DELAY_SECONDS)

    # Save results FIRST, then mark finished=True.
    # The browser redirects to /results the moment finished=True appears.
    # If we set finished before saving, the results page loads empty.
    job_store.set_results(job_id, successful, failed)
    job_store.update_progress(job_id, done=total, total=total, finished=True)

@upload_bp.route("/run", methods=["POST"])
def run_upload():
    """
    Start the upload in a background thread.
    Returns immediately — browser will poll /progress for updates.
    """
    guard = _require_session() or _require_cleaned()
    if guard: return guard

    job_id = session["job_id"]
    config = job_store.get_config(job_id)

    token             = config["token"]
    health_block_code = config["health_block_code"]
    login_id          = config["login_id"]
    institution_type  = config["institution_type"]
    institution_code  = config["institution_code"]

    job      = job_store.get_job(job_id)
    students = job["cleaned_rows"]

    # Reset progress for this run
    job_store.update_progress(job_id, done=0, total=len(students), finished=False)

    # Start upload in background — server is NOT blocked
    thread = threading.Thread(
        target=_do_upload,
        args=(job_id, token, institution_type, institution_code, health_block_code, login_id),
        daemon=True   # Thread will stop automatically if the app exits
    )
    thread.start()

    # Show the progress page immediately
    return render_template("step3_progress.html", total=len(students))


# ── Progress polling endpoint ─────────────────────────────────────────────

@upload_bp.route("/progress")
def get_progress():
    """
    The browser calls this endpoint every 2 seconds to get upload status.
    Returns JSON like: {"done": 5, "total": 20, "finished": false}
    """
    job_id = session.get("job_id")
    job    = job_store.get_job(job_id) if job_id else None
    if not job:
        return jsonify({"done": 0, "total": 0, "finished": True, "error": "Session lost"})

    return jsonify(job["progress"])


# ── Results page ──────────────────────────────────────────────────────────

@upload_bp.route("/results")
def show_results():
    """Show the final results once upload is complete."""
    guard = _require_session() or _require_job()
    if guard: return guard

    job_id  = session["job_id"]
    job     = job_store.get_job(job_id)
    results = job["results"]
    total   = len(job["cleaned_rows"])

    return render_template("step4_results.html",
                           successful=results["successful"],
                           failed=results["failed"],
                           total=total)

