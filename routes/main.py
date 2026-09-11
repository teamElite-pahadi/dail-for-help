from flask import Blueprint, render_template, request
from sqlalchemy import or_
from extensions import db
from models.service import Service
from models.worker import Worker
from models.worker_service import WorkerService
from flask_login import current_user

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def home():
    # Visitors first choose whether they are customers or the website administrator.
    if not current_user.is_authenticated:
        return render_template("portal.html")
    services = Service.query.filter_by(is_active=True).order_by(Service.name.asc()).all()
    return render_template("home.html", services=services)

@main_bp.route("/services")
def services():
    services = Service.query.filter_by(is_active=True).order_by(Service.name.asc()).all()
    return render_template("services.html", services=services)

@main_bp.route("/services/<int:service_id>")
def service_detail(service_id):
    service = Service.query.filter_by(id=service_id, is_active=True).first_or_404()
    area = request.args.get("area", "").strip()
    base_query = (
        Worker.query
        .join(WorkerService, WorkerService.worker_id == Worker.id)
        .filter(
            WorkerService.service_id == service.id,
            Worker.is_available.is_(True),
            Worker.is_approved.is_(True)
        )
    )
    all_workers = base_query.order_by(Worker.id.desc()).all()
    if area:
        # Prefer workers whose saved locality contains the customer's area.
        local_workers = [
            w for w in all_workers
            if w.location and area.lower() in w.location.lower()
        ]
        workers = local_workers
        location_match = bool(local_workers)
    else:
        workers = all_workers
        location_match = False
    return render_template(
        "service_detail.html", service=service, workers=workers,
        area=area, location_match=location_match, total_workers=len(all_workers)
    )

@main_bp.route("/worker/<int:worker_id>")
def worker_profile(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    return render_template("worker_profile.html", worker=worker)

@main_bp.route("/search")
def search():
    q = request.args.get("q", "").strip()
    services = []
    workers = []
    if q:
        services = Service.query.filter(
            Service.is_active.is_(True),
            or_(Service.name.ilike(f"%{q}%"), Service.description.ilike(f"%{q}%"))
        ).all()
        workers = Worker.query.filter(
            Worker.is_available.is_(True), Worker.is_approved.is_(True),
            or_(Worker.location.ilike(f"%{q}%"), Worker.bio.ilike(f"%{q}%"))
        ).all()
        workers += Worker.query.join(Worker.user).filter(
            Worker.is_available.is_(True), Worker.is_approved.is_(True),
            Worker.user.has(name=q)
        ).all()
    return render_template("search.html", q=q, services=services, workers=list({w.id: w for w in workers}.values()))
