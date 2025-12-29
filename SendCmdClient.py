import argparse
import asyncio
import json
import sys

from logger import logger
from read_config import read_config, serialize_commands

DEFAULT_SERVER_PORT = 52000
DEFAULT_MAX_ATTEMPTS = 1  # Maximum number of connection attempts


async def tcp_echo_client(host, port, message):
    try:
        reader, writer = await asyncio.open_connection(host, port)
        encoded_message = serialize_commands(message)

        print(f"Send: {encoded_message!r}")
        writer.write(encoded_message)
        await writer.drain()

        data = await reader.read(4096)
        result = json.loads(data.decode("utf-8"))
        # print(f"Received: {data.decode()!r}")
        print(f"Received: {result}")

        if not any(result):
            logger.info(f"All commands sent to {host} and executed with no errors")
        else:
            logger.info(f"{host}:Error Occured")

        print("Close the connection")
        writer.close()
        await writer.wait_closed()
        # return f"Send Command {message}"

    except ConnectionRefusedError as e:
        logger.info(f"Connection refused by {host}:{port}. Is the server running?")
        return e
    except TimeoutError as e:
        logger.info(f"Timeout connecting to {host}:{port}")
        return e
    except OSError as e:
        logger.info(f"OS error occurred: {e}")
        return e
    except Exception as e:
        logger.info(f"An unexpected error occurred: {e}")
        return e

    else:
        return result


def parse_args():
    parser = argparse.ArgumentParser(description="Run commands on one or more hosts")

    # Optional positionals
    parser.add_argument("hostname", nargs="?", type=str, help="Server IP address.")
    parser.add_argument(
        "command",
        nargs="?",
        type=str,
        help='Command to send. If command is multiple words, enclose in " ".',
    )
    parser.add_argument(
        "--port",
        nargs="?",
        type=int,
        default=DEFAULT_SERVER_PORT,
        help=f"The port to connect to the server. Default is {DEFAULT_SERVER_PORT}.",
    )
    parser.add_argument(
        "--config",
        help="JSON config file with multiple hosts",
        # default="config.json"
    )
    return parser.parse_args()


def load_single_host(hostname: str, port: int, command: str) -> list:
    return [{"hostname": hostname, "port": port, "command": [command]}]


async def main(args=None):
    if len(sys.argv) < 1:
        logger.info(
            'Type "SendCmdClient.exe -h" or "SendCmdClient.exe --help" for usage.',
        )
        return
    args = parse_args()

    try:
        if args.config:
            # CONFIG MODE: ignore positionals
            config_data = read_config(args.config)
        else:
            # SINGLE HOST MODE : positionals required
            if not all([args.hostname, args.port, args.command]):
                sys.exit(
                    "Error: hostname, and command are required unless --config is specified",
                )
            config_data = load_single_host(args.hostname, args.port, args.command)

    except Exception as e:
        sys.exit(f"Error: {e}")

    tasks = [
        asyncio.create_task(
            tcp_echo_client(host["hostname"], host["port"], host["command"]),
        )
        for host in config_data
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    print(f"Task Results: {results}")


if __name__ == "__main__":
    asyncio.run(main())
