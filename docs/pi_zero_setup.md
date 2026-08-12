# Raspberry Pi Zero 2 W Setup & Operational Guide

This document provides step-by-step instructions for deploying and managing the **Sea Retreat Monthly P&L & Melio Invoice Automation** and the **Daily Health Check Daemon** on a Raspberry Pi Zero 2 W.

---

## 1. Network & Device Information

- **Device:** Raspberry Pi Zero 2 W
- **IP Address:** `192.168.68.90`
- **Default User:** `pi`
- **Target Installation Directory:** `/home/pi/searetreat_gemini`

---

## 2. Initial SSH Setup & Repository Cloning

1. Connect to your Pi Zero 2 W over SSH:
   ```bash
   ssh pi@192.168.68.90
   ```

2. Clone the repository to `/home/pi/searetreat_gemini`:
   ```bash
   git clone https://github.com/your-username/searetreat_gemini.git /home/pi/searetreat_gemini
   cd /home/pi/searetreat_gemini
   ```

---

## 3. Environment & System Provisioning

1. Make the setup script executable and run it:
   ```bash
   chmod +x scripts/setup_pi.sh
   ./scripts/setup_pi.sh
   ```

2. Edit `.env` with your actual credentials:
   ```bash
   nano .env
   ```
   Ensure the following environment variables are filled out:
   ```ini
   HOSPITABLE_PAT=your_actual_hospitable_pat
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=searetreatpa@gmail.com
   SMTP_PASS=your_gmail_app_password
   OWNER_EMAIL=searetreatpa@gmail.com
   ```
   Restrict file permissions for security:
   ```bash
   chmod 600 .env
   ```

---

## 4. Enabling Systemd Timers

Enable and start both the monthly automation and daily health check timers:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now searetreat-automation.timer
sudo systemctl enable --now searetreat-healthcheck.timer
```

Verify that the timers are active:
```bash
systemctl list-timers searetreat*
```
*Expected Schedules:*
- Monthly Automation: Next trigger on the 2nd of the month at `06:00:00`.
- Daily Health Check: Next trigger every day at `08:00:00`.

---

## 5. Testing & Manual Execution

To perform immediate manual test runs:
```bash
# Test manual monthly pipeline dry run
.venv/bin/python src/monthly_automation.py --month 2026-07 --no-email

# Test daily health check daemon manually
.venv/bin/python src/daily_health_check.py

# Test triggering full systemd services directly
sudo systemctl start searetreat-automation.service
sudo systemctl start searetreat-healthcheck.service
```

---

## 6. Log Monitoring & Troubleshooting

- **View Live Journalctl Logs:**
  ```bash
  journalctl -u searetreat-automation -f
  journalctl -u searetreat-healthcheck -f
  ```

- **View Execution File Logs:**
  ```bash
  cat /home/pi/searetreat_gemini/logs/monthly_automation.log
  cat /home/pi/searetreat_gemini/logs/daily_healthcheck.log
  ```

- **View Health Trend History JSON:**
  ```bash
  cat /home/pi/searetreat_gemini/logs/health_history.json
  ```
