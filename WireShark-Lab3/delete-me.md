$ python udp_lab.py 
2026-03-21 18:51:10,662 [INFO] udp_lab.capture: Selected capture interface: \Device\NPF_{702F11F5-C29B-4BCC-9383-110E2FC13B2C}
2026-03-21 18:51:10,662 [INFO] udp_lab.capture: Starting capture: tshark -i \Device\NPF_{70k\capture\capture.py", line 170, in _setup_2F11F5-C29B-4BCC-9383-110E2FC13B2C} -a duration:20 -f udp -w data/udp_capture.pcap
2026-03-21 18:51:12,672 [INFO] udp_lab.network: Running: nslookup www.nyu.edu
2026-03-21 18:51:12,899 [INFO] udp_lab: nslookup completed                                  715, in get_event_loop
2026-03-21 18:51:12,900 [INFO] udp_lab: Waiting for capture to complete (up to 20s) …
2026-03-21 18:51:32,205 [INFO] udp_lab.analyzer: Analysing UDP packets in data/udp_capture.pcap …
2026-03-21 18:51:33,169 [INFO] udp_lab.analyzer: Parsed 56 UDP packets (9 DNS queries, 9 DNS responses, 38 other)

======================================================================
  Wireshark Lab 3 – UDP  |  Analysis Report
======================================================================

Packets captured: 56
  DNS queries:    9
  DNS responses:  9
  Other UDP:      38

First UDP packet:
  Packet #1  (UDP (raw))
    Source IP ......... 10.11.5.172
    Destination IP .... 10.11.7.255
    Source Port ....... 59482
    Destination Port .. 15600
    UDP Length ........ 43 bytes
    Checksum .......... 0x7055
    IP Protocol ....... 17
    TTL ............... 64

----------------------------------------------------------------------
Question 1:
  a) The first UDP segment is packet #1 in the trace.
  b) Application-layer protocol: UDP (raw).
  c) The UDP header contains 4 fields:
       1. Source Port
       2. Destination Port
       3. Length
       4. Checksum

Question 2:
  Each of the four UDP header fields is exactly 2 bytes (16 bits) long.
  Total UDP header size = 4 × 2 = 8 bytes.

Question 3:
  The Length field value is 43 bytes.
  This counts the UDP header (8 bytes) plus the payload (35 bytes).
  Number of payload bytes = Length − 8 = 35 bytes.

Question 4:
  The Length field is 16 bits → maximum value 65,535.
  Maximum payload = 65,535 − 8 (header) = 65,527 bytes.

Question 5:
  The source port field is 16 bits → largest possible port = 65,535.

Question 6:
  The IP header Protocol field value is 17 (decimal).
  The protocol number for UDP is 17.

Question 7:
  Request  (packet #2): src port 63587 → dst port 53
  Response (packet #3): src port 53 → dst port 63587
  The source port of the request becomes the destination port of the
  response, and vice-versa.

----------------------------------------------------------------------

── nslookup output ──
Server:  nexuswifi.com
Address:  10.11.0.1

Name:    d1q5ku5vnwkd2k.cloudfront.net
Addresses:  2600:9000:233d:e600:1:f7e2:cb00:93a1
          2600:9000:233d:9c00:1:f7e2:cb00:93a1
          2600:9000:233d:8a00:1:f7e2:cb00:93a1
          2600:9000:233d:5000:1:f7e2:cb00:93a1
          2600:9000:233d:3800:1:f7e2:cb00:93a1
          2600:9000:233d:d400:1:f7e2:cb00:93a1
          2600:9000:233d:bc00:1:f7e2:cb00:93a1
          2600:9000:233d:b600:1:f7e2:cb00:93a1
          108.159.227.49
          108.159.227.17
          108.159.227.127
          108.159.227.93
Aliases:  www.nyu.edu

Non-authoritative answer:


2026-03-21 18:51:33,190 [INFO] udp_lab.report: Markdown report saved to WiresharkLab3_UDP_Report.md

Markdown report saved to WiresharkLab3_UDP_Report.md
(.venv)