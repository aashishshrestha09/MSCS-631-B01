#!/usr/bin/env python3
"""Wireshark Lab 3 – UDP

Automates the full workflow:
  1. Detect the active network interface.
  2. Start a background ``tshark`` capture (BPF filter: ``udp``).
  3. Run ``nslookup`` to generate DNS-over-UDP traffic.
  4. Optionally start a simple UDP server/client exchange.
  5. Parse the resulting ``.pcap`` file with ``pyshark``.
  6. Answer all seven lab questions and generate a Markdown report.

Usage
Live capture (requires ``sudo`` on macOS/Linux for tshark):

    sudo python udp_lab.py [HOSTNAME]

Offline analysis of an existing .pcap:

    python udp_lab.py --analyze-only data/udp_capture.pcap

See ``python udp_lab.py --help`` for all options.
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from udp_lab import (
    AnalysisResults,
    analyze_pcap,
    detect_capture_interface,
    print_report,
    save_report_md,
    start_background_capture,
)
from udp_lab.config import (
    DEFAULT_CAPTURE_DURATION,
    DEFAULT_CAPTURE_FILE,
    DEFAULT_NSLOOKUP_HOST,
    DEFAULT_REPORT_FILE,
)
from udp_lab.network import run_nslookup

logger = logging.getLogger("udp_lab")


# CLI


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Wireshark Lab 3 – UDP capture and analysis",
    )
    p.add_argument(
        "host",
        nargs="?",
        default=DEFAULT_NSLOOKUP_HOST,
        help="Hostname to look up via nslookup (default: %(default)s)",
    )
    p.add_argument(
        "--duration",
        type=int,
        default=DEFAULT_CAPTURE_DURATION,
        help="Capture duration in seconds (default: %(default)s)",
    )
    p.add_argument(
        "--interface",
        default=None,
        help="Override auto-detected capture interface",
    )
    p.add_argument(
        "--output",
        default=DEFAULT_CAPTURE_FILE,
        help="Output .pcap file path (default: %(default)s)",
    )
    p.add_argument(
        "--report",
        default=DEFAULT_REPORT_FILE,
        help="Markdown report output path (default: %(default)s)",
    )
    p.add_argument(
        "--analyze-only",
        metavar="PCAP",
        default=None,
        help="Skip capture; analyse an existing .pcap file",
    )
    p.add_argument(
        "--with-echo",
        action="store_true",
        help="Also run a local UDP echo server/client exchange",
    )
    p.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return p


# Main


def main() -> None:
    args = _build_parser().parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    nslookup_output = ""

    # ── Analyse-only mode ────────────────────────────────────────────
    if args.analyze_only:
        pcap_path = args.analyze_only
        if not os.path.exists(pcap_path):
            logger.error("File not found: %s", pcap_path)
            sys.exit(1)
        logger.info("Analyse-only mode – reading %s", pcap_path)
        results = analyze_pcap(pcap_path)
        print_report(results, nslookup_output)
        save_report_md(results, nslookup_output, args.report)
        print(f"\nMarkdown report saved to {args.report}")
        return

    # Live capture mode
    interface = args.interface or detect_capture_interface()
    pcap_dir = os.path.dirname(args.output)
    if pcap_dir and not os.path.exists(pcap_dir):
        os.makedirs(pcap_dir)

    capture_proc = start_background_capture(interface, args.output, args.duration)

    # Optional local UDP echo server/client
    server_proc: subprocess.Popen | None = None
    if args.with_echo:
        server_script = Path(__file__).with_name("udp_server.py")
        if server_script.exists():
            logger.info("Starting local UDP echo server …")
            server_proc = subprocess.Popen(
                [sys.executable, str(server_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            time.sleep(1)
            client_script = Path(__file__).with_name("udp_client.py")
            if client_script.exists():
                logger.info("Running UDP client …")
                subprocess.run(
                    [sys.executable, str(client_script)],
                    timeout=10,
                )

    # Generate DNS/UDP traffic via nslookup
    try:
        nslookup_output = run_nslookup(args.host)
        logger.info("nslookup completed")
    except Exception as exc:
        logger.warning("nslookup failed: %s", exc)

    # Wait for capture to finish
    logger.info("Waiting for capture to complete (up to %ds) …", args.duration)
    try:
        capture_proc.wait(timeout=args.duration + 10)
    except subprocess.TimeoutExpired:
        logger.warning("Capture timed out – terminating tshark")
        capture_proc.terminate()
        capture_proc.wait(timeout=5)

    # Shut down echo server if running
    if server_proc is not None:
        server_proc.terminate()
        server_proc.wait(timeout=5)

    # Analyse
    results = analyze_pcap(args.output)
    print_report(results, nslookup_output)
    save_report_md(results, nslookup_output, args.report)
    print(f"\nMarkdown report saved to {args.report}")


if __name__ == "__main__":
    main()
