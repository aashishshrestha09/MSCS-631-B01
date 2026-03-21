"""PCAP parsing and UDP packet classification."""

from __future__ import annotations

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .models import AnalysisResults, UDPPacketInfo

logger = logging.getLogger(__name__)


# Helpers


def _safe_get(layer, attr: str, default: str = "") -> str:
    """Safely retrieve a nested pyshark layer attribute."""
    try:
        return str(getattr(layer, attr))
    except AttributeError:
        return default


def _wait_for_file(path: str | Path, timeout: float = 30) -> bool:
    """Block until *path* exists or *timeout* seconds elapse."""
    deadline = time.time() + timeout
    while not os.path.exists(path):
        if time.time() > deadline:
            return False
        logger.debug("Waiting for %s …", path)
        time.sleep(2)
    return True


def _read_packets(pcap_file: str) -> list:
    """Read packets inside a dedicated thread (avoids event-loop conflicts)."""
    import pyshark  # imported here so the thread gets its own event loop

    cap = pyshark.FileCapture(pcap_file, display_filter="udp")
    packets = list(cap)
    cap.close()
    return packets


# Public API


def analyze_pcap(pcap_file: str | Path, wait_timeout: float = 30) -> AnalysisResults:
    """Parse *pcap_file* and return classified :class:`AnalysisResults`.

    Blocks up to *wait_timeout* seconds for the file to appear on disk.
    """
    pcap_file = str(pcap_file)
    if not _wait_for_file(pcap_file, wait_timeout):
        logger.warning("PCAP file %s not found after %ss", pcap_file, wait_timeout)
        return AnalysisResults()

    logger.info("Analysing UDP packets in %s …", pcap_file)

    # Run pyshark in its own thread to avoid asyncio event-loop collisions.
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_read_packets, pcap_file)
        raw_packets = future.result()

    results = AnalysisResults()
    dns_requests: dict[str, UDPPacketInfo] = {}  # keyed by (src_ip, src_port)

    for pkt in raw_packets:
        info = UDPPacketInfo(
            number=_safe_get(pkt, "number"),
            timestamp=_safe_get(pkt, "sniff_timestamp"),
            src_ip=_safe_get(pkt.ip, "src") if hasattr(pkt, "ip") else "",
            dst_ip=_safe_get(pkt.ip, "dst") if hasattr(pkt, "ip") else "",
            src_port=_safe_get(pkt.udp, "srcport"),
            dst_port=_safe_get(pkt.udp, "dstport"),
            udp_length=_safe_get(pkt.udp, "length"),
            checksum=_safe_get(pkt.udp, "checksum"),
            checksum_status=_safe_get(pkt.udp, "checksum_status")
            if hasattr(pkt.udp, "checksum_status")
            else "",
            ip_protocol=_safe_get(pkt.ip, "proto") if hasattr(pkt, "ip") else "",
            ttl=_safe_get(pkt.ip, "ttl") if hasattr(pkt, "ip") else "",
        )

        # Determine higher-layer protocol carried inside UDP.
        if hasattr(pkt, "dns"):
            info.payload_protocol = "DNS"
        elif hasattr(pkt, "quic"):
            info.payload_protocol = "QUIC"
        elif hasattr(pkt, "ntp"):
            info.payload_protocol = "NTP"
        elif hasattr(pkt, "dhcp"):
            info.payload_protocol = "DHCP"
        elif hasattr(pkt, "ssdp"):
            info.payload_protocol = "SSDP"
        elif hasattr(pkt, "mdns"):
            info.payload_protocol = "mDNS"
        else:
            info.payload_protocol = "UDP (raw)"

        # Compute payload size (UDP length minus 8-byte header).
        try:
            info.payload_size = str(int(info.udp_length) - 8)
        except (ValueError, TypeError):
            info.payload_size = ""

        results.all_packets.append(info)

        # Classify
        if info.payload_protocol == "DNS":
            if info.dst_port == "53":
                results.dns_queries.append(info)
                dns_requests[f"{info.src_ip}:{info.src_port}"] = info
            else:
                results.dns_responses.append(info)
                # Try to pair with an earlier query.
                key = f"{info.dst_ip}:{info.dst_port}"
                if key in dns_requests:
                    results.request_response_pairs.append(
                        (dns_requests[key], info)
                    )
        else:
            results.other_udp.append(info)

    if results.all_packets:
        results.source_ip = results.all_packets[0].src_ip
        results.destination_ip = results.all_packets[0].dst_ip

    logger.info(
        "Parsed %d UDP packets (%d DNS queries, %d DNS responses, %d other)",
        len(results.all_packets),
        len(results.dns_queries),
        len(results.dns_responses),
        len(results.other_udp),
    )
    return results
