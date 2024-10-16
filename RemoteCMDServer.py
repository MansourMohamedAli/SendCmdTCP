import socket
import subprocess
import os
import sys
import argparse
from logger import Logger
import threading

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


def start_server(logger):
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Reuse the socket address
    server_socket.bind((IP_ADDRESS, SERVER_PORT))
    server_socket.listen(5)
    cwd = os.getcwd()  # Set the initial current working directory
    logger.info(f"Listening on {IP_ADDRESS}:{SERVER_PORT}...")

    try:
        while True:
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
                        # print('=' *25 + ' Output ' + '=' *25)
                        return_code = execute_command(command, cwd)
                        if not return_code:
                            output = f'{SERVER_HOST_NAME} Received Command.'
                            client_socket.send(output.encode())
                        else:
                            client_socket.send(return_code.encode())                            

    except socket.error as e:
        logger.error(f"Socket error: {e}")
    finally:
        server_socket.close()
        logger.info("Server shut down.")

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description='Client for sending commands to the server.')
    parser.add_argument("--loglevel", type=str.lower, help='Server IP address.', default="INFO",  choices=["debug", "info"])
    parser.add_argument("--logfile", type=str.lower, help='Option to output to logfile', default="false",  choices=["true", "false"])
    args = parser.parse_args(args)

    if args.logfile == "true":
        log = Logger(level=args.loglevel, filename="RemoteCMDServer.log")
    else:
        log = Logger(level=args.loglevel)

    thread = threading.Thread(target=start_server, args=[log.logger])
    thread.start()
        

if __name__ == "__main__":
    main()