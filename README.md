# 🛡️ Secure Network Diagnostic Suite

> A high-performance, asynchronous diagnostic proxy that tunnels `ping` and `traceroute` over SSL/TLS —
> bypassing client-side firewalls, encrypting infrastructure telemetry, and handling concurrent sessions without resource exhaustion.

---

## 📌 Table of Contents

- [The Problem](#-the-problem)
- [Architecture](#-architecture)
- [Request Lifecycle](#-request-lifecycle)
- [File Reference](#-file-reference)
- [Quick Start](#-quick-start)
- [Key Design Decisions](#-key-design-decisions)

---

## ❓ The Problem

Standard network diagnostic tools fall short in production and security-conscious environments:

| Issue | Impact |
|---|---|
| **Plaintext exposure** | Target hostnames and routing paths are visible to any passive network observer |
| **Firewall restrictions** | Client-side firewalls commonly block outbound ICMP, making local `ping` unreliable |
| **No audit trail** | Ad-hoc `ping` runs leave no centralized record of checks, timing, or RTT results |
| **Single-client bottleneck** | Native tools block per operation — a naive server forks per connection and collapses under load |

**The solution:** A centralized async diagnostic server that clients delegate requests to, communicating exclusively over an encrypted tunnel.

---

## 🏗️ Architecture

### 🔐 Security Layer

- RSA asymmetric keypairs generate self-signed **X.509 certificates** via the `cryptography` library
- `ssl_utils.py` encapsulates both server and client `ssl.SSLContext` construction
- Cipher suite and protocol version are configured in one place
- The client **verifies the server certificate** before transmitting any data, preventing MITM interception

---

### ⚡ Concurrency Engine

- A single `asyncio` event loop accepts all inbound connections
- `asyncio.Semaphore` caps concurrent active diagnostics, preventing thread pool exhaustion
- CPU-bound ICMP socket work is offloaded via `loop.run_in_executor`, keeping the loop non-blocking
- Ping and traceroute tasks per request run simultaneously via `asyncio.gather`

---

### 📡 ICMP Ping Engine

- Manually constructs **ICMP Echo Request packets** using raw sockets — no subprocess, no shell dependency
- Computes checksums by hand and parses Echo Replies with **microsecond-precision RTT**
- Produces structured output rather than raw text to parse

---

### 🗄️ DNS Cache

- Time-aware in-memory dictionary stores resolved IPs with a **5-minute TTL**
- Cache hits skip DNS resolution entirely, eliminating redundant round-trips
- Thread-safe; invalidated lazily on read

---

## 🔄 Request Lifecycle

```
Client                             Server
  │                                  │
  │──── TLS ClientHello ───────────► │   ← Server presents X.509 cert
  │◄─── TLS ServerHello ─────────── │
  │                                  │
  │──── "google.com" (encrypted) ──► │   ← Plaintext never leaves the tunnel
  │                                  │
  │                                  │   1. DNS cache check (5-min TTL)
  │                                  │   2. asyncio.gather(ping, traceroute)
  │                                  │   3. Results serialized into report
  │                                  │
  │◄─── Diagnostic report ────────── │   ← Encrypted response
  │                                  │   ← Duration + status → server.log
```

---

## 📁 File Reference

| Module | Responsibility |
|---|---|
| `server.py` | Async TCP server — SSL context, semaphore pool, connection dispatcher, structured logging |
| `client.py` | Interactive CLI — prompts for target, opens TLS connection, renders the diagnostic report |
| `ping.py` | Raw ICMP socket — manual packet construction, checksum calculation, TTL handling |
| `traceroute.py` | Hop-by-hop path mapper via system subprocess; parses output cross-platform |
| `generate_ssl.py` | One-time RSA key + X.509 cert generation; outputs `server.key` and `server.crt` |
| `ssl_utils.py` | Factory functions for server/client `ssl.SSLContext`; centralizes cipher and protocol config |
| `load_test.py` | Spawns 20 concurrent asyncio clients to stress-test semaphore and GC behavior |

---

## 🚀 Quick Start

### Prerequisites

- Python **3.8+**
- `cryptography` package
- **Admin / root privileges** for the server (raw socket requirement)

```bash
pip install cryptography
```

> ⚠️ **Privilege note:** Only `server.py` requires elevation. `client.py` runs without special permissions.

---

### Step 1 — Generate SSL Certificates
> Run this **once** before anything else.

```bash
python generate_ssl.py

# Output:
#   server.key
#   server.crt
```

---

### Step 2 — Start the Server

```bash
# Linux / macOS
sudo python3 server.py

# Windows (run terminal as Administrator)
python server.py
```

---

### Step 3 — Connect a Client
> Open a **new terminal** — no elevated privileges needed.

```bash
python client.py

# Enter a hostname when prompted:
# > google.com
```

---

### Step 4 — Stress Test *(optional)*

```bash
python load_test.py

# Simulates 20 concurrent clients.
# Observe semaphore queuing behaviour in server.log
```

---

## 💡 Key Design Decisions

**Self-signed certificates over CA-signed**
Keeps the project fully self-contained and reproducible without requiring a public domain or external certificate authority.

**Raw ICMP over subprocess ping**
Produces precise, structured RTT data and removes shell dependency entirely — output is a Python dict, not a string to regex-parse.

**Semaphore over process pool**
Lighter weight for I/O-bound work. Avoids the startup overhead and per-request memory cost of spawning OS processes.

**5-minute DNS TTL cache**
Long enough to absorb burst traffic to the same host; short enough to detect DNS changes without requiring a server restart.

---

## 📄 License

MIT — see `LICENSE` for details.
