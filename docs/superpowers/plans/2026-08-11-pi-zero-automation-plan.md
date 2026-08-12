# Pi Zero 2 W Monthly Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, configure, and document the automated headless deployment of the Sea Retreat monthly P&L and Melio invoice pipeline on a Raspberry Pi Zero 2 W (`192.168.68.90`) using native systemd timer and service units with automated failure alerts and a daily end-to-end endpoint health monitor daemon.

**Architecture:** A systemd timer (`OnCalendar=*-*-02 06:00:00`, `Persistent=true`) triggers a systemd service executing `monthly_automation.py` in an isolated Python 3 virtual environment (`.venv`). Environment variables are loaded from `.env`. Errors are caught by a top-level alert handler that emails failure details to `OWNER_EMAIL`. In addition, a daily health check daemon (`src/daily_health_check.py` + `searetreat-healthcheck.timer` running daily at 08:00 AM) probes Hospitable API, SMTP server, and disk health, appending status to `logs/health_history.json` and sending a daily HTML email report with day-over-day status trends (`GREEN`, `YELLOW/ORANGE`, `RED`). An automated provisioning script `scripts/setup_pi.sh` builds the environment and installs both systemd units.

**Tech Stack:** Python 3, Bash, Linux `systemd` (Service & Timer), SMTP (smtplib), pytest.

## Global Constraints

- Device IP: `192.168.68.90`
- Target Remote Path: `/home/pi/searetreat_gemini`
- Python Virtualenv Path: `/home/pi/searetreat_gemini/.venv`
- Monthly Schedule: `OnCalendar=*-*-02 06:00:00`
- Daily Health Check Schedule: `OnCalendar=*-*-* 08:00:00`
- Catch-up Behavior: `Persistent=true`
- Notification Inbox: `searetreatpa@gmail.com` (`OWNER_EMAIL`)

---

### Task 1: Pipeline Failure Alert Handler (`src/alert_sender.py` & Exception Handler)

**Files:**
- Create: `src/alert_sender.py`
- Modify: `src/monthly_automation.py:59-111`
- Test: `tests/test_alert_sender.py`

**Interfaces:**
- Produces: `send_failure_alert(error_message: str, log_snippet: str = "") -> bool`

- [x] **Step 1: Write the failing test for `send_failure_alert`**
- [x] **Step 2: Run test to verify it fails**
- [x] **Step 3: Implement `src/alert_sender.py`**
- [x] **Step 4: Update `src/monthly_automation.py` with top-level try/except alert dispatch**
- [x] **Step 5: Run test to verify it passes**
- [x] **Step 6: Commit** (`9ac14cc`)

---

### Task 2: Create Systemd Service & Timer Unit Files

**Files:**
- Create: `systemd/searetreat-automation.service`
- Create: `systemd/searetreat-automation.timer`
- Test: `tests/test_systemd_files.py`

**Interfaces:**
- Systemd Service file format matching Debian/Raspberry Pi OS requirements.
- Systemd Timer configured for `OnCalendar=*-*-02 06:00:00` and `Persistent=true`.

- [x] **Step 1: Write verification test for Systemd files**
- [x] **Step 2: Run test to verify it fails**
- [x] **Step 3: Create `systemd/searetreat-automation.service`**
- [x] **Step 4: Create `systemd/searetreat-automation.timer`**
- [x] **Step 5: Run test to verify it passes**
- [x] **Step 6: Commit** (`6d56c6f`)

---

### Task 3: Create Automated Provisioning Script (`scripts/setup_pi.sh`)

**Files:**
- Create: `scripts/setup_pi.sh`
- Test: `tests/test_setup_script.py`

**Interfaces:**
- Executable bash script that sets up `.venv`, installs requirements, creates directories, and prepares systemd units.

- [ ] **Step 1: Write test for `scripts/setup_pi.sh` structure**

Create `tests/test_setup_script.py`:
```python
import os
import subprocess
import pytest

def test_setup_pi_script_exists_and_valid_bash():
    script_path = os.path.join("scripts", "setup_pi.sh")
    assert os.path.exists(script_path)
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "#!/usr/bin/env bash" in content
    assert "python3 -m venv .venv" in content
    assert "pip install" in content
    assert "searetreat-automation.service" in content
    assert "searetreat-healthcheck.service" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_setup_script.py -v`
Expected: FAIL with `AssertionError: assert False (path does not exist)`

- [ ] **Step 3: Create `scripts/setup_pi.sh`**

Create `scripts/setup_pi.sh`:
```bash
#!/usr/bin/env bash
# ==============================================================================
# Sea Retreat Raspberry Pi Zero 2 W Setup & Systemd Provisioning Script
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

echo "=== Sea Retreat Pi Zero 2 W Provisioning ==="
echo "Target Directory: $SCRIPT_DIR"

# 1. Update package list and install system dependencies
echo "[1/5] Checking system dependencies..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3-venv python3-pip python3-dev
fi

# 2. Setup Python virtual environment
echo "[2/5] Setting up Python 3 virtual environment (.venv)..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip -q
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q
fi

# 3. Create required output directories
echo "[3/5] Creating application directories..."
mkdir -p logs "722 Milwaukee"

# 4. Check for .env file
echo "[4/5] Checking environment configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "CREATED .env from .env.example. PLEASE EDIT .env WITH YOUR HOSPITABLE_PAT AND SMTP PASSWORDS!"
    else
        echo "WARNING: .env file missing. Please create .env before running automation."
    fi
else
    echo ".env file detected."
fi

# 5. Install systemd service and timer files
echo "[5/5] Installing systemd units..."
if [ -d "/etc/systemd/system" ]; then
    sudo cp systemd/searetreat-automation.service /etc/systemd/system/
    sudo cp systemd/searetreat-automation.timer /etc/systemd/system/
    if [ -f "systemd/searetreat-healthcheck.service" ]; then
        sudo cp systemd/searetreat-healthcheck.service /etc/systemd/system/
        sudo cp systemd/searetreat-healthcheck.timer /etc/systemd/system/
    fi
    sudo systemctl daemon-reload
    echo "Installed systemd units successfully."
    echo "To activate the timers, run:"
    echo "  sudo systemctl enable --now searetreat-automation.timer"
    echo "  sudo systemctl enable --now searetreat-healthcheck.timer"
else
    echo "Non-systemd environment detected. Manual copy to /etc/systemd/system required."
fi

echo "=== Provisioning Complete ==="
```

- [ ] **Step 4: Set execution permission and run test to verify it passes**

Run: `pytest tests/test_setup_script.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/setup_pi.sh tests/test_setup_script.py
git commit -m "feat: add Raspberry Pi Zero automated provisioning script setup_pi.sh"
```

---

### Task 4: Pi Zero Setup & Operational Documentation (`docs/pi_zero_setup.md`)

**Files:**
- Create: `docs/pi_zero_setup.md`
- Test: `tests/test_docs_exist.py`

**Interfaces:**
- Markdown documentation detailing initial SSH access, cloning, `.env` setup, timer enabling, log viewing, and troubleshooting.

- [ ] **Step 1: Write test for documentation presence**

Create `tests/test_docs_exist.py`:
```python
import os
import pytest

def test_pi_zero_setup_doc_exists():
    doc_path = os.path.join("docs", "pi_zero_setup.md")
    assert os.path.exists(doc_path)
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "192.168.68.90" in content
    assert "systemctl enable --now searetreat-automation.timer" in content
    assert "systemctl enable --now searetreat-healthcheck.timer" in content
    assert "journalctl -u searetreat-automation" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_docs_exist.py -v`
Expected: FAIL with `AssertionError: assert False (path does not exist)`

- [ ] **Step 3: Create `docs/pi_zero_setup.md`**

Create `docs/pi_zero_setup.md`:
```markdown
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_docs_exist.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add docs/pi_zero_setup.md tests/test_docs_exist.py
git commit -m "docs: add Raspberry Pi Zero setup and operational guide"
```

---

### Task 5: Daily End-to-End Health Check Daemon & Status Trend Reporter

**Files:**
- Create: `src/daily_health_check.py`
- Create: `systemd/searetreat-healthcheck.service`
- Create: `systemd/searetreat-healthcheck.timer`
- Test: `tests/test_daily_health_check.py`

**Interfaces:**
- Produces: `run_daily_health_check(send_email: bool = True) -> dict`

- [ ] **Step 1: Write failing test for `daily_health_check.py`**

Create `tests/test_daily_health_check.py`:
```python
import os
import json
import pytest
from unittest.mock import patch, MagicMock
from src.daily_health_check import check_hospitable_api, check_smtp_connection, check_system_storage, run_daily_health_check

def test_check_hospitable_api_success():
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.headers = {"X-RateLimit-Remaining": "100"}
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        
        status, details = check_hospitable_api("valid_pat")
        assert status == "GREEN"
        assert "200 OK" in details

def test_check_smtp_connection_success():
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        status, details = check_smtp_connection("smtp.gmail.com", 587, "user@gmail.com", "pass")
        assert status == "GREEN"

def test_run_daily_health_check_trend_recording(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    history_file = log_dir / "health_history.json"
    
    with patch("src.daily_health_check.HISTORY_FILE", str(history_file)):
        with patch("src.daily_health_check.check_hospitable_api", return_value=("GREEN", "OK")):
            with patch("src.daily_health_check.check_smtp_connection", return_value=("GREEN", "OK")):
                with patch("src.daily_health_check.check_system_storage", return_value=("GREEN", "Disk space OK")):
                    with patch("src.daily_health_check.dispatch_health_report_email", return_value=True):
                        res = run_daily_health_check(send_email=False)
                        assert res["overall_status"] == "GREEN"
                        assert os.path.exists(history_file)
                        with open(history_file) as f:
                            history = json.load(f)
                        assert len(history) == 1
                        assert history[0]["status"] == "GREEN"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_daily_health_check.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.daily_health_check'`

- [ ] **Step 3: Implement `src/daily_health_check.py`**

Create `src/daily_health_check.py`:
```python
import os
import sys
import json
import logging
import smtplib
import urllib.request
import urllib.parse
import shutil
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.hospitable_api import load_pat

HISTORY_FILE = os.path.join(ROOT_DIR, "logs", "health_history.json")

def check_hospitable_api(pat: str) -> tuple[str, str]:
    if not pat:
        return "RED", "HOSPITABLE_PAT missing in environment or .env"
    
    url = "https://public.api.hospitable.com/v2/properties"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {pat}",
        "Accept": "application/json",
        "User-Agent": "Python/3.11"
    })
    
    try:
        start_time = datetime.now()
        with urllib.request.urlopen(req, timeout=10) as resp:
            latency = (datetime.now() - start_time).total_seconds()
            code = resp.getcode()
            
            # Check warning headers or token format indicators
            token_status = "GREEN"
            warning_msg = f"HTTP {code} OK ({latency:.2f}s)"
            
            # If PAT is dummy or placeholder
            if "dummy" in pat.lower() or "your_" in pat.lower():
                return "ORANGE", "Warning: HOSPITABLE_PAT is a placeholder token."
            
            if latency > 5.0:
                return "YELLOW", f"Warning: High API latency ({latency:.2f}s)"
                
            return "GREEN", warning_msg
    except Exception as e:
        return "RED", f"API Connection Failed: {e}"

def check_smtp_connection(server_host: str, port: int, user: str, pass_word: str) -> tuple[str, str]:
    if not user or not pass_word:
        return "RED", "SMTP credentials missing in environment"
    try:
        with smtplib.SMTP(server_host, port, timeout=10) as server:
            server.starttls()
            server.login(user, pass_word)
        return "GREEN", "SMTP authentication successful"
    except Exception as e:
        return "RED", f"SMTP Auth Failed: {e}"

def check_system_storage() -> tuple[str, str]:
    try:
        total, used, free = shutil.disk_usage(ROOT_DIR)
        free_gb = free / (1024 ** 3)
        used_pct = (used / total) * 100
        if used_pct > 90:
            return "RED", f"Critical low disk space: {free_gb:.1f}GB free ({used_pct:.1f}% used)"
        elif used_pct > 80:
            return "YELLOW", f"Warning low disk space: {free_gb:.1f}GB free ({used_pct:.1f}% used)"
        return "GREEN", f"Disk space OK: {free_gb:.1f}GB free"
    except Exception as e:
        return "YELLOW", f"Disk check unavailable: {e}"

def dispatch_health_report_email(overall_status: str, results: dict, history: list) -> bool:
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")
    owner_email = os.getenv("OWNER_EMAIL", "searetreatpa@gmail.com")

    if not smtp_user or not smtp_pass:
        logging.error("Cannot send health report: SMTP credentials unconfigured.")
        return False

    status_icon = "🟢" if overall_status == "GREEN" else ("🟧" if overall_status in ("YELLOW", "ORANGE") else "🔴")
    subject = f"{status_icon} Daily Health Report - Sea Retreat Automation [{overall_status}]"

    # Render day-over-day trend row (last 7 days)
    trend_icons = []
    for entry in history[-7:]:
        st = entry.get("status", "GREEN")
        trend_icons.append("🟢" if st == "GREEN" else ("🟧" if st in ("YELLOW", "ORANGE") else "🔴"))
    trend_str = " ".join(trend_icons)

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>{status_icon} Sea Retreat System Health Report</h2>
        <p><strong>Date:</strong> {date.today().isoformat()}</p>
        <p><strong>Overall Status:</strong> <span style="font-weight:bold; color:{'#2e7d32' if overall_status=='GREEN' else ('#f57c00' if overall_status in ('YELLOW','ORANGE') else '#c62828')};">{overall_status}</span></p>
        
        <h3>Day-over-Day Health Trend (Last 7 Days)</h3>
        <p style="font-size: 1.4em; letter-spacing: 4px;">{trend_str}</p>

        <h3>Component Diagnostics</h3>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
            <tr style="background:#f2f2f2;">
                <th>Component</th>
                <th>Status</th>
                <th>Details</th>
            </tr>
            <tr>
                <td>Hospitable API</td>
                <td><strong>{results['api'][0]}</strong></td>
                <td>{results['api'][1]}</td>
            </tr>
            <tr>
                <td>SMTP Delivery</td>
                <td><strong>{results['smtp'][0]}</strong></td>
                <td>{results['smtp'][1]}</td>
            </tr>
            <tr>
                <td>System Storage</td>
                <td><strong>{results['storage'][0]}</strong></td>
                <td>{results['storage'][1]}</td>
            </tr>
        </table>
        <br/>
        <p style="font-size:0.9em; color:#666;">Executed automatically by Raspberry Pi Zero 2 W (192.168.68.90)</p>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = owner_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [owner_email], msg.as_string())
        logging.info(f"Health report successfully sent to {owner_email}.")
        return True
    except Exception as e:
        logging.error(f"Failed to dispatch health report email: {e}")
        return False

def run_daily_health_check(send_email: bool = True) -> dict:
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    pat = load_pat()
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")

    api_st, api_det = check_hospitable_api(pat)
    smtp_st, smtp_det = check_smtp_connection(smtp_server, smtp_port, smtp_user, smtp_pass)
    store_st, store_det = check_system_storage()

    statuses = [api_st, smtp_st, store_st]
    if "RED" in statuses:
        overall = "RED"
    elif "ORANGE" in statuses or "YELLOW" in statuses:
        overall = "YELLOW"
    else:
        overall = "GREEN"

    results = {
        "api": (api_st, api_det),
        "smtp": (smtp_st, smtp_det),
        "storage": (store_st, store_det)
    }

    # Record history
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except Exception:
            history = []

    today_str = date.today().isoformat()
    history.append({
        "date": today_str,
        "status": overall,
        "api": api_st,
        "smtp": smtp_st,
        "storage": store_st
    })
    history = history[-14:]

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

    if send_email:
        dispatch_health_report_email(overall, results, history)

    return {
        "overall_status": overall,
        "results": results,
        "history": history
    }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    res = run_daily_health_check(send_email=True)
    print(f"Daily Health Check Complete. Overall Status: {res['overall_status']}")
```

- [ ] **Step 4: Create `systemd/searetreat-healthcheck.service` and `systemd/searetreat-healthcheck.timer`**

Create `systemd/searetreat-healthcheck.service`:
```ini
[Unit]
Description=Sea Retreat Daily Health Check Daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=pi
WorkingDirectory=/home/pi/searetreat_gemini
EnvironmentFile=/home/pi/searetreat_gemini/.env
ExecStart=/home/pi/searetreat_gemini/.venv/bin/python /home/pi/searetreat_gemini/src/daily_health_check.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Create `systemd/searetreat-healthcheck.timer`:
```ini
[Unit]
Description=Timer for Sea Retreat Daily Health Check (Runs daily at 08:00 AM)

[Timer]
OnCalendar=*-*-* 08:00:00
Persistent=true
Unit=searetreat-healthcheck.service

[Install]
WantedBy=timers.target
```

- [ ] **Step 5: Run tests to verify pass**

Run: `pytest tests/test_daily_health_check.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/daily_health_check.py systemd/searetreat-healthcheck.service systemd/searetreat-healthcheck.timer tests/test_daily_health_check.py
git commit -m "feat: add daily health check daemon and day-over-day status trend reporter"
```
