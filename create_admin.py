import argparse
from app import app, db
from models.user import User

def main():
    parser = argparse.ArgumentParser(description="Create or reset a DIAL FOR SERVICE admin account.")
    parser.add_argument("--email")
    parser.add_argument("--name", default="Administrator")
    parser.add_argument("--password")
    args = parser.parse_args()
    email = (args.email or input("Admin email: ")).strip().lower()
    name = (args.name or input("Admin name: ")).strip() or "Administrator"
    password = args.password or input("Admin password: ")
    if not email or not password:
        raise SystemExit("Email and password are required.")
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user is None:
            user = User(name=name, email=email, role="admin", is_active=True)
            user.set_password(password)
            db.session.add(user)
            action = "created"
        else:
            user.name = name
            user.role = "admin"
            user.is_active = True
            user.set_password(password)
            action = "reset"
        db.session.commit()
        print(f"Admin {action}: {user.email}")
        print("Role:", user.role)
        print("Active:", user.is_active)

if __name__ == "__main__":
    main()
