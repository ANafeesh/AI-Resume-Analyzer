from flask import Flask, render_template, request, redirect, session
import os
from werkzeug.utils import secure_filename

# ----- Import your existing modules -----
from resume_parser import extract_text
from skill_extractor import extract_skills
from matcher import calculate_match
from skill_gap import find_skill_gap
from feedback_generator import generate_feedback

# ----- Flask setup -----
app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect("/dashboard")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin123":
            session["user"] = username
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html")


# ---------------- UPLOAD ----------------
@app.route("/upload")
def upload():
    if "user" not in session:
        return redirect("/")
    return render_template("upload.html")


# ---------------- ANALYZE ----------------
@app.route("/analyze", methods=["POST"])
def analyze():
    if "user" not in session:
        return redirect("/")

    job_desc = request.form.get("jobdesc", "")
    files = request.files.getlist("resumes")
    results = []

    for file in files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)

            text = extract_text(path)
            skills = extract_skills(text)
            score = calculate_match(skills, job_desc)
            missing = find_skill_gap(skills, job_desc)
            feedback = generate_feedback(score, missing)

            results.append({
                "name": filename,
                "skills": skills,
                "score": score,
                "missing": missing,
                "feedback": feedback
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return render_template("results.html", results=results)


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)