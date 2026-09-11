from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from extensions import db
from models.worker import Worker
from models.service import Service
from models.booking import Booking
from models.review import Review
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

def make_action_token(booking_id):
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"]).dumps({"booking_id": booking_id}, salt="booking-action")

def action_url(token, action):
    base = current_app.config.get("PUBLIC_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
    return f"{base}{url_for("booking.mobile_action", token=token, action=action)}"

def notify_worker(booking):
    phone = (booking.worker.user.phone or "").strip() if booking.worker and booking.worker.user else ""
    if not phone:
        return False, "Worker has no mobile number."
    accept = action_url(booking.action_token, "accept")
    decline = action_url(booking.action_token, "decline")
    body = (f"DIAL FOR SERVICE: New {booking.service.name} booking from {booking.customer.name}. "
            f"Accept: {accept} Decline: {decline}")
    sid=current_app.config.get("TWILIO_ACCOUNT_SID"); auth=current_app.config.get("TWILIO_AUTH_TOKEN"); sender=current_app.config.get("TWILIO_FROM_NUMBER")
    if sid and auth and sender:
        try:
            from twilio.rest import Client
            Client(sid, auth).messages.create(body=body, from_=sender, to=phone)
            return True, "SMS sent."
        except Exception as exc:
            current_app.logger.exception("Worker SMS failed: %s", exc)
            return False, "SMS provider error; booking is still available in Worker Dashboard."
    return False, "SMS not configured; worker can use the Worker Dashboard. Set TWILIO_* and PUBLIC_BASE_URL for mobile SMS."

booking_bp = Blueprint("booking", __name__)

@booking_bp.route("/create/<int:worker_id>/<int:service_id>", methods=["GET", "POST"])
@login_required
def create(worker_id, service_id):
    if not current_user.is_customer:
        flash("Only customers can create bookings.", "danger")
        return redirect(url_for("main.home"))
    worker = Worker.query.filter_by(id=worker_id, is_available=True, is_approved=True).first_or_404()
    service = Service.query.filter_by(id=service_id, is_active=True).first_or_404()
    if not any(link.service_id == service.id for link in worker.service_links):
        flash("This worker does not offer the selected service.", "danger")
        return redirect(url_for("main.service_detail", service_id=service.id))
    if request.method == "POST":
        date_text = request.form.get("scheduled_at", "").strip()
        scheduled_at = None
        if date_text:
            try:
                scheduled_at = datetime.fromisoformat(date_text)
            except ValueError:
                flash("Please select a valid date and time.", "danger")
                return render_template("customer/booking_form.html", worker=worker, service=service)
        latitude = longitude = None
        try:
            raw_lat = request.form.get("latitude", "").strip()
            raw_lng = request.form.get("longitude", "").strip()
            if raw_lat and raw_lng:
                latitude = float(raw_lat)
                longitude = float(raw_lng)
                if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                    latitude = longitude = None
        except (TypeError, ValueError):
            latitude = longitude = None

        booking = Booking(
            customer_id=current_user.id,
            worker_id=worker.id,
            service_id=service.id,
            status="pending",
            address=request.form.get("address", "").strip(),
            latitude=latitude,
            longitude=longitude,
            description=request.form.get("description", "").strip(),
            scheduled_at=scheduled_at,
            price=worker.hourly_rate or 0
        )
        db.session.add(booking)
        db.session.flush()
        booking.action_token = make_action_token(booking.id)
        db.session.commit()
        sent, notice = notify_worker(booking)
        flash("Booking request sent to the worker.", "success")
        if not sent:
            flash(notice, "info")
        return redirect(url_for("booking.my_bookings"))
    return render_template("customer/booking_form.html", worker=worker, service=service)


@booking_bp.route("/mobile-action/<token>/<action>")
def mobile_action(token, action):
    if action not in {"accept", "decline"}:
        return "Invalid action", 400
    try:
        data = URLSafeTimedSerializer(current_app.config["SECRET_KEY"]).loads(token, salt="booking-action", max_age=7*24*3600)
    except (BadSignature, SignatureExpired):
        return render_template("errors/404.html"), 404
    booking = Booking.query.get_or_404(data.get("booking_id"))
    if booking.action_token != token or booking.status != "pending":
        return render_template("mobile_action.html", booking=booking, result="This booking is no longer pending.")
    booking.status = "accepted" if action == "accept" else "rejected"
    db.session.commit()
    result = "Booking accepted successfully." if action == "accept" else "Booking declined."
    return render_template("mobile_action.html", booking=booking, result=result)

@booking_bp.route("/my-bookings")
@login_required
def my_bookings():
    if not current_user.is_customer:
        return redirect(url_for("main.home"))
    bookings = Booking.query.filter_by(customer_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template("customer/bookings.html", bookings=bookings)

@booking_bp.route("/<int:booking_id>")
@login_required
def detail(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if current_user.is_customer and booking.customer_id != current_user.id:
        return "Forbidden", 403
    if current_user.is_worker and booking.worker_id != current_user.worker_profile.id:
        return "Forbidden", 403
    return render_template("customer/booking_detail.html", booking=booking)

@booking_bp.route("/<int:booking_id>/review", methods=["GET", "POST"])
@login_required
def review(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if not current_user.is_customer or booking.customer_id != current_user.id:
        return "Forbidden", 403
    if booking.status != "completed":
        flash("You can review a completed booking only.", "warning")
        return redirect(url_for("booking.detail", booking_id=booking.id))
    if booking.review:
        flash("This booking has already been reviewed.", "info")
        return redirect(url_for("booking.detail", booking_id=booking.id))
    if request.method == "POST":
        try:
            rating = int(request.form.get("rating", 0))
        except ValueError:
            rating = 0
        if rating < 1 or rating > 5:
            flash("Please choose a rating from 1 to 5.", "danger")
            return render_template("customer/review.html", booking=booking)
        review = Review(
            booking_id=booking.id,
            customer_id=current_user.id,
            worker_id=booking.worker_id,
            rating=rating,
            comment=request.form.get("comment", "").strip()
        )
        db.session.add(review)
        db.session.commit()
        flash("Thank you for your review.", "success")
        return redirect(url_for("booking.detail", booking_id=booking.id))
    return render_template("customer/review.html", booking=booking)
