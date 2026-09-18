# Render / PostgreSQL + Payment Fix

This build fixes the Render deployment crash caused by the schema-repair code using raw `DATETIME` in PostgreSQL `ALTER TABLE` statements.

## What was fixed
- Database schema repair now detects the active SQLAlchemy dialect.
- `DateTime` is compiled by SQLAlchemy, so SQLite receives `DATETIME` and PostgreSQL receives its supported timestamp type.
- Existing database data is preserved; no database reset or worker seeding was added.
- The `Booking.payment` relationship now points to the actual `Payment` model instead of the complaint relationship.
- Complaint-to-booking records use `Booking.complaints`, removing the relationship collision.
- Pending demo payment transaction IDs are unique.
- The existing demo payment flow remains test-only when Razorpay is not configured.

## Render
After pushing this build to GitHub, Render should redeploy automatically if the service is connected to the repository. The previous crash should no longer occur at `ALTER TABLE ... verified_at DATETIME`.
