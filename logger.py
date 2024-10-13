import logging
from logging import handlers

class Logger(object):
    level_relations = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'crit': logging.CRITICAL
    }  # relationship mapping

    def __init__(self,level='info', fmt='[%(asctime)s] %(message)s', filename=None):
        self.logger = logging.getLogger(filename)
        format_str = logging.Formatter(fmt,"%H:%M:%S")         # Setting the log format
        self.logger.setLevel(self.level_relations.get(level))  # Setting the log level
        console_handler = logging.StreamHandler()              # on-screen output
        console_handler .setFormatter(format_str)              # Setting the format for console messages
        self.logger.addHandler(console_handler)                # Add the console handler to the logger

        # Optional: Add a file handler
        if filename:
            file_handler = logging.FileHandler(filename)
            fmt='[%(asctime)s][%(levelname)s] %(message)s'
            format_str = logging.Formatter(fmt,"%H:%M:%S")   
            file_handler.setLevel(self.logger.level)
            file_handler.setFormatter(format_str)
            self.logger.addHandler(file_handler)

if __name__ == "__main__":
    log = Logger(level='debug')