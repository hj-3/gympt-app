import logging
import sys
from pythonjsonlogger import jsonlogger


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Setup structured JSON logger"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers = []

    # Console handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s",
        rename_fields={"levelname": "level", "asctime": "timestamp"}
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
