# RBSK Student Uploader — Web App

A simple local web app to upload student records to the RBSK portal
from a CSV file. No technical knowledge needed to use it.

---

## Folder Structure

```
rbsk_uploader/
│
├── app.py               ← Start the web app (run this)
├── config.py            ← All fixed settings (domain, state code, etc.)
├── institutions.py      ← Loads AWC and school lists from CSV
├── csv_cleaner.py       ← Validates and cleans student CSV data
├── portal_api.py        ← All HTTP calls to the RBSK portal
├── requirements.txt     ← Python packages needed
│
├── routes/
│   ├── session_routes.py  ← Step 1: Token + institution setup
│   ├── csv_routes.py      ← Step 2: CSV upload, preview, cleaning
│   └── upload_routes.py   ← Step 3: Confirm and run upload
│
├── templates/
│   ├── base.html          ← Shared layout (header, steps bar)
│   ├── step1_setup.html   ← Token + institution form
│   ├── step2_upload.html  ← CSV upload form
│   ├── step2_preview.html ← Raw CSV preview table
│   ├── step2_clean.html   ← Cleaned CSV + problem report
│   ├── step3_confirm.html ← Final confirmation before upload
│   └── step4_results.html ← Upload results (success + failures)
│
└── data/
    ├── awc.csv            ← List of all AWC institutions
    └── school.csv         ← List of all schools
```

---

## Setup (One Time)

1. Make sure Python 3.10+ is installed.

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Update `data/awc.csv` and `data/school.csv` with your full institution lists.

---

## How to Run

```
python app.py
```

Then open your browser and go to: **http://localhost:5000**

---

## How to Use (Step by Step)

### Step 1 — Connect to Portal
- Log in to the RBSK portal in your browser
- Press **F12** → Network tab → Fetch/XHR → find **AuthenticateUser**
- Copy the `loginID` and `healthBlockID` from the Response
- Copy the `accessToken` from the Request cookies
- Paste them into the form and select your institution

### Step 2 — Upload CSV
Prepare a CSV file with these exact column names:

| Column   | Description              | Example           |
|----------|--------------------------|-------------------|
| name     | Student full name        | Ravi Kumar        |
| father   | Father's name            | Suresh Kumar      |
| mother   | Mother's name            | Sunita Kumar      |
| gender   | M or F only              | M                 |
| dob      | Date of birth YYYY-MM-DD | 2010-05-15        |
| address  | Full address             | Village XYZ       |
| pincode  | 6-digit pin code         | 422001            |
| mobile   | 10-digit mobile number   | 9876543210        |

### Step 3 — Review & Clean
- The app will show a preview of your CSV
- It will automatically check for errors (wrong gender format, bad date, etc.)
- Students with errors are shown separately and will be skipped
- Fix errors in your CSV and re-upload if needed

### Step 4 — Confirm
- Review the final list of clean students
- Click **Add All Students** to begin uploading

### Step 5 — Results
- See which students were added successfully and which failed
- Failed students show the reason (e.g. token expired, duplicate)

---

## Troubleshooting

| Problem                     | Solution                                              |
|-----------------------------|-------------------------------------------------------|
| "Token expired" error        | Copy a fresh token from your browser and start again  |
| CSV columns not recognised   | Make sure column names are exactly as listed above    |
| App won't start              | Run `pip install -r requirements.txt` first           |
| Can't reach the portal       | Check your internet connection                        |
