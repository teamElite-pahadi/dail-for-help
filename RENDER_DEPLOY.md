# DIAL FOR SERVICE — Render Deploy

This build is **PAYMENTS + EARNINGS V3**. It removes the old Favorites navigation and adds:
- Customer Payments & History
- Worker Payments & Earnings
- Admin Payments & Revenue
- 10% platform commission calculation

## Git push
```powershell
cd "C:\path\to\DIAL_FOR_SERVICE_PAYMENT_EARNINGS_RENDER_READY_V3"
& "C:\Program Files\Git\cmd\git.exe" init
& "C:\Program Files\Git\cmd\git.exe" remote set-url origin https://github.com/teamElite-pahadi/dail-for-help.git
& "C:\Program Files\Git\cmd\git.exe" add .
& "C:\Program Files\Git\cmd\git.exe" commit -m "DIAL FOR SERVICE payments earnings V3"
& "C:\Program Files\Git\cmd\git.exe" branch -M main
& "C:\Program Files\Git\cmd\git.exe" push -u origin main --force
```

After push, in Render choose **Manual Deploy → Deploy latest commit** if Auto Deploy is disabled.
