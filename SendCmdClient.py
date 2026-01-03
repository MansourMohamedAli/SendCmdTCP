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


async def send_command_tcp(host, port, message):
    try:
        reader, writer = await asyncio.open_connection(host, port)
        print(f"Sending commands: {message} to {host}:{port}")

        encoded_message = serialize_commands(message)
        writer.write(encoded_message)
        await writer.drain()

        ### PICKLE ###
        # results = await recv_pickle(reader)
        ### PICKLE END ###

        ### JSON ###
        data = await reader.read(4096)
        results = json.loads(data.decode("utf-8"))
        # print(f"Received: {data.decode()!r}")
        print(f"Received: {results}")

        # if not any(results):
        #     logger.info(f"All commands sent to {host} and executed with no errors")
        # else:
        #     logger.info(f"{host}:Error Occured")
        ### JSON END ###

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
        "-p",
        "--port",
        nargs="?",
        type=int,
        default=DEFAULT_SERVER_PORT,
        help=f"The port to connect to the server. Default is {DEFAULT_SERVER_PORT}.",
    )
    parser.add_argument(
        "-f",
        "--configfile",
        default="sendcmdconfig.json",
        help="JSON config file with multiple hosts",
    )
    parser.add_argument(
        "-c",
        "--commandset",
        help="command set",
    )
    return parser.parse_args()


def load_single_host(hostname: str, port: int, command: str) -> list:
    command = command.split(";")
    print(command)
    return [{"hostname": hostname, "port": port, "commands": command}]


async def main(args=None):
    if len(sys.argv) < 1:
        logger.info(
            'Type "SendCmdClient.exe -h" or "SendCmdClient.exe --help" for usage.',
        )
        return
    args = parse_args()

    try:
        if args.commandset:
            # CONFIG MODE: ignore positionals
            config_data = read_config(args.configfile, args.commandset)
        else:
            # SINGLE HOST MODE : positionals required
            if not all([args.hostname, args.port, args.command]):
                sys.exit(
                    "Error: hostname, and command are required unless --commandset is specified",
                )
            config_data = load_single_host(args.hostname, args.port, args.command)

    except Exception as e:
        sys.exit(f"Error: {e}")

    tasks = [
        asyncio.create_task(
            send_command_tcp(
                host["hostname"],
                host["port"],
                host["commands"],
            ),
        )
        for host in config_data
    ]
    t1 = time.perf_counter()
    results_list = await asyncio.gather(*tasks, return_exceptions=True)
    t2 = time.perf_counter()

    print(results_list)

    # print(f"Finished in {t2 - t1:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
