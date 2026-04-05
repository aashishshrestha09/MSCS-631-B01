"""
MSCS-631 – Lab 6: ICMP Traceroute
==================================
Implements a traceroute application using raw ICMP echo-request / reply
messages.  The program increments the IP TTL field from 1 up to MAX_HOPS:
  • Each router that discards a packet (TTL → 0) replies with an ICMP
    Time-Exceeded message (type 11).
  • The destination host replies with an ICMP Echo-Reply (type 0).

Packet structure for a received ICMP Time-Exceeded (type 11):
  [0 :20] – IP header (outer, from the responding router)
  [20:28] – ICMP header  (type=11, code=0, checksum, unused word)
  [28:48] – Original IP header  (the header we sent)
  [48:56] – Original ICMP header (first 8 bytes of our echo-request)
  [56:64] – Our payload  ← timestamp double lives here

Packet structure for a received ICMP Echo-Reply (type 0):
  [0 :20] – IP header (from the destination)
  [20:28] – ICMP header (type=0, code=0, checksum, ID, seq)
  [28:36] – Our payload ← timestamp double lives here

Usage (requires root / administrator privileges for raw sockets):
  sudo python3 IcmpTraceroute.py <hostname>
"""

from socket import *
import os
import sys
import struct
import time
import select
import binascii

# Constants
ICMP_ECHO_REQUEST   = 8   # ICMP type: Echo Request
ICMP_ECHO_REPLY     = 0   # ICMP type: Echo Reply
ICMP_TIME_EXCEEDED  = 11  # ICMP type: Time Exceeded (TTL expired)
ICMP_DEST_UNREACH   = 3   # ICMP type: Destination Unreachable

MAX_HOPS = 30
TIMEOUT  = 2.0
TRIES    = 2


# checksum
def checksum(string):
    """
    Compute the Internet Checksum (RFC 1071) over a bytes-like object.
    Returns a 16-bit unsigned integer suitable for embedding in an IP/ICMP
    header.
    """
    csum = 0
    count_to = (len(string) // 2) * 2
    count = 0

    # Sum all 16-bit words
    while count < count_to:
        this_val = string[count + 1] * 256 + string[count]
        csum += this_val
        csum &= 0xFFFFFFFF
        count += 2

    # Add leftover byte (if length is odd)
    if count_to < len(string):
        csum += string[-1]
        csum &= 0xFFFFFFFF

    # Fold 32-bit sum into 16 bits and take one's complement
    csum = (csum >> 16) + (csum & 0xFFFF)
    csum += (csum >> 16)
    answer = ~csum & 0xFFFF
    answer = (answer >> 8) | ((answer & 0xFF) << 8)
    return answer


# build_packet
def build_packet():
    """
    Build a complete ICMP echo-request packet.

    Steps:
      1. Pack a provisional header with a zero checksum placeholder.
      2. Pack an 8-byte payload containing a high-resolution timestamp
         (enables RTT measurement without a separate timer variable).
      3. Compute the checksum over header + payload.
      4. Rebuild the header with the real checksum.
      5. Return the final packet bytes.
    """
    myChecksum = 0
    myID       = os.getpid() & 0xFFFF   # 16-bit process ID as packet ID

    # Step 1 & 2: provisional header + timestamp payload
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, myID, 1)
    data   = struct.pack("d", time.time())          # 8-byte double: send time

    # Step 3: compute checksum
    myChecksum = checksum(header + data)

    # htons byte-swaps on little-endian platforms; macOS also needs masking
    if sys.platform == "darwin":
        myChecksum = htons(myChecksum) & 0xFFFF
    else:
        myChecksum = htons(myChecksum)

    # Step 4: rebuild header with real checksum
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, myID, 1)

    # Step 5: return final packet
    packet = header + data
    return packet


# get_route
def get_route(hostname):
    """
    Perform a traceroute to *hostname* by sending ICMP echo-request packets
    with increasing TTL values (1 … MAX_HOPS).  For each TTL the function
    reports the responding IP address and the measured round-trip time.
    """
    timeLeft    = TIMEOUT
    icmp_proto  = getprotobyname("icmp")

    # Resolve hostname once for the header line
    try:
        destAddr = gethostbyname(hostname)
    except gaierror as exc:
        print(f"traceroute: cannot resolve '{hostname}': {exc}")
        sys.exit(1)

    print(f"\ntraceroute to {hostname} ({destAddr}), {MAX_HOPS} hops max\n")

    for ttl in range(1, MAX_HOPS):
        for tries in range(TRIES):
            timeLeft = TIMEOUT          # reset per-try so it never goes negative
            destAddr = gethostbyname(hostname)

            # Fill in start
            # Make a raw socket named mySocket
            # Raw sockets require root/administrator privileges.
            mySocket = socket(AF_INET, SOCK_RAW, icmp_proto)
            # Fill in end

            mySocket.setsockopt(IPPROTO_IP, IP_TTL, struct.pack('I', ttl))
            mySocket.settimeout(TIMEOUT)

            try:
                d = build_packet()
                mySocket.sendto(d, (hostname, 0))
                t             = time.time()           # send timestamp
                startedSelect = time.time()
                whatReady     = select.select([mySocket], [], [], timeLeft)
                howLongInSelect = (time.time() - startedSelect)

                if whatReady[0] == []:    # Timeout — no response in timeLeft
                    print(f"  {ttl}  * * * Request timed out.")

                recvPacket, addr = mySocket.recvfrom(1024)
                timeReceived = time.time()
                timeLeft     = timeLeft - howLongInSelect

                if timeLeft <= 0:
                    print(f"  {ttl}  * * * Request timed out.")
                    continue

            except timeout:
                continue

            else:
                # Fill in start
                # Fetch the ICMP type from the received IP packet.
                # The IP header is always 20 bytes; the ICMP header follows.
                # Unpack: type(b), code(b), checksum(H), id(H), sequence(h)
                icmp_header = recvPacket[20:28]
                types, code, recv_checksum, packetID, sequence = struct.unpack(
                    "bbHHh", icmp_header
                )
                # Fill in end

                if types == ICMP_TIME_EXCEEDED:
                    # Time-Exceeded: the router discarded our packet.
                    # Layout: [outer IP 20B][ICMP hdr 8B][orig IP 20B]
                    #         [orig ICMP hdr 8B][our payload]
                    # Timestamp is at offset 56 (20+8+20+8).
                    # RFC 792 only requires routers to include 8 bytes of
                    # the original datagram (the ICMP header), so the payload
                    # timestamp may not be present. Fall back to wall-clock.
                    bytes_d  = struct.calcsize("d")
                    payload  = recvPacket[56:56 + bytes_d]
                    if len(payload) == bytes_d:
                        timeSent = struct.unpack("d", payload)[0]
                        rtt_ms   = (timeReceived - timeSent) * 1000
                    else:
                        rtt_ms   = (timeReceived - t) * 1000
                    print(f"  {ttl}  rtt={rtt_ms:.2f} ms  {addr[0]}")
                    break   # move on to next TTL

                elif types == ICMP_DEST_UNREACH:
                    # Destination Unreachable — report and stop.
                    bytes_d  = struct.calcsize("d")
                    payload  = recvPacket[56:56 + bytes_d]
                    if len(payload) == bytes_d:
                        timeSent = struct.unpack("d", payload)[0]
                        rtt_ms   = (timeReceived - timeSent) * 1000
                    else:
                        rtt_ms   = (timeReceived - t) * 1000
                    print(f"  {ttl}  rtt={rtt_ms:.2f} ms  {addr[0]}  "
                          f"(Destination Unreachable – code {code})")
                    return

                elif types == ICMP_ECHO_REPLY:
                    # Echo-Reply: we reached the destination host.
                    # Timestamp is at offset 28 (20 IP + 8 ICMP).
                    bytes_d  = struct.calcsize("d")
                    timeSent = struct.unpack(
                        "d", recvPacket[28:28 + bytes_d]
                    )[0]
                    rtt_ms = (timeReceived - timeSent) * 1000
                    print(f"  {ttl}  rtt={rtt_ms:.2f} ms  {addr[0]}")
                    print(f"\nTraceroute complete — destination {destAddr} reached.")
                    return

                else:
                    # Unexpected ICMP type; log and continue to next TTL.
                    print(f"  {ttl}  Unexpected ICMP type {types} "
                          f"(code {code}) from {addr[0]}")
                    break

            finally:
                mySocket.close()

    print("\nTraceroute complete — maximum hops reached.")


# Entry point
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: sudo python3 IcmpTraceroute.py <hostname>")
        print("  e.g. sudo python3 IcmpTraceroute.py google.com")
        sys.exit(1)

    get_route(sys.argv[1])
