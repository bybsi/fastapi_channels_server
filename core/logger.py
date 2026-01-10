import os
import logging
import settings
from logging.handlers import RotatingFileHandler

class Logger():
    
    def __init__(self, log_name):

        if not os.path.exists(settings.LOG_DIR):
            os.makedirs(settings.LOG_DIR)

        self.logger = logging.getLogger(log_name)
        handler = RotatingFileHandler(
            os.path.join(settings.LOG_DIR, log_name + '.log'),
            maxBytes=10 * 1024 * 1024,
            backupCount=10
        )
        formatter = logging.Formatter(
            '%(asctime)s (%(name)20s) [%(levelname)9s] %(message)s',
            datefmt='%y%m%d:%H%M%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel('DEBUG')

    def info(self, message):
        self.logger.info(message)

    def warn(self, message):
        self.logger.warn(message)

    def debug(self, message):
        self.logger.debug(message)
