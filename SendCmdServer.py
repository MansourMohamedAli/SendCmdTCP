import argparse
import asyncio
import json
import os
import pickle
import struct
import subprocess
import sys
from pathlib import Path

from logger import logger

IP_ADDRESS = "0.0.0.0"
DEFAULT_SERVER_PORT = 52000
DEFAULT_MAX_ATTEMPTS = 1  # Maximum number of connection attempts
PROCESS_NOT_FOUND_CODE = 128

HEADER_FMT = "!I"  # 4-byte unsigned int
HEADER_SIZE = struct.calcsize(HEADER_FMT)


async def send_pickle(writer: asyncio.StreamWriter, obj):
    payload = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
    header = struct.pack(HEADER_FMT, len(payload))
    writer.write(header + payload)
    await writer.drain()


def execute_command_sequential(commands, cwd):
    return_codes = []
    for command in commands:
        if command:
            if command.lower() == "exit":
                logger.info("Exiting...")
                os._exit(0)
            # Check if the command is a "cd" command
            if command.startswith("cd "):
                try:
                    new_dir = command[3:].strip()
                    os.chdir(new_dir)
                    cwd = Path.cwd()  # Update the current working directory
                    logger.info(command)
                except (FileNotFoundError, OSError) as e:
                    logger.error(f"Error: {e}")
                    return_codes.append(e)
            elif len(command) > 1 and command[1] == ":":  # Changing Drive
                new_dir = command[:2].strip()
                os.chdir(new_dir)
                cwd = Path.cwd()  # Update the current working directory
                logger.info(command)
            elif command.startswith("set "):
                try:
                    set_command = command[4:].strip().split("=")
                    os.environ[set_command[0]] = set_command[1]
                    logger.info(command)
                except (FileNotFoundError, OSError) as e:
                    logger.error(f"Error: {e}")
                    return_codes.append(e)
            else:
                # Execute the command and get the output
                logger.info(f"Executing {command}")
                result = execute_command(command, cwd)
                return_codes.append(result)
        else:
            return_codes.append(None)
    return return_codes


def execute_command(cmd, cwd) -> None | int:
    try:
        result = subprocess.run(cmd, shell=True, text=True, cwd=cwd, check=True)
        # logger.info(f"[{cmd!r} exited with {result.returncode}]")
    except subprocess.CalledProcessError as e:
        if cmd.startswith("taskkill ") and e.returncode == PROCESS_NOT_FOUND_CODE:
            return None
        logger.error(
            f'Command "{e.cmd}" returned non-zero exit status {e.returncode}. Output: {e.output}',
        )
        return e
    # else:
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

    # return result.returncode


async def handle_client(reader, writer):
    data = await reader.read(4096)
    commands_list = json.loads(data.decode("utf-8"))
    addr = writer.get_extra_info("peername")
    logger.debug(f"Command from {addr}")
    cwd = Path.cwd()
    task1 = asyncio.create_task(
        asyncio.to_thread(execute_command_sequential, commands_list, cwd),
    )
    results = await task1

    task2 = asyncio.create_task(send_pickle(writer, results))
    await task2


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
    logger.info(f"Serving on {addrs}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
