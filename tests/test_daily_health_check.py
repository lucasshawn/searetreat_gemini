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

def test_check_hospitable_api_placeholder_token():
    status, details = check_hospitable_api("dummy_token_123")
    assert status == "ORANGE"
    assert "placeholder token" in details

def test_check_hospitable_api_missing_token():
    status, details = check_hospitable_api("")
    assert status == "RED"
    assert "missing" in details

def test_check_smtp_connection_success():
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        status, details = check_smtp_connection("smtp.gmail.com", 587, "user@gmail.com", "pass")
        assert status == "GREEN"

def test_check_smtp_connection_missing_credentials():
    status, details = check_smtp_connection("smtp.gmail.com", 587, "", "")
    assert status == "RED"
    assert "missing" in details

def test_check_system_storage():
    with patch("shutil.disk_usage", return_value=(100*(1024**3), 50*(1024**3), 50*(1024**3))):
        status, details = check_system_storage()
        assert status == "GREEN"
        assert "Disk space OK" in details

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
