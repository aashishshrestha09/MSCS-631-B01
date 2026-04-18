"""RTP Packet handling for video streaming.

Handles encoding (packetization) and decoding (de-packetization) of
RTP packets per RFC 3550.
"""

import time
import struct

class RtpPacket:
    HEADER_SIZE = 12  # bytes

    def __init__(self):
        self.header = bytearray(self.HEADER_SIZE)
        self.payload = b''

    def encode(self, version, padding, extension, cc, seqnum,
               marker, pt, ssrc, payload):
        """Encode the RTP packet with header fields and payload.

        Args:
            version: RTP version (2).
            padding: Padding flag (0).
            extension: Extension flag (0).
            cc: CSRC count (0).
            seqnum: Sequence number (frame number).
            marker: Marker bit (0).
            pt: Payload type (26 for MJPEG).
            ssrc: Synchronization source identifier.
            payload: The video frame data (bytes).
        """
        timestamp = int(time.time())
        header = bytearray(self.HEADER_SIZE)

        # Byte 0: V(2) | P(1) | X(1) | CC(4)
        header[0] = (version << 6) | (padding << 5) | (extension << 4) | cc

        # Byte 1: M(1) | PT(7)
        header[1] = (marker << 7) | pt

        # Bytes 2-3: Sequence number (16 bits, big-endian)
        header[2] = (seqnum >> 8) & 0xFF
        header[3] = seqnum & 0xFF

        # Bytes 4-7: Timestamp (32 bits, big-endian)
        struct.pack_into('>I', header, 4, timestamp)

        # Bytes 8-11: SSRC (32 bits, big-endian)
        struct.pack_into('>I', header, 8, ssrc)

        self.header = header
        self.payload = payload

    def decode(self, byteStream):
        """Decode the RTP packet from a byte stream."""
        self.header = bytearray(byteStream[:self.HEADER_SIZE])
        self.payload = byteStream[self.HEADER_SIZE:]

    def version(self):
        """Return RTP version."""
        return (self.header[0] >> 6) & 0x03

    def seqNum(self):
        """Return sequence number."""
        return (self.header[2] << 8) | self.header[3]

    def timestamp(self):
        """Return timestamp."""
        return struct.unpack_from('>I', self.header, 4)[0]

    def payloadType(self):
        """Return payload type."""
        return self.header[1] & 0x7F

    def getPayload(self):
        """Return payload."""
        return self.payload

    def getPacket(self):
        """Return the complete RTP packet (header + payload)."""
        return bytes(self.header) + self.payload
