"""Data containers for ICMP packet information and analysis results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ICMPPacketInfo:
    """Fields extracted from a single ICMP packet."""

    number: str
    timestamp: str
    src_ip: str
    dst_ip: str
    icmp_type: str
    icmp_code: str
    checksum: Optional[str] = None
    identifier: Optional[str] = None
    sequence: Optional[str] = None
    ttl: Optional[str] = None


@dataclass
class AnalysisResults:
    """Aggregated results produced by the pcap analyser."""

    source_ip: str = ""
    destination_ip: str = ""
    ping_requests: list[ICMPPacketInfo] = field(default_factory=list)
    ping_replies: list[ICMPPacketInfo] = field(default_factory=list)
    icmp_errors: list[ICMPPacketInfo] = field(default_factory=list)
    all_packets: list[ICMPPacketInfo] = field(default_factory=list)
