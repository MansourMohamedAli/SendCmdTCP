import argparse
import asyncio
import sys

from logger import logger
from read_config import read_config

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

        if len(sys.argv) < 1:
            logger.info('Type "SendCmdClient.exe -h" or "SendCmdClient.exe --help" for usage.')
            return

    parser = argparse.ArgumentParser(description="Client for sending commands to the server.")
    parser.add_argument("--config", type=str, default="config.json", help="Name of JSON file.")
    args = parser.parse_args(args)

    config           = args.config
    if config:
        try:
            config_data = read_config(config)

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


    tasks = [asyncio.create_task(tcp_echo_client(host["hostname"], host["port"], host["command"])) for host in config_data]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    print(f"Task Results: {results}")

if __name__ == "__main__":
    asyncio.run(main())
