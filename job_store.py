"""
job_store.py — Server-side in-memory storage.

WHY THIS EXISTS:
  Flask sessions are stored in a browser cookie which has a hard 4KB limit.
  Even 10-15 students will overflow it silently, causing data loss.

  This module stores data on the SERVER (in Python memory) instead,
  so there is no size limit.

HOW IT WORKS:
  Every browser gets a unique job_id (stored in their cookie — just a short ID,
  not the actual data). The actual data lives in the JOBS dict below.

CLEANUP:
  Jobs older than 2 hours are purged automatically on each new_job() call
  to prevent unbounded memory growth during long server sessions.
"""

import uuid
import time
import threading

# ── In-memory store — one entry per active browser session ──
# Structure:  JOBS[job_id] = { "raw_rows": [...], "cleaned_rows": [...], ... }
JOBS: dict = {}

# Lock to prevent race conditions when two threads write at the same time
_lock = threading.Lock()

# Jobs older than this many seconds will be purged
_JOB_TTL_SECONDS = 7200  # 2 hours


def _purge_old_jobs():
    """Remove jobs that are older than _JOB_TTL_SECONDS. Called on new_job()."""
    cutoff = time.time() - _JOB_TTL_SECONDS
    to_delete = [jid for jid, j in JOBS.items() if j.get("created_at", 0) < cutoff]
    for jid in to_delete:
        JOBS.pop(jid, None)


def new_job() -> str:
    """Create a new job entry and return its unique ID."""
    job_id = str(uuid.uuid4())
    with _lock:
        _purge_old_jobs()
        JOBS[job_id] = {
            "raw_rows":          [],
            "cleaned_rows":      [],
            "needs_weight_rows": [],
            "config":            None,
            "progress":          {
                "done": 0, "total": 0,
                "running": False, "finished": False,
                "successful_count": 0, "failed_count": 0,
            },
            "results":           {"successful": [], "failed": []},
            "created_at":        time.time(),
        }
    return job_id


def get_job(job_id: str) -> dict | None:
    """Return the job dict for the given ID, or None if not found."""
    return JOBS.get(job_id)


def set_raw_rows(job_id: str, rows: list):
    with _lock:
        if job_id in JOBS:
            JOBS[job_id]["raw_rows"] = rows


def set_cleaned_rows(job_id: str, rows: list):
    with _lock:
        if job_id in JOBS:
            JOBS[job_id]["cleaned_rows"] = rows


def set_needs_weight_rows(job_id: str, rows: list):
    with _lock:
        if job_id in JOBS:
            JOBS[job_id]["needs_weight_rows"] = rows


def update_progress(job_id: str, done: int, total: int,
                    finished: bool = False,
                    successful_count: int = 0,
                    failed_count: int = 0):
    with _lock:
        if job_id in JOBS:
            JOBS[job_id]["progress"] = {
                "done":             done,
                "total":            total,
                "running":          not finished,
                "finished":         finished,
                "successful_count": successful_count,
                "failed_count":     failed_count,
            }


def set_results(job_id: str, successful: list, failed: list):
    with _lock:
        if job_id in JOBS:
            JOBS[job_id]["results"] = {"successful": successful, "failed": failed}


def set_config(job_id: str, token: str, health_block_code: int,
               login_id: int, institution_type: int, institution_code: int,
               team_id: str, suffix: str, institution_name: str = ""):
    """
    Store the portal credentials and institution settings in the job.
    This avoids putting them in the Flask cookie, which has a 4KB limit
    that silently truncates long access tokens.
    """
    with _lock:
        if job_id in JOBS:
            JOBS[job_id]["config"] = {
                "token":             token,
                "health_block_code": health_block_code,
                "login_id":          login_id,
                "institution_type":  institution_type,
                "institution_code":  institution_code,
                "team_id":           team_id,
                "suffix":            suffix,
                "institution_name":  institution_name,
            }


def get_config(job_id: str) -> dict | None:
    """Return the stored config dict for a job, or None if not found."""
    job = JOBS.get(job_id)
    if job is None:
        return None
    return job.get("config")


def delete_job(job_id: str):
    """Clean up a job after the user is done."""
    with _lock:
        JOBS.pop(job_id, None)
