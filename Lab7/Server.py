"""RTSP Server entry point.

Usage: python Server.py <server_port>

Listens for RTSP connections and spawns a ServerWorker thread
for each client.
"""

import sys
import socket
import threading
from ServerWorker import ServerWorker


def main():
    if len(sys.argv) != 2:
        print("Usage: python Server.py <server_port>")
        sys.exit(1)

    server_port = int(sys.argv[1])

    rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rtsp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    rtsp_socket.bind(('', server_port))
    rtsp_socket.listen(5)

    print(f"RTSP Server listening on port {server_port}...")

    while True:
        client_info = {}
        client_info['rtspSocket'] = rtsp_socket.accept()
        addr = client_info['rtspSocket'][1]
        print(f"Connection from {addr}")
        worker = ServerWorker(client_info)
        worker.start()


if __name__ == "__main__":
    main()
