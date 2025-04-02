import logging
from logging.handlers import RotatingFileHandler
from utils.config import (
    LOG_FILE, 
    LOG_TO_FILE, 
    LOG_LEVEL_CONSOLE, 
    LOG_LEVEL_FILE
)

def get_logger(name: str):
    """
    Create and return a logger with the given name.
    Logs will be written to console and optionally to file based on config.
    
    Args:
        name (str): Name of the logger
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Convert string log levels to logging constants
    console_level = getattr(logging, LOG_LEVEL_CONSOLE.upper())
    file_level = getattr(logging, LOG_LEVEL_FILE.upper())

    logger = logging.getLogger(name)
    logger.setLevel(min(console_level, file_level))

    # Check if the logger already has handlers to avoid duplicate logs
    if not logger.hasHandlers():
        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if LOG_TO_FILE:
            try:
                file_handler = RotatingFileHandler(
                    LOG_FILE,
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=5,
                    encoding='utf-8'
                )
                file_handler.setLevel(file_level)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
                logger.debug(f"File logging enabled: writing to {LOG_FILE}")
            except Exception as e:
                logger.error(f"Failed to setup file logging: {e}")

    return logger 