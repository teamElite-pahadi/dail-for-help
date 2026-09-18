"""
Optional database upgrade notes for Advanced Booking Features.

If your existing Booking model does not yet have these fields, add them to the
Booking SQLAlchemy model before running production:
    customer_latitude = db.Column(db.Float, nullable=True)
    customer_longitude = db.Column(db.Float, nullable=True)
    progress_percent = db.Column(db.Integer, nullable=False, default=0)
    estimated_minutes = db.Column(db.Integer, nullable=True)
    worker_arrival_at = db.Column(db.DateTime, nullable=True)

Recommended Worker fields:
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    availability_status = db.Column(db.String(20), nullable=False, default="available")

Recommended notification table:
    Notification(id, user_id, booking_id, title, message, is_read, created_at)

Recommended booking status values:
pending -> accepted -> on_the_way -> arrived -> in_progress -> completed
and cancelled as an alternate terminal state.
"""
