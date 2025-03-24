from flask import Flask, render_template, request, session, redirect, url_for, send_file, flash
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
class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    grade = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.String(50), nullable=False)
    total_aggregate = db.Column(db.Float, nullable=False)
    remarks = db.Column(db.String(255), nullable=True)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    class_score = db.Column(db.Float, nullable=False)
    exam_score = db.Column(db.Float, nullable=False)
    total_score = db.Column(db.Float, nullable=False)
    grade = db.Column(db.String(2), nullable=False)
    remark = db.Column(db.String(100), nullable=True)

# Function to generate letter grades
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
        # Process form data
        school_name = request.form.get("school_name")
        location = request.form.get("location")
        address = request.form.get("address")
        grade = request.form.get("grade")
        semester = request.form.get("semester")
        closing_date = request.form.get("closing_date")
        opening_date = request.form.get("opening_date")
        num_students = request.form.get("num_students")

        # Store data in session
        session["school_details"] = {
            "school_name": school_name,
            "location": location,
            "address": address,
            "grade": grade,
            "semester": semester,
            "closing_date": closing_date,
            "opening_date": opening_date,
            "num_students": int(num_students)
        }

        return redirect(url_for('student', student_index=0))

    return render_template('index.html')


@app.route('/generate_pdf/<int:student_index>')
def generate_pdf(student_index):
    students = session.get('students', [])
    if student_index >= len(students):
        return "Student not found", 404

    student = students[student_index]
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # School Details
    elements.append(Paragraph(f"<b>Great Hope School</b>", styles["Title"]))
    elements.append(Paragraph("Location: Adwumam", styles["Normal"]))
    elements.append(Paragraph("Address: 123 Learning St, Ghana", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Student Details
    elements.append(Paragraph(f"<b>Student Name:</b> {student['name']}", styles["Normal"]))
    elements.append(
        Paragraph(f"<b>Grade:</b> {student['grade']}    <b>Semester:</b> {student['semester']}", styles["Normal"]))
    elements.append(Paragraph("<b>Closing Date:</b> 20th December 2025    <b>Opening Date:</b> 10th January 2026",
                              styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Table Header
    table_data = [["Subject", "Class Score", "Exam Score", "Total", "Grade", "Subject Remarks"]]

    # Add student scores to the table
    for s in student['scores']:
        grade = calculate_grade(s['total_score'])
        table_data.append([s['subject'], s['class_score'], s['exam_score'], s['total_score'], grade, s['remark']])

    # Create Table
    table = Table(table_data, colWidths=[160, 70, 70, 70, 50, 140])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # Summary Section
    elements.append(Paragraph(f"<b>Total Aggregate Score:</b> {student['total_aggregate']}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Position in Class:</b> {student['position']}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Teacher's Remarks:</b> {student['remarks']}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Signatures
    elements.append(Paragraph("<b>Class Teacher's Signature:</b> ________________", styles["Normal"]))
    elements.append(Paragraph("<b>Principal's Signature:</b> ________________", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Footer - Closing and Opening Dates
    elements.append(Paragraph("<b>Closing Date:</b> 20th December 2025    <b>Opening Date:</b> 10th January 2026",
                              styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"{student['name']}_Report.pdf",
                     mimetype='application/pdf')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)