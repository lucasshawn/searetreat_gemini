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
