"""VideoStream reads MJPEG video frames from a file.

The MJPEG file format stores each frame as a JPEG image. Each frame
is preceded by a 5-byte header containing the frame length as ASCII text.
"""


class VideoStream:
    def __init__(self, filename):
        try:
            self.file = open(filename, 'rb')
        except IOError:
            raise IOError(f"Could not open file: {filename}")
        self.frameNum = 0

    def nextFrame(self):
        """Return the next video frame from the file.

        Each frame is preceded by a 5-byte ASCII length field.
        Returns the frame data as bytes, or empty bytes at end of file.
        """
        data = self.file.read(5)  # Read 5-byte length field
        if data:
            framelength = int(data)
            # Read the frame data
            data = self.file.read(framelength)
            self.frameNum += 1
            return data
        return b''

    def frameNbr(self):
        """Return the current frame number."""
        return self.frameNum

    def close(self):
        """Close the video file."""
        self.file.close()
