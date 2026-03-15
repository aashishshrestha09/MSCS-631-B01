"""
Wrappers for the system ping and traceroute utilities.

Security note: host arguments are passed as list elements to subprocess.run —
never interpolated into a shell string — which prevents shell injection.
"""

from __future__ import annotations

import logging
import subprocess

from .config import DEFAULT_PING_COUNT, IS_WINDOWS

logger = logging.getLogger(__name__)


def run_ping(host: str, count: int = DEFAULT_PING_COUNT) -> str:
    """
    Run the system ping utility and return its combined output.

    Uses ``-c`` (POSIX) or ``-n`` (Windows) for the packet count.

    Raises:
        subprocess.TimeoutExpired: If ping does not finish within 2 minutes.
        FileNotFoundError:         If the ping binary is not on PATH.
    """
    flag = "-n" if IS_WINDOWS else "-c"
    cmd: list[str] = ["ping", flag, str(count), host]

    logger.info("Running: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.stdout + result.stderr


def run_traceroute(host: str) -> str:
    """
    Run the system traceroute utility and return its combined output.

    Uses ``tracert`` on Windows, ``traceroute`` on macOS/Linux.

    Raises:
        subprocess.TimeoutExpired: If traceroute does not finish within 5 minutes.
        FileNotFoundError:         If the traceroute binary is not on PATH.
    """
    binary = "tracert" if IS_WINDOWS else "traceroute"
    cmd: list[str] = [binary, host]

    logger.info("Running: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return result.stdout + result.stderr
