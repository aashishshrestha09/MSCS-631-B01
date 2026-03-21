#!/usr/bin/env python3
"""Simple UDP client – sends a message to 127.0.0.1:9999 and waits for a reply.

Used by ``udp_lab.py --with-echo`` alongside ``udp_server.py``.
"""

import socket


def main() -> None:
    server_address = ("127.0.0.1", 9999)
    message = "Hello, UDP server!"
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(message.encode(), server_address)
        sock.settimeout(5)
        try:
            data, addr = sock.recvfrom(4096)
            print(f"Received from {addr}: {data.decode()}")
        except socket.timeout:
            print("No response received.")


if __name__ == "__main__":
    main()
