import logging

DEFAULT_LOG_LEVEL = logging.INFO

logger = logging.getLogger(__name__)
logger.setLevel(DEFAULT_LOG_LEVEL)

# Function to allow users to configure logging
def configure_logging(level=logging.INFO):
    logger.setLevel(level)

