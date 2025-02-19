import logging

DEFAULT_LOG_LEVEL = logging.INFO

logger = logging.getLogger(__name__)
logger.setLevel(DEFAULT_LOG_LEVEL)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Function to allow users to configure logging
def configure_logging(level=logging.INFO, format=None):
    logger.setLevel(level)
