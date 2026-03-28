#!/bin/bash
# run_pings.sh
# Runs ICMPPinger.py against four target hosts on different continents.
# Each ping session sends 10 ICMP echo requests.
# On macOS, uses non-privileged ICMP sockets (no sudo needed).
# On Linux, may require: sudo bash run_pings.sh
#
# Usage:  bash run_pings.sh

set -e

PYTHON_CMD="python3"
PINGER="ICMPPinger.py"
COUNT=10
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Use venv python if available
if [ -f "../.venv/bin/python" ]; then
    PYTHON_CMD="../.venv/bin/python"
fi

echo "=============================================="
echo " Lab 4 - ICMP Pinger: Multi-Continent Tests"
echo "=============================================="
echo ""

# 1. North America — google.com (USA)
echo ">>> Test 1: google.com (North America)"
$PYTHON_CMD "$PINGER" google.com "$COUNT"

# 2. Europe — bbc.co.uk (United Kingdom)
echo ">>> Test 2: bbc.co.uk (Europe)"
$PYTHON_CMD "$PINGER" bbc.co.uk "$COUNT"

# 3. Asia — baidu.com (China)
echo ">>> Test 3: baidu.com (Asia)"
$PYTHON_CMD "$PINGER" baidu.com "$COUNT"

# 4. South America — uol.com.br (Brazil)
echo ">>> Test 4: uol.com.br (South America)"
$PYTHON_CMD "$PINGER" uol.com.br "$COUNT"

echo "=============================================="
echo " All ping tests completed."
echo "=============================================="
