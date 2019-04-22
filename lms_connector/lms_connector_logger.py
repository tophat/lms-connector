import logging
import os

logger = logging.getLogger()
log_level = logging.getLevelName(os.environ.get('LOG_LEVEL', 'INFO'))
logger.setLevel(log_level)
