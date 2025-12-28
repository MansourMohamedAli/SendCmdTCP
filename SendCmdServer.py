import argparse
import asyncio
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

from logger import logger

IP_ADDRESS = "0.0.0.0"
DEFAULT_SERVER_PORT = 52000
DEFAULT_MAX_ATTEMPTS = 1  # Maximum number of connection attempts


def execute_command(cmd) -> tuple[int, str, str]:
    print(f"Executing {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    print(f"[{cmd!r} exited with {result.returncode}]")
    if result.stdout:
        print(f"[Output]\n{result.stdout}")
    if result.stderr:
        print(f"[stderr]\n{result.stderr}")

    # return result.returncode, result.stdout, result.stderr
    return result.returncode


async def handle_client(reader, writer):
    data = await reader.read(4096)
    commands = json.loads(data.decode("utf-8"))
    addr = writer.get_extra_info("peername")
    executor = ThreadPoolExecutor(max_workers=1)
    print(f"Command from {addr}")
    results = executor.map(execute_command, commands)
    # for i, result in enumerate(results):
    #     print(f"Result({i}): {result}")


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
