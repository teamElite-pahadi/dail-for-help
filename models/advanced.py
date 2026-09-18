from datetime import datetime
import secrets
from extensions import db

class AvailabilitySchedule(db.Model):
    __tablename__ = 'availability_schedules'
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey('workers.id', ondelete='CASCADE'), nullable=False)
    weekday = db.Column(db.Integer, nullable=False)  # 0 Monday
    start_time = db.Column(db.String(5), default='09:00', nullable=False)
    end_time = db.Column(db.String(5), default='18:00', nullable=False)
    is_enabled = db.Column(db.Boolean, default=True, nullable=False)
    worker = db.relationship('Worker', backref=db.backref('availability_schedule', cascade='all, delete-orphan'))
    __table_args__ = (db.UniqueConstraint('worker_id', 'weekday', name='uq_worker_weekday'),)

class Complaint(db.Model):
    __tablename__ = 'complaints'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='SET NULL'))
    subject = db.Column(db.String(180), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default='open', nullable=False)
    admin_reply = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    user = db.relationship('User', backref=db.backref('complaints', cascade='all, delete-orphan'))
    booking = db.relationship('Booking', backref=db.backref('complaints', lazy=True))

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    action = db.Column(db.String(180), nullable=False)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship('User')

class Address(db.Model):
    __tablename__ = 'addresses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    label = db.Column(db.String(50), default='Home', nullable=False)
    address = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship('User', backref=db.backref('addresses', cascade='all, delete-orphan'))

class Referral(db.Model):
    __tablename__ = 'referrals'
    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    referred_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    reward_points = db.Column(db.Integer, default=100, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    referrer = db.relationship('User', foreign_keys=[referrer_id])
    referred = db.relationship('User', foreign_keys=[referred_id])


class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey('workers.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Float, default=0, nullable=False)
    commission_amount = db.Column(db.Float, default=0, nullable=False)
    worker_amount = db.Column(db.Float, default=0, nullable=False)
    method = db.Column(db.String(40), default='Razorpay', nullable=False)
    status = db.Column(db.String(30), default='pending', nullable=False)
    transaction_id = db.Column(db.String(80), unique=True, nullable=False)
    razorpay_order_id = db.Column(db.String(80), unique=True)
    razorpay_payment_id = db.Column(db.String(80), unique=True)
    razorpay_signature = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    booking = db.relationship('Booking', backref=db.backref('payment', uselist=False))
    customer = db.relationship('User', foreign_keys=[customer_id])
    worker = db.relationship('Worker', foreign_keys=[worker_id])

class WorkerEarning(db.Model):
    __tablename__ = 'worker_earnings'
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey('workers.id', ondelete='CASCADE'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), unique=True, nullable=False)
    gross_amount = db.Column(db.Float, default=0, nullable=False)
    commission_amount = db.Column(db.Float, default=0, nullable=False)
    net_amount = db.Column(db.Float, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    worker = db.relationship('Worker')
    booking = db.relationship('Booking')

# Helpers for booking completion flow.
def new_otp():
    return f'{secrets.randbelow(10000):04d}'
