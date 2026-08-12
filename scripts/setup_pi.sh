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
    if [ -f "systemd/searetreat-healthcheck.service" ]; then
        sudo cp systemd/searetreat-healthcheck.service /etc/systemd/system/
        sudo cp systemd/searetreat-healthcheck.timer /etc/systemd/system/
    fi
    sudo systemctl daemon-reload
    echo "Installed systemd units successfully."
    echo "To activate the timers, run:"
    echo "  sudo systemctl enable --now searetreat-automation.timer"
    echo "  sudo systemctl enable --now searetreat-healthcheck.timer"
else
    echo "Non-systemd environment detected. Manual copy to /etc/systemd/system required."
fi

echo "=== Provisioning Complete ==="
