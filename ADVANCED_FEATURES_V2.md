# DIAL FOR SERVICE — V2 Advanced Features

This package upgrades the existing Flask project with working, database-backed flows.

## Implemented
- Worker Online/Offline toggle
- Weekly availability schedule
- Worker customer reviews dashboard
- Admin verification badge controls
- Worker location/locality update
- Admin analytics: booking status, revenue, commission, top services/workers
- Complaint/support ticket creation and admin resolution
- Admin activity/audit log
- Google Maps directions from booking coordinates
- Rule-based AI service assistant (no external AI key required)
- Smart worker matching using service, availability, locality, rating and experience
- Customer OTP verification before worker can complete a job
- Optional completion proof upload
- Referral code + starter loyalty points
- Multiple saved customer addresses
- English/Hindi switch for the navigation preference
- Dark/Light mode using local browser storage
- PWA manifest + service worker for installable/offline shell

## External configuration
- Google Maps directions use Google Maps web URLs; no API key is required for the directions link.
- Real SMS/WhatsApp OTP or push notifications still require an external provider such as Twilio and production credentials.
- The assistant is rule-based. A real LLM assistant requires an AI API key/provider.
- PWA installation support depends on HTTPS/hosting/browser requirements.

## Safety/data behavior
- No dummy workers are seeded.
- Worker registration still requires selecting one or more services and admin approval controls visibility.
- Profile photo upload functionality remains removed.
- Existing data is preserved; startup schema repair adds missing columns where possible.
