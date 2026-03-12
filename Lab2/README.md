# Lab 2 — UDP Pinger

## Overview

This lab implements a UDP-based Ping client (`UDPPingerClient.py`) that communicates with a provided UDP Ping server (`UDPPingerServer.py`). The application measures round-trip time (RTT) for 10 successive ping messages and reports packet loss statistics, closely simulating the behavior of the standard `ping` utility, but using UDP instead of ICMP.

## Project Structure

```
Lab2/
├── UDPPingerServer.py    # Provided server (simulates ~30% packet loss)
├── UDPPingerClient.py    # Client implementation (this lab's deliverable)
└── README.md             # This file
```

## Requirements

| Dependency | Version |
| ---------- | ------- |
| Python     | ≥ 3.10  |

No third-party packages required. All functionality uses Python's standard library (`socket`, `time`).

## Running the Programs

> **You need two separate terminal windows open at the same time.**

### Step 1 — Clone the Repository (first time only)

If you have not already cloned the repository, open a terminal and run:

```bash
git clone https://github.com/aashishshrestha09/MSCS-631-B01.git
```

### Terminal 1 — Start the Server

Navigate to the `Lab2` directory and launch the server:

```bash
cd "MSCS-631-B01/Lab2"
python UDPPingerServer.py
```

Expected output — the server will block here and wait for packets:

```
UDP Ping Server is ready and listening on port 12000...
```

> Leave this terminal running. Do **not** close it before running the client.

### Terminal 2 — Run the Client

Open a **new** terminal window, navigate to the same directory, and run the client:

```bash
cd "MSCS-631-B01/Lab2"
python UDPPingerClient.py
```

The client sends 10 ping messages and prints a reply or timeout for each:

```
--- Pinging 127.0.0.1 on port 12000 ---

Ping 1: Request timed out
Ping 2: Request timed out
Ping 3: Request timed out
Ping 4: Request timed out
Ping 5: Request timed out
Ping 6: Request timed out
Ping 7: Reply from 127.0.0.1  RTT = 0.000645 seconds
  Message: PING 7 1773357707.74443
Ping 8: Reply from 127.0.0.1  RTT = 0.000169 seconds
  Message: PING 8 1773357707.745155
Ping 9: Request timed out
Ping 10: Reply from 127.0.0.1  RTT = 0.000601 seconds
  Message: PING 10 1773357708.746294

--- Ping Statistics for 127.0.0.1 ---
Packets: Sent = 10, Received = 3, Lost = 7 (70% loss)
Round-trip times (seconds):
  Minimum = 0.000169s  |  Maximum = 0.000645s  |  Average = 0.000472s
```

### Stop the Server

When finished, switch back to Terminal 1 and press `Ctrl+C` to stop the server.
