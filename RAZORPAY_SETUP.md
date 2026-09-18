# DIAL FOR SERVICE — Real Online Payments

This version adds a real Razorpay checkout flow.

## Render Environment Variables

Set these in Render:

- `RAZORPAY_KEY_ID` = your Razorpay Key ID
- `RAZORPAY_KEY_SECRET` = your Razorpay Key Secret
- `PUBLIC_BASE_URL` = `https://dail-for-help.onrender.com`

Do not put the secret in source code or GitHub.

## Payment flow

1. Customer books a worker.
2. Worker accepts and completes the booking using the existing completion OTP flow.
3. A pending payment is created for the booking.
4. Customer opens Booking Details or Payments & History and clicks **Pay Now**.
5. Razorpay Checkout opens and supports the payment methods enabled on the Razorpay account.
6. The server verifies the Razorpay signature before marking the payment as paid.
7. Only after verified payment is the worker earning created: 10% platform commission and 90% worker net.
8. Customer gets the transaction/payment record in Payment History.

## Local test

Use Razorpay Test Mode keys first. Real money should only be enabled after the integration is tested.
