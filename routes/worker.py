from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.service import Service
from models.worker import Worker
from models.worker_service import WorkerService
from models.booking import Booking


worker_bp = Blueprint("worker", __name__)

def worker_required():
    return current_user.is_authenticated and current_user.is_worker and current_user.worker_profile

@worker_bp.before_request
def check_worker():
    if not worker_required():
        return redirect(url_for("auth.login"))

@worker_bp.route("/dashboard")
def dashboard():
    worker = current_user.worker_profile
    bookings = Booking.query.filter_by(worker_id=worker.id).order_by(Booking.created_at.desc()).limit(8).all()
    return render_template("worker/dashboard.html", worker=worker, bookings=bookings)

@worker_bp.route("/profile", methods=["GET", "POST"])
def profile():
    worker = current_user.worker_profile
    if request.method == "POST":
        current_user.name = request.form.get("name", "").strip() or current_user.name
        current_user.phone = request.form.get("phone", "").strip()
        worker.location = request.form.get("location", "").strip()
        worker.bio = request.form.get("bio", "").strip()
        worker.experience = max(0, int(request.form.get("experience", 0) or 0))
        worker.hourly_rate = max(0, float(request.form.get("hourly_rate", 0) or 0))
        worker.is_available = request.form.get("is_available") == "on"
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("worker.profile"))
    return render_template("worker/profile.html", worker=worker)

@worker_bp.route("/services", methods=["GET", "POST"])
def services():
    worker = current_user.worker_profile
    all_services = Service.query.filter_by(is_active=True).order_by(Service.name.asc()).all()
    selected = {x.service_id for x in worker.service_links}
    if request.method == "POST":
        chosen = {int(x) for x in request.form.getlist("service_ids")}
        for link in list(worker.service_links):
            if link.service_id not in chosen:
                db.session.delete(link)
        for sid in chosen:
            if sid not in selected:
                db.session.add(WorkerService(worker_id=worker.id, service_id=sid))
        db.session.commit()
        flash("Your services were updated.", "success")
        return redirect(url_for("worker.services"))
    return render_template("worker/services.html", worker=worker, services=all_services, selected=selected)

@worker_bp.route("/bookings")
def bookings():
    worker = current_user.worker_profile
    bookings = Booking.query.filter_by(worker_id=worker.id).order_by(Booking.created_at.desc()).all()
    return render_template("worker/bookings.html", worker=worker, bookings=bookings)

@worker_bp.route("/bookings/<int:booking_id>", methods=["GET", "POST"])
def booking_detail(booking_id):
    worker = current_user.worker_profile
    booking = Booking.query.filter_by(id=booking_id, worker_id=worker.id).first_or_404()
    if request.method == "POST":
        status = request.form.get("status")
        if status in {"accepted", "rejected", "in_progress", "completed"}:
            booking.status = status
            try:
                progress = int(request.form.get("progress_percent", booking.progress_percent or 0))
            except (TypeError, ValueError):
                progress = booking.progress_percent or 0
            try:
                estimated = int(request.form.get("estimated_minutes", booking.estimated_minutes or 0))
            except (TypeError, ValueError):
                estimated = booking.estimated_minutes or 0
            booking.progress_percent = max(0, min(100, progress))
            booking.estimated_minutes = max(0, estimated)

            if status == "accepted" and booking.progress_percent < 10:
                booking.progress_percent = 10
            elif status == "in_progress" and booking.progress_percent < 25:
                booking.progress_percent = 25
            elif status == "completed":
                booking.progress_percent = 100
                booking.estimated_minutes = 0

            db.session.commit()
            flash("Booking status and progress updated.", "success")
        return redirect(url_for("worker.booking_detail", booking_id=booking.id))
    return render_template("worker/booking_detail.html", booking=booking, worker=worker)
