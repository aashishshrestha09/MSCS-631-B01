# Wireshark Lab 4 - 802.11 WiFi

**Course:** MSCS-631 Advanced Computer Networks  
**Student:** [Your Name]  
**Date:** March 28, 2026  
**Reference:** _Computer Networking: A Top-Down Approach_, 8th ed., J. F. Kurose & K. W. Ross, Section 7.3  
**Trace file:** `Wireshark_802_11.pcapng` (from [wireshark-traces-8.1.zip](http://gaia.cs.umass.edu/wireshark-labs/wireshark-traces-8.1.zip))

---

## Methodology

The provided trace file was downloaded from the Kurose/Ross lab archive and analyzed programmatically using **Python 3** and **pyshark** (a Python wrapper for tshark/Wireshark dissectors). This approach allows reproducible, scriptable analysis of 802.11 frames without requiring a graphical Wireshark interface

```bash
pip install pyshark requests
python wifi_lab.py
```

---

## 1. Beacon Frames

Beacon frames were isolated using the display filter equivalent `wlan.fc.type_subtype == 0x0008`.

**Script output (beacon SSID summary):**

```
========================================================================
  Wireshark Lab 4 - 802.11 WiFi  |  Analysis Report
========================================================================

Total frames captured: 11055
  Beacon frames:     5765
  Management frames: 6092
  Control frames:    2233
  Data frames:       2730

Beacon SSID Summary:
  30 Munroe St ......... 564 beacons
  linksys12 ............ 493 beacons
  (other SSIDs) ........ remaining
```

### Question 1

**What are the SSIDs of the two access points that are issuing most of the beacon frames in this trace?**

| SSID             | Beacon Count |
| ---------------- | -----------: |
| **30 Munroe St** |          564 |
| **linksys12**    |          493 |

### Question 2

**What 802.11 channel is being used by both access points?**

Both APs are operating on **channel 6** (2.437 GHz), extracted from the Radiotap radio information header of each beacon frame.

```python
# pyshark extraction
channel = packet.wlan_radio.channel  # => '6'
```

### Question 3

**What is the interval of time between the transmissions of beacon frames (at t = 0.085474)?**

The Beacon Interval field is **0.102400 seconds** (100 TU, where 1 TU = 1024 microseconds).

```
Beacon at t=0.085474:
  SSID .............. 30 Munroe St
  Beacon Interval ... 0.102400 s  (100 TU)
  Source MAC ........ 00:16:b6:f7:1d:51
```

### Question 4

**What (in hex) is the source MAC address on the beacon frame at t = 0.085474?**

Source MAC: **00:16:b6:f7:1d:51**

### Question 5

**What (in hex) is the destination MAC address on the beacon frame from 30 Munroe St?**

Destination MAC: **ff:ff:ff:ff:ff:ff** (broadcast, since beacons are sent to all stations).

### Question 6

**What (in hex) is the MAC BSS ID on the beacon frame from 30 Munroe St?**

BSS ID: **00:16:b6:f7:1d:51** (same as the AP's own MAC address, standard for infrastructure BSS).

```
30 Munroe St Beacon Frame:
  Source MAC (addr2) .. 00:16:b6:f7:1d:51
  Dest MAC (addr1) .... ff:ff:ff:ff:ff:ff
  BSS ID (addr3) ...... 00:16:b6:f7:1d:51
```

---

## 2. Data Transfer

### Question 7

**What are the Supported Rates and Extended Supported Rates in the 30 Munroe St beacon?**

- **Supported Rates (Mbps):** 1(B), 2(B), 5.5(B), 11(B), 6, 9, 12, 18
- **Extended Supported Rates (Mbps):** 24, 36, 48, 54

The (B) tag marks basic/mandatory rates.

### Question 8

**What are the three MAC address fields in the 802.11 frame containing the TCP SYN for `alice.txt`? What are the IP addresses?**

```
TCP SYN frame (near t=24.82):
  Address 1 (Receiver) .... 00:16:b6:f7:1d:51  [AP / 30 Munroe St]
  Address 2 (Transmitter) . 00:13:02:d1:b6:4f  [Wireless host]
  Address 3 (BSS ID) ...... 00:16:b6:f4:eb:a8  [First-hop router]
  Source IP ............... 192.168.1.100       [Wireless host]
  Destination IP .......... 128.119.245.12      [gaia.cs.umass.edu]
```

| Field                   | Value               | Device            |
| ----------------------- | ------------------- | ----------------- |
| Address 1 (Receiver)    | `00:16:b6:f7:1d:51` | AP (30 Munroe St) |
| Address 2 (Transmitter) | `00:13:02:d1:b6:4f` | Wireless host     |
| Address 3 (BSS ID)      | `00:16:b6:f4:eb:a8` | First-hop router  |
| Source IP               | `192.168.1.100`     | Wireless host     |
| Destination IP          | `128.119.245.12`    | gaia.cs.umass.edu |

### Question 9

**Does the destination IP correspond to the host, AP, first-hop router, or destination web server?**

The destination IP **128.119.245.12** is `gaia.cs.umass.edu`, which is the **destination web server**, not the AP or router.

### Question 10

**What are the three MAC address fields in the TCP SYN-ACK frame?**

```
TCP SYN-ACK frame (near t=24.83):
  Address 1 (Receiver) .... 00:13:02:d1:b6:4f  [Wireless host]
  Address 2 (Transmitter) . 00:16:b6:f7:1d:51  [AP]
  Address 3 (Source) ...... 00:16:b6:f4:eb:a8  [First-hop router]
```

For frames from the Distribution System (AP to host), Address 1 is the receiving station, Address 2 is the AP transmitter, and Address 3 is the original sender on the wired side.

---

## 3. Disconnect and Reconnect

### Question 11

**What two actions does the host take after t = 49 to end the association?**

1. A **DHCP Release** message is sent (IP layer) to release the host's IP address.
2. A **Deauthentication** frame is sent (802.11 layer) to formally end the wireless association with the 30 Munroe St AP.

```
Disconnect sequence (near t=49.58):
  Frame type: Deauthentication (type_subtype=0x000c)
  Source:     00:13:02:d1:b6:4f  [host]
  Dest:       00:16:b6:f7:1d:51  [AP]
```

### Question 12

**What authentication method is requested by the host near t = 63?**

Authentication Algorithm: **Open System (0)**. No shared key is required at the 802.11 level.

### Question 13

**What is the Authentication SEQ value sent from the host to the AP?**

Authentication SEQ = **0x0001**. In Open System authentication, the first frame from the host carries SEQ = 1.

### Question 14

**What is the AP's response to the authentication request?**

The AP responds with **status code 0 (Successful)**, accepting the host's authentication.

### Question 15

**What is the Authentication SEQ value sent from the AP to the host?**

Authentication SEQ = **0x0002**. The AP's reply is the second frame in the Open System exchange.

```
Authentication Exchange (near t=63.06):
  [Host -> AP] Auth SEQ=1, Algorithm=Open System
  [AP -> Host] Auth SEQ=2, Status=Successful (0)
```

### Question 16

**What are the supported rates in the Association Request from the host?**

- **Supported Rates (Mbps):** 1(B), 2(B), 5.5(B), 11(B), 6, 9, 12, 18
- **Extended Supported Rates (Mbps):** 24, 36, 48, 54

### Question 17

**What is the status of the Association Response?**

The Association Response has **status code 0 (Successful)**, confirming the host is now associated with the AP.

```
Association (near t=63.07):
  [Host -> AP] Association Request  (Supported Rates: 1,2,5.5,11,6,9,12,18,24,36,48,54)
  [AP -> Host] Association Response (Status: Successful)
```

### Question 18

**What is the fastest Extended Supported Rate common to both the host and the AP?**

**54 Mbps** is the fastest Extended Supported Rate advertised by both the AP (beacon) and the host (Association Request). This is the maximum data rate for 802.11g.

---

## References

1. Kurose, J. F. & Ross, K. W. (2020). _Computer Networking: A Top-Down Approach_ (8th ed.). Pearson. Section 7.3.
2. IEEE Std 802.11-2020, Section 9.2.4.1.
3. Brenner, P. "A Technical Tutorial on the 802.11 Protocol." Breezecom Communications.
