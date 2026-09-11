from datetime import datetime
from extensions import db

class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(
        db.Integer, db.ForeignKey("bookings.id", ondelete="CASCADE"),
        unique=True, nullable=False
    )
    customer_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    worker_id = db.Column(
        db.Integer, db.ForeignKey("workers.id", ondelete="CASCADE"),
        nullable=False
    )
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    booking = db.relationship("Booking", back_populates="review")
    customer = db.relationship("User", foreign_keys=[customer_id], back_populates="reviews_given")
    worker = db.relationship("Worker", foreign_keys=[worker_id], back_populates="reviews_received")

    def set_rating(self, rating):
        rating = int(rating)
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5.")
        self.rating = rating

    @property
    def stars(self):
        return "★" * self.rating + "☆" * (5 - self.rating)

    @property
    def rating_text(self):
        return {
            1: "Very Poor", 2: "Poor", 3: "Average",
            4: "Good", 5: "Excellent"
        }.get(self.rating, "")

    def __repr__(self):
        return f"<Review {self.id}: {self.rating}/5>"
