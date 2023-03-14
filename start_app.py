import logging

from voluba_mriwarp.config import mriwarp_name
from voluba_mriwarp.gui import App
from voluba_mriwarp.logging import setup_logger


if __name__ == '__main__':
    setup_logger()
    logger = logging.getLogger(mriwarp_name)
    logger.info('Start app')
    try:
        gui = App()
    except Exception as e:
        logger.error(str(e))
    logger.info('Close app')
