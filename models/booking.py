from datetime import datetime
from extensions import db

class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id", ondelete="CASCADE"), nullable=False)

    status = db.Column(db.String(30), default="pending", nullable=False)
    action_token = db.Column(db.String(255), unique=True, index=True)
    address = db.Column(db.String(255))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    description = db.Column(db.Text)
    scheduled_at = db.Column(db.DateTime)
    price = db.Column(db.Float, default=0)
    progress_percent = db.Column(db.Integer, default=0, nullable=False)
    estimated_minutes = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    customer = db.relationship(
        "User", foreign_keys=[customer_id], back_populates="customer_bookings"
    )
    worker = db.relationship(
        "Worker", foreign_keys=[worker_id], back_populates="bookings"
    )
    service = db.relationship("Service", back_populates="bookings")
    review = db.relationship(
        "Review", back_populates="booking", uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Booking {self.id} {self.status}>"
