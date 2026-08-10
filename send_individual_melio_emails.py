import os
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def send_single_pdf_email(pdf_path: str, vendor_name: str, invoice_num: str, amount: float):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "searetreatpa@gmail.com"
    smtp_pass = "cirk toje dvys tlar"
    recipient = "searetreatpa_7498@invoicesmelio.com"

    filename = os.path.basename(pdf_path)
    
    msg = MIMEMultipart()
    msg['Subject'] = f"Invoice {invoice_num} - {vendor_name}"
    msg['From'] = smtp_user
    msg['To'] = recipient

    body = f"Invoice #{invoice_num} for {vendor_name}. Amount: ${amount:,.2f}"
    msg.attach(MIMEText(body, 'plain'))

    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as f:
            part = MIMEApplication(f.read(), Name=filename)
            part['Content-Disposition'] = f'attachment; filename="{filename}"'
            msg.attach(part)
    else:
        print(f"Error: {pdf_path} does not exist.")
        return False

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        print(f"[SUCCESS] Sent SINGLE invoice email for {vendor_name} ({invoice_num}) -> {recipient}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False

if __name__ == "__main__":
    july_invoices = [
        ("722 Milwaukee/Invoice_Sondra_Owens_CLEAN-PAYOUT-JUL26.pdf", "Sondra Owens", "CLEAN-PAYOUT-JUL26", 1921.00),
        ("722 Milwaukee/Invoice_Gigi_PM_PM-PAYOUT-JUL26.pdf", "Gigi Property Management", "PM-PAYOUT-JUL26", 3258.83)
    ]
    
    for path, vendor, num, amt in july_invoices:
        send_single_pdf_email(path, vendor, num, amt)
        time.sleep(2)
