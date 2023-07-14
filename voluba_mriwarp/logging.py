import logging
import os
import sys
import tempfile

from voluba_mriwarp.config import mriwarp_name


class Logger():
    """Stream that redirects writes to a logger"""

    def __init__(self, logger, level):
        """Initialize the stream.

        :param logging.Logger logger: logger to write to
        :param int level: logging level
        """
        self.logger = logger
        self.level = level

    def write(self, text):
        """Redirect a write to the logger.

        :param str text: text to log
        """
        for line in text.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass


def setup_logger():
    """Setup a logger that also captures stdout and stderr."""
    # Write the log to a temporary file.
    tmp_file = os.path.join(tempfile.gettempdir(), f'{mriwarp_name}.log')
    logging.basicConfig(
        filename=tmp_file, filemode='w',
        format='[%(name)s:%(levelname)s] %(asctime)s %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S', level=logging.DEBUG)
    logger = logging.getLogger(mriwarp_name)
    # Redirect the stream to capture the output of HD_BET and other modules.
    sys.stdout = Logger(logger, logging.INFO)
    sys.stderr = Logger(logger, logging.ERROR)
