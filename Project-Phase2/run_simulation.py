"""
IoT Smart City Network Simulation – Main Entry Point

Usage:
    python run_simulation.py                     # all tests
    python run_simulation.py --scalability       # scalability tests only
    python run_simulation.py --security          # security tests only
    python run_simulation.py --output results/   # save JSON results
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import List

from simulation.config import SCALE_LEVELS, SIM_TICKS
from simulation.models import ScalabilityResult, SecurityTestResult
from simulation.network_sim import run_scalability_test
from simulation.security_sim import (
    test_anomaly_detection,
    test_ddos,
    test_port_scan,
    test_unauthorized_access,
)


# Pretty-print helpers

def _hline(width: int = 90) -> None:
    print("─" * width)


def _header(title: str) -> None:
    print()
    _hline()
    print(f"  {title}")
    _hline()


def _target(value: float, target: float, higher_is_better: bool = False) -> str:
    """Return PASS/FAIL tag for comparison against design target."""
    ok = (value <= target) if not higher_is_better else (value >= target)
    return "✓ PASS" if ok else "✗ FAIL"


# Scalability results table

def print_scalability_results(results: List[ScalabilityResult]) -> None:
    _header("SCALABILITY TEST RESULTS")
    print(f"  Simulation duration per level : {SIM_TICKS} simulated seconds")
    print(f"  Design latency targets        : Edge <10 ms | Fog <50 ms | Cloud <500 ms")
    print()
    hdr = (
        f"  {'Devices':>8}  {'Fog Nodes':>9}  "
        f"{'Edge Avg':>10}  {'Edge P95':>10}  "
        f"{'Fog Avg':>9}  {'Fog P95':>9}  "
        f"{'Cloud Avg':>10}  "
        f"{'Throughput':>12}  {'Loss%':>6}"
    )
    print(hdr)
    print("  " + "-" * 86)

    for r in results:
        edge_tag  = _target(r.edge.avg_latency_ms,  10.0)
        fog_tag   = _target(r.fog.avg_latency_ms,   50.0)
        cloud_tag = _target(r.cloud.avg_latency_ms, 500.0)

        print(
            f"  {r.device_count:>8,}  {r.fog_node_count:>9}  "
            f"{r.edge.avg_latency_ms:>8.2f}ms  {r.edge.p95_latency_ms:>8.2f}ms  "
            f"{r.fog.avg_latency_ms:>7.2f}ms  {r.fog.p95_latency_ms:>7.2f}ms  "
            f"{r.cloud.avg_latency_ms:>8.2f}ms  "
            f"{r.throughput_mps:>11.0f}  {r.edge.packet_loss_pct:>5.2f}%"
        )

    print()
    print("  Layer latency vs. Phase 1 design targets:")
    for r in results:
        et = _target(r.edge.avg_latency_ms,  10.0)
        ft = _target(r.fog.avg_latency_ms,   50.0)
        ct = _target(r.cloud.avg_latency_ms, 500.0)
        print(f"    {r.device_count:>7,} devices  |  Edge {et}  |  Fog {ft}  |  Cloud {ct}")


# Security results table

def print_security_results(results: List[SecurityTestResult]) -> None:
    _header("SECURITY TEST RESULTS")

    for res in results:
        print(f"\n  ── {res.test_name} ──")
        print(f"     Total attack messages  : {res.total_attack_msgs:,}")
        print(f"     Blocked at Edge layer  : {res.blocked_at_edge:,}")
        print(f"     Flagged at Fog layer   : {res.flagged_at_fog:,}")
        if res.total_attack_msgs > 0:
            total_caught = res.blocked_at_edge + res.flagged_at_fog
            rate = min(100.0, total_caught / res.total_attack_msgs * 100)
            print(f"     Overall block rate     : {rate:.1f}%")
        print(f"     Detection time         : {res.detection_time_s:.2f} s")
        print(f"     False positives        : {res.false_positives}")
        print(f"     Legitimate traffic     : {res.legitimate_impact_pct:.1f}% latency impact")

        unique_types = set(ev.event_type for ev in res.events)
        if unique_types:
            print(f"     Security events fired  : {', '.join(sorted(unique_types))}")


# JSON serialiser

def _results_to_dict(
    scalability: List[ScalabilityResult],
    security: List[SecurityTestResult],
) -> dict:
    return {
        "scalability": [
            {
                "device_count":      r.device_count,
                "fog_node_count":    r.fog_node_count,
                "edge_avg_lat_ms":   round(r.edge.avg_latency_ms, 3),
                "edge_p95_lat_ms":   round(r.edge.p95_latency_ms, 3),
                "fog_avg_lat_ms":    round(r.fog.avg_latency_ms, 3),
                "fog_p95_lat_ms":    round(r.fog.p95_latency_ms, 3),
                "cloud_avg_lat_ms":  round(r.cloud.avg_latency_ms, 3),
                "throughput_mps":    round(r.throughput_mps, 1),
                "packet_loss_pct":   round(r.edge.packet_loss_pct, 3),
                "edge_blocked":      r.edge.total_blocked,
            }
            for r in scalability
        ],
        "security": [
            {
                "test_name":           r.test_name,
                "total_attack_msgs":   r.total_attack_msgs,
                "blocked_at_edge":     r.blocked_at_edge,
                "flagged_at_fog":      r.flagged_at_fog,
                "detection_time_s":    r.detection_time_s,
                "false_positives":     r.false_positives,
                "legitimate_impact_pct": r.legitimate_impact_pct,
            }
            for r in security
        ],
    }


# Main

def main() -> None:
    parser = argparse.ArgumentParser(
        description="IoT Smart City Network Simulation – Phase 2"
    )
    parser.add_argument("--scalability", action="store_true",
                        help="Run scalability tests only")
    parser.add_argument("--security", action="store_true",
                        help="Run security tests only")
    parser.add_argument("--output", metavar="DIR", default=None,
                        help="Directory to save JSON results (created if absent)")
    args = parser.parse_args()

    run_all = not args.scalability and not args.security

    scalability_results: List[ScalabilityResult]  = []
    security_results:    List[SecurityTestResult] = []

    # Scalability tests
    if run_all or args.scalability:
        _header("SCALABILITY SIMULATION  –  Running…")
        for count in SCALE_LEVELS:
            print(f"  → Testing {count:,} devices …", end=" ", flush=True)
            t0 = time.perf_counter()
            result = run_scalability_test(count)
            elapsed = time.perf_counter() - t0
            print(f"done ({elapsed:.2f}s real time)")
            scalability_results.append(result)

        print_scalability_results(scalability_results)

    # Security tests
    if run_all or args.security:
        _header("SECURITY SIMULATION  –  Running…")

        print("  → Test 1: DDoS Volumetric Attack …", end=" ", flush=True)
        r1 = test_ddos()
        print("done")

        print("  → Test 2: Unauthorized Device Access …", end=" ", flush=True)
        r2 = test_unauthorized_access()
        print("done")

        print("  → Test 3: Anomaly Detection (Botnet) …", end=" ", flush=True)
        r3 = test_anomaly_detection()
        print("done")

        print("  → Test 4: Port Scan / Reconnaissance …", end=" ", flush=True)
        r4 = test_port_scan()
        print("done")

        security_results = [r1, r2, r3, r4]
        print_security_results(security_results)

    # Save JSON output
    if args.output and (scalability_results or security_results):
        os.makedirs(args.output, exist_ok=True)
        out_path = os.path.join(args.output, "simulation_results.json")
        payload  = _results_to_dict(scalability_results, security_results)
        with open(out_path, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"\n  Results saved → {out_path}")

    _hline()
    print("  Simulation complete.")
    _hline()


if __name__ == "__main__":
    main()
