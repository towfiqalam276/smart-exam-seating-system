# Examly — Smart Exam Hall Seating System

A Flask + SQLite application for managing students, exam halls and generated seating allocations.

## Features in this version
- Premium responsive SaaS-style admin dashboard.
- Overview cards for students, halls, capacity, allocated seats and utilization.
- Student and hall create, edit and delete operations.
- Instant student search and allocation search.
- Subject distribution and seat utilization charts (Chart.js CDN).
- Hall capacity overview and visual numbered seat grid.
- Generate and reset seating allocations.
- Export seating plan as CSV and print the plan from the browser.
- SQLite database is initialized automatically.

## Technology
- Python 3.10+
- Flask
- SQLite
- HTML, CSS and JavaScript
- Chart.js and Lucide icons (loaded from CDN)

## Run locally
```bash
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Deploy on Render
Create a Web Service connected to your GitHub repository.
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Add environment variable `SECRET_KEY` with a long random value.
- For persistent SQLite data, attach a Render persistent disk and set `DATABASE_PATH` to a file inside the mounted disk, for example `/var/data/exam_seating.db`.

If you do not configure a persistent disk, SQLite data stored on the instance filesystem may be lost when the service is redeployed or its instance is replaced.

## Optimization method and limitations
The seating generator uses a lightweight subject-interleaving heuristic: students are grouped by subject, sorted by student ID, and selected in round-robin order before being assigned to seats in hall order. It is an AI-inspired optimization heuristic, not a trained machine-learning model.

The visual seat map displays the generated seat numbers in a grid for readability. The current database stores a linear seat number, not physical row/column coordinates. Exam dates, invigilator assignment, authentication, role management and true physical hall layouts are not included in this version.

## Security notes
Set a strong `SECRET_KEY` in Render. Add authentication and CSRF protection before using this application with real institutional student data. Do not commit secrets or private student data to GitHub.
