import argparse
import asyncio
import json
import sys
import time

from logger import logger
from read_config import read_config, serialize_commands

__version__ = "3.0.0"

DEFAULT_SERVER_PORT = 52000
DEFAULT_MAX_ATTEMPTS = 1  # Maximum number of connection attempts
TIMEOUT = 5


async def send_command_tcp(host, port, message):
    results = {}
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=TIMEOUT)
        logger.info(
            f"[{host}:{port}] Commands: [{', '.join(message)}]",
        )

        encoded_message = serialize_commands(message)
        writer.write(encoded_message)
        await writer.drain()

        data = await reader.read(4096)
        results_message = json.loads(data.decode("utf-8"))
        if results_message:
            results[f"{host}:{port}"] = results_message

        writer.close()
        await writer.wait_closed()

    except (ConnectionRefusedError, TimeoutError, OSError) as e:
        results[f"{host}:{port}"] = e

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
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser.parse_args()


def load_single_host(hostname: str, port: int, command: str) -> list:
    command = command.split(";")
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

    if any(results_list):
        logger.info("Error messages were returned:")
        for result in results_list:
            if result:
                logger.info(result)
    else:
        logger.info("All commands were sent and executed successfully")
    print(f"Finished in {t2 - t1:.2f} seconds")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
