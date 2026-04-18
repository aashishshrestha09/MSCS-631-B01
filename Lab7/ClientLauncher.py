"""ClientLauncher starts the RTSP/RTP video streaming client.

Usage: python ClientLauncher.py <server_host> <server_port> <RTP_port> <video_file>
"""

import sys
import tkinter as tk
from Client import Client


def main():
    if len(sys.argv) != 5:
        print("Usage: python ClientLauncher.py "
              "<server_host> <server_port> <RTP_port> <video_file>")
        sys.exit(1)

    serverAddr = sys.argv[1]
    serverPort = sys.argv[2]
    rtpPort = sys.argv[3]
    fileName = sys.argv[4]

    root = tk.Tk()
    root.title("RTSP/RTP Video Streaming Client")
    root.configure(bg='#2b2b2b')
    root.geometry("420x380")

    Client(root, serverAddr, serverPort, rtpPort, fileName)

    root.mainloop()


if __name__ == "__main__":
    main()
