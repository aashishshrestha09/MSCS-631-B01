"""Data models for captured 802.11 WiFi frames and analysis results."""

from dataclasses import dataclass, field


@dataclass
class WiFiFrameInfo:
    """Extracted fields from a single 802.11 frame."""

    number: str = ""
    timestamp: float = 0.0
    frame_type: str = ""
    frame_subtype: str = ""
    type_subtype: str = ""
    src_addr: str = ""
    dst_addr: str = ""
    bssid: str = ""
    ssid: str = ""
    channel: str = ""
    # IP-layer fields (present in data frames)
    src_ip: str = ""
    dst_ip: str = ""
    # TCP fields
    tcp_flags: str = ""
    # Beacon-specific
    beacon_interval: str = ""
    supported_rates: list[str] = field(default_factory=list)
    extended_rates: list[str] = field(default_factory=list)
    # Authentication-specific
    auth_algorithm: str = ""
    auth_seq: str = ""
    auth_status: str = ""
    # Association-specific
    assoc_status: str = ""


@dataclass
class AnalysisResults:
    """Aggregated results from analysing an 802.11 .pcapng file."""

    # Beacon analysis
    beacon_ssid_counts: dict[str, int] = field(default_factory=dict)
    beacon_channel: str = ""
    beacon_at_target: WiFiFrameInfo | None = None
    munroe_beacon: WiFiFrameInfo | None = None

    # Data frame analysis
    tcp_syn_frame: WiFiFrameInfo | None = None
    tcp_synack_frame: WiFiFrameInfo | None = None

    # Authentication / Association
    auth_request: WiFiFrameInfo | None = None
    auth_response: WiFiFrameInfo | None = None
    assoc_request: WiFiFrameInfo | None = None
    assoc_response: WiFiFrameInfo | None = None

    # Disconnection
    disconnect_frame: WiFiFrameInfo | None = None

    # Summary
    total_frames: int = 0
    beacon_count: int = 0
    data_count: int = 0
    mgmt_count: int = 0
    ctrl_count: int = 0
