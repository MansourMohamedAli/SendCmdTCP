import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

from pydantic import BaseModel

from logger import logger

IP_ADDRESS = "0.0.0.0"
DEFAULT_SERVER_PORT = 52000
DEFAULT_MAX_ATTEMPTS = 1  # Maximum number of connection attempts
PROCESS_NOT_FOUND_CODE = 128
TIMEOUT = 5


class ErrorPayload(BaseModel):
    command: str
    type: str
    message: str

    @classmethod
    def from_exception(cls, command: str, exc: Exception) -> "ErrorPayload":
        return cls(
            command=str(command),
            type=type(exc).__name__,
            message=str(exc),
        )


class CommandExecutionResult(BaseModel):
    errors: list[ErrorPayload]
    exit_requested: bool = False


async def shutdown_server():
    logger.info("Exiting...")
    sys.exit(0)


def execute_command_sequential(commands, cwd):
    errors: list[ErrorPayload] = []
    exit_requested = False

    for command in commands:
        if command:
            result = None
            if command.lower() == "exit":
                exit_requested = True
                break

            # Check if the command is a "cd" command
            if command.startswith("cd "):
                try:
                    new_dir = command[3:].strip()
                    os.chdir(new_dir)
                    cwd = Path.cwd()  # Update the current working directory
                    logger.info(command)
                except (FileNotFoundError, OSError) as e:
                    logger.error(f"Error: {e}")
                    result = ErrorPayload.from_exception(command, e)

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
                    result = ErrorPayload.from_exception(command, e)
            else:
                # Execute the command and get the output
                logger.info(f"Executing {command}")
                result = execute_command(command, cwd)

            if result:
                errors.append(result)

    return CommandExecutionResult(
        errors=errors,
        exit_requested=exit_requested,
    )


def execute_command(cmd, cwd) -> None | int:
    try:
        result = subprocess.run(
            cmd, shell=True, text=True, cwd=cwd, check=True, timeout=TIMEOUT
        )
    except subprocess.CalledProcessError as e:
        if (
            cmd.lower().startswith("taskkill ")
            and e.returncode == PROCESS_NOT_FOUND_CODE
        ):
            return None
        logger.error(
            f'Command "{e.cmd}" returned non-zero exit status {e.returncode}. Output: {e.output}',
        )
        return ErrorPayload.from_exception(cmd, e)
    except subprocess.TimeoutExpired as e:
        logger.error(
            f'Process "{e.cmd}" timed out after {TIMEOUT} seconds.',
        )
        return ErrorPayload.from_exception(cmd, e)

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

    results: CommandExecutionResult = execute_command_sequential(commands_list, cwd)
    return_message = json.dumps([e.model_dump() for e in results.errors])
    writer.write(return_message.encode("utf-8"))
    await writer.drain()

    if results.exit_requested:
        await asyncio.create_task(shutdown_server())


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
        "-p",
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
