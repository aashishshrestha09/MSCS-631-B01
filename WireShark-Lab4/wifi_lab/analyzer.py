"""PCAP parsing and 802.11 WiFi frame analysis for all 18 lab questions."""

from __future__ import annotations

import asyncio
import logging
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pyshark

from .config import TARGET_AP_SSID
from .models import AnalysisResults, WiFiFrameInfo

logger = logging.getLogger(__name__)


# Helpers


def _safe(layer, attr: str, default: str = "") -> str:
    """Safely retrieve a pyshark layer attribute."""
    try:
        val = getattr(layer, attr, None)
        return str(val) if val is not None else default
    except Exception:
        return default


def _extract_frame(pkt) -> WiFiFrameInfo:
    """Build a WiFiFrameInfo from a raw pyshark packet."""
    info = WiFiFrameInfo()

    # Frame metadata
    info.number = _safe(pkt, "number")
    try:
        info.timestamp = float(pkt.sniff_timestamp)
    except Exception:
        info.timestamp = 0.0

    # 802.11 header
    if hasattr(pkt, "wlan"):
        w = pkt.wlan
        info.type_subtype = _safe(w, "fc_type_subtype")
        info.frame_type = _safe(w, "fc_type")
        info.frame_subtype = _safe(w, "fc_subtype")
        info.src_addr = _safe(w, "sa")
        info.dst_addr = _safe(w, "da")
        info.bssid = _safe(w, "bssid")

    # Radio information (channel)
    if hasattr(pkt, "wlan_radio"):
        info.channel = _safe(pkt.wlan_radio, "channel")
    elif hasattr(pkt, "radiotap"):
        info.channel = _safe(pkt.radiotap, "channel_freq")

    # Management-frame fields (SSID, beacon interval, rates, auth, assoc)
    mgt = None
    if hasattr(pkt, "wlan_mgt"):
        mgt = pkt.wlan_mgt
    elif hasattr(pkt, "wlan.mgt"):
        mgt = getattr(pkt, "wlan.mgt")

    if mgt is not None:
        info.ssid = _safe(mgt, "ssid")
        info.beacon_interval = _safe(mgt, "fixed_beacon")
        info.auth_algorithm = _safe(mgt, "fixed_auth_alg")
        info.auth_seq = _safe(mgt, "fixed_auth_seq")
        info.auth_status = _safe(mgt, "fixed_status_code")
        info.assoc_status = _safe(mgt, "fixed_status_code")

        # Supported rates
        sr = _safe(mgt, "supported_rates")
        if sr:
            info.supported_rates = [r.strip() for r in sr.split(",")]
        er = _safe(mgt, "extended_supported_rates")
        if er:
            info.extended_rates = [r.strip() for r in er.split(",")]

    # Try alternative field paths for tagged parameters
    if not info.ssid and hasattr(pkt, "wlan"):
        info.ssid = _safe(pkt.wlan, "ssid")

    # IP layer
    if hasattr(pkt, "ip"):
        info.src_ip = _safe(pkt.ip, "src")
        info.dst_ip = _safe(pkt.ip, "dst")

    # TCP flags
    if hasattr(pkt, "tcp"):
        info.tcp_flags = _safe(pkt.tcp, "flags")

    return info


def _is_beacon(info: WiFiFrameInfo) -> bool:
    ts = info.type_subtype
    return ts in ("0x0008", "8", "0x08", "0008")


def _is_auth(info: WiFiFrameInfo) -> bool:
    ts = info.type_subtype
    return ts in ("0x000b", "11", "0x0b", "000b")


def _is_assoc_req(info: WiFiFrameInfo) -> bool:
    ts = info.type_subtype
    return ts in ("0x0000", "0", "0x00", "0000")


def _is_assoc_resp(info: WiFiFrameInfo) -> bool:
    ts = info.type_subtype
    return ts in ("0x0001", "1", "0x01", "0001")


def _is_deauth(info: WiFiFrameInfo) -> bool:
    ts = info.type_subtype
    return ts in ("0x000c", "12", "0x0c", "000c")


def _is_disassoc(info: WiFiFrameInfo) -> bool:
    ts = info.type_subtype
    return ts in ("0x000a", "10", "0x0a", "000a")


def _has_tcp_flag(info: WiFiFrameInfo, flag: str) -> bool:
    return flag.lower() in info.tcp_flags.lower() if info.tcp_flags else False


# Read packets


def _read_all_packets(pcap_file: str) -> list:
    """Read all packets from the pcap file in a dedicated thread."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    cap = pyshark.FileCapture(pcap_file)
    packets = list(cap)
    cap.close()
    return packets


# Public API


def analyze_pcap(pcap_file: str | Path) -> AnalysisResults:
    """Parse *pcap_file* and return :class:`AnalysisResults` with all Q1–Q18 data."""
    pcap_file = str(pcap_file)
    logger.info("Loading 802.11 frames from %s …", pcap_file)

    with ThreadPoolExecutor(max_workers=1) as pool:
        raw_packets = pool.submit(_read_all_packets, pcap_file).result()

    logger.info("Loaded %d packets – extracting fields …", len(raw_packets))

    results = AnalysisResults(total_frames=len(raw_packets))
    frames: list[WiFiFrameInfo] = []

    for pkt in raw_packets:
        info = _extract_frame(pkt)
        frames.append(info)

    # Classify and count
    ssid_counter: Counter[str] = Counter()
    first_beacon_channel = ""

    for f in frames:
        ft = f.frame_type
        if ft in ("0", "0x00"):
            results.mgmt_count += 1
        elif ft in ("1", "0x01"):
            results.ctrl_count += 1
        elif ft in ("2", "0x02"):
            results.data_count += 1

        if _is_beacon(f):
            results.beacon_count += 1
            ssid = f.ssid or "<Hidden>"
            ssid_counter[ssid] += 1
            if not first_beacon_channel and f.channel:
                first_beacon_channel = f.channel

    results.beacon_ssid_counts = dict(ssid_counter.most_common())
    results.beacon_channel = first_beacon_channel

    # Q3/Q4: Beacon near t ≈ 0.085474
    for f in frames:
        if _is_beacon(f) and abs(f.timestamp - 0.085474) < 0.01:
            results.beacon_at_target = f
            break
    # Fallback: first beacon
    if results.beacon_at_target is None:
        for f in frames:
            if _is_beacon(f):
                results.beacon_at_target = f
                break

    # Q5/Q6: First "30 Munroe St" beacon
    for f in frames:
        if _is_beacon(f) and TARGET_AP_SSID.lower() in f.ssid.lower():
            results.munroe_beacon = f
            break

    # Q8: TCP SYN for alice.txt (near t ≈ 24.82)
    for f in frames:
        if f.tcp_flags and f.src_ip:
            flags_int = 0
            try:
                flags_int = int(f.tcp_flags, 16)
            except (ValueError, TypeError):
                pass
            syn = (flags_int & 0x02) != 0
            ack = (flags_int & 0x10) != 0
            if syn and not ack and 24.0 < f.timestamp < 26.0:
                results.tcp_syn_frame = f
                break

    # Q10: TCP SYN-ACK response (near t ≈ 24.83)
    for f in frames:
        if f.tcp_flags and f.src_ip:
            flags_int = 0
            try:
                flags_int = int(f.tcp_flags, 16)
            except (ValueError, TypeError):
                pass
            syn = (flags_int & 0x02) != 0
            ack = (flags_int & 0x10) != 0
            if syn and ack and 24.0 < f.timestamp < 26.0:
                results.tcp_synack_frame = f
                break

    # Q11: Disconnect frame (near t ≈ 49.58)
    for f in frames:
        if (_is_deauth(f) or _is_disassoc(f)) and 49.0 < f.timestamp < 55.0:
            results.disconnect_frame = f
            break

    # Q12-Q15: Authentication frames (near t ≈ 63.06)
    auth_frames_near = [
        f for f in frames if _is_auth(f) and 62.0 < f.timestamp < 65.0
    ]
    if len(auth_frames_near) >= 1:
        results.auth_request = auth_frames_near[0]
    if len(auth_frames_near) >= 2:
        results.auth_response = auth_frames_near[1]

    # Q16-Q17: Association Request / Response (near t ≈ 63)
    for f in frames:
        if _is_assoc_req(f) and 62.0 < f.timestamp < 65.0:
            results.assoc_request = f
            break
    for f in frames:
        if _is_assoc_resp(f) and 62.0 < f.timestamp < 65.0:
            results.assoc_response = f
            break

    logger.info(
        "Analysis complete: %d beacons, %d mgmt, %d ctrl, %d data frames",
        results.beacon_count,
        results.mgmt_count,
        results.ctrl_count,
        results.data_count,
    )
    return results
