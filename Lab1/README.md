# Lab 1 — Web Server Socket Programming

## Overview

A single-threaded HTTP/1.1 web server implemented in Python using only the standard-library `socket` module. The server accepts TCP connections, parses HTTP GET requests, serves requested files with a `200 OK` response, and returns a `404 Not Found` page for missing resources.

## Project Structure

```
Lab1/
├── WebServer.py          # Main server implementation
├── HelloWorld.html       # Sample HTML file to serve
└── README.md             # This file
```

## Requirements

| Dependency | Version                                  |
| ---------- | ---------------------------------------- |
| Python     | ≥ 3.10 (uses `str \| None` union syntax) |

No third-party packages are required. All functionality relies on Python's standard library.

## Quick Start

### 1. Clone / navigate to the directory

```bash
git clone https://github.com/aashishshrestha09/MSCS-631-B01.git
cd "Lab1"
```

### 2. Start the server

```bash
python3 WebServer.py
```

The server binds to all interfaces on **port 6789** by default.  
Override the port by passing it as the first argument:

```bash
python3 WebServer.py 8080
```

Expected terminal output:

```
2026-03-06 12:00:00  [INFO]   HTTP server started — listening on 0.0.0.0:6789   (Ctrl+C to stop)
Ready to serve...
```

### 3. Test in a browser

| Scenario             | URL                                     | Expected Result           |
| -------------------- | --------------------------------------- | ------------------------- |
| Serve existing file  | `http://127.0.0.1:6789/HelloWorld.html` | Styled HTML page (200 OK) |
| Request missing file | `http://127.0.0.1:6789/missing.html`    | Custom 404 error page     |

> **Tip:** Use an incognito / private window to bypass browser caching during testing.

### 4. Stop the server

Press `Ctrl+C` in the terminal. The server shuts down cleanly and closes the socket.

## How It Works

```
Client (Browser)                    Server (WebServer.py)
       |                                      |
       |--- TCP SYN -----------------------> |  serverSocket.accept()
       |<-- TCP SYN-ACK ------------------- |
       |--- TCP ACK -----------------------> |
       |                                      |
       |--- HTTP GET /HelloWorld.html ------> |  connectionSocket.recv()
       |                                      |  open("HelloWorld.html")
       |<-- HTTP/1.1 200 OK + body --------- |  connectionSocket.sendall()
       |                                      |  connectionSocket.close()
       |--- TCP FIN -----------------------> |
```

1. `socket()` — creates an IPv4 TCP socket.
2. `setsockopt(SO_REUSEADDR)` — allows immediate reuse of the port after restart.
3. `bind()` — associates the socket with `0.0.0.0:6789`.
4. `listen()` — marks the socket as passive with a connection backlog of 5.
5. `accept()` — blocks until a client connects; returns a new connected socket.
6. `recv()` — reads the raw HTTP request bytes from the client.
7. File path is extracted from the request line (`GET /<path> HTTP/1.1`).
8. If the file exists -> `200 OK` response + file body.
9. If the file is missing -> `404 Not Found` response + error HTML body.
10. `close()` — closes the client socket; loop returns to `accept()`.

## Design Decisions

| Decision                    | Rationale                                                                          |
| --------------------------- | ---------------------------------------------------------------------------------- |
| `import socket` (explicit)  | Avoids polluting the global namespace; PEP 8 best practice                         |
| `sendall()` over `send()`   | `send()` may send fewer bytes than requested; `sendall()` guarantees full delivery |
| `SO_REUSEADDR`              | Prevents `[Errno 48] Address already in use` during rapid re-runs                  |
| `logging` module            | Structured, timestamped output with severity levels vs. bare `print`               |
| Named constants             | Eliminates magic numbers; makes configuration self-documenting                     |
| `if __name__ == "__main__"` | Prevents execution when the module is imported by tests or other scripts           |
| Helper functions            | Single-responsibility principle — each function does exactly one thing             |

## Limitations

- **Single-threaded:** Handles exactly one request at a time. A second client must wait until the current request completes.
- **GET only:** Does not handle POST, PUT, or other HTTP methods.
- **No HTTPS:** Communications are unencrypted plaintext.
- **No MIME detection:** All responses use `Content-Type: text/html`; binary files (images, PDFs) are not supported.

## References

- Kurose, J. F., & Ross, K. W. (2022). _Computer networking: A top-down approach_ (8th ed.). Pearson.
- Python Software Foundation. (2023). _socket — Low-level networking interface_. https://docs.python.org/3/library/socket.html
- Fielding, R., Nottingham, M., & Reschke, J. (2022). _HTTP semantics_ (RFC 9110). https://doi.org/10.17487/RFC9110
