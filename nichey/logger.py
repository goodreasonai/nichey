import logging

DEFAULT_LOG_LEVEL = logging.INFO

logger = logging.getLogger(__name__)
logger.setLevel(DEFAULT_LOG_LEVEL)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def configure_logging(level=logging.INFO, log_file=None):    
    # Remove existing handlers
    for handler in logger.handlers:
        logger.removeHandler(handler)
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    logger.setLevel(level)
