#!/usr/bin/env python3
"""
Wireshark Lab 2 – ICMP Capture and Analysis  (entry-point)
Edition : Based on Kurose & Ross, Computer Networking: A Top-Down Approach, 8th ed., §5.6

Usage
    # Live capture — requires elevated privileges:
    #   macOS/Linux : sudo python icmp_lab.py www.ust.hk
    #   Windows     : run as Administrator, then: python icmp_lab.py www.ust.hk
    sudo python icmp_lab.py www.ust.hk

    # Analyse an existing trace file (no capture needed)
    python icmp_lab.py --analyze-only data/ICMP-ethereal-trace-1

    # Full help
    python icmp_lab.py --help
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import time
from pathlib import Path

from icmp_lab.analyzer import analyze_pcap
from icmp_lab.capture import detect_capture_interface, start_background_capture
from icmp_lab.config import (
    CAPTURE_INIT_DELAY,
    DEFAULT_CAPTURE_DURATION,
    DEFAULT_CAPTURE_FILE,
    DEFAULT_PING_COUNT,
    DEFAULT_TARGET_HOST,
)
from icmp_lab.network import run_ping, run_traceroute
from icmp_lab.report import print_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="icmp_lab.py",
        description="Wireshark Lab 2 – ICMP capture and analysis (MSCS-631)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=(
            "NOTE: Live capture requires elevated privileges "
            "(sudo on macOS/Linux, Administrator on Windows)."
        ),
    )
    parser.add_argument(
        "host",
        nargs="?",
        default=DEFAULT_TARGET_HOST,
        help="Target hostname or IP for ping and traceroute",
    )
    parser.add_argument(
        "--count", "-c",
        type=int,
        default=DEFAULT_PING_COUNT,
        metavar="N",
        help="Number of ICMP echo requests sent by ping",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=DEFAULT_CAPTURE_FILE,
        metavar="FILE",
        help="Output path for the .pcap capture file",
    )
    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=DEFAULT_CAPTURE_DURATION,
        metavar="SECS",
        help="Maximum capture duration in seconds",
    )
    parser.add_argument(
        "--interface", "-i",
        default=None,
        metavar="IFACE",
        help="Network interface for live capture (auto-detected if omitted)",
    )
    parser.add_argument(
        "--analyze-only",
        type=Path,
        default=None,
        metavar="PCAP",
        help="Skip live capture; analyse an existing .pcap file instead",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable DEBUG-level logging",
    )
    return parser


def main() -> int:
    """Orchestrate the lab workflow. Returns 0 on success, 1 on fatal error."""
    args = _build_parser().parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    ping_output: str = ""
    traceroute_output: str = ""

    if args.analyze_only:
        # Offline mode — analyse an existing .pcap, skip live capture
        if not args.analyze_only.exists():
            logger.error("File not found: %s", args.analyze_only)
            return 1
        results = analyze_pcap(args.analyze_only)
    else:
        # Live mode — capture traffic, then analyse
        try:
            interface = args.interface or detect_capture_interface()
        except RuntimeError as exc:
            logger.error("%s", exc)
            return 1

        logger.info("Using capture interface: %s", interface)
        capture_proc = start_background_capture(args.output, interface, args.duration)
        time.sleep(CAPTURE_INIT_DELAY)  # let tshark fully initialise

        try:
            ping_output = run_ping(args.host, args.count)
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            logger.warning("ping failed: %s", exc)

        try:
            traceroute_output = run_traceroute(args.host)
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            logger.warning("traceroute failed: %s", exc)

        try:
            capture_proc.wait(timeout=args.duration + 15)
        except subprocess.TimeoutExpired:
            capture_proc.terminate()
            logger.warning("Capture process terminated after exceeding timeout")

        results = analyze_pcap(args.output)

    print_report(results, ping_output, traceroute_output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
