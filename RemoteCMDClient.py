import socket
import time
import sys
from logger import logger
import argparse

DEFAULT_SERVER_PORT = 52000
DEFAULT_MAX_RETRIES = 1  # Maximum number of connection attempts

def connect_to_server(server_host_ip, server_host_port, max_retries):
    """Attempt to connect to the server and return the socket object."""
    attempts = 0 
    while attempts < max_retries:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((server_host_ip, server_host_port))
            logger.info("Connected to server")
            return client_socket
        except socket.error as e:
            attempts += 1
            logger.error(f"Connection attempt {attempts}/{max_retries} failed: {e}. Retrying...")
    else:
        logger.critical(f'Could not connect to server after {max_retries} attempts... Exiting')
        sys.exit(-1)

def main():
    if len(sys.argv) < 2:
        logger.info("Usage: python client.py <command>")
        return

    # SERVER_HOST_IP = sys.argv[1], ' '.join(sys.argv[2:])
    # logger.info(f'Attempting to send command:{command} to server IP:{SERVER_HOST_IP}')

    parser = argparse.ArgumentParser(description='Client for sending commands to the server.')
    parser.add_argument('--host', type=str, help='Server IP address.')
    parser.add_argument('--port', type=int, default=DEFAULT_SERVER_PORT, help=f'The port to connect to the server. Default is {DEFAULT_SERVER_PORT}.')
    parser.add_argument('--command', type=str, help='Command to send. If command is multiple words, enclose in \"\".')
    parser.add_argument('--retries', type=int, default=DEFAULT_MAX_RETRIES, help=f'The maximum number of connection attempts. Default is {DEFAULT_MAX_RETRIES}.')
    parser.add_argument('--feedback', type=int, default=0, help=f'Flag to allow Server to send back command. set 1 to allow feedback.')
    args = parser.parse_args()

    server_host_ip   = args.host 
    server_host_port = args.port
    command          = args.command
    max_retries      = args.retries
    feedback         = args.feedback


    client_socket = connect_to_server(server_host_ip, server_host_port, max_retries)

    while True:
        try:
            client_socket.send(command.encode())
            logger.info(f"Command '{command}' sent to the server.")
            break
        except socket.error as e:
            logger.error(f"Error sending command: {e}. Reconnecting...")
            client_socket = connect_to_server()
        except KeyboardInterrupt:
            logger.error("Interrupted by user. Exiting...")
            break
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            break
    
    # Receive the output from the server
    if feedback:
        output = client_socket.recv(4096).decode()
        logger.info(output)
    
    client_socket.close()

if __name__ == "__main__":
    main()
