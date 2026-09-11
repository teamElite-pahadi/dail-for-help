# Admin Login Fixed

The public portal now shows Customer, Worker, and Administrator choices together.
A separate Admin Login link is also available in the guest navigation/footer.
The existing `/auth/login?role=admin` route and admin blueprint are preserved.
Customer and worker registration still require profile photos and workers must select at least one service.
No database reset/delete is performed by these changes.
