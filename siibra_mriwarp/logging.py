import logging
import os
import sys
import tempfile

from siibra_mriwarp.config import mriwarp_name


class Logger(object):

    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, text):
        for line in text.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass


def setup_logger():
    tmpfile = os.path.join(tempfile.gettempdir(), f'{mriwarp_name}.log')
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(name)s:%(levelname)s] %(asctime)s %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S',
        filename=tmpfile,
        filemode='w'
    )
    logger = logging.getLogger(mriwarp_name)
    sys.stdout = Logger(logger, logging.INFO)
    sys.stderr = Logger(logger, logging.ERROR)
