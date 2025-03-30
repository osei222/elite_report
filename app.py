from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Ensure session works correctly
app.config['SESSION_TYPE'] = 'filesystem'

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///students.db")
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    grade = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.String(50), nullable=False)
    total_aggregate = db.Column(db.Float, nullable=False)
    remarks = db.Column(db.String(255), nullable=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        school_name = request.form.get("school_name")
        location = request.form.get("location")
        semester = request.form.get("semester")
        closing_date = request.form.get("closing_date")
        opening_date = request.form.get("opening_date")
        grade = request.form.get("grade")
        num_students = request.form.get("num_students")

        if not school_name or not num_students:
            flash("All fields are required!", "danger")
            return redirect(url_for('index'))

        session["school_details"] = {
            "school_name": school_name,
            "location": location,
            "semester": semester,
            "closing_date": closing_date,
            "opening_date": opening_date,
            "grade": grade,
            "num_students": int(num_students)
        }

        # ✅ Ensure students list is initialized
        session["students"] = [{}] * int(num_students)

        print("✅ Redirecting to student details page...")  # Debugging log
        return redirect(url_for('student', student_index=0))

    return render_template('index.html')

@app.route('/student/<int:student_index>', methods=['GET', 'POST'])
def student(student_index):
    if "school_details" not in session:
        flash("Please fill in the school details first.", "warning")
        return redirect(url_for('index'))

    total_students = session["school_details"]["num_students"]

    if student_index >= total_students:
        return redirect(url_for('preview'))

    if request.method == 'POST':
        name = request.form.get("name")
        if not name:
            flash("Student name is required!", "danger")
            return redirect(url_for('student', student_index=student_index))

        session["students"][student_index] = {"name": name}
        if student_index + 1 < total_students:
            return redirect(url_for('student', student_index=student_index + 1))
        else:
            return redirect(url_for('preview'))

    return render_template('student_details.html', student_index=student_index, total_students=total_students)

@app.route('/preview')
def preview():
    if "students" not in session:
        return redirect(url_for('index'))
    return render_template('preview.html', students=session["students"], school_details=session["school_details"])

if __name__ == '__main__':
    app.run(debug=True)
