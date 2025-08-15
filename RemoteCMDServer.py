import os
import socket
import subprocess
import sys

from logger import logger

# TODO handle backslash character


# Define the server address and port
SERVER_HOST_NAME = socket.gethostname()
IP_ADDRESS = socket.gethostbyname(SERVER_HOST_NAME)
SERVER_PORT = 52000

def execute_command(command, cwd):
    """Execute a shell command and return its output."""
    try:
        result = subprocess.Popen(command, text=True, shell=True, cwd=cwd)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Command '{e.cmd}' returned non-zero exit status {e.returncode}. Output: {e.output}"


def main():
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Reuse the socket address
    server_socket.bind((IP_ADDRESS, SERVER_PORT))
    server_socket.listen(5)
    cwd = os.getcwd()  # Set the initial current working directory
    logger.info(f"Listening on {IP_ADDRESS}:{SERVER_PORT}...")

    while True:
        try:
            client_socket, client_address = server_socket.accept()
            logger.debug(f"Accepted connection from {client_address}")
            full_command = client_socket.recv(1024).decode()
            if ';' in full_command:
                full_command = full_command.split(';')
            else:
                full_command = [full_command]
            for command in full_command:
                if command:
                    if command.lower() == 'exit':
                        logger.info("Exiting...")
                        sys.exit()
                    # Check if the command is a 'cd' command
                    if command.startswith('cd '):
                        try:
                            new_dir = command[3:].strip()
                            os.chdir(new_dir)
                            cwd = os.getcwd()  # Update the current working directory
                            logger.info(command)
                        except FileNotFoundError as e:
                            logger.error(f"Error: {e}")
                    elif len(command) > 1 and command[1] == ':': # Changing Drive
                        new_dir = command[:2].strip()
                        os.chdir(new_dir)
                        cwd = os.getcwd()  # Update the current working directory
                        logger.info(command)
                    else:
                        # Execute the command and get the output
                        logger.info(f'Executing {command}')
                        execute_command(command, cwd)

        except socket.error as e:
            logger.error(f"Socket error: {e}")

if __name__ == "__main__":
    main()