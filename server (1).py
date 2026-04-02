import asyncio
import time
import logging

from ping import ping
from traceroute import traceroute
from utils import resolve_host
from ssl_utils import create_server_ssl_context

MAX_CONCURRENT_CLIENTS = 20
REQUEST_TIMEOUT = 30
CACHE_TTL = 300

semaphore = asyncio.Semaphore(MAX_CONCURRENT_CLIENTS)

dns_cache = {}

total_requests = 0
active_clients = 0

logging.basicConfig(
    filename="server.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)


def cached_resolve(host):

    now = time.time()

    if host in dns_cache:
        ip, timestamp = dns_cache[host]

        if now - timestamp < CACHE_TTL:
            return ip

    ip = resolve_host(host)

    if ip:
        dns_cache[host] = (ip, now)

    return ip


async def run_ping(host):
    return await asyncio.to_thread(ping, host)


async def run_trace(host):
    return await asyncio.to_thread(traceroute, host)


async def handle_client(reader, writer):

    global total_requests
    global active_clients

    async with semaphore:

        addr = writer.get_extra_info("peername")
        active_clients += 1

        start_time = time.time()

        print(f"Client connected: {addr}")
        logging.info(f"Client connected: {addr}")

        try:

            data = await asyncio.wait_for(reader.read(1024), timeout=REQUEST_TIMEOUT)

            if not data:
                writer.close()
                return

            host = data.decode().strip()

            total_requests += 1

            print(f"Request {total_requests}: {host}")
            logging.info(f"Request {total_requests} for {host}")

            ip = cached_resolve(host)

            if not ip:
                writer.write(b"Host resolution failed")
                await writer.drain()
                writer.close()
                return

            ping_task = asyncio.create_task(run_ping(host))
            trace_task = asyncio.create_task(run_trace(host))

            ping_result = await ping_task
            trace_result = await trace_task

            response = "PING RESULTS\n"
            response += ping_result + "\n\n"

            response += "TRACEROUTE\n"

            for hop in trace_result:
                response += hop + "\n"

            writer.write(response.encode())
            await writer.drain()

            end_time = time.time()

            duration = round(end_time - start_time, 3)

            print(f"Completed in {duration}s")
            logging.info(f"Completed request for {host} in {duration}s")

        except asyncio.TimeoutError:

            writer.write(b"Request timed out\n")
            await writer.drain()
            logging.warning("Client timeout")

        except Exception as e:

            logging.error(f"Server error: {e}")
            writer.write(f"Server error: {e}".encode())
            await writer.drain()

        finally:

            active_clients -= 1

            writer.close()
            await writer.wait_closed()

            print(f"Active clients: {active_clients}")


async def main():

    ssl_context = create_server_ssl_context()

    server = await asyncio.start_server(
        handle_client,
        "0.0.0.0",
        8888,
        ssl=ssl_context
    )

    print("Advanced Diagnostic Server running on port 8888")

    async with server:
        await server.serve_forever()


asyncio.run(main())