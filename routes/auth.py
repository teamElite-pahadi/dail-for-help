from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from extensions import db
from models.user import User
from models.worker import Worker
from models.service import Service
from models.worker_service import WorkerService

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    login_role = request.args.get("role", "customer")
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            flash("Welcome back!", "success")
            if user.is_admin:
                return redirect(url_for("admin.dashboard"))
            if user.is_worker:
                return redirect(url_for("worker.dashboard"))
            return redirect(request.args.get("next") or url_for("main.home"))
        flash("Invalid email or password.", "danger")
    return render_template("auth/login.html", login_role=login_role)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        location = request.form.get("location", "").strip()
        password = request.form.get("password", "")
        if not name or not email or not password:
            flash("Name, email and password are required.", "danger")
            return render_template("auth/register.html")
        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return render_template("auth/register.html")
        user = User(name=name, email=email, phone=phone, location=location, role="customer")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Account created successfully.", "success")
        return redirect(url_for("main.home"))
    return render_template("auth/register.html")

@auth_bp.route("/worker-register", methods=["GET", "POST"])
def worker_register():
    services = Service.query.filter_by(is_active=True).order_by(Service.name.asc()).all()
    if current_user.is_authenticated:
        flash("Logout first to create another worker account.", "info")
        return redirect(url_for("main.home"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        location = request.form.get("location", "").strip()
        bio = request.form.get("bio", "").strip()
        experience = request.form.get("experience", "0")
        hourly_rate = request.form.get("hourly_rate", "0")
        service_ids = request.form.getlist("service_ids")
        if not name or not email or not password:
            flash("Name, email and password are required.", "danger")
            return render_template("auth/worker_register.html", services=services)
        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return render_template("auth/worker_register.html", services=services)
        if not service_ids:
            flash("Please select at least one service you provide.", "danger")
            return render_template("auth/worker_register.html", services=services)
        try:
            experience = max(0, int(experience))
            hourly_rate = max(0, float(hourly_rate))
        except ValueError:
            flash("Experience and hourly rate must be valid numbers.", "danger")
            return render_template("auth/worker_register.html", services=services)
        user = User(name=name, email=email, phone=phone, role="worker")
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        worker = Worker(
            user_id=user.id, location=location, bio=bio,
            experience=experience, hourly_rate=hourly_rate,
            is_available=True, is_approved=False
        )
        db.session.add(worker)
        db.session.flush()
        for sid in service_ids:
            if Service.query.get(int(sid)):
                db.session.add(WorkerService(worker_id=worker.id, service_id=int(sid)))
        db.session.commit()
        login_user(user)
        flash("Worker account created. It will appear publicly after admin approval.", "success")
        return redirect(url_for("worker.dashboard"))
    return render_template("auth/worker_register.html", services=services)


@auth_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    if current_user.is_admin:
        return redirect(url_for("admin.dashboard"))
    if request.method == "POST":
        current_user.name = request.form.get("name", "").strip() or current_user.name
        current_user.phone = request.form.get("phone", "").strip()
        current_user.location = request.form.get("location", "").strip()
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("auth.profile"))
    return render_template("auth/profile.html")

@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.home"))
