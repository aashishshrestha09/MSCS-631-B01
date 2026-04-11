"""
Core IoT Network Simulation Engine.

Implements a discrete-time simulation of the three-tier architecture:
  Device Layer → Edge Gateway → Fog Node → Cloud Service

Each simulated "tick" = 1 second of network time.  The M/M/1 queueing model
drives latency behaviour so results grow realistic as device-count rises.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from .config import (
    DEVICE_DIST, DEVICE_DIST,
    EDGE_BASE_LATENCY_MS, EDGE_QUEUE_CAPACITY, EDGE_TARGET_LATENCY_MS,
    ENVIRON_SENSOR_MSG_RATE,
    FOG_AUTOSCALE_THRESHOLD, FOG_BASE_LATENCY_MS, FOG_NODE_CAPACITY,
    FOG_QUEUE_CAPACITY, FOG_TARGET_LATENCY_MS,
    CLOUD_BASE_LATENCY_MS, CLOUD_QUEUE_CAPACITY, CLOUD_TARGET_LATENCY_MS,
    DDOS_EDGE_DETECTION_THR, DDOS_RATE_MULTIPLIER,
    IDS_FALSE_POSITIVE_RATE, IDS_TRUE_POSITIVE_RATE,
    RATE_LIMIT_MSGS_PER_TICK, RANDOM_SEED, SIM_TICKS,
    SMART_HOME_MSG_RATE, TRAFFIC_SENSOR_MSG_RATE,
)
from .models import (
    DeviceState, DeviceType, LayerMetrics, Message,
    ScalabilityResult, SecurityEvent,
)


# Device Layer helpers

def _create_devices(
    device_count: int,
    rogue_count: int = 0,
    compromised_ids: Set[str] = None,
) -> List[DeviceState]:
    """
    Build the device roster for a given scale level.
    Devices are distributed across traffic / environmental / smart-home
    according to DEVICE_DIST fractions from the Phase 1 design.
    """
    devices: List[DeviceState] = []
    traffic_n = int(device_count * DEVICE_DIST["traffic"])
    environ_n = int(device_count * DEVICE_DIST["environmental"])
    shome_n   = device_count - traffic_n - environ_n

    specs = [
        (DeviceType.TRAFFIC,       traffic_n, TRAFFIC_SENSOR_MSG_RATE),
        (DeviceType.ENVIRONMENTAL, environ_n, ENVIRON_SENSOR_MSG_RATE),
        (DeviceType.SMART_HOME,    shome_n,   SMART_HOME_MSG_RATE),
    ]
    for dtype, count, rate in specs:
        prefix = dtype.value[:3].upper()
        for i in range(count):
            did = f"{prefix}-{i:05d}"
            devices.append(DeviceState(
                device_id=did,
                device_type=dtype,
                msg_rate=rate,
                has_valid_cert=True,
                is_compromised=(compromised_ids is not None and did in compromised_ids),
            ))

    # Rogue devices: valid to the physical network but carry no X.509 cert
    for i in range(rogue_count):
        devices.append(DeviceState(
            device_id=f"ROGUE-{i:04d}",
            device_type=DeviceType.ROGUE,
            msg_rate=TRAFFIC_SENSOR_MSG_RATE,
            has_valid_cert=False,
        ))

    return devices


def _generate_messages(
    devices: List[DeviceState],
    tick: float,
    attack_device_ids: Set[str] = None,
) -> List[Message]:
    """
    Stochastic message generation: each device fires a Poisson process.
    Compromised / attacking devices use DDOS_RATE_MULTIPLIER × normal rate.
    """
    if attack_device_ids is None:
        attack_device_ids = set()

    messages: List[Message] = []
    for dev in devices:
        if dev.is_quarantined:
            continue
        rate = dev.msg_rate
        if dev.device_id in attack_device_ids:
            rate = rate * DDOS_RATE_MULTIPLIER

        # Poisson: expected messages this tick = rate × 1 s
        n = max(0, round(random.gauss(rate, math.sqrt(rate)) if rate > 0 else 0))
        for _ in range(n):
            messages.append(Message(
                device_id=dev.device_id,
                device_type=dev.device_type,
                has_valid_cert=dev.has_valid_cert,
                sent_at=tick,
                payload_bytes=random.randint(64, 512),
            ))
    return messages


# Latency model  (M/M/1-inspired)

def _mm1_latency(base_ms: float, queue_len: int, capacity: int) -> float:
    """
    Compute per-message latency using an M/M/1 queue approximation.
    Latency grows sharply as utilisation approaches 100%.
    """
    rho   = min(0.98, queue_len / capacity)           # utilisation (0..1)
    extra = base_ms * rho / (1 - rho) if rho < 1 else base_ms * 50
    noise = random.gauss(0, base_ms * 0.08)
    return max(0.1, base_ms + extra + noise)


# Edge Layer

def _process_edge(
    messages: List[Message],
    tick: float,
    rate_counters: Dict[str, int],   # per-device message count this tick
    metrics: LayerMetrics,
) -> Tuple[List[Message], List[SecurityEvent]]:
    """
    Edge gateway processing:
      1. X.509 certificate validation  (802.1X / mTLS)
      2. Per-device rate limiting
      3. DDoS detection alert
      4. Latency tagging (M/M/1 model)
    """
    forwarded: List[Message]     = []
    events:    List[SecurityEvent] = []
    queue_len = len(messages)

    for msg in messages:
        metrics.total_received += 1

        # 1. Certificate check
        if not msg.has_valid_cert:
            ev = SecurityEvent(
                event_type="UNAUTHORIZED_ACCESS",
                source_id=msg.device_id,
                tick=tick,
                layer="Edge",
                action="BLOCKED – no valid X.509 certificate",
            )
            events.append(ev)
            metrics.security_events.append(ev)
            metrics.total_blocked += 1
            continue

        # 2. Rate limiting
        rate_counters[msg.device_id] = rate_counters.get(msg.device_id, 0) + 1
        if rate_counters[msg.device_id] > RATE_LIMIT_MSGS_PER_TICK:
            ev = SecurityEvent(
                event_type="RATE_LIMIT_EXCEEDED",
                source_id=msg.device_id,
                tick=tick,
                layer="Edge",
                action=f"DROPPED – exceeds {RATE_LIMIT_MSGS_PER_TICK} msg/s limit",
            )
            events.append(ev)
            metrics.security_events.append(ev)
            metrics.total_blocked     += 1
            metrics.total_rate_limited += 1
            continue

        # 3. DDoS detection alert (does not block yet – alert sent to SIEM)
        if rate_counters[msg.device_id] == DDOS_EDGE_DETECTION_THR:
            ev = SecurityEvent(
                event_type="DDOS_ALERT",
                source_id=msg.device_id,
                tick=tick,
                layer="Edge",
                action="ALERT – DDoS pattern; source flagged for mitigation",
            )
            events.append(ev)
            metrics.security_events.append(ev)

        # 4. Latency + forward
        msg.edge_latency_ms = _mm1_latency(EDGE_BASE_LATENCY_MS, queue_len, EDGE_QUEUE_CAPACITY)
        metrics.latency_samples.append(msg.edge_latency_ms)
        metrics.total_forwarded += 1
        forwarded.append(msg)

    return forwarded, events


# Fog Layer

def _process_fog(
    messages: List[Message],
    tick: float,
    fog_node_count: int,
    behavior_baselines: Dict[str, float],   # device_id → baseline msg/tick
    metrics: LayerMetrics,
) -> Tuple[List[Message], List[SecurityEvent], Set[str]]:
    """
    Fog node processing:
      1. Suricata-style IDS / IPS anomaly detection
      2. Behaviour-baseline anomaly scoring
      3. Quarantine decisions
      4. M/M/c latency (c = fog_node_count)
    Returns (forwarded, events, newly_quarantined_ids).
    """
    forwarded:    List[Message]      = []
    events:       List[SecurityEvent] = []
    quarantined:  Set[str]            = set()

    # Per-device count this tick for anomaly scoring
    device_tick_counts: Dict[str, int] = defaultdict(int)
    for msg in messages:
        device_tick_counts[msg.device_id] += 1

    effective_capacity = fog_node_count * FOG_NODE_CAPACITY
    queue_len          = len(messages)

    for msg in messages:
        metrics.total_received += 1

        # 1. IDS signature matching (probability-based Suricata model)
        # For messages from rogue-typed devices that slipped through: always catch
        is_known_attack = (msg.device_type == DeviceType.ROGUE)
        if is_known_attack and random.random() < IDS_TRUE_POSITIVE_RATE:
            ev = SecurityEvent(
                event_type="IDS_BLOCK",
                source_id=msg.device_id,
                tick=tick,
                layer="Fog",
                action="BLOCKED – Suricata signature match (ROGUE traffic pattern)",
            )
            events.append(ev)
            metrics.security_events.append(ev)
            metrics.total_blocked += 1
            continue

        # 2. Behavioural anomaly detection
        baseline = behavior_baselines.get(msg.device_id, 0)
        current  = device_tick_counts[msg.device_id]
        if baseline > 0 and current > baseline * 10:          # 10× spike
            if random.random() < IDS_TRUE_POSITIVE_RATE:
                quarantined.add(msg.device_id)
                ev = SecurityEvent(
                    event_type="ANOMALY_QUARANTINE",
                    source_id=msg.device_id,
                    tick=tick,
                    layer="Fog",
                    action=f"QUARANTINED – traffic {current:.0f}× baseline {baseline:.1f}",
                )
                events.append(ev)
                metrics.security_events.append(ev)
                metrics.total_blocked += 1
                continue

        # 3. IDS false-positive (rare, for realistic modelling)
        if random.random() < IDS_FALSE_POSITIVE_RATE:
            ev = SecurityEvent(
                event_type="IDS_FALSE_POSITIVE",
                source_id=msg.device_id,
                tick=tick,
                layer="Fog",
                action="DROPPED – false positive (legitimate traffic misclassified)",
            )
            events.append(ev)
            metrics.security_events.append(ev)
            metrics.total_blocked += 1
            continue

        # 4. Latency + forward
        msg.fog_latency_ms = _mm1_latency(FOG_BASE_LATENCY_MS, queue_len, effective_capacity)
        metrics.latency_samples.append(msg.fog_latency_ms)
        metrics.total_forwarded += 1
        forwarded.append(msg)

    return forwarded, events, quarantined


# Cloud Layer

def _process_cloud(
    messages: List[Message],
    tick: float,
    metrics: LayerMetrics,
) -> List[SecurityEvent]:
    """
    Cloud layer processing:
      WAF inspection + storage analytics simulation.
    """
    events: List[SecurityEvent] = []
    queue_len = len(messages)

    for msg in messages:
        metrics.total_received += 1
        msg.cloud_latency_ms = _mm1_latency(CLOUD_BASE_LATENCY_MS, queue_len, CLOUD_QUEUE_CAPACITY)
        metrics.latency_samples.append(msg.cloud_latency_ms)
        metrics.total_forwarded += 1

    return events


# Behaviour baseline builder (warm-up run)

def _build_baselines(devices: List[DeviceState]) -> Dict[str, float]:
    """Compute expected messages-per-tick for each device (used by anomaly detection)."""
    return {dev.device_id: dev.msg_rate for dev in devices}


# Public API: Scalability Test

def run_scalability_test(
    device_count: int,
    ticks: int = SIM_TICKS,
    seed: int = RANDOM_SEED,
    allow_autoscale: bool = True,
) -> ScalabilityResult:
    """
    Run a full scalability test at the given device count.

    Fog nodes auto-scale when utilisation exceeds FOG_AUTOSCALE_THRESHOLD to
    demonstrate the horizontal scaling strategy from Phase 1 Section 5.1.
    """
    random.seed(seed)

    devices = _create_devices(device_count)
    baselines = _build_baselines(devices)

    fog_node_count = max(1, device_count // FOG_NODE_CAPACITY + 1)

    edge_m  = LayerMetrics(layer_name="Edge")
    fog_m   = LayerMetrics(layer_name="Fog")
    cloud_m = LayerMetrics(layer_name="Cloud")

    cloud_delivered = 0
    rate_counters: Dict[str, int] = {}
    quarantined_ids: Set[str]     = set()

    for device in devices:
        if device.is_quarantined:
            quarantined_ids.add(device.device_id)

    for tick in range(ticks):
        rate_counters.clear()    # reset per-tick rate counters

        msgs = _generate_messages(devices, tick)

        msgs, _ = _process_edge(msgs, tick, rate_counters, edge_m)
        msgs, _, new_q = _process_fog(msgs, tick, fog_node_count, baselines, fog_m)

        # Auto-scale fog if utilisation threshold crossed
        if allow_autoscale:
            utilisation = len(msgs) / (fog_node_count * FOG_NODE_CAPACITY + 1)
            if utilisation > FOG_AUTOSCALE_THRESHOLD:
                fog_node_count += 1

        # Mark newly quarantined devices so they stop emitting
        for dev in devices:
            if dev.device_id in new_q:
                dev.is_quarantined = True

        _process_cloud(msgs, tick, cloud_m)
        cloud_delivered += len(msgs)

    throughput = cloud_delivered / ticks if ticks > 0 else 0.0

    return ScalabilityResult(
        device_count=device_count,
        fog_node_count=fog_node_count,
        edge=edge_m,
        fog=fog_m,
        cloud=cloud_m,
        throughput_mps=throughput,
        sim_duration_s=ticks,
    )
