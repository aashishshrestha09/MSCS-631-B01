"""
Data models for the IoT Network Simulation.

These dataclasses represent the core entities that flow through
the simulated three-tier edge → fog → cloud architecture.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


# Device type classification (matches Phase 1 device layer)

class DeviceType(str, Enum):
    TRAFFIC       = "traffic"
    ENVIRONMENTAL = "environmental"
    SMART_HOME    = "smart_home"
    ROGUE         = "rogue"          # no valid X.509 certificate


# Core message entity

@dataclass
class Message:
    """A single IoT data message traversing the network stack."""
    device_id:        str
    device_type:      DeviceType
    has_valid_cert:   bool          # X.509 certificate present and valid
    sent_at:          float         # simulation tick when generated
    payload_bytes:    int = 200     # typical sensor payload

    # Set as message travels upward through layers
    edge_latency_ms:  Optional[float] = None
    fog_latency_ms:   Optional[float] = None
    cloud_latency_ms: Optional[float] = None

    @property
    def total_latency_ms(self) -> Optional[float]:
        parts = [self.edge_latency_ms, self.fog_latency_ms, self.cloud_latency_ms]
        return sum(p for p in parts if p is not None) if None not in parts else None


# Per-device state

@dataclass
class DeviceState:
    """Runtime state for one simulated IoT device."""
    device_id:       str
    device_type:     DeviceType
    msg_rate:        float          # messages per simulated second
    has_valid_cert:  bool
    is_compromised:  bool = False   # True once device joins botnet
    is_quarantined:  bool = False   # True once fog IDS quarantines it
    msg_count_ticks: List[float] = field(default_factory=list)  # recent tick times


# Security event

@dataclass
class SecurityEvent:
    """A security incident detected at any layer."""
    event_type: str   # e.g. UNAUTHORIZED_ACCESS, RATE_LIMIT, DDOS_ALERT, ANOMALY
    source_id:  str
    tick:       float
    layer:      str   # Edge | Fog | Cloud
    action:     str   # human-readable action taken


# Aggregate metrics for a single layer in one test run

@dataclass
class LayerMetrics:
    """Collected metrics for one processing layer during a simulation run."""
    layer_name:            str
    total_received:        int   = 0
    total_forwarded:       int   = 0
    total_blocked:         int   = 0    # auth failures + rate limits
    total_rate_limited:    int   = 0
    latency_samples:       List[float] = field(default_factory=list)
    security_events:       List[SecurityEvent] = field(default_factory=list)

    @property
    def packet_loss_pct(self) -> float:
        if self.total_received == 0:
            return 0.0
        return 100.0 * self.total_blocked / self.total_received

    @property
    def avg_latency_ms(self) -> float:
        return sum(self.latency_samples) / len(self.latency_samples) if self.latency_samples else 0.0

    @property
    def p95_latency_ms(self) -> float:
        if not self.latency_samples:
            return 0.0
        s = sorted(self.latency_samples)
        idx = int(0.95 * len(s))
        return s[idx]


# Complete result for one scalability test run

@dataclass
class ScalabilityResult:
    """Aggregated metrics for a single device-count scalability test."""
    device_count:   int
    fog_node_count: int
    edge:           LayerMetrics
    fog:            LayerMetrics
    cloud:          LayerMetrics
    throughput_mps: float   # messages per simulated second arriving at cloud
    sim_duration_s: int


# Security test summary

@dataclass
class SecurityTestResult:
    """Summary metrics for one security test scenario."""
    test_name:           str
    total_attack_msgs:   int
    blocked_at_edge:     int
    flagged_at_fog:      int
    detection_time_s:    float
    false_positives:     int
    legitimate_impact_pct: float   # % increase in latency for normal devices
    events:              List[SecurityEvent] = field(default_factory=list)
