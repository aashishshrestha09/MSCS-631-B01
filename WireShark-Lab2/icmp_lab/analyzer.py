"""Parse a .pcap file and classify ICMP packets by type."""

from __future__ import annotations

import logging
import time
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
        cap = pyshark.FileCapture(str(pcap_file), display_filter="icmp")
        packets = list(cap)
        cap.close()
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
