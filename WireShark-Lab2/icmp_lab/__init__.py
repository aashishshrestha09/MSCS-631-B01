"""icmp_lab package — public API."""

from .analyzer import analyze_pcap
from .capture import detect_capture_interface, start_background_capture
from .models import AnalysisResults, ICMPPacketInfo
from .network import run_ping, run_traceroute
from .report import print_report, save_report_md

__all__ = [
    "analyze_pcap",
    "detect_capture_interface",
    "start_background_capture",
    "AnalysisResults",
    "ICMPPacketInfo",
    "run_ping",
    "run_traceroute",
    "print_report",
    "save_report_md",
]
