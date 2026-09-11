# DIAL FOR SERVICE - ADVANCED FEATURES UPGRADE

Included in this upgrade package:
1. Nearby worker ranking helper using Haversine distance.
2. Professional booking tracker stage definitions:
   Requested -> Accepted -> On The Way -> Arrived -> Working -> Completed.
3. ETA formatting helper.
4. Notification message helper for every booking state.
5. Dashboard booking statistics helper.
6. Reusable responsive booking-tracker Jinja macro + CSS.
7. Migration notes for the database fields required for GPS, ETA, availability and notifications.

## Important integration
The existing project may have different model field names. The migration notes deliberately do
not overwrite those models blindly. Add the listed nullable fields to the current Booking/Worker
models, then connect the helpers to the existing routes/templates.

## Feature behavior
- Customer location is private to the booking/assigned worker.
- Nearby matching sorts approved/available workers by distance.
- Worker availability controls who can be shown as available.
- Worker updates the booking stage and progress.
- Customer sees current stage, percentage and ETA.
- Notification records can be displayed in the customer/worker dashboards.
- Admin dashboard can use dashboard_stats() for operational counters.

## Payment
No payment gateway is added; the requested feature set did not require payments.
