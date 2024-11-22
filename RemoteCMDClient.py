import socket
import sys
from logger import logger
import argparse
import threading

DEFAULT_SERVER_PORT = 52000
DEFAULT_MAX_ATTEMPTS = 1  # Maximum number of connection attempts


def connect_to_server(server_host_ip, server_host_port, max_retries, interface):
    """Attempt to connect to the server and return the socket object."""
    attempts = 0 
    while attempts < max_retries:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.bind((interface, 0))
            client_socket.connect((server_host_ip, server_host_port))
            logger.info("Connected to server")
            return client_socket
        except socket.error as e:
            attempts += 1
            logger.error(f"Connection attempt {attempts}/{max_retries} failed: {e}. Retrying...")
    else:
        logger.critical(f'Could not connect to server after {max_retries} attempt(s)... Exiting')


def open_connection_thread(server_host_ip, server_host_port, command, max_attempts, interface):
    """New thread is created to not block code execution of GUIs that use this application."""
    client_socket = connect_to_server(server_host_ip, server_host_port, max_attempts, interface)
    if client_socket:
        while True:
            try:
                # t1 = threading.Thread(target=client_socket.send, args=[command.encode()])
                # t1.start()
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
        
        client_socket.close()


def main(args=None):
    if args is None:
        args = sys.argv[1:]
        
        if len(sys.argv) < 2:
            logger.info(f"Type 'RemoteCMDClient.exe -h' or 'RemoteCMDClient.exe --help' for usage.")
            return

    parser = argparse.ArgumentParser(description='Client for sending commands to the server.')
    parser.add_argument("host", type=str, help='Server IP address.')
    parser.add_argument("command", type=str, help='Command to send. If command is multiple words, enclose in \"\".')
    parser.add_argument('--port', type=int, default=DEFAULT_SERVER_PORT, help=f'The port to connect to the server. Default is {DEFAULT_SERVER_PORT}.')
    parser.add_argument('--attempts', type=int, default=DEFAULT_MAX_ATTEMPTS, help=f'The maximum number of connection attempts. Default is {DEFAULT_MAX_ATTEMPTS}.')
    parser.add_argument('--interface', type=str, default='', help=f'IP address of local network interface used to send command.')
    args = parser.parse_args(args)

    server_host_ip   = args.host 
    command          = args.command
    server_host_port = args.port
    max_attempts     = args.attempts
    interface        = args.interface

    server_host_ip = socket.gethostbyname(server_host_ip)

    connection_thread = threading.Thread(target=open_connection_thread, args=[server_host_ip, server_host_port, command, max_attempts, interface])
    connection_thread.start()
    

if __name__ == "__main__":
    main()
