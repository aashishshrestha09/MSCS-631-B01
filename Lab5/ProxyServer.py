from socket import *
import sys
import os

if len(sys.argv) <= 1:
    print('Usage : "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server]')
    sys.exit(2)

# Create a server socket, bind it to a port and start listening
tcpSerSock = socket(AF_INET, SOCK_STREAM)

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
        print(message.split()[1])
        filename = message.split()[1].partition("/")[2]
        print(filename)
    except IndexError:
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

            hostn = filename.replace("www.", "", 1)
            print(hostn)

            try:
                # Connect to the socket to port 80
                # Fill in start
                c.connect((hostn, 80))
                # Fill in end

                # Create a temporary file on this socket and ask port 80
                # for the file requested by the client
                request = (
                    "GET http://" + filename + " HTTP/1.0\r\n"
                    "Host: " + hostn + "\r\n"
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
