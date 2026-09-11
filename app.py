import os
from flask import Flask, render_template, send_from_directory
from extensions import db, login_manager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dial-for-service-development-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "database.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "uploads")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["PUBLIC_BASE_URL"] = os.environ.get("PUBLIC_BASE_URL", "http://127.0.0.1:5000")
app.config["TWILIO_ACCOUNT_SID"] = os.environ.get("TWILIO_ACCOUNT_SID")
app.config["TWILIO_AUTH_TOKEN"] = os.environ.get("TWILIO_AUTH_TOKEN")
app.config["TWILIO_FROM_NUMBER"] = os.environ.get("TWILIO_FROM_NUMBER")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "profiles"), exist_ok=True)
os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "services"), exist_ok=True)

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Please login to continue."

@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None

from models.user import User
from models.service import Service
from models.worker import Worker
from models.worker_service import WorkerService
from models.booking import Booking
from models.review import Review

from routes.main import main_bp
from routes.auth import auth_bp
from routes.worker import worker_bp
from routes.booking import booking_bp
from routes.admin import admin_bp

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(worker_bp, url_prefix="/worker")
app.register_blueprint(booking_bp, url_prefix="/booking")
app.register_blueprint(admin_bp, url_prefix="/admin")

def repair_sqlite_schema():
    """Add columns that may be missing from an older database without deleting data."""
    required = {
        "services": {
            "slug": "VARCHAR(150)",
            "image": "VARCHAR(255)",
            "updated_at": "DATETIME",
            "is_active": "BOOLEAN",
        },
        "users": {
            "location": "VARCHAR(255)",
            "profile_image": "VARCHAR(255)",
            "is_active": "BOOLEAN",
            "created_at": "DATETIME",
        },
        "workers": {
            "bio": "TEXT",
            "location": "VARCHAR(255)",
            "experience": "INTEGER",
            "hourly_rate": "FLOAT",
            "is_available": "BOOLEAN",
            "is_approved": "BOOLEAN",
            "profile_image": "VARCHAR(255)",
            "created_at": "DATETIME",
            "updated_at": "DATETIME",
        },
        "bookings": {
            "action_token": "VARCHAR(255)",
            "address": "VARCHAR(255)",
            "latitude": "FLOAT",
            "longitude": "FLOAT",
            "description": "TEXT",
            "scheduled_at": "DATETIME",
            "price": "FLOAT",
            "progress_percent": "INTEGER",
            "estimated_minutes": "INTEGER",
            "created_at": "DATETIME",
            "updated_at": "DATETIME",
        },
        "reviews": {
            "created_at": "DATETIME",
            "updated_at": "DATETIME",
        },
    }

    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    for table, columns in required.items():
        if table not in inspector.get_table_names():
            continue
        existing = {c["name"] for c in inspector.get_columns(table)}
        for name, sql_type in columns.items():
            if name not in existing:
                if db.engine.dialect.name == "postgresql":
                    db.session.execute(text(
                        f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "{name}" {sql_type}'
                    ))
                else:
                    db.session.execute(text(
                        f'ALTER TABLE "{table}" ADD COLUMN "{name}" {sql_type}'
                    ))
    db.session.commit()

def ensure_admin_from_environment():
    """Create or update the site admin from Render environment variables.

    Set ADMIN_EMAIL and ADMIN_PASSWORD in the hosting environment. The password is
    never stored in source code; it is hashed before being saved to the database.
    If ADMIN_PASSWORD is not set, no admin is created or modified.
    """
    admin_password = os.environ.get("ADMIN_PASSWORD", "").strip()
    if not admin_password:
        return

    admin_email = os.environ.get("ADMIN_EMAIL", "admin@dailforhelp.com").strip().lower()
    admin_name = os.environ.get("ADMIN_NAME", "Administrator").strip() or "Administrator"
    if not admin_email:
        return

    user = User.query.filter_by(email=admin_email).first()
    if user is None:
        user = User(
            name=admin_name,
            email=admin_email,
            role="admin",
            is_active=True,
        )
        db.session.add(user)
    else:
        user.name = admin_name
        user.role = "admin"
        user.is_active = True

    user.set_password(admin_password)
    db.session.commit()
    print(f"Admin account ready: {admin_email}")


with app.app_context():
    db.create_all()
    repair_sqlite_schema()
    ensure_admin_from_environment()

    # Seed useful service categories on a fresh install. No workers are ever created automatically.
    if Service.query.count() == 0:
        default_services = [
            ("Plumbing", "Pipe leaks, taps, drainage and plumbing repairs.", "🔧"),
            ("Electrical", "Wiring, switches, fans, lights and electrical repairs.", "⚡"),
            ("Cleaning", "Home, office and deep-cleaning services.", "🧹"),
            ("AC Repair", "AC servicing, installation and repair.", "❄️"),
            ("Appliance Repair", "Repair help for common home appliances.", "🔌"),
            ("Painting", "Interior and exterior painting services.", "🎨"),
            ("Carpentry", "Furniture repair, doors, shelves and woodwork.", "🪚"),
            ("Computer Repair", "Laptop, desktop, software and basic IT support.", "💻"),
        ]
        for name, description, icon in default_services:
            db.session.add(Service(name=name, slug=name.lower().replace(" ", "-"), description=description, icon=icon, is_active=True))
        db.session.commit()

@app.context_processor
def inject_site_data():
    return {
        "site_name": "DIAL FOR SERVICE",
    }


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html"), 404

@app.errorhandler(500)
def internal_server_error(error):
    db.session.rollback()
    return render_template("errors/500.html"), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
