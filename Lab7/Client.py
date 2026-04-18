"""RTSP Client with video display and statistics.

Implements the RTSP client protocol (SETUP, PLAY, PAUSE, TEARDOWN),
receives RTP packets, decodes video frames, and displays them with
a Tkinter GUI. Also tracks and displays streaming statistics
including packet loss rate and video data rate.
"""

import socket
import threading
import time
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from io import BytesIO
from PIL import Image, ImageTk
from RtpPacket import RtpPacket


class Client:
    INIT = 0
    READY = 1
    PLAYING = 2

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3

    def __init__(self, master, serveraddr, serverport, rtpport, filename):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)

        self.serverAddr = serveraddr
        self.serverPort = int(serverport)
        self.rtpPort = int(rtpport)
        self.fileName = filename
        self.rtspSeq = 0
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = False
        self.state = self.INIT

        self.frameNbr = 0
        self.rtpSocket = None
        self.playEvent = None

        # Statistics tracking
        self.totalBytesReceived = 0
        self.totalPacketsReceived = 0
        self.totalPacketsLost = 0
        self.highestSeqNum = 0
        self.startTime = 0
        self.lastPacketTime = 0

        self.setupWidgets()
        self.connectToServer()

    def setupWidgets(self):
        """Build the GUI with control buttons and video display."""
        # Configure ttk styles for colored buttons
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Setup.TButton', background='#4a90d9',
                        foreground='white', font=('Helvetica', 10, 'bold'),
                        padding=6)
        style.map('Setup.TButton',
                  background=[('active', '#357abd')])
        style.configure('Play.TButton', background='#5cb85c',
                        foreground='white', font=('Helvetica', 10, 'bold'),
                        padding=6)
        style.map('Play.TButton',
                  background=[('active', '#449d44')])
        style.configure('Pause.TButton', background='#f0ad4e',
                        foreground='white', font=('Helvetica', 10, 'bold'),
                        padding=6)
        style.map('Pause.TButton',
                  background=[('active', '#ec971f')])
        style.configure('Teardown.TButton', background='#d9534f',
                        foreground='white', font=('Helvetica', 10, 'bold'),
                        padding=6)
        style.map('Teardown.TButton',
                  background=[('active', '#c9302c')])

        # Top frame for buttons
        buttonFrame = tk.Frame(self.master, bg='#2b2b2b')
        buttonFrame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.setup = ttk.Button(buttonFrame, text="Setup", width=10,
                                command=self.setupMovie,
                                style='Setup.TButton')
        self.setup.pack(side=tk.LEFT, padx=5)

        self.start = ttk.Button(buttonFrame, text="Play", width=10,
                                command=self.playMovie,
                                style='Play.TButton')
        self.start.pack(side=tk.LEFT, padx=5)

        self.pause = ttk.Button(buttonFrame, text="Pause", width=10,
                                command=self.pauseMovie,
                                style='Pause.TButton')
        self.pause.pack(side=tk.LEFT, padx=5)

        self.teardown = ttk.Button(buttonFrame, text="Teardown", width=10,
                                   command=self.exitClient,
                                   style='Teardown.TButton')
        self.teardown.pack(side=tk.LEFT, padx=5)

        # Video display label
        self.label = tk.Label(self.master, bg='black', height=20, width=40)
        self.label.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5,
                        pady=5)

        # Statistics display
        self.statsLabel = tk.Label(
            self.master, text="Statistics will appear here...",
            bg='#2b2b2b', fg='#cccccc', font=('Courier', 9),
            anchor='w', justify=tk.LEFT
        )
        self.statsLabel.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=3)

    def connectToServer(self):
        """Connect to the RTSP server."""
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
            print(f"Connected to RTSP server at {self.serverAddr}:{self.serverPort}")
        except Exception as e:
            messagebox.showerror("Connection Error",
                                 f"Failed to connect to server: {e}")

    def setupMovie(self):
        """Send SETUP request to the server."""
        if self.state == self.INIT:
            self.sendRtspRequest(self.SETUP)

    def playMovie(self):
        """Send PLAY request to the server."""
        if self.state == self.READY:
            self.playEvent = threading.Event()
            self.playEvent.clear()

            # Start the RTP receiving thread
            self.playThread = threading.Thread(target=self.listenRtp,
                                               daemon=True)
            self.playThread.start()

            self.sendRtspRequest(self.PLAY)
            self.startTime = time.time()

    def pauseMovie(self):
        """Send PAUSE request to the server."""
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)

    def exitClient(self):
        """Send TEARDOWN request and close the client."""
        self.teardownAcked = True

        try:
            self.sendRtspRequest(self.TEARDOWN)
        except (BrokenPipeError, OSError):
            pass

        if self.playEvent:
            self.playEvent.set()

        # Print final statistics to console
        self.printFinalStats()

        try:
            if self.rtpSocket:
                self.rtpSocket.close()
            self.rtspSocket.close()
        except OSError:
            pass

        self.master.destroy()

    def listenRtp(self):
        """Listen for RTP packets on the UDP socket."""
        while True:
            try:
                data, addr = self.rtpSocket.recvfrom(65536)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)

                    currentSeqNbr = rtpPacket.seqNum()
                    print(f"Received RTP packet #{currentSeqNbr}")

                    # Track packet loss
                    if currentSeqNbr > self.highestSeqNum + 1:
                        lost = currentSeqNbr - self.highestSeqNum - 1
                        self.totalPacketsLost += lost
                    if currentSeqNbr > self.highestSeqNum:
                        self.highestSeqNum = currentSeqNbr

                    self.totalPacketsReceived += 1

                    # Track data received
                    payloadData = rtpPacket.getPayload()
                    self.totalBytesReceived += len(payloadData)
                    self.lastPacketTime = time.time()

                    if currentSeqNbr > self.frameNbr:
                        self.frameNbr = currentSeqNbr
                        self.updateMovie(payloadData)

                    # Update statistics display
                    self.updateStats()

            except socket.timeout:
                # Socket timeout; check if we should stop
                if self.playEvent and self.playEvent.is_set():
                    break
                continue
            except Exception:
                # If teardown was acked, exit gracefully
                if self.teardownAcked:
                    break
                if self.playEvent and self.playEvent.is_set():
                    break

    def updateMovie(self, imageData):
        """Update the video display with a new frame."""
        try:
            photo = ImageTk.PhotoImage(
                Image.open(BytesIO(imageData))
            )
            self.label.configure(image=photo, height=288)
            self.label.image = photo
        except Exception as e:
            print(f"Error displaying frame: {e}")

    def updateStats(self):
        """Update the statistics label in the GUI."""
        elapsed = time.time() - self.startTime if self.startTime else 0

        if elapsed > 0:
            dataRateBps = (self.totalBytesReceived * 8) / elapsed
            dataRateKbps = dataRateBps / 1000
        else:
            dataRateKbps = 0

        totalExpected = self.highestSeqNum
        if totalExpected > 0:
            lossRate = (self.totalPacketsLost / totalExpected) * 100
        else:
            lossRate = 0

        fps = self.totalPacketsReceived / elapsed if elapsed > 0 else 0

        statsText = (
            f"Packets Received: {self.totalPacketsReceived} | "
            f"Packets Lost: {self.totalPacketsLost} | "
            f"Loss Rate: {lossRate:.1f}% | "
            f"Data Rate: {dataRateKbps:.1f} kbps | "
            f"FPS: {fps:.1f} | "
            f"Total Data: {self.totalBytesReceived / 1024:.1f} KB"
        )

        try:
            self.statsLabel.configure(text=statsText)
        except tk.TclError:
            pass  # Window may be closing

    def printFinalStats(self):
        """Print final streaming statistics to console."""
        elapsed = time.time() - self.startTime if self.startTime else 0
        print("\n" + "=" * 60)
        print("STREAMING SESSION STATISTICS")
        print("=" * 60)
        print(f"Total Packets Received: {self.totalPacketsReceived}")
        print(f"Total Packets Lost:     {self.totalPacketsLost}")

        totalExpected = self.highestSeqNum
        if totalExpected > 0:
            lossRate = (self.totalPacketsLost / totalExpected) * 100
        else:
            lossRate = 0
        print(f"Packet Loss Rate:       {lossRate:.2f}%")

        print(f"Total Bytes Received:   {self.totalBytesReceived}")
        if elapsed > 0:
            print(f"Session Duration:       {elapsed:.2f} seconds")
            dataRateBps = (self.totalBytesReceived * 8) / elapsed
            print(f"Video Data Rate:        {dataRateBps:.0f} bps "
                  f"({dataRateBps / 1000:.1f} kbps)")
            fps = self.totalPacketsReceived / elapsed
            print(f"Average Frame Rate:     {fps:.1f} fps")
        print("=" * 60 + "\n")

    def sendRtspRequest(self, requestCode):
        """Construct and send an RTSP request."""
        self.rtspSeq += 1

        if requestCode == self.SETUP and self.state == self.INIT:
            self.requestSent = self.SETUP
            request = (
                f"SETUP {self.fileName} RTSP/1.0\n"
                f"CSeq: {self.rtspSeq}\n"
                f"Transport: RTP/UDP; client_port= {self.rtpPort}\n"
            )
            print(f"\nSending SETUP request:\n{request}")
            self.rtspSocket.send(request.encode('utf-8'))

            # Parse the server reply
            self.recvRtspReply()

        elif requestCode == self.PLAY and self.state == self.READY:
            self.requestSent = self.PLAY
            request = (
                f"PLAY {self.fileName} RTSP/1.0\n"
                f"CSeq: {self.rtspSeq}\n"
                f"Session: {self.sessionId}\n"
            )
            print(f"\nSending PLAY request:\n{request}")
            self.rtspSocket.send(request.encode('utf-8'))
            self.recvRtspReply()

        elif requestCode == self.PAUSE and self.state == self.PLAYING:
            self.requestSent = self.PAUSE
            request = (
                f"PAUSE {self.fileName} RTSP/1.0\n"
                f"CSeq: {self.rtspSeq}\n"
                f"Session: {self.sessionId}\n"
            )
            print(f"\nSending PAUSE request:\n{request}")
            self.rtspSocket.send(request.encode('utf-8'))
            self.recvRtspReply()

        elif requestCode == self.TEARDOWN:
            self.requestSent = self.TEARDOWN
            request = (
                f"TEARDOWN {self.fileName} RTSP/1.0\n"
                f"CSeq: {self.rtspSeq}\n"
                f"Session: {self.sessionId}\n"
            )
            print(f"\nSending TEARDOWN request:\n{request}")
            self.rtspSocket.send(request.encode('utf-8'))
            self.recvRtspReply()

    def recvRtspReply(self):
        """Receive and parse the server's RTSP reply."""
        try:
            reply = self.rtspSocket.recv(4096)
            if reply:
                self.parseRtspReply(reply.decode('utf-8'))
        except Exception as e:
            print(f"Error receiving RTSP reply: {e}")

    def parseRtspReply(self, data):
        """Parse the RTSP reply and update client state."""
        print(f"\nReceived RTSP reply:\n{data}")
        lines = data.split('\n')
        seqNum = int(lines[1].split(' ')[1])

        # Verify sequence number
        if seqNum == self.rtspSeq:
            session = int(lines[2].split(' ')[1])

            if self.sessionId == 0:
                self.sessionId = session

            if self.sessionId == session:
                statusLine = lines[0].split(' ')
                statusCode = int(statusLine[1])

                if statusCode == 200:
                    if self.requestSent == self.SETUP:
                        self.state = self.READY
                        print("State -> READY")
                        self.openRtpPort()

                    elif self.requestSent == self.PLAY:
                        self.state = self.PLAYING
                        print("State -> PLAYING")

                    elif self.requestSent == self.PAUSE:
                        self.state = self.READY
                        print("State -> READY")
                        if self.playEvent:
                            self.playEvent.set()

                    elif self.requestSent == self.TEARDOWN:
                        self.state = self.INIT
                        print("State -> INIT")

    def openRtpPort(self):
        """Create the RTP UDP socket for receiving video data."""
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtpSocket.settimeout(0.5)
        try:
            self.rtpSocket.bind(('', self.rtpPort))
            print(f"RTP socket bound to port {self.rtpPort}")
        except Exception as e:
            messagebox.showerror("RTP Error",
                                 f"Unable to bind RTP port: {e}")

    def handler(self):
        """Handle window close event."""
        if not self.teardownAcked:
            if self.state == self.PLAYING:
                self.pauseMovie()
            if messagebox.askokcancel("Quit", "Do you want to quit?"):
                self.exitClient()
