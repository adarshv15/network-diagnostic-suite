import asyncio
from ssl_utils import create_client_ssl_context


async def main():

    host = input("Enter target host: ")

    ssl_context = create_client_ssl_context()

    reader, writer = await asyncio.open_connection(
        "127.0.0.1",
        8888,
        ssl=ssl_context
    )

    writer.write(host.encode())
    await writer.drain()

    data = await reader.read(10000)

    print("\nSERVER RESPONSE\n")
    print(data.decode())

    writer.close()
    await writer.wait_closed()


asyncio.run(main())