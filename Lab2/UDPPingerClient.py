#!/usr/bin/env python3
"""
UDPPingerClient.py

Sends 10 ping messages to the UDP Ping Server, reports round-trip time (RTT)
for each successful reply, prints "Request timed out" for dropped packets,
and displays aggregate statistics (packet loss %, min/max/avg RTT) at the end.

Usage:
    python UDPPingerClient.py

Message format:
    Ping <sequence_number> <send_timestamp>
"""

import socket
import time

# Configuration
SERVER_HOST = "127.0.0.1"  # Change to a remote IP when testing across machines
SERVER_PORT = 12000
TIMEOUT = 1                 # Seconds to wait for a reply before declaring loss
NUM_PINGS = 10
BUFFER_SIZE = 1024


def main() -> None:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(TIMEOUT)

    rtt_list: list[float] = []
    packets_sent = 0
    packets_received = 0

    print(f"--- Pinging {SERVER_HOST} on port {SERVER_PORT} ---\n")

    try:
        for sequence_number in range(1, NUM_PINGS + 1):
            # Build the ping message: "Ping <seq_num> <send_timestamp>"
            send_time = time.time()
            message = f"Ping {sequence_number} {send_time}"

            try:
                # Send the ping message to the server (no connection needed — UDP)
                client_socket.sendto(message.encode(), (SERVER_HOST, SERVER_PORT))
                packets_sent += 1

                # Wait up to TIMEOUT seconds for a reply
                response, _ = client_socket.recvfrom(BUFFER_SIZE)
                recv_time = time.time()

                # Calculate and record round-trip time
                rtt = recv_time - send_time
                rtt_list.append(rtt)
                packets_received += 1

                print(f"Ping {sequence_number}: Reply from {SERVER_HOST}  RTT = {rtt:.6f} seconds")
                print(f"  Message: {response.decode()}")

            except socket.timeout:
                print(f"Ping {sequence_number}: Request timed out")

    finally:
        client_socket.close()

    # Summary Statistics
    packets_lost = packets_sent - packets_received
    loss_rate = (packets_lost / packets_sent * 100) if packets_sent > 0 else 0.0

    print(f"\n--- Ping Statistics for {SERVER_HOST} ---")
    print(
        f"Packets: Sent = {packets_sent}, Received = {packets_received}, "
        f"Lost = {packets_lost} ({loss_rate:.0f}% loss)"
    )

    if rtt_list:
        min_rtt = min(rtt_list)
        max_rtt = max(rtt_list)
        avg_rtt = sum(rtt_list) / len(rtt_list)
        print("Round-trip times (seconds):")
        print(f"  Minimum = {min_rtt:.6f}s  |  Maximum = {max_rtt:.6f}s  |  Average = {avg_rtt:.6f}s")
    else:
        print("No replies received — all packets were lost.")


if __name__ == "__main__":
    main()
