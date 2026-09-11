# DIAL FOR SERVICE — Complete Flask Website

A complete local-services marketplace built with Flask, SQLAlchemy and Flask-Login.

## Included features

- Responsive home page with dynamic service cards
- Services page and service detail pages
- Available worker listing per service
- Customer registration/login/logout
- Worker registration/login/logout
- Worker must select at least one service during registration
- Worker profile and service management
- Admin approval required before a worker becomes publicly visible
- Customer booking/request flow
- Worker booking status management
- Customer reviews after completed bookings
- Service/workers search
- Admin dashboard
- Admin service add/edit/show/hide
- Admin worker approval/hide
- Admin customers, bookings and reviews pages
- Automatic SQLite schema repair for common columns from older versions
- Fresh installation automatically creates useful service categories; no dummy workers are created

## Windows setup

```powershell
cd C:\path\to\dail_for_help_complete
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Create admin account

The easiest method is:

```powershell
python create_admin.py
```

Enter your admin email, name and password. Then open the site and login. The navigation will show **⚙ Admin Panel** and `/admin/` redirects to the dashboard.

## Existing database

If you are replacing an older project, make a backup of `database.db` first. This version automatically adds common missing columns such as service `slug`, `image`, `updated_at`, and worker `is_approved` when the existing table is present.

Existing workers from an old database may need approval from **Admin → Workers** before they appear publicly.

If the old database has a fundamentally different schema, rename it to `database_backup.db` and start the app to create a clean database.

## Run

```powershell
python app.py
```

Do not run `python app.py` while you are inside the Python `>>>` shell. If you see `>>>`, first run `exit()`.


## New customer/admin entry flow
- Opening `/` shows Customer and Admin choices.
- Customers use customer login/register and see customer navigation only.
- Admin uses the Admin Login choice and manages workers, services, customers and bookings from Admin Panel.
- Workers can use the credentials created/approved by Admin on their own phone to open Worker Dashboard.

## Worker mobile SMS
Real SMS requires a provider. This project supports Twilio when these environment variables are set: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`, and `PUBLIC_BASE_URL` (a public HTTPS URL when the worker is using a phone outside the local PC).
Without these credentials, bookings still appear in Worker Dashboard and the app tells you SMS is not configured.
## Render admin setup

For the live Render deployment, add these Environment Variables:

- `ADMIN_EMAIL` — admin login email (for example `admin@dailforhelp.com`)
- `ADMIN_PASSWORD` — choose a strong private password; do not commit it to Git
- `ADMIN_NAME` — optional, defaults to `Administrator`

On startup the app creates the admin if it does not exist, or updates that account to the admin role and resets its password to `ADMIN_PASSWORD`. If `ADMIN_PASSWORD` is not set, the app does not change any admin account.

The Render start command is `gunicorn app:app`.



## New: Local worker matching and booking tracker
- Customers can enter their area/locality on a service page to prioritize workers from that area.
- Workers keep their service area in their profile; existing worker records remain intact.
- Booking progress (0–100%) and estimated remaining minutes can be updated by workers.
- Customers see a booking tracker and progress bar.
- Existing databases are preserved; the startup schema repair adds only missing columns.
