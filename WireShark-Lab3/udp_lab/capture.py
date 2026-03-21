"""Network-interface detection and tshark capture management."""

from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path

from .config import CAPTURE_INIT_DELAY

logger = logging.getLogger(__name__)

# Interface detection


def _parse_interface_name(line: str) -> str | None:
    """Extract the interface identifier from a ``tshark -D`` output line."""
    # Typical format: "4. en0 (Wi-Fi)" or "1. \\Device\\NPF_{...} (Ethernet)"
    parts = line.split(".", 1)
    if len(parts) < 2:
        return None
    rest = parts[1].strip()
    # The name is the first token before any parenthesised description.
    name = rest.split(" ", 1)[0].strip()
    return name if name else None


_PREFERRED_KEYWORDS = ("en0", "wi-fi", "wireless", "wlan", "eth0", "ethernet")


def detect_capture_interface() -> str:
    """Return the best network interface for live capture.

    Prioritises Wi-Fi / Ethernet interfaces by keyword matching, falling back
    to the first available interface.

    Raises ``RuntimeError`` if *tshark* is not installed or no interfaces are
    found.
    """
    try:
        result = subprocess.run(
            ["tshark", "-D"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "tshark not found – please install Wireshark and ensure tshark is on PATH"
        )

    lines = result.stdout.strip().splitlines()
    if not lines:
        raise RuntimeError("tshark -D returned no interfaces")

    interfaces: list[tuple[str, str]] = []  # (id_or_name, raw_line)
    for line in lines:
        name = _parse_interface_name(line)
        if name:
            interfaces.append((name, line))

    if not interfaces:
        raise RuntimeError("Could not parse any interfaces from tshark output")

    # Prefer well-known Wi-Fi / Ethernet interfaces.
    for name, raw in interfaces:
        low = raw.lower()
        if any(kw in low for kw in _PREFERRED_KEYWORDS):
            logger.info("Selected capture interface: %s", name)
            return name

    # Fall back to first listed interface.
    fallback = interfaces[0][0]
    logger.info("Falling back to first interface: %s", fallback)
    return fallback


# Background capture


def start_background_capture(
    interface: str,
    output_file: str | Path,
    duration: int = 20,
) -> subprocess.Popen:
    """Start ``tshark`` in the background capturing UDP traffic.

    Returns the :class:`subprocess.Popen` handle so the caller can wait on or
    terminate the capture later.
    """
    output_file = str(output_file)
    cmd = [
        "tshark",
        "-i", interface,
        "-a", f"duration:{duration}",
        "-f", "udp",           # BPF capture filter – hard-coded for safety
        "-w", output_file,
    ]
    logger.info("Starting capture: %s", " ".join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(CAPTURE_INIT_DELAY)  # allow tshark to initialise
    return proc
