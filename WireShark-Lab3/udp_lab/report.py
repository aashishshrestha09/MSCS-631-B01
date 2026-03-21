"""Lab report generation – stdout and Markdown file output."""

from __future__ import annotations

import logging
from pathlib import Path

from .models import AnalysisResults, UDPPacketInfo

logger = logging.getLogger(__name__)

# Formatting helpers


def _fmt_packet(pkt: UDPPacketInfo) -> str:
    """Return a human-readable one-block summary of a UDP packet."""
    lines = [
        f"  Packet #{pkt.number}  ({pkt.payload_protocol or 'UDP'})",
        f"    Source IP ......... {pkt.src_ip}",
        f"    Destination IP .... {pkt.dst_ip}",
        f"    Source Port ....... {pkt.src_port}",
        f"    Destination Port .. {pkt.dst_port}",
        f"    UDP Length ........ {pkt.udp_length} bytes",
        f"    Checksum .......... {pkt.checksum}",
        f"    IP Protocol ....... {pkt.ip_protocol}",
        f"    TTL ............... {pkt.ttl}",
    ]
    return "\n".join(lines)


def _fmt_packet_md(pkt: UDPPacketInfo) -> str:
    """Return a Markdown-fenced summary of a UDP packet."""
    return (
        f"```\n"
        f"Packet #{pkt.number}  ({pkt.payload_protocol or 'UDP'})\n"
        f"  Source IP ......... {pkt.src_ip}\n"
        f"  Destination IP .... {pkt.dst_ip}\n"
        f"  Source Port ....... {pkt.src_port}\n"
        f"  Destination Port .. {pkt.dst_port}\n"
        f"  UDP Length ........ {pkt.udp_length} bytes\n"
        f"  Checksum .......... {pkt.checksum}\n"
        f"  IP Protocol ....... {pkt.ip_protocol}\n"
        f"  TTL ............... {pkt.ttl}\n"
        f"```"
    )


# Question-answer generators


def _q1(results: AnalysisResults) -> tuple[str, str]:
    """Q1: First UDP segment – packet number, payload, header fields."""
    if not results.all_packets:
        return ("N/A – no UDP packets captured", "N/A")

    first = results.all_packets[0]
    plain = (
        f"Question 1:\n"
        f"  a) The first UDP segment is packet #{first.number} in the trace.\n"
        f"  b) Application-layer protocol: {first.payload_protocol or 'Unknown'}.\n"
        f"  c) The UDP header contains 4 fields:\n"
        f"       1. Source Port\n"
        f"       2. Destination Port\n"
        f"       3. Length\n"
        f"       4. Checksum\n"
    )
    md = (
        f"### Question 1\n\n"
        f"**Select the first UDP segment in your trace. What is the packet number "
        f"of this segment? What type of application-layer payload or protocol message "
        f"is being carried? How many fields are in the UDP header? What are the names "
        f"of these fields?**\n\n"
        f"- **Packet number:** {first.number}\n"
        f"- **Application-layer payload / protocol:** {first.payload_protocol or 'Unknown'}\n"
        f"- **Number of UDP header fields:** 4\n"
        f"- **Field names:**\n"
        f"  1. Source Port\n"
        f"  2. Destination Port\n"
        f"  3. Length\n"
        f"  4. Checksum\n\n"
        f"**First UDP packet details:**\n\n"
        f"{_fmt_packet_md(first)}\n"
    )
    return plain, md


def _q2(results: AnalysisResults) -> tuple[str, str]:
    """Q2: Length of each UDP header field."""
    plain = (
        "Question 2:\n"
        "  Each of the four UDP header fields is exactly 2 bytes (16 bits) long.\n"
        "  Total UDP header size = 4 × 2 = 8 bytes.\n"
    )
    md = (
        "### Question 2\n\n"
        "**By consulting the displayed information in Wireshark's packet content "
        "field for this packet (or by consulting the textbook), what is the length "
        "(in bytes) of each of the first two fields in the UDP header?**\n\n"
        "Each of the four UDP header fields is exactly **2 bytes (16 bits)** long, "
        "giving a total UDP header size of **8 bytes**.\n\n"
        "| Field | Size |\n"
        "| --- | --- |\n"
        "| Source Port | 2 bytes |\n"
        "| Destination Port | 2 bytes |\n"
        "| Length | 2 bytes |\n"
        "| Checksum | 2 bytes |\n"
    )
    return plain, md


def _q3(results: AnalysisResults) -> tuple[str, str]:
    """Q3: Value of the Length field and what it includes."""
    if not results.all_packets:
        return ("N/A", "N/A")

    first = results.all_packets[0]
    plain = (
        f"Question 3:\n"
        f"  The Length field value is {first.udp_length} bytes.\n"
        f"  This counts the UDP header (8 bytes) plus the payload "
        f"({first.payload_size} bytes).\n"
        f"  Number of payload bytes = Length − 8 = {first.payload_size} bytes.\n"
    )
    md = (
        f"### Question 3\n\n"
        f"**What is the value in the Length field of this UDP header? What is the "
        f"maximum number of payload bytes that can be carried in a UDP segment?**\n\n"
        f"- **Length field value:** {first.udp_length} bytes\n"
        f"- The Length field specifies the total size of the UDP datagram — that is, "
        f"the 8-byte header **plus** the application-layer payload.\n"
        f"- **Payload bytes in this packet:** {first.udp_length} − 8 = "
        f"{first.payload_size} bytes\n"
    )
    return plain, md


def _q4(results: AnalysisResults) -> tuple[str, str]:
    """Q4: Maximum number of bytes in a UDP payload."""
    max_payload = 65535 - 8
    plain = (
        f"Question 4:\n"
        f"  The Length field is 16 bits → maximum value 65,535.\n"
        f"  Maximum payload = 65,535 − 8 (header) = {max_payload:,} bytes.\n"
    )
    md = (
        f"### Question 4\n\n"
        f"**What is the maximum number of bytes that can be included in a UDP "
        f"payload?**\n\n"
        f"The `Length` field is 16 bits, so its maximum value is **65,535**. Since "
        f"the UDP header is 8 bytes, the maximum payload is:\n\n"
        f"$$65,535 - 8 = {max_payload:,} \\text{{{{ bytes}}}}$$\n"
    )
    return plain, md


def _q5(results: AnalysisResults) -> tuple[str, str]:
    """Q5: Largest possible source port number."""
    plain = (
        "Question 5:\n"
        "  The source port field is 16 bits → largest possible port = 65,535.\n"
    )
    md = (
        "### Question 5\n\n"
        "**What is the largest possible source port number?**\n\n"
        "The Source Port field is 16 bits, so the largest possible value is "
        "**65,535** ($2^{16} - 1$).\n"
    )
    return plain, md


def _q6(results: AnalysisResults) -> tuple[str, str]:
    """Q6: IP protocol number for UDP."""
    proto = ""
    if results.all_packets:
        proto = results.all_packets[0].ip_protocol

    plain = (
        f"Question 6:\n"
        f"  The IP header Protocol field value is {proto} (decimal).\n"
        f"  The protocol number for UDP is 17.\n"
    )
    md = (
        f"### Question 6\n\n"
        f"**What is the protocol number for UDP in the IP header? Examine the "
        f"Protocol field in the IP header of the packet carrying this UDP segment.**\n\n"
        f"- **IP Protocol field value:** {proto}\n"
        f"- The protocol number for UDP is **17** (0x11). This tells the IP layer "
        f"to pass the payload up to the UDP module.\n"
    )
    return plain, md


def _q7(results: AnalysisResults) -> tuple[str, str]:
    """Q7: Relationship between request/response source & destination ports."""
    if not results.request_response_pairs:
        # Fall back to using first two packets
        if len(results.all_packets) < 2:
            return ("Not enough UDP packets to analyse a request/response pair.", "N/A")
        req = results.all_packets[0]
        rep = results.all_packets[1]
    else:
        req, rep = results.request_response_pairs[0]

    plain = (
        f"Question 7:\n"
        f"  Request  (packet #{req.number}): src port {req.src_port} → dst port {req.dst_port}\n"
        f"  Response (packet #{rep.number}): src port {rep.src_port} → dst port {rep.dst_port}\n"
        f"  The source port of the request becomes the destination port of the\n"
        f"  response, and vice-versa.\n"
    )
    md = (
        f"### Question 7\n\n"
        f"**Examine the pair of UDP packets in which your host sends the first UDP "
        f"packet and the second UDP packet is a reply. Describe the relationship "
        f"between the port numbers in the two packets.**\n\n"
        f"| | Packet # | Source Port | Destination Port |\n"
        f"| --- | --- | --- | --- |\n"
        f"| **Request** | {req.number} | {req.src_port} | {req.dst_port} |\n"
        f"| **Response** | {rep.number} | {rep.src_port} | {rep.dst_port} |\n\n"
        f"**Relationship:** The source port of the request ({req.src_port}) becomes "
        f"the destination port of the response, and the destination port of the "
        f"request ({req.dst_port}) becomes the source port of the response. This "
        f"\"port swap\" is how the reply is routed back to the correct application "
        f"process on the requesting host.\n"
    )
    return plain, md


# Report assembly


_QUESTION_FUNCS = [_q1, _q2, _q3, _q4, _q5, _q6, _q7]


def print_report(
    results: AnalysisResults,
    nslookup_output: str = "",
) -> None:
    """Print a human-readable lab report to stdout."""
    print("\n" + "=" * 70)
    print("  Wireshark Lab 3 – UDP  |  Analysis Report")
    print("=" * 70)

    print(f"\nPackets captured: {len(results.all_packets)}")
    print(f"  DNS queries:    {len(results.dns_queries)}")
    print(f"  DNS responses:  {len(results.dns_responses)}")
    print(f"  Other UDP:      {len(results.other_udp)}")

    if results.all_packets:
        print("\nFirst UDP packet:")
        print(_fmt_packet(results.all_packets[0]))

    print("\n" + "-" * 70)
    for fn in _QUESTION_FUNCS:
        plain, _ = fn(results)
        print(plain)
    print("-" * 70)

    if nslookup_output:
        print("\n── nslookup output ──")
        print(nslookup_output)


def save_report_md(
    results: AnalysisResults,
    nslookup_output: str = "",
    output_path: str = "WiresharkLab3_UDP_Report.md",
) -> None:
    """Write a Markdown-formatted lab report to *output_path*."""
    sections: list[str] = []

    # Header
    sections.append(
        "# Wireshark Lab 3 – UDP\n\n"
        "**Course:** MSCS-631 Advanced Computer Networks  \n"
        "**Reference:** *Computer Networking: A Top-Down Approach*, 8th ed., "
        "J. F. Kurose & K. W. Ross, §3.3\n"
    )

    # Overview
    sections.append(
        "## Overview\n\n"
        "This report documents the capture and analysis of UDP traffic generated "
        "by `nslookup` (DNS) queries.  The captured `.pcap` file was parsed with "
        "`pyshark` and the seven lab questions are answered below using values "
        "extracted directly from the packet trace.\n"
    )

    # Capture summary
    sections.append(
        f"## Capture Summary\n\n"
        f"| Metric | Count |\n"
        f"| --- | ---: |\n"
        f"| Total UDP packets | {len(results.all_packets)} |\n"
        f"| DNS queries | {len(results.dns_queries)} |\n"
        f"| DNS responses | {len(results.dns_responses)} |\n"
        f"| Other UDP | {len(results.other_udp)} |\n"
    )

    if results.all_packets:
        sections.append(
            f"### First Captured UDP Packet\n\n"
            f"{_fmt_packet_md(results.all_packets[0])}\n"
        )

    # Answers
    sections.append("## Lab Questions & Answers\n")
    for fn in _QUESTION_FUNCS:
        _, md_text = fn(results)
        sections.append(md_text)

    # nslookup output
    if nslookup_output:
        sections.append(
            "## Appendix – nslookup Output\n\n"
            f"```\n{nslookup_output.strip()}\n```\n"
        )

    report = "\n".join(sections)
    Path(output_path).write_text(report, encoding="utf-8")
    logger.info("Markdown report saved to %s", output_path)
