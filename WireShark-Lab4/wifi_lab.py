#!/usr/bin/env python3
"""Wireshark Lab 4 – 802.11 WiFi

Automates the full workflow:
  1. Download (or locate) the 802.11 trace file.
  2. Parse the ``.pcapng`` file with ``pyshark``.
  3. Answer all 18 lab questions and generate a Markdown report.

Usage
  Analyse the downloaded trace (default):
      python wifi_lab.py

  Analyse a specific pcap file:
      python wifi_lab.py --analyze-only path/to/file.pcapng

See ``python wifi_lab.py --help`` for all options.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from wifi_lab import analyze_pcap, download_trace, print_report, save_report_md
from wifi_lab.config import DEFAULT_REPORT_FILE, DOWNLOAD_FILE, ZIP_URL

logger = logging.getLogger("wifi_lab")


# CLI


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Wireshark Lab 4 – 802.11 WiFi capture analysis",
    )
    p.add_argument(
        "--analyze-only",
        metavar="PCAP",
        default=None,
        help="Skip download; analyse an existing .pcapng file",
    )
    p.add_argument(
        "--report",
        default=DEFAULT_REPORT_FILE,
        help="Markdown report output path (default: %(default)s)",
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

    # Determine capture file
    if args.analyze_only:
        pcap_path = args.analyze_only
        if not os.path.exists(pcap_path):
            logger.error("File not found: %s", pcap_path)
            sys.exit(1)
    else:
        pcap_path = download_trace(url=ZIP_URL, output_path=DOWNLOAD_FILE)

    # Analyse
    results = analyze_pcap(pcap_path)

    # Output
    print_report(results)
    save_report_md(results, output_path=args.report)
    print(f"\nMarkdown report saved to {args.report}")


if __name__ == "__main__":
    main()
