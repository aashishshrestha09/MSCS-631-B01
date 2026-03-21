"""OS-aware wrappers for nslookup and the UDP client/server."""

from __future__ import annotations

import logging
import subprocess

logger = logging.getLogger(__name__)


def run_nslookup(host: str) -> str:
    """Run ``nslookup`` for *host* and return the combined stdout+stderr."""
    cmd = ["nslookup", host]
    logger.info("Running: %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout + result.stderr
    except FileNotFoundError:
        raise FileNotFoundError("nslookup command not found on this system")
