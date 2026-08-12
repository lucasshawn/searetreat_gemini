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
