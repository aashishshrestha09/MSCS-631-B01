"""ServerWorker handles an individual RTSP client session.

Processes RTSP requests (SETUP, PLAY, PAUSE, TEARDOWN) and
streams RTP video packets to the client.
"""

import socket
import threading
import random
from RtpPacket import RtpPacket
from VideoStream import VideoStream


class ServerWorker(threading.Thread):
    SETUP = 'SETUP'
    PLAY = 'PLAY'
    PAUSE = 'PAUSE'
    TEARDOWN = 'TEARDOWN'

    INIT = 0
    READY = 1
    PLAYING = 2

    OK_200 = 0
    FILE_NOT_FOUND_404 = 1
    CON_ERR_500 = 2

    def __init__(self, client_info):
        super().__init__(daemon=True)
        self.clientInfo = client_info
        self.state = self.INIT
        self.rtspSocket = self.clientInfo['rtspSocket'][0]
        self.clientAddr = self.clientInfo['rtspSocket'][1]
        self.sessionId = random.randint(100000, 999999)
        self.requestUri = ''
        self.videoStream = None
        self.rtpSocket = None
        self.event = None

    def run(self):
        """Receive and process RTSP requests."""
        while True:
            data = self.rtspSocket.recv(4096)
            if data:
                request = data.decode('utf-8')
                print(f"\nReceived from client:\n{request}")
                self.processRtspRequest(request)
            else:
                break

    def processRtspRequest(self, data):
        """Parse and handle an RTSP request."""
        lines = data.split('\n')
        requestLine = lines[0].split(' ')
        requestType = requestLine[0]
        filename = requestLine[1]
        seq = lines[1].split(' ')

        # Get the RTSP sequence number
        seqNum = int(seq[1])

        if requestType == self.SETUP:
            if self.state == self.INIT:
                print(f"Processing SETUP for {filename}")
                try:
                    self.videoStream = VideoStream(filename)
                    self.state = self.READY
                except IOError:
                    self.replyRtsp(self.FILE_NOT_FOUND_404, seqNum)
                    return

                self.requestUri = filename

                # Get the RTP/UDP port from Transport header
                # Format: "Transport: RTP/UDP; client_port= 25000"
                transportHeader = lines[2]
                self.clientRtpPort = None
                if 'client_port=' in transportHeader:
                    portStr = transportHeader.split('client_port=')[1].strip()
                    self.clientRtpPort = int(portStr)

                if self.clientRtpPort is None:
                    self.replyRtsp(self.CON_ERR_500, seqNum)
                    return

                self.replyRtsp(self.OK_200, seqNum)

        elif requestType == self.PLAY:
            if self.state == self.READY:
                print("Processing PLAY")
                self.state = self.PLAYING

                # Create a UDP socket for RTP packets
                self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

                self.replyRtsp(self.OK_200, seqNum)

                # Start sending RTP packets
                self.event = threading.Event()
                self.event.clear()
                self.worker = threading.Thread(target=self.sendRtp, daemon=True)
                self.worker.start()

        elif requestType == self.PAUSE:
            if self.state == self.PLAYING:
                print("Processing PAUSE")
                self.state = self.READY
                self.event.set()
                self.replyRtsp(self.OK_200, seqNum)

        elif requestType == self.TEARDOWN:
            print("Processing TEARDOWN")
            self.state = self.INIT
            if self.event:
                self.event.set()
            self.replyRtsp(self.OK_200, seqNum)

            if self.rtpSocket:
                self.rtpSocket.close()
            if self.videoStream:
                self.videoStream.close()

    def sendRtp(self):
        """Send RTP packets of video frames at ~20 fps (50ms interval)."""
        while True:
            self.event.wait(0.05)

            # Stop sending if event is set (PAUSE or TEARDOWN)
            if self.event.is_set():
                break

            data = self.videoStream.nextFrame()
            if data:
                frameNumber = self.videoStream.frameNbr()
                try:
                    rtpPacket = RtpPacket()
                    rtpPacket.encode(
                        version=2,
                        padding=0,
                        extension=0,
                        cc=0,
                        seqnum=frameNumber,
                        marker=0,
                        pt=26,          # MJPEG payload type
                        ssrc=0,
                        payload=data
                    )
                    packet = rtpPacket.getPacket()
                    address = (self.clientAddr[0], self.clientRtpPort)
                    self.rtpSocket.sendto(packet, address)
                    print(f"Sent RTP packet #{frameNumber}, "
                          f"{len(data)} bytes")
                except Exception as e:
                    print(f"Error sending RTP packet: {e}")

    def replyRtsp(self, code, seq):
        """Send an RTSP reply to the client."""
        if code == self.OK_200:
            reply = (
                f"RTSP/1.0 200 OK\n"
                f"CSeq: {seq}\n"
                f"Session: {self.sessionId}\n"
            )
            self.rtspSocket.send(reply.encode('utf-8'))
            print(f"Sent RTSP reply: 200 OK")

        elif code == self.FILE_NOT_FOUND_404:
            reply = (
                f"RTSP/1.0 404 FILE NOT FOUND\n"
                f"CSeq: {seq}\n"
            )
            self.rtspSocket.send(reply.encode('utf-8'))
            print(f"Sent RTSP reply: 404 NOT FOUND")

        elif code == self.CON_ERR_500:
            reply = (
                f"RTSP/1.0 500 CONNECTION ERROR\n"
                f"CSeq: {seq}\n"
            )
            self.rtspSocket.send(reply.encode('utf-8'))
            print(f"Sent RTSP reply: 500 CONNECTION ERROR")
