"""
Simulation configuration parameters.

All values align with the Phase 1 architecture design targets
"""

# Phase 1 design latency targets (milliseconds)
EDGE_TARGET_LATENCY_MS   = 10.0
FOG_TARGET_LATENCY_MS    = 50.0
CLOUD_TARGET_LATENCY_MS  = 500.0

# Base processing latency per hop (exponential distribution mean, ms)
EDGE_BASE_LATENCY_MS     = 2.5
FOG_BASE_LATENCY_MS      = 10.0
CLOUD_BASE_LATENCY_MS    = 60.0

# Queue capacities (messages)
EDGE_QUEUE_CAPACITY      = 2_000
FOG_QUEUE_CAPACITY       = 8_000
CLOUD_QUEUE_CAPACITY     = 30_000

# Device message rates (messages per second per device)
TRAFFIC_SENSOR_MSG_RATE  = 2.0
ENVIRON_SENSOR_MSG_RATE  = 0.2
SMART_HOME_MSG_RATE      = 1.0

# Device type distribution (fraction of total device count)
DEVICE_DIST = {
    "traffic":       0.30,
    "environmental": 0.35,
    "smart_home":    0.35,
}

# Scale test levels (total device counts)
SCALE_LEVELS = [100, 500, 1_000, 5_000, 10_000]

# Auto-scale threshold: add fog node when fog utilization exceeds this
FOG_AUTOSCALE_THRESHOLD  = 0.80   # 80% capacity
FOG_NODE_CAPACITY        = 2_000  # messages/tick before degradation sets in

# Security: rate limiting
RATE_LIMIT_MSGS_PER_TICK = 15     # max messages per device per simulated second
DDOS_RATE_MULTIPLIER     = 150    # burst multiplier for DDoS-attacking devices
DDOS_EDGE_DETECTION_THR  = 50     # msgs/tick from one source triggers DDoS alert

# Security: intrusion detection
IDS_TRUE_POSITIVE_RATE   = 0.95   # probability Suricata catches known attack
IDS_FALSE_POSITIVE_RATE  = 0.01   # probability of false positive per clean msg

# Security test parameters
ROGUE_DEVICE_COUNT       = 50     # devices with invalid certs in access test
COMPROMISED_DEVICE_COUNT = 10     # legitimate devices turned into bots
PORT_SCAN_PORTS          = 1_024  # ports scanned in port-scan scenario

# Simulation timing
SIM_TICKS                = 10     # simulated seconds per test run
RANDOM_SEED              = 42
