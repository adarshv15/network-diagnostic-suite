import asyncio
from ping import ping
from traceroute import traceroute
from utils import resolve_host
from ssl_utils import create_server_ssl_context


async def handle_client(reader, writer):

    addr = writer.get_extra_info("peername")
    print(f"Client connected: {addr}")
    ssl_obj = writer.get_extra_info("ssl_object")

    if ssl_obj:
        print("SSL connection established")
        print("Cipher:", ssl_obj.cipher())

    data = await reader.read(1024)
    host = data.decode().strip()

    print(f"Request for: {host}")

    ip = resolve_host(host)

    if not ip:
        writer.write(b"Host resolution failed")
        await writer.drain()
        writer.close()
        return

    ping_result = ping(host)
    trace = traceroute(host)

    response = "PING RESULTS\n"
    response += str(ping_result) + "\n\n"

    response += "TRACEROUTE\n"

    for hop in trace:
        response += hop + "\n"


    writer.write(response.encode())
    await writer.drain()
    print(f"Response sent successfully for: {host}\n")
    writer.close()
    await writer.wait_closed()


async def main():

    ssl_context = create_server_ssl_context()

    server = await asyncio.start_server(
        handle_client,
        "0.0.0.0",
        8888,
        ssl=ssl_context
    )

    print("Diagnostic Server Running on port 8888\n")

    async with server:
        await server.serve_forever()


asyncio.run(main())