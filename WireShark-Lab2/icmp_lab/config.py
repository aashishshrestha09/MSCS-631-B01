"""Shared constants used across the icmp_lab package."""

from __future__ import annotations

import platform
from pathlib import Path

# Network defaults
DEFAULT_TARGET_HOST: str = "www.ust.hk"  # HKUST — good cross-Pacific RTT demo
DEFAULT_PING_COUNT: int = 10

# Capture defaults
DEFAULT_OUTPUT_DIR: Path = Path("data")
DEFAULT_CAPTURE_FILE: Path = DEFAULT_OUTPUT_DIR / "icmp_capture.pcap"
DEFAULT_CAPTURE_DURATION: int = 60   # seconds — covers ping + traceroute
CAPTURE_INIT_DELAY: float = 2.0      # seconds to let tshark initialise

# Report output
DEFAULT_REPORT_FILE: Path = Path("WiresharkLab2_ICMP_Report.md")

# Platform flag
IS_WINDOWS: bool = platform.system() == "Windows"
