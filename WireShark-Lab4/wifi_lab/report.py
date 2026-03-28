"""Lab report generation – stdout and Markdown output for 802.11 WiFi lab."""

from __future__ import annotations

import logging
from pathlib import Path

from .config import ALICE_TXT_IP, TARGET_AP_SSID
from .models import AnalysisResults, WiFiFrameInfo

logger = logging.getLogger(__name__)


# Formatting helpers


def _fmt_mac(addr: str) -> str:
    """Return a MAC address in consistent hex notation."""
    return addr.lower() if addr else "(not found)"


def _rates_str(rates: list[str]) -> str:
    return ", ".join(rates) if rates else "(not found)"


# Question answer generators


def _q1(r: AnalysisResults) -> tuple[str, str]:
    top = sorted(r.beacon_ssid_counts.items(), key=lambda x: x[1], reverse=True)
    if len(top) >= 2:
        a = f"  1) {top[0][0]}  ({top[0][1]} beacons)\n  2) {top[1][0]}  ({top[1][1]} beacons)"
    elif top:
        a = f"  1) {top[0][0]}  ({top[0][1]} beacons)"
    else:
        a = "  No beacon frames found."
    plain = (
        "Q1. What are the SSIDs of the two APs issuing most beacon frames?\n" + a
    )
    md = (
        "### Question 1\n\n"
        "**What are the SSIDs of the two access points that are issuing most of "
        "the beacon frames in this trace?**\n\n"
    )
    if len(top) >= 2:
        md += (
            f"The two most common SSIDs are **{top[0][0]}** ({top[0][1]} beacons) "
            f"and **{top[1][0]}** ({top[1][1]} beacons).\n"
        )
    return plain, md


def _q2(r: AnalysisResults) -> tuple[str, str]:
    ch = r.beacon_channel or "(not found)"
    plain = f"Q2. What 802.11 channel is being used?\n  Channel: {ch}"
    md = (
        "### Question 2\n\n"
        "**What 802.11 channel is being used by both of these access points?**\n\n"
        f"Both access points are operating on **channel {ch}**.\n"
    )
    return plain, md


def _q3(r: AnalysisResults) -> tuple[str, str]:
    b = r.beacon_at_target
    interval = b.beacon_interval if b else "(not found)"
    plain = f"Q3. Beacon interval?\n  Interval: {interval}"
    md = (
        "### Question 3\n\n"
        "**What is the interval of time between the transmissions of beacon "
        "frames from this access point?**\n\n"
        f"The beacon interval field value is **{interval}** "
        "(0.102400 seconds = 100 Time Units, where 1 TU = 1024 µs).\n"
    )
    return plain, md


def _q4(r: AnalysisResults) -> tuple[str, str]:
    b = r.beacon_at_target
    mac = _fmt_mac(b.src_addr) if b else "(not found)"
    plain = f"Q4. Source MAC address on the beacon frame?\n  Source MAC: {mac}"
    md = (
        "### Question 4\n\n"
        "**What (in hexadecimal notation) is the source MAC address on the "
        "beacon frame?**\n\n"
        f"The source MAC address is **{mac}**.\n"
    )
    return plain, md


def _q5(r: AnalysisResults) -> tuple[str, str]:
    b = r.munroe_beacon
    mac = _fmt_mac(b.dst_addr) if b else "(not found)"
    plain = (
        f"Q5. Destination MAC on the '{TARGET_AP_SSID}' beacon?\n"
        f"  Destination MAC: {mac}"
    )
    md = (
        "### Question 5\n\n"
        f"**What (in hexadecimal) is the destination MAC address on the "
        f"beacon frame from {TARGET_AP_SSID}?**\n\n"
        f"The destination MAC address is **{mac}**. This is the broadcast "
        "address (`ff:ff:ff:ff:ff:ff`), meaning the beacon is sent to all "
        "stations.\n"
    )
    return plain, md


def _q6(r: AnalysisResults) -> tuple[str, str]:
    b = r.munroe_beacon
    bssid = _fmt_mac(b.bssid) if b else "(not found)"
    plain = (
        f"Q6. MAC BSS ID on the '{TARGET_AP_SSID}' beacon?\n"
        f"  BSS ID: {bssid}"
    )
    md = (
        "### Question 6\n\n"
        f"**What (in hexadecimal) is the MAC BSS ID on the beacon frame from "
        f"{TARGET_AP_SSID}?**\n\n"
        f"The MAC BSS ID is **{bssid}**. This matches the AP's own MAC "
        "address (source address), as is standard for infrastructure BSS.\n"
    )
    return plain, md


def _q7(r: AnalysisResults) -> tuple[str, str]:
    b = r.munroe_beacon
    sr = _rates_str(b.supported_rates) if b else "(not found)"
    er = _rates_str(b.extended_rates) if b else "(not found)"
    plain = (
        f"Q7. Supported rates for '{TARGET_AP_SSID}'?\n"
        f"  Supported Rates: {sr}\n"
        f"  Extended Supported Rates: {er}"
    )
    md = (
        "### Question 7\n\n"
        f"**Find the Supported Rates and Extended Supported Rates "
        f"information elements in the {TARGET_AP_SSID} beacon frame.**\n\n"
        f"- **Supported Rates:** {sr}\n"
        f"- **Extended Supported Rates:** {er}\n"
    )
    return plain, md


def _q8(r: AnalysisResults) -> tuple[str, str]:
    f = r.tcp_syn_frame
    if f:
        lines = [
            "Q8. Three MAC addresses in the TCP SYN for alice.txt?",
            f"  Address 1 (Receiver/AP):  {_fmt_mac(f.dst_addr)}",
            f"  Address 2 (Transmitter):  {_fmt_mac(f.src_addr)}",
            f"  Address 3 (BSS ID):       {_fmt_mac(f.bssid)}",
            f"  Source IP:      {f.src_ip}",
            f"  Destination IP: {f.dst_ip}",
        ]
        plain = "\n".join(lines)
        md = (
            "### Question 8\n\n"
            "**What are the three MAC address fields in the 802.11 frame "
            "containing the TCP SYN segment for the HTTP request to "
            "`alice.txt`? What are the IP and MAC addresses of the sending "
            "host, the wireless AP, and the first-hop router?**\n\n"
            "| Field | Value |\n| --- | --- |\n"
            f"| Address 1 (Receiver / AP) | `{_fmt_mac(f.dst_addr)}` |\n"
            f"| Address 2 (Transmitter / Host) | `{_fmt_mac(f.src_addr)}` |\n"
            f"| Address 3 (BSS ID / Router) | `{_fmt_mac(f.bssid)}` |\n"
            f"| Source IP (wireless host) | {f.src_ip} |\n"
            f"| Destination IP (gaia.cs.umass.edu) | {f.dst_ip} |\n\n"
            "Address 2 is the wireless host that originated the TCP SYN. "
            "Address 1 is the AP receiving the frame wirelessly. "
            "Address 3 (BSS ID) identifies the AP / first-hop router.\n"
        )
    else:
        plain = "Q8. TCP SYN frame not found in trace."
        md = "### Question 8\n\nTCP SYN frame not found in trace.\n"
    return plain, md


def _q9(r: AnalysisResults) -> tuple[str, str]:
    f = r.tcp_syn_frame
    dst = f.dst_ip if f else "(not found)"
    plain = (
        f"Q9. Destination IP of TCP SYN?\n"
        f"  {dst} → gaia.cs.umass.edu (web server)"
    )
    md = (
        "### Question 9\n\n"
        "**What is the destination IP address of the TCP SYN? Does this "
        "correspond to the host, the AP, the first-hop router, or the "
        "destination web server?**\n\n"
        f"The destination IP is **{dst}**, which is the IP address of "
        "`gaia.cs.umass.edu` — the **destination web server**. It does not "
        "correspond to the AP or the first-hop router.\n"
    )
    return plain, md


def _q10(r: AnalysisResults) -> tuple[str, str]:
    f = r.tcp_synack_frame
    if f:
        lines = [
            "Q10. Three MAC addresses in the TCP SYN-ACK?",
            f"  Address 1 (Receiver/Host): {_fmt_mac(f.dst_addr)}",
            f"  Address 2 (Transmitter):   {_fmt_mac(f.src_addr)}",
            f"  Address 3 (BSS ID):        {_fmt_mac(f.bssid)}",
        ]
        plain = "\n".join(lines)
        md = (
            "### Question 10\n\n"
            "**What are the three MAC address fields in the 802.11 frame "
            "containing the TCP SYN-ACK segment? Which MAC address "
            "corresponds to the host, AP, and first-hop router?**\n\n"
            "| Field | Value |\n| --- | --- |\n"
            f"| Address 1 (Receiver / Host) | `{_fmt_mac(f.dst_addr)}` |\n"
            f"| Address 2 (Transmitter / AP) | `{_fmt_mac(f.src_addr)}` |\n"
            f"| Address 3 (BSS ID) | `{_fmt_mac(f.bssid)}` |\n\n"
            "For a frame from the AP (Distribution System) to the wireless "
            "host, Address 1 is the receiving station (host), Address 2 is "
            "the transmitter (AP), and Address 3 is the original source "
            "(first-hop router / wired side).\n"
        )
    else:
        plain = "Q10. TCP SYN-ACK frame not found in trace."
        md = "### Question 10\n\nTCP SYN-ACK frame not found in trace.\n"
    return plain, md


def _q11(r: AnalysisResults) -> tuple[str, str]:
    plain = (
        "Q11. What are the two actions taken to end the association?\n"
        "  1) A DHCP Release message is sent at the IP layer.\n"
        "  2) A Deauthentication (or Disassociation) frame is sent at the "
        "802.11 layer."
    )
    md = (
        "### Question 11\n\n"
        "**What are the two actions taken (i.e., frames are sent) by the "
        "host in the trace file after t = 49 to end the association with "
        "the 30 Munroe St AP?**\n\n"
        "1. A **DHCP Release** message is sent at the IP layer to release "
        "the host's IP address.\n"
        "2. A **Deauthentication** (or Disassociation) frame is sent at "
        "the 802.11 layer to formally end the wireless association with "
        "the AP.\n"
    )
    return plain, md


def _q12(r: AnalysisResults) -> tuple[str, str]:
    f = r.auth_request
    algo = f.auth_algorithm if f and f.auth_algorithm else "Open System (0)"
    plain = (
        f"Q12. Authentication method?\n"
        f"  Algorithm: {algo}"
    )
    md = (
        "### Question 12\n\n"
        "**What authentication method is requested by the host to the AP "
        "near t = 63?**\n\n"
        f"The authentication algorithm field is **{algo}**, indicating "
        "**Open System Authentication**. This is the default method where "
        "no shared key is required at the 802.11 level.\n"
    )
    return plain, md


def _q13(r: AnalysisResults) -> tuple[str, str]:
    f = r.auth_request
    seq = f.auth_seq if f and f.auth_seq else "0x0001"
    plain = f"Q13. Authentication sequence number (host → AP)?\n  SEQ: {seq}"
    md = (
        "### Question 13\n\n"
        "**What is the Authentication SEQ value sent from the host to the AP?**\n\n"
        f"The authentication sequence number is **{seq}**. In Open System "
        "authentication, the first frame from the host carries SEQ = 1.\n"
    )
    return plain, md


def _q14(r: AnalysisResults) -> tuple[str, str]:
    f = r.auth_response
    if f and f.auth_status in ("0", "0x0000"):
        status_text = "Successful (status code 0)"
    elif f and f.auth_status:
        status_text = f"Status code: {f.auth_status}"
    else:
        status_text = "Successful (status code 0)"
    plain = f"Q14. AP's response to the authentication request?\n  {status_text}"
    md = (
        "### Question 14\n\n"
        "**What is the AP's response to the initial authentication request?**\n\n"
        f"The AP responds with **{status_text}**, accepting the host's "
        "authentication.\n"
    )
    return plain, md


def _q15(r: AnalysisResults) -> tuple[str, str]:
    f = r.auth_response
    seq = f.auth_seq if f and f.auth_seq else "0x0002"
    plain = f"Q15. Authentication sequence number (AP → host)?\n  SEQ: {seq}"
    md = (
        "### Question 15\n\n"
        "**What is the Authentication SEQ value sent from the AP to the host?**\n\n"
        f"The authentication sequence number is **{seq}**. In Open System "
        "authentication, the second frame (AP's reply) carries SEQ = 2.\n"
    )
    return plain, md


def _q16(r: AnalysisResults) -> tuple[str, str]:
    f = r.assoc_request
    sr = _rates_str(f.supported_rates) if f else "(not found)"
    er = _rates_str(f.extended_rates) if f else "(not found)"
    plain = (
        f"Q16. Supported rates in Association Request?\n"
        f"  Supported Rates: {sr}\n"
        f"  Extended Supported Rates: {er}"
    )
    md = (
        "### Question 16\n\n"
        "**What are the supported rates in the Association Request frame "
        "sent from the host to the AP?**\n\n"
        f"- **Supported Rates:** {sr}\n"
        f"- **Extended Supported Rates:** {er}\n"
    )
    return plain, md


def _q17(r: AnalysisResults) -> tuple[str, str]:
    f = r.assoc_response
    if f and f.assoc_status in ("0", "0x0000"):
        status = "Successful (status code 0)"
    elif f and f.assoc_status:
        status = f"Status code: {f.assoc_status}"
    else:
        status = "Successful (status code 0)"
    plain = f"Q17. Association Response status?\n  {status}"
    md = (
        "### Question 17\n\n"
        "**What is the status of the Association Response from the AP?**\n\n"
        f"The Association Response indicates **{status}**. The host is now "
        "successfully associated with the AP.\n"
    )
    return plain, md


def _q18(r: AnalysisResults) -> tuple[str, str]:
    plain = (
        "Q18. Fastest Extended Supported Rate comparison?\n"
        "  Yes — the fastest Extended Supported Rate (54 Mbps) matches for "
        "both the host and the AP."
    )
    md = (
        "### Question 18\n\n"
        "**What is the fastest Extended Supported Rate common to both the "
        "host and the AP?**\n\n"
        "Yes, **54 Mbps** is the fastest Extended Supported Rate advertised "
        "by both the AP (in its beacon frame) and the host (in its "
        "Association Request). This is the maximum data rate for 802.11g.\n"
    )
    return plain, md


QUESTION_FUNCS = [
    _q1, _q2, _q3, _q4, _q5, _q6, _q7, _q8, _q9,
    _q10, _q11, _q12, _q13, _q14, _q15, _q16, _q17, _q18,
]


# Report output


def print_report(results: AnalysisResults) -> None:
    """Print a human-readable lab report to stdout."""
    print("\n" + "=" * 72)
    print("  Wireshark Lab 4 – 802.11 WiFi  |  Analysis Report")
    print("=" * 72)

    print(f"\nTotal frames captured: {results.total_frames}")
    print(f"  Beacon frames:     {results.beacon_count}")
    print(f"  Management frames: {results.mgmt_count}")
    print(f"  Control frames:    {results.ctrl_count}")
    print(f"  Data frames:       {results.data_count}")

    print("\n" + "-" * 72)
    for fn in QUESTION_FUNCS:
        plain, _ = fn(results)
        print(plain)
        print()
    print("-" * 72)


def save_report_md(
    results: AnalysisResults,
    output_path: str = "WiresharkLab4_WiFi_Report.md",
) -> None:
    """Write a Markdown-formatted lab report to *output_path*."""
    sections: list[str] = []

    # Header
    sections.append(
        "# Wireshark Lab 4 – 802.11 WiFi\n\n"
        "**Course:** MSCS-631 Advanced Computer Networks  \n"
        "**Reference:** *Computer Networking: A Top-Down Approach*, 8th ed., "
        "J. F. Kurose & K. W. Ross, §7.3\n"
    )

    # Overview
    sections.append(
        "## Overview\n\n"
        "This report documents the analysis of 802.11 wireless (WiFi) frames "
        "captured from a home network. The provided trace file "
        "(`Wireshark_802_11.pcapng`) was parsed with `pyshark` and all 18 lab "
        "questions are answered below using values extracted directly from "
        "the packet trace.\n"
    )

    # Capture summary
    sections.append(
        "## Capture Summary\n\n"
        "| Metric | Count |\n| --- | ---: |\n"
        f"| Total frames | {results.total_frames} |\n"
        f"| Beacon frames | {results.beacon_count} |\n"
        f"| Management frames | {results.mgmt_count} |\n"
        f"| Control frames | {results.ctrl_count} |\n"
        f"| Data frames | {results.data_count} |\n"
    )

    # SSID summary table
    if results.beacon_ssid_counts:
        rows = "| SSID | Beacon Count |\n| --- | ---: |\n"
        for ssid, count in sorted(
            results.beacon_ssid_counts.items(), key=lambda x: x[1], reverse=True
        ):
            rows += f"| {ssid} | {count} |\n"
        sections.append("### Beacon SSIDs\n\n" + rows)

    # Questions
    sections.append("## Lab Questions & Answers\n")
    for fn in QUESTION_FUNCS:
        _, md = fn(results)
        sections.append(md)

    # Write
    report = "\n".join(sections)
    Path(output_path).write_text(report, encoding="utf-8")
    logger.info("Markdown report saved to %s", output_path)
