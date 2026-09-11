from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(30))
    location = db.Column(db.String(255))
    role = db.Column(db.String(20), nullable=False, default="customer")
    profile_image = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    worker_profile = db.relationship(
        "Worker", back_populates="user", uselist=False,
        cascade="all, delete-orphan"
    )
    customer_bookings = db.relationship(
        "Booking", foreign_keys="Booking.customer_id",
        back_populates="customer", cascade="all, delete-orphan"
    )
    reviews_given = db.relationship(
        "Review", foreign_keys="Review.customer_id",
        back_populates="customer", cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_customer(self):
        return self.role == "customer"

    @property
    def is_worker(self):
        return self.role == "worker"

    @property
    def is_admin(self):
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.email}>"
