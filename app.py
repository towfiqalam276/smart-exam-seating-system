import csv
import io
import os
import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from optimizer import optimize_seating

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "exam_seating.db"))

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-before-production")


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            subject TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS halls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            capacity INTEGER NOT NULL CHECK(capacity > 0)
        );
        CREATE TABLE IF NOT EXISTS allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            hall_id INTEGER NOT NULL REFERENCES halls(id) ON DELETE CASCADE,
            seat_no INTEGER NOT NULL,
            UNIQUE(student_id),
            UNIQUE(hall_id, seat_no)
        );
        """)


@app.context_processor
def inject_globals():
    return {"app_name": "Examly", "current_year": 2026}


@app.route("/")
def index():
    with get_db() as db:
        students = db.execute("SELECT * FROM students ORDER BY student_no").fetchall()
        halls = db.execute("SELECT * FROM halls ORDER BY name").fetchall()
        allocation_count = db.execute("SELECT COUNT(*) FROM allocations").fetchone()[0]
        subject_rows = db.execute(
            "SELECT subject, COUNT(*) AS total FROM students GROUP BY subject ORDER BY total DESC, subject"
        ).fetchall()
        hall_rows = db.execute("""
            SELECT h.id, h.name, h.capacity, COUNT(a.id) AS occupied
            FROM halls h LEFT JOIN allocations a ON a.hall_id = h.id
            GROUP BY h.id ORDER BY h.name
        """).fetchall()
        recent = db.execute("""
            SELECT s.student_no, s.name, s.subject, h.name AS hall_name, a.seat_no
            FROM allocations a JOIN students s ON s.id=a.student_id
            JOIN halls h ON h.id=a.hall_id
            ORDER BY a.id DESC LIMIT 6
        """).fetchall()

    total_capacity = sum(h["capacity"] for h in halls)
    available_seats = max(total_capacity - allocation_count, 0)
    utilization = round((allocation_count / total_capacity) * 100) if total_capacity else 0
    return render_template(
        "index.html", students=students, halls=halls,
        allocation_count=allocation_count, total_capacity=total_capacity,
        available_seats=available_seats, utilization=utilization,
        subject_labels=[r["subject"] for r in subject_rows],
        subject_values=[r["total"] for r in subject_rows],
        hall_labels=[r["name"] for r in hall_rows],
        hall_capacities=[r["capacity"] for r in hall_rows],
        hall_occupied=[r["occupied"] for r in hall_rows],
        recent=recent
    )


@app.route("/students/add", methods=["POST"])
def add_student():
    values = [request.form.get(k, "").strip() for k in ("student_no", "name", "subject")]
    if not all(values):
        flash("Please complete all student fields.", "error")
    else:
        try:
            with get_db() as db:
                db.execute("INSERT INTO students(student_no, name, subject) VALUES (?, ?, ?)", values)
                db.execute("DELETE FROM allocations")
            flash("Student added. Regenerate the seating plan to refresh allocations.", "success")
        except sqlite3.IntegrityError:
            flash("This Student ID already exists.", "error")
    return redirect(url_for("index") + "#students")


@app.route("/students/<int:student_id>/edit", methods=["POST"])
def edit_student(student_id):
    values = [request.form.get(k, "").strip() for k in ("student_no", "name", "subject")]
    if not all(values):
        flash("Please complete all student fields.", "error")
    else:
        try:
            with get_db() as db:
                db.execute("UPDATE students SET student_no=?, name=?, subject=? WHERE id=?", (*values, student_id))
                db.execute("DELETE FROM allocations")
            flash("Student updated. Regenerate the seating plan to refresh allocations.", "success")
        except sqlite3.IntegrityError:
            flash("That Student ID is already in use.", "error")
    return redirect(url_for("index") + "#students")


@app.route("/students/<int:student_id>/delete", methods=["POST"])
def delete_student(student_id):
    with get_db() as db:
        db.execute("DELETE FROM allocations")
        db.execute("DELETE FROM students WHERE id = ?", (student_id,))
    flash("Student deleted.", "success")
    return redirect(url_for("index") + "#students")


@app.route("/halls/add", methods=["POST"])
def add_hall():
    name = request.form.get("name", "").strip()
    try:
        capacity = int(request.form.get("capacity", "0"))
    except ValueError:
        capacity = 0
    if not name or capacity <= 0:
        flash("Enter a hall name and a positive seat capacity.", "error")
    else:
        try:
            with get_db() as db:
                db.execute("INSERT INTO halls(name, capacity) VALUES (?, ?)", (name, capacity))
                db.execute("DELETE FROM allocations")
            flash("Hall added. Regenerate the seating plan to refresh allocations.", "success")
        except sqlite3.IntegrityError:
            flash("A hall with this name already exists.", "error")
    return redirect(url_for("index") + "#halls")


@app.route("/halls/<int:hall_id>/edit", methods=["POST"])
def edit_hall(hall_id):
    name = request.form.get("name", "").strip()
    try:
        capacity = int(request.form.get("capacity", "0"))
    except ValueError:
        capacity = 0
    if not name or capacity <= 0:
        flash("Enter a hall name and a positive seat capacity.", "error")
    else:
        try:
            with get_db() as db:
                db.execute("UPDATE halls SET name=?, capacity=? WHERE id=?", (name, capacity, hall_id))
                db.execute("DELETE FROM allocations")
            flash("Hall updated. Regenerate the seating plan to refresh allocations.", "success")
        except sqlite3.IntegrityError:
            flash("That hall name is already in use.", "error")
    return redirect(url_for("index") + "#halls")


@app.route("/halls/<int:hall_id>/delete", methods=["POST"])
def delete_hall(hall_id):
    with get_db() as db:
        db.execute("DELETE FROM allocations")
        db.execute("DELETE FROM halls WHERE id = ?", (hall_id,))
    flash("Hall deleted.", "success")
    return redirect(url_for("index") + "#halls")


@app.route("/generate", methods=["POST"])
def generate():
    with get_db() as db:
        students = db.execute("SELECT * FROM students ORDER BY student_no").fetchall()
        halls = db.execute("SELECT * FROM halls ORDER BY name").fetchall()
        if not students:
            flash("Add students before generating a seating plan.", "error")
            return redirect(url_for("index"))
        if not halls:
            flash("Add at least one exam hall.", "error")
            return redirect(url_for("index"))
        total_capacity = sum(h["capacity"] for h in halls)
        if len(students) > total_capacity:
            flash(f"Not enough seats. {len(students)} students need seats, but capacity is {total_capacity}.", "error")
            return redirect(url_for("index"))
        assignments = optimize_seating([dict(s) for s in students], [dict(h) for h in halls])
        db.execute("DELETE FROM allocations")
        for item in assignments:
            db.execute(
                "INSERT INTO allocations(student_id, hall_id, seat_no) VALUES (?, ?, ?)",
                (item["student_id"], item["hall_id"], item["seat_no"])
            )
    flash("Seating plan generated successfully.", "success")
    return redirect(url_for("results"))


@app.route("/results")
def results():
    with get_db() as db:
        halls = db.execute("""
            SELECT h.id, h.name, h.capacity, COUNT(a.id) AS occupied
            FROM halls h LEFT JOIN allocations a ON a.hall_id=h.id
            GROUP BY h.id ORDER BY h.name
        """).fetchall()
        rows = db.execute("""
            SELECT s.student_no, s.name, s.subject, h.name AS hall_name,
                   h.id AS hall_id, a.seat_no
            FROM allocations a JOIN students s ON s.id=a.student_id
            JOIN halls h ON h.id=a.hall_id
            ORDER BY h.name, a.seat_no
        """).fetchall()
    by_hall = {}
    for row in rows:
        by_hall.setdefault(row["hall_id"], []).append(row)
    return render_template("results.html", rows=rows, halls=halls, by_hall=by_hall)


@app.route("/reports/seating.csv")
def export_csv():
    with get_db() as db:
        rows = db.execute("""
            SELECT h.name, a.seat_no, s.student_no, s.name, s.subject
            FROM allocations a JOIN students s ON s.id=a.student_id
            JOIN halls h ON h.id=a.hall_id ORDER BY h.name, a.seat_no
        """).fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Exam Hall", "Seat Number", "Student ID", "Student Name", "Subject"])
    writer.writerows([tuple(row) for row in rows])
    response = make_response("\\ufeff" + output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=exam-seating-plan.csv"
    return response


@app.route("/reset", methods=["POST"])
def reset_allocations():
    with get_db() as db:
        db.execute("DELETE FROM allocations")
    flash("Seating allocations have been reset.", "success")
    return redirect(url_for("index"))


@app.get("/health")
def health():
    return {"status": "ok"}


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
