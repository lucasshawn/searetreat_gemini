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
