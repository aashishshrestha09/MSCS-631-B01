"""Centralized constants for the UDP lab."""

import platform

# Network
DEFAULT_NSLOOKUP_HOST = "www.nyu.edu"
UDP_SERVER_HOST = "127.0.0.1"
UDP_SERVER_PORT = 9999

# Capture
DEFAULT_CAPTURE_FILE = "data/udp_capture.pcap"
DEFAULT_CAPTURE_DURATION = 20  # seconds
CAPTURE_INIT_DELAY = 2.0  # seconds to wait for tshark to start

# Report
DEFAULT_REPORT_FILE = "WiresharkLab3_UDP_Report.md"

# Platform
IS_WINDOWS = platform.system() == "Windows"
