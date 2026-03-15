"""
Network interface detection and tshark packet capture.

Security note: the tshark command is built as a list (never a shell string),
and the capture filter is a hard-coded BPF expression — not derived from
user input — preventing command/injection vulnerabilities.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Ordered preference list used by detect_capture_interface()
_PREFERRED_KEYWORDS = [
    "en0",       # macOS Wi-Fi (primary)
    "Wi-Fi",     # Wireshark label on macOS / Windows
    "Wireless",
    "wifi",
    "wlan",
    "eth0",      # Linux Ethernet
    "Ethernet",
]


def detect_capture_interface() -> str:
    """
    Discover the primary active network interface via ``tshark -D``.

    Prefers Wi-Fi / Ethernet.  Falls back to the first listed interface when
    none of the preferred keywords match.

    Raises:
        RuntimeError: If tshark is not on PATH or no interface is found.
    """
    try:
        result = subprocess.run(
            ["tshark", "-D"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "tshark not found. Install Wireshark from https://www.wireshark.org/"
        ) from exc

    lines = result.stdout.splitlines()
    logger.debug("tshark -D output:\n%s", result.stdout)

    for keyword in _PREFERRED_KEYWORDS:
        for line in lines:
            if keyword.lower() in line.lower():
                iface = _parse_interface_name(line)
                if iface:
                    logger.debug("Selected interface '%s' (keyword '%s')", iface, keyword)
                    return iface

    if lines:
        iface = _parse_interface_name(lines[0])
        if iface:
            logger.warning("No preferred interface found; using first listed: %s", iface)
            return iface

    raise RuntimeError("No network interfaces found. Check your tshark installation.")


def _parse_interface_name(line: str) -> Optional[str]:
    """
    Parse one line of ``tshark -D`` output and return the interface name.

    Examples::

        macOS/Linux : "1. en0 (Wi-Fi)"      → "en0"
        Windows     : "5. \\Device\\NPF_{…}" → "5"  (numeric index)
    """
    parts = line.strip().split(" ", 2)
    if len(parts) < 2:
        return None

    numeric_index = parts[0].rstrip(".")
    iface_name = parts[1].rstrip(".")

    # Windows NPF device paths are unusable directly; return the index.
    if "\\" in iface_name:
        return numeric_index

    return iface_name


def start_background_capture(
    output_file: Path,
    interface: str,
    duration: int,
) -> subprocess.Popen:
    """
    Start a tshark capture process in the background.

    Only ICMP traffic is written to *output_file* (BPF filter ``icmp``).

    Args:
        output_file: Destination ``.pcap`` path.
        interface:   Interface name or numeric ID from ``tshark -D``.
        duration:    Auto-stop after this many seconds.

    Returns:
        The :class:`subprocess.Popen` handle of the background process.
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)

    cmd: list[str] = [
        "tshark",
        "-i", interface,
        "-a", f"duration:{duration}",
        "-f", "icmp",          # hard-coded BPF filter — not user-controlled
        "-w", str(output_file),
    ]

    logger.info(
        "Capture started  interface=%s  duration=%ds  output=%s",
        interface, duration, output_file,
    )
    logger.debug("Command: %s", " ".join(cmd))

    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
