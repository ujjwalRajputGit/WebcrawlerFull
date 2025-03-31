import logging

def get_logger(name: str):
    """
    Create and return a logger with the given name.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Check if the logger already has handlers to avoid duplicate logs
    if not logger.hasHandlers():
        # Create a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # Set the log format
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(console_handler)

    return logger 