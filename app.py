"""
app.py — Main entry point for the RBSK Student Uploader web app.

Run this file to start the local web server:
    python app.py

Then open your browser at:
    http://localhost:5000
"""

from flask import Flask
from routes.session_routes import session_bp
from routes.csv_routes import csv_bp
from routes.upload_routes import upload_bp

app = Flask(__name__)
app.secret_key = "rbsk-local-secret-2024"  # Used for flash messages

# ---------------------------------------------------------------------------
# Register route blueprints (each file handles one section of the app)
# ---------------------------------------------------------------------------
app.register_blueprint(session_bp)   # Step 1: Token + institution setup
app.register_blueprint(csv_bp)       # Step 2: CSV upload, preview, cleaning
app.register_blueprint(upload_bp)    # Step 3: Upload students to portal

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  RBSK Student Uploader is running!")
    print("  Open your browser and go to:")
    print("  http://localhost:5000")
    print("="*50 + "\n")
    # threaded=True is REQUIRED — without it, the progress polling requests
    # would be blocked while the upload thread is running (single-threaded server).
    app.run(debug=True, port=5000, threaded=True)
