from datetime import datetime
from extensions import db

class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(150), unique=True, index=True)
    description = db.Column(db.Text)
    icon = db.Column(db.String(20), default="🔧")
    image = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    worker_links = db.relationship(
        "WorkerService", back_populates="service",
        cascade="all, delete-orphan"
    )
    bookings = db.relationship("Booking", back_populates="service")

    def __repr__(self):
        return f"<Service {self.name}>"
