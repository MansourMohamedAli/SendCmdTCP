import socket
import sys
from logger import Logger
import argparse
import threading

DEFAULT_SERVER_PORT = 52000
DEFAULT_MAX_ATTEMPTS = 1  # Maximum number of connection attempts


def connect_to_server(server_host_ip, server_host_port, max_retries, logger):
    """Attempt to connect to the server and return the socket object."""
    attempts = 0 
    while attempts < max_retries:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((server_host_ip, server_host_port))
            logger.debug(f'Socker succesfully opened{client_socket.getsockname()}')
            return client_socket
        except socket.error as e:
            attempts += 1
            logger.error(f"Connection attempt {attempts}/{max_retries} failed: {e}. Retrying...")
    else:
        logger.critical(f'Could not connect to server after {max_retries} attempt(s)... Exiting')


def open_connection_thread(server_host_ip, server_host_port, command, max_attempts, feedback, logger):
    """New thread is created to not block code execution of GUIs that use this application."""
    client_socket = connect_to_server(server_host_ip, server_host_port, max_attempts, logger)
    if client_socket:
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
        if feedback == 'true':
            output = client_socket.recv(4096).decode()
            logger.info(output)
        client_socket.close()

def parse_args_from_file(file, parser):
    # Read arguments from the file
    with open(file, 'r') as f:
        for line in f:
            if line:
                line = line.strip().split()
                args = parser.parse_args(line)
                print(args)
        return 


def main(args=None):
    if args is None:
        args = sys.argv[1:]
        
        if len(sys.argv) < 2:
            print(f"Type 'RemoteCMDClient.exe -h' or 'RemoteCMDClient.exe --help' for usage.")
            return

    parser = argparse.ArgumentParser(description='Client for sending commands to the server.')
    parser.add_argument("host",       type=str,       help='Server IP address.')
    parser.add_argument("command",    type=str,       help='Command to send. If command is multiple words, enclose in \"\".')
    parser.add_argument('--port',     type=int,       help=f'The port to connect to the server. Default is {DEFAULT_SERVER_PORT}.', default=DEFAULT_SERVER_PORT)
    parser.add_argument('--attempts', type=int,       help=f'The maximum number of connection attempts. Default is {DEFAULT_MAX_ATTEMPTS}.', default=DEFAULT_MAX_ATTEMPTS)
    parser.add_argument('--feedback', type=str.lower, help=f'Flag to allow Server to send back command.', default="false", choices=["true", "false"])
    parser.add_argument("--loglevel", type=str.lower, help='Server IP address.', default="info",  choices=["debug", "info"])
    parser.add_argument("--logfile",  type=str.lower, help='Option to output to logfile', default="false",  choices=["true", "false"])
    parser.add_argument("--file",     type=str,       help='Option to process commands from file')

    args = parser.parse_args(args)

    server_host_ip   = args.host 
    command          = args.command
    server_host_port = args.port
    max_attempts     = args.attempts
    feedback         = args.feedback
    loglevel         = args.loglevel
    logfile          = args.logfile
    file             = args.file
    
    parse_args_from_file(file, parser)


    if logfile == "true":
        log = Logger(level=loglevel, filename="RemoteCMDClient.log")
    else:
        log = Logger(level=loglevel)

    server_host_ip = socket.gethostbyname(server_host_ip)

    # feedback_list = []

    # if file:
    #     with open(file) as f:
    #         for line in f:
    #             line = line.rstrip()
    #             connection_thread = threading.Thread(target=open_connection_thread, args=[server_host_ip, server_host_port, command, max_attempts, feedback, log.logger])
    #             connection_thread.start()
    # else:
    #     connection_thread = threading.Thread(target=open_connection_thread, args=[server_host_ip, server_host_port, command, max_attempts, feedback, log.logger])
    #     connection_thread.start()

    connection_thread = threading.Thread(target=open_connection_thread, args=[server_host_ip, server_host_port, command, max_attempts, feedback, log.logger])
    connection_thread.start()        

if __name__ == "__main__":
    main()
