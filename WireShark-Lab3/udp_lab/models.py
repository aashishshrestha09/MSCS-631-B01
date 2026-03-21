"""Data models for captured UDP packets and analysis results."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UDPPacketInfo:
    """Extracted fields from a single UDP packet."""

    number: str = ""
    timestamp: str = ""
    src_ip: str = ""
    dst_ip: str = ""
    src_port: str = ""
    dst_port: str = ""
    udp_length: str = ""
    checksum: str = ""
    checksum_status: str = ""
    ip_protocol: str = ""
    ttl: str = ""
    payload_protocol: Optional[str] = None
    payload_size: str = ""


@dataclass
class AnalysisResults:
    """Aggregated results from analysing a UDP .pcap file."""

    source_ip: str = ""
    destination_ip: str = ""
    dns_queries: list[UDPPacketInfo] = field(default_factory=list)
    dns_responses: list[UDPPacketInfo] = field(default_factory=list)
    other_udp: list[UDPPacketInfo] = field(default_factory=list)
    all_packets: list[UDPPacketInfo] = field(default_factory=list)
    # Request/response pairs: list of (request, response) tuples
    request_response_pairs: list[tuple[UDPPacketInfo, UDPPacketInfo]] = field(
        default_factory=list
    )
