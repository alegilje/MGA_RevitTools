# logger.py


import logging
import os

class ScriptLogger(object):
    def __init__(self, name='DoorScript', log_to_file=False, log_file_path=None):
        self.logger = logging.getLogger(name)

        if not self.logger.handlers:
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            if log_to_file:
                if not log_file_path:
                    # Default log file in user temp folder
                    log_file_path = os.path.join(os.getenv('TEMP'), '{}.log'.format(name))
                file_handler = logging.FileHandler(log_file_path)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)

            self.logger.setLevel(logging.INFO)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)
