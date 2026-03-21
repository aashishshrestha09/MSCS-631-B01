#!/usr/bin/env python3
"""
Lab 3 – SMTP Mail Client
Sends an email by speaking raw SMTP over a TCP socket.
Required packages:  pip install python-dotenv aiosmtpd
"""

import os
import ssl
import base64
from socket import *

msg    = "\r\nI love computer networks!"
endmsg = "\r\n.\r\n"


def main():
    # Configuration
    sender_email    = os.getenv("SENDER_EMAIL")
    recipient_email = os.getenv("RECIPIENT_EMAIL")
    email_password  = os.getenv("EMAIL_PASSWORD") or None   # None → skip AUTH

    # SMTP_HOST / SMTP_PORT / SMTP_TLS let you point at a local debug server.
    # Defaults target Gmail.
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    use_tls   = os.getenv("SMTP_TLS", "true").strip().lower() != "false"

    if not sender_email or not recipient_email:
        print("Error: SENDER_EMAIL and RECIPIENT_EMAIL must be set in .env or the shell.")
        return

    #  Choose a mail server and establish a TCP connection
    # Fill in start
    mailserver   = (smtp_host, smtp_port)
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect(mailserver)
    # Fill in end

    recv = clientSocket.recv(1024).decode()
    print("Server response after connection:", recv)
    if not recv.startswith('220'):
        print('220 reply not received from server.')
        clientSocket.close()
        return

    # Send HELO command and print server response.
    heloCommand = 'HELO Alice\r\n'
    clientSocket.send(heloCommand.encode())
    recv = clientSocket.recv(1024).decode()
    print("Server response after HELO:", recv)
    if not recv.startswith('250'):
        print('250 reply not received from server.')
        clientSocket.close()
        return

    # Upgrade to TLS with STARTTLS (required by Gmail on port 587).
    # Skipped when SMTP_TLS=false (e.g. local debug server).
    if use_tls:
        startTLSCommand = 'STARTTLS\r\n'
        clientSocket.send(startTLSCommand.encode())
        recv = clientSocket.recv(1024).decode()
        print("Server response after STARTTLS:", recv)
        if not recv.startswith('220'):
            print('220 reply not received from server after STARTTLS.')
            clientSocket.close()
            return

        context      = ssl.create_default_context()
        clientSocket = context.wrap_socket(clientSocket, server_hostname=smtp_host)

        # Re-introduce ourselves over the encrypted channel (EHLO required post-TLS).
        ehloCommand = 'EHLO Alice\r\n'
        clientSocket.send(ehloCommand.encode())
        recv = clientSocket.recv(1024).decode()
        print("Server response after EHLO (post-TLS):", recv)
        if not recv.startswith('250'):
            print('250 reply not received from server.')
            clientSocket.close()
            return

    # If a password is provided, perform AUTH LOGIN; otherwise, skip authentication.
    if email_password:
        # Fill in start
        authLogin = 'AUTH LOGIN\r\n'
        clientSocket.send(authLogin.encode())
        recv = clientSocket.recv(1024).decode()   # 334 Username:
        print("Server response after AUTH LOGIN:", recv)

        username_encoded = base64.b64encode(sender_email.encode()).decode() + '\r\n'
        clientSocket.send(username_encoded.encode())
        recv = clientSocket.recv(1024).decode()   # 334 Password:
        print("Server response after sending username:", recv)

        password_encoded = base64.b64encode(email_password.encode()).decode() + '\r\n'
        clientSocket.send(password_encoded.encode())
        recv = clientSocket.recv(1024).decode()   # 235 Authentication successful
        print("Server response after sending password:", recv)
        if not recv.startswith('235'):
            print("235 reply not received – authentication failed. Check your App Password.")
            clientSocket.close()
            return
        # Fill in end
    else:
        print("No password provided, skipping authentication.")

    # Send MAIL FROM command and print server response.
    # Fill in start
    mailFrom = f"MAIL FROM:<{sender_email}>\r\n"
    clientSocket.send(mailFrom.encode())
    recv = clientSocket.recv(1024).decode()
    print("Server response after MAIL FROM:", recv)
    if not recv.startswith('250'):
        print("250 reply not received from server.")
        clientSocket.close()
        return
    # Fill in end

    # Send RCPT TO command and print server response.
    # Fill in start
    rcptTo = f"RCPT TO:<{recipient_email}>\r\n"
    clientSocket.send(rcptTo.encode())
    recv = clientSocket.recv(1024).decode()
    print("Server response after RCPT TO:", recv)
    if not recv.startswith('250'):
        print("250 reply not received from server.")
        clientSocket.close()
        return
    # Fill in end

    # Send DATA command and print server response.
    # Fill in start
    dataCommand = 'DATA\r\n'
    clientSocket.send(dataCommand.encode())
    recv = clientSocket.recv(1024).decode()
    print("Server response after DATA command:", recv)
    if not recv.startswith('354'):
        print("354 reply not received from server.")
        clientSocket.close()
        return
    # Fill in end

    # Send message data (headers + body).
    # Fill in start
    message = (f"From: <{sender_email}>\r\n"
               f"To: <{recipient_email}>\r\n"
               f"Subject: SMTP Lab Test – I love computer networks!\r\n"
               f"\r\n")
    clientSocket.send(message.encode())
    clientSocket.send(msg.encode())
    # Fill in end

    # Message ends with a single period.
    # Fill in start
    clientSocket.send(endmsg.encode())
    recv = clientSocket.recv(1024).decode()
    print("Server response after sending message data:", recv)
    if not recv.startswith('250'):
        print("250 reply not received from server after end-of-message.")
        clientSocket.close()
        return
    # Fill in end

    # Send QUIT command and get server response.
    # Fill in start
    quitCommand = 'QUIT\r\n'
    clientSocket.send(quitCommand.encode())
    recv = clientSocket.recv(1024).decode()
    print("Server response after QUIT command:", recv)
    # Fill in end

    clientSocket.close()
    print("\nEmail sent successfully!")


if __name__ == "__main__":
    main()
