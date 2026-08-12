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
