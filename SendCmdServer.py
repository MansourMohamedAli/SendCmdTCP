import argparse
import asyncio
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

from logger import logger

IP_ADDRESS = "0.0.0.0"
DEFAULT_SERVER_PORT = 52000
DEFAULT_MAX_ATTEMPTS = 1  # Maximum number of connection attempts


def execute_command_sequential(commands):
    for cmd in commands:
        execute_command(cmd)


def execute_command(cmd) -> tuple[int, str, str]:
    print(f"Executing {cmd}")
    if cmd.startswith("set "):
        set_cmd = cmd[4:].strip().split("=")
        os.environ[set_cmd[0]] = set_cmd[1]

    # result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    result = subprocess.run(cmd, shell=True, text=True)

    print(f"[{cmd!r} exited with {result.returncode}]")

    #################################################################################
    # Since no longer capturing output, stdout and stderr are null. Going
    # to leave this here juset in case output capture is needed in the future.
    # Capturing output will pause command execution as the server will wait for
    # the process to end before moving on to the next. For example: notepad will
    # only return an output after it is closed even with using "start".

    # if result.stdout:
    #     print(f"[stdout]\n{result.stdout}")
    # if result.stderr:
    #     print(f"[stderr]\n{result.stderr}")
    # return result.returncode, result.stdout, result.stderr
    #################################################################################
    return result.returncode


async def handle_client(reader, writer):
    data = await reader.read(4096)
    commands = json.loads(data.decode("utf-8"))
    addr = writer.get_extra_info("peername")
    executor = ThreadPoolExecutor(max_workers=1)
    print(f"Command from {addr}")
    executor.submit(execute_command_sequential, commands)


async def main(args=None) -> None:
    if args is None:
        args = sys.argv[1:]

        if len(sys.argv) < 1:
            logger.info(
                'Type "SendCmdClient.exe -h" or "SendCmdClient.exe --help" for usage.',
            )
            return

    parser = argparse.ArgumentParser(
        description="Server for receiving commands from the client.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_SERVER_PORT,
        help=f"The port to connect to the server. Default is {DEFAULT_SERVER_PORT}.",
    )
    args = parser.parse_args(args)

    port = args.port

    server = await asyncio.start_server(handle_client, IP_ADDRESS, port)

    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    print(f"Serving on {addrs}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
