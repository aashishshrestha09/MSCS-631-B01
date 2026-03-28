"""
This program implements a Ping application using ICMP echo request and reply
messages. It sends ICMP echo requests to a specified host, measures round-trip
time (RTT), records packet loss, and prints a statistical summary.

Usage:
    python3 ICMPPinger.py <hostname> [count]

    - hostname: target host (IP or domain name)
    - count:    number of pings to send (default: 10)

On macOS, uses SOCK_DGRAM (non-privileged ICMP) so sudo is not required.
On Linux/Windows, falls back to SOCK_RAW which may need root/admin privileges.
"""

from socket import *
import os
import sys
import struct
import time
import select

ICMP_ECHO_REQUEST = 8
ICMP_ECHO_REPLY = 0


def checksum(data):
    """
    Compute the Internet Checksum of the supplied data.
    Works with Python 3 bytes objects (indexing returns int).
    """
    csum = 0
    count_to = (len(data) // 2) * 2
    count = 0

    while count < count_to:
        this_val = data[count + 1] * 256 + data[count]
        csum = csum + this_val
        csum = csum & 0xFFFFFFFF
        count += 2

    if count_to < len(data):
        csum = csum + data[-1]
        csum = csum & 0xFFFFFFFF

    csum = (csum >> 16) + (csum & 0xFFFF)
    csum = csum + (csum >> 16)
    answer = ~csum & 0xFFFF
    answer = (answer >> 8) | ((answer & 0xFF) << 8)
    return answer


def receiveOnePing(mySocket, ID, timeout, destAddr, useDgram=False):
    """
    Receive an ICMP echo reply and return the round-trip delay in seconds,
    along with TTL and packet size. Returns None on timeout.
    """
    timeLeft = timeout

    while True:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = time.time() - startedSelect

        if whatReady[0] == []:  # Timeout
            return None

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        # ---- Fill in start ----
        # Auto-detect whether the IP header is present.
        # If the first nibble is 0x4 (IPv4), we have a 20-byte IP header.
        hasIPHeader = (recPacket[0] >> 4) == 4
        if hasIPHeader:
            ipOffset = 20
            ipTTL = struct.unpack("B", recPacket[8:9])[0]
        else:
            ipOffset = 0
            # TTL unavailable without IP header; use socket default.
            try:
                ipTTL = mySocket.getsockopt(IPPROTO_IP, IP_TTL)
            except Exception:
                ipTTL = 0

        icmpHeader = recPacket[ipOffset : ipOffset + 8]
        icmpType, icmpCode, icmpChecksum, icmpID, icmpSequence = struct.unpack(
            "bbHHh", icmpHeader
        )

        # On SOCK_DGRAM the kernel may rewrite the ICMP ID, so skip
        # the ID check in that mode (kernel already filters for us).
        idMatch = (not useDgram and icmpID == ID) or useDgram

        if icmpType == ICMP_ECHO_REPLY and idMatch:
            bytesDouble = struct.calcsize("d")
            payloadStart = ipOffset + 8
            timeSent = struct.unpack(
                "d", recPacket[payloadStart : payloadStart + bytesDouble]
            )[0]
            rtt = timeReceived - timeSent
            packetSize = len(recPacket) - ipOffset
            return (rtt, ipTTL, packetSize)
        # ---- Fill in end ----

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return None


def sendOnePing(mySocket, destAddr, ID, sequence):
    """
    Build and send one ICMP echo request packet.
    """
    # Header: type (8), code (8), checksum (16), id (16), sequence (16)
    myChecksum = 0

    # Dummy header with zero checksum
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, sequence)
    data = struct.pack("d", time.time())

    # Calculate checksum over header + data
    myChecksum = checksum(header + data)

    if sys.platform == "darwin":
        myChecksum = htons(myChecksum) & 0xFFFF
    else:
        myChecksum = htons(myChecksum)

    # Rebuild header with correct checksum
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, sequence)
    packet = header + data

    mySocket.sendto(packet, (destAddr, 1))


def doOnePing(destAddr, timeout, sequence):
    """
    Open an ICMP socket, send one ping, receive the reply, and return
    the result.  On macOS uses SOCK_DGRAM (no root needed); elsewhere
    falls back to SOCK_RAW.
    """
    icmp = getprotobyname("icmp")
    useDgram = False

    # Try non-privileged DGRAM ICMP first (works on macOS without sudo).
    try:
        mySocket = socket(AF_INET, SOCK_DGRAM, icmp)
        useDgram = True
    except PermissionError:
        mySocket = socket(AF_INET, SOCK_RAW, icmp)

    myID = os.getpid() & 0xFFFF

    sendOnePing(mySocket, destAddr, myID, sequence)
    result = receiveOnePing(mySocket, myID, timeout, destAddr, useDgram)

    mySocket.close()
    return result


def ping(host, timeout=1, count=10):
    """
    Ping a host `count` times, printing per-packet results and a final
    statistical summary (min/max/avg RTT and packet loss).
    """
    dest = gethostbyname(host)
    print(f"\nPinging {host} ({dest}) with ICMP echo requests:")
    print(f"{'─' * 55}")

    rtts = []
    sent = 0
    received = 0

    for seq in range(1, count + 1):
        sent += 1
        result = doOnePing(dest, timeout, seq)

        if result is None:
            print(f"Request {seq}: Request timed out.")
        else:
            rtt_sec, ttl, pkt_size = result
            rtt_ms = rtt_sec * 1000
            rtts.append(rtt_ms)
            received += 1
            print(
                f"Reply from {dest}: bytes={pkt_size}  time={rtt_ms:.2f}ms  TTL={ttl}  seq={seq}"
            )

        # Wait ~1 second between pings (minus time already spent)
        if seq < count:
            time.sleep(1)

    # --- Statistics ---
    lost = sent - received
    loss_pct = (lost / sent) * 100 if sent > 0 else 0

    print(f"\n{'─' * 55}")
    print(f"Ping statistics for {host} ({dest}):")
    print(
        f"  Packets: Sent = {sent}, Received = {received}, "
        f"Lost = {lost} ({loss_pct:.0f}% loss)"
    )

    if rtts:
        min_rtt = min(rtts)
        max_rtt = max(rtts)
        avg_rtt = sum(rtts) / len(rtts)
        print(f"Approximate round trip times:")
        print(
            f"  Minimum = {min_rtt:.2f}ms, Maximum = {max_rtt:.2f}ms, "
            f"Average = {avg_rtt:.2f}ms"
        )
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 ICMPPinger.py <hostname> [count]")
        sys.exit(1)

    host = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) >= 3 else 10
    ping(host, count=count)
