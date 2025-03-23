import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Define subjects dictionary
subjects_dict = {
    "Grade 1": ["Integrated Science", "Mathematics", "English Language", "Ghanaian Language", "Creative Art",
                "Religious and Moral Education", "History", "Computing", "OWOP", "Dictation"],
    "Grade 7": ["Integrated Science", "Mathematics", "English Language", "Ghanaian Language", "Creative Art",
                "Social Studies", "Computing", "Career Technology", "Religious and Moral Education", "Dictation"]
}

# Global lists for pupil names and scores
pupil_entries = []
class_score_entries = []
exam_score_entries = []

def generate_report():
    try:
        grade = grade_var.get()
        semester = semester_var.get()
        num_pupils = int(num_pupils_var.get())
        school_name = school_name_var.get()
        location = location_var.get()

        if not school_name or not location:
            messagebox.showerror("Input Error", "Please enter school name and location.")
            return

        subjects = subjects_dict.get(grade, [])

        # Ask user where to save the PDF
        pdf_file = filedialog.asksaveasfilename(defaultextension=".pdf",
                                                filetypes=[("PDF Files", "*.pdf")],
                                                title="Save Report As")
        if not pdf_file:  # User canceled save
            return

        c = canvas.Canvas(pdf_file, pagesize=letter)
        c.drawString(200, 750, f"School: {school_name}")
        c.drawString(200, 730, f"Location: {location}")
        c.drawString(200, 710, f"Grade: {grade}")
        c.drawString(200, 690, f"Semester: {semester}")

        y_position = 660

        for i in range(num_pupils):
            pupil_name = pupil_entries[i].get()
            c.drawString(50, y_position, f"Pupil: {pupil_name}")
            y_position -= 20
            total_score = 0

            for subject in subjects:
                try:
                    class_score = float(class_score_entries[i][subject].get())
                    exam_score = float(exam_score_entries[i][subject].get())
                except ValueError:
                    messagebox.showerror("Input Error", f"Invalid score for {subject}. Ensure all scores are numeric.")
                    return

                final_score = (class_score * 0.5) + (exam_score * 0.5)
                total_score += final_score
                c.drawString(70, y_position,
                             f"{subject}: Class Score = {class_score}, Exam Score = {exam_score}, Total = {final_score}")
                y_position -= 20

            c.drawString(50, y_position, f"Total Aggregate Score: {total_score}")
            y_position -= 40

        c.save()
        messagebox.showinfo("Success", f"PDF Report saved successfully at:\n{pdf_file}")

        # Open the PDF file after saving (optional)
        if os.name == "nt":  # Windows
            os.startfile(pdf_file)
        elif os.name == "posix":  # macOS / Linux
            os.system(f"xdg-open {pdf_file}")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

def update_subjects():
    grade = grade_var.get()
    subjects = subjects_dict.get(grade, [])

    for widget in subject_frame.winfo_children():
        widget.destroy()

    global pupil_entries, class_score_entries, exam_score_entries
    pupil_entries = []
    class_score_entries = []
    exam_score_entries = []

    for i in range(int(num_pupils_var.get())):
        tk.Label(subject_frame, text=f"Pupil {i + 1} Name:").grid(row=i * 11, column=0, pady=5)
        pupil_name_entry = tk.Entry(subject_frame)
        pupil_name_entry.grid(row=i * 11, column=1)
        pupil_entries.append(pupil_name_entry)

        class_scores = {}
        exam_scores = {}

        for j, subject in enumerate(subjects):
            tk.Label(subject_frame, text=subject).grid(row=i * 11 + j + 1, column=0)
            class_entry = tk.Entry(subject_frame, width=5)
            class_entry.grid(row=i * 11 + j + 1, column=1)
            exam_entry = tk.Entry(subject_frame, width=5)
            exam_entry.grid(row=i * 11 + j + 1, column=2)
            class_scores[subject] = class_entry
            exam_scores[subject] = exam_entry

        class_score_entries.append(class_scores)
        exam_score_entries.append(exam_scores)

# GUI Setup
top = tk.Tk()
top.title("Student Report Generator")

tk.Label(top, text="School Name:").grid(row=0, column=0)
school_name_var = tk.StringVar()
tk.Entry(top, textvariable=school_name_var).grid(row=0, column=1)

tk.Label(top, text="Location:").grid(row=1, column=0)
location_var = tk.StringVar()
tk.Entry(top, textvariable=location_var).grid(row=1, column=1)

tk.Label(top, text="Grade:").grid(row=2, column=0)
grade_var = tk.StringVar(value="Grade 1")
ttk.Combobox(top, textvariable=grade_var, values=list(subjects_dict.keys())).grid(row=2, column=1)

tk.Label(top, text="Semester:").grid(row=3, column=0)
semester_var = tk.StringVar()
tk.Entry(top, textvariable=semester_var).grid(row=3, column=1)

tk.Label(top, text="Number of Pupils:").grid(row=4, column=0)
num_pupils_var = tk.StringVar(value="1")
tk.Entry(top, textvariable=num_pupils_var).grid(row=4, column=1)

tk.Button(top, text="Update Subjects", command=update_subjects).grid(row=5, column=1)

tk.Button(top, text="Generate Report", command=generate_report).grid(row=6, column=1, pady=10)

subject_frame = tk.Frame(top)
subject_frame.grid(row=7, column=0, columnspan=2)

top.mainloop()
