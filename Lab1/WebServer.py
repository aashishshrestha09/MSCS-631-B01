"""
WebServer.py

A single-threaded HTTP/1.1 web server implemented using Python's low-level
socket API.  The server accepts one TCP connection at a time, parses the
incoming GET request, serves the requested file, and returns an appropriate
HTTP status code (200 OK or 404 Not Found).

Usage:
    python3 WebServer.py          # defaults: host=all interfaces, port=6789
    python3 WebServer.py 8080     # override port from the command line
"""

# Standard-library imports  (explicit imports — avoid wildcard 'from x import *')
import logging
import socket
import sys

# Server configuration constants
SERVER_HOST: str = ""  # Empty string → bind to all available interfaces
SERVER_PORT: int = 6789  # Default port for this lab
RECV_BUFFER: int = 4096  # Receive buffer size in bytes
LISTEN_BACKLOG: int = 5  # Maximum number of queued connections

# Logging — structured output with timestamps instead of bare print()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# Helper functions
def build_response_header(
    status_line: str, content_type: str, body_length: int
) -> bytes:
    """
    Build a standards-compliant HTTP/1.1 response header block.

    Args:
        status_line  : The HTTP status line, e.g. ``"HTTP/1.1 200 OK"``.
        content_type : MIME type of the response body, e.g. ``"text/html"``.
        body_length  : Length of the response body in bytes.

    Returns:
        Fully encoded header block, including the mandatory blank-line
        separator before the response body.
    """
    headers = (
        f"{status_line}\r\n"
        f"Content-Type: {content_type}; charset=utf-8\r\n"
        f"Content-Length: {body_length}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    )
    return headers.encode("utf-8")


def parse_request_path(raw_message: str) -> str | None:
    """
    Extract the URL path from the first line of an HTTP request.

    Args:
        raw_message: Raw HTTP request string received from the client.

    Returns:
        The URL path (e.g. ``"/HelloWorld.html"``), or ``None`` if
        the message is malformed or empty.
    """
    tokens = raw_message.split()
    return tokens[1] if len(tokens) >= 2 else None


# Request handlers
def handle_client(connectionSocket: socket.socket, addr: tuple) -> None:
    """
    Process a single client connection: receive the HTTP request, serve the
    appropriate response, and always close the socket when finished.

    Args:
        connectionSocket : The accepted, connected client socket.
        addr             : ``(host, port)`` tuple of the remote client.
    """
    logger.info("Connection accepted from  %s:%d", addr[0], addr[1])

    try:
        # Receive the HTTP request from the client
        # Fill in start
        message = connectionSocket.recv(RECV_BUFFER).decode(
            "utf-8"
        )  # Receive and decode the HTTP request
        # Fill in end

        if not message.strip():
            logger.warning("Empty request from %s — ignoring.", addr[0])
            return

        # Parse the filename from the HTTP request line (e.g. "GET /HelloWorld.html HTTP/1.1")
        filename = parse_request_path(message)

        if filename is None:
            logger.warning("Malformed HTTP request from %s.", addr[0])
            return

        # Open the requested file (strip the leading '/')
        f = open(filename[1:])

        # Read the full file content
        # Fill in start
        outputdata = f.read()  # Read entire file contents as a string
        f.close()
        # Fill in end

        body_bytes = outputdata.encode("utf-8")

        # Send one HTTP header line into socket
        # Fill in start
        header = build_response_header("HTTP/1.1 200 OK", "text/html", len(body_bytes))
        connectionSocket.sendall(header)
        # Fill in end

        # Send the content of the requested file to the client
        for i in range(0, len(outputdata)):
            connectionSocket.sendall(outputdata[i].encode("utf-8"))
        connectionSocket.sendall(b"\r\n")

        logger.info("200 OK  →  %s  (%d bytes)", filename[1:], len(body_bytes))
        connectionSocket.close()

    except IOError:
        # Send response message for file not found
        # Fill in start
        not_found_body = (
            "<!DOCTYPE html><html lang='en'>"
            "<head><meta charset='UTF-8'><title>404 Not Found</title></head>"
            "<body><h1>404 Not Found</h1>"
            "<p>The requested resource could not be found on this server.</p>"
            "</body></html>"
        )
        body_bytes = not_found_body.encode("utf-8")
        header = build_response_header(
            "HTTP/1.1 404 Not Found", "text/html", len(body_bytes)
        )
        connectionSocket.sendall(header)
        connectionSocket.sendall(body_bytes)
        # Fill in end

        logger.warning(
            "404 Not Found  →  %s", filename if "filename" in dir() else "/unknown"
        )

        # Close client socket
        # Fill in start
        connectionSocket.close()
        # Fill in end


# Server entry point
def run_server(host: str = SERVER_HOST, port: int = SERVER_PORT) -> None:
    """
    Initialise the TCP server socket and enter the main accept loop.

    The server runs until interrupted with Ctrl+C (KeyboardInterrupt).

    Args:
        host : Interface to bind to (default: all interfaces via ``""``).
        port : TCP port to listen on (default: 6789).
    """
    # Import socket module — create the server socket
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Prepare a server socket
    # Fill in start
    serverSocket.setsockopt(
        socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
    )  # Allow immediate address reuse
    serverSocket.bind((host, port))  # Bind to host:port
    serverSocket.listen(LISTEN_BACKLOG)  # Start listening for connections
    # Fill in end

    logger.info(
        "HTTP server started — listening on %s:%d   (Ctrl+C to stop)",
        host or "0.0.0.0",
        port,
    )

    try:
        while True:
            # Establish the connection
            print("Ready to serve...")

            # Fill in start
            connectionSocket, addr = (
                serverSocket.accept()
            )  # Block until a client connects
            # Fill in end

            handle_client(connectionSocket, addr)

    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user.")
    finally:
        serverSocket.close()

    sys.exit(0)  # Terminate the program after sending the corresponding data


# Script entry guard — prevents execution when imported as a module
if __name__ == "__main__":
    # Allow optional port override: python3 WebServer.py 8080
    port = int(sys.argv[1]) if len(sys.argv) > 1 else SERVER_PORT
    run_server(port=port)
