"""Parse a .pcap file and classify ICMP packets by type."""

from __future__ import annotations

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

import pyshark

from .models import AnalysisResults, ICMPPacketInfo

logger = logging.getLogger(__name__)

# ICMP type codes we care about
_TYPE_ECHO_REPLY = "0"
_TYPE_ECHO_REQUEST = "8"
_TYPE_TIME_EXCEEDED = "11"


def analyze_pcap(pcap_file: Path, wait_timeout: int = 30) -> AnalysisResults:
    """
    Parse *pcap_file* and return classified ICMP packet data.

    Blocks until the file exists (up to *wait_timeout* seconds), then reads
    every ICMP packet and sorts it into one of three buckets:

    * Type  8 — Echo Request  (ping query)
    * Type  0 — Echo Reply    (ping reply)
    * Type 11 — Time Exceeded (traceroute TTL expiry)

    Args:
        pcap_file:    Path to the ``.pcap`` file to analyse.
        wait_timeout: Maximum seconds to wait for the file to appear on disk.
    """
    _wait_for_file(pcap_file, wait_timeout)

    logger.info("Analysing %s …", pcap_file)
    results = AnalysisResults()

    try:
        # pyshark uses asyncio internally. On Python 3.10+ there may already be
        # a running event loop in the main thread, which causes:
        #   "There is already a running event loop"
        # Running the capture in a fresh thread (with its own event loop) avoids
        # this reliably on all platforms.
        with ThreadPoolExecutor(max_workers=1) as pool:
            packets = list(pool.submit(_read_packets, str(pcap_file)).result())
    except Exception as exc:
        logger.error("pyshark error reading %s: %s", pcap_file, exc)
        return results

    if not packets:
        logger.warning("No ICMP packets found in %s", pcap_file)
        return results

    logger.info("Found %d ICMP packet(s)", len(packets))

    results.source_ip = _safe_get(packets[0], "ip", "src") or "unknown"
    results.destination_ip = _safe_get(packets[0], "ip", "dst") or "unknown"

    for pkt in packets:
        if not hasattr(pkt, "icmp"):
            continue

        info = ICMPPacketInfo(
            number=str(pkt.number),
            timestamp=str(pkt.sniff_time),
            src_ip=_safe_get(pkt, "ip", "src") or "",
            dst_ip=_safe_get(pkt, "ip", "dst") or "",
            icmp_type=_safe_get(pkt, "icmp", "type") or "",
            icmp_code=_safe_get(pkt, "icmp", "code") or "",
            checksum=_safe_get(pkt, "icmp", "checksum"),
            identifier=_safe_get(pkt, "icmp", "ident"),
            sequence=_safe_get(pkt, "icmp", "seq"),
            ttl=_safe_get(pkt, "ip", "ttl"),
        )

        results.all_packets.append(info)

        if info.icmp_type == _TYPE_ECHO_REQUEST:
            results.ping_requests.append(info)
        elif info.icmp_type == _TYPE_ECHO_REPLY:
            results.ping_replies.append(info)
        elif info.icmp_type == _TYPE_TIME_EXCEEDED:
            results.icmp_errors.append(info)

    return results


# Helpers

def _read_packets(pcap_path: str) -> list:
    """
    Open *pcap_path* with pyshark in a thread that owns its own event loop.

    This avoids the ``"There is already a running event loop"`` error that
    pyshark raises on Python 3.10+ when called from the main thread.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        cap = pyshark.FileCapture(pcap_path, display_filter="icmp")
        pkts = list(cap)
        cap.close()
        return pkts
    finally:
        loop.close()


def _wait_for_file(path: Path, timeout: int) -> None:
    """Block until *path* exists or *timeout* seconds elapse."""
    deadline = time.monotonic() + timeout
    while not path.exists():
        if time.monotonic() > deadline:
            logger.error("Timed out waiting for %s", path)
            return
        logger.info("Waiting for capture file to appear…")
        time.sleep(2)


def _safe_get(packet, *attrs: str) -> Optional[str]:
    """Safely traverse nested pyshark layer attributes; returns None if absent."""
    obj = packet
    for attr in attrs:
        try:
            obj = getattr(obj, attr)
        except AttributeError:
            return None
    return str(obj) if obj is not None else None
