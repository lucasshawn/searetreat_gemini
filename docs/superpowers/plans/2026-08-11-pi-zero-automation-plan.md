# Pi Zero 2 W Monthly Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, configure, and document the automated headless deployment of the Sea Retreat monthly P&L and Melio invoice pipeline on a Raspberry Pi Zero 2 W (`192.168.68.90`) using native systemd timer and service units with automated failure alerts.

**Architecture:** A systemd timer (`OnCalendar=*-*-02 06:00:00`, `Persistent=true`) triggers a systemd service executing `monthly_automation.py` in an isolated Python 3 virtual environment (`.venv`). Environment variables are loaded from `.env`. Errors are caught by a top-level alert handler that emails failure details to `OWNER_EMAIL`. An automated provisioning script `scripts/setup_pi.sh` builds the environment and installs systemd units.

**Tech Stack:** Python 3, Bash, Linux `systemd` (Service & Timer), SMTP (smtplib), pytest.

## Global Constraints

- Device IP: `192.168.68.90`
- Target Remote Path: `/home/pi/searetreat_gemini`
- Python Virtualenv Path: `/home/pi/searetreat_gemini/.venv`
- Schedule: `OnCalendar=*-*-02 06:00:00`
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

- [ ] **Step 1: Write the failing test for `send_failure_alert`**

Create `tests/test_alert_sender.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from src.alert_sender import send_failure_alert

def test_send_failure_alert_success():
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        env_vars = {
            "SMTP_SERVER": "smtp.gmail.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "test@gmail.com",
            "SMTP_PASS": "secret",
            "OWNER_EMAIL": "owner@gmail.com"
        }
        with patch.dict("os.environ", env_vars):
            success = send_failure_alert("Test API Error", "Traceback details...")
            assert success is True
            assert mock_server.sendmail.called
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_alert_sender.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.alert_sender'`

- [ ] **Step 3: Implement `src/alert_sender.py`**

Create `src/alert_sender.py`:
```python
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_failure_alert(error_message: str, log_snippet: str = "") -> bool:
    """
    Sends an urgent email notification to OWNER_EMAIL when the monthly automation pipeline fails.
    """
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")
    owner_email = os.getenv("OWNER_EMAIL", "searetreatpa@gmail.com")

    if not smtp_user or not smtp_pass:
        logging.error("Cannot send failure alert: SMTP credentials missing in environment.")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = owner_email
        msg["Subject"] = "🚨 URGENT: Sea Retreat Monthly Automation Failed"

        body = (
            f"Sea Retreat Monthly Automation encountered a critical failure.\n\n"
            f"Error Details:\n{error_message}\n\n"
            f"Log Snippet:\n{log_snippet}\n\n"
            f"Please check your Raspberry Pi Zero (192.168.68.90) logs using:\n"
            f"journalctl -u searetreat-automation -n 100\n"
        )
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [owner_email], msg.as_string())
        
        logging.info(f"Failure alert email successfully dispatched to {owner_email}.")
        return True
    except Exception as e:
        logging.error(f"Failed to dispatch failure alert email: {e}")
        return False
```

- [ ] **Step 4: Update `src/monthly_automation.py` with top-level try/except alert dispatch**

Modify `src/monthly_automation.py`:
```python
# Import alert_sender
from src.alert_sender import send_failure_alert

# Wrap run_monthly_pipeline logic in try/except block
def run_monthly_pipeline(target_month_override: str = None, send_email: bool = True):
    setup_logging()
    try:
        # existing logic ...
        return True
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        logging.error(f"Pipeline crashed with unhandled exception: {e}")
        logging.error(tb_str)
        if send_email:
            send_failure_alert(str(e), tb_str)
        return False
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_alert_sender.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/alert_sender.py src/monthly_automation.py tests/test_alert_sender.py
git commit -m "feat: add pipeline failure alert email handler"
```

---

### Task 2: Create Systemd Service & Timer Unit Files

**Files:**
- Create: `systemd/searetreat-automation.service`
- Create: `systemd/searetreat-automation.timer`
- Test: `tests/test_systemd_files.py`

**Interfaces:**
- Systemd Service file format matching Debian/Raspberry Pi OS requirements.
- Systemd Timer configured for `OnCalendar=*-*-02 06:00:00` and `Persistent=true`.

- [ ] **Step 1: Write verification test for Systemd files**

Create `tests/test_systemd_files.py`:
```python
import os
import pytest

def test_systemd_service_content():
    service_path = os.path.join("systemd", "searetreat-automation.service")
    assert os.path.exists(service_path)
    with open(service_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "[Unit]" in content
    assert "[Service]" in content
    assert "WorkingDirectory=/home/pi/searetreat_gemini" in content
    assert "EnvironmentFile=/home/pi/searetreat_gemini/.env" in content
    assert "ExecStart=/home/pi/searetreat_gemini/.venv/bin/python /home/pi/searetreat_gemini/src/monthly_automation.py" in content

def test_systemd_timer_content():
    timer_path = os.path.join("systemd", "searetreat-automation.timer")
    assert os.path.exists(timer_path)
    with open(timer_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "[Unit]" in content
    assert "[Timer]" in content
    assert "OnCalendar=*-*-02 06:00:00" in content
    assert "Persistent=true" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_systemd_files.py -v`
Expected: FAIL with `AssertionError: assert False (path does not exist)`

- [ ] **Step 3: Create `systemd/searetreat-automation.service`**

Create `systemd/searetreat-automation.service`:
```ini
[Unit]
Description=Sea Retreat Monthly P&L and Melio Invoice Automation
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=pi
WorkingDirectory=/home/pi/searetreat_gemini
EnvironmentFile=/home/pi/searetreat_gemini/.env
ExecStart=/home/pi/searetreat_gemini/.venv/bin/python /home/pi/searetreat_gemini/src/monthly_automation.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 4: Create `systemd/searetreat-automation.timer`**

Create `systemd/searetreat-automation.timer`:
```ini
[Unit]
Description=Timer for Sea Retreat Monthly Automation (2nd of every month at 06:00 AM)

[Timer]
OnCalendar=*-*-02 06:00:00
Persistent=true
Unit=searetreat-automation.service

[Install]
WantedBy=timers.target
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_systemd_files.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add systemd/searetreat-automation.service systemd/searetreat-automation.timer tests/test_systemd_files.py
git commit -m "feat: add systemd service and timer unit configuration files"
```

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
    sudo systemctl daemon-reload
    echo "Installed systemd units successfully."
    echo "To activate the timer, run:"
    echo "  sudo systemctl enable --now searetreat-automation.timer"
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
    assert "journalctl -u searetreat-automation" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_docs_exist.py -v`
Expected: FAIL with `AssertionError: assert False (path does not exist)`

- [ ] **Step 3: Create `docs/pi_zero_setup.md`**

Create `docs/pi_zero_setup.md`:
```markdown
# Raspberry Pi Zero 2 W Setup & Operational Guide

This document provides step-by-step instructions for deploying and managing the **Sea Retreat Monthly P&L & Melio Invoice Automation** on a Raspberry Pi Zero 2 W.

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

## 4. Enabling the Monthly Systemd Timer

Enable and start the systemd timer unit:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now searetreat-automation.timer
```

Verify that the timer is scheduled active:
```bash
systemctl list-timers searetreat-automation.timer
```
*Expected Schedule:* Next trigger on the 2nd of the month at `06:00:00`.

---

## 5. Testing & Manual Execution

To perform an immediate manual test run without waiting for the 2nd of the month:
```bash
# Test manual run with --no-email flag via virtualenv
.venv/bin/python src/monthly_automation.py --month 2026-07 --no-email

# Test triggering full systemd service directly
sudo systemctl start searetreat-automation.service
```

---

## 6. Log Monitoring & Troubleshooting

- **View Live Journalctl Logs:**
  ```bash
  journalctl -u searetreat-automation -f
  ```

- **View Execution File Logs:**
  ```bash
  cat /home/pi/searetreat_gemini/logs/monthly_automation.log
  ```

- **Check Service Status:**
  ```bash
  systemctl status searetreat-automation.service
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
