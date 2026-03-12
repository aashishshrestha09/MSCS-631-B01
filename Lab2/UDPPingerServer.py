#!/usr/bin/env python3
"""
UDPPingerServer.py

Simulates ~36% packet loss by randomly discarding incoming datagrams.
Runs indefinitely until interrupted with Ctrl+C.

Usage:
    python UDPPingerServer.py
"""

import random
import socket

HOST = ""          # Bind to all available interfaces
PORT = 12000
BUFFER_SIZE = 1024


def main() -> None:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST, PORT))
    print(f"UDP Ping Server is ready and listening on port {PORT}...")

    try:
        while True:
            # Generate random number in the range of 0 to 10
            rand = random.randint(0, 10)

            # Receive the client packet along with the address it is coming from
            message, address = server_socket.recvfrom(BUFFER_SIZE)

            # Capitalize the message from the client
            message = message.upper()

            # If rand is less than 4, we consider the packet lost and do not respond
            if rand < 4:
                continue

            # Otherwise, the server responds
            server_socket.sendto(message, address)

    except KeyboardInterrupt:
        print("\nServer shutting down gracefully.")
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
