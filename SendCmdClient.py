import argparse
import asyncio
import json
import pickle
import struct
import sys
import time

from logger import logger
from read_config import read_config, serialize_commands

DEFAULT_SERVER_PORT = 52000
DEFAULT_MAX_ATTEMPTS = 1  # Maximum number of connection attempts
HEADER_FMT = "!I"  # 4-byte unsigned int
HEADER_SIZE = struct.calcsize(HEADER_FMT)


async def recv_pickle(reader: asyncio.StreamReader):
    header = await reader.readexactly(HEADER_SIZE)
    (length,) = struct.unpack(HEADER_FMT, header)
    payload = await reader.readexactly(length)
    return pickle.loads(payload)


async def tcp_echo_client(host, port, message, error_dict):
    try:
        reader, writer = await asyncio.open_connection(host, port)
        print(f"Sending commands: {message} to {host}:{port}")

        encoded_message = serialize_commands(message)
        writer.write(encoded_message)
        await writer.drain()

        results = await recv_pickle(reader)

        if any(results):
            for index, result in enumerate(results):
                if result:
                    error_dict[f"{host}{port} Command:[{message[index]}]"] = (
                        f'Resulted in "{result}".'
                    )
        writer.close()
        await writer.wait_closed()

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
        return results


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

    error_dict = {}
    tasks = [
        asyncio.create_task(
            tcp_echo_client(
                host["hostname"],
                host["port"],
                host["command"],
                error_dict,
            ),
        )
        for host in config_data
    ]
    t1 = time.perf_counter()
    await asyncio.gather(*tasks, return_exceptions=True)
    t2 = time.perf_counter()

    if error_dict:
        print(json.dumps(error_dict, indent=4, sort_keys=True))
    else:
        print("All commands sent to all hosts and executed with no errors")

    print(f"Finished in {t2 - t1:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
