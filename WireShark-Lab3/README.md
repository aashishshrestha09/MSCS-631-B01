# Wireshark Lab 3 – UDP

## Overview

This lab explores the **UDP transport protocol** by capturing and analysing real UDP traffic. The toolkit automates the complete workflow:

1. **Detect** the active network interface via `tshark -D`.
2. **Capture** UDP packets in the background using `tshark` with a BPF filter (`udp`).
3. **Generate traffic** by running `nslookup` (DNS queries travel over UDP port 53).
4. **Optionally** run a local UDP echo server/client pair for additional traffic.
5. **Parse** the resulting `.pcap` file with `pyshark`.
6. **Answer** all seven lab questions and produce a formatted Markdown report.

## Prerequisites

| Requirement        | Notes                                  |
| ------------------ | -------------------------------------- |
| Python ≥ 3.10      | `python3 --version`                    |
| Wireshark / tshark | `tshark --version` — must be on `PATH` |
| pyshark ≥ 0.6      | Installed via `requirements.txt`       |

## Installation

```bash
cd WireShark-Lab3
pip install -r requirements.txt
```

## Usage

### Live Capture

Live packet capture requires elevated privileges on macOS/Linux so that `tshark` can access the network interface:

```bash
sudo python udp_lab.py                     # default: nslookup www.nyu.edu
sudo python udp_lab.py www.google.com      # custom hostname
sudo python udp_lab.py --with-echo         # also run local UDP echo test
sudo python udp_lab.py --duration 30 -v    # 30-second capture, verbose logging
```

### Offline Analysis

Analyse an existing `.pcap` file without capturing:

```bash
python udp_lab.py --analyze-only data/udp_capture.pcap
```

### CLI Options

| Flag                  | Description                          | Default                       |
| --------------------- | ------------------------------------ | ----------------------------- |
| `host`                | Hostname for `nslookup`              | `www.nyu.edu`                 |
| `--duration`          | Capture duration (seconds)           | `20`                          |
| `--interface`         | Override auto-detected interface     | auto                          |
| `--output`            | Output `.pcap` path                  | `data/udp_capture.pcap`       |
| `--report`            | Markdown report path                 | `WiresharkLab3_UDP_Report.md` |
| `--analyze-only PCAP` | Skip capture; analyse existing file  | —                             |
| `--with-echo`         | Run local UDP server/client exchange | off                           |
| `-v, --verbose`       | Debug logging                        | off                           |

## Project Structure

```
WireShark-Lab3/
├── udp_lab.py            # CLI entry point
├── udp_server.py         # Simple UDP echo server (optional)
├── udp_client.py         # Simple UDP client (optional)
├── requirements.txt
├── README.md
└── udp_lab/              # Analysis package
    ├── __init__.py
    ├── config.py          # Centralised constants
    ├── models.py          # UDPPacketInfo & AnalysisResults dataclasses
    ├── capture.py         # Interface detection & tshark management
    ├── network.py         # nslookup wrapper
    ├── analyzer.py        # PCAP parsing & packet classification
    └── report.py          # Lab-report generation (stdout + Markdown)
```

## Lab Questions Answered

The generated report addresses all seven questions from the Wireshark UDP Lab v8.1:

1. **First UDP segment** – packet number, application-layer protocol, UDP header fields and their names.
2. **Header field sizes** – each field is 2 bytes (16 bits); total header is 8 bytes.
3. **Length field** – value observed and relationship to payload size.
4. **Maximum UDP payload** – 65,535 − 8 = 65,527 bytes.
5. **Largest source port** – 65,535 (2¹⁶ − 1).
6. **IP protocol number** – 17 for UDP.
7. **Port-number relationship** – source/destination ports swap between request and response.

## Security Notes

- **No shell injection:** All subprocess commands are built as Python lists (`subprocess.run([...])`) — no user input is interpolated into shell strings.
- **Hard-coded BPF filter:** The capture filter `udp` is a constant; it cannot be influenced by external input.
- **Elevated privileges:** `sudo` is only needed for live capture; offline analysis runs without elevated privileges.
