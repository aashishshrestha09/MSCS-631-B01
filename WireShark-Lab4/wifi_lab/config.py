"""Centralized constants for the 802.11 WiFi lab."""

import platform

# Trace file
DOWNLOAD_FILE = "data/Wireshark_802_11.pcapng"
ZIP_URL = "http://gaia.cs.umass.edu/wireshark-labs/wireshark-traces-8.1.zip"
ZIP_MEMBER = "Wireshark_802_11.pcapng"

# Known trace-file parameters (from provided Wireshark_801_11.pcapng)
TARGET_AP_SSID = "30 Munroe St"
ALICE_TXT_IP = "128.119.245.12"
CS_UMASS_IP = "128.119.240.19"

# Report
DEFAULT_REPORT_FILE = "WiresharkLab4_WiFi_Report.md"

# 802.11 frame type/subtype codes (decimal strings as pyshark returns them)
BEACON_SUBTYPE = "0x0008"
AUTH_SUBTYPE = "0x000b"
ASSOC_REQ_SUBTYPE = "0x0000"
ASSOC_RESP_SUBTYPE = "0x0001"
DEAUTH_SUBTYPE = "0x000c"
DISASSOC_SUBTYPE = "0x000a"

# Platform
IS_WINDOWS = platform.system() == "Windows"
