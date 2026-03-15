"""
Print the annotated lab report that answers all 10 Wireshark Lab 2 questions.
"""

from __future__ import annotations

from .models import AnalysisResults, ICMPPacketInfo

_SEP = "=" * 72


def print_report(
    results: AnalysisResults,
    ping_output: str,
    traceroute_output: str,
) -> None:
    """
    Print a complete lab report to stdout.

    Substitutes live captured values where available; the explanatory text
    is always printed regardless of what was captured.
    """
    req = results.ping_requests[0] if results.ping_requests else None
    rep = results.ping_replies[0] if results.ping_replies else None
    err = results.icmp_errors[0] if results.icmp_errors else None
    last_three = results.all_packets[-3:] if len(results.all_packets) >= 3 else results.all_packets

    _header()
    _part1(results, req, rep)
    _part2(results, err, last_three)
    _raw_outputs(ping_output, traceroute_output)


# Header
def _header() -> None:
    print()
    print(_SEP)
    print("  WIRESHARK LAB 2 – ICMP ANALYSIS REPORT")
    print("  MSCS-631 Advanced Computer Networks | University of Cumberlands")
    print(_SEP)


# Part 1 – Ping
def _part1(
    results: AnalysisResults,
    req: "ICMPPacketInfo | None",
    rep: "ICMPPacketInfo | None",
) -> None:
    print("\n── PART 1: ICMP AND PING ──────────────────────────────────────────────\n")
    _q1(results)
    _q2()
    _q3(req)
    _q4(rep)


def _q1(results: AnalysisResults) -> None:
    print("Question 1  What is the IP address of your host?")
    print("            What is the IP address of the destination host?")
    print()
    print(f"  Your host (source) : {results.source_ip}")
    print(f"  Destination host   : {results.destination_ip}")
    print()


def _q2() -> None:
    print("Question 2  Why does an ICMP packet have no source/destination port numbers?")
    print()
    print(
        "  ICMP is a network-layer protocol carried directly inside an IP\n"
        "  datagram (IP protocol number 1). Port numbers are a transport-layer\n"
        "  (TCP/UDP) concept used to demultiplex streams between applications.\n"
        "  ICMP bypasses the transport layer entirely; its Type and Code fields\n"
        "  serve the same identification role without needing ports.\n"
    )


def _q3(req: "ICMPPacketInfo | None") -> None:
    print("Question 3  Examine one ping request (ICMP Echo Request).")
    print("            Type, Code numbers? Other fields? Field sizes?")
    print()
    if req:
        print(_fmt_packet(req))
        print()
    print(
        "  Type : 8  (Echo Request)\n"
        "  Code : 0  (no sub-type)\n"
        "\n"
        "  ┌─────────────────────────┬──────────┬─────────────────────────────┐\n"
        "  │ Field                   │ Size     │ Purpose                     │\n"
        "  ├─────────────────────────┼──────────┼─────────────────────────────┤\n"
        "  │ Type                    │ 1 byte   │ Message category (8 = req)  │\n"
        "  │ Code                    │ 1 byte   │ Sub-type (0 = n/a)          │\n"
        "  │ Checksum                │ 2 bytes  │ 16-bit one's complement CRC │\n"
        "  │ Identifier              │ 2 bytes  │ Links request to reply      │\n"
        "  │ Sequence Number         │ 2 bytes  │ Increments per ping sent    │\n"
        "  │ Data (payload)          │ variable │ Timestamp + padding bytes   │\n"
        "  └─────────────────────────┴──────────┴─────────────────────────────┘\n"
    )


def _q4(rep: "ICMPPacketInfo | None") -> None:
    print("Question 4  Examine the ping reply (ICMP Echo Reply).")
    print("            Type, Code numbers? Field sizes?")
    print()
    if rep:
        print(_fmt_packet(rep))
        print()
    print(
        "  Type : 0  (Echo Reply)\n"
        "  Code : 0\n"
        "\n"
        "  The Echo Reply header layout is identical to the Echo Request.\n"
        "  Identifier and Sequence Number are copied verbatim from the request\n"
        "  so the sender can match each reply to its outgoing probe.\n"
        "\n"
        "  Checksum        : 2 bytes\n"
        "  Identifier      : 2 bytes\n"
        "  Sequence Number : 2 bytes\n"
    )


# Part 2 – Traceroute
def _part2(
    results: AnalysisResults,
    err: "ICMPPacketInfo | None",
    last_three: "list[ICMPPacketInfo]",
) -> None:
    print("── PART 2: ICMP AND TRACEROUTE ────────────────────────────────────────\n")
    _q5(results)
    _q6()
    _q7(err)
    _q8()
    _q9(last_three)
    _q10()


def _q5(results: AnalysisResults) -> None:
    print("Question 5  Source and target IP addresses (traceroute)?")
    print()
    print(f"  Your host (source) : {results.source_ip}")
    print(f"  Target destination : {results.destination_ip}")
    print()


def _q6() -> None:
    print("Question 6  If traceroute used UDP probes, would the IP protocol number")
    print("            still be 01?  If not, what would it be?")
    print()
    print(
        "  No — it would be 17 (0x11).\n"
        "  The IP Protocol field identifies the encapsulated payload:\n"
        "    1  = ICMP\n"
        "    17 = UDP\n"
        "  Unix/Linux traceroute sends UDP datagrams, so each probe packet\n"
        "  would carry protocol number 17 instead of 1.\n"
    )


def _q7(err: "ICMPPacketInfo | None") -> None:
    print("Question 7  Is the traceroute ICMP echo packet different from a ping echo?")
    print()
    if err:
        print(_fmt_packet(err))
        print()
    print(
        "  On Windows (tracert): same ICMP type (8, Code 0) as ping.\n"
        "  The only difference is in the IP TTL field — tracert uses\n"
        "  TTL=1, 2, 3 … for successive probes; ping uses the OS default (64/128).\n"
        "\n"
        "  On macOS/Linux: traceroute sends UDP probes by default (IP proto 17),\n"
        "  so those probes are not ICMP at all — the comparison doesn't apply.\n"
    )


def _q8() -> None:
    print("Question 8  What extra fields appear in the ICMP error packet?")
    print()
    print(
        "  ICMP Time-Exceeded (Type 11, Code 0) extends the standard 8-byte\n"
        "  ICMP header with:\n"
        "\n"
        "  ┌──────────────────────────────────────────┬──────────┐\n"
        "  │ Field                                    │ Size     │\n"
        "  ├──────────────────────────────────────────┼──────────┤\n"
        "  │ Type (11), Code (0), Checksum            │ 4 bytes  │\n"
        "  │ Unused (all zeros)                       │ 4 bytes  │\n"
        "  │ Original IP header of the probe packet   │ ≥20 bytes│\n"
        "  │ First 8 bytes of the original payload    │ 8 bytes  │\n"
        "  └──────────────────────────────────────────┴──────────┘\n"
        "\n"
        "  Embedding part of the original datagram lets the source identify\n"
        "  which probe caused the error.\n"
    )


def _q9(last_three: "list[ICMPPacketInfo]") -> None:
    print("Question 9  How do the last three ICMP packets differ from error packets?")
    print()
    if last_three:
        print("  Last three captured packets:")
        for p in last_three:
            print(
                f"    Pkt #{p.number:>5} | Type={p.icmp_type:>2}  Code={p.icmp_code}"
                f" | {p.src_ip} → {p.dst_ip}"
            )
        print()
    print(
        "  The last three packets are ICMP Echo Replies (Type 0) sent by the\n"
        "  destination host — not Time-Exceeded errors (Type 11) from routers.\n"
        "\n"
        "  Differences:\n"
        "    Type   : 0 (Echo Reply) vs. 11 (Time Exceeded)\n"
        "    Source : destination host vs. an intermediate router\n"
        "\n"
        "  The final probe reaches the target with TTL > 0, so the destination\n"
        "  processes it and replies normally — the same behaviour as ping.\n"
    )


def _q10() -> None:
    print("Question 10 Is there a link with significantly longer delay in traceroute?")
    print()
    print(
        "  Look for the hop where RTT increases most sharply (e.g., 100+ ms jump).\n"
        "  Such a spike typically marks a trans-oceanic undersea cable segment\n"
        "  (light in glass travels ~200,000 km/s ≈ 5 ms per 1,000 km).\n"
        "\n"
        "  Identify the routers using hostname codes:\n"
        "    lax, sjc, nyc  → US West / East Coast\n"
        "    lon, ams, par  → Western Europe\n"
        "    hkg, tyo, sin  → East / South-East Asia\n"
        "\n"
        "  The router pair bracketing the large RTT jump marks the\n"
        "  trans-continental or trans-oceanic crossing point.\n"
    )



# Raw output section
def _raw_outputs(ping_output: str, traceroute_output: str) -> None:
    print(_SEP)
    print("  RAW COMMAND OUTPUTS")
    print(_SEP)

    print("\n── Ping ───────────────────────────────────────────────────────────────\n")
    print(ping_output if ping_output.strip() else "  (no ping output captured)\n")

    print("── Traceroute ─────────────────────────────────────────────────────────\n")
    print(traceroute_output if traceroute_output.strip() else "  (no traceroute output captured)\n")

    print(_SEP)
    print("  END OF REPORT")
    print(_SEP)
    print()


# Packet formatter (shared by multiple question helpers)
def _fmt_packet(pkt: ICMPPacketInfo) -> str:
    return (
        f"  Packet #{pkt.number}  |  {pkt.timestamp}\n"
        f"    {pkt.src_ip}  →  {pkt.dst_ip}    TTL={pkt.ttl}\n"
        f"    ICMP Type : {pkt.icmp_type}   Code : {pkt.icmp_code}\n"
        f"    Checksum  : {pkt.checksum}\n"
        f"    Identifier: {pkt.identifier}   Sequence: {pkt.sequence}"
    )
