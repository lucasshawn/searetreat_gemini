import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def send_invoice_email(recipient_email: str, subject: str, body_html: str, attachments: list = None, env_path: str = '.env') -> bool:
    """
    Send invoice email via SMTP.
    Reads SMTP credentials from .env:
    - SMTP_SERVER (default: smtp.gmail.com)
    - SMTP_PORT (default: 587)
    - SMTP_USER
    - SMTP_PASS
    """
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    smtp_user = os.environ.get('SMTP_USER', '')
    smtp_pass = os.environ.get('SMTP_PASS', '')

    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith('SMTP_SERVER='):
                    smtp_server = line.strip().split('=', 1)[1].strip('"\'')
                elif line.startswith('SMTP_PORT='):
                    smtp_port = int(line.strip().split('=', 1)[1].strip('"\''))
                elif line.startswith('SMTP_USER='):
                    smtp_user = line.strip().split('=', 1)[1].strip('"\'')
                elif line.startswith('SMTP_PASS='):
                    smtp_pass = line.strip().split('=', 1)[1].strip('"\'')

    if not smtp_user or not smtp_pass:
        print(f"[Email Notice] SMTP credentials not configured in .env. To enable auto-sending to {recipient_email}, set SMTP_USER and SMTP_PASS in .env.")
        return False

    msg = MIMEMultipart('mixed')
    msg['Subject'] = subject
    msg['From'] = f"Sea Retreat PA <{smtp_user}>"
    msg['To'] = recipient_email

    msg.attach(MIMEText(body_html, 'html'))

    if attachments:
        for file_path in attachments:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                with open(file_path, 'rb') as f:
                    part = MIMEApplication(f.read(), Name=filename)
                    part['Content-Disposition'] = f'attachment; filename="{filename}"'
                    msg.attach(part)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        print(f"[Email Success] Sent invoice email to {recipient_email}")
        return True
    except Exception as e:
        print(f"[Email Error] Failed to send email: {e}")
        return False
