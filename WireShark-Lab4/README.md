# Wireshark Lab 4 – 802.11 WiFi

## Overview

This lab explores the **802.11 wireless (WiFi) protocol** by analysing captured 802.11 frames. The toolkit automates the complete workflow:

1. **Download** the provided trace file from the Kurose/Ross lab archive.
2. **Parse** the `.pcapng` file with `pyshark`.
3. **Answer** all 18 lab questions and produce a formatted Markdown report.

## Prerequisites

| Requirement        | Notes                                  |
| ------------------ | -------------------------------------- |
| Python ≥ 3.10      | `python3 --version`                    |
| Wireshark / tshark | `tshark --version` — must be on `PATH` |
| pyshark ≥ 0.6      | Installed via `requirements.txt`       |
| requests ≥ 2.28    | Installed via `requirements.txt`       |

## Installation

```bash
cd WireShark-Lab4
pip install -r requirements.txt
```

## Usage

### Automatic Download & Analysis (default)

```bash
python wifi_lab.py
```

This downloads the trace file from the Kurose/Ross archive and analyses it.

### Analyse an Existing File

```bash
python wifi_lab.py --analyze-only path/to/capture.pcapng
```

### Quick Start (shell script)

```bash
./run_lab4.sh
```

Creates a virtual environment, installs dependencies, and runs the analysis.

### CLI Options

| Option                | Description                             |
| --------------------- | --------------------------------------- |
| `--analyze-only PCAP` | Skip download; analyse an existing file |
| `--report PATH`       | Markdown report output path             |
| `-v, --verbose`       | Enable debug logging                    |

## Project Structure

```
WireShark-Lab4/
├── wifi_lab.py                  # CLI entry point
├── wifi_lab/                    # Analysis package
│   ├── __init__.py
│   ├── analyzer.py              # PCAP parsing & Q1-Q18 analysis
│   ├── capture.py               # Trace file download
│   ├── config.py                # Constants
│   ├── models.py                # Data classes
│   └── report.py                # Report generation (stdout + Markdown)
├── data/                        # Downloaded trace files
├── requirements.txt
├── run_lab4.sh                  # Quick-start script
├── README.md
└── WiresharkLab4_WiFi_Report.md # Generated report
```

## Questions Answered

The script answers all 18 questions from the Kurose/Ross 802.11 Wireshark lab (v8.1):

1. SSIDs of the two most common beacon-advertising APs
2. 802.11 channel used by both APs
3. Beacon interval
4. Source MAC address on a beacon frame
5. Destination MAC address on the 30 Munroe St beacon
6. BSS ID on the 30 Munroe St beacon
7. Supported and Extended Supported Rates
8. Three MAC addresses in the TCP SYN frame (alice.txt)
9. Destination IP of the TCP SYN
10. Three MAC addresses in the TCP SYN-ACK frame
11. Actions taken to end association after t = 49
12. Authentication method requested
13. Authentication SEQ (host → AP)
14. AP's authentication response
15. Authentication SEQ (AP → host)
16. Supported rates in Association Request
17. Association Response status
18. Fastest Extended Supported Rate comparison

## Reference

- _Computer Networking: A Top-Down Approach_, 8th ed., J. F. Kurose & K. W. Ross, §7.3
- IEEE 802.11-2020 Standard, Section 9.2.4.1
- Pablo Brenner, "A Technical Tutorial on the 802.11 Protocol"
