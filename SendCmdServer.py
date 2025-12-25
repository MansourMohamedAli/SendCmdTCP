import argparse
import asyncio
import sys

from logger import logger

IP_ADDRESS = "0.0.0.0"
DEFAULT_SERVER_PORT = 52000
DEFAULT_MAX_ATTEMPTS = 1  # Maximum number of connection attempts

async def handle_echo(reader, writer):
    data = await reader.read(100)
    message = data.decode()
    addr = writer.get_extra_info('peername')

    print(f"Received {message!r} from {addr!r}")

    print(f"Send: {message!r}")
    writer.write(data)
    await writer.drain()

    print("Close the connection")
    writer.close()
    await writer.wait_closed()

async def main(args=None) -> None:
    if args is None:
        args = sys.argv[1:]

        if len(sys.argv) < 1:
            logger.info('Type "SendCmdClient.exe -h" or "SendCmdClient.exe --help" for usage.')
            # print('Type "SendCmdClient.exe -h" or "SendCmdClient.exe --help" for usage.')
            return

    parser = argparse.ArgumentParser(description="Server for receiving commands from the client.")
    parser.add_argument("--port", type=int, default=DEFAULT_SERVER_PORT, help=f"The port to connect to the server. Default is {DEFAULT_SERVER_PORT}.")
    args = parser.parse_args(args)

    port = args.port

    server = await asyncio.start_server(
        handle_echo, IP_ADDRESS, port)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()

asyncio.run(main())