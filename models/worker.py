from datetime import datetime
from extensions import db

class Worker(db.Model):
    __tablename__ = "workers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    bio = db.Column(db.Text)
    location = db.Column(db.String(255))
    experience = db.Column(db.Integer, default=0)
    hourly_rate = db.Column(db.Float, default=0)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    profile_image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="worker_profile")
    service_links = db.relationship("WorkerService", back_populates="worker", cascade="all, delete-orphan")
    bookings = db.relationship("Booking", back_populates="worker", foreign_keys="Booking.worker_id")
    reviews_received = db.relationship("Review", back_populates="worker", foreign_keys="Review.worker_id")

    @property
    def display_name(self):
        return self.user.name if self.user else "Worker"

    @property
    def average_rating(self):
        ratings = [r.rating for r in self.reviews_received if r.rating]
        return round(sum(ratings) / len(ratings), 1) if ratings else 0

    @property
    def review_count(self):
        return len([r for r in self.reviews_received if r.rating])

    def __repr__(self):
        return f"<Worker {self.id}>"
