from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from uuid import uuid4
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timezone
from sqlalchemy.sql import func
from datetime import datetime
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
db_url = os.environ.get("DATABASE_URL")

if db_url:
    # Render gives postgres://, SQLAlchemy expects postgresql://
    db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "portfolio.db")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

UPLOAD_FOLDER = os.path.join(basedir, "static/uploads/projects")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

EDU_ICON_FOLDER = os.path.join(basedir, "static/uploads/education")
os.makedirs(EDU_ICON_FOLDER, exist_ok=True)

app.config["EDU_ICON_FOLDER"] = EDU_ICON_FOLDER


# --- MODELS --------------------------------------------------------
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    subtitle = db.Column(db.String(200))
    description = db.Column(db.Text)
    tech_stack = db.Column(db.String(200))
    github_url = db.Column(db.String(255))
    live_url = db.Column(db.String(255))
    image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone = True), server_default=func.now())


class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(50)) 
    category = db.Column(db.String(100))


class Certification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    issuer = db.Column(db.String(200))
    date_obtained = db.Column(db.String(50))  # keep as string for simplicity
    credential_url = db.Column(db.String(255))


class Experience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(150), nullable=False)
    company = db.Column(db.String(150), nullable=False)
    start_date = db.Column(db.String(50))
    end_date = db.Column(db.String(50))
    location = db.Column(db.String(150))
    description = db.Column(db.Text)

class Education(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    degree = db.Column(db.String(200), nullable=False)
    degree_type = db.Column(db.String(100))
    institute = db.Column(db.String(200), nullable=False)
    institute_url = db.Column(db.String(255))
    start_year = db.Column(db.String(20))
    end_year = db.Column(db.String(20))
    location = db.Column(db.String(150))
    description = db.Column(db.Text)
    icon = db.Column(db.String(255))

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone = True), server_default=func.now())


# --- PUBLIC ROUTES -------------------------------------------------
@app.route("/")
def index():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    skills = Skill.query.order_by(Skill.category.asc(), Skill.name.asc()).all()
    certs = Certification.query.order_by(Certification.date_obtained.desc()).all()
    experiences = Experience.query.all()
    education =  Education.query.order_by(Education.end_year.desc()).all()

    skill_groups = {}
    for s in skills:
        key = (s.category or "Other").strip()
        skill_groups.setdefault(key, []).append(s)


    return render_template(
        "index.html",
        projects=projects,
        skills=skills,
        skill_groups=skill_groups,
        certs=certs,
        experiences=experiences,
        education=education,
    )


# --- SIMPLE ADMIN DASHBOARD ----------------------------------------
@app.route("/admin")
def admin_dashboard():
    return render_template("admin_dashboard.html")


# --- PROJECTS CRUD -------------------------------------------------
@app.route("/admin/projects")
def admin_projects():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template("admin_projects.html", projects=projects)


@app.route("/admin/projects/create", methods=["GET", "POST"])
def create_project():
    if request.method == "POST":

        image_file = request.files.get("image")
        image_filename = None

        if image_file and image_file.filename != "":
            image_filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))

        project = Project(
            title=request.form["title"],
            subtitle=request.form.get("subtitle"),
            description=request.form.get("description"),
            tech_stack=request.form.get("tech_stack"),
            github_url=request.form.get("github_url"),
            live_url=request.form.get("live_url"),
            image=image_filename
        )
        db.session.add(project)
        db.session.commit()
        return redirect(url_for("admin_projects"))
    return render_template("project_form.html", project=None)


@app.route("/admin/projects/<int:project_id>/edit", methods=["GET", "POST"])
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    if request.method == "POST":
        project.title = request.form["title"]
        project.subtitle = request.form.get("subtitle")
        project.description = request.form.get("description")
        project.tech_stack = request.form.get("tech_stack")
        project.github_url = request.form.get("github_url")
        project.live_url = request.form.get("live_url")
        image_file = request.files.get("image")
        if image_file and image_file.filename:
            if project.image:
                old_path = os.path.join(app.config["UPLOAD_FOLDER"], project.image)
                if os.path.exists(old_path):
                    os.remove(old_path)

            ext = os.path.splitext(image_file.filename)[1].lower() 
            new_filename = f"{uuid4().hex}{ext}" 
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], new_filename))
            project.image = new_filename
        db.session.commit()
        return redirect(url_for("admin_projects"))
    return render_template("project_form.html", project=project)


@app.route("/admin/projects/<int:project_id>/delete", methods=["POST"])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return redirect(url_for("admin_projects"))


# --- SKILLS (Create + Delete) --------------------------------------
@app.route("/admin/skills", methods=["GET", "POST"])
def admin_skills():
    if request.method == "POST":
        skill = Skill(
            name=request.form["name"],
            level=request.form.get("level"),
            category=request.form.get("category")
        )
        db.session.add(skill)
        db.session.commit()
        return redirect(url_for("admin_skills"))

    skills = Skill.query.order_by(Skill.name.asc()).all()
    return render_template("admin_skills.html", skills=skills)


@app.route("/admin/skills/<int:skill_id>/delete", methods=["POST"])
def delete_skill(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    db.session.delete(skill)
    db.session.commit()
    return redirect(url_for("admin_skills"))

#--- EDUCATION CRUD ------------------------------------------
@app.route("/admin/education")
def admin_education():
    education = Education.query.order_by(Education.end_year.desc()).all()
    return render_template("admin_education.html", education=education)


@app.route("/admin/education/create", methods=["GET", "POST"])
def create_education():
    if request.method == "POST":
        icon_file = request.files.get("icon")
        icon_filename = None

        if icon_file and icon_file.filename:
            ext = os.path.splitext(icon_file.filename)[1].lower()
            icon_filename = f"{uuid4().hex}{ext}"
            icon_file.save(os.path.join(app.config["EDU_ICON_FOLDER"], icon_filename))

        edu = Education(
            degree=request.form["degree"],
            degree_type=request.form["degree_type"],
            institute=request.form["institute"],
            institute_url=request.form["institute_url"],
            start_year=request.form.get("start_year"),
            end_year=request.form.get("end_year"),
            location=request.form.get("location"),
            description=request.form.get("description"),
            icon=icon_filename,
        )

        db.session.add(edu)
        db.session.commit()
        return redirect(url_for("admin_education"))

    return render_template("education_form.html", edu=None)


@app.route("/admin/education/<int:edu_id>/edit", methods=["GET", "POST"])
def edit_education(edu_id):
    edu = Education.query.get_or_404(edu_id)

    if request.method == "POST":
        edu.degree = request.form["degree"]
        edu.degree_type = request.form["degree_type"]
        edu.institute = request.form["institute"]
        edu.institute_url = request.form["institute_url"]
        edu.start_year = request.form.get("start_year")
        edu.end_year = request.form.get("end_year")
        edu.location = request.form.get("location")
        edu.description = request.form.get("description")

        icon_file = request.files.get("icon")
        if icon_file and icon_file.filename:
            if edu.icon:
                old_path = os.path.join(app.config["EDU_ICON_FOLDER"], edu.icon)
                if os.path.exists(old_path):
                    os.remove(old_path)

            ext = os.path.splitext(icon_file.filename)[1].lower()
            icon_filename = f"{uuid4().hex}{ext}"
            icon_file.save(os.path.join(app.config["EDU_ICON_FOLDER"], icon_filename))
            edu.icon = icon_filename

        db.session.commit()
        return redirect(url_for("admin_education"))

    return render_template("education_form.html", edu=edu)


@app.route("/admin/education/<int:edu_id>/delete", methods=["POST"])
def delete_education(edu_id):
    edu = Education.query.get_or_404(edu_id)

    if edu.icon:
        icon_path = os.path.join(app.config["EDU_ICON_FOLDER"], edu.icon)
        if os.path.exists(icon_path):
            os.remove(icon_path)

    db.session.delete(edu)
    db.session.commit()
    return redirect(url_for("admin_education"))



# --- CERTIFICATIONS CRUD -------------------------------------------
@app.route("/admin/certifications")
def admin_certifications():
    certs = Certification.query.order_by(Certification.date_obtained.desc()).all()
    return render_template("admin_certifications.html", certs=certs)


@app.route("/admin/certifications/create", methods=["GET", "POST"])
def create_certification():
    if request.method == "POST":
        cert = Certification(
            name=request.form["name"],
            issuer=request.form.get("issuer"),
            date_obtained=request.form.get("date_obtained"),
            credential_url=request.form.get("credential_url"),
        )
        db.session.add(cert)
        db.session.commit()
        return redirect(url_for("admin_certifications"))
    return render_template("certification_form.html", cert=None)


@app.route("/admin/certifications/<int:cert_id>/edit", methods=["GET", "POST"])
def edit_certification(cert_id):
    cert = Certification.query.get_or_404(cert_id)
    if request.method == "POST":
        cert.name = request.form["name"]
        cert.issuer = request.form.get("issuer")
        cert.date_obtained = request.form.get("date_obtained")
        cert.credential_url = request.form.get("credential_url")
        db.session.commit()
        return redirect(url_for("admin_certifications"))
    return render_template("certification_form.html", cert=cert)


@app.route("/admin/certifications/<int:cert_id>/delete", methods=["POST"])
def delete_certification(cert_id):
    cert = Certification.query.get_or_404(cert_id)
    db.session.delete(cert)
    db.session.commit()
    return redirect(url_for("admin_certifications"))


# --- EXPERIENCE CRUD -----------------------------------------------
@app.route("/admin/experience")
def admin_experience():
    experiences = Experience.query.all()
    return render_template("admin_experience.html", experiences=experiences)


@app.route("/admin/experience/create", methods=["GET", "POST"])
def create_experience():
    if request.method == "POST":
        exp = Experience(
            role=request.form["role"],
            company=request.form["company"],
            start_date=request.form.get("start_date"),
            end_date=request.form.get("end_date"),
            location=request.form.get("location"),
            description=request.form.get("description"),
        )
        db.session.add(exp)
        db.session.commit()
        return redirect(url_for("admin_experience"))
    return render_template("experience_form.html", exp=None)


@app.route("/admin/experience/<int:exp_id>/edit", methods=["GET", "POST"])
def edit_experience(exp_id):
    exp = Experience.query.get_or_404(exp_id)
    if request.method == "POST":
        exp.role = request.form["role"]
        exp.company = request.form["company"]
        exp.start_date = request.form.get("start_date")
        exp.end_date = request.form.get("end_date")
        exp.location = request.form.get("location")
        exp.description = request.form.get("description")
        db.session.commit()
        return redirect(url_for("admin_experience"))
    return render_template("experience_form.html", exp=exp)


@app.route("/admin/experience/<int:exp_id>/delete", methods=["POST"])
def delete_experience(exp_id):
    exp = Experience.query.get_or_404(exp_id)
    db.session.delete(exp)
    db.session.commit()
    return redirect(url_for("admin_experience"))

@app.route("/contact", methods=["POST"])
def contact():
    email = request.form.get("email")
    message = request.form.get("message")

    # Save to DB
    msg = ContactMessage(email=email, message=message)
    db.session.add(msg)
    db.session.commit()

    return jsonify({"success": True, "message": "Message sent successfully!"})

@app.route("/admin/messages")
def admin_messages():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template("admin_messages.html", messages=messages)

@app.route("/admin/messages/<int:msg_id>/delete", methods=["POST"])
def delete_message(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    db.session.delete(msg)
    db.session.commit()
    return redirect(url_for("admin_messages"))

# --- MAIN ----------------------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)