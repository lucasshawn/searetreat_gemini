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

from src.hospitable_api import load_pat, load_env

HISTORY_FILE = os.path.join(ROOT_DIR, "logs", "health_history.json")

def check_hospitable_api(pat: str) -> tuple[str, str]:
    if not pat:
        return "RED", "HOSPITABLE_PAT missing in environment or .env"
    
    if "dummy" in pat.lower() or "your_" in pat.lower():
        return "ORANGE", "Warning: HOSPITABLE_PAT is a placeholder token."

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
            
            warning_msg = f"HTTP {code} OK ({latency:.2f}s)"
            
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
    load_env()
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
