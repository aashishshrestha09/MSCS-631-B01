from socket import *
import sys
import os
from urllib.parse import urlsplit

if len(sys.argv) <= 1:
    print('Usage : "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server]')
    sys.exit(2)

# Create a server socket, bind it to a port and start listening
tcpSerSock = socket(AF_INET, SOCK_STREAM)
CACHE_ROOT = "cache"

# Fill in start
tcpSerSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
tcpSerSock.bind((sys.argv[1], 8888))
tcpSerSock.listen(5)
# Fill in end

while 1:
    # Start receiving data from the client
    print('Ready to serve...')
    tcpCliSock, addr = tcpSerSock.accept()
    print('Received a connection from:', addr)

    message = tcpCliSock.recv(4096).decode('utf-8', errors='ignore')  # Fill in start  # Fill in end
    print(message)

    if not message.strip():
        tcpCliSock.close()
        continue

    # Extract the filename from the given message
    try:
        parts = message.split()
        method = parts[0]
        raw_target = parts[1]
        print(raw_target)

        parsed = urlsplit(raw_target)
        if parsed.scheme and parsed.netloc:
            origin_host = parsed.hostname or parsed.netloc
            origin_port = parsed.port or 80
            origin_path = parsed.path or "/"
            if parsed.query:
                origin_path += "?" + parsed.query
        else:
            host_header = ""
            for line in message.splitlines():
                if line.lower().startswith("host:"):
                    host_header = line.split(":", 1)[1].strip()
                    break
            if not host_header:
                raise ValueError("Missing Host header")
            host_only, _, port_text = host_header.partition(":")
            origin_host = host_only
            origin_port = int(port_text) if port_text else 80
            origin_path = raw_target if raw_target else "/"

        if not origin_path.startswith("/"):
            origin_path = "/" + origin_path

        # Build a cache file path like host/path/to/file and map "/" to "index.html".
        cache_rel_path = origin_path.lstrip("/")
        if not cache_rel_path or cache_rel_path.endswith("/"):
            cache_rel_path += "index.html"
        cache_rel_path = cache_rel_path.replace("?", "__q__")
        filename = os.path.join(CACHE_ROOT, origin_host, cache_rel_path)
        print(filename)
    except IndexError:
        tcpCliSock.close()
        continue
    except Exception as e:
        print("Invalid request:", e)
        tcpCliSock.close()
        continue

    fileExist = "false"
    filetouse = "/" + filename
    print(filetouse)

    try:
        # Check whether the file exists in the cache
        f = open(filetouse[1:], "rb")
        outputdata = f.read()
        fileExist = "true"
        f.close()

        # ProxyServer finds a cache hit and generates a response message
        tcpCliSock.send(b"HTTP/1.0 200 OK\r\n")
        tcpCliSock.send(b"Content-Type:text/html\r\n")
        tcpCliSock.send(b"\r\n")

        # Fill in start
        tcpCliSock.sendall(outputdata)
        # Fill in end

        print('Read from cache')

    # Error handling for file not found in cache
    except IOError:
        if fileExist == "false":
            # Create a socket on the proxyserver
            c = socket(AF_INET, SOCK_STREAM)  # Fill in start  # Fill in end

            print(origin_host)

            try:
                # Connect to the socket to port 80
                # Fill in start
                c.connect((origin_host, origin_port))
                # Fill in end

                # Create a temporary file on this socket and ask port 80
                # for the file requested by the client
                request = (
                    method + " " + origin_path + " HTTP/1.0\r\n"
                    "Host: " + origin_host + "\r\n"
                    "Connection: close\r\n\r\n"
                )
                c.sendall(request.encode())

                # Read the response into buffer
                # Fill in start
                buff = b""
                while True:
                    data = c.recv(4096)
                    if not data:
                        break
                    buff += data
                # Fill in end

                # Create a new file in the cache for the requested file.
                # Also send the response in the buffer to client socket
                # and write the corresponding file in the cache.
                # Fill in start
                cache_dir = os.path.dirname(filename)
                if cache_dir and not os.path.exists(cache_dir):
                    os.makedirs(cache_dir, exist_ok=True)

                tmpFile = open(filename, "wb")
                tmpFile.write(buff)
                tmpFile.close()

                tcpCliSock.sendall(buff)
                # Fill in end

                c.close()

            except Exception as e:
                print("Error fetching from origin server:", e)
        else:
            # HTTP response message for file not found
            tcpCliSock.send(b"HTTP/1.0 404 Not Found\r\n\r\n")

    # Close the client socket
    tcpCliSock.close()

tcpSerSock.close()
