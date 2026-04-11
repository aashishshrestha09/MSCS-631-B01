# Project Phase 2 – IoT Smart City Network Simulation

## Overview

This folder contains all Phase 2 deliverables: simulation source code, test results, and the written report. The simulation implements the three-tier edge → fog → cloud architecture designed in Phase 1 and runs both scalability and security test suites.

## Directory Structure

```
Project-Phase2/
├── simulation/
│   ├── __init__.py         Package entry point
│   ├── config.py           All tunable parameters (latency targets, rates, thresholds)
│   ├── models.py           Dataclasses: Message, DeviceState, LayerMetrics, results
│   ├── network_sim.py      Core discrete-event simulation engine (edge / fog / cloud)
│   └── security_sim.py     Four security test scenarios (DDoS, auth, anomaly, port scan)
├── results/
│   └── simulation_results.json   JSON output from the last simulation run
├── run_simulation.py       Main entry point (CLI)
├── requirements.txt        Optional dependencies (matplotlib / numpy for charting)
├── Phase2_Report.md        Written report with results, analysis, and recommendations
└── README.md               This file
```

## How to Run

### Prerequisites

Python 3.10+ is required. No third-party packages are needed for the core simulation.

```bash
# From the workspace root
source .venv/bin/activate

cd "Project-Phase2"
```

### Full simulation (scalability + security)

```bash
python run_simulation.py
```

### Scalability tests only

```bash
python run_simulation.py --scalability
```

### Security tests only

```bash
python run_simulation.py --security
```

### Save results to JSON

```bash
python run_simulation.py --output results/
```

## Simulation Design

### Architecture Modelled

| Layer  | Simulated Component | Key Mechanism                                               |
| ------ | ------------------- | ----------------------------------------------------------- |
| Device | `_create_devices()` | Poisson message generation at per-type rates                |
| Edge   | `_process_edge()`   | X.509 cert validation, per-device rate limiting, DDoS alert |
| Fog    | `_process_fog()`    | IDS signature match, behaviour-baseline anomaly, auto-scale |
| Cloud  | `_process_cloud()`  | WAF inspection, M/M/1 storage latency                       |

### Latency Model

Each layer uses the M/M/1 queueing approximation:

```
latency = base_ms + base_ms × ρ/(1−ρ)  where ρ = queue_depth / capacity
```

Latency grows gradually at low load and spikes as utilisation approaches 100%, matching real network behaviour.

### Security Tests

| Test                | Threat Modelled                       | Primary Defence Tested                     |
| ------------------- | ------------------------------------- | ------------------------------------------ |
| DDoS Volumetric     | 100 devices at 150× rate              | Edge rate limiter + fog anomaly detection  |
| Unauthorized Access | 50 rogue devices (no cert)            | Edge 802.1X / X.509 certificate validation |
| Anomaly Detection   | 10 compromised devices (botnet)       | Fog behaviour-baseline anomaly engine      |
| Port Scan           | External attacker probing 1,024 ports | Edge stateful firewall / DPI               |

## Key Results (from `results/simulation_results.json`)

### Scalability

| Devices | Edge Avg | Fog Avg  | Cloud Avg | Throughput   | Meets Targets? |
| ------: | -------- | -------- | --------- | ------------ | :------------: |
|     100 | 2.64 ms  | 10.55 ms | 60.39 ms  | 103 msg/s    |     All ✓      |
|     500 | 3.41 ms  | 13.61 ms | 61.08 ms  | 526 msg/s    |     All ✓      |
|   1,000 | 5.32 ms  | 21.31 ms | 62.14 ms  | 1,048 msg/s  |     All ✓      |
|   5,000 | 125 ms   | 38.03 ms | 73.05 ms  | 5,369 msg/s  |     Edge ✗     |
|  10,000 | 125 ms   | 49.37 ms | 93.27 ms  | 10,700 msg/s |     Edge ✗     |

_Edge saturation at 5,000+ devices requires horizontal edge gateway scaling (see report Section 5.1)._

### Security

| Test                | Attack Messages |       Block Rate        | Detection Time |
| ------------------- | --------------: | :---------------------: | :------------: |
| DDoS Attack         |         118,755 |          96.6%          |     3.0 s      |
| Unauthorized Access |             974 |         100.0%          |     0.0 s      |
| Anomaly Detection   |       73 events | 50% devices quarantined |     2.0 s      |
| Port Scan           |     1,024 ports |          98.0%          |     0.02 s     |
