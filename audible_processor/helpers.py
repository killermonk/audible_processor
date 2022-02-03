import logging

def get_logger(name: str, verbosity: int) -> logging.Logger:
    if verbosity == 0:
        log_level = logging.WARNING
        format = '%(message)s'
    elif verbosity == 1:
        log_level = logging.INFO
        format = '%(levelname)s - %(message)s'
    elif verbosity >= 2:
        log_level = logging.DEBUG
        format = '%(asctime)s - %(levelname)s - %(message)s'

    logging.basicConfig(level=log_level, format=format)

    return logging.getLogger(name)
