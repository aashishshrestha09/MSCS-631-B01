# Lab 6 – ICMP Traceroute

## Overview

This lab implements a traceroute application using raw ICMP echo-request and reply messages in Python. The program discovers the path (sequence of routers) between the local host and any target host by sending packets with incrementally increasing IP TTL values and collecting the resulting ICMP Time-Exceeded and Echo-Reply responses.

## File

| File                | Description                        |
| ------------------- | ---------------------------------- |
| `IcmpTraceroute.py` | Complete traceroute implementation |

## Requirements

- Python 3.7+
- **Root / administrator privileges** are required for raw ICMP sockets.

## Usage

```bash
sudo python3 IcmpTraceroute.py <hostname>
```

### Examples

```bash
sudo python3 IcmpTraceroute.py google.com
sudo python3 IcmpTraceroute.py 8.8.8.8
sudo python3 IcmpTraceroute.py cs.mit.edu
sudo python3 IcmpTraceroute.py bbc.co.uk
```

## How It Works

1. The program calls `build_packet()` to craft an ICMP echo-request packet that embeds a high-resolution timestamp in its payload.
2. The packet is sent via a raw socket whose `IP_TTL` socket option is set to the current hop count (starting at 1).
3. Each intermediate router that discards the packet (because TTL reaches 0) returns an **ICMP Time-Exceeded** message (type 11). The program extracts the responding router's IP address and computes the round-trip time.
4. When the destination host receives the echo-request it returns an **ICMP Echo-Reply** (type 0), ending the route discovery.
5. The program retries each TTL up to `TRIES` (2) times before reporting a timeout, and stops after `MAX_HOPS` (30) hops.

## ICMP Packet Layout Reference

### Time-Exceeded Reply (type 11) — offset of our timestamp

```
[0 :20]  outer IP header (from the responding router)
[20:28]  ICMP header  (type=11, code=0, checksum, unused)
[28:48]  original IP header  (what we sent)
[48:56]  original ICMP header (first 8 bytes of our echo-request)
[56:64]  ← our payload: timestamp double
```

### Echo-Reply (type 0) — offset of our timestamp

```
[0 :20]  IP header (from the destination)
[20:28]  ICMP header  (type=0, code=0, checksum, ID, seq)
[28:36]  ← our payload: timestamp double
```

## Notes

- Hosts that **block ICMP** traffic will show `* * * Request timed out.`
- Disable your firewall / antivirus if packets are blocked locally.
- Some hops along the path may also suppress ICMP Time-Exceeded responses, producing timeout lines in the middle of an otherwise complete route.
