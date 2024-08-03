import socket
import subprocess
import os
from logger import logger

# Define the server address and port

SERVER_HOST_NAME = socket.gethostname()
IP_ADDRESS = socket.gethostbyname(SERVER_HOST_NAME)
SERVER_PORT = 52000

def execute_command(command, cwd):
    """Execute a shell command and return its output."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True, check=True, cwd=cwd)
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

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            logger.debug(f"Accepted connection from {client_address}")

            try:
                # Receive the command from the client
                command = client_socket.recv(1024).decode()
                if command:
                    if command.lower() == 'exit':
                        logger.info("Exiting...")
                        break

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
                        output = execute_command(command, cwd)
                        # logger.info(command)

                        if output:
                            logger.info(f'{command}\n' + '-'*25 + ' Output ' + '-'*25 + f'\n\n{output}\n' + '-'*23 + ' End Output ' + '-'*23)
                        else:
                            logger.info(command)
   
                        client_socket.send(output.encode())
                        logger.debug(f"Sent output to client: {client_address}")

            except KeyboardInterrupt:
                logger.info("Interrupted by user. Exiting...")
                break

            except socket.error as e:
                logger.error(f"Socket error: {e}")

            # finally:
            #     client_socket.close()
            #     logger.info(f"Closed connection with {client_address}")

    finally:
        server_socket.close()
        logger.info("Server shut down.")


if __name__ == "__main__":
    main()