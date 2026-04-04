#!/bin/bash
# Wireshark Lab 4 – 802.11 WiFi
# Run this script to set up the environment and execute the analysis.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
# shellcheck disable=SC1091
source venv/bin/activate

echo "Upgrading pip and installing required packages..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Running wifi_lab.py..."
python wifi_lab.py "$@"

echo ""
echo "Deactivating virtual environment..."
deactivate
