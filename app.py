from flask import Flask, render_template, request, session, redirect, url_for, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("⚠️ DATABASE_URL environment variable not set!")

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


def calculate_grade(score):
    if score >= 80:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 50:
        return "D"
    else:
        return "E"


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session["school_details"] = {
            "school_name": request.form.get("school_name"),
            "location": request.form.get("location"),
            "address": request.form.get("address"),
            "grade": request.form.get("grade"),
            "semester": request.form.get("semester"),
            "closing_date": request.form.get("closing_date"),
            "opening_date": request.form.get("opening_date"),
            "num_students": int(request.form.get("num_students"))
        }
        session["students"] = [{} for _ in range(session["school_details"]["num_students"])]  # Initialize students
        return redirect(url_for('student', student_index=0))
    return render_template('index.html')


@app.route('/student/<int:student_index>', methods=['GET', 'POST'])
def student(student_index):
    total_students = session.get("school_details", {}).get("num_students", 0)
    subjects = ["Integrated Science", "Mathematics", "English Language", "Ghanaian Language",
                "Creative Art", "Religious and Moral Education", "History", "Computing",
                "OWOP", "Dictation"] if session["school_details"]["grade"] == "Grade 1-6" else \
        ["Integrated Science", "Mathematics", "English Language", "Ghanaian Language",
         "Creative Art", "Social Studies", "Computing", "Career Technology",
         "Religious and Moral Education", "Dictation"]

    if request.method == 'POST':
        name = request.form.get("name")
        class_scores = list(map(float, request.form.getlist("class_score[]")))
        exam_scores = list(map(float, request.form.getlist("exam_score[]")))
        remarks = request.form.getlist("remark[]")
        teacher_remarks = request.form.get("teacher_remarks")

        scores = []
        total_aggregate = 0
        for i in range(len(subjects)):
            total_score = class_scores[i] + exam_scores[i]
            total_aggregate += total_score
            scores.append({
                "subject": subjects[i],
                "class_score": class_scores[i],
                "exam_score": exam_scores[i],
                "total_score": total_score,
                "grade": calculate_grade(total_score),
                "remark": remarks[i]
            })

        session["students"][student_index] = {
            "name": name,
            "grade": session["school_details"]["grade"],
            "semester": session["school_details"]["semester"],
            "scores": scores,
            "total_aggregate": total_aggregate / len(subjects),
            "teacher_remarks": teacher_remarks
        }

        if student_index + 1 < total_students:
            return redirect(url_for('student', student_index=student_index + 1))
        else:
            return redirect(url_for('preview'))

    return render_template('student_details.html', student_index=student_index, total_students=total_students,
                           subjects=subjects)


@app.route('/preview')
def preview():
    students = session.get('students', [])
    school_details = session.get('school_details', {})
    return render_template('preview.html', students=students, school_details=school_details)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
