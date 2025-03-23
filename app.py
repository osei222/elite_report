from flask import Flask, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import os

app = Flask(__name__)

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://school_reports_db_user:GAwhK1OzIt9kFUUB5uyDi6DZ4SGRYdmV@dpg-cvfkt78fnakc739pqkrg-a.oregon-postgres.render.com/school_reports_db")
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        school_name = request.form['school_name']
        location = request.form['location']
        grade = request.form['grade']
        semester = request.form['semester']
        vacating_date = request.form['vacating_date']
        reopening_date = request.form['reopening_date']

        pupils = []
        student_index = 0

        while f'pupil_name_{student_index}' in request.form:
            pupil_name = request.form[f'pupil_name_{student_index}']
            subjects = []

            # Create student record
            student = Student(name=pupil_name, grade=grade, semester=semester, total_aggregate=0)
            db.session.add(student)
            db.session.flush()  # Get student.id before commit

            for i in range(len(request.form.getlist(f'subject_{student_index}[]'))):
                subject_name = request.form.getlist(f'subject_{student_index}[]')[i]
                class_score = float(request.form.getlist(f'class_score_{student_index}[]')[i])
                exam_score = float(request.form.getlist(f'exam_score_{student_index}[]')[i])
                total_score = (class_score * 0.5) + (exam_score * 0.5)

                if total_score >= 75:
                    remark = "Pass"
                elif total_score >= 50:
                    remark = "Credit"
                else:
                    remark = "Fail"

                # Save scores to database
                score = Score(student_id=student.id, subject=subject_name, class_score=class_score,
                              exam_score=exam_score, total_score=total_score, remark=remark)
                db.session.add(score)

                subjects.append({
                    "name": subject_name,
                    "class_score": class_score,
                    "exam_score": exam_score,
                    "total_score": total_score,
                    "remark": remark
                })

            total_aggregate = sum(sub["total_score"] for sub in subjects)
            student.total_aggregate = total_aggregate  # Update total_aggregate
            db.session.commit()  # Save all changes

            pupils.append({
                "name": pupil_name,
                "subjects": subjects,
                "total_aggregate": total_aggregate
            })

            student_index += 1

        # Sort pupils by total aggregate score
        pupils = sorted(pupils, key=lambda x: x["total_aggregate"], reverse=True)
        for index, pupil in enumerate(pupils):
            pupil["position"] = index + 1

        buffer = BytesIO()
        pdf = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph(f"<b>{school_name.upper()}</b>", styles['Title']))
        elements.append(Paragraph(f"Location: {location}", styles['Normal']))
        elements.append(Paragraph(f"Grade: {grade} | Semester: {semester}", styles['Normal']))
        elements.append(Paragraph(f"Date of Vacating: {vacating_date} | Date of Reopening: {reopening_date}", styles['Normal']))
        elements.append(Spacer(1, 10))

        table_data = [["Pupil Name", "Subject", "Class Score", "Exam Score", "Total Score", "Remark", "Position"]]

        for pupil in pupils:
            first_row = True
            for subject in pupil["subjects"]:
                row = [
                    pupil["name"] if first_row else "",
                    subject["name"],
                    subject["class_score"],
                    subject["exam_score"],
                    subject["total_score"],
                    subject["remark"],
                    pupil["position"] if first_row else ""
                ]
                table_data.append(row)
                first_row = False

            table_data.append(["", "Total Aggregate", "", "", pupil["total_aggregate"], "", ""])
            table_data.append(["", "", "", "", "", "", ""])

        table = Table(table_data, colWidths=[120, 120, 80, 80, 80, 80, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("<b>Teacher's Remarks:</b>", styles['Normal']))
        elements.append(Paragraph("Great effort! Keep improving your performance.", styles['Italic']))

        pdf.build(elements)
        buffer.seek(0)

        return send_file(buffer, as_attachment=True, download_name="student_report.pdf", mimetype='application/pdf')

    except Exception as e:
        return f"Error generating PDF: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
