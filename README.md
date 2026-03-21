# ICMP-Based Network Diagnostic Suite

A multi-client TCP server that performs Ping and Traceroute diagnostics over a secure SSL/TLS connection.

## Features
- Raw ICMP socket-based Ping with RTT & packet-loss stats
- Traceroute with hop-by-hop network path (up to 15 hops)
- Async multi-client support using Python asyncio
- End-to-end TLS encryption with self-signed RSA-2048 / X.509 certificate

## Tech Stack
Python, asyncio, Raw Sockets, SSL/TLS, cryptography, subprocess

## How to Run
1. Generate SSL certificate: `python generate_ssl.py`
2. Start the server: `python server.py`
3. Run the client: `python client.py`
