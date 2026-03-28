# Lab 4: ICMP Pinger

## Overview

This lab implements a custom **Ping** application in Python using raw ICMP echo request/reply messages. The program measures round-trip time (RTT), records packet loss, and prints a statistical summary (min, max, average RTT) for each target host.

## Files

| File            | Description                                             |
| --------------- | ------------------------------------------------------- |
| `ICMPPinger.py` | Completed ICMP Pinger client (Python 3)                 |
| `run_pings.sh`  | Shell script to ping four hosts on different continents |
| `README.md`     | This file                                               |

## Prerequisites

- **Python 3.6+**
- **macOS**: No sudo needed (uses non-privileged `SOCK_DGRAM` ICMP sockets).
- **Linux/Windows**: May need root/administrator privileges (`SOCK_RAW` fallback).

## How to Run

### Single host

```bash
python3 ICMPPinger.py <hostname> [count]
```

**Examples:**

```bash
python3 ICMPPinger.py google.com              # google.com, 10 pings (default)
python3 ICMPPinger.py bbc.co.uk 5             # bbc.co.uk, 5 pings
```

> **Note:** On macOS, localhost (127.0.0.1) may not respond with `SOCK_DGRAM` ICMP.
> Use an external host for testing.

### All four continents (automated)

```bash
bash run_pings.sh
```

This pings:

1. **google.com** — North America
2. **bbc.co.uk** — Europe
3. **baidu.com** — Asia
4. **uol.com.br** — South America

## How It Works

1. **`sendOnePing()`** — Constructs an ICMP echo request packet with a type-8
   header, computes the Internet checksum, embeds the current timestamp as
   payload, and sends it via a raw socket.

2. **`receiveOnePing()`** — Waits (with `select`) for an incoming packet up to
   the timeout. Extracts the ICMP header from the IP packet (bytes 20–28),
   verifies the echo-reply type and matching process ID, then computes RTT from
   the embedded timestamp.

3. **`doOnePing()`** — Opens a raw ICMP socket, calls send then receive, and
   closes the socket.

4. **`ping()`** — Orchestrates multiple ping rounds, collects RTTs, and prints
   per-packet results followed by aggregate statistics.

## Target Hosts (Four Continents)

| Host         | Continent     | Location       |
| ------------ | ------------- | -------------- |
| `google.com` | North America | USA            |
| `bbc.co.uk`  | Europe        | United Kingdom |
| `baidu.com`  | Asia          | China          |
| `uol.com.br` | South America | Brazil         |
