from functools import wraps
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.user import User
from models.service import Service
from models.worker import Worker
from models.worker_service import WorkerService
from models.booking import Booking
from models.review import Review
from models.extra_features import Coupon, Notification

admin_bp = Blueprint("admin", __name__)

def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            flash("Admin access required.", "danger")
            return redirect(url_for("main.home"))
        return view(*args, **kwargs)
    return wrapped

def make_slug(value):
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value or "service"

def unique_slug(name, current_id=None):
    base = make_slug(name)
    slug = base
    n = 2
    while True:
        q = Service.query.filter_by(slug=slug)
        if current_id:
            q = q.filter(Service.id != current_id)
        if not q.first():
            return slug
        slug = f"{base}-{n}"
        n += 1

@admin_bp.route("/")
@admin_required
def index():
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    stats = {
        "customers": User.query.filter_by(role="customer").count(),
        "workers": Worker.query.count(),
        "pending_workers": Worker.query.filter_by(is_approved=False).count(),
        "services": Service.query.count(),
        "bookings": Booking.query.count(),
        "reviews": Review.query.count(),
    }
    recent = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
    pending_workers = Worker.query.filter_by(is_approved=False).order_by(Worker.created_at.desc()).limit(8).all()
    return render_template("admin/dashboard.html", stats=stats, bookings=recent, pending_workers=pending_workers)

@admin_bp.route("/services")
@admin_required
def services():
    services = Service.query.order_by(Service.name.asc()).all()
    return render_template("admin/services.html", services=services)

@admin_bp.route("/services/add", methods=["GET", "POST"])
@admin_required
def add_service():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        icon = request.form.get("icon", "🔧").strip() or "🔧"
        if not name:
            flash("Service name is required.", "danger")
            return render_template("admin/service_form.html", service=None)
        service = Service(name=name, slug=unique_slug(name), description=description, icon=icon, is_active=True)
        db.session.add(service)
        db.session.commit()
        flash("Service added successfully.", "success")
        return redirect(url_for("admin.services"))
    return render_template("admin/service_form.html", service=None)

@admin_bp.route("/services/<int:service_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)
    if request.method == "POST":
        name = request.form.get("name", "").strip() or service.name
        service.name = name
        service.slug = unique_slug(name, service.id)
        service.description = request.form.get("description", "").strip()
        service.icon = request.form.get("icon", "🔧").strip() or "🔧"
        service.is_active = request.form.get("is_active") == "on"
        db.session.commit()
        flash("Service updated successfully.", "success")
        return redirect(url_for("admin.services"))
    return render_template("admin/service_form.html", service=service)

@admin_bp.route("/services/<int:service_id>/toggle", methods=["POST"])
@admin_required
def toggle_service(service_id):
    service = Service.query.get_or_404(service_id)
    service.is_active = not service.is_active
    db.session.commit()
    flash("Service visibility updated.", "success")
    return redirect(url_for("admin.services"))

@admin_bp.route("/workers/add", methods=["GET", "POST"])
@admin_required
def add_worker():
    services = Service.query.filter_by(is_active=True).order_by(Service.name.asc()).all()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        location = request.form.get("location", "").strip()
        bio = request.form.get("bio", "").strip()
        try:
            experience = max(0, int(request.form.get("experience", 0) or 0))
            hourly_rate = max(0, float(request.form.get("hourly_rate", 0) or 0))
        except ValueError:
            flash("Experience and hourly rate must be valid numbers.", "danger")
            return render_template("admin/worker_form.html", services=services, selected=set())
        selected = {int(x) for x in request.form.getlist("service_ids") if x.isdigit()}
        valid_ids = {s.id for s in services}
        selected &= valid_ids
        if not name or not email or not password:
            flash("Name, email and password are required.", "danger")
            return render_template("admin/worker_form.html", services=services, selected=selected)
        if not selected:
            flash("Select at least one service.", "danger")
            return render_template("admin/worker_form.html", services=services, selected=selected)
        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return render_template("admin/worker_form.html", services=services, selected=selected)
        user = User(name=name, email=email, phone=phone, role="worker", is_active=True)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        worker = Worker(user_id=user.id, location=location, bio=bio, experience=experience,
                        hourly_rate=hourly_rate, is_available=True, is_approved=True)
        db.session.add(worker)
        db.session.flush()
        for sid in selected:
            db.session.add(WorkerService(worker_id=worker.id, service_id=sid))
        db.session.commit()
        flash(f"Worker {name} added and approved successfully.", "success")
        return redirect(url_for("admin.workers"))
    return render_template("admin/worker_form.html", services=services, selected=set())

@admin_bp.route("/workers")
@admin_required
def workers():
    workers = Worker.query.order_by(Worker.is_approved.asc(), Worker.id.desc()).all()
    return render_template("admin/workers.html", workers=workers)

@admin_bp.route("/workers/<int:worker_id>")
@admin_required
def worker_detail(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    services = [link.service for link in worker.service_links if link.service]
    return render_template("admin/worker_detail.html", worker=worker, services=services)

@admin_bp.route("/workers/<int:worker_id>/approve", methods=["POST"])
@admin_required
def approve_worker(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    worker.is_approved = True
    db.session.commit()
    flash(f"{worker.display_name} has been approved.", "success")
    return redirect(request.referrer or url_for("admin.workers"))

@admin_bp.route("/workers/<int:worker_id>/reject", methods=["POST"])
@admin_required
def reject_worker(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    worker.is_approved = False
    db.session.commit()
    flash(f"{worker.display_name} is now hidden from customers.", "info")
    return redirect(request.referrer or url_for("admin.workers"))

@admin_bp.route("/customers")
@admin_required
def customers():
    customers = User.query.filter_by(role="customer").order_by(User.id.desc()).all()
    return render_template("admin/customers.html", customers=customers)

@admin_bp.route("/customers/<int:customer_id>")
@admin_required
def customer_detail(customer_id):
    customer = User.query.filter_by(id=customer_id, role="customer").first_or_404()
    bookings = Booking.query.filter_by(customer_id=customer.id).order_by(Booking.created_at.desc()).all()
    return render_template("admin/customer_detail.html", customer=customer, bookings=bookings)

@admin_bp.route("/bookings")
@admin_required
def bookings():
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template("admin/bookings.html", bookings=bookings)

@admin_bp.route("/bookings/<int:booking_id>/status", methods=["POST"])
@admin_required
def update_booking_status(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    status = request.form.get("status", "").strip()
    allowed = {"accepted", "rejected", "in_progress", "completed"}
    if status not in allowed:
        flash("Invalid booking status.", "danger")
        return redirect(url_for("admin.bookings"))
    booking.status = status
    db.session.commit()
    label = "accepted" if status == "accepted" else "declined" if status == "rejected" else status.replace("_", " ")
    flash(f"Booking #{booking.id} {label} successfully.", "success")
    return redirect(url_for("admin.bookings"))

@admin_bp.route("/coupons", methods=["GET", "POST"])
@admin_required
def coupons():
    if request.method == "POST":
        code=request.form.get("code", "").strip().upper()
        try:
            pct=max(0,float(request.form.get("discount_percent",0))); cap=max(0,float(request.form.get("max_discount",0)))
        except ValueError:
            flash("Discount values must be numbers.", "danger"); return redirect(url_for("admin.coupons"))
        if not code or pct<=0: flash("Coupon code and discount are required.", "danger")
        elif Coupon.query.filter_by(code=code).first(): flash("Coupon already exists.", "danger")
        else: db.session.add(Coupon(code=code,discount_percent=min(pct,100),max_discount=cap,is_active=True)); db.session.commit(); flash("Coupon created.","success")
    return render_template("admin/coupons.html", coupons=Coupon.query.order_by(Coupon.created_at.desc()).all())

@admin_bp.route("/coupons/<int:coupon_id>/toggle", methods=["POST"])
@admin_required
def toggle_coupon(coupon_id):
    c=Coupon.query.get_or_404(coupon_id); c.is_active=not c.is_active; db.session.commit(); return redirect(url_for("admin.coupons"))

@admin_bp.route("/reviews")
@admin_required
def reviews():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template("admin/reviews.html", reviews=reviews)

# ---------- Advanced admin management ----------
@admin_bp.route('/payments')
@admin_required
def payments():
    from sqlalchemy import func
    from models.advanced import Payment
    payments = Payment.query.order_by(Payment.created_at.desc()).all()
    gross = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).scalar() or 0
    commission = db.session.query(func.coalesce(func.sum(Payment.commission_amount), 0)).scalar() or 0
    worker_net = db.session.query(func.coalesce(func.sum(Payment.worker_amount), 0)).scalar() or 0
    return render_template('admin/payments.html', payments=payments, gross=gross, commission=commission, worker_net=worker_net)

@admin_bp.route('/analytics')
@admin_required
def analytics():
    from sqlalchemy import func
    from models.advanced import WorkerEarning
    total_revenue = db.session.query(func.coalesce(func.sum(WorkerEarning.gross_amount),0)).scalar() or 0
    commission = db.session.query(func.coalesce(func.sum(WorkerEarning.commission_amount),0)).scalar() or 0
    completed = Booking.query.filter_by(status='completed').count()
    status_counts = {s: Booking.query.filter_by(status=s).count() for s in ['pending','accepted','in_progress','arrived','completed','rejected']}
    top_services = db.session.query(Service.name, func.count(Booking.id)).join(Booking, Booking.service_id==Service.id).group_by(Service.id).order_by(func.count(Booking.id).desc()).limit(8).all()
    top_workers = db.session.query(Worker, func.count(Booking.id)).join(Booking, Booking.worker_id==Worker.id).group_by(Worker.id).order_by(func.count(Booking.id).desc()).limit(8).all()
    return render_template('admin/analytics.html', total_revenue=total_revenue, commission=commission, completed=completed,
                           status_counts=status_counts, top_services=top_services, top_workers=top_workers)

@admin_bp.route('/complaints')
@admin_required
def complaints():
    from models.advanced import Complaint
    return render_template('admin/complaints.html', complaints=Complaint.query.order_by(Complaint.created_at.desc()).all())

@admin_bp.route('/complaints/<int:complaint_id>/update', methods=['POST'])
@admin_required
def update_complaint(complaint_id):
    from models.advanced import Complaint
    c=Complaint.query.get_or_404(complaint_id); c.status=request.form.get('status','open'); c.admin_reply=request.form.get('admin_reply','').strip(); db.session.commit()
    flash('Support ticket updated.','success'); return redirect(url_for('admin.complaints'))

@admin_bp.route('/activity-log')
@admin_required
def activity_log():
    from models.advanced import ActivityLog
    return render_template('admin/activity_log.html', logs=ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(200).all())

@admin_bp.route('/worker/<int:worker_id>/verify', methods=['POST'])
@admin_required
def verify_worker(worker_id):
    worker=Worker.query.get_or_404(worker_id); worker.verification_status='verified'; worker.verified_at=datetime.utcnow(); db.session.commit(); flash('Worker verification badge enabled.','success'); return redirect(request.referrer or url_for('admin.worker_detail', worker_id=worker.id))

@admin_bp.route('/worker/<int:worker_id>/unverify', methods=['POST'])
@admin_required
def unverify_worker(worker_id):
    worker=Worker.query.get_or_404(worker_id); worker.verification_status='pending'; worker.verified_at=None; db.session.commit(); flash('Worker verification badge removed.','info'); return redirect(request.referrer or url_for('admin.worker_detail', worker_id=worker.id))
