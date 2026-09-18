from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.service import Service
from models.worker import Worker
from models.worker_service import WorkerService
from models.booking import Booking
from models.review import Review
from models.extra_features import Notification, BookingExtra
from models.advanced import AvailabilitySchedule, WorkerEarning, Payment, new_otp

worker_bp = Blueprint('worker', __name__)

def worker_required():
    return current_user.is_authenticated and current_user.is_worker and current_user.worker_profile

def log_notify(title, message, user_id=None):
    db.session.add(Notification(user_id=user_id or current_user.id, title=title, message=message))

@worker_bp.before_request
def check_worker():
    if not worker_required():
        return redirect(url_for('auth.login'))

@worker_bp.route('/dashboard')
def dashboard():
    worker = current_user.worker_profile
    bookings = Booking.query.filter_by(worker_id=worker.id).order_by(Booking.created_at.desc()).limit(8).all()
    completed = Booking.query.filter_by(worker_id=worker.id, status='completed').count()
    pending = Booking.query.filter_by(worker_id=worker.id, status='pending').count()
    earnings = sum(x.net_amount for x in WorkerEarning.query.filter_by(worker_id=worker.id).all())
    reviews = Review.query.filter_by(worker_id=worker.id).order_by(Review.created_at.desc()).all()
    return render_template('worker/dashboard.html', worker=worker, bookings=bookings, completed=completed,
                           pending=pending, earnings=earnings, reviews=reviews[:5])

@worker_bp.route('/toggle-availability', methods=['POST'])
def toggle_availability():
    worker = current_user.worker_profile
    worker.is_available = request.form.get('is_available') == '1'
    db.session.commit()
    flash('Online status updated.', 'success')
    return redirect(request.referrer or url_for('worker.dashboard'))

@worker_bp.route('/earnings')
def earnings():
    worker = current_user.worker_profile
    items = WorkerEarning.query.filter_by(worker_id=worker.id).order_by(WorkerEarning.created_at.desc()).all()
    gross = sum(x.gross_amount for x in items)
    commission = sum(x.commission_amount for x in items)
    net = sum(x.net_amount for x in items)
    return render_template('worker/earnings.html', earnings=items, gross=gross, commission=commission, net=net)

@worker_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    worker = current_user.worker_profile
    if request.method == 'POST':
        current_user.name = request.form.get('name', '').strip() or current_user.name
        current_user.phone = request.form.get('phone', '').strip()
        worker.location = request.form.get('location', '').strip()
        worker.bio = request.form.get('bio', '').strip()
        worker.experience = max(0, int(request.form.get('experience', 0) or 0))
        worker.hourly_rate = max(0, float(request.form.get('hourly_rate', 0) or 0))
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('worker.profile'))
    return render_template('worker/profile.html', worker=worker)

@worker_bp.route('/services', methods=['GET', 'POST'])
def services():
    worker = current_user.worker_profile
    all_services = Service.query.filter_by(is_active=True).order_by(Service.name.asc()).all()
    selected = {x.service_id for x in worker.service_links}
    if request.method == 'POST':
        chosen = {int(x) for x in request.form.getlist('service_ids') if x.isdigit()}
        for link in list(worker.service_links):
            if link.service_id not in chosen: db.session.delete(link)
        for sid in chosen:
            if sid not in selected: db.session.add(WorkerService(worker_id=worker.id, service_id=sid))
        db.session.commit(); flash('Your services were updated.', 'success')
        return redirect(url_for('worker.services'))
    return render_template('worker/services.html', worker=worker, services=all_services, selected=selected)

@worker_bp.route('/schedule', methods=['GET', 'POST'])
def schedule():
    worker = current_user.worker_profile
    if request.method == 'POST':
        for day in range(7):
            row = AvailabilitySchedule.query.filter_by(worker_id=worker.id, weekday=day).first()
            if not row:
                row = AvailabilitySchedule(worker_id=worker.id, weekday=day); db.session.add(row)
            row.is_enabled = request.form.get(f'enabled_{day}') == 'on'
            row.start_time = request.form.get(f'start_{day}', '09:00')[:5]
            row.end_time = request.form.get(f'end_{day}', '18:00')[:5]
        db.session.commit(); flash('Availability schedule saved.', 'success')
        return redirect(url_for('worker.schedule'))
    rows = {r.weekday:r for r in AvailabilitySchedule.query.filter_by(worker_id=worker.id).all()}
    return render_template('worker/schedule.html', rows=rows)

@worker_bp.route('/reviews')
def reviews():
    worker = current_user.worker_profile
    items = Review.query.filter_by(worker_id=worker.id).order_by(Review.created_at.desc()).all()
    avg = worker.average_rating
    return render_template('worker/reviews.html', worker=worker, reviews=items, average=avg)

@worker_bp.route('/location', methods=['GET', 'POST'])
def location():
    worker = current_user.worker_profile
    if request.method == 'POST':
        worker.location = request.form.get('location', '').strip() or worker.location
        db.session.commit(); flash('Location updated.', 'success')
        return redirect(url_for('worker.location'))
    return render_template('worker/location.html', worker=worker)

@worker_bp.route('/bookings')
def bookings():
    worker = current_user.worker_profile
    bookings = Booking.query.filter_by(worker_id=worker.id).order_by(Booking.created_at.desc()).all()
    return render_template('worker/bookings.html', worker=worker, bookings=bookings)

@worker_bp.route('/bookings/<int:booking_id>', methods=['GET', 'POST'])
def booking_detail(booking_id):
    worker = current_user.worker_profile
    booking = Booking.query.filter_by(id=booking_id, worker_id=worker.id).first_or_404()
    if request.method == 'POST':
        status = request.form.get('status')
        if status in {'accepted','rejected','in_progress','arrived','completed'}:
            if status == 'completed':
                extra = BookingExtra.query.filter_by(booking_id=booking.id).first()
                if not extra or not extra.completion_otp_verified:
                    flash('Customer OTP verification is required before completion.', 'warning')
                    return redirect(url_for('worker.booking_detail', booking_id=booking.id))
                booking.progress_percent = 100
                booking.estimated_minutes = 0
            else:
                booking.status = status
                if status == 'accepted' and booking.progress_percent < 10: booking.progress_percent = 10
                if status == 'in_progress' and booking.progress_percent < 25: booking.progress_percent = 25
                if status == 'arrived': booking.progress_percent = max(booking.progress_percent, 75)
            if status == 'completed': booking.status = status
            try: booking.progress_percent = max(0,min(100,int(request.form.get('progress_percent', booking.progress_percent or 0)))) if status != 'completed' else 100
            except (TypeError,ValueError): pass
            try: booking.estimated_minutes = max(0,int(request.form.get('estimated_minutes', booking.estimated_minutes or 0)))
            except (TypeError,ValueError): pass
            if status == 'accepted': log_notify('Booking accepted', f'Worker accepted booking #{booking.id}.', booking.customer_id)
            elif status == 'rejected': log_notify('Booking declined', f'Worker declined booking #{booking.id}.', booking.customer_id)
            elif status in {'in_progress','arrived'}: log_notify('Booking update', f'Booking #{booking.id} is now {status.replace("_"," ")}.', booking.customer_id)
            elif status == 'completed':
                gross = max(0, booking.price or 0); commission = round(gross * 0.10, 2)
                import uuid
                if not Payment.query.filter_by(booking_id=booking.id).first():
                        db.session.add(Payment(booking_id=booking.id, customer_id=booking.customer_id, worker_id=worker.id, amount=gross, commission_amount=commission, worker_amount=round(gross-commission,2), method='Razorpay', status='pending', transaction_id='DFS-PENDING-'+uuid.uuid4().hex[:12].upper()))
                log_notify('Job completed', f'Booking #{booking.id} has been completed.', booking.customer_id)
            db.session.commit(); flash('Booking status updated.', 'success')
        return redirect(url_for('worker.booking_detail', booking_id=booking.id))
    extra = BookingExtra.query.filter_by(booking_id=booking.id).first()
    return render_template('worker/booking_detail.html', booking=booking, worker=worker, extra=extra)

@worker_bp.route('/bookings/<int:booking_id>/request-otp', methods=['POST'])
def request_completion_otp(booking_id):
    worker=current_user.worker_profile
    booking=Booking.query.filter_by(id=booking_id, worker_id=worker.id).first_or_404()
    code=new_otp(); extra=BookingExtra.query.filter_by(booking_id=booking.id).first() or BookingExtra(booking_id=booking.id)
    extra.completion_otp=code; extra.completion_otp_verified=False; db.session.add(extra)
    log_notify('Completion OTP', f'Your job completion OTP for booking #{booking.id} is {code}. Share it with your worker when the work is complete.', booking.customer_id)
    db.session.commit(); flash('OTP generated and sent to the customer notification center.', 'success')
    return redirect(url_for('worker.booking_detail', booking_id=booking.id))
