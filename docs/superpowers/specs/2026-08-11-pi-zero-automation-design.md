# Design Specification: Sea Retreat Automation on Raspberry Pi Zero 2 W

**Date:** 2026-08-11  
**Status:** Approved  
**Target Device:** Raspberry Pi Zero 2 W (`192.168.68.90`)  
**Repository Location:** `C:\Users\lucas\source\repos\searetreat_gemini` (Remote target: `/home/pi/searetreat_gemini`)

---

## 1. Executive Summary

This design specification details the architecture, configuration, failure recovery, and deployment procedure for running the **Sea Retreat P&L & Melio Monthly Automation** as a headless, automated background task on a Raspberry Pi Zero 2 W.

The system will execute on the **2nd of every month at 06:00 AM local time** using native Linux `systemd` service and timer units. It includes isolated virtual environment setup, persistent execution catching (recovers missed runs after power loss), structured system logging via `journalctl`, and automatic failure email dispatch to `OWNER_EMAIL`.

---

## 2. Hardware & Network Parameters

- **Hardware:** Raspberry Pi Zero 2 W (Quad-core ARMv7/ARM64)
- **Local IP Address:** `192.168.68.90`
- **Default SSH User:** `pi` (or user default on target host)
- **Remote Repo Path:** `/home/pi/searetreat_gemini`
- **Python Runtime:** Python 3.11+ in isolated `.venv` (`/home/pi/searetreat_gemini/.venv`)

---

## 3. Architecture & Components

```
┌─────────────────────────────────────────────────────────────┐
│                 Raspberry Pi Zero 2 W                       │
│                     (192.168.68.90)                         │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ systemd timer (searetreat-automation.timer)        │   │
│   │ Schedule: *-*-02 06:00:00 (Persistent=true)        │   │
│   └─────────────────────────┬───────────────────────────┘   │
│                             │ Triggers                       │
│                             ▼                               │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ systemd service (searetreat-automation.service)    │   │
│   │ Runs: .venv/bin/python src/monthly_automation.py    │   │
│   └─────────────────────────┬───────────────────────────┘   │
│                             │                               │
│        ┌────────────────────┴───────────────────┐           │
│        ▼                                       ▼           │
│   ┌───────────────┐                   ┌────────────────┐  │
│   │ Hospitable    │                   │ Email Dispatch │  │
│   │ API           │                   │ (Melio & Owner)│  │
│   └───────────────┘                   └────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Component Details:

1. **`scripts/setup_pi.sh` (Automated Provisioning Script)**
   - Installs system packages (`python3-venv`, `python3-pip`).
   - Builds `.venv` virtual environment.
   - Installs Python dependencies (`requirements.txt`).
   - Creates required directories (`logs/`, `722 Milwaukee/`).
   - Installs systemd service & timer files to `/etc/systemd/system/`.

2. **`systemd/searetreat-automation.service` (Systemd Service Unit)**
   - Invokes `/home/pi/searetreat_gemini/.venv/bin/python /home/pi/searetreat_gemini/src/monthly_automation.py`.
   - Reads environment configuration from `/home/pi/searetreat_gemini/.env`.
   - Standard output and standard error piped to `journalctl` and `logs/monthly_automation.log`.

3. **`systemd/searetreat-automation.timer` (Systemd Timer Unit)**
   - Scheduled for `OnCalendar=*-*-02 06:00:00`.
   - Configured with `Persistent=true` so if the Pi Zero was powered off during the scheduled time, `systemd` triggers the job immediately upon boot.

4. **Failure Notification System (`src/monthly_automation.py`)**
   - Wrapped in top-level `try...except` handling.
   - If execution fails due to API errors, missing credentials, network disconnect, or file IO issues, an urgent notification email is generated and sent to `OWNER_EMAIL` (`searetreatpa@gmail.com`) with failure details and recent log output.

5. **Setup Documentation (`docs/pi_zero_setup.md`)**
   - Step-by-step instructions for SSH access to `192.168.68.90`, cloning, script execution, systemd activation, and log inspection commands.

---

## 5. Verification Plan

1. **Local Virtualenv Test:** Run `scripts/setup_pi.sh` on Pi Zero (`192.168.68.90`) and confirm `.venv` builds cleanly.
2. **Dry Run Command:** Run `.venv/bin/python src/monthly_automation.py --month 2026-07 --no-email` to verify API fetching and PDF generation on Linux/ARM.
3. **Systemd Service Test:** Trigger manual service run: `sudo systemctl start searetreat-automation.service`.
4. **Log Inspection:** Verify logs via `journalctl -u searetreat-automation.service -n 50`.
5. **Systemd Timer Activation:** Enable timer: `sudo systemctl enable --now searetreat-automation.timer` and verify active state via `systemctl list-timers`.

---

## 6. Self-Review Checklist

- [x] Hardware IP explicitly defined (`192.168.68.90`).
- [x] Systemd timer handles offline catch-up via `Persistent=true`.
- [x] Virtual environment isolation prevents Python version issues on Pi OS.
- [x] Clear failure alerting procedure specified.
- [x] All paths and commands formatted cleanly for copy-paste deployment.
