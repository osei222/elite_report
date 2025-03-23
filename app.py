from flask import Flask, render_template, request, session, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session handling

# Securely Fetch Database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("⚠️ DATABASE_URL environment variable not set!")

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Define Database Models
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    grade = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.String(50), nullable=False)
    total_aggregate = db.Column(db.Float, nullable=False)


class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    class_score = db.Column(db.Float, nullable=False)
    exam_score = db.Column(db.Float, nullable=False)
    total_score = db.Column(db.Float, nullable=False)
    remark = db.Column(db.String(50), nullable=False)


# Create tables if they don't exist
with app.app_context():
    db.create_all()

# Predefined subjects per grade
grade_subjects = {
    "Grade 1-6": ["Integrated Science", "Mathematics", "English Language", "Ghanaian Language", "Creative Art",
                  "Religious and Moral Education", "History", "Computing", "OWOP", "Dictation"],
    "Grade 7-9": ["Integrated Science", "Mathematics", "English Language", "Ghanaian Language", "Creative Art",
                  "Social Studies", "Computing", "Career Technology", "Religious and Moral Education", "Dictation"]
}


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session['school_name'] = request.form['school_name']
        session['location'] = request.form['location']
        session['grade'] = request.form['grade']
        session['semester'] = request.form['semester']
        session['num_students'] = int(request.form['num_students'])
        session['students'] = []  # Initialize an empty list for student data
        return redirect(url_for('student_entry', student_index=0))
    return render_template('index.html')


@app.route('/student/<int:student_index>', methods=['GET', 'POST'])
def student_entry(student_index):
    num_students = session.get('num_students', 0)
    grade = session.get('grade', 'Grade 1-6')
    subjects = grade_subjects.get(grade, [])

    if request.method == 'POST':
        name = request.form['name']
        class_scores = request.form.getlist('class_score[]')
        exam_scores = request.form.getlist('exam_score[]')

        total_aggregate = sum(
            (float(class_scores[i]) * 0.5) + (float(exam_scores[i]) * 0.5) for i in range(len(subjects)))

        student_data = {
            'name': name,
            'total_aggregate': total_aggregate,
            'scores': [{
                'subject': subjects[i],
                'class_score': float(class_scores[i]),
                'exam_score': float(exam_scores[i]),
                'total_score': (float(class_scores[i]) * 0.5) + (float(exam_scores[i]) * 0.5)
            } for i in range(len(subjects))]
        }

        if 'students' not in session:
            session['students'] = []
        session['students'].append(student_data)
        session.modified = True

        if student_index + 1 < num_students:
            return redirect(url_for('student_entry', student_index=student_index + 1))
        else:
            return redirect(url_for('preview_reports'))

    return render_template('student_details.html', student_index=student_index, subjects=subjects,
                           total_students=num_students)


@app.route('/preview')
def preview_reports():
    students = sorted(session.get('students', []), key=lambda x: x['total_aggregate'], reverse=True)
    for index, student in enumerate(students):
        student['position'] = index + 1
    session['students'] = students
    session.modified = True
    return render_template('preview.html', students=students)


if __name__ == '__main__':
    app.run(debug=True)
