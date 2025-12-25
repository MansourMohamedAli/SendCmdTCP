import argparse
import asyncio
import sys

from logger import logger

DEFAULT_SERVER_PORT = 52000
DEFAULT_MAX_ATTEMPTS = 1  # Maximum number of connection attempts

async def tcp_echo_client(host, port, message):
    reader, writer = await asyncio.open_connection(
        host, port)

    print(f'Send: {message!r}')
    writer.write(message.encode())
    await writer.drain()

    # data = await reader.read(100)
    # print(f'Received: {data.decode()!r}')

    print('Close the connection')
    writer.close()
    await writer.wait_closed()
    return f"Send Command {message}"

async def main(args=None):
    if args is None:
        args = sys.argv[1:]

        if len(sys.argv) < 2:
            logger.info('Type "SendCmdClient.exe -h" or "SendCmdClient.exe --help" for usage.')
            return

    parser = argparse.ArgumentParser(description="Client for sending commands to the server.")
    parser.add_argument("host", type=str, help="Server IP address.")
    parser.add_argument("command", type=str, help='Command to send. If command is multiple words, enclose in " ".')
    # parser.add_argument("--port", type=int, default=DEFAULT_SERVER_PORT, help=f"The port to connect to the server. Default is {DEFAULT_SERVER_PORT}.")
    parser.add_argument("--attempts", type=int, default=DEFAULT_MAX_ATTEMPTS, help=f"The maximum number of connection attempts. Default is {DEFAULT_MAX_ATTEMPTS}.")
    args = parser.parse_args(args)

    requested_host   = args.host
    command          = args.command

    tasks = [asyncio.create_task(tcp_echo_client(requested_host, i, command)) for i in range(52000, 52001)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    print(f"Task Results: {results}")


if __name__ == "__main__":
    asyncio.run(main())
