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
