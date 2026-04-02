import asyncio
import ssl

HOST = "127.0.0.1"
PORT = 8888
TARGET = "google.com"

CLIENTS = 20


async def client_task():

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    reader, writer = await asyncio.open_connection(
        HOST,
        PORT,
        ssl=context
    )

    writer.write(TARGET.encode())
    await writer.drain()

    data = await reader.read(5000)

    print("Response received")

    writer.close()
    await writer.wait_closed()


async def main():

    tasks = []

    for _ in range(CLIENTS):
        tasks.append(asyncio.create_task(client_task()))

    await asyncio.gather(*tasks)


asyncio.run(main())