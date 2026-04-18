# Lab 7: Video Streaming with RTSP and RTP

A streaming video server and client that communicate using the Real-Time Streaming Protocol (RTSP) and send data using the Real-time Transfer Protocol (RTP).

## Files

| File                | Description                                              |
| ------------------- | -------------------------------------------------------- |
| `Server.py`         | RTSP server entry point; listens for client connections  |
| `ServerWorker.py`   | Handles RTSP session per client; streams RTP packets     |
| `Client.py`         | RTSP client with GUI; receives and displays video frames |
| `ClientLauncher.py` | Launches the client application                          |
| `RtpPacket.py`      | RTP packet encoding (packetization) and decoding         |
| `VideoStream.py`    | Reads MJPEG frames from a video file                     |
| `generate_mjpeg.py` | Utility to generate the sample `movie.Mjpeg` file        |

## Setup

```bash
pip install -r requirements.txt
python generate_mjpeg.py   # generates movie.Mjpeg if not present
```

## Running

**Terminal 1 (Server):**

```bash
python Server.py 8554
```

**Terminal 2 (Client):**

```bash
python ClientLauncher.py localhost 8554 25000 movie.Mjpeg
```

## Usage

1. Click **Setup** to establish the RTSP session
2. Click **Play** to start video playback
3. Click **Pause** to pause playback
4. Click **Teardown** to end the session

Statistics (packet loss rate, data rate, FPS) are displayed at the bottom of the client window and printed to the console on teardown.
