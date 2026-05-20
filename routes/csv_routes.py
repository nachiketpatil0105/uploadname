"""
routes/csv_routes.py — Step 2: Upload, preview, and clean the student CSV.

Handles:
  GET  /upload        → Show CSV upload page
  POST /upload        → Receive CSV file, show preview
  POST /clean         → Run the cleaner, show results
  POST /confirm-clean → Store cleaned data, go to Step 3
  GET  /sample        → Download the sample CSV file
  GET  /download-problems → Download problem rows as CSV

NOTE ON STORAGE:
  CSV row data is stored in job_store (server-side memory), NOT in the Flask
  session cookie. The cookie only holds a short job_id string. This avoids
  the 4KB cookie limit which would silently lose data for larger CSV files.
"""

import csv
import io
from flask import (Blueprint, render_template, request,
                   session, redirect, url_for, send_file, Response)
from csv_cleaner import check_and_clean, check_columns
from config import REQUIRED_CSV_COLUMNS
import job_store

csv_bp = Blueprint("csv_bp", __name__)


def _require_session():
    """Redirect to setup if the user hasn't completed Step 1 yet."""
    job_id = session.get("job_id")
    if not job_id or not job_store.get_config(job_id):
        return redirect(url_for("session_bp.index"))
    return None


def _get_or_create_job_id() -> str:
    """
    Get the job_id from the Flask session, or create a new one.
    The job_id is just a short reference — actual data lives in job_store.
    """
    job_id = session.get("job_id")
    if not job_id or not job_store.get_job(job_id):
        job_id = job_store.new_job()
        session["job_id"] = job_id
    return job_id


@csv_bp.route("/upload", methods=["GET"])
def upload_csv():
    """Step 2a: Show the CSV upload form."""
    guard = _require_session()
    if guard: return guard
    return render_template("step2_upload.html",
                           required_columns=REQUIRED_CSV_COLUMNS)


@csv_bp.route("/upload", methods=["POST"])
def preview_csv():
    """
    Step 2b: Receive the uploaded CSV file.
    Parse it and show a preview table so the user can check it looks right.
    """
    guard = _require_session()
    if guard: return guard

    file = request.files.get("csv_file")
    if not file or file.filename == "":
        return render_template("step2_upload.html",
                               required_columns=REQUIRED_CSV_COLUMNS,
                               error="Please choose a CSV file to upload.")

    try:
        content = file.read().decode("utf-8")
        reader  = csv.DictReader(io.StringIO(content))
        rows    = list(reader)
        headers = reader.fieldnames or []
    except Exception as e:
        return render_template("step2_upload.html",
                               required_columns=REQUIRED_CSV_COLUMNS,
                               error=f"Could not read the file: {e}")

    # Check for missing columns before showing preview
    missing = check_columns(headers)
    if missing:
        return render_template("step2_upload.html",
                               required_columns=REQUIRED_CSV_COLUMNS,
                               error=f"Your CSV is missing these columns: {', '.join(missing)}")

    # Store raw rows in job_store (server-side), not in the cookie
    job_id = _get_or_create_job_id()
    job_store.set_raw_rows(job_id, rows)

    return render_template("step2_preview.html",
                           headers=headers,
                           rows=rows,
                           total=len(rows))


@csv_bp.route("/clean", methods=["POST"])
def clean_csv():
    """
    Step 2c: Run the cleaner on the uploaded rows.
    Show which rows are fine and which have problems.
    """
    guard = _require_session()
    if guard: return guard

    job_id = session.get("job_id")
    job    = job_store.get_job(job_id) if job_id else None
    if not job or not job["raw_rows"]:
        return redirect(url_for("csv_bp.upload_csv"))

    result = check_and_clean(job["raw_rows"])

    # Store the cleaned results so /confirm-clean can read them directly
    # (avoids re-running check_and_clean a second time with possible ordering differences)
    job_store.set_cleaned_rows(job_id, result["cleaned"])
    job_store.set_needs_weight_rows(job_id, result["needs_weight"])

    return render_template("step2_clean.html",
                           cleaned=result["cleaned"],
                           needs_weight=result["needs_weight"],
                           problems=result["problems"],
                           ready=result["ready"],
                           total_raw=len(job["raw_rows"]),
                           total_clean=len(result["cleaned"]),
                           total_needs_weight=len(result["needs_weight"]),
                           total_problems=len(result["problems"]))


@csv_bp.route("/confirm-clean", methods=["POST"])
def confirm_clean():
    """
    Step 2d: User confirms they want to proceed with the cleaned rows.
    Reads already-cleaned rows from job_store, attaches birth weights for
    under-1 children, then moves to Step 3 (upload confirmation).
    """
    guard = _require_session()
    if guard: return guard

    job_id = session.get("job_id")
    job    = job_store.get_job(job_id) if job_id else None
    if not job or not job["raw_rows"]:
        return redirect(url_for("csv_bp.upload_csv"))

    # Read the already-cleaned rows stored during /clean — do NOT re-run
    # check_and_clean, because that could produce rows in a different order
    # and misalign the weight_N form inputs with the wrong children.
    needs_weight = job.get("needs_weight_rows", [])
    for i, row in enumerate(needs_weight):
        row["birth_weight"] = int(request.form.get(f"weight_{i}", 0) or 0)

    job_store.set_needs_weight_rows(job_id, needs_weight)

    return redirect(url_for("upload_bp.confirm_upload"))


@csv_bp.route("/sample")
def download_sample():
    """Serve the sample CSV file so new users can see the required format."""
    return send_file("sample_students.csv",
                     mimetype="text/csv",
                     as_attachment=True,
                     download_name="sample_students.csv")


@csv_bp.route("/download-problems")
def download_problems():
    """
    Download the problem rows from the last clean run as a CSV.
    Lets users fix errors in their spreadsheet without manually hunting for rows.
    """
    guard = _require_session()
    if guard: return guard

    job_id = session.get("job_id")
    job    = job_store.get_job(job_id) if job_id else None
    if not job or not job["raw_rows"]:
        return redirect(url_for("csv_bp.upload_csv"))

    result = check_and_clean(job["raw_rows"])
    problems = result["problems"]

    # Build a CSV with row number, name, and errors
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["CSV Row", "Student Name", "Errors"])
    for p in problems:
        writer.writerow([p["row"], p["name"], "; ".join(p["errors"])])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=problems.csv"}
    )
