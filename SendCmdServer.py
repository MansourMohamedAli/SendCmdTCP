import argparse
import asyncio
import json
import sys

from logger import logger

IP_ADDRESS = "0.0.0.0"
DEFAULT_SERVER_PORT = 52000
DEFAULT_MAX_ATTEMPTS = 1  # Maximum number of connection attempts

async def execute_command(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    print(f'[{cmd!r} exited with {proc.returncode}]')
    if stdout:
        print(f'[stdout]\n{stdout.decode()}')
    if stderr:
        print(f'[stderr]\n{stderr.decode()}')

    return proc.returncode, stdout.decode(), stderr.decode()


async def handle_client(reader, writer):
    data = await reader.read(100)
    commands = json.loads(data.decode("utf-8"))
    addr = writer.get_extra_info('peername')
    tasks = [asyncio.create_task(execute_command(cmd=command)) for command in commands]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    print(f"Received {commands!r} from {addr!r}. Result of Execution {results}")


async def main(args=None) -> None:
    if args is None:
        args = sys.argv[1:]

        if len(sys.argv) < 1:
            logger.info('Type "SendCmdClient.exe -h" or "SendCmdClient.exe --help" for usage.')
            return

    parser = argparse.ArgumentParser(description="Server for receiving commands from the client.")
    parser.add_argument("--port", type=int, default=DEFAULT_SERVER_PORT, help=f"The port to connect to the server. Default is {DEFAULT_SERVER_PORT}.")
    args = parser.parse_args(args)

    port = args.port

    server = await asyncio.start_server(
        handle_client, IP_ADDRESS, port)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")