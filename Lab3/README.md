# Lab 3 – SMTP Mail Client

## Overview

A raw-socket SMTP client that sends email via Gmail's SMTP server **without** using Python's `smtplib` module, demonstrating the full SMTP protocol dialog at the socket level including STARTTLS negotiation and AUTH LOGIN authentication.

## Files

| File                | Description                         |
| ------------------- | ----------------------------------- |
| `SMTPMailClient.py` | Complete SMTP client implementation |
| `requirements.txt`  | Python package dependencies         |

## Prerequisites

- Python 3.x
- A **Gmail** account with **2-Step Verification** enabled
- A Gmail **App Password** (16 characters, no spaces)

## Installation

```bash
# From the repo root — create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate          # Windows

pip install -r Lab3/requirements.txt
```

## Configuration

The following environment variables are required. Set them via a `.env` file, `direnv` (`.envrc`), or plain shell exports — whichever you prefer. **Never commit credentials to git.**

| Variable          | Required                       | Description                                                     |
| ----------------- | ------------------------------ | --------------------------------------------------------------- |
| `SENDER_EMAIL`    | Yes                            | Sender Gmail address                                            |
| `RECIPIENT_EMAIL` | Yes                            | Recipient address (can be same as sender)                       |
| `EMAIL_PASSWORD`  | Yes                            | 16-character Gmail App Password — no spaces, no inline comments |
| `SMTP_HOST`       | No (default: `smtp.gmail.com`) | Mail server hostname                                            |
| `SMTP_PORT`       | No (default: `587`)            | Mail server port                                                |
| `SMTP_TLS`        | No (default: `true`)           | Set to `false` for a local debug server                         |

### Getting a Gmail App Password

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Confirm **2-Step Verification** is **on**
3. Search for **App Passwords** → select _Mail_ → **Generate**
4. Copy the 16-character code — paste it as `EMAIL_PASSWORD` with **no spaces and no inline comments**

## Running the Client

```bash
cd Lab3
python SMTPMailClient.py
```

Expected output:

```
Server response after connection: 220 smtp.gmail.com ESMTP ...
Server response after HELO: 250 smtp.gmail.com at your service
Server response after STARTTLS: 220 2.0.0 Ready to start TLS
Server response after EHLO (post-TLS): 250-smtp.gmail.com ...
Server response after AUTH LOGIN: 334 ...
Server response after sending username: 334 ...
Server response after sending password: 235 2.7.0 Accepted
Server response after MAIL FROM: 250 2.1.0 OK
Server response after RCPT TO: 250 2.1.5 OK
Server response after DATA command: 354 Go ahead
Server response after sending message data: 250 2.0.0 OK
Server response after QUIT command: 221 2.0.0 closing connection

Email sent successfully!
```

Check your **Spam/Junk** folder if the email does not appear in the inbox immediately.

## Local Debug Server (no Gmail account needed)

For testing without a live server, use `aiosmtpd`:

```bash
# Terminal 1 — start debug server
python -m aiosmtpd -n -l localhost:1025

# Terminal 2 — update .env, then run client
# SMTP_HOST=localhost
# SMTP_PORT=1025
# SMTP_TLS=false
python SMTPMailClient.py
```

The debug server prints the received message to stdout instead of forwarding it.

## SMTP Protocol Flow

```
Client                        Server (smtp.gmail.com:587)
  |--- TCP connect ---------->|
  |<-- 220 Service Ready -----|
  |--- HELO Alice ----------->|
  |<-- 250 OK ----------------|
  |--- STARTTLS ------------->|
  |<-- 220 Ready for TLS -----|
  |=== TLS handshake (ssl) ===|
  |--- EHLO Alice ----------->|
  |<-- 250 Capabilities ------|
  |--- AUTH LOGIN ----------->|
  |<-- 334 Username: ---------|
  |--- <base64 user> -------->|
  |<-- 334 Password: ---------|
  |--- <base64 pass> -------->|
  |<-- 235 Authenticated -----|
  |--- MAIL FROM:<...> ------>|
  |<-- 250 OK ----------------|
  |--- RCPT TO:<...> -------->|
  |<-- 250 OK ----------------|
  |--- DATA ----------------->|
  |<-- 354 Start input -------|
  |--- headers + body ------->|
  |--- <CRLF>.<CRLF> -------->|
  |<-- 250 OK (queued) -------|
  |--- QUIT ----------------->|
  |<-- 221 Bye ---------------|
```
