# Lab 5: HTTP Web Proxy Server

## Overview

A simple HTTP web proxy server that handles GET requests and caches responses locally. When a cached response exists, it is served directly from disk; otherwise, the proxy fetches the content from the origin server, caches it, and forwards it to the client.

## Files

| File             | Description                           |
| ---------------- | ------------------------------------- |
| `ProxyServer.py` | Completed proxy server implementation |

## Requirements

- Python 3.x
- No external packages required (uses standard library only)

## Running the Proxy Server

```bash
python ProxyServer.py <server_ip>
```

**Example (local machine):**

```bash
python ProxyServer.py localhost
```

The proxy listens on port **8888** by default.

## Usage

### Direct URL in Browser

With the proxy running, navigate to:

```
http://localhost:8888/www.example.com
```

### Configure Browser Proxy Settings

Set your browser's HTTP proxy to:

- **Host:** `localhost` (or the machine's IP if on a separate host)
- **Port:** `8888`

Then navigate to any HTTP URL normally (e.g., `http://www.example.com`).

## How Caching Works

1. The proxy parses the hostname from the incoming GET request.
2. It checks for a local cache file matching the requested path.
3. **Cache hit:** Responds immediately with the cached content (`HTTP/1.0 200 OK`).
4. **Cache miss:** Opens a TCP connection to the origin server on port 80, fetches the full response, writes it to disk, and forwards it to the client.

## Notes

- Only HTTP (port 80) is supported; HTTPS is not handled.
- Cache files are stored in the working directory, mirroring the hostname path.
